"use client";

import React from "react";
import { DecisionEvent } from "../../lib/types";

interface DecisionTimelineProps {
  events: DecisionEvent[];
}

export function DecisionTimeline({ events }: DecisionTimelineProps) {
  return (
    <div className="bg-ink-panel border border-hairline rounded-md p-6 space-y-4">
      <div className="flex items-center justify-between border-b border-hairline pb-3">
        <h3 className="text-[15px] font-heading font-medium text-text-primary">
          Decision timeline
        </h3>
        <span className="text-[11px] font-mono text-text-secondary">
          {events.length} event{events.length !== 1 ? "s" : ""} recorded
        </span>
      </div>

      {events.length === 0 ? (
        <div className="p-8 text-center text-[13px] font-mono text-text-secondary border border-dashed border-hairline rounded-sm">
          No optimization decisions recorded yet. Start the simulation to stream candidate evaluations.
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-[13px] font-mono">
            <thead className="border-b border-hairline text-[11px] text-text-secondary uppercase">
              <tr>
                <th className="py-2.5 px-3">Time</th>
                <th className="py-2.5 px-3">Candidate / Group</th>
                <th className="py-2.5 px-3">Decision</th>
                <th className="py-2.5 px-3">Reason</th>
                <th className="py-2.5 px-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-hairline">
              {events.map((item, idx) => {
                const isAccepted = item.status === "Accepted";
                const isRejected = item.status === "Rejected";

                return (
                  <tr key={idx} className="hover:bg-ink-panel-raised/50">
                    <td className="py-2.5 px-3 text-text-secondary">{item.timestamp}</td>
                    <td className="py-2.5 px-3 text-text-primary font-medium">{item.target}</td>
                    <td className="py-2.5 px-3">
                      <span
                        className={
                          isAccepted
                            ? "text-accent-quantum"
                            : isRejected
                            ? "text-status-danger"
                            : "text-accent-classical"
                        }
                      >
                        {item.decision}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-text-secondary max-w-xs truncate">
                      {item.reason}
                    </td>
                    <td className="py-2.5 px-3">
                      <span
                        className={`text-[11px] px-2 py-0.5 rounded-sm border ${
                          isAccepted
                            ? "border-accent-quantum/30 text-accent-quantum bg-accent-quantum/10"
                            : isRejected
                            ? "border-status-danger/30 text-status-danger bg-status-danger/10"
                            : "border-hairline text-text-secondary bg-ink-base"
                        }`}
                      >
                        {item.status}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      <div className="pt-2 border-t border-hairline">
        <p className="text-[11px] font-mono text-text-secondary">
          Future backend integration: animate the selected route and candidate path directly on the NetworkX graph viewport.
        </p>
      </div>
    </div>
  );
}
