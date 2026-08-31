"use client";

export default function DashboardError({
  reset,
}: {
  error: Error;
  reset: () => void;
}) {
  return (
    <section className="centered-state">
      <h2>Failed to load this page</h2>
      <p>The API may be unavailable. Start FastAPI and try again.</p>
      <button className="button" onClick={reset}>
        Try again
      </button>
    </section>
  );
}
