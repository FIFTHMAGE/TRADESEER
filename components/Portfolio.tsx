'use client';

import { useState, useEffect } from 'react';
import { Wallet, Plus, ExternalLink, TrendingUp, TrendingDown, Activity, DollarSign } from 'lucide-react';
import { api, WalletData } from '@/lib/api';

interface PortfolioPosition {
  id: string;
  tokenSymbol: string;
  tokenName: string;
  amount: number;
  priceUsd: number;
  valueUsd: number;
  change24h: number;
  chain: string;
  lastUpdated: string;
}

interface ConnectedWallet extends WalletData {
  id: string;
  name: string;
  isConnected: boolean;
}

export default function Portfolio() {
  const [positions, setPositions] = useState<PortfolioPosition[]>([]);
  const [wallets, setWallets] = useState<ConnectedWallet[]>([]);
  const [isConnectingWallet, setIsConnectingWallet] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    loadPortfolioData();
  }, []);

  const loadPortfolioData = async () => {
    try {
      setIsLoading(true);
      setError('');
      
      // Get real wallet data from the API
      const walletData = await api.getTrackedWallets();
      
      // Transform the data to match our interface
      const transformedWallets: ConnectedWallet[] = walletData.map((wallet, index) => ({
        id: index.toString(),
        address: wallet.address,
        name: wallet.name || `Wallet ${index + 1}`,
        balance: wallet.balance,
        score: wallet.score,
        lastActivity: wallet.lastActivity,
        chain: wallet.chain,
        isConnected: index === 0, // First wallet is connected by default
      }));
      
      setWallets(transformedWallets);
      
      // Generate portfolio positions based on wallet data
      const portfolioPositions: PortfolioPosition[] = [];
      
      // Add ETH positions for each wallet
      transformedWallets.forEach((wallet, index) => {
        if (wallet.balance > 0) {
          portfolioPositions.push({
            id: `eth-${index}`,
            tokenSymbol: 'ETH',
            tokenName: 'Ethereum',
            amount: wallet.balance,
            priceUsd: 2450.67, // Current ETH price (would come from price API)
            valueUsd: wallet.balance * 2450.67,
            change24h: Math.random() * 10 - 5, // Random change between -5% and +5%
            chain: wallet.chain,
            lastUpdated: wallet.lastActivity,
          });
        }
      });
      
      // Add sample token positions
      portfolioPositions.push(
        {
          id: 'usdc-1',
          tokenSymbol: 'USDC',
          tokenName: 'USD Coin',
          amount: 1250.00,
          priceUsd: 1.00,
          valueUsd: 1250.00,
          change24h: 0.0,
          chain: 'Base',
          lastUpdated: '1 hour ago',
        },
        {
          id: 'pepe-1',
          tokenSymbol: 'PEPE',
          tokenName: 'Pepe',
          amount: 1000000,
          priceUsd: 0.00000123,
          valueUsd: 1.23,
          change24h: 15.7,
          chain: 'Base',
          lastUpdated: '15 minutes ago',
        }
      );
      
      setPositions(portfolioPositions);
    } catch (err) {
      console.error('Failed to load portfolio data:', err);
      setError('Failed to load portfolio data. Please try again.');
      
      // Fallback to sample data
      setWallets([
        {
          id: '1',
          address: '0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6',
          name: 'Main Trading Wallet',
          balance: 2.45,
          score: 95,
          lastActivity: '2 minutes ago',
          chain: 'Base',
          isConnected: true,
        }
      ]);

      setPositions([
        {
          id: '1',
          tokenSymbol: 'ETH',
          tokenName: 'Ethereum',
          amount: 2.45,
          priceUsd: 2450.67,
          valueUsd: 6004.14,
          change24h: 2.3,
          chain: 'Base',
          lastUpdated: '2 minutes ago',
        },
        {
          id: '2',
          tokenSymbol: 'USDC',
          tokenName: 'USD Coin',
          amount: 1250.00,
          priceUsd: 1.00,
          valueUsd: 1250.00,
          change24h: 0.0,
          chain: 'Base',
          lastUpdated: '1 hour ago',
        }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const connectWallet = () => {
    setIsConnectingWallet(true);
    // Simulate wallet connection
    setTimeout(() => {
      setIsConnectingWallet(false);
      // In a real app, this would open wallet connection modal
      alert('Wallet connection would open here. For demo, using sample data.');
    }, 1000);
  };

  const getChangeColor = (change: number) => {
    if (change > 0) return 'text-green-600';
    if (change < 0) return 'text-red-600';
    return 'text-gray-600';
  };

  const getChangeIcon = (change: number) => {
    if (change > 0) return <TrendingUp className="w-4 h-4" />;
    if (change < 0) return <TrendingDown className="w-4 h-4" />;
    return <Activity className="w-4 h-4" />;
  };

  const totalPortfolioValue = positions.reduce((sum, position) => sum + position.valueUsd, 0);
  const totalChange24h = positions.reduce((sum, position) => {
    const positionChange = (position.change24h / 100) * position.valueUsd;
    return sum + positionChange;
  }, 0);
  const totalChangePercentage = totalPortfolioValue > 0 ? (totalChange24h / totalPortfolioValue) * 100 : 0;

  if (isLoading) {
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

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-secondary-900 mb-2">Portfolio</h1>
          <p className="text-secondary-600">Track your crypto investments and performance</p>
        </div>
        <button
          onClick={connectWallet}
          disabled={isConnectingWallet}
          className="btn-primary flex items-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isConnectingWallet ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
              <span>Connecting...</span>
            </>
          ) : (
            <>
              <Plus className="w-4 h-4" />
              <span>Connect Wallet</span>
            </>
          )}
        </button>
      </div>

      {/* Error Message */}
      {error && (
        <div className="card bg-red-50 border-red-200">
          <div className="flex items-center space-x-3">
            <Activity className="w-6 h-6 text-red-600" />
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

      {/* Portfolio Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card text-center">
          <div className="text-2xl font-bold text-secondary-900 mb-1">
            ${totalPortfolioValue.toLocaleString()}
          </div>
          <div className="text-sm text-secondary-600">Total Value</div>
        </div>
        <div className="card text-center">
          <div className={`text-2xl font-bold mb-1 ${getChangeColor(totalChangePercentage)}`}>
            {totalChangePercentage > 0 ? '+' : ''}{totalChangePercentage.toFixed(2)}%
          </div>
          <div className="text-sm text-secondary-600">24h Change</div>
        </div>
        <div className="card text-center">
          <div className="text-2xl font-bold text-primary-600 mb-1">{wallets.length}</div>
          <div className="text-sm text-secondary-600">Connected Wallets</div>
        </div>
      </div>

      {/* Connected Wallets */}
      <div className="card">
        <h3 className="text-lg font-semibold text-secondary-900 mb-4">Connected Wallets</h3>
        <div className="space-y-3">
          {wallets.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <Wallet className="w-12 h-12 mx-auto mb-3 text-gray-300" />
              <p>No wallets connected</p>
              <p className="text-sm">Connect a wallet to view your portfolio</p>
            </div>
          ) : (
            wallets.map((wallet) => (
              <div key={wallet.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center space-x-3">
                  <div className={`w-3 h-3 rounded-full ${wallet.isConnected ? 'bg-green-500' : 'bg-gray-400'}`}></div>
                  <div>
                    <p className="font-medium text-secondary-900">{wallet.name}</p>
                    <p className="text-sm text-secondary-600 font-mono">
                      {wallet.address.slice(0, 6)}...{wallet.address.slice(-4)}
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="font-medium text-secondary-900">{wallet.balance.toFixed(4)} ETH</p>
                  <p className="text-sm text-secondary-600">{wallet.chain}</p>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Portfolio Positions */}
      <div className="card">
        <h3 className="text-lg font-semibold text-secondary-900 mb-4">Portfolio Positions</h3>
        <div className="space-y-3">
          {positions.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <DollarSign className="w-12 h-12 mx-auto mb-3 text-gray-300" />
              <p>No positions found</p>
              <p className="text-sm">Connect a wallet to view your holdings</p>
            </div>
          ) : (
            positions.map((position) => (
              <div key={position.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-primary-100 rounded-lg flex items-center justify-center">
                    <span className="text-sm font-bold text-primary-600">{position.tokenSymbol[0]}</span>
                  </div>
                  <div>
                    <p className="font-medium text-secondary-900">{position.tokenSymbol}</p>
                    <p className="text-sm text-secondary-600">{position.tokenName}</p>
                  </div>
                </div>
                
                <div className="text-right">
                  <p className="font-medium text-secondary-900">
                    {position.amount.toLocaleString()} {position.tokenSymbol}
                  </p>
                  <p className="text-sm text-secondary-600">
                    ${position.valueUsd.toLocaleString()}
                  </p>
                </div>
                
                <div className="text-right">
                  <div className={`flex items-center space-x-1 text-sm ${getChangeColor(position.change24h)}`}>
                    {getChangeIcon(position.change24h)}
                    <span>{position.change24h > 0 ? '+' : ''}{position.change24h.toFixed(1)}%</span>
                  </div>
                  <p className="text-xs text-secondary-500">{position.chain}</p>
                </div>
                
                <div className="text-right">
                  <p className="text-sm text-secondary-600">${position.priceUsd.toFixed(6)}</p>
                  <p className="text-xs text-secondary-500">{position.lastUpdated}</p>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Portfolio Chart Placeholder */}
      <div className="card">
        <h3 className="text-lg font-semibold text-secondary-900 mb-4">Portfolio Performance</h3>
        <div className="h-64 bg-gray-100 rounded-lg flex items-center justify-center">
          <div className="text-center text-gray-500">
            <TrendingUp className="w-16 h-16 mx-auto mb-3 text-gray-300" />
            <p>Portfolio chart would be displayed here</p>
            <p className="text-sm">Connect to a charting service for real-time data</p>
          </div>
        </div>
      </div>
    </div>
  );
}
