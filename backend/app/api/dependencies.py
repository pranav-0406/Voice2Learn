"""Reusable FastAPI dependencies."""

from app.core.config import get_settings
from app.db.database import Database


def get_database() -> Database:
    return Database(get_settings().database_path)
