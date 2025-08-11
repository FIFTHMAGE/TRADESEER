'use client';

import { useState, useEffect } from 'react';
import { TrendingUp, Eye, Wallet, Activity, ArrowUpRight, ArrowDownRight, Search } from 'lucide-react';
import { api, DashboardStats } from '@/lib/api';

export default function Dashboard() {
  const [stats, setStats] = useState<DashboardStats>({
    totalWallets: 0,
    averageScore: 0,
    totalVolume: 0,
    activeWallets: 0,
    recentAlerts: 0,
    portfolioValue: 0,
  });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    const loadDashboardData = async () => {
      try {
        setIsLoading(true);
        setError('');
        
        // Get real data from the bot API
        const dashboardStats = await api.getDashboardStats();
        setStats(dashboardStats);
      } catch (err) {
        console.error('Failed to load dashboard data:', err);
        setError('Failed to load dashboard data. Please try again.');
        
        // Fallback to default stats
        setStats({
          totalWallets: 0,
          averageScore: 0,
          totalVolume: 0,
          activeWallets: 0,
          recentAlerts: 0,
          portfolioValue: 0,
        });
      } finally {
        setIsLoading(false);
      }
    };

    loadDashboardData();
    
    // Refresh data every 30 seconds
    const interval = setInterval(loadDashboardData, 30000);
    return () => clearInterval(interval);
  }, []);

  const StatCard = ({ title, value, icon: Icon, change, changeType }: {
    title: string;
    value: string | number;
    icon: any;
    change?: string;
    changeType?: 'positive' | 'negative';
  }) => (
    <div className="card hover:shadow-glow transition-shadow duration-300">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-secondary-600">{title}</p>
          <p className="text-2xl font-bold text-secondary-900">{value}</p>
          {change && (
            <div className={`flex items-center mt-1 text-sm ${
              changeType === 'positive' ? 'text-green-600' : 'text-red-600'
            }`}>
              {changeType === 'positive' ? (
                <ArrowUpRight className="w-4 h-4 mr-1" />
              ) : (
                <ArrowDownRight className="w-4 h-4 mr-1" />
              )}
              {change}
            </div>
          )}
        </div>
        <div className="p-3 bg-primary-100 rounded-lg">
          <Icon className="w-6 h-6 text-primary-600" />
        </div>
      </div>
    </div>
  );

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/4 mb-6"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="h-32 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div className="text-center py-12">
          <div className="w-16 h-16 mx-auto mb-4 bg-red-100 rounded-full flex items-center justify-center">
            <Activity className="w-8 h-8 text-red-600" />
          </div>
          <h2 className="text-xl font-semibold text-red-800 mb-2">Connection Error</h2>
          <p className="text-red-600 mb-4">{error}</p>
          <button 
            onClick={() => window.location.reload()} 
            className="btn-primary"
          >
            Retry Connection
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-secondary-900 mb-2">Dashboard</h1>
        <p className="text-secondary-600">Your trading portfolio overview and insights</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <StatCard
          title="Tracked Wallets"
          value={stats.totalWallets}
          icon={Eye}
          change={`${stats.totalWallets > 0 ? '+' : ''}${stats.totalWallets} total`}
          changeType={stats.totalWallets > 0 ? "positive" : undefined}
        />
        <StatCard
          title="Average Score"
          value={`${stats.averageScore}/100`}
          icon={TrendingUp}
          change={stats.averageScore > 70 ? "High Quality" : stats.averageScore > 50 ? "Good" : "Needs Attention"}
          changeType={stats.averageScore > 70 ? "positive" : stats.averageScore > 50 ? undefined : "negative"}
        />
        <StatCard
          title="Total Volume"
          value={`$${stats.totalVolume.toLocaleString()}`}
          icon={Activity}
          change={`${stats.totalWallets > 0 ? Math.floor(stats.totalVolume / stats.totalWallets).toLocaleString() : 0} avg per wallet`}
        />
        <StatCard
          title="Active Wallets"
          value={stats.activeWallets}
          icon={Wallet}
          change={`${stats.totalWallets > 0 ? Math.round((stats.activeWallets / stats.totalWallets) * 100) : 0}% active`}
          changeType={stats.activeWallets > 0 ? "positive" : undefined}
        />
        <StatCard
          title="Recent Alerts"
          value={stats.recentAlerts}
          icon={Activity}
          change="Last 24h"
        />
        <StatCard
          title="Portfolio Value"
          value={`$${stats.portfolioValue.toLocaleString()}`}
          icon={TrendingUp}
          change={`${stats.totalVolume > 0 ? Math.round(((stats.portfolioValue - stats.totalVolume) / stats.totalVolume) * 100) : 0}% from volume`}
          changeType={stats.portfolioValue > stats.totalVolume ? "positive" : "negative"}
        />
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h3 className="text-lg font-semibold text-secondary-900 mb-4">Quick Actions</h3>
          <div className="space-y-3">
            <button 
              onClick={() => window.location.href = '/tracker'}
              className="w-full btn-primary flex items-center justify-center space-x-2"
            >
              <Eye className="w-4 h-4" />
              <span>Track New Wallet</span>
            </button>
            <button 
              onClick={() => window.location.href = '/discovery'}
              className="w-full btn-secondary flex items-center justify-center space-x-2"
            >
              <Search className="w-4 h-4" />
              <span>Discover Tokens</span>
            </button>
            <button 
              onClick={() => window.location.href = '/portfolio'}
              className="w-full btn-secondary flex items-center justify-center space-x-2"
            >
              <Wallet className="w-4 h-4" />
              <span>View Portfolio</span>
            </button>
          </div>
        </div>

        <div className="card">
          <h3 className="text-lg font-semibold text-secondary-900 mb-4">Recent Activity</h3>
          <div className="space-y-3">
            {stats.recentAlerts > 0 ? (
              <>
                <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
                  <div className="flex items-center space-x-3">
                    <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                    <span className="text-sm text-green-800">
                      {stats.recentAlerts} wallet{stats.recentAlerts > 1 ? 's' : ''} received ETH
                    </span>
                  </div>
                  <span className="text-xs text-green-600">2m ago</span>
                </div>
                <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
                  <div className="flex items-center space-x-3">
                    <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                    <span className="text-sm text-blue-800">
                      Portfolio value: ${stats.portfolioValue.toLocaleString()}
                    </span>
                  </div>
                  <span className="text-xs text-blue-600">15m ago</span>
                </div>
                <div className="flex items-center justify-between p-3 bg-purple-50 rounded-lg">
                  <div className="flex items-center space-x-3">
                    <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
                    <span className="text-sm text-purple-800">
                      {stats.totalWallets} wallet{stats.totalWallets > 1 ? 's' : ''} being monitored
                    </span>
                  </div>
                  <span className="text-xs text-purple-600">1h ago</span>
                </div>
              </>
            ) : (
              <div className="text-center py-8 text-gray-500">
                <Activity className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                <p>No recent activity</p>
                <p className="text-sm">Start tracking wallets to see alerts</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
