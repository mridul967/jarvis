"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { TrafficMap, type SimulationFrame, type SimulationGraph } from "../../components/simulation/traffic-map";

type SimulationResult = {
  run_id: string;
  seed: number;
  graph: SimulationGraph;
  frames: SimulationFrame[];
  events: { vehicle_id: string; engine: string; prediction: { predicted_pressure: number }; selected_offer: { route: string[]; predicted_arrival_s: number } }[];
  vrp_source: { dimension?: number; capacity?: number };
};

const defaults = { seed: 42, vehicle_count: 16, ticks: 30 };

export default function VisualizePage() {
  const [result, setResult] = useState<SimulationResult | null>(null);
  const [frameIndex, setFrameIndex] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedVehicle, setSelectedVehicle] = useState<string | null>(null);

  const frame = result?.frames[frameIndex] ?? null;
  const selectedEvent = useMemo(
    () => result?.events.filter((event) => event.vehicle_id === selectedVehicle).at(-1),
    [result, selectedVehicle],
  );

  useEffect(() => {
    if (!playing || !result) return;
    const timer = window.setInterval(() => {
      setFrameIndex((current) => {
        if (current >= result.frames.length - 1) {
          setPlaying(false);
          return current;
        }
        return current + 1;
      });
    }, 700);
    return () => window.clearInterval(timer);
  }, [playing, result]);

  const start = useCallback(async () => {
    setLoading(true);
    setError(null);
    setPlaying(false);
    try {
      const created = await fetch("/api/simulations", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(defaults),
      });
      const summary = await created.json();
      if (!created.ok) throw new Error(summary.detail ?? "Could not create simulation");
      const replay = await fetch(`/api/simulations/${summary.run_id}`);
      const next = await replay.json();
      if (!replay.ok) throw new Error(next.detail ?? "Could not load simulation replay");
      setResult(next);
      setFrameIndex(0);
      setSelectedVehicle(null);
      setPlaying(true);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Could not load simulation");
    } finally {
      setLoading(false);
    }
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <span className="block mb-1 font-mono text-[13px] text-accent-quantum">REPLAYABLE SYNTHETIC SCENARIO</span>
          <h1 className="text-[32px] font-heading text-text-primary">Bengaluru traffic simulation</h1>
          <p className="mt-1 max-w-[65ch] text-[15px] text-text-secondary">BPR traffic, deterministic route negotiation, and incident-aware candidate engines.</p>
        </div>
        <button type="button" onClick={start} disabled={loading} className="rounded-md bg-accent-quantum px-4 py-2 text-[13px] font-medium text-ink-base disabled:opacity-60">
          {loading ? "Starting…" : result ? "Run again" : "Start simulation"}
        </button>
      </div>

      {error && <p role="alert" className="rounded-md border border-status-danger/50 bg-status-danger/10 p-3 text-sm text-status-danger">{error}</p>}

      {result ? (
        <div className="space-y-4">
          <TrafficMap graph={result.graph} frame={frame} selectedVehicle={selectedVehicle} onSelectVehicle={setSelectedVehicle} />
          <div className="flex flex-wrap items-center gap-3 rounded-md border border-hairline bg-ink-panel p-4">
            <button type="button" onClick={() => setPlaying((value) => !value)} className="rounded border border-hairline-strong px-3 py-1.5 text-sm">
              {playing ? "Pause" : "Play"}
            </button>
            <input aria-label="Replay timeline" className="min-w-48 flex-1 accent-accent-quantum" type="range" min="0" max={Math.max(0, result.frames.length - 1)} value={frameIndex} onChange={(event) => { setPlaying(false); setFrameIndex(Number(event.target.value)); }} />
            <span className="font-mono text-xs text-text-secondary">TICK {frameIndex + 1}/{result.frames.length} · seed {result.seed} · {result.vrp_source.dimension ?? "?"} stops</span>
          </div>
          {selectedVehicle && (
            <div className="rounded-md border border-hairline bg-ink-panel p-4 text-sm text-text-secondary">
              <span className="font-mono text-text-primary">{selectedVehicle}</span>{selectedEvent ? ` · ${selectedEvent.engine} chose ${selectedEvent.selected_offer.route.join(" → ")} (ETA ${Math.round(selectedEvent.selected_offer.predicted_arrival_s)}s, predicted pressure ${selectedEvent.prediction.predicted_pressure})` : " · no route offer yet"}
            </div>
          )}
        </div>
      ) : (
        <div className="rounded-lg border border-dashed border-hairline bg-ink-panel p-12 text-center text-sm text-text-secondary">Start a deterministic 16-vehicle, 30-tick replay.</div>
      )}
    </div>
  );
}
