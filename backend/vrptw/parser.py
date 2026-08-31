import re

from backend.vrptw.model import Customer, Instance


def parse_solomon(text: str) -> Instance:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        raise ValueError("Instance is empty")

    vehicle_index = next(
        (i for i, line in enumerate(lines) if "NUMBER" in line and "CAPACITY" in line),
        None,
    )
    customer_index = next(
        (i for i, line in enumerate(lines) if line.startswith("CUST NO.")), None
    )
    if vehicle_index is None or customer_index is None:
        raise ValueError("Expected Solomon VEHICLE and CUSTOMER sections")

    vehicle_values = _numbers(lines[vehicle_index + 1])
    if len(vehicle_values) < 2:
        raise ValueError("Invalid vehicle row")

    customers = []
    for line in lines[customer_index + 1 :]:
        values = _numbers(line)
        if len(values) >= 7:
            customers.append(
                Customer(
                    id=int(values[0]),
                    x=values[1],
                    y=values[2],
                    demand=int(values[3]),
                    ready=values[4],
                    due=values[5],
                    service=values[6],
                )
            )
    if len(customers) < 2 or customers[0].id != 0:
        raise ValueError("Customer table must start with depot id 0")
    if len({customer.id for customer in customers}) != len(customers):
        raise ValueError("Customer ids must be unique")
    return Instance(
        name=lines[0],
        vehicle_count=int(vehicle_values[0]),
        capacity=int(vehicle_values[1]),
        depot=customers[0],
        customers=tuple(customers[1:]),
    )


def _numbers(line: str) -> list[float]:
    return [float(value) for value in re.findall(r"-?\d+(?:\.\d+)?", line)]
