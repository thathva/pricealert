import type { NextConfig } from "next";

const config: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${process.env.BACKEND_URL ?? "http://localhost:8000"}/api/:path*`,
      },
      {
        source: "/webhook",
        destination: `${process.env.BACKEND_URL ?? "http://localhost:8000"}/webhook`,
      },
    ];
  },
};

export default config;
