import hashlib
import os
import tempfile
from pathlib import Path

from backend.core.config import settings


def sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def write_artifact(content: bytes) -> tuple[str, str]:
    digest = sha256(content)
    relative = Path("sha256") / digest[:2] / digest
    target = settings.artifact_root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        if sha256(target.read_bytes()) != digest:
            raise RuntimeError(f"Artifact checksum mismatch: {relative}")
        return relative.as_posix(), digest
    with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as temporary:
        temporary.write(content)
        temporary_path = Path(temporary.name)
    try:
        os.replace(temporary_path, target)
    finally:
        temporary_path.unlink(missing_ok=True)
    return relative.as_posix(), digest


def read_artifact(artifact_id: str, expected_sha256: str) -> bytes:
    relative = Path(artifact_id)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("Invalid artifact id")
    content = (settings.artifact_root / relative).read_bytes()
    if sha256(content) != expected_sha256:
        raise RuntimeError(f"Artifact checksum mismatch: {artifact_id}")
    return content
