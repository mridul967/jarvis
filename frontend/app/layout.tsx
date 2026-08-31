import type { Metadata } from "next";
import "./styles.css";

export const metadata: Metadata = {
  title: "Anywhere Door | VRPTW Lab",
  description: "Compare PSO and QPSO vehicle routes",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
