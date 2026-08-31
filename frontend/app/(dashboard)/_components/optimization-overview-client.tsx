"use client";

import { useState } from "react";

import { ExperimentForm } from "./experiment-form";
import { RecentRunsTable } from "./recent-runs-table";
import { ResultSummary } from "./result-summary";
import { getRuns } from "@/lib/api/runs";
import { solveExperiment } from "@/lib/api/experiments";
import type { RunSummary, SolveRequest, SolveResult } from "@/types/experiment";

export function OptimizationOverviewClient({
  initialRuns,
}: {
  initialRuns: RunSummary[];
}) {
  const [runs, setRuns] = useState(initialRuns);
  const [result, setResult] = useState<SolveResult | null>(null);
  const [status, setStatus] = useState("Ready");
  const [solving, setSolving] = useState(false);

  async function run(input: SolveRequest) {
    setSolving(true);
    setStatus("Optimizing…");
    try {
      const solved = await solveExperiment(input);
      setResult(solved);
      setRuns(await getRuns());
      setStatus("Complete");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Experiment failed");
    } finally {
      setSolving(false);
    }
  }

  return (
    <>
      <header className="page-heading">
        <p className="eyebrow">SIH 26137 · Optimization workbench</p>
        <h2>Traffic routes, tested—not guessed.</h2>
        <p className="lede">
          Compare PSO and quantum-behaved PSO under the same VRPTW constraints,
          seeds, and evaluation settings.
        </p>
      </header>
      <section className="grid two">
        <ExperimentForm onSubmit={run} solving={solving} status={status} />
        <ResultSummary result={result} />
      </section>
      <section style={{ marginTop: 40 }}>
        <div className="toolbar">
          <h3>Recent experiments</h3>
          <a className="button secondary" href="/runs">
            View all
          </a>
        </div>
        <RecentRunsTable runs={runs.slice(0, 8)} />
      </section>
    </>
  );
}
