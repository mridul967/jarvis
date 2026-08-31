import { RecentRunsTable } from "../_components/recent-runs-table";
import { getRuns } from "@/lib/api/runs";

export const dynamic = "force-dynamic";

export default async function RunsPage() {
  const runs = await getRuns().catch(() => []);
  return (
    <>
      <header className="page-heading">
        <p className="eyebrow">Evidence</p>
        <h2>Experiment history.</h2>
        <p className="lede">
          Persisted results keep algorithm comparisons inspectable and
          reproducible.
        </p>
      </header>
      <RecentRunsTable runs={runs} />
    </>
  );
}
