import type { RunSummary } from "@/types/experiment";

export function RecentRunsTable({ runs }: { runs: RunSummary[] }) {
  if (!runs.length)
    return <p className="empty">No experiments recorded yet.</p>;
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Run</th>
            <th>Algorithm</th>
            <th>Distance</th>
            <th>Vehicles</th>
            <th>Runtime</th>
            <th>Valid</th>
          </tr>
        </thead>
        <tbody>
          {runs.map((run) => (
            <tr key={run.id}>
              <td>#{run.id}</td>
              <td>{run.algorithm.toUpperCase()}</td>
              <td>{run.distance.toFixed(1)}</td>
              <td>{run.vehicles}</td>
              <td>{run.runtime_ms} ms</td>
              <td>{run.feasible ? "Yes" : "No"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
