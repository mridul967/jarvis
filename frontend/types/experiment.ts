export type Algorithm = "pso" | "qpso";
export interface SolveRequest {
  algorithm: Algorithm;
  population_size: number;
  iterations: number;
  seed: number;
  instance?: string;
}
export interface RunSummary {
  id: number;
  created_at: string;
  algorithm: Algorithm;
  distance: number;
  vehicles: number;
  feasible: boolean;
  runtime_ms: number;
}
export interface SolveResult extends RunSummary {
  instance: string;
  violations: number;
  routes: number[][];
  convergence: number[];
  evaluations: number;
  parameters: Omit<SolveRequest, "algorithm" | "instance">;
}
