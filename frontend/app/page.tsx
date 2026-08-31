"use client";

import { FormEvent, useEffect, useState } from "react";

type Result = {
  id: number;
  algorithm: string;
  distance: number;
  vehicles: number;
  feasible: boolean;
  runtime_ms: number;
  routes?: number[][];
};

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export default function Home() {
  const [algorithm, setAlgorithm] = useState("qpso");
  const [iterations, setIterations] = useState(80);
  const [result, setResult] = useState<Result | null>(null);
  const [runs, setRuns] = useState<Result[]>([]);
  const [status, setStatus] = useState("Ready");

  async function loadRuns() {
    const response = await fetch(`${API}/runs`);
    if (response.ok) setRuns(await response.json());
  }

  useEffect(() => {
    fetch(`${API}/runs`)
      .then(async (response) => {
        if (response.ok) setRuns(await response.json());
      })
      .catch(() => setStatus("Start the FastAPI server to load runs."));
  }, []);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setStatus("Optimizing…");
    try {
      const response = await fetch(`${API}/solve`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ algorithm, iterations, population_size: 30, seed: 42 }),
      });
      if (!response.ok) throw new Error(await response.text());
      const payload = await response.json();
      setResult(payload);
      setStatus("Complete");
      await loadRuns();
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Request failed");
    }
  }

  return (
    <main>
      <header>
        <p className="eyebrow">SIH 26137 · Optimization workbench</p>
        <h1>Traffic routes, tested—not guessed.</h1>
        <p className="lede">Run the same VRPTW instance through classical PSO and quantum-behaved PSO, then compare feasibility, distance, and runtime.</p>
      </header>

      <section className="workspace">
        <form onSubmit={submit}>
          <h2>New experiment</h2>
          <label>Algorithm
            <select value={algorithm} onChange={(event) => setAlgorithm(event.target.value)}>
              <option value="qpso">QPSO</option>
              <option value="pso">PSO</option>
            </select>
          </label>
          <label>Iterations <strong>{iterations}</strong>
            <input type="range" min="10" max="300" step="10" value={iterations} onChange={(event) => setIterations(Number(event.target.value))} />
          </label>
          <button type="submit">Run optimizer</button>
          <p role="status">{status}</p>
        </form>

        <article className="result" aria-live="polite">
          <h2>Latest solution</h2>
          {result ? <>
            <div className="metrics">
              <Metric label="Distance" value={result.distance.toFixed(1)} />
              <Metric label="Vehicles" value={String(result.vehicles)} />
              <Metric label="Runtime" value={`${result.runtime_ms} ms`} />
            </div>
            <p className={result.feasible ? "feasible" : "infeasible"}>{result.feasible ? "All constraints satisfied" : "Constraint violation"}</p>
            <ol className="routes">{result.routes?.map((route, index) => <li key={index}>Depot → {route.join(" → ")} → Depot</li>)}</ol>
          </> : <p className="empty">Run an experiment to inspect its routes.</p>}
        </article>
      </section>

      <section>
        <h2>Experiment history</h2>
        <div className="table-wrap"><table>
          <thead><tr><th>Run</th><th>Algorithm</th><th>Distance</th><th>Vehicles</th><th>Runtime</th><th>Valid</th></tr></thead>
          <tbody>{runs.map((run) => <tr key={run.id}><td>#{run.id}</td><td>{run.algorithm.toUpperCase()}</td><td>{run.distance.toFixed(1)}</td><td>{run.vehicles}</td><td>{run.runtime_ms} ms</td><td>{run.feasible ? "Yes" : "No"}</td></tr>)}</tbody>
        </table></div>
      </section>
    </main>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return <div><span>{label}</span><strong>{value}</strong></div>;
}
