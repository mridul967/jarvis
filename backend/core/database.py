import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager

from backend.core.config import settings


@contextmanager
def connection() -> Iterator[sqlite3.Connection]:
    database = sqlite3.connect(settings.database_path)
    database.row_factory = sqlite3.Row
    try:
        yield database
        database.commit()
    except Exception:
        database.rollback()
        raise
    finally:
        database.close()


def initialize_database() -> None:
    with connection() as database:
        database.execute(
            """CREATE TABLE IF NOT EXISTS runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                algorithm TEXT NOT NULL CHECK (algorithm IN ('pso', 'qpso')),
                distance REAL NOT NULL CHECK (distance >= 0),
                vehicles INTEGER NOT NULL CHECK (vehicles > 0),
                feasible INTEGER NOT NULL CHECK (feasible IN (0, 1)),
                runtime_ms REAL NOT NULL CHECK (runtime_ms >= 0),
                payload TEXT NOT NULL
            )"""
        )


def check_database() -> bool:
    try:
        with connection() as database:
            database.execute("SELECT 1").fetchone()
        return True
    except sqlite3.Error:
        return False
