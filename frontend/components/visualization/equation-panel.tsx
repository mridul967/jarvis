"use client";

import React from "react";
import { KatexMath } from "../shared/katex-math";

const EQUATIONS = [
  ["VRP objective", "\\min F=(H,U,K,L,TT,D,CE)"],
  ["BPR traffic", "t_e=t_e^0[1+\\alpha(f_e/C_e)^\\beta]"],
  ["PSO velocity", "v_i^{t+1}=\\omega v_i^t+c_1r_1(p_i-x_i)+c_2r_2(g-x_i)"],
  ["QPSO attractor", "p_i=\\phi pbest_i+(1-\\phi)gbest"],
  ["QPSO potential well", "x_i^{t+1}=p_i\\pm\\beta|mbest-x_i^t|\\ln(1/u)"],
  ["Born collapse", "x=\\sin^2(\\theta)"],
  ["Rotation gate", "\\theta^{t+1}=\\theta^t+\\alpha r_a(\\theta_p-\\theta)+\\beta r_b(\\theta_g-\\theta)"],
  ["ACO transition", "P_{ij}=\\frac{\\tau_{ij}^{\\alpha}\\eta_{ij}^{\\beta}}{\\sum_k\\tau_{ik}^{\\alpha}\\eta_{ik}^{\\beta}}"],
  ["Interference", "P_{ij}\\propto|a_h+a_t e^{i\\phi}|^2"],
  ["Tunnelling", "P_{accept}=\\exp(-\\Delta E/T)"],
  ["Evaporation", "\\tau_{ij}\\leftarrow(1-\\rho)\\tau_{ij}+\\Delta\\tau_{ij}"],
];

export function EquationPanel() {
  return (
    <section className="bg-ink-panel border border-hairline rounded-md p-6 space-y-4">
      <div className="flex items-center justify-between border-b border-hairline pb-3">
        <div>
          <h3 className="text-[15px] font-heading font-medium text-text-primary">Research equation stack</h3>
          <p className="text-[12px] text-text-secondary mt-1">Ports of the formulations used across the research notebooks.</p>
        </div>
        <span className="text-[11px] font-mono text-accent-quantum">{EQUATIONS.length} equations</span>
      </div>
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-3">
        {EQUATIONS.map(([label, math]) => (
          <div key={label} className="p-3 bg-ink-base border border-hairline rounded-sm overflow-x-auto">
            <span className="block text-[10px] uppercase tracking-wide font-mono text-text-secondary mb-2">{label}</span>
            <KatexMath math={math} block />
          </div>
        ))}
      </div>
    </section>
  );
}
