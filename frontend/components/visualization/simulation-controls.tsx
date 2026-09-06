"use client";

import React from "react";
import {
  DATASET_OPTIONS,
  ROUTING_MODES,
  VISUALIZER_ALGORITHMS,
  TRAFFIC_CONDITIONS,
  OBJECTIVE_PROFILES,
  DatasetOption,
  AlgorithmOption,
} from "../../lib/mock-data";
import { ResultStatus, RoutingMode, SolverId } from "../../lib/types";

// TODO(backend): POST /api/v1/scenarios with the selected dataset,
// routing mode, objective profile, constraints, and solver policy.
// The local object currently represents a ScenarioSnapshot.

// TODO(backend): POST /api/v1/jobs with solver_policy.primary_solver
// set to the selected registry identifier.
// Replace the local simulation with the returned JobId.

interface SimulationControlsProps {
  selectedDatasetId: string;
  onSelectDataset: (id: string) => void;
  selectedMode: RoutingMode;
  onSelectMode: (mode: RoutingMode) => void;
  selectedAlgorithmId: SolverId | null;
  onSelectAlgorithm: (id: SolverId) => void;
  selectedTrafficId: string;
  onSelectTraffic: (id: string) => void;
  selectedObjectiveId: string;
  onSelectObjective: (id: string) => void;
  simulationState: "idle" | "running" | "done";
  onRunSimulation: () => void;
  onStopSimulation: () => void;
  onResetSimulation: () => void;
  iteration: number;
  elapsedSec: number;
  statusText: ResultStatus;
}

export function SimulationControls({
  selectedDatasetId,
  onSelectDataset,
  selectedMode,
  onSelectMode,
  selectedAlgorithmId,
  onSelectAlgorithm,
  selectedTrafficId,
  onSelectTraffic,
  selectedObjectiveId,
  onSelectObjective,
  simulationState,
  onRunSimulation,
  onStopSimulation,
  onResetSimulation,
  iteration,
  elapsedSec,
  statusText,
}: SimulationControlsProps) {
  const isRunnable = Boolean(selectedDatasetId && selectedAlgorithmId);

  const selectedSolverObj = VISUALIZER_ALGORITHMS.find(
    (a) => a.id === selectedAlgorithmId
  );
  const selectedTrafficObj = TRAFFIC_CONDITIONS.find(
    (t) => t.id === selectedTrafficId
  );

  return (
    <div className="w-full md:w-[320px] shrink-0 bg-ink-panel border-b md:border-b-0 md:border-r border-hairline p-6 flex flex-col gap-6">
      <div>
        <h2 className="text-[17px] font-heading font-medium text-text-primary">
          Scenario configuration
        </h2>
        <p className="text-[13px] text-text-secondary mt-1">
          Synthetic parameters for the optimization run.
        </p>
      </div>

      {/* Dataset Selection */}
      <div className="space-y-2">
        <label
          htmlFor="dataset-select"
          className="text-[13px] font-medium text-text-primary block font-sans"
        >
          Dataset
        </label>
        <select
          id="dataset-select"
          value={selectedDatasetId}
          disabled={simulationState === "running"}
          onChange={(e) => onSelectDataset(e.target.value)}
          className="w-full h-10 px-3 rounded-md bg-ink-base border border-hairline text-text-primary text-[13px] focus:outline-none focus:border-accent-quantum disabled:opacity-50"
        >
          <option value="">Select a dataset</option>
          {DATASET_OPTIONS.map((d) => (
            <option key={d.id} value={d.id}>
              {d.name}
            </option>
          ))}
        </select>
      </div>

      {/* Routing Mode */}
      <div className="space-y-2">
        <label className="text-[13px] font-medium text-text-primary block font-sans">
          Routing mode
        </label>
        <div className="grid grid-cols-2 gap-2" role="radiogroup" aria-label="Routing mode">
          {ROUTING_MODES.map((m) => {
            const isSelected = selectedMode === m.id;
            return (
              <button
                key={m.id}
                type="button"
                role="radio"
                aria-checked={isSelected}
                disabled={simulationState === "running"}
                onClick={() => onSelectMode(m.id)}
                className={`py-2 px-3 rounded-sm border text-left text-[13px] font-mono transition-colors disabled:opacity-50 ${
                  isSelected
                    ? "bg-ink-panel-raised border-accent-quantum text-accent-quantum"
                    : "bg-ink-base border-hairline text-text-secondary hover:text-text-primary"
                }`}
              >
                {m.id.toUpperCase()}
              </button>
            );
          })}
        </div>
      </div>

      {/* Algorithm Selection: Vertical Chips */}
      <div className="space-y-2">
        <label className="text-[13px] font-medium text-text-primary block font-sans">
          Algorithm
        </label>
        <div className="space-y-2" role="radiogroup" aria-label="Optimization Algorithm">
          {VISUALIZER_ALGORITHMS.map((alg) => {
            const isSelected = selectedAlgorithmId === alg.id;
            const isTeal = alg.accent === "teal";

            return (
              <button
                key={alg.id}
                type="button"
                role="radio"
                aria-checked={isSelected}
                disabled={simulationState === "running"}
                onClick={() => onSelectAlgorithm(alg.id)}
                className={`w-full min-h-[44px] px-3 py-2 rounded-sm border flex items-center justify-between transition-colors text-left disabled:opacity-50 ${
                  isSelected
                    ? isTeal
                      ? "bg-ink-panel-raised border-accent-quantum text-accent-quantum"
                      : "bg-ink-panel-raised border-accent-classical text-accent-classical"
                    : "bg-ink-base border-hairline text-text-secondary hover:text-text-primary hover:border-hairline-strong"
                }`}
              >
                <div className="flex flex-col">
                  <span className="text-[13px] font-mono font-medium">
                    {alg.name}
                  </span>
                  <span className="text-[11px] font-sans text-text-secondary">
                    {alg.family}
                  </span>
                </div>
                <span
                  className={`text-[11px] font-mono px-2 py-0.5 rounded-sm border ${
                    isSelected
                      ? isTeal
                        ? "border-accent-quantum/40 text-accent-quantum"
                        : "border-accent-classical/40 text-accent-classical"
                      : "border-hairline text-text-secondary"
                  }`}
                >
                  {alg.badge}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Traffic Condition */}
      <div className="space-y-2">
        <label
          htmlFor="traffic-select"
          className="text-[13px] font-medium text-text-primary block font-sans"
        >
          Traffic condition
        </label>
        <select
          id="traffic-select"
          value={selectedTrafficId}
          disabled={simulationState === "running"}
          onChange={(e) => onSelectTraffic(e.target.value)}
          className="w-full h-10 px-3 rounded-md bg-ink-base border border-hairline text-text-primary text-[13px] focus:outline-none focus:border-accent-quantum disabled:opacity-50"
        >
          {TRAFFIC_CONDITIONS.map((t) => (
            <option key={t.id} value={t.id}>
              {t.label}
            </option>
          ))}
        </select>
      </div>

      {/* Objective Profile */}
      <div className="space-y-2">
        <label
          htmlFor="objective-select"
          className="text-[13px] font-medium text-text-primary block font-sans"
        >
          Objective profile
        </label>
        <select
          id="objective-select"
          value={selectedObjectiveId}
          disabled={simulationState === "running"}
          onChange={(e) => onSelectObjective(e.target.value)}
          className="w-full h-10 px-3 rounded-md bg-ink-base border border-hairline text-text-primary text-[13px] focus:outline-none focus:border-accent-quantum disabled:opacity-50"
        >
          {OBJECTIVE_PROFILES.map((o) => (
            <option key={o.id} value={o.id}>
              {o.label}
            </option>
          ))}
        </select>
      </div>

      <div className="border-t border-hairline pt-2" />

      {/* Action Button */}
      <div>
        {simulationState === "idle" && (
          <button
            type="button"
            disabled={!isRunnable}
            onClick={onRunSimulation}
            className="w-full h-12 rounded-md bg-accent-classical text-ink-base font-medium text-[15px] hover:bg-accent-classical/90 transition-colors disabled:opacity-40 disabled:cursor-not-allowed focus:outline-none"
          >
            Run visualization
          </button>
        )}

        {simulationState === "running" && (
          <button
            type="button"
            onClick={onStopSimulation}
            className="w-full h-12 rounded-md border border-status-danger text-status-danger font-medium text-[15px] hover:bg-status-danger/10 transition-colors focus:outline-none"
          >
            Stop simulation
          </button>
        )}

        {simulationState === "done" && (
          <button
            type="button"
            onClick={onResetSimulation}
            className="w-full h-12 rounded-md bg-accent-classical text-ink-base font-medium text-[15px] hover:bg-accent-classical/90 transition-colors focus:outline-none"
          >
            Run again
          </button>
        )}
      </div>

      {/* Status Readout */}
      <div className="p-3 bg-ink-base border border-hairline rounded-md text-[13px] font-mono space-y-1">
        <div className="flex justify-between">
          <span className="text-text-secondary">state:</span>
          <span className="text-text-primary">{simulationState}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-text-secondary">iteration:</span>
          <span className="text-text-primary">{iteration > 0 ? iteration : "—"}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-text-secondary">elapsed:</span>
          <span className="text-text-primary">
            {elapsedSec > 0 ? `00:0${elapsedSec}s` : "—"}
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-text-secondary">selected solver:</span>
          <span className="text-accent-quantum truncate max-w-[140px]">
            {selectedSolverObj ? selectedSolverObj.id : "—"}
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-text-secondary">traffic condition:</span>
          <span className="text-text-primary truncate max-w-[140px]">
            {selectedTrafficObj ? selectedTrafficObj.label : "—"}
          </span>
        </div>
        {simulationState === "done" && (
          <div className="flex justify-between pt-1 border-t border-hairline text-accent-quantum font-medium">
            <span className="text-text-secondary">result status:</span>
            <span>{statusText}</span>
          </div>
        )}
      </div>
    </div>
  );
}
