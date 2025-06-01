/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,

  // Variables d'environnement publiques
  env: {
    NEXT_PUBLIC_API_URL:
      process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  },

  // Configuration des images
  images: {
    domains: ["localhost"],
  },

  // Configuration du serveur de développement
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://localhost:8000/api/:path*",
      },
    ];
  },

  // Configuration du serveur
  serverRuntimeConfig: {
    backendUrl: process.env.BACKEND_URL || "http://localhost:8000",
  },
  
  // Configuration publique
  publicRuntimeConfig: {
    apiUrl: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  },
};

module.exports = nextConfig;
