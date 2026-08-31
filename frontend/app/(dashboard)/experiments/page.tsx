import { ExperimentClient } from "./_components/experiment-client";
import { getSampleInstance } from "@/lib/api/datasets";

export const dynamic = "force-dynamic";

export default async function ExperimentsPage() {
  const sample = await getSampleInstance().catch(() => null);
  return <ExperimentClient initialInstance={sample?.content ?? ""} />;
}
