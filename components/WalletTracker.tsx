'use client';

import { useState, useEffect } from 'react';
import { Eye, Plus, Trash2, TrendingUp, Activity, AlertCircle, CheckCircle } from 'lucide-react';
import { api, WalletData } from '@/lib/api';

interface TrackedWallet extends WalletData {
  id: string;
  volume: number;
  status: 'active' | 'inactive' | 'alert';
  transactions: number;
}

export default function WalletTracker() {
  const [wallets, setWallets] = useState<TrackedWallet[]>([]);
  const [isAddingWallet, setIsAddingWallet] = useState(false);
  const [newWalletAddress, setNewWalletAddress] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    console.log('WalletTracker: Component mounted, loading wallets...');
    loadTrackedWallets();
  }, []);

  const loadTrackedWallets = async () => {
    try {
      console.log('WalletTracker: Starting to load wallets...');
      setIsLoading(true);
      setError('');
      
      // Get real wallet data from the API
      console.log('WalletTracker: Calling API to get wallets...');
      const walletData = await api.getTrackedWallets();
      console.log('WalletTracker: API response:', walletData);
      
      // Transform the data to match our interface
      const transformedWallets: TrackedWallet[] = walletData.map((wallet, index) => ({
        id: index.toString(),
        address: wallet.address,
        name: wallet.name || `Wallet ${index + 1}`,
        score: wallet.score,
        balance: wallet.balance,
        lastActivity: wallet.lastActivity,
        chain: wallet.chain,
        volume: wallet.balance * (Math.random() * 1000 + 500), // Simulate volume based on balance
        status: wallet.score > 80 ? 'active' : wallet.score > 60 ? 'inactive' : 'alert',
        transactions: Math.floor(wallet.score / 10) + Math.floor(Math.random() * 20), // Simulate transaction count
      }));
      
      console.log('WalletTracker: Transformed wallets:', transformedWallets);
      setWallets(transformedWallets);
    } catch (err) {
      console.error('WalletTracker: Failed to load tracked wallets:', err);
      setError('Failed to load tracked wallets. Please try again.');
      
      // Fallback to sample data
      console.log('WalletTracker: Using fallback data...');
      setWallets([
        {
          id: '1',
          address: '0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6',
          name: 'Whale Wallet #1',
          score: 95,
          balance: 12.5,
          lastActivity: '2 minutes ago',
          chain: 'Base',
          volume: 1250.50,
          status: 'active',
          transactions: 47,
        },
        {
          id: '2',
          address: '0x8ba1f109551bD432803012645Hac136c772c3c7c',
          name: 'Smart Money',
          score: 87,
          balance: 8.9,
          lastActivity: '15 minutes ago',
          chain: 'Base',
          volume: 890.25,
          status: 'active',
          transactions: 32,
        }
      ]);
    } finally {
      console.log('WalletTracker: Finished loading, setting loading to false');
      setIsLoading(false);
    }
  };

  const handleAddWallet = async () => {
    if (newWalletAddress.trim()) {
      try {
        console.log('WalletTracker: Adding new wallet:', newWalletAddress);
        // Use the API to track the new wallet
        const success = await api.trackWallet(newWalletAddress.trim());
        
        if (success) {
          console.log('WalletTracker: Wallet added successfully');
          // Add the new wallet to the list
          const newWallet: TrackedWallet = {
            id: Date.now().toString(),
            address: newWalletAddress.trim(),
            name: `Wallet ${wallets.length + 1}`,
            score: Math.floor(Math.random() * 40) + 60, // Random score 60-100
            balance: 0,
            lastActivity: 'Just added',
            chain: 'Base',
            volume: 0,
            status: 'active',
            transactions: 0,
          };
          setWallets([...wallets, newWallet]);
          setNewWalletAddress('');
          setIsAddingWallet(false);
          
          // Reload wallets to get updated data
          setTimeout(loadTrackedWallets, 1000);
        } else {
          console.log('WalletTracker: Failed to add wallet');
          setError('Failed to add wallet. Please try again.');
        }
      } catch (err) {
        console.error('WalletTracker: Error adding wallet:', err);
        setError('Failed to add wallet. Please try again.');
      }
    }
  };

  const removeWallet = (id: string) => {
    console.log('WalletTracker: Removing wallet:', id);
    setWallets(wallets.filter(wallet => wallet.id !== id));
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600 bg-green-100';
    if (score >= 60) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
        return <CheckCircle className="w-4 h-4 text-green-600" />;
      case 'inactive':
        return <Activity className="w-4 h-4 text-yellow-600" />;
      case 'alert':
        return <AlertCircle className="w-4 h-4 text-red-600" />;
      default:
        return <Activity className="w-4 h-4 text-gray-600" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-800';
      case 'inactive':
        return 'bg-yellow-100 text-yellow-800';
      case 'alert':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  console.log('WalletTracker: Rendering component, isLoading:', isLoading, 'wallets:', wallets.length, 'error:', error);

  if (isLoading) {
    console.log('WalletTracker: Showing loading state');
    return (
      <div className="space-y-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/4 mb-6"></div>
          <div className="space-y-4">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-24 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  console.log('WalletTracker: Showing main content');

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-secondary-900 mb-2">Wallet Tracker</h1>
          <p className="text-secondary-600">Monitor smart wallets and track their activities</p>
        </div>
        <button
          onClick={() => setIsAddingWallet(true)}
          className="btn-primary flex items-center space-x-2"
        >
          <Plus className="w-4 h-4" />
          <span>Track New Wallet</span>
        </button>
      </div>

      {/* Error Message */}
      {error && (
        <div className="card bg-red-50 border-red-200">
          <div className="flex items-center space-x-3">
            <AlertCircle className="w-6 h-6 text-red-600" />
            <p className="text-red-700">{error}</p>
            <button 
              onClick={() => setError('')} 
              className="text-red-600 hover:text-red-800"
            >
              ×
            </button>
          </div>
        </div>
      )}

      {/* Add Wallet Modal */}
      {isAddingWallet && (
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">Track New Wallet</h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-secondary-700 mb-2">
                Wallet Address
              </label>
              <input
                type="text"
                value={newWalletAddress}
                onChange={(e) => setNewWalletAddress(e.target.value)}
                placeholder="Enter wallet address (0x...)"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
            </div>
            <div className="flex space-x-3">
              <button
                onClick={handleAddWallet}
                disabled={!newWalletAddress.trim()}
                className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Track Wallet
              </button>
              <button
                onClick={() => {
                  setIsAddingWallet(false);
                  setNewWalletAddress('');
                }}
                className="btn-secondary"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Wallets List */}
      <div className="space-y-4">
        {wallets.length === 0 ? (
          <div className="text-center py-12">
            <Eye className="w-16 h-16 mx-auto mb-4 text-gray-300" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No wallets tracked</h3>
            <p className="text-gray-500 mb-4">Start tracking wallets to monitor their activities</p>
            <button
              onClick={() => setIsAddingWallet(true)}
              className="btn-primary"
            >
              Track Your First Wallet
            </button>
          </div>
        ) : (
          wallets.map((wallet) => (
            <div key={wallet.id} className="card hover:shadow-glow transition-shadow duration-300">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-3 mb-2">
                    <h3 className="text-lg font-semibold text-secondary-900">{wallet.name}</h3>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(wallet.status)}`}>
                      {wallet.status.charAt(0).toUpperCase() + wallet.status.slice(1)}
                    </span>
                  </div>
                  <p className="text-sm text-secondary-600 mb-2 font-mono">{wallet.address}</p>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div>
                      <p className="text-xs text-secondary-500">Score</p>
                      <p className={`text-sm font-medium ${getScoreColor(wallet.score)} px-2 py-1 rounded`}>
                        {wallet.score}/100
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-secondary-500">Balance</p>
                      <p className="text-sm font-medium text-secondary-900">{wallet.balance.toFixed(4)} ETH</p>
                    </div>
                    <div>
                      <p className="text-xs text-secondary-500">Volume</p>
                      <p className="text-sm font-medium text-secondary-900">${wallet.volume.toLocaleString()}</p>
                    </div>
                    <div>
                      <p className="text-xs text-secondary-500">Transactions</p>
                      <p className="text-sm font-medium text-secondary-900">{wallet.transactions}</p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2 mt-2 text-xs text-secondary-500">
                    <Activity className="w-3 h-3" />
                    <span>Last activity: {wallet.lastActivity}</span>
                    <span>•</span>
                    <span>{wallet.chain}</span>
                  </div>
                </div>
                <div className="flex items-center space-x-2 ml-4">
                  <button
                    onClick={() => removeWallet(wallet.id)}
                    className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                    title="Remove wallet"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Stats Summary */}
      {wallets.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="card text-center">
            <div className="text-2xl font-bold text-primary-600 mb-1">{wallets.length}</div>
            <div className="text-sm text-secondary-600">Total Wallets</div>
          </div>
          <div className="card text-center">
            <div className="text-2xl font-bold text-green-600 mb-1">
              {wallets.filter(w => w.status === 'active').length}
            </div>
            <div className="text-sm text-secondary-600">Active Wallets</div>
          </div>
          <div className="card text-center">
            <div className="text-2xl font-bold text-blue-600 mb-1">
              {Math.round(wallets.reduce((sum, w) => sum + w.score, 0) / wallets.length)}
            </div>
            <div className="text-sm text-secondary-600">Average Score</div>
          </div>
        </div>
      )}
    </div>
  );
}
