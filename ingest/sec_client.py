import os
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = PROJECT_ROOT / ".env"

SUBMISSIONS_BASE_URL = "https://data.sec.gov/submissions"


load_dotenv(dotenv_path=ENV_PATH)


def normalize_cik(cik: str | int) -> str:
    """Return an SEC CIK as a ten-digit, zero-padded string."""
    cik_text = str(cik).strip()

    if not cik_text.isdigit():
        raise ValueError("CIK must contain only digits.")

    if len(cik_text) > 10:
        raise ValueError("CIK cannot contain more than 10 digits.")

    return cik_text.zfill(10)


def get_company_submissions(
    cik: str | int,
    timeout_seconds: float = 30.0,
) -> dict[str, Any]:
    """Retrieve a company's submission metadata from the SEC."""
    user_agent = os.getenv("SEC_USER_AGENT")

    if not user_agent:
        raise RuntimeError(
            f"SEC_USER_AGENT is not set. Expected to load it from {ENV_PATH}."
        )

    normalized_cik = normalize_cik(cik)
    url = f"{SUBMISSIONS_BASE_URL}/CIK{normalized_cik}.json"

    response = requests.get(
        url,
        headers={
            "User-Agent": user_agent,
            "Accept": "application/json",
        },
        timeout=timeout_seconds,
    )

    response.raise_for_status()
    return response.json()
