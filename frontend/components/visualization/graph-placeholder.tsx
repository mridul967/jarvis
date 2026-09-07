"use client";

import React from "react";
import { DemoGraph } from "../../lib/demo-types";

const ROUTE_COLORS = ["#4FB8AE", "#D98E3F", "#8AB4F8", "#D783B9", "#A9C46C"];

interface GraphPlaceholderProps {
  state: "idle" | "running" | "done";
  pulseActive: boolean;
  graph: DemoGraph | null;
  routes: number[][];
}

export function GraphPlaceholder({ state, pulseActive, graph, routes }: GraphPlaceholderProps) {
  const nodes = new Map(graph?.nodes.map((node) => [node.id, node]) ?? []);

  return (
    <div
      className={`relative min-h-[520px] w-full bg-ink-panel rounded-lg border p-5 transition-colors duration-200 ${
        pulseActive ? "graph-pulse-active border-accent-quantum" : "border-hairline"
      }`}
    >
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-hairline pb-3 text-[11px] font-mono text-text-secondary">
        <span>{graph?.name ?? "Loading NetworkX snapshot…"}</span>
        <span>
          {state.toUpperCase()} · {graph?.nodes.length ?? 0} nodes · {graph?.edges.length ?? 0} edges
        </span>
      </div>

      <svg
        viewBox="0 0 100 100"
        className="w-full h-[430px] mt-3"
        role="img"
        aria-label="Bengaluru directed routing graph"
      >
        <defs>
          <marker id="arrow" markerWidth="5" markerHeight="5" refX="4" refY="2.5" orient="auto">
            <path d="M0,0 L5,2.5 L0,5 Z" fill="#3A3F47" />
          </marker>
        </defs>
        {graph?.edges.map((edge) => {
          const source = nodes.get(edge.source);
          const target = nodes.get(edge.target);
          if (!source || !target) return null;
          return (
            <line
              key={`${edge.source}-${edge.target}`}
              x1={source.x}
              y1={source.y}
              x2={target.x}
              y2={target.y}
              stroke={
                edge.shocked
                  ? "#D85A4A"
                  : edge.gat_score !== null && edge.gat_score > 0.55
                    ? "#2E6E68"
                    : "#2E333B"
              }
              strokeWidth={edge.shocked ? 0.9 : 0.35}
              opacity={edge.shocked ? 0.95 : 0.7}
              markerEnd="url(#arrow)"
            />
          );
        })}
        {routes.map((route, routeIndex) => {
          const stops = route[0] === 0 ? route : [0, ...route, 0];
          const points = stops
            .map((id) => nodes.get(id))
            .filter((node): node is NonNullable<typeof node> => Boolean(node))
            .map((node) => `${node.x},${node.y}`)
            .join(" ");
          return (
            <polyline
              key={`route-${routeIndex}`}
              points={points}
              fill="none"
              stroke={ROUTE_COLORS[routeIndex % ROUTE_COLORS.length]}
              strokeWidth="1.2"
              strokeLinejoin="round"
              strokeLinecap="round"
              opacity="0.95"
            />
          );
        })}
        {graph?.nodes.map((node) => (
          <g key={node.id}>
            <circle
              cx={node.x}
              cy={node.y}
              r={node.is_depot ? 2.4 : 1.55}
              fill={node.is_depot ? "#D98E3F" : "#14171C"}
              stroke={node.is_depot ? "#E9E6DD" : "#4FB8AE"}
              strokeWidth="0.65"
            />
            <text
              x={node.x + 1.8}
              y={node.y - 1.3}
              fill="#E9E6DD"
              fontSize="2.15"
              fontFamily="monospace"
            >
              {node.id}. {node.road}
            </text>
          </g>
        ))}
      </svg>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 border-t border-hairline pt-3 text-[11px] font-mono text-text-secondary">
        <span>Red: traffic shock</span>
        <span>Teal: GAT-prior edge</span>
        <span>Amber node: depot</span>
        <span>Colored paths: vehicles</span>
      </div>
    </div>
  );
}
