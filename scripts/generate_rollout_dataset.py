from pathlib import Path

from backend.simulation.rollouts import generate_rollout_dataset


if __name__ == "__main__":
    print(generate_rollout_dataset(Path("data/artifacts/simulations/rollouts.jsonl")))
