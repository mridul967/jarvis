"use client";

import React from "react";
import { KatexMath } from "../shared/katex-math";

// TODO(backend): Replace these mock values with DynamicEdgeCost and
// TrafficSnapshot data returned by the future FastAPI traffic endpoint.
// See spec §5.3, §9.3, and §9.4.

interface DynamicCostPanelProps {
  edgeCost: {
    t0: number;
    flow: number;
    capacity: number;
    alpha: number;
    beta: number;
    travelTime: number;
    congestionDelay: number;
    incidentFactor: number;
  };
}

export function DynamicCostPanel({ edgeCost }: DynamicCostPanelProps) {
  return (
    <div className="bg-ink-panel border border-hairline rounded-md p-6 space-y-4">
      <div className="flex items-center justify-between border-b border-hairline pb-3">
        <h3 className="text-[15px] font-heading font-medium text-text-primary">
          Dynamic edge cost
        </h3>
        <span className="text-[11px] font-mono text-accent-quantum bg-ink-base px-2 py-0.5 rounded-sm border border-hairline">
          BPR model
        </span>
      </div>

      {/* KaTeX formula */}
      <div className="p-3 bg-ink-base border border-hairline rounded-sm flex items-center justify-center overflow-x-auto text-[14px]">
        <KatexMath
          math={"t_e(f_e) = t_e^0 \\left[ 1 + \\alpha \\left(\\frac{f_e}{C_e}\\right)^\\beta \\right]"}
          block
        />
      </div>

      {/* IBM Plex Mono readouts */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 text-[13px] font-mono pt-1">
        <div className="p-2.5 bg-ink-base rounded-sm border border-hairline">
          <span className="text-text-secondary text-[11px] block">t0 (free flow):</span>
          <span className="text-text-primary font-medium">{edgeCost.t0.toFixed(1)}s</span>
        </div>

        <div className="p-2.5 bg-ink-base rounded-sm border border-hairline">
          <span className="text-text-secondary text-[11px] block">f (flow veh/h):</span>
          <span className="text-text-primary font-medium">{edgeCost.flow}</span>
        </div>

        <div className="p-2.5 bg-ink-base rounded-sm border border-hairline">
          <span className="text-text-secondary text-[11px] block">C (capacity):</span>
          <span className="text-text-primary font-medium">{edgeCost.capacity}</span>
        </div>

        <div className="p-2.5 bg-ink-base rounded-sm border border-hairline">
          <span className="text-text-secondary text-[11px] block">α (alpha):</span>
          <span className="text-text-primary font-medium">{edgeCost.alpha.toFixed(2)}</span>
        </div>

        <div className="p-2.5 bg-ink-base rounded-sm border border-hairline">
          <span className="text-text-secondary text-[11px] block">β (beta):</span>
          <span className="text-text-primary font-medium">{edgeCost.beta}</span>
        </div>
      </div>

      {/* Edge travel time & delays */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-[13px] font-mono">
        <div className="p-2.5 bg-ink-base rounded-sm border border-hairline flex justify-between items-center">
          <span className="text-text-secondary text-[11px]">Travel time te:</span>
          <span className="text-accent-classical font-medium">{edgeCost.travelTime.toFixed(2)}s</span>
        </div>
        <div className="p-2.5 bg-ink-base rounded-sm border border-hairline flex justify-between items-center">
          <span className="text-text-secondary text-[11px]">Congestion delay:</span>
          <span className="text-text-primary font-medium">+{edgeCost.congestionDelay.toFixed(2)}s</span>
        </div>
        <div className="p-2.5 bg-ink-base rounded-sm border border-hairline flex justify-between items-center">
          <span className="text-text-secondary text-[11px]">Incident factor:</span>
          <span className="text-text-primary font-medium">{edgeCost.incidentFactor.toFixed(2)}x</span>
        </div>
      </div>

      <p className="text-[11px] font-mono text-text-secondary">
        Synthetic frontend simulation. Production values will come from the traffic snapshot service.
      </p>
    </div>
  );
}
