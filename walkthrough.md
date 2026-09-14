# Deterministic multi-agent traffic simulator walkthrough

This implementation delivers the first demonstration milestone as a replayable, synthetic Bengaluru traffic simulation. It deliberately stays inside the requested low-risk stack: NetworkX, the existing traffic/BPR conventions, typed Python actors, deterministic heuristics, JSONL, FastAPI polling, and a browser-rendered SVG map. It does not add Neo4j, SUMO, live traffic, or LLM calls.

## What is implemented

The new `backend/simulation/` package contains:

- `graph.py`: a directed 3x3 Bengaluru-like road mesh with 9 intersections, coordinates, road classes, capacities, and free-flow times. It also reads `data/vlsvrp/1040.vrp` for reproducible source metadata.
- `schemas.py`: `NodeAgent`, `VehicleState`, `Shock`, and `SimulationState` dataclasses.
- `generator.py`: seeded vehicle generation. Vehicle types, origin/destination pairs, loads, availability, and routes are deterministic.
- `shocks.py`: a morning peak plus an arterial incident beginning at 300 simulated seconds (08:45 when the run starts at 08:40).
- `engine.py`: the discrete 30-second clock, BPR-style congestion calculation, movement, route invalidation, agent pressure updates, and frame generation.
- `quantum_engines.py`: bounded research-derived candidate engines. `QACO22Engine` follows the Version 2.2 dynamic-interference/tunnelling ideas; `ADMRQPSOEngine` follows the three-swarm adaptive-diversity QPSO wave update. Both are classical, seeded route-candidate generators.
- `negotiation.py`: typed `RouteOffer` values, Pareto-dominance filtering, and a deterministic lexicographic tie-break.
- `audit.py`: append-only JSONL audit output.
- `agents.py` and `vehicles.py`: small runtime helpers for node agents and vehicle edge identity.

The simulator uses a seeded `random.Random`; it never samples from global process randomness. A run has up to 50 vehicles and 60 frames/ticks through the API, with the demo UI using 16 vehicles and 30 ticks.

## Traffic and negotiation flow

At each tick, the engine:

1. Activates shocks whose time window contains the current timestamp.
2. Counts vehicles on each directed edge.
3. Calculates edge travel time with the BPR expression `free_flow * (1 + alpha * (flow / capacity)^beta)`, then applies the peak and incident multipliers.
4. Updates node-agent queue, occupancy, and predicted pressure.
5. Re-negotiates at startup, every third tick, or whenever a vehicle route intersects an active incident.
6. Generates up to four shortest simple route candidates using current edge travel time.
7. Creates typed offers with predicted arrival, queue, energy, and spillback values.
8. Removes dominated offers and picks the remaining offer using arrival, queue, spillback, energy, and route ordering.
9. Advances vehicle progress across the selected route.
10. Captures a complete frontend frame and writes every decision to JSONL.

The quantum engines are candidate generators, not decision authorities. Peak ticks select ADMR-QPSO and incident ticks select QACO v2.2; Pareto filtering still commits the route. A full run with the demo defaults verifies both engine labels in the audit stream.

## API

Start the backend from the repository root:

```bash
./.venv/bin/python -m uvicorn backend.main:app --reload
```

Create a run:

```bash
curl -X POST http://localhost:8000/api/v1/simulations \
  -H 'content-type: application/json' \
  -d '{"seed":42,"vehicle_count":16,"ticks":30}'
```

The response contains `run_id`, frame count, vehicle count, seed, and the JSONL path. Fetch the complete replay with:

```bash
curl http://localhost:8000/api/v1/simulations/<run_id>
curl http://localhost:8000/api/v1/simulations/<run_id>/events
```

Runs are held in process memory for fast demo polling. The audit file is durable under `data/artifacts/simulations/<run_id>/events.jsonl`. A later persistence phase can index these files without putting a database in the simulation loop.

## Frontend visualization

Run the frontend with:

```bash
cd frontend
npm run dev
```

Open `/visualize`, click **Start simulation**, and the page will call the create endpoint and then fetch the full replay. The `TrafficMap` component renders the actual graph coordinates as SVG, colors live edges by congestion, sizes node-agent pressure halos, and animates vehicle markers while the replay timer advances. The Play/Pause control and timeline slider allow deterministic inspection of every frame. Clicking a vehicle shows its most recent negotiation event.

This is deliberately a local SVG map rather than Leaflet/MapLibre: the first milestone has no external tile dependency, works offline during a presentation, and still displays real graph geometry and dynamic state. The graph payload is ready to be swapped for GeoJSON or OSMnx output in the next phase.

## Synthetic data and regeneration

The checked-in VRP data is used from `data/vlsvrp/1040.vrp`; its dimension and capacity are shown in the UI and persisted in the run response. The compact road graph and traffic demand are generated in Python because a small Bengaluru road extract is not required for this milestone.

To regenerate a deterministic fixture and JSONL audit run explicitly:

```bash
./.venv/bin/python scripts/generate_demo_fixture.py
```

The script uses seed 42, 16 vehicles, and 30 ticks. The API accepts other bounded values for controlled experiments.

## Verification

The following checks pass in this workspace:

```bash
./.venv/bin/python -m py_compile backend/simulation/*.py backend/api/routes/simulations.py
cd frontend && ./node_modules/.bin/tsc --noEmit
cd frontend && ./node_modules/.bin/eslint app components lib
```

The local environment does not currently have `pytest` or `bun` on PATH. The added `tests/test_simulation.py` covers same-seed replay equality, incident activation, and JSONL run-id integrity; run it once pytest is installed in the project environment. The API route was verified by calling its FastAPI handler directly because the installed Starlette/httpx TestClient combination hangs in this environment.

## Deliberate boundaries

- GAT remains opt-in and is not used for routing decisions.
- QPSO/QACO remain candidate-engine integration points rather than per-node hot-loop work.
- No live traffic or ORS duration is presented as live data.
- No Graphify/Neo4j object is used as the operational road graph.
- No separate process or LLM is created per node.

## Implementation-plan checklist

This checklist covers every deliverable in the supplied plan. A checked item has an implementation and a verification command or deterministic smoke assertion. Items marked deferred are intentionally outside the first-demo acceptance boundary; they are not represented as completed features.

### Phase 1 — first demonstration

- [x] Synthetic 9-node Bengaluru-like directed graph — `build_bengaluru_graph()` returns 9 nodes and 24 directed edges; verified by the 30-frame run.
- [x] 10–50 deterministic vehicles — API bounds 1–50; verified with 16 vehicles and frame vehicle counts.
- [x] Discrete simulation clock — 30-second ticks; verified with 30 frames and timestamps 0–870 seconds.
- [x] Vehicle movement — progress, current edge, arrival status, and route are serialized in every frame; verified by comparing first and final frames.
- [x] Existing traffic/BPR convention — dynamic flow/capacity travel-time calculation with peak and incident multipliers; verified by live edge travel-time values in frames.
- [x] Peak-hour shock — deterministic `morning-peak`; verified in frame 0.
- [x] Incident shock at simulated 08:45 — `arterial-incident-0845` starts at 300 seconds; verified in frame 10.
- [x] Node-agent runtime — one typed `NodeAgent` per graph node with queue, occupancy, pressure, and policy; verified in API frame payloads.
- [x] Typed Pareto offers — `RouteOffer`, dominance filtering, and deterministic tie-break; verified by 59 `negotiation_decision` events in the default run.
- [x] QACO Version 2.2 candidate generation — pheromone memory, dynamic interference weighting, and tunnelling-inspired stochastic proposal; verified by `qaco_v2.2_dynamic_interference_tunneling` audit events during the incident.
- [x] ADMR-QPSO candidate generation — exploitation/exploration/robustness swarms, adaptive alpha, mbest, and QPSO wave update; verified by `admr_qpso_research` audit events during peak ticks.
- [x] Append-only JSONL audit — one file per run under `data/artifacts/simulations/<run_id>/events.jsonl`; verified by JSON parsing and run-id integrity test.
- [x] FastAPI polling API — POST run, GET full replay, GET events; handler smoke test returns 4 frames and event data.
- [x] Dynamic frontend map — SVG graph, congestion colors, pressure halos, moving vehicle markers, timeline, play/pause, vehicle selection, and event stream; verified by TypeScript, ESLint, and production build.
- [x] VRP input usage — `data/vlsvrp/1040.vrp` metadata is loaded into each run; verified in the frontend source card and result payload.
- [x] Synthetic-data regeneration script — `scripts/generate_demo_fixture.py`; verified by direct execution of `SimulationEngine` and audit output.

### Phase 2 — real road geometry

- [ ] OSMnx importer and GraphML/GeoJSON snapshots — deferred; the first demo intentionally uses the offline synthetic graph.
- [x] Offline GraphML/GeoJSON snapshot export and GraphML reload — `backend/simulation/snapshots.py` and `scripts/export_demo_snapshot.py` are implemented and verified by compilation; OSMnx remains optional for the later download adapter.
- [ ] District boundary configuration, vehicle-compatible filtering, OSM attribution, and snapshot hashes — deferred with the OSM importer.

### Phase 3 — GAT prediction

- [ ] Rollout dataset generator, temporal windows, training script, checkpoint management, and baseline comparison — deferred until rollout data is collected.
- [x] Rollout dataset generator — `backend/simulation/rollouts.py` and `scripts/generate_rollout_dataset.py` emit timestamped one-step future travel-time targets from simulation frames.
- [x] Untrained-GAT safety boundary and heuristic fallback — verified: the GAT route is lazy-loaded and returns an explicit 503 when PyTorch/checkpoints are unavailable; simulation routing does not consume GAT output.
- [ ] Confidence-aware trained GAT candidate ranking — deferred until trained checkpoints and validation scenarios exist.

### Phase 4 — optimizer portfolio expansion

- [x] Candidate-engine boundary and policy selection — verified by separate engine labels in audit records.
- [x] Bounded QPSO and QACO candidate caching/state within a run — verified by the deterministic default run.
- [x] Async simulation job abstraction — `POST /api/v1/simulations/jobs` and `GET /api/v1/simulations/jobs/{job_id}` use a bounded thread pool and replay result IDs.
- [ ] QACO/QPSO runtime-quality benchmark dashboard and OR-Tools fleet subproblem integration — deferred to benchmark work; OR-Tools is not placed in the per-tick loop.

### Phase 5 — scale and persistence

- [x] Replayable runs and durable JSONL artifacts — verified by audit path output and replay frames.
- [ ] Neo4j audit export, analyst query UI, Graphify integration, and read-only LLM explanation — deferred by the supplied plan’s first-demo boundary.

### Explicit exclusions checked

- [x] No Neo4j in the routing loop.
- [x] No LLM call per node.
- [x] No SUMO.
- [x] No live traffic claim.
- [x] No untrained GAT route decisions.
- [x] No process-per-node runtime.
