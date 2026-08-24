/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    const backendUrl =
      process.env.API_URL ||
      process.env.NEXT_PUBLIC_API_URL ||
      (process.env.RAILWAY_PUBLIC_DOMAIN ? `https://${process.env.RAILWAY_PUBLIC_DOMAIN}/api` : null) ||
      (process.env.RAILWAY_STATIC_URL ? `https://${process.env.RAILWAY_STATIC_URL}/api` : null) ||
      "http://127.0.0.1:8000/api";

    return [
      {
        source: "/api/:path*",
        destination: `${backendUrl.replace(/\/$/, "")}/:path*`,
      },
    ];
  },
};

export default nextConfig;
