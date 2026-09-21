from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

from .config import get_settings
from .models import Base


s = get_settings()
engine = create_engine(
    s.database_url,
    connect_args={"check_same_thread": False} if s.database_url.startswith("sqlite") else {},
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(bind=engine)


REVIEW_COLUMNS = {
    "disclosure_suggestion": "BOOLEAN NOT NULL DEFAULT FALSE",
    "advertiser_risk_level": "VARCHAR(16) NOT NULL DEFAULT 'LOW'",
    "disclosure_suggestion_reason": "TEXT NOT NULL DEFAULT ''",
    "human_watched_confirmed": "BOOLEAN NOT NULL DEFAULT FALSE",
    "human_disclosure_answer": "BOOLEAN",
}


def _ensure_review_columns() -> None:
    inspector = inspect(engine)
    if "videos" not in inspector.get_table_names():
        return
    existing = {column["name"] for column in inspector.get_columns("videos")}
    with engine.begin() as connection:
        for name, definition in REVIEW_COLUMNS.items():
            if name not in existing:
                connection.execute(
                    text(f"ALTER TABLE videos ADD COLUMN {name} {definition}")
                )


def init_db():
    Base.metadata.create_all(engine)
    _ensure_review_columns()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
