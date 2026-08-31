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
is ingested separately as WGS84 graph and travel-time artifacts.

For OSM/ORS routing, import a `canonical_json` dataset through `/api/v1/datasets` with:

- `coordinate_system` set to `wgs84`;
- every coordinate ordered as `[longitude, latitude]` (`x=longitude`, `y=latitude`);
- `distance_unit` set to `metres` and `time_unit` set to `seconds`;
- an explicit IANA timezone such as `Asia/Kolkata`;
- depot, customer, and fleet fields required by schema version `1`.

You do not manually place ORS responses in this folder. The backend creates credential-free,
content-addressed snapshots in `data/artifacts/` through `POST /api/v1/cost-snapshots`.
