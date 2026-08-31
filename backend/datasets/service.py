import hashlib
import json
import os
import tempfile
from pathlib import Path

from backend.core.config import settings
from backend.datasets.importers import parse_dataset
from backend.datasets.model import DatasetImport, DatasetVersion, ParsedDataset
from backend.datasets.repository import save_dataset

MAX_DATASET_BYTES = 5_000_000


def validate_import(request: DatasetImport) -> ParsedDataset:
    _validate_request(request)
    return parse_dataset(request)


def import_dataset(request: DatasetImport) -> DatasetVersion:
    parsed = validate_import(request)
    original = request.content.encode("utf-8")
    canonical = parsed.canonical_json.encode("utf-8")
    original_sha256 = _digest(original)
    canonical_sha256 = _digest(canonical)
    options: dict[str, int | str | None] = {
        "vehicle_count": request.vehicle_count,
        "capacity": request.capacity,
        "depot_id": request.depot_id,
        "coordinate_system": request.coordinate_system,
        "distance_unit": request.distance_unit,
        "time_unit": request.time_unit,
        "timezone": request.timezone,
    }
    identity = {
        "attribution": request.attribution,
        "canonical_sha256": canonical_sha256,
        "family": request.family,
        "format": request.format,
        "license": request.license,
        "name": request.name or parsed.problem.name,
        "original_filename": request.filename,
        "original_sha256": original_sha256,
        "parser_name": parsed.parser_name,
        "parser_version": parsed.parser_version,
        "source_type": "url" if request.source_url else "user_upload",
        "source_url": request.source_url,
        "options": options,
    }
    version_id = _digest(
        json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
    )
    original_artifact = _write_artifact(original, original_sha256)
    canonical_artifact = _write_artifact(canonical, canonical_sha256)
    return save_dataset(
        DatasetVersion(
            version_id=version_id,
            created_at="",
            name=request.name or parsed.problem.name,
            family=request.family.strip(),
            format=request.format,
            source_type="url" if request.source_url else "user_upload",
            source_url=request.source_url,
            license=request.license,
            attribution=request.attribution,
            original_filename=request.filename,
            media_type=request.media_type,
            original_size=len(original),
            original_sha256=original_sha256,
            canonical_sha256=canonical_sha256,
            parser_name=parsed.parser_name,
            parser_version=parsed.parser_version,
            coordinate_system=parsed.coordinate_system,
            distance_unit=parsed.distance_unit,
            time_unit=parsed.time_unit,
            timezone=parsed.timezone,
            vehicle_count=len(parsed.problem.vehicles),
            customer_count=len(parsed.problem.customers),
            original_artifact=original_artifact,
            canonical_artifact=canonical_artifact,
            validation_status="valid",
            validation_errors=(),
            import_options=options,
        )
    )


def _validate_request(request: DatasetImport) -> None:
    if not request.filename or request.filename != Path(request.filename).name:
        raise ValueError("filename must be a plain filename without directories")
    if len(request.filename) > 255 or any(ord(character) < 32 for character in request.filename):
        raise ValueError("filename is invalid")
    if not request.family.strip():
        raise ValueError("family is required")
    if len(request.content.encode("utf-8")) > MAX_DATASET_BYTES:
        raise ValueError(f"Dataset exceeds the {MAX_DATASET_BYTES}-byte import limit")


def _write_artifact(content: bytes, digest: str) -> str:
    relative = Path("sha256") / digest[:2] / digest
    target = settings.artifact_root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        if _digest(target.read_bytes()) != digest:
            raise RuntimeError(f"Artifact checksum mismatch: {relative}")
        return relative.as_posix()
    with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as temporary:
        temporary.write(content)
        temporary_path = Path(temporary.name)
    try:
        os.replace(temporary_path, target)
    finally:
        temporary_path.unlink(missing_ok=True)
    return relative.as_posix()


def _digest(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()
