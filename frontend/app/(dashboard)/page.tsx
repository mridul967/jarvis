import { OptimizationOverviewClient } from "./_components/optimization-overview-client";
import { getRuns } from "@/lib/api/runs";

export const dynamic = "force-dynamic";

export default async function OverviewPage() {
  const initialRuns = await getRuns().catch(() => []);
  return <OptimizationOverviewClient initialRuns={initialRuns} />;
}
