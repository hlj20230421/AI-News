/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    // Docker 内用服务名 backend；本地裸跑 frontend 时设 API_PROXY_TARGET=http://localhost:8001
    const target = process.env.API_PROXY_TARGET || "http://backend:8000";
    return [
      {
        source: "/api/:path*",
        destination: `${target}/:path*`,
      },
    ];
  },
  webpack: (config, { dev }) => {
    if (dev) {
      config.watchOptions = {
        ...config.watchOptions,
        ignored: ["**/node_modules/**", "**/.git/**", "../backend/**", "../scripts/**"],
      };
    }
    return config;
  },
};

module.exports = nextConfig;
