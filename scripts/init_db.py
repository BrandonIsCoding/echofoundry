from app.db import engine
from app.models import Base


def init_database() -> None:
    """Create database tables registered with SQLAlchemy metadata."""
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    init_database()
    print("Database tables initialized.")
