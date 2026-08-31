# Dataset inbox

Download the two archives from the
[VRPTW Benchmark Datasets Kaggle page](https://www.kaggle.com/datasets/senju14/vrptw-benchmark-datasets),
extract them, and place the extracted folders here:

```text
data/inbox/
├── Solomon_Instances/                  # expected: 56 .txt instances
└── Gehring_Homberger_Instances/
    ├── homberger_200_customer_instances/
    ├── homberger_400_customer_instances/
    ├── homberger_600_customer_instances/
    ├── homberger_800_customer_instances/
    └── homberger_1000_customer_instances/
```

The importer scans recursively, so an additional directory level created by unzipping is fine.
Do not rename or edit the source files. Raw inputs and generated artifacts are intentionally ignored
by Git.

From the repository root, import each collection with:

```bash
uv run python -m backend.tools.import_datasets \
  data/inbox/Solomon_Instances --family solomon

uv run python -m backend.tools.import_datasets \
  data/inbox/Gehring_Homberger_Instances --family homberger
```

The command validates every instance, stores immutable content-addressed files under
`data/artifacts/`, and records version/provenance metadata in `anywhere-door.db`. A non-zero exit
status means at least one file was rejected; failures are reported and are not silently repaired.

These are Euclidean benchmark instances, not geographic road-network coordinates. OSM/ORS data
will be ingested separately in a later phase as WGS84 graph and travel-time artifacts.
