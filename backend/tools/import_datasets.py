import argparse
from pathlib import Path

from backend.datasets.model import DatasetImport
from backend.datasets.service import import_dataset

KAGGLE_URL = "https://www.kaggle.com/datasets/senju14/vrptw-benchmark-datasets"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Recursively import extracted Solomon-format VRPTW .txt instances."
    )
    parser.add_argument("folder", type=Path, help="Folder containing extracted .txt instances")
    parser.add_argument("--family", required=True, help="Dataset family, e.g. solomon or homberger")
    parser.add_argument("--source-url", default=KAGGLE_URL)
    parser.add_argument("--license", default="CC BY 4.0")
    parser.add_argument(
        "--attribution",
        default="Solomon (1987); Gehring and Homberger (1999); Kaggle mirror by senju14",
    )
    arguments = parser.parse_args()

    if not arguments.folder.is_dir():
        parser.error(f"folder does not exist or is not a directory: {arguments.folder}")
    files = sorted(arguments.folder.rglob("*.txt"))
    if not files:
        parser.error(f"no .txt instances found under: {arguments.folder}")

    failures: list[tuple[Path, str]] = []
    for path in files:
        try:
            version = import_dataset(
                DatasetImport(
                    format="solomon_text",
                    filename=path.name,
                    content=path.read_text(encoding="utf-8-sig"),
                    family=arguments.family,
                    source_url=arguments.source_url,
                    license=arguments.license,
                    attribution=arguments.attribution,
                )
            )
            print(f"imported {path}: {version.version_id}")
        except (OSError, UnicodeError, ValueError) as error:
            failures.append((path, str(error)))
            print(f"failed {path}: {error}")

    print(f"processed={len(files)} imported={len(files) - len(failures)} failed={len(failures)}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
