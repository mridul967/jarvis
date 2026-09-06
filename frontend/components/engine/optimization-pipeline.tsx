"use client";

import React from "react";
import { ENGINE_PIPELINE_STAGES } from "../../lib/mock-data";

export function OptimizationPipeline() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-[20px] font-heading font-medium text-text-primary">
          End-to-end optimization pipeline
        </h2>
        <p className="text-[15px] text-text-secondary mt-1 max-w-[65ch]">
          The engine coordinates specialized agents to decouple graph preprocessing, candidate
          generation, combinatorial reconciliation, and hard validation.
        </p>
      </div>

      <div className="relative pl-6 md:pl-8 border-l border-hairline-strong space-y-6 ml-3">
        {ENGINE_PIPELINE_STAGES.map((stage, idx) => (
          <div key={idx} className="relative group">
            {/* Stage indicator node */}
            <div className="absolute -left-[31px] md:-left-[39px] top-6 w-3.5 h-3.5 rounded-full bg-ink-base border-2 border-accent-quantum" />

            <div className="bg-ink-panel border border-hairline rounded-md p-5 min-h-[80px] space-y-2 hover:border-hairline-strong transition-colors">
              <div className="flex flex-wrap items-center justify-between gap-2 border-b border-hairline pb-2.5">
                <div className="flex items-center gap-3">
                  <span className="text-[11px] font-mono text-accent-classical font-medium">
                    {stage.step}
                  </span>
                  <span className="text-hairline-strong hidden sm:inline">|</span>
                  <h3 className="text-[16px] font-heading font-medium text-text-primary">
                    {stage.title}
                  </h3>
                </div>
                <div className="px-2 py-0.5 rounded-sm bg-ink-base border border-hairline text-[11px] font-mono text-text-secondary">
                  Agents: <span className="text-text-primary">{stage.agents}</span>
                </div>
              </div>

              <p className="text-[13px] text-text-secondary leading-relaxed font-sans">
                {stage.description}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
