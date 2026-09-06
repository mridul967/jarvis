"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { NAV_ITEMS } from "./side-rail";

export function MobileTabBar() {
  const pathname = usePathname();

  return (
    <nav
      className="md:hidden fixed bottom-0 left-0 right-0 h-14 bg-ink-panel border-t border-hairline z-40 flex items-center justify-around px-4"
      aria-label="Mobile Navigation"
    >
      {NAV_ITEMS.map((item) => {
        const isActive =
          item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
        const Icon = item.icon;

        return (
          <Link
            key={item.href}
            href={item.href}
            aria-label={item.name}
            className={`flex flex-col items-center justify-center py-1 px-3 text-xs transition-colors focus:outline-none ${
              isActive
                ? item.accent === "teal"
                  ? "text-accent-quantum border-t-2 border-accent-quantum"
                  : "text-accent-classical border-t-2 border-accent-classical"
                : "text-text-secondary hover:text-text-primary border-t-2 border-transparent"
            }`}
          >
            <Icon size={20} aria-hidden="true" />
            <span className="text-[11px] font-sans mt-0.5">{item.name}</span>
          </Link>
        );
      })}
    </nav>
  );
}
