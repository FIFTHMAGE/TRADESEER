'use client';

import { useState, useEffect } from 'react';
import { Settings, Bell, Shield, Database, Palette, User, Key, Save, CheckCircle } from 'lucide-react';

interface UserSettings {
  notifications: {
    email: boolean;
    push: boolean;
    telegram: boolean;
    walletAlerts: boolean;
    priceAlerts: boolean;
  };
  appearance: {
    theme: 'light' | 'dark' | 'auto';
    compactMode: boolean;
    showCharts: boolean;
  };
  trading: {
    autoTracking: boolean;
    riskLevel: 'low' | 'medium' | 'high';
    maxWallets: number;
  };
  api: {
    etherscanKey: string;
    webhookUrl: string;
    updateInterval: number;
  };
}

export default function SettingsPanel() {
  const [settings, setSettings] = useState<UserSettings>({
    notifications: {
      email: true,
      push: true,
      telegram: false,
      walletAlerts: true,
      priceAlerts: true,
    },
    appearance: {
      theme: 'auto',
      compactMode: false,
      showCharts: true,
    },
    trading: {
      autoTracking: true,
      riskLevel: 'medium',
      maxWallets: 20,
    },
    api: {
      etherscanKey: '',
      webhookUrl: '',
      updateInterval: 300,
    },
  });
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [activeTab, setActiveTab] = useState<'notifications' | 'appearance' | 'trading' | 'api'>('notifications');
  const [showSuccess, setShowSuccess] = useState(false);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      setIsLoading(true);
      
      // Load settings from localStorage (in a real app, this would come from your backend)
      const savedSettings = localStorage.getItem('tradeseer-settings');
      if (savedSettings) {
        const parsedSettings = JSON.parse(savedSettings);
        setSettings(parsedSettings);
      }
      
      // Load API settings from environment or bot
      try {
        const response = await fetch('http://localhost:5000/health');
        if (response.ok) {
          const healthData = await response.json();
          // Update API settings with bot data
          setSettings(prev => ({
            ...prev,
            api: {
              ...prev.api,
              webhookUrl: `http://localhost:5000/webhook`,
              updateInterval: 300,
            }
          }));
        }
      } catch (error) {
        console.log('Bot not running, using default API settings');
      }
    } catch (error) {
      console.error('Failed to load settings:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      // Save settings to localStorage (in a real app, this would save to your backend)
      localStorage.setItem('tradeseer-settings', JSON.stringify(settings));
      
      // Show success message
      setShowSuccess(true);
      setTimeout(() => setShowSuccess(false), 3000);
      
      // In a real app, you would also save to your backend here
      console.log('Settings saved:', settings);
    } catch (error) {
      console.error('Failed to save settings:', error);
    } finally {
      setIsSaving(false);
    }
  };

  const updateSetting = (
    category: keyof UserSettings,
    key: string,
    value: any
  ) => {
    setSettings(prev => ({
      ...prev,
      [category]: {
        ...prev[category],
        [key]: value,
      },
    }));
  };

  const resetToDefaults = () => {
    if (confirm('Are you sure you want to reset all settings to defaults?')) {
      setSettings({
        notifications: {
          email: true,
          push: true,
          telegram: false,
          walletAlerts: true,
          priceAlerts: true,
        },
        appearance: {
          theme: 'auto',
          compactMode: false,
          showCharts: true,
        },
        trading: {
          autoTracking: true,
          riskLevel: 'medium',
          maxWallets: 20,
        },
        api: {
          etherscanKey: '',
          webhookUrl: 'http://localhost:5000/webhook',
          updateInterval: 300,
        },
      });
    }
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
        <h1 className="text-3xl font-bold text-secondary-900 mb-2">Settings</h1>
        <p className="text-secondary-600">Customize your TradeSeer experience</p>
      </div>

      {/* Success Message */}
      {showSuccess && (
        <div className="card bg-green-50 border-green-200">
          <div className="flex items-center space-x-3">
            <CheckCircle className="w-6 h-6 text-green-600" />
            <div>
              <h3 className="font-semibold text-green-800">Settings Saved!</h3>
              <p className="text-green-700">Your preferences have been updated successfully.</p>
            </div>
          </div>
        </div>
      )}

      {/* Tab Navigation */}
      <div className="flex space-x-1 bg-gray-100 p-1 rounded-lg">
        <button
          onClick={() => setActiveTab('notifications')}
          className={`flex items-center space-x-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
            activeTab === 'notifications'
              ? 'bg-white text-primary-600 shadow-sm'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          <Bell className="w-4 h-4" />
          <span>Notifications</span>
        </button>
        <button
          onClick={() => setActiveTab('appearance')}
          className={`flex items-center space-x-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
            activeTab === 'appearance'
              ? 'bg-white text-primary-600 shadow-sm'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          <Palette className="w-4 h-4" />
          <span>Appearance</span>
        </button>
        <button
          onClick={() => setActiveTab('trading')}
          className={`flex items-center space-x-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
            activeTab === 'trading'
              ? 'bg-white text-primary-600 shadow-sm'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          <Shield className="w-4 h-4" />
          <span>Trading</span>
        </button>
        <button
          onClick={() => setActiveTab('api')}
          className={`flex items-center space-x-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
            activeTab === 'api'
              ? 'bg-white text-primary-600 shadow-sm'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          <Database className="w-4 h-4" />
          <span>API</span>
        </button>
      </div>

      {/* Settings Content */}
      <div className="card">
        {activeTab === 'notifications' && (
          <div className="space-y-6">
            <h3 className="text-lg font-semibold text-secondary-900">Notification Preferences</h3>
            
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-secondary-900">Email Notifications</p>
                  <p className="text-sm text-secondary-600">Receive updates via email</p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={settings.notifications.email}
                    onChange={(e) => updateSetting('notifications', 'email', e.target.checked)}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
                </label>
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-secondary-900">Push Notifications</p>
                  <p className="text-sm text-secondary-600">Browser push notifications</p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={settings.notifications.push}
                    onChange={(e) => updateSetting('notifications', 'push', e.target.checked)}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
                </label>
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-secondary-900">Telegram Bot</p>
                  <p className="text-sm text-secondary-600">Connect to Telegram bot</p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={settings.notifications.telegram}
                    onChange={(e) => updateSetting('notifications', 'telegram', e.target.checked)}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
                </label>
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-secondary-900">Wallet Alerts</p>
                  <p className="text-sm text-secondary-600">Get notified of wallet activity</p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={settings.notifications.walletAlerts}
                    onChange={(e) => updateSetting('notifications', 'walletAlerts', e.target.checked)}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
                </label>
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-secondary-900">Price Alerts</p>
                  <p className="text-sm text-secondary-600">Token price change notifications</p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={settings.notifications.priceAlerts}
                    onChange={(e) => updateSetting('notifications', 'priceAlerts', e.target.checked)}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
                </label>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'appearance' && (
          <div className="space-y-6">
            <h3 className="text-lg font-semibold text-secondary-900">Appearance Settings</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-secondary-700 mb-2">Theme</label>
                <select
                  value={settings.appearance.theme}
                  onChange={(e) => updateSetting('appearance', 'theme', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                >
                  <option value="light">Light</option>
                  <option value="dark">Dark</option>
                  <option value="auto">Auto (System)</option>
                </select>
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-secondary-900">Compact Mode</p>
                  <p className="text-sm text-secondary-600">Reduce spacing for more content</p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={settings.appearance.compactMode}
                    onChange={(e) => updateSetting('appearance', 'compactMode', e.target.checked)}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
                </label>
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-secondary-900">Show Charts</p>
                  <p className="text-sm text-secondary-600">Display price charts and graphs</p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={settings.appearance.showCharts}
                    onChange={(e) => updateSetting('appearance', 'showCharts', e.target.checked)}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
                </label>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'trading' && (
          <div className="space-y-6">
            <h3 className="text-lg font-semibold text-secondary-900">Trading Preferences</h3>
            
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-secondary-900">Auto Tracking</p>
                  <p className="text-sm text-secondary-600">Automatically track new wallets</p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={settings.trading.autoTracking}
                    onChange={(e) => updateSetting('trading', 'autoTracking', e.target.checked)}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
                </label>
              </div>

              <div>
                <label className="block text-sm font-medium text-secondary-700 mb-2">Risk Level</label>
                <select
                  value={settings.trading.riskLevel}
                  onChange={(e) => updateSetting('trading', 'riskLevel', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                >
                  <option value="low">Low Risk</option>
                  <option value="medium">Medium Risk</option>
                  <option value="high">High Risk</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-secondary-700 mb-2">Max Wallets to Track</label>
                <input
                  type="number"
                  min="1"
                  max="100"
                  value={settings.trading.maxWallets}
                  onChange={(e) => updateSetting('trading', 'maxWallets', parseInt(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
                <p className="text-xs text-secondary-500 mt-1">Maximum number of wallets to track simultaneously</p>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'api' && (
          <div className="space-y-6">
            <h3 className="text-lg font-semibold text-secondary-900">API Configuration</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-secondary-700 mb-2">Etherscan API Key</label>
                <input
                  type="password"
                  value={settings.api.etherscanKey}
                  onChange={(e) => updateSetting('api', 'etherscanKey', e.target.value)}
                  placeholder="Enter your Etherscan API key"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
                <p className="text-xs text-secondary-500 mt-1">Required for blockchain data and wallet tracking</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-secondary-700 mb-2">Webhook URL</label>
                <input
                  type="url"
                  value={settings.api.webhookUrl}
                  onChange={(e) => updateSetting('api', 'webhookUrl', e.target.value)}
                  placeholder="https://your-domain.com/webhook"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
                <p className="text-xs text-secondary-500 mt-1">URL for receiving real-time updates from the bot</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-secondary-700 mb-2">Update Interval (seconds)</label>
                <input
                  type="number"
                  min="30"
                  max="3600"
                  value={settings.api.updateInterval}
                  onChange={(e) => updateSetting('api', 'updateInterval', parseInt(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
                <p className="text-xs text-secondary-500 mt-1">How often to check for updates (30s - 1h)</p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Action Buttons */}
      <div className="flex items-center justify-between">
        <button
          onClick={resetToDefaults}
          className="btn-secondary"
        >
          Reset to Defaults
        </button>
        
        <div className="flex space-x-3">
          <button
            onClick={handleSave}
            disabled={isSaving}
            className="btn-primary flex items-center justify-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSaving ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                <span>Saving...</span>
              </>
            ) : (
              <>
                <Save className="w-4 h-4" />
                <span>Save Settings</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
