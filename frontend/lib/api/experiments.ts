import { api } from "@/lib/api/client";
import type { SolveRequest, SolveResult } from "@/types/experiment";

export function solveExperiment(input: SolveRequest): Promise<SolveResult> {
  return api<SolveResult>("/api/v1/solve", {
    method: "POST",
    body: JSON.stringify(input),
  });
}
