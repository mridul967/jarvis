import React from "react";
import Link from "next/link";
import { ArrowRight, ShieldCheck, Database, Layers, CheckCircle2 } from "lucide-react";
import { KatexMath } from "../components/shared/katex-math";

export default function LandingPage() {
  return (
    <div className="space-y-16 md:space-y-24">
      {/* Section 1 — Hero */}
      <section className="min-h-[40vh] grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-12 items-center border-b border-hairline pb-16">
        <div className="lg:col-span-7 space-y-6">
          <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-sm border border-hairline bg-ink-panel text-text-secondary text-[13px] font-medium font-sans">
            <span>SIH 2026</span>
            <span className="text-hairline-strong">·</span>
            <span>Quantum Technology Vertical</span>
          </div>

          <h1 className="text-[32px] md:text-[40px] leading-tight font-heading font-medium text-text-primary">
            Route intelligence for roads that refuse to behave.
          </h1>

          <p className="text-[15px] leading-relaxed text-text-secondary max-w-[65ch]">
            Vehicle routing is not just about finding the shortest line between two points. It is a
            changing search across capacity, time windows, congestion, road restrictions, and
            competing route choices.
          </p>

          <div className="flex flex-wrap items-center gap-4 pt-2">
            <Link
              href="/visualize"
              className="inline-flex items-center justify-center px-5 h-12 rounded-md bg-accent-classical text-ink-base font-medium text-[15px] hover:bg-accent-classical/90 transition-colors focus:outline-none"
            >
              Open the visualizer
            </Link>

            <Link
              href="/engine"
              className="inline-flex items-center justify-center px-5 h-12 rounded-md border border-hairline bg-ink-panel text-text-primary font-medium text-[15px] hover:bg-ink-panel-raised transition-colors focus:outline-none"
            >
              Explore the engine
            </Link>
          </div>
        </div>

        {/* Hero visual: Static SVG sketch of weighted graph */}
        <div className="lg:col-span-5 flex flex-col items-center">
          <div className="w-full aspect-[4/3] max-w-[420px] bg-ink-panel border border-hairline rounded-lg p-6 flex flex-col justify-between">
            <div className="flex items-center justify-between text-[11px] font-mono text-text-secondary border-b border-hairline pb-2">
              <span>Graph topology preview</span>
              <span className="text-accent-quantum">N=12 · E=18</span>
            </div>

            <svg
              viewBox="0 0 360 220"
              className="w-full h-auto"
              aria-label="Static weighted graph topology diagram"
            >
              {/* Inactive background edges */}
              <line x1="40" y1="40" x2="140" y2="30" stroke="#3A3F47" strokeWidth="1.5" />
              <line x1="40" y1="40" x2="90" y2="120" stroke="#3A3F47" strokeWidth="1.5" />
              <line x1="140" y1="30" x2="220" y2="50" stroke="#3A3F47" strokeWidth="1.5" />
              <line x1="90" y1="120" x2="180" y2="110" stroke="#3A3F47" strokeWidth="1.5" />
              <line x1="90" y1="120" x2="70" y2="190" stroke="#3A3F47" strokeWidth="1.5" />
              <line x1="180" y1="110" x2="220" y2="50" stroke="#3A3F47" strokeWidth="1.5" />
              <line x1="180" y1="110" x2="260" y2="130" stroke="#3A3F47" strokeWidth="1.5" />
              <line x1="220" y1="50" x2="310" y2="60" stroke="#3A3F47" strokeWidth="1.5" />
              <line x1="70" y1="190" x2="160" y2="180" stroke="#3A3F47" strokeWidth="1.5" />
              <line x1="160" y1="180" x2="250" y2="190" stroke="#3A3F47" strokeWidth="1.5" />
              <line x1="260" y1="130" x2="320" y2="150" stroke="#3A3F47" strokeWidth="1.5" />

              {/* Highlighted active route: 40,40 -> 140,30 -> 180,110 -> 260,130 -> 320,150 */}
              <polyline
                points="40,40 140,30 180,110 260,130 320,150"
                fill="none"
                stroke="#D98E3F"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />

              {/* Inactive nodes */}
              <circle cx="90" cy="120" r="4" fill="#2E333B" stroke="#3A3F47" strokeWidth="1.5" />
              <circle cx="220" cy="50" r="4" fill="#2E333B" stroke="#3A3F47" strokeWidth="1.5" />
              <circle cx="70" cy="190" r="4" fill="#2E333B" stroke="#3A3F47" strokeWidth="1.5" />
              <circle cx="160" cy="180" r="4" fill="#2E333B" stroke="#3A3F47" strokeWidth="1.5" />
              <circle cx="250" cy="190" r="4" fill="#2E333B" stroke="#3A3F47" strokeWidth="1.5" />
              <circle cx="310" cy="60" r="4" fill="#2E333B" stroke="#3A3F47" strokeWidth="1.5" />

              {/* Route nodes */}
              <circle cx="40" cy="40" r="6" fill="#14171C" stroke="#D98E3F" strokeWidth="2" />
              <text x="40" y="26" fill="#8A8F98" fontSize="9" fontFamily="monospace" textAnchor="middle">
                Depot 01
              </text>

              <circle cx="140" cy="30" r="5" fill="#14171C" stroke="#D98E3F" strokeWidth="2" />
              <text x="140" y="18" fill="#8A8F98" fontSize="9" fontFamily="monospace" textAnchor="middle">
                C-04
              </text>

              <circle cx="180" cy="110" r="5" fill="#14171C" stroke="#4FB8AE" strokeWidth="2" />
              <text x="180" y="130" fill="#4FB8AE" fontSize="9" fontFamily="monospace" textAnchor="middle">
                QACO node
              </text>

              <circle cx="260" cy="130" r="5" fill="#14171C" stroke="#D98E3F" strokeWidth="2" />
              <text x="260" y="150" fill="#8A8F98" fontSize="9" fontFamily="monospace" textAnchor="middle">
                C-12
              </text>

              <circle cx="320" cy="150" r="6" fill="#14171C" stroke="#4FB8AE" strokeWidth="2" />
              <text x="320" y="172" fill="#8A8F98" fontSize="9" fontFamily="monospace" textAnchor="middle">
                Dest
              </text>
            </svg>

            <div className="text-center pt-2">
              <span className="text-[11px] font-mono text-text-secondary">
                Frontend prototype · Synthetic data · Backend integration pending
              </span>
            </div>
          </div>
        </div>
      </section>

      {/* Section 2 — Why VRP Is NP-Hard */}
      <section className="space-y-6">
        <div>
          <h2 className="text-[20px] font-heading font-medium text-text-primary">
            Why VRP is NP-hard
          </h2>
          <p className="text-[15px] text-text-secondary mt-2 max-w-[65ch]">
            Vehicle Routing Problems are a family of combinatorial optimization problems. The
            difficulty comes from the number of possible assignments, stop sequences, and route
            structures that must be considered before constraints can be validated.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-ink-panel border border-hairline rounded-md p-6 min-h-[90px] space-y-3">
            <span className="text-[13px] font-medium text-text-secondary font-sans">
              Problem 1
            </span>
            <h3 className="text-[17px] font-heading font-medium text-text-primary">
              Combinatorial explosion
            </h3>
            <p className="text-[15px] leading-relaxed text-text-secondary">
              As the number of stops grows, the number of possible stop sequences grows factorially
              (n!). Adding multiple vehicles creates an additional exponential layer of customer
              assignment decisions across the fleet.
            </p>
          </div>

          <div className="bg-ink-panel border border-hairline rounded-md p-6 min-h-[90px] space-y-3">
            <span className="text-[13px] font-medium text-text-secondary font-sans">
              Problem 2
            </span>
            <h3 className="text-[17px] font-heading font-medium text-text-primary">
              Constraints compound
            </h3>
            <p className="text-[15px] leading-relaxed text-text-secondary">
              VRPTW introduces customer time windows, service durations, vehicle capacity limits,
              depot availability, and road restrictions on top of the sequence. Even finding a single
              feasible solution becomes computationally demanding.
            </p>
          </div>

          <div className="bg-ink-panel border border-hairline rounded-md p-6 min-h-[90px] space-y-3">
            <span className="text-[13px] font-medium text-text-secondary font-sans">
              Problem 3
            </span>
            <h3 className="text-[17px] font-heading font-medium text-text-primary">
              Optimality becomes expensive
            </h3>
            <p className="text-[15px] leading-relaxed text-text-secondary">
              Exact solvers can prove <code className="text-accent-classical font-mono text-[13px]">OPTIMAL_PROVEN</code>{" "}
              solutions for small instances, but cost explodes as scale expands. Practical solutions
              are reported as <code className="text-accent-quantum font-mono text-[13px]">FEASIBLE</code> or{" "}
              <code className="text-accent-quantum font-mono text-[13px]">BEST_FOUND</code>.
            </p>
          </div>
        </div>
      </section>

      {/* Section 3 — Why Indian Road Conditions Make It Harder */}
      <section className="space-y-6 border-t border-hairline pt-12">
        <h2 className="text-[20px] font-heading font-medium text-text-primary">
          Why Indian road conditions make the problem harder
        </h2>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          <div className="lg:col-span-5 space-y-4">
            <p className="text-[15px] leading-relaxed text-text-secondary">
              Indian urban road networks introduce conditions that are difficult to represent with a
              single static travel-time assumption. The challenge is not that classical or modern
              solvers are useless; it is that the data, constraints, and costs can change quickly
              while the network itself remains irregular and heterogeneous.
            </p>
            <div className="p-4 rounded-md border border-hairline bg-ink-panel space-y-2">
              <span className="text-[13px] font-medium text-text-primary">
                BPR Congestion Coupling
              </span>
              <p className="text-[13px] text-text-secondary leading-relaxed">
                Rather than treating edge costs as fixed distances, the platform models travel time
                as an exponential function of current corridor flow relative to effective capacity,
                adjusting for high-variance disruptions.
              </p>
            </div>
          </div>

          <div className="lg:col-span-7 bg-ink-panel border border-hairline rounded-md divide-y divide-hairline">
            {[
              "Mixed vehicle types and non-uniform operating speeds (2W, 3W, LCV, freight)",
              "Non-lane-disciplined and highly heterogeneous traffic flow patterns",
              "Informal parking, encroachment, and temporary corridor obstructions",
              "High-variance signal delay and uncoordinated intersection bottlenecks",
              "Volatile congestion around arterial corridors and rapid queue buildup",
              "Sparse or inconsistent road-capacity data across municipal datasets",
              "Unscheduled road closures and incident-related localized detours",
              "Toll barriers, turn bans, and vehicle-compatibility restrictions",
              "Changing customer service and delivery unloading conditions",
            ].map((item, idx) => (
              <div key={idx} className="p-3.5 flex items-start gap-3">
                <span className="text-[11px] font-mono text-text-secondary mt-0.5 w-6 shrink-0">
                  0{idx + 1}
                </span>
                <span className="text-[14px] text-text-primary font-sans">{item}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Section 4 — How We Are Approaching It */}
      <section className="space-y-8 border-t border-hairline pt-12">
        <div>
          <h2 className="text-[20px] font-heading font-medium text-text-primary">
            Hybrid by design. Explicit about uncertainty.
          </h2>
          <p className="text-[15px] leading-relaxed text-text-secondary mt-2 max-w-[65ch]">
            The platform combines classical baselines with quantum-inspired candidate generation. A
            transportation network is represented as a weighted graph, dynamic edge costs are updated
            from traffic conditions, candidate routes are generated, and a separate validation layer
            checks whether hard constraints are satisfied.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-ink-panel border border-hairline rounded-md p-6 space-y-3">
            <span className="text-[11px] font-mono text-accent-classical font-medium">
              01 — Model
            </span>
            <h3 className="text-[17px] font-heading font-medium text-text-primary">
              Graph representation
            </h3>
            <p className="text-[13px] text-text-secondary leading-relaxed">
              Represent the transportation network as a directed weighted graph with free-flow travel
              times, distances, and road capacities.
            </p>
          </div>

          <div className="bg-ink-panel border border-hairline rounded-md p-6 space-y-3">
            <span className="text-[11px] font-mono text-accent-quantum font-medium">
              02 — Update
            </span>
            <h3 className="text-[17px] font-heading font-medium text-text-primary">
              Dynamic edge costs
            </h3>
            <p className="text-[13px] text-text-secondary leading-relaxed">
              Calculate edge costs from traffic observations and a BPR congestion function:
            </p>
            <div className="p-2.5 bg-ink-base border border-hairline rounded-sm overflow-x-auto text-[13px]">
              <KatexMath math={"t_e(f_e) = t_e^0 \\left[ 1 + \\alpha \\left(\\frac{f_e}{C_e}\\right)^\\beta \\right]"} block />
            </div>
          </div>

          <div className="bg-ink-panel border border-hairline rounded-md p-6 space-y-3">
            <span className="text-[11px] font-mono text-accent-quantum font-medium">
              03 — Search
            </span>
            <h3 className="text-[17px] font-heading font-medium text-text-primary">
              Candidate generation
            </h3>
            <p className="text-[13px] text-text-secondary leading-relaxed">
              Compare classical baselines with quantum-inspired approaches such as QACO, QPSO, and SBM
              on structured subproblems.
            </p>
          </div>

          <div className="bg-ink-panel border border-hairline rounded-md p-6 space-y-3">
            <span className="text-[11px] font-mono text-accent-classical font-medium">
              04 — Validate
            </span>
            <h3 className="text-[17px] font-heading font-medium text-text-primary">
              Constraint verification
            </h3>
            <p className="text-[13px] text-text-secondary leading-relaxed">
              Independently check capacity, time windows, route structure, vehicle compatibility, and
              forbidden edges before reporting feasibility.
            </p>
          </div>
        </div>

        <div className="p-4 rounded-md border border-hairline bg-ink-panel-raised flex items-start gap-4">
          <ShieldCheck className="text-accent-quantum shrink-0 mt-0.5" size={20} />
          <div className="space-y-1">
            <span className="text-[13px] font-medium text-text-primary">
              A solver score is not proof of feasibility.
            </span>
            <p className="text-[13px] text-text-secondary leading-relaxed">
              Every result must pass an independent validator. Solver energy, objective value, or
              internal heuristics are never accepted as proof of route validity.
            </p>
          </div>
        </div>
      </section>

      {/* Section 5 — Method Context */}
      <section className="space-y-6 border-t border-hairline pt-12">
        <div>
          <h2 className="text-[20px] font-heading font-medium text-text-primary">
            Method context
          </h2>
          <p className="text-[15px] text-text-secondary mt-2 max-w-[65ch]">
            Classical solvers remain essential baselines. Heuristic and quantum-inspired methods search
            large combinatorial spaces without guaranteeing global optimality.
          </p>
        </div>

        <div className="overflow-x-auto border border-hairline rounded-md bg-ink-panel">
          <table className="w-full text-left text-[14px]">
            <thead className="border-b border-hairline text-[11px] font-mono text-text-secondary uppercase">
              <tr>
                <th className="p-3.5">Method</th>
                <th className="p-3.5">Role</th>
                <th className="p-3.5">Strength</th>
                <th className="p-3.5">Result language</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-hairline">
              <tr>
                <td className="p-3.5 font-medium text-accent-classical">Dijkstra / A*</td>
                <td className="p-3.5 text-text-secondary">Baseline shortest path</td>
                <td className="p-3.5 text-text-primary">Fast and interpretable</td>
                <td className="p-3.5 font-mono text-[13px] text-accent-quantum">FEASIBLE</td>
              </tr>
              <tr>
                <td className="p-3.5 font-medium text-accent-classical">OR-Tools</td>
                <td className="p-3.5 text-text-secondary">Production fleet-routing baseline</td>
                <td className="p-3.5 text-text-primary">Strong constraint handling</td>
                <td className="p-3.5 font-mono text-[13px] text-accent-classical">
                  FEASIBLE / BEST_FOUND
                </td>
              </tr>
              <tr>
                <td className="p-3.5 font-medium text-accent-quantum">QACO</td>
                <td className="p-3.5 text-text-secondary">Local route candidate generation</td>
                <td className="p-3.5 text-text-primary">Explores route combinations</td>
                <td className="p-3.5 font-mono text-[13px] text-accent-quantum">BEST_FOUND</td>
              </tr>
              <tr>
                <td className="p-3.5 font-medium text-accent-quantum">QPSO</td>
                <td className="p-3.5 text-text-secondary">Parameter or policy search</td>
                <td className="p-3.5 text-text-primary">Global search behavior</td>
                <td className="p-3.5 font-mono text-[13px] text-accent-quantum">BEST_FOUND</td>
              </tr>
              <tr>
                <td className="p-3.5 font-medium text-accent-quantum">SBM</td>
                <td className="p-3.5 text-text-secondary">Small binary subproblems</td>
                <td className="p-3.5 text-text-primary">Experimental combinatorial search</td>
                <td className="p-3.5 font-mono text-[13px] text-accent-quantum">BEST_FOUND</td>
              </tr>
              <tr>
                <td className="p-3.5 font-medium text-accent-classical">CPLEX</td>
                <td className="p-3.5 text-text-secondary">Small-instance exact validation</td>
                <td className="p-3.5 text-text-primary">Can prove optimality at small scale</td>
                <td className="p-3.5 font-mono text-[13px] text-accent-classical">OPTIMAL_PROVEN</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      {/* Section 6 — Platform Preview */}
      <section className="space-y-6 border-t border-hairline pt-12 pb-8">
        <div>
          <h2 className="text-[20px] font-heading font-medium text-text-primary">
            Platform preview
          </h2>
          <p className="text-[15px] text-text-secondary mt-2 max-w-[65ch]">
            Inspect the prototype modules or review the optimization pipeline architecture.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Link
            href="/visualize"
            className="group bg-ink-panel hover:bg-ink-panel-raised border border-hairline rounded-md p-6 space-y-3 transition-colors focus:outline-none"
          >
            <div className="flex items-center justify-between">
              <span className="text-[13px] font-medium text-accent-quantum font-sans">
                Interactive Module
              </span>
              <ArrowRight size={16} className="text-text-secondary group-hover:text-accent-quantum transition-colors" />
            </div>
            <h3 className="text-[17px] font-heading font-medium text-text-primary">
              Visualization
            </h3>
            <p className="text-[13px] text-text-secondary leading-relaxed">
              Watch a synthetic routing run update its traffic-cost model, telemetry, and decision timeline.
            </p>
          </Link>

          <Link
            href="/engine"
            className="group bg-ink-panel hover:bg-ink-panel-raised border border-hairline rounded-md p-6 space-y-3 transition-colors focus:outline-none"
          >
            <div className="flex items-center justify-between">
              <span className="text-[13px] font-medium text-accent-classical font-sans">
                System Architecture
              </span>
              <ArrowRight size={16} className="text-text-secondary group-hover:text-accent-classical transition-colors" />
            </div>
            <h3 className="text-[17px] font-heading font-medium text-text-primary">
              Core Optimization Engine
            </h3>
            <p className="text-[13px] text-text-secondary leading-relaxed">
              Inspect the multi-agent pipeline from scenario intake through independent validation.
            </p>
          </Link>

          <div className="bg-ink-panel border border-hairline rounded-md p-6 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-[13px] font-medium text-text-secondary font-sans">
                Informational
              </span>
              <Database size={16} className="text-text-secondary" />
            </div>
            <h3 className="text-[17px] font-heading font-medium text-text-primary">
              Reproducible Experiments
            </h3>
            <p className="text-[13px] text-text-secondary leading-relaxed">
              Future runs will record graph snapshots, traffic snapshots, solver configuration, seeds, runtime, and result status.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}
