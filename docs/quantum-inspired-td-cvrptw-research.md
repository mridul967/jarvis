The strongest solution is not “apply QPSO directly to a road graph.” It is a layered Time-Dependent Capacitated Vehicle Routing Problem with Time Windows (TD-CVRPTW):

1. A road-network model produces departure-time-dependent travel costs.
2. A VRP layer decides vehicle assignment and customer order.
3. QPSO searches a continuous random-key representation.
4. A deterministic split decoder converts each particle into feasible routes.
5. An independent validator checks every constraint.
6. QPSO is evaluated against PSO, ACO, Hybrid Genetic Search, OR-Tools, and exact methods under equal budgets.
7. Dynamic routing is tested through replayable traffic scenarios before any live integration.

The crucial research finding is that strong evidence exists for QPSO on continuous optimization and for PSO/ACO on VRPTW, but I did not find a canonical, high-quality study establishing that QPSO is superior for large-scale time-dependent VRPTW. That is the research gap—and therefore the hypothesis your project should test, not a result you should assume.

# 1. What problem should actually be solved?

The original VRP assigns customers to vehicles and orders their visits while minimizing routing cost. It dates to Dantzig and Ramser’s truck-dispatching formulation. [Dantzig and Ramser, 1959](https://pubsonline.informs.org/doi/pdf/10.1287/mnsc.6.1.80)

Your actual operational problem is richer:

> Dynamic, time-dependent, capacitated vehicle routing with hard time windows and route-stability constraints.

It includes:

- Road-network topology.
- Multiple vehicles.
- Vehicle capacities.
- Customer demand.
- Service times.
- Time windows.
- Departure-time-dependent travel time.
- Traffic incidents.
- Optional new requests.
- Re-optimization during execution.
- A penalty for unnecessarily changing already communicated routes.

Solomon’s classical benchmark establishes the standard VRPTW structure and benchmark families, but its Euclidean/static travel costs are not real traffic. [Solomon, 1987](https://pubsonline.informs.org/doi/10.1287/opre.35.2.254)

Therefore, Solomon should be your algorithm-correctness benchmark—not your final traffic-congestion demonstration.

# 2. Graph and problem definition

Let the road network be a directed graph:

\[
G_R=(V_R,A_R)
\]

where:

- \(V_R\) contains intersections and road positions.
- \(A_R\) contains directed road segments.
- \(d_a\) is the length of edge \(a\).
- \(c_a\) is its traffic capacity.
- \(\tau_a(t,\omega)\) is travel time when entering edge \(a\) at departure time \(t\) under traffic scenario \(\omega\).

Customers and depots are mapped to graph vertices or snapped road positions.

The routing problem itself uses:

\[
G=(V,A)
\]

where:

\[
V=\{0\}\cup N
\]

- \(0\) is the depot.
- \(N=\{1,\ldots,n\}\) is the customer set.
- \(K=\{1,\ldots,m\}\) is the vehicle set.

For every customer \(i\):

- \(q_i\): demand.
- \([e_i,l_i]\): service time window.
- \(s_i\): service duration.

For every vehicle \(k\):

- \(Q_k\): capacity.
- \([E_k,L_k]\): vehicle operating interval.
- \(o_k\), \(r_k\): start and end depot if heterogeneous depots are later supported.

## Time-dependent shortest-path cost

Travel time between routing nodes \(i\) and \(j\) is not a single matrix entry. It is:

\[
\tau_{ij}(t,\omega)
=
\min_{p\in\mathcal P_{ij}}
\operatorname{ArrivalTime}(p,t,\omega)-t
\]

The travel time of every subsequent edge depends on when the preceding edge was completed.

The travel-time model should satisfy the FIFO property:

\[
t_1\le t_2
\implies
t_1+\tau_{ij}(t_1)
\le
t_2+\tau_{ij}(t_2)
\]

In plain language, departing later must not let an identical vehicle arrive earlier by overtaking itself mathematically. Ichoua, Gendreau, and Potvin specifically developed a time-dependent vehicle-dispatching model satisfying FIFO. [Ichoua, Gendreau, and Potvin, 2003](https://www.tdrouting.com/2003/vehicle-dispatching-with-time-dependent-travel-times/)

Any generated or learned travel-time profile must be validated for FIFO before an experiment is admitted.

# 3. Mathematical formulation

Define binary variables:

\[
x_{ijk}=
\begin{cases}
1 & \text{vehicle }k\text{ travels directly from }i\text{ to }j\\
0 & \text{otherwise}
\end{cases}
\]

\[
y_{ik}=
\begin{cases}
1 & \text{customer }i\text{ is served by vehicle }k\\
0 & \text{otherwise}
\end{cases}
\]

Continuous variables:

- \(a_{ik}\): service-start time at customer \(i\).
- \(u_{ik}\): cumulative load after visiting \(i\).

## Visit every customer exactly once

\[
\sum_{k\in K}y_{ik}=1
\qquad \forall i\in N
\]

## Incoming and outgoing flow

\[
\sum_{j\in V,\;j\ne i}x_{ijk}=y_{ik}
\qquad \forall i\in N,\; k\in K
\]

\[
\sum_{j\in V,\;j\ne i}x_{jik}=y_{ik}
\qquad \forall i\in N,\; k\in K
\]

## Depot constraints

\[
\sum_{j\in N}x_{0jk}\le 1
\qquad \forall k\in K
\]

\[
\sum_{i\in N}x_{i0k}
=
\sum_{j\in N}x_{0jk}
\qquad \forall k\in K
\]

## Vehicle capacity

A route-level form is:

\[
\sum_{i\in N}q_i y_{ik}\le Q_k
\qquad \forall k\in K
\]

For exact models, load-propagation constraints can provide stronger subtour elimination:

\[
u_{jk}
\ge
u_{ik}+q_j-M^Q_{ijk}(1-x_{ijk})
\]

\[
q_i\le u_{ik}\le Q_k
\]

## Time propagation

\[
a_{jk}
\ge
a_{ik}+s_i+
\tau_{ij}(a_{ik}+s_i,\omega)
-
M^T_{ijk}(1-x_{ijk})
\]

The \(M^T_{ijk}\) value must be derived from known time-window bounds:

\[
M^T_{ijk}
=
l_i+s_i+
\max_t\tau_{ij}(t,\omega)-e_j
\]

It must not be a hard-coded arbitrary large constant.

## Time-window constraints

\[
e_i y_{ik}\le a_{ik}\le l_i y_{ik}
\]

Equivalent indicator constraints are preferable when supported by the exact solver.

# 4. Do not combine the objectives naively

The problem statement lists:

- Travel time.
- Distance.
- Congestion.
- Operational cost.
- Convergence speed.

These are not interchangeable.

A route minimizing distance may use a congested road. A route minimizing present travel time may be longer. A route avoiding traffic may shift congestion elsewhere. A fast algorithm can produce a worse route.

## Recommended objective structure

Use a lexicographic objective:

\[
\min_{\text{lex}}
\left(
V(S),
K(S),
T(S),
C(S),
D(S),
R(S)
\right)
\]

where:

- \(V(S)\): number or severity of hard-constraint violations.
- \(K(S)\): number of vehicles used.
- \(T(S)\): total fleet travel time.
- \(C(S)\): congestion-related cost.
- \(D(S)\): total distance.
- \(R(S)\): route disruption after re-optimization.

Hard feasibility always dominates route quality:

\[
V(S)=0
\]

must be required for an operational solution.

This avoids arbitrary weights such as:

\[
10^6 \times \text{violations}+10^4 \times \text{vehicles}+\text{distance}
\]

unless those coefficients are mathematically derived.

## Congestion exposure

If traffic is exogenous—that is, your fleet is too small to change city traffic—define delay exposure:

\[
C_{\text{exposure}}(S)
=
\sum_{k}\sum_{(i,j)\in R_k}
\left[
\tau_{ij}(a_{ik}+s_i,\omega)
-
\tau^{\text{free}}_{ij}
\right]
\]

This measures how much traffic delay your vehicles experience.

It does not prove that your routing system reduced city congestion.

## Actual congestion reduction

To claim congestion reduction, your routing decisions must influence network load.

Let:

\[
f_a(t)=b_a(t)+r_a(t)
\]

where:

- \(b_a(t)\): background traffic.
- \(r_a(t)\): traffic caused by routed fleet vehicles.

Then edge travel time becomes:

\[
\tau_a(t)
=
\tau_a^0
\left[
1+\alpha_a
\left(
\frac{f_a(t)}{c_a}
\right)^{\beta_a}
\right]
\]

The parameters \(\alpha_a,\beta_a\) must be calibrated from data or declared as scenario parameters.

The system-level objective is then:

\[
\min
\sum_{a\in A_R}
\int_0^H f_a(t)\tau_a(t)\,dt
\]

or its simulation-based discrete equivalent.

Without this endogenous model or a traffic simulator, say:

> “The system minimizes fleet traffic exposure.”

Do not say:

> “The system reduces urban congestion.”

# 5. How QPSO fits the problem

QPSO was introduced as a continuous stochastic optimizer inspired by a quantum delta-potential model. It does not run on quantum hardware. The original method removes velocity vectors and samples positions around a probabilistic attractor. [Sun et al., 2004](https://ieeexplore.ieee.org/abstract/document/1330875/)

For particle \(r\), dimension \(j\), and iteration \(t\), define:

- \(X_{rj}^{t}\): current position.
- \(P_{rj}^{t}\): personal-best position.
- \(G_j^t\): global-best position.
- \(M_j^t\): mean personal-best position.

\[
M_j^t=\frac{1}{M}\sum_{r=1}^{M}P_{rj}^t
\]

The local attractor is:

\[
p_{rj}^t
=
\phi_{rj}P_{rj}^t+
(1-\phi_{rj})G_j^t
\]

where:

\[
\phi_{rj}\sim U(0,1)
\]

The QPSO update is:

\[
X_{rj}^{t+1}
=
p_{rj}^{t}
\pm
\beta_t
\left|M_j^t-X_{rj}^{t}\right|
\ln\left(\frac{1}{u_{rj}}\right)
\]

where:

\[
u_{rj}\sim U(0,1)
\]

and \(\beta_t\) is the contraction-expansion coefficient.

QPSO convergence theory was developed for its continuous stochastic search dynamics and benchmark functions. It does not automatically transfer to a discontinuous route decoder. [Sun et al., 2012](https://www.sciencedirect.com/science/article/pii/S0020025512000230)

That distinction must appear explicitly in the project.

# 6. Continuous QPSO to discrete vehicle routes

Use a random-key representation.

For \(n\) customers, a particle contains:

\[
X_r=(z_{r1},z_{r2},\ldots,z_{rn})
\]

The customer permutation is:

\[
\pi_r=\operatorname{argsort}(X_r)
\]

Example:

\[
X_r=(0.62,0.11,0.83,0.34)
\]

produces:

\[
\pi_r=(2,4,1,3)
\]

Random-key PSO has precedent in vehicle routing, including assignment and decoding strategies. [Ai and Kachitvichyanukul, 2009](https://www.sciencedirect.com/science/article/pii/S0305054808000774)

However, sorting alone gives one giant customer sequence. It does not decide route boundaries.

## Use a deterministic Split decoder

For permutation:

\[
\pi=(\pi_1,\ldots,\pi_n)
\]

construct an auxiliary acyclic graph with vertices:

\[
0,1,\ldots,n
\]

Add edge \((i,j)\) when the subsequence:

\[
(\pi_{i+1},\ldots,\pi_j)
\]

forms a feasible vehicle route.

The edge cost equals the lexicographic cost of that route.

Dynamic programming then finds the best feasible partition:

\[
F(j)=\min_{0\le i<j}
\left[
F(i)+c(i+1,j)
\right]
\]

This decoder finds the best route segmentation for that customer ordering.

It is materially stronger and more reproducible than greedily starting a new vehicle whenever the next customer does not fit.

## Local improvement

After decoding, apply the same local-search operators to every population-based algorithm:

- Relocate.
- Swap.
- 2-opt.
- 2-opt*.
- Cross-exchange.
- Or-opt.
- Time-window-aware route insertion.

The same operators and budgets must be used for PSO and QPSO. Otherwise, an apparent QPSO improvement may actually come from stronger local search.

Recent PSO research for VRPTW continues to emphasize the difficulty of adapting continuous swarm mechanics to discrete constrained routing. [N-CLPSO for VRPTW, 2024](https://www.sciencedirect.com/science/article/pii/S2210650223001980)

# 7. Proposed QPSO algorithm

Each experimental run should follow this logical procedure:

1. Load a validated scenario.
2. Construct time-dependent cost functions.
3. Generate the initial population.
4. Decode every particle with the same Split decoder.
5. Validate decoded routes independently.
6. Compare solutions lexicographically.
7. Update personal and global bests.
8. Apply the QPSO sampling equation.
9. Decode and improve the new solutions.
10. Record every improving incumbent and its timestamp/evaluation count.
11. Stop at the declared evaluation or time budget.
12. Revalidate the final solution.

## Initial population

Compare these initialization policies as an ablation:

- Entirely random keys.
- Solomon insertion heuristic converted to keys.
- Mixed population: heuristic seeds plus randomized solutions.
- Warm start from the previous decision epoch.

Do not silently seed QPSO with a good heuristic while giving PSO or ACO random initialization.

## QPSO parameters

Parameters must not be embedded as unexplained constants.

At minimum, declare:

- Population size \(M\).
- Evaluation budget.
- \(\beta_{\text{start}}\).
- \(\beta_{\text{end}}\).
- Schedule type.
- Local-search budget.
- Stagnation policy.
- Initialization policy.
- Random seed.

Parameter configurations should be tuned only on a designated training set, frozen, and then evaluated on unseen test instances.

# 8. Dynamic re-optimization

Dynamic routing should use rolling-horizon decision epochs:

\[
t_0,t_1,\ldots,t_R
\]

At epoch \(t_r\):

1. Receive a new traffic snapshot.
2. Receive new, cancelled, or changed requests.
3. Freeze completed service.
4. Freeze vehicles currently traversing an edge.
5. Preserve an explicit committed route prefix.
6. Re-optimize only the remaining decisions.
7. Validate the revised schedule.
8. Publish the new plan with a scenario and cost-model version.

Let:

- \(S^{r-1}\): previous plan.
- \(S^r\): revised plan.

Route disruption can be measured as:

\[
R(S^r,S^{r-1})
=
\lambda_1 N_{\text{reassigned}}
+
\lambda_2 N_{\text{reordered}}
+
\lambda_3\sum_i |\Delta a_i|
\]

For research, report the individual components instead of only the weighted value.

A dynamic solution should be compared against:

- Static route with no re-optimization.
- Periodic re-optimization.
- Event-triggered re-optimization.
- Warm-started re-optimization.
- Full re-optimization without stability protection.

Dynamic VRP research distinguishes problems based on how information arrives and how much future information is available. [Pillac et al., 2013](https://explore.openaire.eu/search/publication?pid=10.1016%2Fj.ejor.2012.08.015)

# 9. Algorithms that must be benchmarked

## Construction baseline

Use Solomon’s insertion heuristic or a nearest-feasible insertion method.

Purpose:

- Parser/constraint smoke test.
- Fast initial incumbent.
- Minimum standard that every advanced method must beat.

## Classical PSO

Use exactly the same:

- Encoding.
- Split decoder.
- Local search.
- Initialization.
- Evaluation budget.

Only the particle-update rule should differ from QPSO.

## QPSO

This is the experimental algorithm.

Primary question:

> Does its probabilistic update reach better feasible routes faster or more consistently?

## ACO/MACS

ACO is naturally discrete and constructs routes customer by customer. MACS-VRPTW uses cooperating colonies to minimize fleet size and distance hierarchically. [Gambardella, Taillard, and Agazzi, 1999](https://arodes.hes-so.ch/record/8230?ln=en)

Time-dependent ACO has been applied directly to TDVRPTW and real traffic-oriented settings. [Donati et al., 2008](https://www.sciencedirect.com/science/article/pii/S0377221706006345) A later hybrid combined ACO with insertion heuristics specifically for TDVRPTW. [Figliozzi-style TDVRPTW ACS study](https://www.sciencedirect.com/science/article/pii/S0305054810002327)

ACO may outperform QPSO because its representation matches the discrete routing structure better. That is a legitimate possible result.

## Hybrid Genetic Search/PyVRP

PyVRP implements a high-performance Hybrid Genetic Search and has reported state-of-the-art VRPTW results. It ranked first in the 2021 DIMACS VRPTW challenge. [Wouda, Lan, and Kool, 2024](https://pubsonline.informs.org/doi/10.1287/ijoc.2023.0055)

This is the strongest practical metaheuristic baseline.

If QPSO is compared only with a weak PSO implementation, the research conclusion will not be convincing.

## OR-Tools

OR-Tools provides an accessible constraint-programming routing baseline with time dimensions and time windows. [Official OR-Tools VRPTW documentation](https://developers.google.com/optimization/routing/vrptw)

Use it as a practical industry baseline, not automatically as an exact solver.

## Exact solver

For small and medium static instances, use branch-price-and-cut or a documented exact interface such as VRPSolverEasy. Modern exact VRPTW methods have solved the 56 Solomon 100-customer instances and many 200-customer Homberger instances. [Pecin et al., 2017](https://ideas.repec.org/a/inm/orijoc/v29y2017i3p489-502.html) [VRPSolverEasy](https://ideas.repec.org/a/inm/orijoc/v36y2024i4p956-965.html)

Exact methods provide:

- Optimal objective where solved.
- A lower bound where not solved.
- A trustworthy gap for heuristic evaluation.

# 10. Experimental programme

## Experiment A: static VRPTW correctness

Datasets:

- Solomon: 56 instances, 100 customers.
- Homberger–Gehring: 200, 400, 600, 800, and 1,000 customers.
- DIMACS VRPTW instances and cost conventions.

Homberger extends the Solomon structure to as many as 1,000 customers across clustered, random, and mixed spatial families. [Benchmark collection](https://neo.lcc.uma.es/radi-aeb/WebVRP/Problem_Instances/CVRPTWInstances.html)

Questions:

- Is every returned route feasible?
- Does QPSO beat PSO under equal evaluations?
- Does it approach HGS quality?
- How does performance degrade from 100 to 1,000 customers?

## Experiment B: controlled time-dependent VRPTW

Transform the static instances using declared speed profiles:

\[
v_a(t,\omega)
\]

\[
\tau_a(t,\omega)=\frac{d_a}{v_a(t,\omega)}
\]

Scenario families:

- Morning peak.
- Evening peak.
- Local incident.
- Corridor slowdown.
- Random edge closures.
- Spatially correlated congestion.
- Gradual demand increase.

All profiles must:

- Be versioned.
- Preserve FIFO.
- Declare the generation seed.
- Preserve the original static coordinates and customer constraints.
- Avoid undocumented cost substitutions.

## Experiment C: real road network

Use OpenStreetMap for topology and a routing engine for road paths.

OSRM is a high-performance routing engine built for OpenStreetMap road networks and supports fast path and matrix queries. [OSRM project](https://github.com/project-osrm/osrm-backend)

The road-network layer and the vehicle-order optimizer should remain separate:

```text
Road engine → paths and cost functions
VRP optimizer → assignment and visit ordering
```

OSRM alone does not solve the capacitated multi-vehicle optimization problem.

## Experiment D: closed-loop traffic simulation

Use SUMO to determine whether routing changes actually improve or worsen network congestion. SUMO is an open-source microscopic traffic simulator designed for large road networks. [SUMO documentation and reference publication](https://sumo.dlr.de/docs/)

Closed-loop procedure:

1. Load road graph and background demand.
2. Run baseline traffic simulation.
3. Insert fleet vehicles using baseline routing.
4. Repeat using PSO, QPSO, ACO, and HGS routes.
5. Measure network-wide travel time, delay, queues, and throughput.
6. Feed simulated traffic snapshots into the re-optimizer.
7. Repeat across identical seeds and demand scenarios.

CityFlow is an alternative for very large city-scale traffic experiments, especially if traffic-signal control or reinforcement learning is later introduced. [CityFlow paper](https://arxiv.org/abs/1905.05217)

# 11. Fair benchmarking protocol

## Equal budgets

Do not compare algorithms only by iteration count.

One QPSO iteration with 100 particles is not equivalent to one ACO iteration with 20 ants.

Primary budget:

\[
B_{\text{eval}}
=
\text{number of complete decoded solution evaluations}
\]

Also report:

- Wall-clock time.
- CPU time.
- Local-search move evaluations.
- Shortest-path queries.
- Peak memory.

The COCO benchmarking methodology recommends measuring runtime in evaluations required to reach defined quality targets. [Hansen et al., 2016](https://arxiv.org/abs/1605.03560)

## Repetitions

For each stochastic algorithm and instance:

- At least 30 independent seeds for the main study.
- Same seed schedule for algorithms where meaningful.
- Single-threaded benchmark mode.
- Same hardware.
- Same compiler/runtime versions.
- Fixed CPU-affinity policy if possible.
- No parameter tuning on test instances.

## Solution-quality metrics

Report:

\[
\text{Gap}(\%)
=
100
\frac{f(S)-f_{\text{BKS}}}{f_{\text{BKS}}}
\]

Also report:

- Feasibility rate.
- Vehicle count.
- Distance.
- Travel time.
- Congestion delay.
- Hard-window violations.
- Mean and maximum lateness for soft-window experiments.
- Route disruption.
- Best, median, IQR, and worst result.

## Anytime performance

Record every improving feasible incumbent:

\[
(t_1,f_1),(t_2,f_2),\ldots
\]

Use:

- Time to first feasible solution.
- Time to 10%, 5%, and 1% gaps.
- Area under the convergence curve.
- Primal integral.
- Empirical cumulative distribution of time-to-target.

The DIMACS VRPTW challenge used feasibility checking and primal-integral-style evaluation to reward algorithms that find strong solutions early, not just at termination. [DIMACS rules](https://dimacs.rutgers.edu/files/7616/3155/5530/VRPTW_Competition_Rules.pdf)

## Statistical analysis

Across benchmark instances:

- Friedman test for overall multiple-algorithm differences.
- Pairwise Wilcoxon signed-rank tests.
- Holm correction for multiple comparisons.
- Effect size, not only \(p\)-values.
- Bootstrap confidence intervals for median differences.

Stochastic optimizer outcomes are commonly non-normal, making nonparametric paired comparisons appropriate. [SOS benchmarking study](https://www.mdpi.com/2227-7390/8/5/785)

# 12. Required ablation experiments

Ablations are essential because a hybrid QPSO can improve for reasons unrelated to its quantum-inspired update.

Run:

1. PSO update + shared decoder.
2. QPSO update + shared decoder.
3. PSO + local search.
4. QPSO + local search.
5. QPSO with greedy splitting.
6. QPSO with dynamic-programming Split.
7. QPSO with random initialization.
8. QPSO with heuristic initialization.
9. Fixed \(\beta\).
10. Scheduled \(\beta\).
11. Without `mbest`.
12. Static QPSO.
13. Warm-started dynamic QPSO.
14. QPSO under static cost but evaluated under traffic.
15. QPSO optimized directly using time-dependent cost.

Only comparisons 1 versus 2 isolate the particle-update mechanism.

# 13. Falsifiable research hypotheses

## H1: solution quality

At equal feasible-solution evaluation budgets, discrete QPSO produces a lower median lexicographic gap than classical PSO.

## H2: convergence

QPSO reaches declared quality targets in fewer evaluations than PSO.

## H3: robustness

QPSO has lower cross-seed variance and a higher feasible-run rate.

## H4: scalability

The QPSO advantage, if present, remains measurable from 100 to 1,000 customers.

## H5: dynamic routing

Warm-started QPSO reduces fleet traffic delay relative to static routes under replayed traffic scenarios.

## H6: congestion

Closed-loop QPSO routing reduces total system travel time relative to the same traffic scenario using baseline routing.

Any of these hypotheses may be rejected. That does not make the project unsuccessful; a reproducible negative result is stronger than a forced superiority claim.

# 14. Computational complexity

For:

- \(M\): population size.
- \(I\): iterations.
- \(n\): customers.

The QPSO position update is:

\[
O(IMn)
\]

Random-key sorting costs:

\[
O(IMn\log n)
\]

A naive exact Split decoder can cost:

\[
O(IMn^2)
\]

Local search may dominate this depending on its neighborhoods and stopping policy.

Therefore, QPSO does not change the NP-hard worst-case nature of VRP. The defensible claim is:

> QPSO may reduce empirical time-to-quality or improve solution quality under a fixed computational budget.

Do not claim:

> QPSO reduces the computational complexity of VRP.

unless you prove a different asymptotic bound.

# 15. Research-backed software architecture

```text
Scenario and data layer
├── Solomon/Homberger/DIMACS importer
├── road-network importer
├── traffic snapshot importer
├── scenario generator
└── strict scenario validator

Network layer
├── directed road graph
├── path engine
├── time-dependent edge functions
├── FIFO validator
└── cost-oracle versioning

Optimization core
├── canonical problem model
├── lexicographic objective
├── Split decoder
├── independent feasibility validator
├── local-search engine
└── incumbent/event recorder

Solver implementations
├── construction heuristic
├── PSO
├── QPSO
├── ACO/MACS
├── HGS/PyVRP adapter
├── OR-Tools adapter
└── exact-solver adapter

Dynamic orchestration
├── event stream
├── vehicle-state tracker
├── committed-prefix manager
├── rolling-horizon controller
└── route-stability evaluator

Experiment platform
├── immutable run manifest
├── benchmark scheduler
├── seed manager
├── metrics calculator
├── statistical analysis
└── artifact exporter

Traffic simulation
├── SUMO scenario adapter
├── fleet route injector
├── traffic measurement collector
└── closed-loop replay coordinator

Application layer
├── FastAPI experiment API
├── run and scenario persistence
├── Next.js experiment interface
├── map and route visualization
└── comparison and convergence views
```

# 16. No-hard-coding/no-fallback policy

Every run must have an immutable manifest containing:

- Dataset checksum.
- Graph version.
- Traffic-scenario version.
- Cost-model version.
- Algorithm.
- Complete parameter set.
- Random seed.
- Evaluation/time budget.
- Constraint policy.
- Objective order or Pareto policy.
- Hardware and runtime metadata.
- Git commit.
- Start and finish timestamps.

Invalid or missing inputs must cause the run to be rejected.

Examples:

- Missing travel-time profile: reject; do not substitute Euclidean distance.
- Non-FIFO profile: reject; do not silently repair unless the repair is a separately versioned preprocessing operation.
- Missing vehicle capacity: reject.
- Unmapped customer: reject.
- Unknown algorithm parameter: reject.
- Infeasible customer even when served alone: reject the instance before optimization.
- Unavailable traffic API: mark the scenario unavailable; do not optimize using stale or invented traffic unless an explicitly selected, versioned replay scenario is requested.

# 17. Recommended research order

## Stage 1: scientific baseline

- Static Solomon parser and validator.
- Independent route validator.
- Construction heuristic.
- Exact solver on small cases.
- PSO and QPSO with shared decoder.
- Reproducible 30-seed benchmark.

## Stage 2: strong competition

- Dynamic-programming Split.
- Shared local search.
- ACO/MACS.
- PyVRP/HGS.
- DIMACS-style anytime evaluation.

## Stage 3: scale

- Homberger 200–1,000 customers.
- Memory and runtime profiling.
- Parallel experiment execution, while individual benchmark runs remain single-threaded.

## Stage 4: traffic

- FIFO-compliant synthetic time profiles.
- Static-route-versus-time-dependent-route comparison.
- Incident and peak-hour scenarios.

## Stage 5: road network

- OpenStreetMap network.
- OSRM path generation.
- Versioned time-dependent edge costs.
- Geographic route visualization.

## Stage 6: congestion claim

- Closed-loop SUMO experiments.
- Background traffic.
- Fleet route injection.
- Network-wide congestion metrics.

## Stage 7: dynamic operation

- Rolling-horizon re-optimization.
- Committed prefixes.
- Route-change metrics.
- Event replay.
- Operational latency tests.

# 18. Final recommendation

Build the product around a solver-independent canonical problem and benchmark harness, not around QPSO itself.

QPSO should be one research implementation inside the platform. The main scientific contribution should be:

> A reproducible discrete-QPSO framework for static and time-dependent VRPTW, using random-key encoding, an exact-for-order Split decoder, shared local search, strict feasibility validation, and closed-loop traffic simulation, evaluated fairly against PSO, ACO, HGS, practical constraint solvers, and exact methods.

That is considerably stronger than claiming that quantum inspiration automatically improves routing.

## Evidence limitations

- QPSO convergence results primarily concern continuous optimization; discrete decoding changes the search landscape.
- Solomon instances validate VRPTW optimization but do not validate real urban traffic.
- Simulated congestion reduction may not transfer directly to real traffic.
- Live traffic data introduces missingness, licensing, latency, geographic bias, and privacy considerations.
- Weighted multiobjective results are policy-dependent; Pareto or lexicographic reporting is more transparent.
- I did not find strong canonical evidence directly establishing QPSO superiority on large-scale TDVRPTW.

AI-assisted research tools were used to search, organize, and synthesize sources. Every cited source above should be independently checked again when producing the final academic report or competition submission.
