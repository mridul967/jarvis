"use client";

import React from "react";
import { ResultStatus } from "../../lib/types";

interface TelemetryPanelProps {
  iteration: number;
  elapsedSec: number;
  bestObjective: number;
  candidatesCount: number;
  trafficMultiplier: number;
  statusText: ResultStatus;
  currentDecision: string;
}

export function TelemetryPanel({
  iteration,
  elapsedSec,
  bestObjective,
  candidatesCount,
  trafficMultiplier,
  statusText,
  currentDecision,
}: TelemetryPanelProps) {
  const isStatusFeasible = statusText === "FEASIBLE" || statusText === "BEST_FOUND" || statusText === "OPTIMAL_PROVEN";
  const isStatusDanger = statusText === "INFEASIBLE" || statusText === "FAILED";

  return (
    <div className="bg-ink-panel border border-hairline rounded-md p-6 space-y-4">
      <div className="flex items-center justify-between border-b border-hairline pb-3">
        <h3 className="text-[15px] font-heading font-medium text-text-primary">
          Telemetry stream
        </h3>
        <span
          className={`text-[11px] font-mono px-2 py-0.5 rounded-sm border ${
            isStatusFeasible
              ? "border-accent-quantum/40 text-accent-quantum bg-accent-quantum/10"
              : isStatusDanger
              ? "border-status-danger/40 text-status-danger bg-status-danger/10"
              : "border-hairline text-text-secondary bg-ink-base"
          }`}
        >
          {statusText}
        </span>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-[13px] font-mono">
        <div className="p-2.5 bg-ink-base rounded-sm border border-hairline">
          <span className="text-text-secondary text-[11px] block">Iteration:</span>
          <span className="text-text-primary font-medium">{iteration > 0 ? iteration : "—"}</span>
        </div>

        <div className="p-2.5 bg-ink-base rounded-sm border border-hairline">
          <span className="text-text-secondary text-[11px] block">Elapsed:</span>
          <span className="text-text-primary font-medium">
            {elapsedSec > 0 ? `00:0${elapsedSec}s` : "00:00s"}
          </span>
        </div>

        <div className="p-2.5 bg-ink-base rounded-sm border border-hairline">
          <span className="text-text-secondary text-[11px] block">Best objective:</span>
          <span className="text-accent-classical font-medium">
            {bestObjective > 0 ? bestObjective.toFixed(1) : "—"}
          </span>
        </div>

        <div className="p-2.5 bg-ink-base rounded-sm border border-hairline">
          <span className="text-text-secondary text-[11px] block">Candidates:</span>
          <span className="text-text-primary font-medium">{candidatesCount}</span>
        </div>

        <div className="p-2.5 bg-ink-base rounded-sm border border-hairline">
          <span className="text-text-secondary text-[11px] block">Traffic mult:</span>
          <span className="text-text-primary font-medium">{trafficMultiplier.toFixed(2)}x</span>
        </div>

        <div className="p-2.5 bg-ink-base rounded-sm border border-hairline">
          <span className="text-text-secondary text-[11px] block">Feasibility:</span>
          <span
            className={`font-medium ${
              isStatusFeasible ? "text-accent-quantum" : "text-status-danger"
            }`}
          >
            {statusText}
          </span>
        </div>
      </div>

      <div className="p-3 bg-ink-base rounded-sm border border-hairline text-[13px] font-mono flex items-start gap-2">
        <span className="text-text-secondary shrink-0 text-[11px] mt-0.5">Decision:</span>
        <span className="text-text-primary">{currentDecision}</span>
      </div>
    </div>
  );
}
