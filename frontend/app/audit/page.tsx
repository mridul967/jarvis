"use client";

import { useEffect, useMemo, useState } from "react";

type Audit = { run_id: string; event_count: number; updated_at: number };
type Event = { event_id: string; tick: number; timestamp_s: number; vehicle_id: string; engine: string; prediction: { model: string; predicted_pressure: number }; selected_offer: { route: string[]; predicted_arrival_s: number }; reason_codes: string[] };

export default function AuditPage() {
  const [audits, setAudits] = useState<Audit[]>([]);
  const [runId, setRunId] = useState("");
  const [events, setEvents] = useState<Event[]>([]);
  const [error, setError] = useState("");

  useEffect(() => { fetch("/api/simulations/audits").then((response) => response.json()).then((items) => { setAudits(items); const saved = window.localStorage.getItem("latestSimulationRunId"); setRunId(saved || items[0]?.run_id || ""); }).catch(() => setError("Could not load audit runs.")); }, []);
  useEffect(() => { if (!runId) return; fetch(`/api/simulations/${runId}/events`).then((response) => response.json()).then((items) => Array.isArray(items) ? setEvents(items) : setError(items.detail || "Could not load audit events.")).catch(() => setError("Could not load audit events.")); }, [runId]);

  const algorithms = useMemo(() => Object.entries(events.reduce<Record<string, number>>((counts, event) => ({ ...counts, [event.engine]: (counts[event.engine] || 0) + 1 }), {})), [events]);
  const pressure = events.length ? (events.reduce((total, event) => total + event.prediction.predicted_pressure, 0) / events.length).toFixed(3) : "—";

  return <div className="space-y-6"><div><span className="block mb-1 font-mono text-[13px] text-accent-quantum">APPEND-ONLY JSONL AUDIT</span><h1 className="text-[32px] font-heading">Simulation audit</h1><p className="mt-1 text-text-secondary">Decision records, local inference, and candidate engines used by each replay.</p></div>
    <select aria-label="Simulation audit run" value={runId} onChange={(event) => setRunId(event.target.value)} className="w-full rounded-md border border-hairline bg-ink-panel p-3 font-mono text-sm text-text-primary"><option value="">Select a run</option>{audits.map((audit) => <option key={audit.run_id} value={audit.run_id}>{audit.run_id} · {audit.event_count} decisions</option>)}</select>
    {error && <p role="alert" className="rounded border border-status-danger/50 p-3 text-status-danger">{error}</p>}
    <div className="grid gap-4 md:grid-cols-3"><div className="rounded-md border border-hairline bg-ink-panel p-4"><p className="text-xs text-text-secondary">DECISIONS</p><p className="mt-1 font-mono text-2xl">{events.length}</p></div><div className="rounded-md border border-hairline bg-ink-panel p-4"><p className="text-xs text-text-secondary">INFERENCE</p><p className="mt-1 font-mono text-sm">heuristic_pressure_v1 · {pressure}</p></div><div className="rounded-md border border-hairline bg-ink-panel p-4"><p className="text-xs text-text-secondary">ALGORITHMS</p>{algorithms.map(([name, count]) => <p key={name} className="mt-1 font-mono text-xs">{name}: {count}</p>)}</div></div>
    <div className="overflow-x-auto rounded-md border border-hairline"><table className="w-full text-left text-xs"><thead className="bg-ink-panel text-text-secondary"><tr><th className="p-3">Tick</th><th>Vehicle</th><th>Engine</th><th>Inference</th><th>Route</th><th>Reasons</th></tr></thead><tbody>{events.map((event) => <tr key={event.event_id} className="border-t border-hairline"><td className="p-3 font-mono">{event.tick}</td><td>{event.vehicle_id}</td><td className="font-mono">{event.engine}</td><td>{event.prediction.model}: {event.prediction.predicted_pressure}</td><td className="font-mono">{event.selected_offer.route.join(" → ")}</td><td>{event.reason_codes.join(", ")}</td></tr>)}</tbody></table></div>
    <details className="rounded-md border border-hairline bg-ink-panel p-4"><summary className="cursor-pointer text-sm">Raw JSONL records</summary><pre className="mt-3 max-h-96 overflow-auto text-xs text-text-secondary">{events.map((event) => JSON.stringify(event)).join("\n")}</pre></details>
  </div>;
}
