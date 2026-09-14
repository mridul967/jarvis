import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.simulation.osm import import_district

if __name__ == "__main__":
    print(import_district())
