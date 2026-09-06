/**
 * Mock Data Engine for SIH 2026 Egreen Quanta
 * Quantum-Inspired Traffic and Vehicle-Routing Optimization Platform.
 *
 * All datasets and simulation models are typed local mock implementations.
 * No real solver or map hardware connections exist in this milestone.
 */

import {
  DecisionEvent,
  ObjectiveProfile,
  ResultStatus,
  RoutingMode,
  SolverId,
  SolverRegistryItem,
  ValidationReport,
} from "./types";

export interface DatasetOption {
  id: string;
  name: string;
  nodeCount: number;
  edgeCount: number;
  snapshotId: string;
  description: string;
}

export const DATASET_OPTIONS: DatasetOption[] = [
  {
    id: "delhi-ncr",
    name: "Delhi NCR sample network (synthetic, 40 nodes)",
    nodeCount: 40,
    edgeCount: 68,
    snapshotId: "delhi-ncr-synth-040",
    description: "Arterial corridors with high-density ring-road intersections and synthetic peak delays.",
  },
  {
    id: "bengaluru-grid",
    name: "Bengaluru synthetic grid (25 nodes)",
    nodeCount: 25,
    edgeCount: 44,
    snapshotId: "bengaluru-grid-025",
    description: "Bottleneck corridors modeling outer ring road chokepoints and variable signal delay.",
  },
  {
    id: "small-demo",
    name: "Small demo network (9 nodes)",
    nodeCount: 9,
    edgeCount: 16,
    snapshotId: "demo-mesh-009",
    description: "Compact 3x3 planar mesh for exact baseline comparison and rapid inspection.",
  },
];

export const ROUTING_MODES: { id: RoutingMode; label: string; description: string }[] = [
  {
    id: "casp",
    label: "CASP — Congestion-Aware Shortest Path",
    description: "Single origin-destination routing incorporating non-linear BPR congestion costs.",
  },
  {
    id: "vrptw",
    label: "VRPTW — Vehicle Routing with Time Windows",
    description: "Multi-vehicle customer delivery with capacity, time windows, and service durations.",
  },
];

export interface AlgorithmOption {
  id: SolverId;
  name: string;
  family: string;
  accent: "amber" | "teal";
  badge: string;
  description: string;
}

export const VISUALIZER_ALGORITHMS: AlgorithmOption[] = [
  {
    id: "qaco_local",
    name: "QACO",
    family: "Quantum-inspired Ant Colony",
    accent: "teal",
    badge: "Quantum-inspired",
    description: "Local route candidate generation exploring combinations with quantum rotation updates.",
  },
  {
    id: "qpso_policy",
    name: "QPSO",
    family: "Quantum-inspired Particle Swarm",
    accent: "teal",
    badge: "Quantum-inspired",
    description: "Global parameter and routing policy search with delta-potential well behavior.",
  },
  {
    id: "sbm_assignment",
    name: "SBM",
    family: "Simulated Bifurcation",
    accent: "teal",
    badge: "Quantum-inspired",
    description: "Experimental binary combinatorial subproblem search modeled as an Ising spin Hamiltonian.",
  },
  {
    id: "dijkstra",
    name: "Dijkstra (baseline)",
    family: "Classical Deterministic",
    accent: "amber",
    badge: "Baseline",
    description: "Deterministic single-source shortest path baseline with dynamic traffic edge weighting.",
  },
];

export const TRAFFIC_CONDITIONS = [
  { id: "normal", label: "Normal flow", multiplier: 1.05, incidentFactor: 1.0 },
  { id: "peak", label: "Peak congestion", multiplier: 1.68, incidentFactor: 1.25 },
  { id: "incident", label: "Incident on arterial", multiplier: 2.15, incidentFactor: 1.9 },
  { id: "volatility", label: "Mixed traffic volatility", multiplier: 1.42, incidentFactor: 1.4 },
];

export const OBJECTIVE_PROFILES = [
  { id: "min_time", label: "Minimize travel time", timeWeight: 1.0, congestionWeight: 0.2 },
  { id: "balance", label: "Balance time and congestion", timeWeight: 0.7, congestionWeight: 0.8 },
  { id: "avoid_tolls", label: "Avoid tolls", timeWeight: 0.8, congestionWeight: 0.4 },
  { id: "feasibility_first", label: "Fleet feasibility first", timeWeight: 0.5, congestionWeight: 0.5 },
];

// Specification §18: Initial Solver Registry
export const SOLVER_REGISTRY: SolverRegistryItem[] = [
  {
    id: "dijkstra",
    name: "DijkstraSolver",
    family: "shortest_path",
    role: "Baseline shortest-path solver",
    statusLabel: "Baseline",
    isQuantum: false,
    accent: "amber",
  },
  {
    id: "astar",
    name: "AStarSolver",
    family: "shortest_path",
    role: "Heuristic shortest-path solver",
    statusLabel: "Production",
    isQuantum: false,
    accent: "amber",
  },
  {
    id: "greedy_fleet",
    name: "GreedyFleetSolver",
    family: "classical_heuristic",
    role: "Fast fleet-routing fallback",
    statusLabel: "Fallback",
    isQuantum: false,
    accent: "amber",
  },
  {
    id: "hill_climbing",
    name: "HillClimbingFleetSolver",
    family: "classical_heuristic",
    role: "Local improvement and route polishing",
    statusLabel: "Production",
    isQuantum: false,
    accent: "amber",
  },
  {
    id: "ortools_vrptw",
    name: "OrToolsVrptwSolver",
    family: "classical_heuristic",
    role: "Production fleet-routing baseline",
    statusLabel: "Production",
    isQuantum: false,
    accent: "amber",
  },
  {
    id: "cplex_vrptw",
    name: "CplexVrptwSolver",
    family: "exact_mip",
    role: "Exact small-instance validation",
    statusLabel: "Exact small-instance",
    isQuantum: false,
    accent: "amber",
  },
  {
    id: "qaco_local",
    name: "QacoFleetCandidateSolver",
    family: "qaco",
    role: "Local route candidate generation",
    statusLabel: "Experimental",
    isQuantum: true,
    accent: "teal",
  },
  {
    id: "qpso_policy",
    name: "QpsoFleetPolicySolver",
    family: "qpso",
    role: "Quantum-inspired parameter or policy search",
    statusLabel: "Experimental",
    isQuantum: true,
    accent: "teal",
  },
  {
    id: "sbm_assignment",
    name: "SbmAssignmentSolver",
    family: "sbm",
    role: "Binary assignment subproblems",
    statusLabel: "Experimental",
    isQuantum: true,
    accent: "teal",
  },
  {
    id: "sbm_route_master",
    name: "SbmRouteMaster",
    family: "sbm",
    role: "Experimental route-master selection",
    statusLabel: "Experimental",
    isQuantum: true,
    accent: "teal",
  },
];

// Deterministic simulation state for each second of the run (5 seconds total)
export interface SimulationStepData {
  iteration: number;
  elapsedSec: number;
  bestObjective: number;
  candidatesCount: number;
  trafficMultiplier: number;
  statusText: ResultStatus;
  currentDecision: string;
  edgeCost: {
    t0: number;
    flow: number;
    capacity: number;
    alpha: number;
    beta: number;
    travelTime: number;
    congestionDelay: number;
    incidentFactor: number;
  };
  event: DecisionEvent;
}

export const SIMULATION_TIMELINE_STEPS: SimulationStepData[] = [
  {
    iteration: 1,
    elapsedSec: 1,
    bestObjective: 412.8,
    candidatesCount: 12,
    trafficMultiplier: 1.18,
    statusText: "FEASIBLE",
    currentDecision: "Exploring lower-congestion alternative corridor",
    edgeCost: {
      t0: 4.2,
      flow: 780,
      capacity: 1200,
      alpha: 0.15,
      beta: 4.0,
      travelTime: 5.12,
      congestionDelay: 0.92,
      incidentFactor: 1.0,
    },
    event: {
      step: 1,
      timestamp: "00:01",
      target: "Edge group 14 → 22",
      decision: "Explored",
      reason: "Lower estimated congestion delay on secondary arterial",
      status: "Exploring",
    },
  },
  {
    iteration: 2,
    elapsedSec: 2,
    bestObjective: 395.4,
    candidatesCount: 24,
    trafficMultiplier: 1.35,
    statusText: "FEASIBLE",
    currentDecision: "Candidate rejected: toll constraint check failed",
    edgeCost: {
      t0: 4.2,
      flow: 890,
      capacity: 1200,
      alpha: 0.15,
      beta: 4.0,
      travelTime: 5.84,
      congestionDelay: 1.64,
      incidentFactor: 1.1,
    },
    event: {
      step: 2,
      timestamp: "00:02",
      target: "Edge group 08 → 15",
      decision: "Rejected",
      reason: "Toll constraint active; candidate path incurred penalty",
      status: "Rejected",
    },
  },
  {
    iteration: 3,
    elapsedSec: 3,
    bestObjective: 342.1,
    candidatesCount: 48,
    trafficMultiplier: 1.48,
    statusText: "BEST_FOUND",
    currentDecision: "Candidate accepted: improved travel time under peak weight",
    edgeCost: {
      t0: 4.2,
      flow: 812,
      capacity: 1200,
      alpha: 0.15,
      beta: 4.0,
      travelTime: 5.38,
      congestionDelay: 1.18,
      incidentFactor: 1.0,
    },
    event: {
      step: 3,
      timestamp: "00:03",
      target: "Edge group 22 → 31",
      decision: "Selected",
      reason: "Better congestion-adjusted score without hard violations",
      status: "Accepted",
    },
  },
  {
    iteration: 4,
    elapsedSec: 4,
    bestObjective: 326.5,
    candidatesCount: 64,
    trafficMultiplier: 1.42,
    statusText: "BEST_FOUND",
    currentDecision: "Revalidating selected route against hard time windows",
    edgeCost: {
      t0: 4.2,
      flow: 805,
      capacity: 1200,
      alpha: 0.15,
      beta: 4.0,
      travelTime: 5.32,
      congestionDelay: 1.12,
      incidentFactor: 1.0,
    },
    event: {
      step: 4,
      timestamp: "00:04",
      target: "Subproblem 04 (Corridor B)",
      decision: "Revalidated",
      reason: "All 18 customer delivery windows preserved inside tolerance",
      status: "Accepted",
    },
  },
  {
    iteration: 5,
    elapsedSec: 5,
    bestObjective: 318.9,
    candidatesCount: 76,
    trafficMultiplier: 1.38,
    statusText: "BEST_FOUND",
    currentDecision: "Feasible candidate retained; independent validation passed",
    edgeCost: {
      t0: 4.2,
      flow: 795,
      capacity: 1200,
      alpha: 0.15,
      beta: 4.0,
      travelTime: 5.24,
      congestionDelay: 1.04,
      incidentFactor: 1.0,
    },
    event: {
      step: 5,
      timestamp: "00:05",
      target: "Global master tour #1",
      decision: "Retained",
      reason: "Global master tour finalized; 0 hard violations reported",
      status: "Accepted",
    },
  },
];

// Architecture Pipeline Stages for /engine
export interface PipelineStage {
  step: string;
  title: string;
  agents: string;
  description: string;
}

export const ENGINE_PIPELINE_STAGES: PipelineStage[] = [
  {
    step: "Stage 01",
    title: "Scenario intake",
    agents: "Scenario Agent",
    description:
      "Validate the routing mode, graph reference, demand, constraints, objective profile, solver policy, and execution deadline.",
  },
  {
    step: "Stage 02",
    title: "Graph & traffic snapshot",
    agents: "Graph Agent · Traffic Agent",
    description:
      "Load a directed graph snapshot and calculate dynamic edge costs from the traffic snapshot and BPR-style model.",
  },
  {
    step: "Stage 03",
    title: "Presolve & decomposition",
    agents: "Presolver Agent · Decomposition Agent",
    description:
      "Check connectivity, remove or filter unsuitable edges, preserve protected nodes, and create local subproblems where appropriate.",
  },
  {
    step: "Stage 04",
    title: "Solver portfolio",
    agents: "Solver Selection Agent · Local Solver Agent",
    description:
      "Select an approved classical or quantum-inspired solver path based on problem mode, scale, constraints, and deadline.",
  },
  {
    step: "Stage 05",
    title: "Global master, repair & validation",
    agents: "Master Agent · Repair Agent · Validation Agent",
    description:
      "Reconcile candidate routes, repair violations where possible, and independently verify all hard constraints.",
  },
  {
    step: "Stage 06",
    title: "Persistence & benchmarking",
    agents: "Benchmark Agent · Reporting Agent",
    description:
      "Record solver configuration, seeds, runtime, metrics, validation state, and reproducibility metadata.",
  },
];

// Independent Validation Checklist
export const VALIDATION_CHECKS = [
  "All mandatory customers covered exactly once",
  "Vehicle capacity respected across each delivery stop",
  "Customer time windows and service durations respected",
  "Every route starts at an allowed depot",
  "Every route returns to an allowed depot",
  "No forbidden edges, closed corridors, or toll violations",
  "No disconnected subtour in any vehicle trajectory",
  "Vehicle-to-customer compatibility rules checked",
];

// Objective Profile default weights
export const DEFAULT_OBJECTIVE_WEIGHTS = [
  { label: "Travel time", weight: 1.0, value: "1.00", width: "100%", accent: "classical" },
  { label: "Distance", weight: 0.25, value: "0.25", width: "25%", accent: "classical" },
  { label: "Congestion", weight: 0.8, value: "0.80", width: "80%", accent: "quantum" },
  { label: "Toll cost", weight: 0.4, value: "0.40", width: "40%", accent: "classical" },
  { label: "Emissions", weight: 0.15, value: "0.15", width: "15%", accent: "quantum" },
  { label: "Vehicle activation", weight: 0.2, value: "0.20", width: "20%", accent: "classical" },
];

// Engine synthetic metrics preview
export const ENGINE_METRICS_PREVIEW = [
  { label: "Total travel time", value: "318.9 s", note: "Congestion-weighted" },
  { label: "Congestion delay", value: "+46.2 s", note: "BPR penalty factor" },
  { label: "Total distance", value: "14.8 km", note: "Road-network metric" },
  { label: "Customers served", value: "24 / 24", note: "100% coverage" },
  { label: "Vehicles deployed", value: "3 active", note: "Capacities respected" },
  { label: "Candidates generated", value: "76 routes", note: "QACO local generator" },
  { label: "Master runtime", value: "4.82 s", note: "Decomposed reconciliation" },
  { label: "Feasibility rate", value: "100%", note: "0 hard violations" },
];

// Sample validation report
export const SAMPLE_VALIDATION_REPORT: ValidationReport = {
  valid: true,
  hard_violation_count: 0,
  soft_violation_count: 1,
  violations: [
    {
      constraint_id: "soft_congestion_corridor",
      severity: "soft",
      entity_id: "edge_22_31",
      message: "Edge exceeded 80% theoretical capacity during peak hour",
      observed_value: 812,
      required_value: 800,
      magnitude: 12,
      repairable: false,
    },
  ],
  checked_at: "2026-09-06T12:00:05Z",
  validator_version: "validator-demo-0.1",
};
