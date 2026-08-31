import type { Dispatch, SetStateAction } from "react";
import type { SolveRequest } from "@/types/experiment";

export function SolverControls({
  request,
  onChange,
  solving,
  status,
}: {
  request: SolveRequest;
  onChange: Dispatch<SetStateAction<SolveRequest>>;
  solving: boolean;
  status: string;
}) {
  const set = <K extends keyof SolveRequest>(key: K, value: SolveRequest[K]) =>
    onChange((current) => ({ ...current, [key]: value }));
  return (
    <section className="panel">
      <h3>Configuration</h3>
      <label className="field">
        Algorithm
        <select
          value={request.algorithm}
          onChange={(e) =>
            set("algorithm", e.target.value as SolveRequest["algorithm"])
          }
        >
          <option value="qpso">QPSO</option>
          <option value="pso">PSO</option>
        </select>
      </label>
      <label className="field">
        Population
        <input
          type="number"
          min="5"
          max="200"
          value={request.population_size}
          onChange={(e) => set("population_size", Number(e.target.value))}
        />
      </label>
      <label className="field">
        Iterations
        <input
          type="number"
          min="1"
          max="2000"
          value={request.iterations}
          onChange={(e) => set("iterations", Number(e.target.value))}
        />
      </label>
      <label className="field">
        Seed
        <input
          type="number"
          value={request.seed}
          onChange={(e) => set("seed", Number(e.target.value))}
        />
      </label>
      <label className="field">
        Solomon instance
        <textarea
          rows={8}
          value={request.instance ?? ""}
          onChange={(e) => set("instance", e.target.value)}
        />
      </label>
      <button className="button" disabled={solving}>
        {solving ? "Running…" : "Run experiment"}
      </button>
      <p className="muted" role="status">
        {status}
      </p>
    </section>
  );
}
