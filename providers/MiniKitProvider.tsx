'use client';

import { createAppKit } from '@reown/appkit';
import { WagmiAdapter } from '@reown/appkit-adapter-wagmi';
import { ReactNode, createContext, useContext, useEffect, useState } from 'react';

interface AppKitContextType {
  modal: any;
  isReady: boolean;
  isConnected: boolean;
  connectedAddress: string | null;
  openModal: () => Promise<void>;
  disconnect: () => Promise<void>;
  refreshConnection: () => void;
}

const AppKitContext = createContext<AppKitContextType | null>(null);

export function useAppKit() {
  const context = useContext(AppKitContext);
  if (!context) {
    throw new Error('useAppKit must be used within AppKitProvider');
  }
  return context;
}

export function MiniKitContextProvider({ children }: { children: ReactNode }) {
  const [modal, setModal] = useState<any>(null);
  const [isReady, setIsReady] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [connectedAddress, setConnectedAddress] = useState<string | null>(null);

  useEffect(() => {
    const initializeAppKit = async () => {
      try {
        console.log('🚀 Initializing Reown AppKit...');
        
        const PROJECT_ID = process.env.NEXT_PUBLIC_REOWN_PROJECT_ID || 'df764ed317f9390856ac428d23191a43';
        console.log('🔑 Project ID:', PROJECT_ID);
        
        // Configure networks - use Base as primary
        const networks = [
          { id: 8453, name: 'Base', chainId: 8453 }, // Base Mainnet
          { id: 1, name: 'Ethereum', chainId: 1 },   // Ethereum Mainnet
          { id: 137, name: 'Polygon', chainId: 137 }  // Polygon
        ] as [{ id: number; name: string; chainId: number }, ...{ id: number; name: string; chainId: number }[]];

        console.log('🌐 Networks configured:', networks);

        // Set up Wagmi adapter
        const wagmiAdapter = new WagmiAdapter({
          projectId: PROJECT_ID,
          networks
        });

        console.log('✅ WagmiAdapter created');

        // Configure metadata
        const metadata = {
          name: process.env.NEXT_PUBLIC_APP_NAME || 'TradeSeer',
          description: process.env.NEXT_PUBLIC_APP_DESCRIPTION || 'AI-Powered Trading Bot with Web3 Integration',
          url: process.env.NEXT_PUBLIC_APP_URL || window.location.origin,
          icons: [process.env.NEXT_PUBLIC_APP_HERO_IMAGE || 'https://avatars.githubusercontent.com/u/179229932']
        };

        console.log('📝 Metadata configured:', metadata);

        // Create AppKit modal
        const appKitModal = createAppKit({
          projectId: PROJECT_ID,
          adapters: [wagmiAdapter],
          networks,
          metadata,
          features: {
            analytics: false // Disable analytics to avoid issues
          }
        });

        console.log('✅ AppKit modal created');
        setModal(appKitModal);
        setIsReady(true);

        // Set up connection listeners
        setupConnectionListeners(appKitModal);

      } catch (error) {
        console.error('❌ Failed to initialize AppKit:', error);
        setIsReady(false);
      }
    };

    initializeAppKit();
  }, []);

  const setupConnectionListeners = (appKitModal: any) => {
    if (!appKitModal) return;

    try {
      console.log('🔌 Setting up connection listeners...');
      
      // Subscribe to connection changes
      const unsubscribeConnections = appKitModal.subscribeConnections((connectionState: any) => {
        console.log('🔗 AppKit: Connection state updated:', connectionState);
        
        try {
          // Check if we have any active connections
          const activeConnections = connectionState.connections;
          if (activeConnections && activeConnections.size > 0) {
            // Get the first connected address from the Map
            const firstNamespace = Array.from(activeConnections.keys())[0];
            const connections = activeConnections.get(firstNamespace);
            
            if (connections && connections.length > 0) {
              const address = connections[0].accounts?.[0]?.address;
              if (address) {
                console.log('✅ AppKit: Wallet connected:', address);
                setConnectedAddress(address);
                setIsConnected(true);
              }
            }
          } else {
            // No connections, wallet disconnected
            console.log('❌ AppKit: Wallet disconnected');
            setConnectedAddress(null);
            setIsConnected(false);
          }
        } catch (error) {
          console.error('❌ Error processing connection state:', error);
        }
      });

      console.log('✅ Connection listeners set up successfully');

      // Cleanup subscription on unmount
      return () => {
        if (unsubscribeConnections) {
          unsubscribeConnections();
        }
      };

    } catch (error) {
      console.error('❌ Error setting up AppKit connection listeners:', error);
    }
  };

  const openModal = async () => {
    if (modal) {
      try {
        console.log('🔓 Opening AppKit modal...');
        await modal.open();
        console.log('✅ Modal opened successfully');
      } catch (error) {
        console.error('❌ Failed to open AppKit modal:', error);
        throw error;
      }
    } else {
      throw new Error('AppKit modal not initialized');
    }
  };

  const disconnect = async () => {
    if (modal) {
      try {
        console.log('🔌 AppKit: Disconnecting wallet...');
        
        // Try to disconnect through the modal first
        if (typeof modal.disconnect === 'function') {
          await modal.disconnect();
          console.log('✅ Disconnected through modal');
        } else {
          console.log('⚠️ Modal disconnect method not available, using alternative approach');
          // Alternative: try to close the modal and reset state
          if (typeof modal.close === 'function') {
            await modal.close();
            console.log('✅ Modal closed');
          }
        }
        
        // Force update local state regardless of modal response
        setConnectedAddress(null);
        setIsConnected(false);
        
        console.log('✅ AppKit: Wallet disconnected successfully');
      } catch (error) {
        console.error('❌ Failed to disconnect wallet:', error);
        // Even if the modal disconnect fails, update local state
        setConnectedAddress(null);
        setIsConnected(false);
      }
    } else {
      // If no modal, just reset the state
      console.log('⚠️ No modal available, resetting connection state');
      setConnectedAddress(null);
      setIsConnected(false);
    }
  };

  const refreshConnection = () => {
    console.log('🔄 Refreshing connection state...');
    // Force a refresh of the connection state
    if (modal) {
      try {
        // This will trigger the connection listeners
        modal.subscribeConnections((connectionState: any) => {
          console.log('🔄 AppKit: Refreshing connection state:', connectionState);
        });
      } catch (error) {
        console.error('❌ Failed to refresh connection:', error);
      }
    }
  };

  const value: AppKitContextType = {
    modal,
    isReady,
    isConnected,
    connectedAddress,
    openModal,
    disconnect,
    refreshConnection
  };

  return (
    <AppKitContext.Provider value={value}>
      {children}
    </AppKitContext.Provider>
  );
}
