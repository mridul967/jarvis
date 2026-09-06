"use client";

import React from "react";
import { SOLVER_REGISTRY } from "../../lib/mock-data";

export function SolverPortfolio() {
  const classicalSolvers = SOLVER_REGISTRY.filter((s) => !s.isQuantum);
  const quantumSolvers = SOLVER_REGISTRY.filter((s) => s.isQuantum);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-[20px] font-heading font-medium text-text-primary">
          Solver portfolio
        </h2>
        <p className="text-[15px] text-text-secondary mt-1 max-w-[65ch]">
          The platform keeps classical fallbacks and quantum-inspired experiments in the same
          unified solver registry. Experimental methods do not bypass independent validation.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Classical Lane (Amber Accent) */}
        <div className="space-y-4">
          <div className="flex items-center justify-between pb-2 border-b border-hairline">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-sm bg-accent-classical" />
              <h3 className="text-[16px] font-heading font-medium text-text-primary">
                Classical & Exact Lane
              </h3>
            </div>
            <span className="text-[11px] font-mono text-text-secondary">
              Production baselines & MIP
            </span>
          </div>

          <div className="space-y-3">
            {classicalSolvers.map((s) => (
              <div
                key={s.id}
                className="p-4 bg-ink-panel border border-hairline rounded-md space-y-2 hover:border-hairline-strong transition-colors"
              >
                <div className="flex items-center justify-between">
                  <span className="text-[13px] font-mono font-medium text-accent-classical">
                    {s.id}
                  </span>
                  <span className="text-[11px] font-mono px-2 py-0.5 rounded-sm border border-hairline bg-ink-base text-text-secondary">
                    {s.statusLabel}
                  </span>
                </div>
                <div className="text-[14px] font-medium text-text-primary font-heading">
                  {s.name}
                </div>
                <p className="text-[13px] text-text-secondary font-sans">{s.role}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Quantum-Inspired Lane (Teal Accent) */}
        <div className="space-y-4">
          <div className="flex items-center justify-between pb-2 border-b border-hairline">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-sm bg-accent-quantum" />
              <h3 className="text-[16px] font-heading font-medium text-text-primary">
                Quantum-Inspired Lane
              </h3>
            </div>
            <span className="text-[11px] font-mono text-text-secondary">
              Combinatorial search & heuristic
            </span>
          </div>

          <div className="space-y-3">
            {quantumSolvers.map((s) => (
              <div
                key={s.id}
                className="p-4 bg-ink-panel border border-hairline rounded-md space-y-2 hover:border-hairline-strong transition-colors"
              >
                <div className="flex items-center justify-between">
                  <span className="text-[13px] font-mono font-medium text-accent-quantum">
                    {s.id}
                  </span>
                  <span className="text-[11px] font-mono px-2 py-0.5 rounded-sm border border-accent-quantum/30 text-accent-quantum bg-accent-quantum/5">
                    {s.statusLabel}
                  </span>
                </div>
                <div className="text-[14px] font-medium text-text-primary font-heading">
                  {s.name}
                </div>
                <p className="text-[13px] text-text-secondary font-sans">{s.role}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
