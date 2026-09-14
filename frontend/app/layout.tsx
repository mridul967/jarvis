import type { Metadata } from "next";
import "katex/dist/katex.min.css";
import "./globals.css";
import { AppShell } from "../components/layout/app-shell";

export const metadata: Metadata = {
  title: "Jarvis — Quantum-Inspired Route Intelligence",
  description:
    "SIH 2026 Quantum Technology Vertical: Quantum-inspired metaheuristic traffic and vehicle-routing optimization platform.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="bg-ink-base text-text-primary antialiased font-sans">
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
