"use client";

/**
 * GATInferencePanel — calls POST /api/v1/gat/infer on the backend.
 *
 * Uses the toy 6-node synthetic graph from the spec self-check as the
 * default payload so you can test end-to-end without building a real graph.
 * All fields are editable raw JSON for flexibility.
 */

import React, { useState } from "react";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

const DEFAULT_NODE_FEATURES = [
  [0.0, 0.0, 2.0],
  [1.0, 0.5, 2.0],
  [2.0, 1.0, 2.0],
  [3.0, 1.5, 2.0],
  [4.0, 2.0, 2.0],
  [5.0, 2.5, 2.0],
];

const DEFAULT_EDGE_INDEX = [
  [0, 1], [1, 2], [2, 3], [3, 4], [4, 5], [0, 2], [2, 5], [1, 4],
];

const DEFAULT_EDGE_FEATURES = [
  [1.0, 40.0, 2.0],
  [1.0, 40.0, 2.0],
  [1.0, 40.0, 2.0],
  [1.0, 40.0, 2.0],
  [1.0, 40.0, 2.0],
  [2.0, 40.0, 2.0],
  [3.0, 40.0, 2.0],
  [3.0, 40.0, 2.0],
];

type Mode = "search_space" | "edge_weight" | "both";

interface GATResult {
  mode: string;
  edge_scores?: number[];
  reduced_search_space?: Record<string, [number, number, number][]>;
  search_space_trained?: boolean;
  predicted_weights?: number[];
  edge_weight_trained?: boolean;
}

export function GATInferencePanel() {
  const [mode, setMode] = useState<Mode>("both");
  const [topK, setTopK] = useState(3);
  const [nodeJson, setNodeJson] = useState(JSON.stringify(DEFAULT_NODE_FEATURES, null, 2));
  const [edgeIdxJson, setEdgeIdxJson] = useState(JSON.stringify(DEFAULT_EDGE_INDEX, null, 2));
  const [edgeFeatJson, setEdgeFeatJson] = useState(JSON.stringify(DEFAULT_EDGE_FEATURES, null, 2));
  const [result, setResult] = useState<GATResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function runInference() {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const body = {
        node_features: JSON.parse(nodeJson),
        edge_index: JSON.parse(edgeIdxJson),
        edge_features: JSON.parse(edgeFeatJson),
        mode,
        top_k: topK,
      };
      const res = await fetch(`${BACKEND_URL}/api/v1/gat/infer`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!res.ok) {
        const text = await res.text();
        throw new Error(`${res.status}: ${text}`);
      }
      setResult(await res.json());
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-[20px] font-heading font-medium text-text-primary">
          GAT Inference
        </h2>
        <p className="text-[13px] text-text-secondary mt-1 max-w-[65ch]">
          Run the Graph Attention Network forward pass on a directed road graph.
          Defaults are the spec self-check toy graph (6 nodes, 8 edges).
        </p>
      </div>

      {/* Controls row */}
      <div className="flex flex-wrap gap-4 items-end">
        <div className="space-y-1">
          <label className="text-[12px] font-mono text-text-secondary block">Mode</label>
          <div className="flex gap-2" role="radiogroup">
            {(["search_space", "edge_weight", "both"] as Mode[]).map((m) => (
              <button
                key={m}
                type="button"
                onClick={() => setMode(m)}
                className={`px-3 py-1.5 rounded-sm border text-[12px] font-mono transition-colors ${
                  mode === m
                    ? "border-accent-quantum text-accent-quantum bg-ink-panel-raised"
                    : "border-hairline text-text-secondary hover:text-text-primary"
                }`}
              >
                {m}
              </button>
            ))}
          </div>
        </div>

        <div className="space-y-1">
          <label htmlFor="top-k" className="text-[12px] font-mono text-text-secondary block">
            top_k
          </label>
          <input
            id="top-k"
            type="number"
            min={1}
            max={64}
            value={topK}
            onChange={(e) => setTopK(Number(e.target.value))}
            className="w-20 h-9 px-2 rounded-sm bg-ink-base border border-hairline text-text-primary text-[13px] font-mono focus:outline-none focus:border-accent-quantum"
          />
        </div>

        <button
          type="button"
          disabled={loading}
          onClick={runInference}
          className="h-9 px-5 rounded-md bg-accent-classical text-ink-base font-medium text-[14px] hover:bg-accent-classical/90 transition-colors disabled:opacity-40 focus:outline-none"
        >
          {loading ? "Running…" : "Run inference"}
        </button>
      </div>

      {/* JSON editors */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {[
          { label: "node_features  [[lat, lon, degree], …]", val: nodeJson, set: setNodeJson },
          { label: "edge_index  [[src, dst], …]", val: edgeIdxJson, set: setEdgeIdxJson },
          { label: "edge_features  [[length, speed_limit, lanes], …]", val: edgeFeatJson, set: setEdgeFeatJson },
        ].map(({ label, val, set }) => (
          <div key={label} className="space-y-1">
            <label className="text-[11px] font-mono text-text-secondary block">{label}</label>
            <textarea
              value={val}
              onChange={(e) => set(e.target.value)}
              rows={8}
              spellCheck={false}
              className="w-full rounded-md bg-ink-base border border-hairline text-text-primary text-[12px] font-mono p-3 focus:outline-none focus:border-accent-quantum resize-y"
            />
          </div>
        ))}
      </div>

      {/* Error */}
      {error && (
        <div className="p-4 rounded-md border border-status-danger/40 bg-status-danger/10 text-status-danger text-[13px] font-mono">
          {error}
        </div>
      )}

      {/* Results */}
      {result && (
        <div className="space-y-4">
          {/* Trained flags */}
          <div className="flex gap-4 flex-wrap">
            {result.search_space_trained !== undefined && (
              <span className={`text-[12px] font-mono px-2 py-0.5 rounded-sm border ${
                result.search_space_trained
                  ? "border-accent-quantum/40 text-accent-quantum bg-accent-quantum/10"
                  : "border-hairline text-text-secondary bg-ink-base"
              }`}>
                search_space_gat: {result.search_space_trained ? "trained ✓" : "untrained (random weights)"}
              </span>
            )}
            {result.edge_weight_trained !== undefined && (
              <span className={`text-[12px] font-mono px-2 py-0.5 rounded-sm border ${
                result.edge_weight_trained
                  ? "border-accent-quantum/40 text-accent-quantum bg-accent-quantum/10"
                  : "border-hairline text-text-secondary bg-ink-base"
              }`}>
                edge_weight_gat: {result.edge_weight_trained ? "trained ✓" : "untrained (random weights)"}
              </span>
            )}
          </div>

          {/* Edge scores */}
          {result.edge_scores && (
            <div className="bg-ink-panel border border-hairline rounded-md p-5 space-y-3">
              <h3 className="text-[14px] font-heading font-medium text-text-primary">
                Edge scores — P(edge ∈ good route)
              </h3>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                {result.edge_scores.map((s, i) => (
                  <div key={i} className="p-2 bg-ink-base border border-hairline rounded-sm font-mono text-[12px]">
                    <span className="text-text-secondary block">edge {i}</span>
                    <span className="text-accent-quantum font-medium">{s.toFixed(4)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Reduced search space */}
          {result.reduced_search_space && (
            <div className="bg-ink-panel border border-hairline rounded-md p-5 space-y-3">
              <h3 className="text-[14px] font-heading font-medium text-text-primary">
                Reduced search space — top-{topK} edges per source node
              </h3>
              <div className="overflow-x-auto">
                <table className="w-full text-[12px] font-mono">
                  <thead className="border-b border-hairline text-text-secondary text-[11px]">
                    <tr>
                      <th className="py-2 px-3 text-left">src</th>
                      <th className="py-2 px-3 text-left">dst → score</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-hairline">
                    {Object.entries(result.reduced_search_space).map(([src, edges]) => (
                      <tr key={src} className="hover:bg-ink-panel-raised/40">
                        <td className="py-2 px-3 text-accent-classical font-medium">node {src}</td>
                        <td className="py-2 px-3 text-text-primary">
                          {edges.map(([dst, sc]) => `${dst} (${(sc as number).toFixed(3)})`).join("  ·  ")}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Predicted weights */}
          {result.predicted_weights && (
            <div className="bg-ink-panel border border-hairline rounded-md p-5 space-y-3">
              <h3 className="text-[14px] font-heading font-medium text-text-primary">
                Predicted edge weights — GAT-estimated travel cost
              </h3>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                {result.predicted_weights.map((w, i) => (
                  <div key={i} className="p-2 bg-ink-base border border-hairline rounded-sm font-mono text-[12px]">
                    <span className="text-text-secondary block">edge {i}</span>
                    <span className="text-accent-classical font-medium">{w.toFixed(4)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
