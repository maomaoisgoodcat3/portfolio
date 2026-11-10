import type { NextConfig } from "next";

const isDev = process.env.NODE_ENV === "development";

const nextConfig: NextConfig = {
  // Defaults from create-next-app 16.4: keep them.
  cacheComponents: true,
  partialPrefetching: true,
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
  // Project settings.
  poweredByHeader: false,
  async rewrites() {
    // Only in local development: forward /api/* to the FastAPI container.
    // On Vercel, /api/* is served by the Python service on the same domain.
    if (!isDev) return [];
    return [
      {
        source: "/api/:path*",
        destination: "http://127.0.0.1:8000/api/:path*",
      },
    ];
  },
};

export default nextConfig;