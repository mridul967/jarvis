import json

from backend.app.core.database import connection, initialize_database


def save_run(result: dict) -> int:
    initialize_database()
    with connection() as database:
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
    with connection() as database:
        rows = database.execute(
            """SELECT id, created_at, algorithm, distance, vehicles,
                      feasible, runtime_ms
               FROM runs ORDER BY id DESC LIMIT ?""",
            (limit,),
        ).fetchall()
    return [dict(row) | {"feasible": bool(row["feasible"])} for row in rows]
