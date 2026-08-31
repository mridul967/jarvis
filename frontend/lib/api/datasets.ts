import { api } from "@/lib/api/client";
import type { Dataset } from "@/types/dataset";

export function getSampleInstance(): Promise<Dataset> {
  return api<Dataset>("/api/v1/instances/sample", {
    next: { revalidate: 3600 },
  });
}
