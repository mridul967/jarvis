/**
 * Domain Schemas and Contracts for SIH 2026 Egreen Quanta
 * Quantum-Inspired Traffic and Vehicle-Routing Optimization Platform.
 *
 * Source: SIH Quantum-Inspired Traffic Optimization Architecture & Domain Schemas Specification v0.1
 */

export type NodeId = string;
export type EdgeId = string;
export type CustomerId = string;
export type VehicleId = string;
export type DepotId = string;
export type ScenarioId = string;
export type SnapshotId = string;
export type JobId = string;
export type RouteId = string;
export type SolverId =
  | "nearest_neighbor"
  | "random_keys"
  | "ortools"
  | "dynamic_ors"
  | "pso"
  | "qpso"
  | "qrg_qpso"
  | "admr_qpso"
  | "aco"
  | "aco_local_search"
  | "qaco_rotation"
  | "qaco_interference"
  | "qaco_tunneling"
  | "qaco_adaptive"
  | "qaco_full"
  | "classical_fusion"
  | "dynamic_qaco"
  | "dijkstra"
  | "astar"
  | "greedy_fleet"
  | "hill_climbing"
  | "ortools_vrptw"
  | "cplex_vrptw"
  | "qaco_local"
  | "qpso_policy"
  | "sbm_assignment"
  | "sbm_route_master";

export type RoutingMode = "casp" | "vrptw";

export type ResultStatus =
  | "OPTIMAL_PROVEN"
  | "FEASIBLE"
  | "BEST_FOUND"
  | "INFEASIBLE"
  | "TIME_LIMIT"
  | "FAILED";

export type JobStatus =
  | "queued"
  | "validating"
  | "presolving"
  | "decomposing"
  | "solving"
  | "merging"
  | "repairing"
  | "validating_result"
  | "completed"
  | "time_limit"
  | "failed"
  | "infeasible"
  | "cancelled";

export type ReductionGuarantee = "safe" | "heuristic" | "experimental";

export type SolverFamily =
  | "shortest_path"
  | "exact_mip"
  | "classical_heuristic"
  | "qaco"
  | "qpso"
  | "sbm"
  | "qubo";

export type ConstraintSeverity = "hard" | "soft" | "warning";

export interface Coordinate {
  latitude: float;
  longitude: float;
}
type float = number;

export interface Node {
  id: NodeId;
  coordinate: Coordinate;
  node_type: string;
  is_depot?: boolean;
  is_customer?: boolean;
  is_signalized?: boolean;
  is_protected?: boolean;
  zone_id?: string | null;
}

export interface Edge {
  id: EdgeId;
  source: NodeId;
  target: NodeId;
  length_m: number;
  free_flow_time_s: number;
  capacity_veh_per_hour: number;
  road_class?: string | null;
  toll?: boolean;
  closed?: boolean;
  allowed_vehicle_types?: string[];
  geometry?: Coordinate[] | null;
}

export interface DynamicEdgeCost {
  edge_id: EdgeId;
  travel_time_s: number;
  distance_m: number;
  congestion_delay_s: number;
  toll_cost: number;
  incident_factor: number;
  computed_at: string;
  model_name: string;
  model_version: string;
}

export interface GraphSnapshot {
  snapshot_id: SnapshotId;
  source: string;
  created_at: string;
  nodes: Node[];
  edges: Edge[];
  dynamic_costs: DynamicEdgeCost[];
  graph_version: string;
  units: Record<string, string>;
}

export interface TrafficObservation {
  edge_id: EdgeId;
  observed_flow_veh_per_hour: number;
  observed_speed_kmh?: number | null;
  confidence?: number | null;
  observed_at: string;
}

export interface TrafficModelConfig {
  model_name: string;
  alpha: number;
  beta: number;
  incident_multiplier_enabled: boolean;
  signal_delay_enabled: boolean;
}

export interface TrafficSnapshot {
  snapshot_id: SnapshotId;
  graph_snapshot_id: SnapshotId;
  observations: TrafficObservation[];
  model_config: TrafficModelConfig;
  created_at: string;
}

export interface TimeWindow {
  earliest_s: number;
  latest_s: number;
}

export interface Customer {
  id: CustomerId;
  node_id: NodeId;
  demand: number;
  service_duration_s?: number;
  time_window?: TimeWindow | null;
  priority?: number;
  mandatory?: boolean;
  allowed_vehicle_types?: string[];
}

export interface Vehicle {
  id: VehicleId;
  vehicle_type: string;
  capacity: number;
  start_depot_id: DepotId;
  end_depot_id: DepotId;
  available_from_s?: number;
  available_until_s?: number | null;
  fixed_activation_cost?: number;
}

export interface Depot {
  id: DepotId;
  node_id: NodeId;
  opening_window?: TimeWindow | null;
}

export interface ObjectiveProfile {
  name: string;
  time_weight: number;
  distance_weight: number;
  congestion_weight: number;
  toll_weight: number;
  emissions_weight: number;
  risk_weight: number;
  vehicle_activation_weight: number;
  route_change_weight: number;
}

export interface ConstraintProfile {
  avoid_tolls: boolean;
  max_travel_time_s?: number | null;
  max_route_duration_s?: number | null;
  enforce_time_windows: boolean;
  enforce_capacity: boolean;
  enforce_vehicle_compatibility: boolean;
  enforce_forbidden_edges: boolean;
  allow_customer_drop: boolean;
  max_vehicles?: number | null;
  penalty_strategy: string;
  penalty_scale: number;
}

export interface SolverOptions {
  solver_id: SolverId;
  time_limit_ms: number;
  random_seed?: number | null;
  max_iterations?: number | null;
  population_size?: number | null;
  return_candidate_count?: number;
  use_gpu?: boolean;
  enable_repair?: boolean;
  enable_local_search?: boolean;
  configuration?: Record<string, unknown>;
}

export interface SolverPolicy {
  primary_solver: SolverId;
  fallback_solvers: SolverId[];
  comparison_solvers?: SolverId[];
  max_parallel_solvers?: number;
  require_feasible_result?: boolean;
  permit_heuristic_pruning?: boolean;
  permit_experimental_solver?: boolean;
}

export interface ScenarioSnapshot {
  scenario_id: ScenarioId;
  graph_snapshot_id: SnapshotId;
  traffic_snapshot_id?: SnapshotId | null;
  mode: RoutingMode;
  origin_node_id?: NodeId | null;
  destination_node_id?: NodeId | null;
  depots?: Depot[];
  customers?: Customer[];
  vehicles?: Vehicle[];
  objective: ObjectiveProfile;
  constraints: ConstraintProfile;
  solver_policy: SolverPolicy;
  created_at: string;
  schema_version: string;
}

export interface ArrivalRecord {
  node_id: NodeId;
  arrival_time_s: number;
  departure_time_s: number;
  load_after_service: number;
}

export interface RouteMetrics {
  travel_time_s: number;
  service_time_s: number;
  total_duration_s: number;
  distance_m: number;
  congestion_delay_s: number;
  toll_cost: number;
  estimated_emissions?: number | null;
}

export interface RouteCandidate {
  route_id: RouteId;
  vehicle_id?: VehicleId | null;
  depot_start_id?: DepotId | null;
  depot_end_id?: DepotId | null;
  customer_ids: CustomerId[];
  node_sequence: NodeId[];
  edge_sequence: EdgeId[];
  arrivals: ArrivalRecord[];
  metrics: RouteMetrics;
  feasible: boolean;
  violations: string[];
  solver_id: SolverId;
  seed?: number | null;
  generated_at: string;
}

export interface ConstraintViolation {
  constraint_id: string;
  severity: ConstraintSeverity;
  entity_id?: string | null;
  message: string;
  observed_value?: number | null;
  required_value?: number | null;
  magnitude?: number | null;
  repairable?: boolean;
}

export interface ValidationReport {
  valid: boolean;
  hard_violation_count: number;
  soft_violation_count: number;
  violations: ConstraintViolation[];
  checked_at: string;
  validator_version: string;
}

export interface SolverResult {
  job_id: JobId;
  solver_id: SolverId;
  solver_family: SolverFamily;
  status: ResultStatus;
  routes: RouteCandidate[];
  objective_value: number;
  objective_breakdown: Record<string, number>;
  validation: ValidationReport;
  runtime_ms: number;
  iterations?: number | null;
  candidates_generated: number;
  seed?: number | null;
  metadata: Record<string, unknown>;
  warnings: string[];
  errors: string[];
}

export interface RegionBoundary {
  entry_node_ids: NodeId[];
  exit_node_ids: NodeId[];
  preserved_edge_ids: EdgeId[];
}

export interface LocalSubproblem {
  subproblem_id: string;
  scenario_id: ScenarioId;
  customer_ids: CustomerId[];
  candidate_vehicle_ids: VehicleId[];
  graph_snapshot_id: SnapshotId;
  boundary: RegionBoundary;
  constraints: ConstraintProfile;
  objective: ObjectiveProfile;
  reduction_guarantee: ReductionGuarantee;
}

export interface ReducedGraph {
  reduced_graph_snapshot_id: SnapshotId;
  original_snapshot_id: SnapshotId;
  retained_node_ids: NodeId[];
  retained_edge_ids: EdgeId[];
  removed_node_ids: NodeId[];
  removed_edge_ids: EdgeId[];
  contraction_map: Record<NodeId, NodeId[]>;
  actions: string[];
  guarantee: ReductionGuarantee;
}

// UI Decision Timeline Event
export interface DecisionEvent {
  step: number;
  timestamp: string;
  target: string;
  decision: "Explored" | "Rejected" | "Selected" | "Revalidated" | "Retained";
  reason: string;
  status: "Exploring" | "Rejected" | "Accepted";
}

// Solver Registry Item for UI
export interface SolverRegistryItem {
  id: SolverId;
  name: string;
  family: SolverFamily;
  role: string;
  statusLabel: string;
  isQuantum: boolean;
  accent: "amber" | "teal";
}
