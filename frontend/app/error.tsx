"use client";

import React from "react";

export default function RootError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="min-h-[50vh] flex flex-col items-center justify-center text-center p-6 space-y-4">
      <span className="text-[13px] font-mono text-status-danger uppercase tracking-wider">
        System Fault Encountered
      </span>
      <h1 className="text-[24px] font-heading font-medium text-text-primary">
        An error occurred in the optimization runtime
      </h1>
      <p className="text-[14px] text-text-secondary max-w-md">
        {error.message || "An unexpected error disrupted the interface state."}
      </p>
      <button
        onClick={reset}
        className="px-4 py-2 rounded-md bg-accent-classical text-ink-base font-medium text-[13px] hover:bg-accent-classical/90 transition-colors"
      >
        Retry scenario
      </button>
    </div>
  );
}
