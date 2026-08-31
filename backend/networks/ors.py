import json
import math
from collections.abc import Sequence
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from backend.core.config import settings

ORS_PROFILES = frozenset(
    {
        "driving-car",
        "driving-hgv",
        "cycling-regular",
        "cycling-road",
        "cycling-mountain",
        "cycling-electric",
        "foot-walking",
        "foot-hiking",
        "wheelchair",
    }
)


class OrsRequestError(RuntimeError):
    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


def matrix_blocks(
    node_count: int, maximum_routes: int
) -> list[tuple[tuple[int, ...], tuple[int, ...]]]:
    if node_count <= 0 or maximum_routes <= 0:
        raise ValueError("node_count and maximum_routes must be positive")
    side = max(1, math.isqrt(maximum_routes))
    chunks = [
        tuple(range(start, min(start + side, node_count))) for start in range(0, node_count, side)
    ]
    return [(sources, destinations) for sources in chunks for destinations in chunks]


def fetch_matrix(
    profile: str,
    locations: Sequence[tuple[float, float]],
    sources: Sequence[int],
    destinations: Sequence[int],
) -> dict[str, Any]:
    _validate_profile(profile)
    validate_base_url()
    if len(sources) * len(destinations) > settings.ors_matrix_max_routes:
        raise ValueError("Matrix block exceeds ORS_MATRIX_MAX_ROUTES")
    payload = {
        "locations": [list(location) for location in locations],
        "sources": [str(index) for index in sources],
        "destinations": [str(index) for index in destinations],
        "metrics": ["distance", "duration"],
        "units": "m",
        "resolve_locations": False,
    }
    response = _post_json(f"/v2/matrix/{profile}", payload)
    validate_matrix_response(response, len(sources), len(destinations))
    return response


def fetch_directions(profile: str, coordinates: Sequence[tuple[float, float]]) -> dict[str, Any]:
    _validate_profile(profile)
    validate_base_url()
    if len(coordinates) < 2:
        raise ValueError("Directions requires at least two coordinates")
    return _post_json(
        f"/v2/directions/{profile}/geojson",
        {"coordinates": [list(coordinate) for coordinate in coordinates]},
    )


def _post_json(path: str, payload: dict[str, Any]) -> dict[str, Any]:
    if not settings.ors_api_key:
        raise OrsRequestError("ORS_API_KEY is not configured")
    request = Request(
        f"{settings.ors_base_url}{path}",
        data=json.dumps(payload, separators=(",", ":")).encode("utf-8"),
        headers={
            "Accept": "application/json",
            "Authorization": settings.ors_api_key,
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=settings.ors_timeout_seconds) as response:
            body = response.read()
    except HTTPError as error:
        raise OrsRequestError(f"ORS request failed with HTTP {error.code}", error.code) from error
    except TimeoutError as error:
        raise OrsRequestError("ORS request timed out") from error
    except URLError as error:
        raise OrsRequestError("ORS request could not reach the configured server") from error
    try:
        parsed = json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise OrsRequestError("ORS returned invalid JSON") from error
    if not isinstance(parsed, dict):
        raise OrsRequestError("ORS returned an invalid response object")
    return parsed


def _validate_profile(profile: str) -> None:
    if profile not in ORS_PROFILES:
        raise ValueError(f"Unsupported ORS profile: {profile}")


def validate_base_url() -> None:
    parsed = urlsplit(settings.ors_base_url)
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.netloc
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("ORS_BASE_URL must be an HTTP(S) origin without credentials or query data")


def validate_matrix_response(response: dict[str, Any], rows: int, columns: int) -> None:
    for metric in ("distances", "durations"):
        matrix = response.get(metric)
        if not isinstance(matrix, list) or len(matrix) != rows:
            raise OrsRequestError(f"ORS {metric} row count does not match the request")
        for row in matrix:
            if not isinstance(row, list) or len(row) != columns:
                raise OrsRequestError(f"ORS {metric} column count does not match the request")
            if any(
                value is not None
                and (
                    isinstance(value, bool)
                    or not isinstance(value, int | float)
                    or not math.isfinite(value)
                    or value < 0
                )
                for value in row
            ):
                raise OrsRequestError(f"ORS {metric} contains an invalid value")
