from typing import Literal

from pydantic import BaseModel, Field

from backend.datasets.model import CoordinateSystem, DatasetFormat

Algorithm = Literal["pso", "qpso"]
OrsProfile = Literal[
    "driving-car",
    "driving-hgv",
    "cycling-regular",
    "cycling-road",
    "cycling-mountain",
    "cycling-electric",
    "foot-walking",
    "foot-hiking",
    "wheelchair",
]


class SolveRequest(BaseModel):
    algorithm: Algorithm = "qpso"
    population_size: int = Field(30, ge=5, le=200)
    iterations: int = Field(80, ge=1, le=2_000)
    seed: int = 42
    instance: str | None = Field(default=None, min_length=1, max_length=1_000_000)


class SolveParameters(BaseModel):
    population_size: int
    iterations: int
    seed: int


class ScoreResponse(BaseModel):
    hard_violations: int
    coverage_errors: int
    vehicles: int
    lateness: float
    travel_time: float
    distance: float
    congestion: float


class ConvergencePointResponse(BaseModel):
    evaluations: int
    score: ScoreResponse


class SolveResponse(BaseModel):
    id: int
    instance: str
    algorithm: Algorithm
    algorithm_version: str
    distance: float
    vehicles: int
    feasible: bool
    violations: int
    routes: list[list[int]]
    convergence: list[float]
    convergence_points: list[ConvergencePointResponse]
    score: ScoreResponse
    evaluations: int
    runtime_ms: float
    parameters: SolveParameters


class RunSummary(BaseModel):
    id: int
    created_at: str
    algorithm: Algorithm
    distance: float
    vehicles: int
    feasible: bool
    runtime_ms: float


class InstanceResponse(BaseModel):
    name: str
    content: str


class DatasetImportRequest(BaseModel):
    format: DatasetFormat
    filename: str = Field(min_length=1, max_length=255)
    content: str = Field(max_length=5_000_000)
    family: str = Field(min_length=1, max_length=100)
    source_url: str | None = Field(default=None, max_length=2_000)
    license: str | None = Field(default=None, max_length=200)
    attribution: str | None = Field(default=None, max_length=2_000)
    name: str | None = Field(default=None, min_length=1, max_length=200)
    media_type: str = Field(default="text/plain", min_length=1, max_length=100)
    vehicle_count: int | None = Field(default=None, gt=0)
    capacity: int | None = Field(default=None, gt=0)
    depot_id: int | None = Field(default=None, ge=0)
    coordinate_system: CoordinateSystem | None = None
    distance_unit: str | None = Field(default=None, min_length=1, max_length=100)
    time_unit: str | None = Field(default=None, min_length=1, max_length=100)
    timezone: str | None = Field(default=None, min_length=1, max_length=100)


class DatasetValidationResponse(BaseModel):
    valid: bool
    errors: list[str]
    name: str | None = None
    vehicle_count: int | None = None
    customer_count: int | None = None
    canonical_sha256: str | None = None


class DatasetVersionResponse(BaseModel):
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
    validation_errors: list[str]
    import_options: dict[str, int | str | None]


class CostSnapshotCreateRequest(BaseModel):
    dataset_version_id: str = Field(min_length=64, max_length=64)
    profile: OrsProfile = "driving-car"


class CostSnapshotResponse(BaseModel):
    snapshot_id: str
    created_at: str
    dataset_version_id: str
    profile: str
    provider: str
    provider_url: str
    attribution: str
    request_sha256: str
    raw_sha256: str
    normalized_sha256: str
    raw_artifact: str
    normalized_artifact: str
    node_count: int
    block_count: int
    unreachable_count: int


class CostSnapshotDetailResponse(CostSnapshotResponse):
    request: dict


class ArcMultiplierRequest(BaseModel):
    origin: int
    destination: int
    start: float
    end: float
    multiplier: float


class ExogenousTrafficRequest(BaseModel):
    source_type: Literal["simulated", "historical_replay", "live"]
    timezone: str = Field(min_length=1, max_length=100)
    horizon_start: float
    horizon_end: float
    intervals: list[ArcMultiplierRequest] = Field(min_length=1)
    source: str = Field(min_length=1, max_length=2_000)
    generator_seed: int | None = None
    generator_parameters: dict[str, int | float | str] = Field(default_factory=dict)


class ArcCongestionRequest(BaseModel):
    origin: int
    destination: int
    capacity: float
    alpha: float
    beta: float


class EndogenousTrafficRequest(BaseModel):
    arcs: list[ArcCongestionRequest] = Field(min_length=1)
    flow_unit: str = Field(min_length=1, max_length=100)
    interval_seconds: float = Field(gt=0)
    assignment_rule: Literal["simultaneous_vehicle_count"]
    tolerance: float = Field(ge=0)
    max_rounds: int = Field(gt=0, le=10_000)


class TrafficScenarioRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    exogenous: ExogenousTrafficRequest | None = None
    endogenous: EndogenousTrafficRequest | None = None


class TrafficScenarioValidationResponse(BaseModel):
    valid: bool
    errors: list[str]
    mode: Literal["exogenous", "endogenous", "combined"] | None = None
    content_sha256: str | None = None


class TrafficScenarioResponse(BaseModel):
    scenario_id: str
    created_at: str
    name: str
    mode: Literal["exogenous", "endogenous", "combined"]
    content_sha256: str
    artifact: str


class TrafficScenarioDetailResponse(TrafficScenarioResponse):
    content: dict
