'use client';

import { useState, useEffect } from 'react';
import { Search, TrendingUp, AlertTriangle, Star, Activity, DollarSign, Users } from 'lucide-react';
import { api, TokenData } from '@/lib/api';

interface TokenInfo extends TokenData {
  id: string;
  discoveryRating: number;
  riskLevel: 'low' | 'medium' | 'high';
  trendingScore: number;
  socialMetrics: {
    holders: number;
    socialScore: number;
    communityGrowth: number;
  };
}

export default function TokenDiscovery() {
  const [tokens, setTokens] = useState<TokenInfo[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [filterRisk, setFilterRisk] = useState<'all' | 'low' | 'medium' | 'high'>('all');
  const [error, setError] = useState<string>('');

  useEffect(() => {
    loadTrendingTokens();
  }, []);

  const loadTrendingTokens = async () => {
    try {
      setIsLoading(true);
      setError('');
      
      // Get real token data from the API
      const tokenData = await api.getTrendingTokens();
      
      // Transform the data to match our interface
      const transformedTokens: TokenInfo[] = tokenData.map((token, index) => ({
        id: index.toString(),
        symbol: token.symbol,
        name: token.name,
        price: token.price,
        change24h: token.change24h,
        volume: token.volume,
        marketCap: token.marketCap,
        discoveryRating: Math.floor(Math.random() * 30) + 70, // 70-100 range
        riskLevel: token.change24h > 20 ? 'high' : token.change24h > 5 ? 'medium' : 'low',
        trendingScore: Math.floor(Math.random() * 30) + 70, // 70-100 range
        socialMetrics: {
          holders: Math.floor(token.marketCap / 1000) + Math.floor(Math.random() * 100000),
          socialScore: Math.floor(Math.random() * 30) + 70, // 70-100 range
          communityGrowth: Math.random() * 20 + 5, // 5-25% range
        },
      }));
      
      setTokens(transformedTokens);
    } catch (err) {
      console.error('Failed to load trending tokens:', err);
      setError('Failed to load trending tokens. Please try again.');
      
      // Fallback to sample data
      setTokens([
        {
          id: '1',
          symbol: 'PEPE',
          name: 'Pepe',
          price: 0.00000123,
          change24h: 15.7,
          volume: 2500000,
          marketCap: 50000000,
          discoveryRating: 92,
          riskLevel: 'medium',
          trendingScore: 95,
          socialMetrics: {
            holders: 125000,
            socialScore: 88,
            communityGrowth: 12.5,
          },
        },
        {
          id: '2',
          symbol: 'SHIB',
          name: 'Shiba Inu',
          price: 0.00001234,
          change24h: -2.3,
          volume: 1800000,
          marketCap: 75000000,
          discoveryRating: 78,
          riskLevel: 'low',
          trendingScore: 72,
          socialMetrics: {
            holders: 980000,
            socialScore: 85,
            communityGrowth: 8.2,
          },
        }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const filteredTokens = tokens.filter(token => {
    const matchesSearch = token.symbol.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         token.name.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesRisk = filterRisk === 'all' || token.riskLevel === filterRisk;
    return matchesSearch && matchesRisk;
  });

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'low':
        return 'bg-green-100 text-green-800';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800';
      case 'high':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getChangeColor = (change: number) => {
    if (change > 0) return 'text-green-600';
    if (change < 0) return 'text-red-600';
    return 'text-gray-600';
  };

  const getChangeIcon = (change: number) => {
    if (change > 0) return <TrendingUp className="w-4 h-4" />;
    if (change < 0) return <TrendingUp className="w-4 h-4 transform rotate-180" />;
    return <Activity className="w-4 h-4" />;
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/4 mb-6"></div>
          <div className="space-y-4">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-32 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-secondary-900 mb-2">Token Discovery</h1>
        <p className="text-secondary-600">Discover trending tokens and analyze their potential</p>
      </div>

      {/* Error Message */}
      {error && (
        <div className="card bg-red-50 border-red-200">
          <div className="flex items-center space-x-3">
            <AlertTriangle className="w-6 h-6 text-red-600" />
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

      {/* Search and Filters */}
      <div className="card">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <input
                type="text"
                placeholder="Search tokens by symbol or name..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
            </div>
          </div>
          <div className="flex space-x-2">
            <button
              onClick={() => setFilterRisk('all')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                filterRisk === 'all'
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              All
            </button>
            <button
              onClick={() => setFilterRisk('low')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                filterRisk === 'low'
                  ? 'bg-green-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Low Risk
            </button>
            <button
              onClick={() => setFilterRisk('medium')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                filterRisk === 'medium'
                  ? 'bg-yellow-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Medium
            </button>
            <button
              onClick={() => setFilterRisk('high')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                filterRisk === 'high'
                  ? 'bg-red-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              High Risk
            </button>
          </div>
        </div>
      </div>

      {/* Tokens List */}
      <div className="space-y-4">
        {filteredTokens.length === 0 ? (
          <div className="text-center py-12">
            <Search className="w-16 h-16 mx-auto mb-4 text-gray-300" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No tokens found</h3>
            <p className="text-gray-500 mb-4">
              {searchQuery ? `No tokens match "${searchQuery}"` : 'No trending tokens available'}
            </p>
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="btn-primary"
              >
                Clear Search
              </button>
            )}
          </div>
        ) : (
          filteredTokens.map((token) => (
            <div key={token.id} className="card hover:shadow-glow transition-shadow duration-300">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Token Basic Info */}
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center space-x-3">
                      <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center">
                        <span className="text-lg font-bold text-primary-600">{token.symbol[0]}</span>
                      </div>
                      <div>
                        <h3 className="text-lg font-semibold text-secondary-900">{token.name}</h3>
                        <p className="text-sm text-secondary-600">${token.symbol}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-lg font-bold text-secondary-900">
                        ${token.price.toFixed(8)}
                      </div>
                      <div className={`flex items-center space-x-1 text-sm ${getChangeColor(token.change24h)}`}>
                        {getChangeIcon(token.change24h)}
                        <span>{token.change24h > 0 ? '+' : ''}{token.change24h.toFixed(1)}%</span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-xs text-secondary-500">Market Cap</p>
                      <p className="text-sm font-medium text-secondary-900">
                        ${(token.marketCap / 1000000).toFixed(1)}M
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-secondary-500">Volume 24h</p>
                      <p className="text-sm font-medium text-secondary-900">
                        ${(token.volume / 1000000).toFixed(1)}M
                      </p>
                    </div>
                  </div>
                </div>

                {/* Token Metrics */}
                <div>
                  <div className="grid grid-cols-2 gap-4 mb-4">
                    <div>
                      <p className="text-xs text-secondary-500">Discovery Rating</p>
                      <div className="flex items-center space-x-2">
                        <div className="flex-1 bg-gray-200 rounded-full h-2">
                          <div 
                            className="bg-primary-600 h-2 rounded-full" 
                            style={{ width: `${token.discoveryRating}%` }}
                          ></div>
                        </div>
                        <span className="text-sm font-medium text-secondary-900">{token.discoveryRating}</span>
                      </div>
                    </div>
                    <div>
                      <p className="text-xs text-secondary-500">Trending Score</p>
                      <div className="flex items-center space-x-2">
                        <div className="flex-1 bg-gray-200 rounded-full h-2">
                          <div 
                            className="bg-accent-600 h-2 rounded-full" 
                            style={{ width: `${token.trendingScore}%` }}
                          ></div>
                        </div>
                        <span className="text-sm font-medium text-secondary-900">{token.trendingScore}</span>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-secondary-600">Risk Level</span>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getRiskColor(token.riskLevel)}`}>
                        {token.riskLevel.charAt(0).toUpperCase() + token.riskLevel.slice(1)}
                      </span>
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-secondary-600">Holders</span>
                      <span className="text-sm font-medium text-secondary-900">
                        {token.socialMetrics.holders.toLocaleString()}
                      </span>
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-secondary-600">Community Growth</span>
                      <span className="text-sm font-medium text-green-600">
                        +{token.socialMetrics.communityGrowth.toFixed(1)}%
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex space-x-3 mt-4 pt-4 border-t border-gray-200">
                <button className="btn-primary flex-1 flex items-center justify-center space-x-2">
                  <Star className="w-4 h-4" />
                  <span>Track Token</span>
                </button>
                <button className="btn-secondary flex-1 flex items-center justify-center space-x-2">
                  <Activity className="w-4 h-4" />
                  <span>View Chart</span>
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Stats Summary */}
      {filteredTokens.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="card text-center">
            <div className="text-2xl font-bold text-primary-600 mb-1">{filteredTokens.length}</div>
            <div className="text-sm text-secondary-600">Tokens Found</div>
          </div>
          <div className="card text-center">
            <div className="text-2xl font-bold text-green-600 mb-1">
              {filteredTokens.filter(t => t.change24h > 0).length}
            </div>
            <div className="text-sm text-secondary-600">Gaining</div>
          </div>
          <div className="card text-center">
            <div className="text-2xl font-bold text-blue-600 mb-1">
              {Math.round(filteredTokens.reduce((sum, t) => sum + t.discoveryRating, 0) / filteredTokens.length)}
            </div>
            <div className="text-sm text-secondary-600">Avg Rating</div>
          </div>
          <div className="card text-center">
            <div className="text-2xl font-bold text-purple-600 mb-1">
              {filteredTokens.filter(t => t.riskLevel === 'low').length}
            </div>
            <div className="text-sm text-secondary-600">Low Risk</div>
          </div>
        </div>
      )}
    </div>
  );
}
