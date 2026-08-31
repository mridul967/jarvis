export function ConvergenceChart({ values }: { values: number[] }) {
  if (values.length < 2) return null;
  const width = 900,
    height = 220,
    min = Math.min(...values),
    max = Math.max(...values),
    span = max - min || 1;
  const points = values
    .map(
      (value, index) =>
        `${(index / (values.length - 1)) * width},${height - ((value - min) / span) * height}`,
    )
    .join(" ");
  return (
    <section className="panel" style={{ marginTop: 20 }}>
      <h3>Best objective by iteration</h3>
      <svg
        viewBox={`0 0 ${width} ${height}`}
        role="img"
        aria-label="Convergence curve"
        style={{ width: "100%", height: "auto" }}
      >
        <polyline
          points={points}
          fill="none"
          stroke="var(--accent)"
          strokeWidth="4"
          vectorEffect="non-scaling-stroke"
        />
      </svg>
      <p className="muted">
        Start {values[0].toFixed(1)} · Best {values.at(-1)?.toFixed(1)}
      </p>
    </section>
  );
}
