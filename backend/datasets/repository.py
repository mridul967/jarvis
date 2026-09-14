import json
import sqlite3

from backend.app.core.database import connection, initialize_database
from backend.datasets.model import DatasetVersion


def save_dataset(version: DatasetVersion) -> DatasetVersion:
    initialize_database()
    with connection() as database:
        database.execute(
            """INSERT OR IGNORE INTO dataset_versions (
                version_id, name, family, format, source_type, source_url, license, attribution,
                original_filename, media_type, original_size, original_sha256, canonical_sha256,
                parser_name, parser_version, coordinate_system, distance_unit,
                time_unit, timezone, vehicle_count, customer_count,
                original_artifact, canonical_artifact, validation_status,
                validation_errors, import_options
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                version.version_id,
                version.name,
                version.family,
                version.format,
                version.source_type,
                version.source_url,
                version.license,
                version.attribution,
                version.original_filename,
                version.media_type,
                version.original_size,
                version.original_sha256,
                version.canonical_sha256,
                version.parser_name,
                version.parser_version,
                version.coordinate_system,
                version.distance_unit,
                version.time_unit,
                version.timezone,
                version.vehicle_count,
                version.customer_count,
                version.original_artifact,
                version.canonical_artifact,
                version.validation_status,
                json.dumps(version.validation_errors),
                json.dumps(version.import_options, sort_keys=True, separators=(",", ":")),
            ),
        )
        row = database.execute(
            "SELECT * FROM dataset_versions WHERE version_id = ?", (version.version_id,)
        ).fetchone()
    if row is None:  # pragma: no cover - SQLite insert/select invariant
        raise RuntimeError("Dataset version was not saved")
    return _from_row(row)


def get_dataset(version_id: str) -> DatasetVersion | None:
    initialize_database()
    with connection() as database:
        row = database.execute(
            "SELECT * FROM dataset_versions WHERE version_id = ?", (version_id,)
        ).fetchone()
    return _from_row(row) if row is not None else None


def list_datasets(limit: int = 100) -> list[DatasetVersion]:
    initialize_database()
    with connection() as database:
        rows = database.execute(
            """SELECT * FROM dataset_versions
               ORDER BY created_at DESC, version_id DESC LIMIT ?""",
            (limit,),
        ).fetchall()
    return [_from_row(row) for row in rows]


def _from_row(row: sqlite3.Row) -> DatasetVersion:
    values = dict(row)
    values["validation_errors"] = tuple(json.loads(values["validation_errors"]))
    values["import_options"] = json.loads(values["import_options"])
    return DatasetVersion(**values)
