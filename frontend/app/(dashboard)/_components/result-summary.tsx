import type { SolveResult } from "@/types/experiment";

export function ResultSummary({ result }: { result: SolveResult | null }) {
  return (
    <article className="panel" aria-live="polite">
      <h3>Latest solution</h3>
      {!result ? (
        <p className="empty">Run an experiment to inspect its routes.</p>
      ) : (
        <>
          <div className="metrics">
            <Metric label="Distance" value={result.distance.toFixed(1)} />
            <Metric label="Vehicles" value={String(result.vehicles)} />
            <Metric label="Runtime" value={`${result.runtime_ms} ms`} />
          </div>
          <p className={result.feasible ? "status-good" : "status-bad"}>
            {result.feasible
              ? "All constraints satisfied"
              : `${result.violations} constraint violations`}
          </p>
          <ol className="routes">
            {result.routes.map((route, index) => (
              <li key={index}>Depot → {route.join(" → ")} → Depot</li>
            ))}
          </ol>
        </>
      )}
    </article>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}
