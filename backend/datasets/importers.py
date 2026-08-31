import csv
import json
import re
from io import StringIO

from backend.datasets.model import CoordinateSystem, DatasetImport, ParsedDataset
from backend.vrptw.evaluate import validate_solution
from backend.vrptw.model import Customer, Problem, Route, Solution, Vehicle
from backend.vrptw.parser import parse_solomon

PARSER_VERSION = "1.0.0"

_CSV_ALIASES = {
    "id": {"id", "cust no", "customer id", "customer no", "customer number"},
    "x": {"x", "xcoord", "x coordinate"},
    "y": {"y", "ycoord", "y coordinate"},
    "demand": {"demand"},
    "ready": {"ready", "ready time", "earliest", "earliest time"},
    "due": {"due", "due date", "latest", "latest time"},
    "service": {"service", "service time", "service duration"},
}


def parse_dataset(request: DatasetImport) -> ParsedDataset:
    if request.format == "solomon_text":
        problem = parse_solomon(request.content)
        parsed = _parsed(
            problem,
            parser_name="solomon_text",
            coordinate_system="euclidean",
            distance_unit="coordinate_units",
            time_unit="coordinate_units",
            timezone=None,
        )
    elif request.format == "solomon_csv":
        parsed = _parse_csv(request)
    else:
        parsed = _parse_json(request.content)
    _validate_admission(parsed)
    return parsed


def _parse_csv(request: DatasetImport) -> ParsedDataset:
    if request.vehicle_count is None or request.capacity is None or request.depot_id is None:
        raise ValueError("CSV requires vehicle_count, capacity, and depot_id")
    if request.vehicle_count <= 0 or request.capacity <= 0:
        raise ValueError("CSV vehicle_count and capacity must be positive")
    if not request.name:
        raise ValueError("CSV requires an explicit dataset name")
    if not request.coordinate_system or not request.distance_unit or not request.time_unit:
        raise ValueError("CSV requires coordinate_system, distance_unit, and time_unit")
    _validate_timezone(request.coordinate_system, request.timezone)

    reader = csv.DictReader(StringIO(request.content.lstrip("\ufeff")))
    if not reader.fieldnames:
        raise ValueError("CSV header is required")
    headers = _csv_headers(reader.fieldnames)
    rows: list[Customer] = []
    for row_number, row in enumerate(reader, start=2):
        if not any(value and value.strip() for value in row.values()):
            continue
        try:
            rows.append(
                Customer(
                    id=_integer(row[headers["id"]], "customer id"),
                    x=_number(row[headers["x"]], "x"),
                    y=_number(row[headers["y"]], "y"),
                    demand=_integer(row[headers["demand"]], "demand"),
                    ready=_number(row[headers["ready"]], "ready time"),
                    due=_number(row[headers["due"]], "due date"),
                    service=_number(row[headers["service"]], "service time"),
                )
            )
        except (TypeError, ValueError) as error:
            raise ValueError(f"CSV row {row_number}: {error}") from error
    depot_rows = [row for row in rows if row.id == request.depot_id]
    if len(depot_rows) != 1:
        raise ValueError("CSV depot_id must identify exactly one row")
    source_depot = depot_rows[0]
    depot = Customer(
        id=0,
        x=source_depot.x,
        y=source_depot.y,
        demand=source_depot.demand,
        ready=source_depot.ready,
        due=source_depot.due,
        service=source_depot.service,
    )
    customers = tuple(row for row in rows if row.id != request.depot_id)
    problem = Problem(
        name=request.name,
        depot=depot,
        customers=customers,
        vehicles=tuple(
            Vehicle(vehicle_id, request.capacity, depot.ready, depot.due)
            for vehicle_id in range(request.vehicle_count)
        ),
    )
    return _parsed(
        problem,
        parser_name="solomon_csv",
        coordinate_system=request.coordinate_system,
        distance_unit=request.distance_unit,
        time_unit=request.time_unit,
        timezone=request.timezone,
    )


def _parse_json(content: str) -> ParsedDataset:
    try:
        payload = json.loads(content)
    except json.JSONDecodeError as error:
        raise ValueError(f"Invalid JSON: {error.msg}") from error
    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        raise ValueError("Canonical JSON requires schema_version 1")
    required = {
        "schema_version",
        "name",
        "coordinate_system",
        "distance_unit",
        "time_unit",
        "timezone",
        "depot",
        "customers",
        "vehicles",
    }
    missing = sorted(required - payload.keys())
    if missing:
        raise ValueError(f"Canonical JSON missing fields: {', '.join(missing)}")
    coordinate_system = payload["coordinate_system"]
    if coordinate_system not in {"euclidean", "wgs84"}:
        raise ValueError("coordinate_system must be euclidean or wgs84")
    _validate_timezone(coordinate_system, payload["timezone"])
    if not isinstance(payload["customers"], list) or not isinstance(payload["vehicles"], list):
        raise ValueError("customers and vehicles must be arrays")
    problem = Problem(
        name=_text(payload["name"], "name"),
        depot=_json_customer(payload["depot"], "depot"),
        customers=tuple(
            _json_customer(item, f"customers[{index}]")
            for index, item in enumerate(payload["customers"])
        ),
        vehicles=tuple(
            _json_vehicle(item, f"vehicles[{index}]")
            for index, item in enumerate(payload["vehicles"])
        ),
    )
    return _parsed(
        problem,
        parser_name="canonical_json",
        coordinate_system=coordinate_system,
        distance_unit=_text(payload["distance_unit"], "distance_unit"),
        time_unit=_text(payload["time_unit"], "time_unit"),
        timezone=payload["timezone"],
    )


def _parsed(
    problem: Problem,
    parser_name: str,
    coordinate_system: CoordinateSystem,
    distance_unit: str,
    time_unit: str,
    timezone: str | None,
) -> ParsedDataset:
    canonical = {
        "schema_version": 1,
        "name": problem.name,
        "coordinate_system": coordinate_system,
        "distance_unit": distance_unit,
        "time_unit": time_unit,
        "timezone": timezone,
        "depot": _customer_dict(problem.depot),
        "customers": [_customer_dict(customer) for customer in problem.customers],
        "vehicles": [_vehicle_dict(vehicle) for vehicle in problem.vehicles],
    }
    return ParsedDataset(
        problem=problem,
        parser_name=parser_name,
        parser_version=PARSER_VERSION,
        coordinate_system=coordinate_system,
        distance_unit=distance_unit,
        time_unit=time_unit,
        timezone=timezone,
        canonical_json=json.dumps(
            canonical, sort_keys=True, separators=(",", ":"), allow_nan=False
        ),
    )


def _validate_admission(parsed: ParsedDataset) -> None:
    problem = parsed.problem
    if not problem.customers:
        raise ValueError("At least one customer is required")
    if parsed.coordinate_system == "wgs84":
        for node in (problem.depot, *problem.customers):
            if not -180 <= node.x <= 180 or not -90 <= node.y <= 90:
                raise ValueError("WGS84 coordinates must be [longitude, latitude]")
    if parsed.coordinate_system == "euclidean":
        impossible = []
        for customer in problem.customers:
            if not any(
                validate_solution(
                    problem,
                    Solution((Route(vehicle.id, (customer.id,)),)),
                )
                .route_evaluations[0]
                .hard_violations
                == 0
                for vehicle in problem.vehicles
            ):
                impossible.append(customer.id)
        if impossible:
            raise ValueError(f"Customers impossible to serve alone: {impossible}")


def _csv_headers(fieldnames: list[str]) -> dict[str, str]:
    selected: dict[str, str] = {}
    for header in fieldnames:
        normalized = _normalize_header(header)
        matches = [name for name, aliases in _CSV_ALIASES.items() if normalized in aliases]
        if not matches:
            continue
        name = matches[0]
        if name in selected:
            raise ValueError(f"Ambiguous CSV columns for {name}")
        selected[name] = header
    missing = sorted(_CSV_ALIASES.keys() - selected.keys())
    if missing:
        raise ValueError(f"CSV missing columns: {', '.join(missing)}")
    return selected


def _normalize_header(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower().replace("_", " ").replace(".", ""))


def _json_customer(value: object, field: str) -> Customer:
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be an object")
    return Customer(
        id=_integer(value.get("id"), f"{field}.id"),
        x=_number(value.get("x"), f"{field}.x"),
        y=_number(value.get("y"), f"{field}.y"),
        demand=_integer(value.get("demand"), f"{field}.demand"),
        ready=_number(value.get("ready"), f"{field}.ready"),
        due=_number(value.get("due"), f"{field}.due"),
        service=_number(value.get("service"), f"{field}.service"),
    )


def _json_vehicle(value: object, field: str) -> Vehicle:
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be an object")
    return Vehicle(
        id=_integer(value.get("id"), f"{field}.id"),
        capacity=_integer(value.get("capacity"), f"{field}.capacity"),
        shift_start=_number(value.get("shift_start"), f"{field}.shift_start"),
        shift_end=_number(value.get("shift_end"), f"{field}.shift_end"),
        start_node=_integer(value.get("start_node"), f"{field}.start_node"),
        end_node=_integer(value.get("end_node"), f"{field}.end_node"),
        fixed_cost=_number(value.get("fixed_cost"), f"{field}.fixed_cost"),
    )


def _customer_dict(customer: Customer) -> dict[str, int | float]:
    return {
        "id": customer.id,
        "x": customer.x,
        "y": customer.y,
        "demand": customer.demand,
        "ready": customer.ready,
        "due": customer.due,
        "service": customer.service,
    }


def _vehicle_dict(vehicle: Vehicle) -> dict[str, int | float]:
    return {
        "id": vehicle.id,
        "capacity": vehicle.capacity,
        "shift_start": vehicle.shift_start,
        "shift_end": vehicle.shift_end,
        "start_node": vehicle.start_node,
        "end_node": vehicle.end_node,
        "fixed_cost": vehicle.fixed_cost,
    }


def _integer(value: object, field: str) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{field} must be an integer")
    try:
        number = float(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{field} must be an integer") from error
    if not number.is_integer():
        raise ValueError(f"{field} must be an integer")
    return int(number)


def _number(value: object, field: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{field} must be numeric")
    try:
        return float(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{field} must be numeric") from error


def _text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be non-empty text")
    return value.strip()


def _validate_timezone(coordinate_system: str, timezone: object) -> None:
    if coordinate_system == "wgs84" and (not isinstance(timezone, str) or not timezone.strip()):
        raise ValueError("WGS84 datasets require a timezone")
    if timezone is not None and not isinstance(timezone, str):
        raise ValueError("timezone must be text or null")
