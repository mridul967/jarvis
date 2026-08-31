import type { SolveResult } from "@/types/experiment";

export function RouteView({ result }: { result: SolveResult | null }) {
  return (
    <section className="panel">
      <h3>Routes</h3>
      {!result ? (
        <p className="empty">Results will appear here.</p>
      ) : (
        <>
          <div className="metrics">
            <div className="metric">
              <span>Distance</span>
              <strong>{result.distance}</strong>
            </div>
            <div className="metric">
              <span>Vehicles</span>
              <strong>{result.vehicles}</strong>
            </div>
            <div className="metric">
              <span>Evaluations</span>
              <strong>{result.evaluations}</strong>
            </div>
          </div>
          <ol className="routes">
            {result.routes.map((route, index) => (
              <li key={index}>Depot → {route.join(" → ")} → Depot</li>
            ))}
          </ol>
        </>
      )}
    </section>
  );
}
