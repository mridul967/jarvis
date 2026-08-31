import json
import os
import sqlite3
from pathlib import Path

DATABASE_PATH = Path(os.getenv("DATABASE_PATH", "anywhere-door.db"))


def connect() -> sqlite3.Connection:
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database() -> None:
    with connect() as database:
        database.execute(
            """CREATE TABLE IF NOT EXISTS runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                algorithm TEXT NOT NULL,
                distance REAL NOT NULL,
                vehicles INTEGER NOT NULL,
                feasible INTEGER NOT NULL,
                runtime_ms REAL NOT NULL,
                payload TEXT NOT NULL
            )"""
        )


def save_run(result: dict) -> int:
    initialize_database()
    with connect() as database:
        cursor = database.execute(
            """INSERT INTO runs
               (algorithm, distance, vehicles, feasible, runtime_ms, payload)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                result["algorithm"],
                result["distance"],
                result["vehicles"],
                int(result["feasible"]),
                result["runtime_ms"],
                json.dumps(result),
            ),
        )
        return int(cursor.lastrowid)


def list_runs(limit: int = 20) -> list[dict]:
    initialize_database()
    with connect() as database:
        rows = database.execute(
            """SELECT id, created_at, algorithm, distance, vehicles,
                      feasible, runtime_ms
               FROM runs ORDER BY id DESC LIMIT ?""",
            (limit,),
        ).fetchall()
    return [dict(row) | {"feasible": bool(row["feasible"])} for row in rows]
