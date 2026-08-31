"use client";

import { useState } from "react";
import type { Dataset } from "@/types/dataset";

export function DatasetManagerClient({ sample }: { sample: Dataset | null }) {
  const [content, setContent] = useState(sample?.content ?? "");
  function loadFile(file: File | undefined) {
    if (file) void file.text().then(setContent);
  }
  return (
    <>
      <header className="page-heading">
        <p className="eyebrow">Input data</p>
        <h2>Solomon datasets.</h2>
        <p className="lede">
          Inspect the bundled smoke instance or load a local Solomon-format file
          without uploading it.
        </p>
      </header>
      <section className="panel">
        <label className="field">
          Local instance
          <input
            type="file"
            accept=".txt,.vrp"
            onChange={(event) => loadFile(event.target.files?.[0])}
          />
        </label>
        <label className="field">
          Contents
          <textarea
            rows={22}
            value={content}
            onChange={(event) => setContent(event.target.value)}
          />
        </label>
        <p className="muted">
          The backend currently persists experiment results, not dataset files.
        </p>
      </section>
    </>
  );
}
