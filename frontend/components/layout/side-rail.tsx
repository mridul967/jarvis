"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, Waypoints, Cpu, ScrollText } from "lucide-react";

export interface NavItem {
  name: string;
  href: string;
  icon: typeof LayoutDashboard;
  accent: "amber" | "teal";
}

export const NAV_ITEMS: NavItem[] = [
  {
    name: "Overview",
    href: "/",
    icon: LayoutDashboard,
    accent: "amber",
  },
  {
    name: "Visualization",
    href: "/visualize",
    icon: Waypoints,
    accent: "teal",
  },
  {
    name: "Optimization Engine",
    href: "/engine",
    icon: Cpu,
    accent: "amber",
  },
  { name: "Audit", href: "/audit", icon: ScrollText, accent: "teal" },
];

export function SideRail() {
  const pathname = usePathname();

  return (
    <aside
      className="hidden md:flex fixed top-0 left-0 bottom-0 w-[72px] bg-ink-panel border-r border-hairline flex-col items-center z-30 pt-14"
      aria-label="Primary Navigation"
    >
      <nav className="flex flex-col items-center gap-6 mt-6 w-full">
        {NAV_ITEMS.map((item) => {
          const isActive =
            item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
          const Icon = item.icon;

          return (
            <Link
              key={item.href}
              href={item.href}
              title={item.name}
              aria-label={item.name}
              className={`relative flex items-center justify-center w-full h-12 transition-colors focus:outline-none ${
                isActive
                  ? item.accent === "teal"
                    ? "border-l-2 border-accent-quantum text-accent-quantum"
                    : "border-l-2 border-accent-classical text-accent-classical"
                  : "border-l-2 border-transparent text-text-secondary hover:text-text-primary"
              }`}
            >
              <Icon size={20} aria-hidden="true" />
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
