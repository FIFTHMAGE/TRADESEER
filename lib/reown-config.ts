import { createAppKit } from '@reown/appkit';
import { WagmiAdapter } from '@reown/appkit-adapter-wagmi';

// Production Project ID from Reown Dashboard
const PROJECT_ID = 'df764ed317f9390856ac428d23191a43';

// Validate Project ID
if (!PROJECT_ID) {
  throw new Error('Reown AppKit Project ID not configured. Please set a valid Project ID in lib/reown-config.ts');
}

console.log('🔑 Reown AppKit Project ID:', PROJECT_ID);

// Basic network configuration - AppKit will handle the rest
const defaultNetworks = [{ id: 1, name: 'Ethereum' }] as [{ id: number; name: string }, ...{ id: number; name: string }[]];

// Set up Wagmi adapter with validated Project ID
export const wagmiAdapter = new WagmiAdapter({
  projectId: PROJECT_ID,
  networks: defaultNetworks
});

// Configure the metadata for production
export const metadata = {
  name: 'TradeSeer',
  description: 'AI-Powered Trading Bot with Web3 Integration',
  url: 'http://localhost:3000', // Update this for production deployment
  icons: ['https://avatars.githubusercontent.com/u/179229932']
};

// Create the modal with validated configuration
export const modal = createAppKit({
  adapters: [wagmiAdapter],
  networks: defaultNetworks,
  metadata,
  // Ensure project ID is available to AppKit
  projectId: PROJECT_ID,
  features: {
    analytics: false // Disable analytics to avoid remote API calls
  }
});

// Export the modal for use in components
export default modal;
