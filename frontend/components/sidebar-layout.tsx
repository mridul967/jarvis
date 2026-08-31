"use client";

import { Menu } from "lucide-react";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { AppSidebar } from "@/components/app-sidebar";

const TITLES: Record<string, string> = {
  "/": "Overview",
  "/experiments": "Experiments",
  "/runs": "Runs",
  "/datasets": "Datasets",
};

export function SidebarLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [menuOpen, setMenuOpen] = useState(false);
  return (
    <div className="dashboard" data-menu-open={menuOpen}>
      <AppSidebar pathname={pathname} onNavigate={() => setMenuOpen(false)} />
      <div className="dashboard-body">
        <header className="topbar">
          <button
            className="menu-button"
            aria-label="Open navigation"
            onClick={() => setMenuOpen((open) => !open)}
          >
            <Menu size={20} />
          </button>
          <h1>{TITLES[pathname] ?? "Anywhere Door"}</h1>
        </header>
        <main className="content" id="main-content">
          {children}
        </main>
      </div>
    </div>
  );
}
