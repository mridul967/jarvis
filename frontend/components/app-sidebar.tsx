import { Database, FlaskConical, History, House, Route } from "lucide-react";
import Link from "next/link";

const items = [
  { href: "/", label: "Overview", icon: House },
  { href: "/experiments", label: "Experiments", icon: FlaskConical },
  { href: "/runs", label: "Runs", icon: History },
  { href: "/datasets", label: "Datasets", icon: Database },
];

export function AppSidebar({
  pathname,
  onNavigate,
}: {
  pathname: string;
  onNavigate: () => void;
}) {
  return (
    <aside className="sidebar">
      <Link className="brand" href="/" onClick={onNavigate}>
        <span className="brand-mark">
          <Route size={18} />
        </span>
        Anywhere Door
      </Link>
      <nav className="nav" aria-label="Primary">
        {items.map(({ href, label, icon: Icon }) => (
          <Link
            key={href}
            href={href}
            data-active={pathname === href}
            onClick={onNavigate}
          >
            <Icon size={18} />
            {label}
          </Link>
        ))}
      </nav>
    </aside>
  );
}
