import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  async rewrites() {
    const backend = (process.env.INTERNAL_API_URL ?? "http://localhost:8000").replace(/\/$/, "");
    const api = backend.endsWith("/api/v1") ? backend : `${backend}/api/v1`;
    return [
      {
        source: "/api/:path*",
        destination: `${api}/:path*`,
      },
    ];
  },
};

export default nextConfig;
