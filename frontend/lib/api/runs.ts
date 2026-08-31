import { api } from "@/lib/api/client";
import type { RunSummary } from "@/types/experiment";

export function getRuns(): Promise<RunSummary[]> {
  return api<RunSummary[]>("/api/v1/runs", { cache: "no-store" });
}
