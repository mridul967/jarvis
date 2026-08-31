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
        database.execute(
            """CREATE TABLE IF NOT EXISTS dataset_versions (
                version_id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                name TEXT NOT NULL,
                family TEXT NOT NULL,
                format TEXT NOT NULL CHECK (
                    format IN ('solomon_text', 'solomon_csv', 'canonical_json')
                ),
                source_type TEXT NOT NULL CHECK (source_type IN ('url', 'user_upload')),
                source_url TEXT,
                license TEXT,
                attribution TEXT,
                original_filename TEXT NOT NULL,
                media_type TEXT NOT NULL,
                original_size INTEGER NOT NULL CHECK (original_size >= 0),
                original_sha256 TEXT NOT NULL,
                canonical_sha256 TEXT NOT NULL,
                parser_name TEXT NOT NULL,
                parser_version TEXT NOT NULL,
                coordinate_system TEXT NOT NULL CHECK (
                    coordinate_system IN ('euclidean', 'wgs84')
                ),
                distance_unit TEXT NOT NULL,
                time_unit TEXT NOT NULL,
                timezone TEXT,
                vehicle_count INTEGER NOT NULL CHECK (vehicle_count > 0),
                customer_count INTEGER NOT NULL CHECK (customer_count > 0),
                original_artifact TEXT NOT NULL,
                canonical_artifact TEXT NOT NULL,
                validation_status TEXT NOT NULL CHECK (validation_status = 'valid'),
                validation_errors TEXT NOT NULL,
                import_options TEXT NOT NULL
            )"""
        )
        database.execute(
            """CREATE INDEX IF NOT EXISTS dataset_versions_created_at
               ON dataset_versions(created_at DESC)"""
        )


def check_database() -> bool:
    try:
        with connection() as database:
            database.execute("SELECT 1").fetchone()
        return True
    except sqlite3.Error:
        return False
