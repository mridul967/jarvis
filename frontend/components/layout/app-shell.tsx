"use client";

import React from "react";
import { SideRail } from "./side-rail";
import { MobileTabBar } from "./mobile-tab-bar";

interface AppShellProps {
  children: React.ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  return (
    <div className="min-h-screen bg-ink-base text-text-primary flex flex-col selection:bg-accent-quantum/20 selection:text-text-primary">
      {/* Topbar: 56px height, bottom hairline border */}
      <header className="fixed top-0 left-0 right-0 h-14 bg-ink-base border-b border-hairline z-20 flex items-center px-4 md:px-6">
        <div className="flex items-center gap-3 md:ml-16">
          <span className="font-heading text-[15px] font-medium text-text-primary tracking-tight">
            Jarvis
          </span>
          <span className="text-hairline-strong hidden sm:inline" aria-hidden="true">
            /
          </span>
          <span className="text-[13px] text-text-secondary hidden sm:inline font-sans">
            Quantum-inspired route intelligence
          </span>
        </div>
      </header>

      {/* Desktop Left Rail: 72px */}
      <SideRail />

      {/* Main Content Area: Centered, max-width 1200px */}
      <main className="flex-1 pt-14 pb-20 md:pb-12 md:pl-[72px] flex justify-center">
        <div className="w-full max-w-[1200px] px-4 md:px-8 py-6 md:py-8">
          {children}
        </div>
      </main>

      {/* Mobile Bottom Tab Bar */}
      <MobileTabBar />
    </div>
  );
}
