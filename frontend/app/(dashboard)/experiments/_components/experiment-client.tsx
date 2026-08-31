"use client";

import { FormEvent, useState } from "react";

import { ConvergenceChart } from "./convergence-chart";
import { RouteView } from "./route-view";
import { SolverControls } from "./solver-controls";
import { solveExperiment } from "@/lib/api/experiments";
import type { SolveRequest, SolveResult } from "@/types/experiment";

export function ExperimentClient({
  initialInstance,
}: {
  initialInstance: string;
}) {
  const [request, setRequest] = useState<SolveRequest>({
    algorithm: "qpso",
    iterations: 80,
    population_size: 30,
    seed: 42,
    instance: initialInstance || undefined,
  });
  const [result, setResult] = useState<SolveResult | null>(null);
  const [status, setStatus] = useState("Ready");
  const [solving, setSolving] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setSolving(true);
    setStatus("Optimizing…");
    try {
      setResult(await solveExperiment(request));
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
        <p className="eyebrow">Solver laboratory</p>
        <h2>Run controlled experiments.</h2>
        <p className="lede">
          Change the algorithm and its budget while keeping the instance and
          constraints explicit.
        </p>
      </header>
      <form className="grid two" onSubmit={submit}>
        <SolverControls
          request={request}
          onChange={setRequest}
          solving={solving}
          status={status}
        />
        <RouteView result={result} />
      </form>
      <ConvergenceChart values={result?.convergence ?? []} />
    </>
  );
}
