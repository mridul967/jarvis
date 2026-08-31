"use client";

export default function RootError({
  reset,
}: {
  error: Error;
  reset: () => void;
}) {
  return (
    <main className="centered-state">
      <h1>Anywhere Door could not start</h1>
      <p>Reload the application or try again.</p>
      <button onClick={reset}>Try again</button>
    </main>
  );
}
