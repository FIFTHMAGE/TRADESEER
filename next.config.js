/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    domains: ['images.unsplash.com', 'via.placeholder.com'],
  },
  env: {
    NEXT_PUBLIC_ONCHAINKIT_PROJECT_NAME: process.env.NEXT_PUBLIC_ONCHAINKIT_PROJECT_NAME || 'tradeseer',
    NEXT_PUBLIC_URL: process.env.NEXT_PUBLIC_URL || 'http://localhost:3000',
    NEXT_PUBLIC_ONCHAINKIT_API_KEY: process.env.NEXT_PUBLIC_ONCHAINKIT_API_KEY || '',
    NEXT_PUBLIC_WALLETCONNECT_PROJECT_ID: 'df764ed317f9390856ac428d23191a43',
  },
}

module.exports = nextConfig
