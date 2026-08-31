# Phase-wise implementation plan

## Goal and success criteria

Build a reproducible VRPTW experimentation product that minimizes total travel
distance and vehicle count while enforcing vehicle capacity, customer time
windows, service time, depot return time, and fleet size. “Quantum-inspired”
means a classical algorithm whose update rule is motivated by quantum mechanics;
it does not imply quantum execution or advantage.

The project succeeds when every algorithm runs through the same parser, decoder,
constraints, seeds, evaluation budget, and metrics, and the results can be
repeated from stored experiment parameters.

## Modular monolith

```text
frontend/app
  experiment page + API client

backend
  routes      HTTP validation and response models
  vrptw       instance model, Solomon parser, decoder, evaluation
  optimizers  PSO/QPSO now; ACO/QACO later
  runs        SQLite experiment persistence
```

Module rule: routes call domain services; domain services call optimizers and
persistence. Optimizers never import FastAPI, SQLite, or frontend concepts.

## Phase 0 - reproducible baseline (implemented)

Deliverables:

- Bun-managed Next.js App Router frontend.
- uv-managed FastAPI backend with OpenAPI documentation.
- Solomon-format parser and embedded C101-mini smoke instance.
- Random-keys route representation and deterministic constraint-aware splitter.
- Classical PSO and QPSO using the same objective and evaluation budget.
- SQLite experiment history.
- Unit/API tests plus frontend lint and production-build checks.

Exit criteria: a clean checkout can run both algorithms, return every customer
exactly once, report feasibility separately, and persist the run.

## Phase 1 - benchmark correctness

1. Add the public Solomon 100-customer C1/C2/R1/R2/RC1/RC2 instances under a
   versioned `data/solomon/` directory with provenance and checksums. Do not use
   a Kaggle mirror as the canonical source when the original benchmark is
   available.
2. Add an instance upload endpoint and reject malformed IDs, negative demand,
   impossible single-customer routes, and inconsistent vehicle metadata.
3. Implement known-best-solution lookup and report relative gap:
   `100 * (candidate - best_known) / best_known`.
4. Run at least 30 seeds per algorithm/instance. Store seed, wall time,
   evaluations, convergence, distance, vehicles, violations, and environment.
5. Add greedy nearest-neighbor and OR-Tools baselines. Compare lexicographically:
   violations first, vehicle count second, distance third.

Exit criteria: benchmark tables are reproducible and no infeasible solution can
outscore a feasible solution.

## Phase 2 - experiment workbench

1. Add dataset upload/selection, parameter controls, route plotting, convergence
   plots, and side-by-side runs.
2. Add CSV/JSON export containing the complete experiment configuration.
3. Move long solves to a process worker only after request latency exceeds the
   deployment timeout; expose queued/running/completed/failed states.
4. Add cancellation and a maximum evaluation budget.

Exit criteria: a judge can select an instance, compare algorithms fairly, see
constraint status, and download enough data to reproduce the result.

## Phase 3 - ACO and quantum-inspired ACO

1. Implement standard Ant Colony System with pheromone evaporation, candidate
   lists, and feasibility-aware construction.
2. Lock the shared benchmark harness before adding QACO/PACO variants.
3. Define every “quantum-inspired” mechanism mathematically (for example,
   probability-amplitude representation or rotation-gate-inspired update), then
   add an ablation that removes it.
4. Match algorithms by objective evaluations and report median, IQR, best, and
   statistical effect size—not only the best seed.

Exit criteria: the claimed improvement survives multiple seeds and ablation;
otherwise report a negative result.

## Phase 4 - dynamic traffic and congestion

1. Introduce a time-dependent travel-time provider interface; keep Euclidean
   distance as the deterministic test provider.
2. Add replayable traffic scenarios before integrating a live traffic API.
3. Re-optimize only affected route suffixes and measure stability alongside
   distance: changed stops, lateness, compute time, and driver disruption.
4. Add stale-data timestamps, fallback travel times, rate-limit handling, and
   scenario provenance.

Exit criteria: traffic runs can be replayed offline and degradation is graceful
when the provider fails.

## Phase 5 - RL/QAOA research track

Keep this out of the production critical path. First use RL for bounded control
tasks such as adaptive parameter or shot allocation. Compare against fixed and
scheduled policies. Use QAOA only on reduced subproblems that fit simulator or
hardware limits, and never label simulator results as operational quantum
advantage.

Exit criteria: the RL state/action/reward, training/test split, classical
baseline, compute budget, and hardware/simulator details are explicit.

## Phase 6 - production and visibility

- Containerize the frontend and API; use one managed deployment environment.
- Run CI: backend tests, formatter/type checks, frontend lint/build, dependency
  audit, and a fixed-seed smoke solve.
- Retain SQLite for local demos. Move to Supabase Postgres only when shared
  remote access, dashboards, or concurrent writers are required.
- Add structured logs, request IDs, solve duration/evaluation counters, error
  rate, queue depth, database backups, and health/readiness endpoints.
- Load-test read endpoints and solve submission separately; optimizers are CPU
  work and must not block web workers at scale.

## Testing matrix

| Layer | Required checks |
| --- | --- |
| Parser | valid Solomon files; missing sections; duplicate IDs; bad numeric rows |
| Decoder | every customer once; capacity; time windows; depot return; fleet size |
| Optimizer | fixed-seed determinism; bounds; evaluation count; monotonic best curve |
| API | validation, error shape, persistence, CORS, timeout/cancellation |
| UI | keyboard operation, status/error states, responsive layout, result accuracy |
| Performance | p50/p95 submission latency, solve throughput, memory, 100/1000 nodes |
| Resilience | database unavailable, worker crash, malformed data, stale traffic API |

## Immediate next pull requests

1. Import and validate the full Solomon corpus plus best-known values.
2. Add 30-seed benchmark CLI and CSV output.
3. Add OR-Tools and greedy baselines.
4. Add instance upload and route visualization.
5. Add ACO only after the benchmark harness is locked.
