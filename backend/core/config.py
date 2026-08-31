import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    environment: str
    database_path: Path
    artifact_root: Path
    allowed_origins: tuple[str, ...]


def load_settings() -> Settings:
    origins = tuple(
        origin.strip()
        for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
        if origin.strip()
    )
    return Settings(
        environment=os.getenv("ENVIRONMENT", "development"),
        database_path=Path(os.getenv("DATABASE_PATH", "anywhere-door.db")),
        artifact_root=Path(os.getenv("ARTIFACT_ROOT", "data/artifacts")),
        allowed_origins=origins or ("http://localhost:3000",),
    )


settings = load_settings()
