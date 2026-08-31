from dataclasses import dataclass
from typing import Literal

from backend.vrptw.model import Problem

DatasetFormat = Literal["solomon_text", "solomon_csv", "canonical_json"]
CoordinateSystem = Literal["euclidean", "wgs84"]


@dataclass(frozen=True)
class DatasetImport:
    format: DatasetFormat
    filename: str
    content: str
    family: str
    source_url: str | None = None
    license: str | None = None
    attribution: str | None = None
    name: str | None = None
    media_type: str = "text/plain"
    vehicle_count: int | None = None
    capacity: int | None = None
    depot_id: int | None = None
    coordinate_system: CoordinateSystem | None = None
    distance_unit: str | None = None
    time_unit: str | None = None
    timezone: str | None = None


@dataclass(frozen=True)
class ParsedDataset:
    problem: Problem
    parser_name: str
    parser_version: str
    coordinate_system: CoordinateSystem
    distance_unit: str
    time_unit: str
    timezone: str | None
    canonical_json: str


@dataclass(frozen=True)
class DatasetVersion:
    version_id: str
    created_at: str
    name: str
    family: str
    format: DatasetFormat
    source_type: str
    source_url: str | None
    license: str | None
    attribution: str | None
    original_filename: str
    media_type: str
    original_size: int
    original_sha256: str
    canonical_sha256: str
    parser_name: str
    parser_version: str
    coordinate_system: CoordinateSystem
    distance_unit: str
    time_unit: str
    timezone: str | None
    vehicle_count: int
    customer_count: int
    original_artifact: str
    canonical_artifact: str
    validation_status: str
    validation_errors: tuple[str, ...]
    import_options: dict[str, int | str | None]
