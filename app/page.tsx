'use client';

import { useEffect, useState } from 'react';
import { Wallet, TrendingUp, Eye, Settings, BarChart3, Search, Plus, Activity, DollarSign, Link } from 'lucide-react';
import Dashboard from '@/components/Dashboard';
import WalletTracker from '@/components/WalletTracker';
import TestWalletTracker from '@/components/TestWalletTracker';
import SimpleWalletTracker from '@/components/SimpleWalletTracker';
import MinimalWalletTracker from '@/components/MinimalWalletTracker';
import ErrorBoundaryWalletTracker from '@/components/ErrorBoundaryWalletTracker';
import TokenDiscovery from '@/components/TokenDiscovery';
import SettingsPanel from '@/components/SettingsPanel';
import Portfolio from '@/components/Portfolio';
import USDCPurchase from '@/components/USDCPurchase';
import WalletConnection from '@/components/WalletConnection';
import { useAppKit } from '@/providers/MiniKitProvider';

type TabType = 'dashboard' | 'tracker' | 'discovery' | 'portfolio' | 'wallets' | 'usdc' | 'settings';

export default function HomePage() {
  const { isReady, isConnected, connectedAddress } = useAppKit();
  const [activeTab, setActiveTab] = useState<TabType>('dashboard');
  const [isLoading, setIsLoading] = useState(true);

  // Initialize AppKit when the app is ready
  useEffect(() => {
    // Simulate app loading and AppKit initialization
    const initializeApp = async () => {
      try {
        // Wait for AppKit to be ready
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        // Additional app initialization
        await new Promise(resolve => setTimeout(resolve, 500));
        setIsLoading(false);
      } catch (error) {
        console.error('App initialization error:', error);
        setIsLoading(false);
      }
    };

    initializeApp();
  }, []);

  // Show loading screen while initializing
  if (isLoading) {
    return (
      <div className="min-h-screen gradient-bg flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 mx-auto mb-4 bg-gradient-to-r from-primary-600 to-accent-600 rounded-full flex items-center justify-center animate-pulse-slow">
            <Eye className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-gradient mb-2">TradeSeer</h1>
          <p className="text-secondary-600">
            {isReady ? 'Initializing trading features...' : 'Loading AppKit...'}
          </p>
          {isReady && (
            <div className="mt-4 text-sm text-green-600">
              ✅ AppKit Ready
            </div>
          )}
        </div>
      </div>
    );
  }

  const renderTabContent = () => {
    console.log('HomePage: Rendering tab:', activeTab);
    switch (activeTab) {
      case 'dashboard':
        console.log('HomePage: Rendering Dashboard');
        return <Dashboard />;
      case 'tracker':
        console.log('HomePage: Rendering WalletTracker');
        return <WalletTracker />;
      case 'discovery':
        console.log('HomePage: Rendering TokenDiscovery');
        return <TokenDiscovery />;
      case 'portfolio':
        console.log('HomePage: Rendering Portfolio');
        return <Portfolio />;
      case 'wallets':
        console.log('HomePage: Rendering WalletConnection component');
        return <WalletConnection />;
      case 'usdc':
        console.log('HomePage: Rendering USDCPurchase');
        return <USDCPurchase />;
      case 'settings':
        console.log('HomePage: Rendering SettingsPanel');
        return <SettingsPanel />;
      default:
        console.log('HomePage: Rendering default Dashboard');
        return <Dashboard />;
    }
  };

  return (
    <div className="min-h-screen gradient-bg">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-gradient-to-r from-primary-600 to-accent-600 rounded-lg flex items-center justify-center">
                <Eye className="w-5 h-5 text-white" />
              </div>
              <h1 className="text-xl font-bold text-gradient">TradeSeer</h1>
            </div>
            
            <div className="flex items-center space-x-2 text-sm text-secondary-600">
              <span>AppKit Status</span>
              <span className={`px-2 py-1 rounded-full text-xs ${
                isConnected 
                  ? 'bg-green-100 text-green-800' 
                  : isReady 
                    ? 'bg-yellow-100 text-yellow-800'
                    : 'bg-red-100 text-red-800'
              }`}>
                {isConnected ? 'Connected' : isReady ? 'Ready' : 'Initializing'}
              </span>
              {isConnected && connectedAddress && (
                <span className="text-xs text-gray-500 font-mono">
                  {connectedAddress.slice(0, 6)}...{connectedAddress.slice(-4)}
                </span>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Navigation Tabs */}
      <nav className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-8">
            {[
              { id: 'dashboard', label: 'Dashboard', icon: BarChart3 },
              { id: 'tracker', label: 'Wallet Tracker', icon: Eye },
              { id: 'discovery', label: 'Token Discovery', icon: Search },
              { id: 'portfolio', label: 'Portfolio', icon: Wallet },
              { id: 'wallets', label: 'Connect Wallets', icon: Link },
              { id: 'usdc', label: 'Buy USDC', icon: DollarSign },
              { id: 'settings', label: 'Settings', icon: Settings },
            ].map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => {
                    console.log('HomePage: Tab clicked:', tab.id);
                    setActiveTab(tab.id as TabType);
                  }}
                  className={`flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm transition-colors duration-200 ${
                    activeTab === tab.id
                      ? 'border-primary-500 text-primary-600'
                      : 'border-transparent text-secondary-500 hover:text-secondary-700 hover:border-secondary-300'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {renderTabContent()}
      </main>
    </div>
  );
}
