import { createAppKit } from '@reown/appkit';
import { WagmiAdapter } from '@reown/appkit-adapter-wagmi';

// Production Project ID from Reown Dashboard
const PROJECT_ID = 'df764ed317f9390856ac428d23191a43';

// Validate Project ID
if (!PROJECT_ID) {
  throw new Error('Reown AppKit Project ID not configured. Please set a valid Project ID in lib/reown-config.ts');
}

console.log('🔑 Reown AppKit Project ID:', PROJECT_ID);

// Configure the metadata for production
export const metadata = {
  name: 'TradeSeer',
  description: 'AI-Powered Trading Bot with Web3 Integration',
  url: 'http://localhost:3000', // Update this for production deployment
  icons: ['https://avatars.githubusercontent.com/u/179229932']
};

// Create the modal with minimal configuration
export const modal = createAppKit({
  projectId: PROJECT_ID,
  metadata,
  features: {
    analytics: false // Disable analytics to avoid remote API calls
  }
});

// Export the modal for use in components
export default modal;
