/** @type {import('next').NextConfig} */
const nextConfig = {
  // Enable static exports for better Vercel compatibility
  output: 'standalone',
  
  // Image optimization
  images: {
    domains: ['images.unsplash.com', 'via.placeholder.com'],
    unoptimized: true, // Disable image optimization for Vercel
  },
  
  // Environment variables
  env: {
    NEXT_PUBLIC_ONCHAINKIT_PROJECT_NAME: process.env.NEXT_PUBLIC_ONCHAINKIT_PROJECT_NAME || 'tradeseer',
    NEXT_PUBLIC_URL: process.env.NEXT_PUBLIC_URL || 'http://localhost:3000',
    NEXT_PUBLIC_ONCHAINKIT_API_KEY: process.env.NEXT_PUBLIC_ONCHAINKIT_API_KEY || '',
    NEXT_PUBLIC_WALLETCONNECT_PROJECT_ID: process.env.NEXT_PUBLIC_WALLETCONNECT_PROJECT_ID || 'df764ed317f9390856ac428d23191a43',
    NEXT_PUBLIC_REOWN_PROJECT_ID: process.env.NEXT_PUBLIC_REOWN_PROJECT_ID || 'df764ed317f9390856ac428d23191a43',
  },
  
  // Webpack configuration for better bundling
  webpack: (config, { isServer }) => {
    if (!isServer) {
      config.resolve.fallback = {
        ...config.resolve.fallback,
        fs: false,
        net: false,
        tls: false,
      };
    }
    return config;
  },
}

module.exports = nextConfig
