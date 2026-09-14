import json
from pathlib import Path
from typing import Any


class JsonlAuditWriter:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._event_number = 0

    def write(self, event: dict[str, Any]) -> dict[str, Any]:
        self._event_number += 1
        payload = {"event_id": f"evt-{self._event_number:06d}", **event}
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n")
        return payload
