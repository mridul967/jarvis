export interface DemoNode {
  id: number;
  road: string;
  area: string;
  x: number;
  y: number;
  demand: number;
  is_depot: boolean;
}

export interface DemoEdge {
  source: number;
  target: number;
  distance_km: number;
  travel_time_min: number;
  utilization: number;
  shocked: boolean;
  gat_score: number | null;
}

export interface DemoGraph {
  id: string;
  name: string;
  source: string;
  source_type: string;
  nodes: DemoNode[];
  edges: DemoEdge[];
}

export interface DemoResponse {
  scenario: DemoGraph;
  algorithm: {
    id: string;
    name: string;
    family: string;
    quantum_inspired: boolean;
    mechanisms: string[];
    source_notebook: string;
  };
  traffic: string;
  gat: {
    applied: boolean;
    production_ready: boolean;
    training_source?: string;
    loss?: number;
    scored_edges?: number;
    reason?: string;
  };
  result: {
    feasible: boolean;
    routes: number[][];
    route_paths: number[][];
    score: {
      hard_violations: number;
      coverage_errors: number;
      vehicles: number;
      lateness: number;
      travel_time: number;
      distance: number;
      congestion: number;
    };
    evaluations: number;
    runtime_ms: number;
    seed: number;
    convergence: { evaluations: number; objective: number }[];
    diagnostics: Record<string, string | number | boolean>;
  };
  events: string[];
  disclosure: string;
}

export interface BenchmarkResponse {
  traffic: string;
  gat_enabled: boolean;
  population_size: number;
  iterations: number;
  seed: number;
  rows: Array<{
    algorithm: DemoResponse["algorithm"];
    feasible: boolean;
    score: DemoResponse["result"]["score"];
    runtime_ms: number;
    evaluations: number;
    initial_objective: number;
    final_objective: number;
    improvement_percent: number;
  }>;
  disclosure: string;
}
