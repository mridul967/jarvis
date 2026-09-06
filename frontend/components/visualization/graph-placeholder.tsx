"use client";

import React from "react";
import { DatasetOption } from "../../lib/mock-data";

interface GraphPlaceholderProps {
  state: "idle" | "running" | "done";
  pulseActive: boolean;
  selectedDataset: DatasetOption | null;
  selectedMode: string;
}

export function GraphPlaceholder({
  state,
  pulseActive,
  selectedDataset,
  selectedMode,
}: GraphPlaceholderProps) {
  {/* TODO(backend): replace this panel with the NetworkX-rendered graph
      once the Graph Agent / graph snapshot endpoint exists (spec §5.2, §9.3).
      Once wired, this is where the colored route line animation will render.
      The stroke will trace the edge sequence currently being considered by
      the solver, updated from:
      GET /api/v1/jobs/{job_id}/events
      as defined in spec §12.2 and §12.5. */}

  const stateSubtitle =
    state === "running"
      ? "Simulation active"
      : state === "done"
      ? "Snapshot complete"
      : "NetworkX graph viewport · awaiting graph snapshot";

  const nodeCount = selectedDataset ? selectedDataset.nodeCount : 96;
  const edgeCount = selectedDataset ? selectedDataset.edgeCount : 142;
  const snapshotLabel = selectedDataset
    ? selectedDataset.snapshotId
    : "synthetic-urban-042";

  return (
    <div
      className={`relative min-h-[480px] w-full bg-ink-panel rounded-lg border flex flex-col justify-between p-6 transition-colors duration-200 ${
        pulseActive ? "graph-pulse-active border-accent-quantum" : "border-hairline"
      }`}
    >
      {/* Top metadata header */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-hairline pb-4 text-[11px] font-mono text-text-secondary">
        <div className="flex items-center gap-2">
          <span className="inline-block w-2 h-2 rounded-full bg-hairline-strong" />
          <span>Viewport: NetworkX Canvas Target</span>
        </div>
        <div className="flex items-center gap-3">
          <span>Mode: {selectedMode.toUpperCase()}</span>
          <span>·</span>
          <span>Snapshot: {snapshotLabel}</span>
        </div>
      </div>

      {/* Centered Monospace Viewport Labels */}
      <div className="my-auto flex flex-col items-center justify-center py-16 text-center space-y-3">
        <div className="p-3 rounded-md bg-ink-base border border-hairline font-mono text-[13px] text-text-primary max-w-md">
          Graph visualization renders here
        </div>
        <div className="text-[13px] font-mono text-text-secondary">
          {stateSubtitle}
        </div>
        <div className="text-[11px] font-mono text-text-secondary/70 max-w-sm">
          Awaiting NetworkX / Graph Agent snapshot stream via GET /api/v1/jobs/&#123;job_id&#125;/events
        </div>
      </div>

      {/* Bottom Mock Metadata Table (labeled as illustrative synthetic values) */}
      <div className="border-t border-hairline pt-4 grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 text-[11px] font-mono">
        <div>
          <span className="text-text-secondary block">Synthetic graph:</span>
          <span className="text-text-primary">Urban Arterial</span>
        </div>
        <div>
          <span className="text-text-secondary block">Nodes:</span>
          <span className="text-text-primary">{nodeCount}</span>
        </div>
        <div>
          <span className="text-text-secondary block">Edges:</span>
          <span className="text-text-primary">{edgeCount}</span>
        </div>
        <div>
          <span className="text-text-secondary block">Directed graph:</span>
          <span className="text-text-primary">Yes</span>
        </div>
        <div>
          <span className="text-text-secondary block">Weight model:</span>
          <span className="text-accent-quantum">BPR-style</span>
        </div>
        <div>
          <span className="text-text-secondary block">Update interval:</span>
          <span className="text-text-primary">1 second</span>
        </div>
      </div>
    </div>
  );
}
