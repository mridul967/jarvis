"use client";

import { FormEvent, useState } from "react";

import type { SolveRequest } from "@/types/experiment";

export function ExperimentForm({
  onSubmit,
  solving,
  status,
}: {
  onSubmit: (input: SolveRequest) => Promise<void>;
  solving: boolean;
  status: string;
}) {
  const [algorithm, setAlgorithm] = useState<SolveRequest["algorithm"]>("qpso");
  const [iterations, setIterations] = useState(80);

  function submit(event: FormEvent) {
    event.preventDefault();
    void onSubmit({ algorithm, iterations, population_size: 30, seed: 42 });
  }

  return (
    <form className="panel" onSubmit={submit}>
      <h3>New experiment</h3>
      <label className="field">
        Algorithm
        <select
          value={algorithm}
          onChange={(event) =>
            setAlgorithm(event.target.value as SolveRequest["algorithm"])
          }
        >
          <option value="qpso">QPSO</option>
          <option value="pso">PSO</option>
        </select>
      </label>
      <label className="field">
        Iterations <strong>{iterations}</strong>
        <input
          type="range"
          min="10"
          max="300"
          step="10"
          value={iterations}
          onChange={(event) => setIterations(Number(event.target.value))}
        />
      </label>
      <button className="button" disabled={solving} type="submit">
        {solving ? "Running…" : "Run optimizer"}
      </button>
      <p className="muted" role="status">
        {status}
      </p>
    </form>
  );
}
