import React from "react";
import { CheckCircle2, ShieldCheck, Cpu } from "lucide-react";
import { OptimizationPipeline } from "../../components/engine/optimization-pipeline";
import { SolverPortfolio } from "../../components/engine/solver-portfolio";
import { GATInferencePanel } from "../../components/visualization/gat-inference-panel";
import {
  DEFAULT_OBJECTIVE_WEIGHTS,
  ENGINE_METRICS_PREVIEW,
  VALIDATION_CHECKS,
  SAMPLE_VALIDATION_REPORT,
} from "../../lib/mock-data";

// TODO(backend): Replace this mock ObjectiveProfile with the scenario
// configuration returned from POST /api/v1/scenarios and GET
// /api/v1/scenarios/{scenario_id}.

export default function EnginePage() {
  return (
    <div className="space-y-16 md:space-y-20">
      {/* Page Header */}
      <div>
        <span className="text-[13px] font-mono text-accent-classical block mb-1">
          Core optimization engine
        </span>
        <h1 className="text-[32px] font-heading font-medium text-text-primary">
          From graph snapshot to validated route.
        </h1>
        <p className="text-[15px] text-text-secondary mt-2 max-w-[65ch] leading-relaxed">
          The engine separates graph preparation, candidate generation, global coordination, repair,
          and independent validation. Classical baselines and quantum-inspired methods operate under
          a unified schema.
        </p>
      </div>

      {/* GAT Graph Preprocessing — runs before the optimizer pipeline */}
      <section className="border-t border-hairline pt-12">
        <GATInferencePanel />
      </section>

      {/* Pipeline Section */}
      <section className="border-t border-hairline pt-12">
        <OptimizationPipeline />
      </section>

      {/* Solver Portfolio Section */}
      <section className="border-t border-hairline pt-12">
        <SolverPortfolio />
      </section>

      {/* Objective Profile & Independent Validation Panels */}
      <section className="border-t border-hairline pt-12 grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Objective Profile Panel */}
        <div className="bg-ink-panel border border-hairline rounded-md p-6 space-y-5">
          <div className="flex items-center justify-between border-b border-hairline pb-3">
            <div>
              <h3 className="text-[16px] font-heading font-medium text-text-primary">
                Objective profile weights
              </h3>
              <p className="text-[13px] text-text-secondary mt-0.5">
                Multi-factor scalarization parameters
              </p>
            </div>
            <span className="text-[11px] font-mono text-accent-classical bg-ink-base px-2 py-0.5 rounded-sm border border-hairline">
              Profile: balanced
            </span>
          </div>

          <div className="space-y-4">
            {DEFAULT_OBJECTIVE_WEIGHTS.map((item, idx) => (
              <div key={idx} className="space-y-1.5">
                <div className="flex justify-between text-[13px] font-mono">
                  <span className="text-text-secondary">{item.label}</span>
                  <span className="text-text-primary font-medium">{item.value}</span>
                </div>
                {/* Horizontal Meter Bar */}
                <div className="h-1.5 w-full bg-ink-base rounded-full overflow-hidden border border-hairline">
                  <div
                    className={`h-full ${
                      item.accent === "quantum" ? "bg-accent-quantum" : "bg-accent-classical"
                    }`}
                    style={{ width: item.width }}
                  />
                </div>
              </div>
            ))}
          </div>

          <div className="pt-2 border-t border-hairline">
            <p className="text-[11px] font-mono text-text-secondary">
              Illustrative configuration. Production values will come from the scenario objective profile.
            </p>
          </div>
        </div>

        {/* Independent Validation Panel */}
        <div className="bg-ink-panel border border-hairline rounded-md p-6 space-y-5">
          <div className="flex items-center justify-between border-b border-hairline pb-3">
            <div>
              <h3 className="text-[16px] font-heading font-medium text-text-primary">
                Independent validation
              </h3>
              <p className="text-[13px] text-text-secondary mt-0.5">
                Hard constraint verification contract
              </p>
            </div>
            <span className="text-[11px] font-mono text-accent-quantum bg-ink-base px-2 py-0.5 rounded-sm border border-hairline">
              Validator 0.1
            </span>
          </div>

          <div className="space-y-2.5">
            {VALIDATION_CHECKS.map((check, idx) => (
              <div key={idx} className="flex items-center gap-3 text-[13px]">
                <CheckCircle2 size={16} className="text-accent-quantum shrink-0" />
                <span className="text-text-primary font-sans">{check}</span>
              </div>
            ))}
          </div>

          {/* Synthetic Validation Report Output */}
          <div className="p-3 bg-ink-base rounded-sm border border-hairline text-[11px] font-mono space-y-1">
            <div className="flex justify-between">
              <span className="text-text-secondary">Validation status:</span>
              <span className="text-accent-quantum font-medium">
                {SAMPLE_VALIDATION_REPORT.valid ? "FEASIBLE" : "INFEASIBLE"}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-text-secondary">Hard violations:</span>
              <span className="text-text-primary">{SAMPLE_VALIDATION_REPORT.hard_violation_count}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-text-secondary">Soft violations:</span>
              <span className="text-accent-classical">{SAMPLE_VALIDATION_REPORT.soft_violation_count}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-text-secondary">Validator version:</span>
              <span className="text-text-primary">{SAMPLE_VALIDATION_REPORT.validator_version}</span>
            </div>
          </div>

          <div className="p-3 rounded-sm border border-hairline bg-ink-panel-raised flex items-start gap-2.5">
            <ShieldCheck size={16} className="text-accent-quantum shrink-0 mt-0.5" />
            <p className="text-[11px] font-mono text-text-secondary leading-relaxed">
              Solver energy, score, or status is never treated as proof of feasibility. Every route
              must satisfy deterministic validator assertions.
            </p>
          </div>
        </div>
      </section>

      {/* Engine Metrics Preview */}
      <section className="border-t border-hairline pt-12 space-y-6">
        <div>
          <h2 className="text-[20px] font-heading font-medium text-text-primary">
            Engine metrics & telemetry schema
          </h2>
          <p className="text-[15px] text-text-secondary mt-1 max-w-[65ch]">
            Standardized execution metrics exposed by the orchestration tier for benchmarking.
          </p>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {ENGINE_METRICS_PREVIEW.map((metric, idx) => (
            <div key={idx} className="p-4 bg-ink-panel border border-hairline rounded-md space-y-1">
              <span className="text-[11px] font-mono text-text-secondary block">
                {metric.label}
              </span>
              <div className="text-[18px] font-mono font-medium text-text-primary">
                {metric.value}
              </div>
              <span className="text-[11px] font-mono text-accent-quantum block">
                {metric.note}
              </span>
            </div>
          ))}
        </div>

        <p className="text-[11px] font-mono text-text-secondary">
          Synthetic benchmark preview. Values reflect simulated local execution.
        </p>
      </section>

      {/* Explainability Panel */}
      <section className="border-t border-hairline pt-12 pb-12 space-y-6">
        <div>
          <h2 className="text-[20px] font-heading font-medium text-text-primary">
            Why this solver path?
          </h2>
          <p className="text-[15px] text-text-secondary mt-1 max-w-[65ch] leading-relaxed">
            The selected path begins with QACO candidate generation because this demo scenario
            is a constrained VRPTW instance with a GAT-scored Bengaluru graph. OR-Tools remains
            available as the classical fallback. The final route must pass the independent validator
            before it can be marked FEASIBLE.
          </p>
        </div>

        <div className="bg-ink-panel border border-hairline rounded-md p-6 max-w-2xl">
          <div className="space-y-2.5 text-[13px] font-mono divide-y divide-hairline">
            <div className="flex justify-between py-1.5">
              <span className="text-text-secondary">Selected solver:</span>
              <span className="text-accent-quantum font-medium">qaco_full</span>
            </div>
            <div className="flex justify-between py-1.5">
              <span className="text-text-secondary">Fallback solver:</span>
              <span className="text-accent-classical font-medium">ortools</span>
            </div>
            <div className="flex justify-between py-1.5">
              <span className="text-text-secondary">Random seed:</span>
              <span className="text-text-primary">42</span>
            </div>
            <div className="flex justify-between py-1.5">
              <span className="text-text-secondary">Input snapshot:</span>
              <span className="text-text-primary">bengaluru-historical-derived-16</span>
            </div>
            <div className="flex justify-between py-1.5">
              <span className="text-text-secondary">Objective profile:</span>
              <span className="text-text-primary">balanced-congestion</span>
            </div>
            <div className="flex justify-between py-1.5">
              <span className="text-text-secondary">Validation version:</span>
              <span className="text-text-primary">validator-demo-0.1</span>
            </div>
            <div className="flex justify-between py-1.5">
              <span className="text-text-secondary">Result status:</span>
              <span className="text-accent-quantum font-medium">FEASIBLE</span>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
