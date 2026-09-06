"use client";

import React, { useState, useEffect, useRef, useMemo, useCallback } from "react";
import {
  DATASET_OPTIONS,
  SIMULATION_TIMELINE_STEPS,
  VISUALIZER_ALGORITHMS,
  SimulationStepData,
} from "../../lib/mock-data";
import { DecisionEvent, ResultStatus, RoutingMode, SolverId } from "../../lib/types";
import { GraphPlaceholder } from "../../components/visualization/graph-placeholder";
import { SimulationControls } from "../../components/visualization/simulation-controls";
import { DynamicCostPanel } from "../../components/visualization/dynamic-cost-panel";
import { TelemetryPanel } from "../../components/visualization/telemetry-panel";
import { DecisionTimeline } from "../../components/visualization/decision-timeline";

// TODO(backend): Replace this local interval with job progress events from
// GET /api/v1/jobs/{job_id}/events as defined in spec §12.2 and §12.5.
// The backend will eventually provide stage, progress, solver metrics,
// candidate counts, and validation state.

// TODO(backend): Replace this local result with:
// GET /api/v1/jobs/{job_id}/result
// and GET /api/v1/jobs/{job_id}/metrics.

export default function VisualizePage() {
  // Scenario Configuration State
  const [selectedDatasetId, setSelectedDatasetId] = useState<string>("delhi-ncr");
  const [selectedMode, setSelectedMode] = useState<RoutingMode>("vrptw");
  const [selectedAlgorithmId, setSelectedAlgorithmId] = useState<SolverId | null>("qaco_local");
  const [selectedTrafficId, setSelectedTrafficId] = useState<string>("peak");
  const [selectedObjectiveId, setSelectedObjectiveId] = useState<string>("balance");

  // Simulation Lifecycle State
  const [simulationState, setSimulationState] = useState<"idle" | "running" | "done">("idle");
  const [pulseActive, setPulseActive] = useState<boolean>(false);
  const [currentStepIndex, setCurrentStepIndex] = useState<number>(0);
  const [events, setEvents] = useState<DecisionEvent[]>([]);

  const timerRef = useRef<NodeJS.Timeout | null>(null);

  const selectedDataset = useMemo(
    () => DATASET_OPTIONS.find((d) => d.id === selectedDatasetId) || null,
    [selectedDatasetId]
  );

  const selectedAlgorithm = useMemo(
    () => VISUALIZER_ALGORITHMS.find((a) => a.id === selectedAlgorithmId) || null,
    [selectedAlgorithmId]
  );

  // Baseline telemetry values when idle
  const activeStep: SimulationStepData = useMemo(() => {
    if (simulationState === "idle") {
      return {
        iteration: 0,
        elapsedSec: 0,
        bestObjective: 0,
        candidatesCount: 0,
        trafficMultiplier: 1.0,
        statusText: "FEASIBLE" as ResultStatus,
        currentDecision: "Awaiting scenario trigger...",
        edgeCost: {
          t0: 4.2,
          flow: 812,
          capacity: 1200,
          alpha: 0.15,
          beta: 4.0,
          travelTime: 5.38,
          congestionDelay: 1.18,
          incidentFactor: 1.0,
        },
        event: {
          step: 0,
          timestamp: "00:00",
          target: "System Initialized",
          decision: "Explored",
          reason: "Baseline graph snapshot mounted",
          status: "Exploring",
        },
      };
    }
    const idx = Math.min(currentStepIndex, SIMULATION_TIMELINE_STEPS.length - 1);
    return SIMULATION_TIMELINE_STEPS[idx];
  }, [simulationState, currentStepIndex]);

  // Handle Stopping Simulation
  const handleStopSimulation = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
    setSimulationState("idle");
    setPulseActive(false);
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, []);

  // Handle Starting Simulation
  const handleRunSimulation = useCallback(() => {
    if (!selectedDatasetId || !selectedAlgorithmId) return;

    if (timerRef.current) {
      clearInterval(timerRef.current);
    }

    setSimulationState("running");
    setCurrentStepIndex(0);
    setEvents([SIMULATION_TIMELINE_STEPS[0].event]);

    // Motion Rule: The one visual motion moment.
    // Graph placeholder border briefly pulses to var(--accent-quantum) for 400ms and returns.
    setPulseActive(true);
    setTimeout(() => {
      setPulseActive(false);
    }, 400);

    let step = 0;
    timerRef.current = setInterval(() => {
      step += 1;
      if (step < SIMULATION_TIMELINE_STEPS.length) {
        setCurrentStepIndex(step);
        setEvents((prev) => [...prev, SIMULATION_TIMELINE_STEPS[step].event]);
      } else {
        if (timerRef.current) {
          clearInterval(timerRef.current);
          timerRef.current = null;
        }
        setSimulationState("done");
      }
    }, 1000);
  }, [selectedDatasetId, selectedAlgorithmId]);

  // Handle Reset / Run Again
  const handleResetSimulation = useCallback(() => {
    handleStopSimulation();
    handleRunSimulation();
  }, [handleStopSimulation, handleRunSimulation]);

  return (
    <div className="space-y-8">
      {/* Top Header */}
      <div>
        <span className="text-[13px] font-mono text-accent-quantum block mb-1">
          Synthetic algorithm visualizer
        </span>
        <h1 className="text-[32px] font-heading font-medium text-text-primary">
          Dynamic optimization run
        </h1>
        <p className="text-[15px] text-text-secondary mt-1 max-w-[65ch]">
          Simulate quantum-inspired metaheuristic search against dynamic BPR traffic conditions and
          track decision verification in real time.
        </p>
      </div>

      {/* Main Workspace Layout: Desktop Fixed 320px Controls + Flexible Stage */}
      <div className="flex flex-col md:flex-row border border-hairline rounded-md bg-ink-panel overflow-hidden">
        {/* Left Control Rail */}
        <SimulationControls
          selectedDatasetId={selectedDatasetId}
          onSelectDataset={setSelectedDatasetId}
          selectedMode={selectedMode}
          onSelectMode={setSelectedMode}
          selectedAlgorithmId={selectedAlgorithmId}
          onSelectAlgorithm={setSelectedAlgorithmId}
          selectedTrafficId={selectedTrafficId}
          onSelectTraffic={setSelectedTrafficId}
          selectedObjectiveId={selectedObjectiveId}
          onSelectObjective={setSelectedObjectiveId}
          simulationState={simulationState}
          onRunSimulation={handleRunSimulation}
          onStopSimulation={handleStopSimulation}
          onResetSimulation={handleResetSimulation}
          iteration={activeStep.iteration}
          elapsedSec={activeStep.elapsedSec}
          statusText={activeStep.statusText}
        />

        {/* Flexible Stage: Padding 24px */}
        <div className="flex-1 p-6 space-y-6 overflow-hidden">
          {/* Graph Placeholder Panel */}
          <GraphPlaceholder
            state={simulationState}
            pulseActive={pulseActive}
            selectedDataset={selectedDataset}
            selectedMode={selectedMode}
          />

          {/* Telemetry & Dynamic Equation Readouts */}
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
            <TelemetryPanel
              iteration={activeStep.iteration}
              elapsedSec={activeStep.elapsedSec}
              bestObjective={activeStep.bestObjective}
              candidatesCount={activeStep.candidatesCount}
              trafficMultiplier={activeStep.trafficMultiplier}
              statusText={activeStep.statusText}
              currentDecision={activeStep.currentDecision}
            />

            <DynamicCostPanel edgeCost={activeStep.edgeCost} />
          </div>

          {/* Decision Timeline */}
          <DecisionTimeline events={events} />

          {/* Summary Banner on Done */}
          {simulationState === "done" && (
            <div className="p-4 rounded-md border border-accent-quantum/40 bg-accent-quantum/5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
              <div className="space-y-1">
                <span className="text-[13px] font-mono text-accent-quantum font-medium">
                  Run complete: {activeStep.statusText}
                </span>
                <p className="text-[13px] text-text-secondary">
                  Evaluated {activeStep.candidatesCount} candidate routes. Best objective score:{" "}
                  <span className="text-text-primary font-mono font-medium">
                    {activeStep.bestObjective.toFixed(1)}
                  </span>
                  . All hard time-window and capacity constraints verified.
                </p>
              </div>
              <button
                type="button"
                onClick={handleResetSimulation}
                className="px-4 py-2 rounded-md bg-accent-classical text-ink-base text-[13px] font-medium hover:bg-accent-classical/90 transition-colors shrink-0"
              >
                Run again
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Visualization Footer */}
      <footer className="pt-6 border-t border-hairline flex flex-wrap items-center justify-between gap-4 text-[13px] font-sans text-text-secondary">
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-sm bg-accent-classical block" />
            <span>Classical baseline path</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-sm bg-accent-quantum block" />
            <span>Quantum-inspired candidate path</span>
          </div>
        </div>

        <div className="flex items-center gap-4 text-[11px] font-mono">
          <span className="px-2 py-0.5 rounded-sm border border-hairline bg-ink-panel text-text-primary">
            Family: {selectedAlgorithm?.family ?? "Standard"}
          </span>
          <span className="px-2 py-0.5 rounded-sm border border-hairline bg-ink-panel text-accent-quantum">
            Solver: {selectedAlgorithm?.id ?? "none"}
          </span>
          <span className="text-text-secondary">Synthetic prototype stream</span>
        </div>
      </footer>
    </div>
  );
}
