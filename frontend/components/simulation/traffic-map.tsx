"use client";

import React from "react";

export interface SimulationGraph {
  nodes: { id: string; latitude: number; longitude: number; signalized: boolean }[];
  edges: { id: string; source: string; target: string }[];
}
export interface SimulationFrame {
  tick: number; timestamp_s: number; active_shocks: string[];
  edges: { edge_id: string; source: string; target: string; congestion: number; travel_time_s: number; flow: number; capacity: number }[];
  vehicles: { vehicle_id: string; current_node: string; current_edge: string; progress: number; status: string; vehicle_type: string; route: string[] }[];
  agents: { node_id: string; queue_length: number; predicted_pressure: number }[];
}
interface TrafficMapProps { graph: SimulationGraph; frame: SimulationFrame | null; selectedVehicle: string | null; onSelectVehicle: (id: string) => void }
const colors = ["#4FB8AE", "#D98E3F", "#D85A4A"];

export function TrafficMap({ graph, frame, selectedVehicle, onSelectVehicle }: TrafficMapProps) {
  const minLat = Math.min(...graph.nodes.map((node) => node.latitude)); const maxLat = Math.max(...graph.nodes.map((node) => node.latitude));
  const minLon = Math.min(...graph.nodes.map((node) => node.longitude)); const maxLon = Math.max(...graph.nodes.map((node) => node.longitude));
  const point = (id: string) => { const node = graph.nodes.find((item) => item.id === id); if (!node) return { x: 0, y: 0 }; return { x: 70 + ((node.longitude - minLon) / (maxLon - minLon || 1)) * 760, y: 55 + ((maxLat - node.latitude) / (maxLat - minLat || 1)) * 330 }; };
  const edgeById = new Map((frame?.edges ?? []).map((edge) => [edge.edge_id, edge])); const agentById = new Map((frame?.agents ?? []).map((agent) => [agent.node_id, agent]));
  return <div className="relative rounded-lg border border-hairline bg-ink-panel overflow-hidden"><div className="absolute z-10 left-4 top-4 right-4 flex justify-between text-[11px] font-mono text-text-secondary"><span>LIVE NETWORKX REPLAY · BENGALURU / 9 NODES</span><span>{frame ? `${Math.floor(frame.timestamp_s / 60).toString().padStart(2, "0")}:${Math.floor(frame.timestamp_s % 60).toString().padStart(2, "0")}` : "READY"}</span></div><svg viewBox="0 0 900 440" className="w-full h-auto min-h-[420px] bg-[#171b20]" role="img" aria-label="Animated traffic simulation map"><defs><pattern id="grid" width="36" height="36" patternUnits="userSpaceOnUse"><path d="M 36 0 L 0 0 0 36" fill="none" stroke="#252b32" strokeWidth="1" /></pattern></defs><rect width="900" height="440" fill="url(#grid)" />{graph.edges.map((baseEdge) => { const source = point(baseEdge.source); const target = point(baseEdge.target); const live = edgeById.get(baseEdge.id); const congestion = live?.congestion ?? 0; return <line key={baseEdge.id} x1={source.x} y1={source.y} x2={target.x} y2={target.y} stroke={colors[Math.min(2, Math.floor(congestion * 3))]} strokeWidth={live?.travel_time_s && live.travel_time_s > 100 ? 6 : 3} opacity={0.8} strokeLinecap="round" />; })}{graph.nodes.map((node) => { const p = point(node.id); const agent = agentById.get(node.id); const pressure = agent?.predicted_pressure ?? 0; return <g key={node.id}><circle cx={p.x} cy={p.y} r={10 + pressure * 8} fill={pressure > 0.65 ? "#D85A4A" : "#4FB8AE"} opacity={0.22} /><circle cx={p.x} cy={p.y} r="6" fill="#E9E6DD" stroke="#14171C" strokeWidth="3" /><text x={p.x + 10} y={p.y - 10} fill="#8A8F98" fontSize="11" fontFamily="monospace">{node.id.replace("j-", "J")}</text></g>; })}{(frame?.vehicles ?? []).map((vehicle) => { const p = point(vehicle.current_node); const color = vehicle.vehicle_type === "bus" ? "#D98E3F" : "#4FB8AE"; return <g key={vehicle.vehicle_id} onClick={() => onSelectVehicle(vehicle.vehicle_id)} className="cursor-pointer"><circle cx={p.x} cy={p.y} r={selectedVehicle === vehicle.vehicle_id ? 12 : 8} fill={color} stroke={selectedVehicle === vehicle.vehicle_id ? "#E9E6DD" : "#14171C"} strokeWidth="3"><animate attributeName="r" values="7;10;7" dur="1.8s" repeatCount="indefinite" /></circle><text x={p.x + 12} y={p.y + 4} fill="#E9E6DD" fontSize="10" fontFamily="monospace">{vehicle.vehicle_id}</text></g>; })}</svg><div className="px-4 py-3 border-t border-hairline flex flex-wrap gap-4 text-[11px] font-mono text-text-secondary"><span><i className="inline-block w-2 h-2 rounded-full bg-accent-quantum mr-2" />free flow</span><span><i className="inline-block w-2 h-2 rounded-full bg-accent-classical mr-2" />moderate</span><span><i className="inline-block w-2 h-2 rounded-full bg-status-danger mr-2" />shock / pressure</span><span className="ml-auto">{frame?.active_shocks.length ? `ACTIVE: ${frame.active_shocks.join(", ")}` : "NO ACTIVE SHOCK"}</span></div></div>;
}
