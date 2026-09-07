import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    environment: str
    database_path: Path
    artifact_root: Path
    allowed_origins: tuple[str, ...]
    ors_api_key: str | None = None
    ors_base_url: str = "https://api.openrouteservice.org"
    ors_matrix_max_routes: int = 3_500
    ors_timeout_seconds: float = 30.0


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
        ors_api_key=os.getenv("ORS_API_KEY") or None,
        ors_base_url=os.getenv("ORS_BASE_URL", "https://api.openrouteservice.org").rstrip("/"),
        ors_matrix_max_routes=int(os.getenv("ORS_MATRIX_MAX_ROUTES", "3500")),
        ors_timeout_seconds=float(os.getenv("ORS_TIMEOUT_SECONDS", "30")),
    )


settings = load_settings()
