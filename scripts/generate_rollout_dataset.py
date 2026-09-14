import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.simulation.rollouts import generate_rollout_dataset


if __name__ == "__main__":
    print(generate_rollout_dataset(Path("data/artifacts/simulations/rollouts.jsonl")))
