'use client';

import { useState, useEffect } from 'react';
import { Wallet, Plus, Trash2, Copy, CheckCircle, AlertCircle, Link, ExternalLink, Network } from 'lucide-react';
import { api } from '@/lib/api';
import { useAppKit } from '@/providers/MiniKitProvider';

interface WalletData {
  address: string;
  name?: string;
  balance?: number;
  score?: number;
  lastActivity?: string;
  chain?: string;
}

export default function WalletConnection() {
  const { modal, isReady, isConnected, connectedAddress, openModal, disconnect, refreshConnection } = useAppKit();
  const [wallets, setWallets] = useState<WalletData[]>([]);
  const [isLoadingWallets, setIsLoadingWallets] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [copiedAddress, setCopiedAddress] = useState('');
  const [isConnecting, setIsConnecting] = useState(false);
  const [isDisconnecting, setIsDisconnecting] = useState(false);

  useEffect(() => {
    loadWallets();
  }, []);

  // Update local state when AppKit connection changes
  useEffect(() => {
    if (isConnected && connectedAddress) {
      setSuccess('Wallet connected successfully!');
      setTimeout(() => setSuccess(''), 3000);
      setIsConnecting(false);
    } else if (!isConnected && !connectedAddress) {
      setSuccess('Wallet disconnected successfully');
      setTimeout(() => setSuccess(''), 3000);
      setIsDisconnecting(false);
    }
  }, [isConnected, connectedAddress]);

  const loadWallets = async () => {
    try {
      setIsLoadingWallets(true);
      const walletData = await api.getTrackedWallets();
      setWallets(walletData);
    } catch (error) {
      console.error('Error loading wallets:', error);
      setError('Failed to load wallets');
    } finally {
      setIsLoadingWallets(false);
    }
  };

  const handleWalletConnect = async () => {
    try {
      setIsConnecting(true);
      setError('');
      
      // Open Reown AppKit modal for wallet connection
      await openModal();
      
      // The connection status will be updated through the AppKit provider
      
    } catch (error) {
      console.error('Error connecting wallet:', error);
      setError('Failed to connect wallet. Please try again.');
      setIsConnecting(false);
    }
  };

  const handleNetworkSwitch = async () => {
    try {
      // Open network selection modal
      await openModal();
    } catch (error) {
      console.error('Error switching network:', error);
      setError('Failed to open network selection');
    }
  };

  const handleDisconnect = async () => {
    try {
      setIsDisconnecting(true);
      setError('');
      
      // Disconnect through the AppKit provider
      await disconnect();
      
      // Clear any success message and show disconnect confirmation
      setSuccess('Wallet disconnected successfully');
      setTimeout(() => setSuccess(''), 3000);
      
    } catch (error) {
      console.error('Error disconnecting wallet:', error);
      setError('Failed to disconnect wallet. Please try refreshing the page.');
      setIsDisconnecting(false);
    }
  };

  const handleRemoveWallet = async (address: string) => {
    if (confirm('Are you sure you want to remove this wallet?')) {
      try {
        // For now, just remove from local state
        // TODO: Add API endpoint to remove wallets
        setWallets(prev => prev.filter(w => w.address !== address));
        setSuccess('Wallet removed successfully');
        setTimeout(() => setSuccess(''), 2000);
      } catch (error) {
        setError('Failed to remove wallet');
      }
    }
  };

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedAddress(text);
      setTimeout(() => setCopiedAddress(''), 2000);
    } catch (error) {
      console.error('Failed to copy:', error);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Connect Wallets</h1>
        <p className="text-gray-600">Connect your Web3 wallets using Reown AppKit</p>
      </div>

      {/* Connection Status */}
      {isConnected && connectedAddress && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <CheckCircle className="w-5 h-5 text-green-600" />
              <div>
                <h3 className="font-medium text-green-800">Wallet Connected</h3>
                <p className="text-sm text-green-700 font-mono">
                  {connectedAddress.slice(0, 6)}...{connectedAddress.slice(-4)}
                </p>
              </div>
            </div>
            <button
              onClick={handleDisconnect}
              disabled={isDisconnecting}
              className="px-3 py-1 bg-red-100 text-red-700 rounded-md hover:bg-red-200 transition-colors text-sm disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
            >
              {isDisconnecting ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-red-700"></div>
                  <span>Disconnecting...</span>
                </>
              ) : (
                <span>Disconnect</span>
              )}
            </button>
          </div>
        </div>
      )}

      {/* AppKit Status */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className={`w-3 h-3 rounded-full ${isReady ? 'bg-green-500' : 'bg-yellow-500'}`}></div>
            <div>
              <h3 className="font-medium text-blue-800">AppKit Status</h3>
              <p className="text-sm text-blue-700">
                {isReady ? 'Ready' : 'Initializing'} • {isConnected ? 'Connected' : 'Not Connected'}
              </p>
            </div>
          </div>
          <button
            onClick={refreshConnection}
            className="px-3 py-1 bg-blue-100 text-blue-700 rounded-md hover:bg-blue-200 transition-colors text-sm"
          >
            Refresh
          </button>
        </div>
      </div>

      {/* Reown AppKit Integration */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
          <Link className="w-5 h-5 mr-2 text-primary-600" />
          Connect New Wallet
        </h2>
        
        <div className="text-center py-8">
          <div className="w-16 h-16 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center mx-auto mb-4">
            <Wallet className="w-8 h-8 text-white" />
          </div>
          
          <h3 className="text-lg font-medium text-gray-900 mb-2">Connect Your Wallet</h3>
          <p className="text-gray-600 mb-6 max-w-md mx-auto">
            Use Reown AppKit to securely connect your Web3 wallet and start tracking your portfolio
          </p>
          
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <button
              onClick={handleWalletConnect}
              disabled={isConnecting || isConnected}
              className="px-8 py-3 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-lg hover:from-blue-600 hover:to-purple-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2 transition-all duration-200 transform hover:scale-105"
            >
              {isConnecting ? (
                <>
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                  <span>Connecting...</span>
                </>
              ) : (
                <>
                  <Link className="w-5 h-5" />
                  <span>Connect Wallet</span>
                </>
              )}
            </button>
            
            <button
              onClick={handleNetworkSwitch}
              disabled={!isConnected}
              className="px-6 py-3 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 flex items-center justify-center space-x-2 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Network className="w-5 h-5" />
              <span>Switch Network</span>
            </button>
          </div>
          
          <p className="text-sm text-gray-500 mt-4">
            Supports MetaMask, Trust Wallet, Rainbow, and 100+ other wallets
          </p>
        </div>

        {/* Error/Success Messages */}
        {error && (
          <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md flex items-center">
            <AlertCircle className="w-5 h-5 text-red-500 mr-2" />
            <span className="text-red-700">{error}</span>
          </div>
        )}
        
        {success && (
          <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-md flex items-center">
            <CheckCircle className="w-5 h-5 text-green-500 mr-2" />
            <span className="text-green-700">{success}</span>
          </div>
        )}
      </div>

      {/* Connected Wallets */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
          <Wallet className="w-5 h-5 mr-2 text-primary-600" />
          Connected Wallets ({wallets.length})
        </h2>

        {isLoadingWallets ? (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading wallets...</p>
          </div>
        ) : wallets.length === 0 ? (
          <div className="text-center py-8 border-2 border-dashed border-gray-300 rounded-lg">
            <Wallet className="w-12 h-12 mx-auto mb-3 text-gray-400" />
            <p className="text-gray-500 mb-2">No wallets connected yet</p>
            <p className="text-sm text-gray-400">Connect your first wallet above to get started</p>
          </div>
        ) : (
          <div className="space-y-3">
            {wallets.map((wallet) => (
              <div key={wallet.address} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      <h3 className="font-medium text-gray-900">{wallet.name || `Wallet ${wallet.address.slice(0, 6)}...${wallet.address.slice(-4)}`}</h3>
                      <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">
                        Connected
                      </span>
                    </div>
                    
                    <div className="flex items-center space-x-4 text-sm text-gray-600">
                      <div className="flex items-center space-x-1">
                        <span className="font-mono">{wallet.address.slice(0, 6)}...{wallet.address.slice(-4)}</span>
                        <button
                          onClick={() => copyToClipboard(wallet.address)}
                          className="text-gray-400 hover:text-gray-600 transition-colors"
                          title="Copy address"
                        >
                          {copiedAddress === wallet.address ? (
                            <CheckCircle className="w-4 h-4 text-green-500" />
                          ) : (
                            <Copy className="w-4 h-4" />
                          )}
                        </button>
                      </div>
                      
                      <span>•</span>
                      <span>Balance: ${(wallet.balance || 0).toFixed(2)}</span>
                      <span>•</span>
                      <span>Score: {wallet.score || 0}</span>
                      <span>•</span>
                      <span>{wallet.chain || 'Base'}</span>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => copyToClipboard(wallet.address)}
                      className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-md transition-colors"
                      title="Copy address"
                    >
                      {copiedAddress === wallet.address ? (
                        <CheckCircle className="w-4 h-4 text-green-500" />
                      ) : (
                        <Copy className="w-4 h-4" />
                      )}
                    </button>
                    
                    <button
                      onClick={() => handleRemoveWallet(wallet.address)}
                      className="p-2 text-red-400 hover:text-red-600 hover:bg-red-50 rounded-md transition-colors"
                      title="Remove wallet"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
