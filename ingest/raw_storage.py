import hashlib
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

from ingest.sec_client import (
    DownloadedFiling,
    build_primary_document_url,
)
from ingest.sec_filings import FilingMetadata


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_SEC_ROOT = PROJECT_ROOT / "data" / "raw" / "sec"


@dataclass(frozen=True, slots=True)
class ArchivedFiling:
    """Verified location and identity of an archived SEC document."""

    path: Path
    content_hash: str
    size_bytes: int
    already_existed: bool


def sha256_bytes(content: bytes) -> str:
    """Calculate the SHA-256 hash of bytes held in memory."""
    return hashlib.sha256(content).hexdigest()


def sha256_file(path: Path) -> str:
    """Calculate a file's SHA-256 hash in one-megabyte chunks."""
    digest = hashlib.sha256()

    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()


def build_raw_filing_path(
    filing: FilingMetadata,
    root: Path = RAW_SEC_ROOT,
) -> Path:
    """Build a deterministic archive path for an SEC primary document."""
    cik = filing.cik.zfill(10)
    accession = filing.accession_number.replace("-", "")
    filename = filing.primary_document.strip()

    if not cik.isdigit() or len(cik) != 10:
        raise ValueError("CIK must normalize to exactly 10 digits.")

    if not accession.isdigit():
        raise ValueError(
            "Accession number must contain only digits and hyphens."
        )

    if not filename:
        raise ValueError("Primary document filename cannot be empty.")

    if Path(filename).name != filename:
        raise ValueError(
            "Primary document must be a filename, not a path."
        )

    return root / cik / accession / filename


def archive_filing(
    filing: FilingMetadata,
    downloaded: DownloadedFiling,
    root: Path = RAW_SEC_ROOT,
) -> ArchivedFiling:
    """Atomically archive and verify an SEC primary document."""
    expected_url = build_primary_document_url(filing)

    if downloaded.source_url != expected_url:
        raise ValueError(
            "Downloaded document URL does not match the filing metadata."
        )

    calculated_hash = sha256_bytes(downloaded.content)

    if calculated_hash != downloaded.content_hash:
        raise ValueError(
            "Downloaded content does not match its recorded SHA-256 hash."
        )

    final_path = build_raw_filing_path(filing, root)
    final_path.parent.mkdir(parents=True, exist_ok=True)

    if final_path.exists():
        existing_hash = sha256_file(final_path)

        if existing_hash != calculated_hash:
            raise FileExistsError(
                "Archive path already contains different content: "
                f"{final_path}"
            )

        return ArchivedFiling(
            path=final_path,
            content_hash=existing_hash,
            size_bytes=final_path.stat().st_size,
            already_existed=True,
        )

    temporary_path: Path | None = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            dir=final_path.parent,
            prefix=f".{final_path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary_file:
            temporary_file.write(downloaded.content)
            temporary_file.flush()
            os.fsync(temporary_file.fileno())
            temporary_path = Path(temporary_file.name)

        temporary_hash = sha256_file(temporary_path)

        if temporary_hash != calculated_hash:
            raise IOError(
                "Temporary archive file failed SHA-256 verification."
            )

        try:
            os.link(temporary_path, final_path)
        except FileExistsError:
            existing_hash = sha256_file(final_path)

            if existing_hash != calculated_hash:
                raise FileExistsError(
                    "Archive path was created with different content: "
                    f"{final_path}"
                )

            return ArchivedFiling(
                path=final_path,
                content_hash=existing_hash,
                size_bytes=final_path.stat().st_size,
                already_existed=True,
            )

        final_hash = sha256_file(final_path)

        if final_hash != calculated_hash:
            final_path.unlink(missing_ok=True)
            raise IOError(
                "Final archive file failed SHA-256 verification."
            )

        return ArchivedFiling(
            path=final_path,
            content_hash=final_hash,
            size_bytes=final_path.stat().st_size,
            already_existed=False,
        )

    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()
