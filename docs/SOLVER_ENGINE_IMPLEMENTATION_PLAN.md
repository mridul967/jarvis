# Anywhere Door solver engine: detailed phase-wise implementation plan

## 1. Outcome and scope

Build a reproducible modular-monolith platform for static and dynamic Vehicle
Routing Problems with Time Windows (VRPTW). The platform will compare Greedy,
OR-Tools, PSO, QPSO, ACO, and a precisely defined quantum-inspired ACO (QACO)
under identical problem definitions, constraints, validation, seeds, and compute
budgets.

The system will support static Euclidean Solomon instances, OSM/ORS road costs,
exogenous traffic scenarios, endogenous fleet-induced congestion, and combined
traffic. QPSO and QACO are research hypotheses, not assumed winners. Negative
and statistically inconclusive results are valid outcomes.

Each implementation phase ends at an explicit pause gate. At that gate we will
explain the changes, equations, files, verification evidence, deliberate
omissions, and next phase. We will not begin the next phase until it is accepted.

## 2. Locked design decisions

### 2.1 Authoritative objective

Compare solutions lexicographically in this exact order:

1. hard-constraint violations;
2. unserved or multiply served customers;
3. vehicles used;
4. total lateness;
5. total travel time;
6. total distance;
7. congestion exposure.

The engine will compare a typed score tuple directly. It will not use a large
weighted penalty as a substitute for lexicographic comparison.

### 2.2 Traffic from the initial engine

The shared cost contract must support:

- static Euclidean Solomon costs;
- static OSM/ORS road costs;
- simulated or historical exogenous traffic;
- endogenous congestion caused by assigned vehicle flow;
- combined exogenous and endogenous traffic.

OpenRouteService is a routing provider, not a live-traffic provider. Runs must
be labelled `static`, `simulated`, `historical_replay`, or `live`. ORS-only
durations must never be labelled live.

### 2.3 Dynamic re-optimization

At each traffic event or re-optimization epoch:

- completed visits are immutable;
- current vehicle positions, times, and loads are immutable;
- each vehicle's next committed stop is immutable;
- only remaining route suffixes may change;
- the current solution supplies a warm start;
- teleportation or reordering executed work is invalid.

### 2.4 Initial constraints

The canonical model supports one depot; a fixed fleet; vehicle-specific
capacity, shift window, start/end node, and fixed cost; customer demand, service
duration, and hard service-start time window; delivery-only loads; exactly-once
service; and time-dependent asymmetric travel costs.

Pickups/deliveries, multiple depots, EV charging, driver breaks, and customer
priorities are separate future problem classes.

### 2.5 Data sources

Initial input adapters:

1. native Solomon text;
2. manually downloaded Kaggle-style Solomon CSV plus explicit fleet/capacity
   metadata;
3. canonical versioned JSON for custom and geographic datasets.

The importer never guesses capacity from a filename, silently supplies `200`,
or treats arbitrary columns by position as the practice prototype does.

### 2.6 OSM/ORS reproducibility

Every successful ORS response used by a solver becomes an immutable snapshot
containing request parameters, distance/duration matrices, unreachable pairs,
geometry where requested, retrieval time, attribution, and checksums. Benchmarks
consume snapshots and do not repeatedly call ORS.

The ORS key is backend-only configuration. It is never committed, logged,
persisted in a snapshot, returned by the API, or exposed to Next.js.

### 2.7 Experiment execution

FastAPI validates and enqueues experiments in SQLite. A separate Python worker
claims and executes jobs. The frontend polls job status and can cancel. Celery,
Redis, Kafka, and a distributed scheduler are excluded until measured load
requires them.

### 2.8 Hardware

CPU NumPy is the reproducible reference. This development Mac has an Apple GPU,
not an NVIDIA CUDA device. Metal/MPS may be explored after profiling. CUDA is
only valid on a separately documented NVIDIA environment.

## 3. Mathematical contract

### 3.1 Problem data

Let the directed graph be

\[
G=(V,A),\qquad V=\{0,1,\ldots,n\},
\]

where node `0` is the depot. Customer `i` has demand `q_i`, service-start window
`[e_i,l_i]`, and service time `s_i`. Vehicle `k` has capacity `Q_k`, shift
`[a_k,b_k]`, start node `o_k`, end node `d_k`, and fixed cost `c_k`.

For arc `(i,j)` and departure time `t`, distance and travel time are:

\[
d_{ij}\ge0,\qquad T_{ij}(t,\mathbf f)\ge0,
\]

where `f` is the flow state when endogenous congestion is active.

### 3.2 Schedule propagation

If service starts at `i` at time `B_ik`, then:

\[
A_{jk}=B_{ik}+s_i+T_{ij}(B_{ik}+s_i,\mathbf f),
\]

\[
B_{jk}=\max(e_j,A_{jk}).
\]

A route is time-feasible only if `B_jk <= l_j` for every customer and the
vehicle returns to its end node by `b_k`.

### 3.3 Coverage and capacity

\[
\sum_{i\in R_k}q_i\le Q_k,
\]

\[
\sum_k\mathbf1[i\in R_k]=1\quad\forall i\in V\setminus\{0\}.
\]

### 3.4 Exogenous traffic

An exogenous scenario supplies a positive time-indexed arc multiplier:

\[
T^{exo}_{ij}(t)=T^0_{ij}m_{ij}(t),\qquad m_{ij}(t)>0.
\]

Its intervals, interpolation, time zone, horizon, units, source, and checksum
are immutable metadata. A missing required interval is a validation error.

### 3.5 Endogenous congestion

The first complete implementation operates on the directed stop-to-stop graph
from an ORS snapshot. Each OD arc has declared capacity `C_ij`, flow `f_ij`, and
BPR parameters:

\[
T_{ij}(t,f_{ij})=T^{exo}_{ij}(t)
\left[1+\alpha_{ij}\left(\frac{f_{ij}}{C_{ij}}\right)^{\beta_{ij}}\right].
\]

`C_ij`, `alpha_ij`, and `beta_ij` are supplied by the scenario or an explicitly
versioned generator. They are not hidden constants. Results are labelled
OD-arc congestion, not calibrated street-segment traffic. OSM-edge refinement
can be added after this working model is measured.

### 3.6 Score

For solution `S`:

\[
F(S)=(H,U,K,L,TT,D,CE),
\]

where `H` is hard violations, `U` is coverage errors, `K` is vehicles, `L` is
lateness, `TT` is travel time, `D` is distance, and `CE` is congestion exposure.
Python tuple ordering decides quality. A scalar projection may be used only for
display and never to select the best solution.

## 4. Minimal modular-monolith design

Retain the current repository and grow modules only when a phase needs them:

```text
backend/
  api/routes/              HTTP schemas and endpoints
  core/                    settings, SQLite lifecycle, migrations
  datasets/                immutable versions and strict importers
  networks/                ORS client and cost snapshots
  traffic/                 scenarios and time-dependent costs
  vrptw/                   canonical domain, decoder, evaluator, validator
  optimizers/              solver functions and shared operators
  jobs/                    SQLite queue and worker
  experiments/             orchestration, benchmark, statistics
  runs/                    persisted run queries
frontend/
  app/(dashboard)/         datasets, experiments, results
  lib/api/                 typed API calls
  types/                   frontend transport types
tests/                     mirrors backend capabilities
```

Dependency direction:

```text
FastAPI routes -> application services -> domain/solver registry
                                      -> repositories
solvers        -> canonical domain + cost contract + validator types
domain         -> Python/NumPy only
frontend       -> versioned HTTP API only
```

Solvers never import FastAPI, SQLite, ORS, environment settings, or frontend
types.

### 4.1 Solver contract

A typed function is sufficient; do not create a service class hierarchy:

```python
def solve(
    problem: Problem,
    costs: CostSnapshot,
    parameters: SolverParameters,
    seed: int,
    budget: EvaluationBudget,
    warm_start: Solution | None = None,
    should_cancel: Callable[[], bool] | None = None,
) -> SolverResult: ...
```

`backend/optimizers/registry.py` is a small mapping from stable algorithm names
to functions. Unimplemented algorithms are not registered.

### 4.2 Shared solver result

Every solver returns its algorithm/implementation version, seed, normalized
parameters, best solution, independently computed evaluation, candidate count,
best-so-far convergence keyed by evaluations, runtime, cancellation state,
diagnostics, and warm-start provenance.

## 5. Phase 0 — audit, research, and grilling

**Status: complete.**

Included:

- read the current Anywhere Door backend and tests end-to-end;
- read every source/benchmark file under `/Users/vinodpandey/practice concepts`
  without modifying it;
- checked original/official Solomon, PSO, QPSO, ACS/MACS, QACO-style, OR-Tools,
  ORS, and OSM references;
- locked the design decisions above.

Reusable practice concepts: feasibility-aware probabilistic construction,
probability-guided ants, rotation-inspired updates, benchmark scripts, and route
visualization requirements.

Not copied: hard-coded capacity, positional CSV parsing, weighted vehicle
penalty, missing depot-return/fleet validation, random zero-probability fallback,
missing convergence output, relative API file paths, and solver-owned
feasibility claims.

**Pause gate:** completed and accepted.

## 6. Phase 1 — canonical domain, validator, and solver contract

### Goal

Make it impossible for algorithms to solve subtly different problems. Add no
new solver yet; migrate current PSO/QPSO through the shared contract.

### Files

- change `backend/vrptw/model.py`, `evaluate.py`, and `service.py`;
- add `backend/vrptw/validate.py` only if separation cannot stay clear in the
  existing evaluator;
- add `backend/optimizers/model.py` and `registry.py`;
- migrate `backend/optimizers/swarm.py` without deleting it until callers move;
- update `backend/api/schemas.py`;
- add focused `tests/vrptw/` and `tests/optimizers/test_contract.py`.

### Implementation

1. Add immutable vehicle, problem, route, solution, score, evaluation, budget,
   parameter, and solver-result dataclasses.
2. Preserve a convenience constructor for homogeneous Solomon fleets.
3. Give every route a vehicle ID and explicit start/end semantics.
4. Separate proposal from authority: decoders/solvers propose; the validator
   recomputes coverage, loads, timing, shifts, return, and all metrics.
5. Replace the million-point scalar violation penalty with tuple comparison.
6. Version every algorithm implementation.
7. Make convergence use candidate-evaluation counts.
8. Add cooperative cancellation to the common loop contract.
9. Keep Pydantic at HTTP boundaries and dataclasses in the domain.

### Tests

- missing, duplicated, and unknown customer IDs;
- capacity equality/overflow;
- waiting, late start, service-time propagation, and late depot return;
- asymmetric travel costs and heterogeneous vehicle shifts/capacities;
- feasible longer solution beats infeasible shorter solution;
- identical solution evaluates identically for every solver label;
- fixed-seed compatibility of current PSO/QPSO;
- exact candidate counts and monotonic best-so-far trace.

### Exit criteria

- current PSO/QPSO and API smoke paths use the new contract;
- no optimizer has private capacity/time-window logic;
- validator output is authoritative in persisted/API results;
- tests and Ruff pass.

### Pause after Phase 1

Explain domain types, score tuple, migrated call flow, files, verification, and
deferred work. Do not start data ingestion until accepted.

## 7. Phase 2 — immutable dataset registry and strict importers

### Goal

Admit manually downloaded Kaggle/Solomon and custom datasets without guessing
semantics.

### Files

- add `backend/datasets/model.py`, `importers.py`, `repository.py`, `service.py`;
- add `backend/api/routes/datasets.py` and register it;
- update API schemas and database initialization/migrations;
- add `tests/datasets/` fixtures and tests.

### Metadata

Persist immutable version ID, source/URL or user-upload marker, license and
attribution, original filename/media type/size/SHA-256, parser/version,
coordinate reference, units, time zone, fleet/customer counts, validation
status/errors, and normalized canonical checksum.

### Adapters

**Solomon text:** parse fleet/capacity and depot/customer table explicitly;
preserve double precision; Euclidean travel time is used only in declared
Solomon mode.

**Kaggle CSV:** match documented named columns after normalization; require
fleet size, capacity, and depot identity via sidecar JSON or upload form; use a
small documented header alias table; reject ambiguity.

**Canonical JSON:** require schema version, coordinate type, units, fleet,
customers, depot, and time semantics; WGS84 is `[longitude, latitude]`.

### API

- `POST /api/v1/datasets/validate` validates without persistence;
- `POST /api/v1/datasets` stores a valid immutable version;
- `GET /api/v1/datasets` lists metadata;
- `GET /api/v1/datasets/{version_id}` shows one version.

Never accept arbitrary server filesystem paths.

### Storage

Store original and normalized data content-addressably under configured artifact
storage. SQLite stores metadata and safe artifact IDs, not unchecked user paths.

### Tests and exit

Test native text, all six practice CSV families, harmless header differences,
missing metadata, duplicate IDs, missing depot, invalid numeric values/windows,
impossible single-customer service, WGS84 ranges, checksum stability, duplicate
upload, and upload bounds.

Exit when Kaggle CSV plus explicit metadata imports correctly, malformed inputs
cannot enter the queue, and no field/capacity is inferred silently.

### Pause after Phase 2

Demonstrate native text and CSV imports plus at least three expected rejections;
explain normalization and provenance.

## 8. Phase 3 — OSM/ORS snapshots and traffic models

### Goal

Create immutable road-cost snapshots and expose static, exogenous, endogenous,
and combined costs through one contract.

### Files

- add `backend/networks/ors.py` and `snapshots.py`;
- add `backend/traffic/model.py` and `costs.py`;
- add snapshot/scenario API routes;
- update settings/database;
- add `tests/networks/` and `tests/traffic/`.

### ORS flow

1. Require a validated WGS84 dataset.
2. Validate coordinates and routing profile.
3. Call ORS Matrix for durations/distances using backend authorization.
4. Partition requests to documented service limits and record block boundaries.
5. Reassemble and validate matrix shape, finiteness, and non-negativity.
6. Preserve unreachable pairs; never replace them with Euclidean values.
7. Fetch Directions geometry only when needed for displayed/selected routes.
8. Persist credential-free request, raw/normalized response, attribution,
   retrieval time, provider metadata, and checksums.
9. Reuse only an identical existing immutable snapshot checksum.

### Cost contract

```python
distance(i: int, j: int) -> float
travel_time(i: int, j: int, departure: float, flow: float = 0.0) -> float
reachable(i: int, j: int) -> bool
```

Euclidean, ORS static, exogenous, endogenous, and combined behavior should be
data/configurations over this contract, not a class hierarchy.

### Scenario validation

Exogenous data declares source type, zone/horizon, intervals, directed arcs,
positive multipliers, checksum, and generator seed/parameters if simulated.

Endogenous data declares arc capacities, alpha/beta, flow unit/interval,
assignment rule, tolerance, and maximum rounds. No unbounded fixed-point loop.

### Closed-loop assignment

Propagate schedules with current costs, aggregate flow per OD arc/time interval,
apply BPR, re-evaluate/re-optimize per experiment mode, and stop at declared
tolerance or maximum rounds. Store residual and convergence status.

### Tests and exit

Test auth placement without revealing the key, timeout and 400/403/413/429/503,
matrix block reconstruction, unreachable/snap failure, checksums, traffic
interval boundaries, BPR zero-flow/monotonicity, combined order, asymmetry,
cross-interval schedule propagation, and missing-data failure. Solver tests must
make no live network call.

Exit when a geographic dataset creates a reproducible snapshot and one fixed
solution evaluates correctly under all four traffic modes.

### Pause after Phase 3

Show secret-free snapshot metadata, all cost modes, one unreachable failure,
and equation-level traffic tests.

## 9. Phase 4 — SQLite jobs and worker

### Goal

Keep optimization outside FastAPI requests with the smallest restart-safe queue.

### Files

- add `backend/jobs/repository.py`, `worker.py`;
- add `backend/experiments/service.py`;
- add job/experiment routes;
- add `backend/tools/worker.py`;
- add database migrations and job/API tests.

### State machine

```text
queued -> running -> completed
                  -> failed
                  -> cancelled
queued ----------------> cancelled
```

Claims and transitions are transactional. A lease permits recovery after worker
crash without concurrent duplicate execution. Add a schema-version table and
migrate the existing `runs` algorithm constraint transactionally; do not delete
the current database.

Minimum metadata entities: dataset versions, cost snapshots, experiments, jobs,
and runs. Large matrices/traces are compressed immutable artifacts referenced by
checksum.

Worker behavior: one process, cooperative cancellation, evaluation/seed-based
progress, graceful SIGINT/SIGTERM, structured safe errors, and explicit retry
policy. CLI: `uv run python -m backend.tools.worker`.

API: submit experiment, get job, cancel job, and get experiment/runs. Support an
explicit idempotency key.

### Tests and exit

Test atomic claim, invalid transitions, cancellation, stale lease/restart,
structured failure, API responsiveness during CPU work, and idempotent submit.

Exit when jobs survive API restart, cancellation works, and FastAPI no longer
runs full solver loops directly.

### Pause after Phase 4

Demonstrate queue, progress, cancellation, recovery, and migration; explain why
Redis/Celery is not yet justified.

## 10. Phase 5 — Greedy and OR-Tools baselines

### Goal

Establish deterministic/simple and practical constraint-solver baselines before
experimental solvers.

### Files

- add `backend/optimizers/greedy.py`, `ortools_solver.py`;
- register both;
- add tests;
- add OR-Tools to `pyproject.toml`/lock only now.

### Greedy feasible insertion

Start empty; evaluate each unserved customer at every vehicle/insertion
position; rank by canonical score delta; use stable customer/vehicle/position
tie-breaks; select the minimum; fail explicitly if a required customer cannot be
served. This is more meaningful for VRPTW than nearest neighbor alone.

### OR-Tools

Build routing manager/model from canonical data. Register directed cost
callbacks, time/waiting dimension, shifts/windows, and vehicle-specific
capacities/fixed costs. Declare time/search limit and supported seed. Extract
routes, then independently validate them. Record OR-Tools version and complete
search parameters.

Initial OR-Tools dynamic comparisons use a declared frozen departure-epoch
snapshot; time-varying execution is evaluated by the external simulator and
labelled accordingly.

### Tests and exit

Test deterministic output, tiny exhaustive optimum, waiting, heterogeneous
capacity, unreachable arc, independent OR-Tools validation, and identical input
checksums across solvers.

Exit when both run through jobs/shared results and match exhaustive ground truth
on tiny cases.

### Pause after Phase 5

Present routes, validator output, runtime/evaluations, and optimality fixtures.

## 11. Phase 6 — PSO and QPSO

### Goal

Split current swarm code into auditable solvers sharing random keys, decoder,
initialization, warm start, and budgets.

### Representation

For `n` remaining customers, `x in [0,1)^n` defines stable order

\[
\pi=\operatorname{argsort}(x).
\]

A deterministic split decoder assigns the order to vehicles while checking
capacity/schedules. Decoder versions are explicit. Warm starts convert current
suffix order to evenly spaced keys and apply seeded bounded perturbation.

### PSO

\[
v_{id}^{t+1}=\omega v_{id}^{t}
+c_1r_1(p_{id}-x_{id}^t)+c_2r_2(g_d-x_{id}^t),
\]

\[
x_{id}^{t+1}=\operatorname{bound}(x_{id}^t+v_{id}^{t+1}).
\]

Boundary/velocity rules are stored parameters.

### QPSO

\[
p_{id}=\phi_{id}pbest_{id}+(1-\phi_{id})gbest_d,
\]

\[
mbest_d=M^{-1}\sum_i pbest_{id},
\]

\[
x_{id}^{t+1}=p_{id}\pm
\beta_t|mbest_d-x_{id}^t|\ln(1/u_{id}),
\]

with `u` strictly in `(0,1)`, independent signs, and stored beta schedule.

### Files and fairness

Add `pso.py`, `qpso.py`, `random_keys.py`, and a VRPTW decoder; remove combined
`swarm.py` only after migration. Use identical initial particles for paired
seeds, decoder, validation, evaluation budget, warm start, and local-search
mode. Main comparison has no solver-specific heuristic seed.

### Tests and exit

Test fixed-seed determinism, finite bounded keys, safe logarithm, monotonic best,
exact counts, cancellation, exactly-once decoding, paired initialization, and
controlled one-step equations.

Exit when PSO/QPSO differ only in update logic and both support every cost mode.
Make no superiority claim from a single seed/instance.

### Pause after Phase 6

Explain equations, shared/different code, paired fairness, tests, and preliminary
observations without declaring a winner.

## 12. Phase 7 — Ant Colony System

### Goal

Implement a discrete routing baseline and freeze it before QACO ablation.

### Construction

For feasible candidate set `N_i`, use a documented heuristic such as

\[
\eta_{ij}=\frac{1}
{(\epsilon+T_{ij}(t))(\epsilon+slack_j)(1+congestion_{ij})}.
\]

ACS exploits when `q <= q_0`:

\[
j=\arg\max_{h\in N_i}\tau_{ih}^{a}\eta_{ih}^{b},
\]

otherwise:

\[
P_{ij}=\frac{\tau_{ij}^{a}\eta_{ij}^{b}}
{\sum_{h\in N_i}\tau_{ih}^{a}\eta_{ih}^{b}}.
\]

Invalid or zero total weights produce a diagnostic failure, not an unrecorded
random fallback.

Local/global updates:

\[
\tau_{ij}\leftarrow(1-\xi)\tau_{ij}+\xi\tau_0,
\]

\[
\tau_{ij}\leftarrow(1-\rho)\tau_{ij}+\rho\Delta\tau_{ij}.
\]

Every customer choice checks capacity, time, and end-depot reachability. Fleet
exhaustion yields an explicit partial/infeasible solution. Candidate order is
stable before seeded selection.

### Files, tests, exit

Add `aco.py` and shared `ant_construction.py`; test probability normalization,
both selection branches, updates, depot return, finite fleet, invalid weights,
determinism, best-so-far monotonicity, and shared validator use.

Exit when ACS supports all cost modes under comparable candidate budgets and
has no private objective/constraint implementation.

### Pause after Phase 7

Demonstrate probabilities, updates, constraints, budget parity, and freeze the
ACS version used by QACO ablations.

## 13. Phase 8 — QACO

### Goal

Implement the agreed classical quantum-inspired ACS variant and compare it with
the frozen ACS baseline.

### Representation

For directed edge `(i,j)`:

\[
\theta_{ij}\in[\theta_{min},\theta_{max}]\subset(0,\pi/2),
\]

\[
\alpha_{ij}=\cos\theta_{ij},\quad
\beta_{ij}=\sin\theta_{ij},\quad
q_{ij}=|\beta_{ij}|^2=\sin^2\theta_{ij},
\]

so `|alpha|^2 + |beta|^2 = 1`.

Transition:

\[
P_{ij}=\frac{q_{ij}^{a}\eta_{ij}^{b}}
{\sum_{h\in N_i}q_{ih}^{a}\eta_{ih}^{b}}.
\]

Only pheromone representation/update differs from ACS.

### Rotation update

For best-solution target `y_ij in {0,1}`:

\[
\Delta\theta_{ij}=\gamma_t(y_{ij}-q_{ij}),
\]

\[
\begin{bmatrix}\alpha'\\\beta'\end{bmatrix}=
\begin{bmatrix}
\cos\Delta\theta&-\sin\Delta\theta\\
\sin\Delta\theta&\cos\Delta\theta
\end{bmatrix}
\begin{bmatrix}\alpha\\\beta\end{bmatrix}.
\]

Probability bounds preserve exploration. Gamma schedule, bounds, target policy,
and restart policy are persisted parameters. No quantum hardware/library is
used; the solver is labelled `quantum-inspired-classical`.

### Required ablations

1. frozen scalar-pheromone ACS;
2. amplitude QACO with rotation;
3. QACO initialization with rotation disabled;
4. any mixed update only if mathematically defined;
5. all variants in raw and shared-local-search modes.

### Tests and exit

Test normalization, probability bounds, positive/negative/zero rotation,
identical shared construction path, determinism, and single-component ablation.

Exit when the mechanism is stored with the result and tied, negative, and
positive comparisons follow the same reporting path. Never use “quantum
advantage” for this classical method.

### Pause after Phase 8

Show rotation tests and the full ablation matrix; report results without bias.

## 14. Phase 9 — shared local search

### Goal

Report solvers both raw and hybridized with the identical deterministic
improvement pipeline.

Implement, in order: intra-route 2-opt, inter-route relocate, and inter-route
swap. Evaluate every move through shared costs/validator. Use stable move order,
explicit first/best-improvement policy, and fixed move-evaluation budget.

Modes:

- `raw`: no local search;
- `shared_ls`: same operators/order/budget for compatible solvers.

Report local-search evaluations separately and include them in total budget when
the comparison equalizes total work.

Tests ensure coverage preservation, infeasible-move rejection, strict score
improvement, determinism, time-dependent re-propagation, and absence of
solver-specific hidden operators.

### Exit and pause

Exit when Greedy, PSO, QPSO, ACO, and QACO all support raw/shared-LS and reports
separate optimizer from local-search gains. Pause with before/after examples and
budget accounting.

## 15. Phase 10 — dynamic replay and suffix re-optimization

### Goal

Execute route plans across traffic events without rewriting history.

At every epoch persist scenario time; vehicle position/time/load; completed
customers; committed next stops; remaining customers; traffic interval/flows;
previous solution checksum; and trigger event.

Events include periodic epochs, multiplier changes, incident start/end, arrival
or service completion, and manual request. Warm-start adapters preserve immutable
prefixes/commitments and translate remaining order into solver state.

If a committed movement becomes unreachable, mark the simulation blocked and
apply only an explicitly selected incident policy; never teleport or silently
change the commitment.

Metrics: executed time/distance, planned-realized arrival error, lateness,
congestion exposure, re-optimization count, stops moved between vehicles, route
edit distance, commitment violations, compute latency, and BPR residual.

Tests cover immutable prefixes/next stops, exactly-once service across epochs,
load propagation, deterministic equal-time events, warm/cold provenance,
incident failure, and all traffic combinations.

### Exit and pause

Exit when a replay is fully deterministic and auditable by epoch. Pause with one
incident replay showing fixed prefixes, changed suffixes, traffic, and stability.

## 16. Phase 11 — benchmark and statistics engine

### Solver/dataset matrix

Solvers: Greedy, OR-Tools, PSO, QPSO, ACS, QACO.

Datasets: Solomon C1/C2/R1/R2/RC1/RC2; Kaggle mirrors verified by metadata and
checksum; selected Homberger 200–1,000 instances; geographic OSM/ORS instances;
and all declared traffic modes.

### Fairness

- deterministic baselines once where truly deterministic;
- 30 paired seeds for stochastic solvers;
- equal candidate-solution evaluation budgets;
- identical local-search mode/budget;
- single-threaded individual runs;
- parallelism only across independent runs;
- separate tuning and held-out test manifests;
- convergence indexed by evaluations;
- wall time secondary to quality/evaluations.

Persist OS/architecture, Python/packages, git commit and dirty flag, CPU/device,
thread settings, solver version, and all dataset/snapshot/scenario/config hashes.

Report feasible rate; median/IQR/best/worst; convention-specific benchmark gap;
evaluations/time to target; convergence area where defined; runtime/memory;
dynamic stability/latency; and BPR residual.

Statistics: paired Wilcoxon signed-rank, declared effect size, Holm multiple-test
correction, seeded bootstrap confidence intervals when used, and explicit ties,
failures, and infeasible runs. Never conclude from only the best seed.

SINTEF's hierarchical double-precision convention must not be mixed with
CVRPLIB/DIMACS rounding or monolithic objectives.

### Exit and pause

Exit when a manifest reproduces the run matrix and summaries regenerate only
from raw persisted results. Pause with seed/budget evidence, raw artifact,
summary/statistics, and honest negative/inconclusive interpretation.

## 17. Phase 12 — FastAPI and Next.js workbench

### Backend capabilities

Dataset validate/upload/list/detail; ORS snapshot creation/status/detail;
traffic scenario validate/create/list/detail; experiment submit/detail; job
status/cancel; run list/detail; benchmark submit/detail/export; health/readiness.

### Frontend

**Datasets:** upload formats/metadata, row/field errors, source/checksum/units/
fleet/version. Never expose ORS key.

**Network/traffic:** create ORS snapshot, select profile, upload/generate
exogenous scenario, configure explicit endogenous inputs, show provenance and
OSM attribution.

**Experiments:** choose immutable dataset/snapshot/scenario, solver,
raw/shared-LS, seed set, and budget; preview normalized config; show full job
state and cancellation; compare only equal input checksums.

**Results:** validator/score components, OSM or Euclidean routes, schedule/load
timeline, convergence by evaluations, traffic/re-optimization timeline, raw and
statistical results, reproducible JSON/CSV export.

Reuse existing App Router, colocated components, and API clients. Server
components fetch initial data; client components own interaction. Add a map
dependency only when implementing the map. Loading/empty/error/cancel states and
keyboard accessibility are required. The browser never recomputes feasibility.

### Exit and pause

Verify backend contracts, frontend lint/build, and the browser smoke flow:
upload -> snapshot -> submit -> worker -> result. Pause with the end-to-end demo,
provenance/security checks, and errors/cancellation.

## 18. Phase 13 — profiling and optional acceleration

Profile validator/schedule, split decoder, batched PSO/QPSO evaluation,
ACO/QACO construction, local search, and artifact persistence—in that order.

CPU first: precompute immutable arrays, batch with NumPy only where semantics
remain identical, remove hot-loop object lookup only when measured, and cache
only immutable checksum-keyed work.

Only after a measured batched bottleneck may we add an accelerator backend:
Metal/MPS on this Mac or CUDA on an NVIDIA host. Keep CPU validation authoritative
and record device/backend/precision/version plus transfer/compile overhead. Do
not add PyTorch, JAX, CuPy, or MLX solely to claim GPU support.

Scale on Solomon 25/50/100 and Homberger 200/400/600/800/1,000; track memory,
runtime, cancellation latency, snapshot block behavior, and SQLite metadata
performance.

### Exit and pause

Every optimization needs before/after profiles and identical validator output.
Keep acceleration only for net end-to-end gain. Pause with evidence or an honest
decision that GPU is not useful.

## 19. Phase 14 — production and Supabase visibility

Containerize Next.js, FastAPI, and worker as separate processes from this
repository. Keep SQLite/artifact storage for local development. Introduce
Supabase/Postgres only for shared visibility/concurrent workers, and object
storage for large immutable artifacts.

CI: Ruff, backend tests, fixed-seed smoke benchmark, frontend lint/build,
dependency/secret scan, and migration from a previous-schema fixture.

Observability: request/job/run IDs, queue depth/age, submission latency, solve
duration/evaluations, feasible candidate rate, worker failures/cancellation, ORS
status/quota errors without keys, database readiness, and artifact health.

Fail explicitly: absent key disables new ORS ingestion but existing snapshots
remain usable; ORS/quota failure fails snapshot creation; missing traffic fails
validation; worker crashes follow leases; corrupt checksums block runs; database
failure blocks writes; frontend never invents fallback results.

### Exit and pause

Require clean deployment, backup/restore drill, separated API/solver load tests,
resilience evidence, and proof that Supabase does not alter solver semantics.

## 20. Cross-phase verification matrix

| Layer | Evidence |
| --- | --- |
| Domain | immutable types, units, IDs, vehicle/customer validation |
| Parser | valid/malformed format fixtures; no inferred metadata |
| Snapshot | checksums, ORS validation, unreachable pairs, no leaked key |
| Traffic | interval boundaries, BPR monotonicity, missing-data failure |
| Validator | coverage, load, time, shift, depot return, dynamic/asymmetric costs |
| Decoder | permutation preservation, deterministic split, warm-start validity |
| Solver | fixed seed, equation-level step, count, monotonic best, cancellation |
| Local search | feasibility, strict improvement, fixed budget |
| Dynamic | immutable history, commitment, event order, replayability |
| Jobs | atomic claim, state machine, cancellation, crash recovery |
| API | validation/error schema, secret isolation, safe artifacts |
| Frontend | workflow, errors/status, accessibility, provenance |
| Benchmark | paired seeds, equal budgets, raw results, regenerated statistics |
| Performance | profiles, memory, submission latency, solve throughput |
| Resilience | ORS/database/worker/artifact failures without invented fallback |

## 21. Mandatory phase handoff format

After every phase, stop and provide:

1. outcome;
2. files added/changed/moved/removed;
3. equations and contracts implemented;
4. commands run and exact verification result;
5. one reproducible example;
6. ponytail omissions and the condition that would justify them;
7. scientific/engineering limitations;
8. proposed next-phase scope without starting it.

## 22. Immediate next phase

Implement **Phase 1 only**:

- canonical heterogeneous problem/solution models;
- lexicographic score;
- independent validator;
- common budget/parameter/result types;
- current PSO/QPSO compatibility;
- focused domain and contract tests.

Do not add ORS, OR-Tools, ACO, QACO, jobs, GPU libraries, Supabase, or frontend
screens during Phase 1. Their correctness depends on this foundation.

## 23. Primary and official references

- Solomon VRPTW paper: <https://pubsonline.informs.org/doi/10.1287/opre.35.2.254>
- SINTEF Solomon convention/BKS:
  <https://www.sintef.no/projectweb/top/vrptw/100-customers/>
- CVRPLIB Solomon/Homberger catalogue:
  <https://galgos.inf.puc-rio.br/cvrplib/en/instances/2>
- Original PSO: <https://doi.org/10.1109/ICNN.1995.488968>
- Original QPSO: <https://ieeexplore.ieee.org/document/1330875>
- Ant Colony System: <https://doi.org/10.1109/4235.585892>
- MACS-VRPTW:
  <https://aris.supsi.ch/entities/publication/b7e86cbb-4b9f-4e91-92f5-3203514451d9>
- Probability-amplitude/rotation QACO precedent:
  <https://www.nature.com/articles/s41598-018-31254-3>
- Official OR-Tools VRPTW guide:
  <https://developers.google.com/optimization/routing/vrptw>
- Official ORS Matrix guide:
  <https://giscience.github.io/openrouteservice/v8.2.0/api-reference/endpoints/matrix/>
- Official ORS travel-speed model:
  <https://giscience.github.io/openrouteservice/technical-details/travel-speeds/>
- Official ORS/OSM data-source documentation:
  <https://giscience.github.io/openrouteservice/run-instance/data>

