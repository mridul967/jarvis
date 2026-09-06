"use client";

import React, { useMemo } from "react";
import katex from "katex";

interface KatexMathProps {
  math: string;
  block?: boolean;
  className?: string;
}

export function KatexMath({ math, block = false, className = "" }: KatexMathProps) {
  const html = useMemo(() => {
    try {
      return katex.renderToString(math, {
        displayMode: block,
        throwOnError: false,
      });
    } catch (err) {
      console.error("KaTeX rendering error:", err);
      return math;
    }
  }, [math, block]);

  return (
    <span
      className={className}
      dangerouslySetInnerHTML={{ __html: html }}
      aria-label={math}
    />
  );
}
