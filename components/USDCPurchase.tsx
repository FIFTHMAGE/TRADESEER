'use client';

import { useState, useEffect } from 'react';
import { DollarSign, CreditCard, Wallet, ArrowRight, CheckCircle, AlertCircle, ExternalLink } from 'lucide-react';
import { api, PurchaseOrder, ConnectedWallet } from '@/lib/api';

export default function USDCPurchase() {
  const [amount, setAmount] = useState<string>('100');
  const [selectedWallet, setSelectedWallet] = useState<ConnectedWallet | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [purchaseUrl, setPurchaseUrl] = useState<string>('');
  const [showSuccess, setShowSuccess] = useState(false);
  const [error, setError] = useState<string>('');
  const [orders, setOrders] = useState<PurchaseOrder[]>([]);
  const [wallets, setWallets] = useState<ConnectedWallet[]>([]);

  const presetAmounts = [50, 100, 250, 500, 1000];

  useEffect(() => {
    loadConnectedWallets();
  }, []);

  const loadConnectedWallets = async () => {
    try {
      const connectedWallets = await api.getConnectedWallets();
      setWallets(connectedWallets);
      
      // Auto-select first wallet if available
      if (connectedWallets.length > 0 && !selectedWallet) {
        setSelectedWallet(connectedWallets[0]);
      }
    } catch (error) {
      console.error('Error loading wallets:', error);
      setError('Failed to load connected wallets');
    }
  };

  const handleAmountChange = (newAmount: string) => {
    setAmount(newAmount);
    setError('');
  };

  const handlePresetAmount = (presetAmount: number) => {
    setAmount(presetAmount.toString());
    setError('');
  };

  const handleCustomAmount = (event: React.ChangeEvent<HTMLInputElement>) => {
    const value = event.target.value;
    if (value === '' || /^\d+(\.\d{0,2})?$/.test(value)) {
      setAmount(value);
      setError('');
    }
  };

  const createPurchaseOrder = async () => {
    if (!amount || parseFloat(amount) <= 0) {
      setError('Please enter a valid amount');
      return;
    }

    if (!selectedWallet) {
      setError('Please select a wallet first');
      return;
    }

    setIsLoading(true);
    setError('');

    try {
      // Create a unique chat ID for this purchase
      const chatId = Date.now();
      
      // Use the API service to create the order via webhook
      const response = await fetch('http://localhost:5000/webhook', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: {
            text: `/buy_usdc ${amount}`,
            chat: { id: chatId },
            from: { id: chatId, username: 'web_user' }
          }
        })
      });

      if (!response.ok) {
        throw new Error('Failed to create purchase order');
      }

      // Create local order record
      const newOrder: PurchaseOrder = {
        id: Date.now().toString(),
        amount: parseFloat(amount),
        status: 'pending',
        walletAddress: selectedWallet.address,
        createdAt: new Date().toISOString()
      };
      
      setOrders(prev => [newOrder, ...prev]);
      setShowSuccess(true);
      
      // Generate FunBonk purchase URL (this would come from the bot's response)
      // For now, we'll create a demo URL
      const demoUrl = `https://sandbox.funbonk.com/onramp?amount=${amount}&wallet=${selectedWallet.address}&merchant=${process.env.NEXT_PUBLIC_FONBNK_MERCHANT || 'aBnoWFna'}`;
      setPurchaseUrl(demoUrl);
      
      setTimeout(() => setShowSuccess(false), 5000);
    } catch (error) {
      setError('Failed to create purchase order. Please try again.');
      console.error('Purchase error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const openPurchaseUrl = () => {
    if (purchaseUrl) {
      window.open(purchaseUrl, '_blank');
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-secondary-900 mb-2">Buy USDC</h1>
        <p className="text-secondary-600">Purchase USDC with fiat currency and receive it directly in your wallet</p>
      </div>

      {/* Success Message */}
      {showSuccess && (
        <div className="card bg-green-50 border-green-200">
          <div className="flex items-center space-x-3">
            <CheckCircle className="w-6 h-6 text-green-600" />
            <div>
              <h3 className="font-semibold text-green-800">Purchase Order Created!</h3>
              <p className="text-green-700">Your USDC purchase order has been created successfully.</p>
              {purchaseUrl && (
                <button
                  onClick={openPurchaseUrl}
                  className="mt-2 btn-primary text-sm flex items-center space-x-2"
                >
                  <ExternalLink className="w-4 h-4" />
                  <span>Complete Purchase</span>
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="card bg-red-50 border-red-200">
          <div className="flex items-center space-x-3">
            <AlertCircle className="w-6 h-6 text-red-600" />
            <p className="text-red-700">{error}</p>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Purchase Form */}
        <div className="card">
          <h2 className="text-xl font-semibold mb-4">Purchase Details</h2>
          
          {/* Amount Selection */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-secondary-700 mb-3">
              Amount (USD)
            </label>
            
            {/* Preset Amounts */}
            <div className="grid grid-cols-3 gap-2 mb-3">
              {presetAmounts.map((preset) => (
                <button
                  key={preset}
                  onClick={() => handlePresetAmount(preset)}
                  className={`p-3 text-sm font-medium rounded-lg border transition-colors ${
                    amount === preset.toString()
                      ? 'border-primary-500 bg-primary-50 text-primary-700'
                      : 'border-gray-300 text-gray-700 hover:border-gray-400'
                  }`}
                >
                  ${preset}
                </button>
              ))}
            </div>
            
            {/* Custom Amount */}
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <DollarSign className="h-5 w-5 text-gray-400" />
              </div>
              <input
                type="text"
                value={amount}
                onChange={handleCustomAmount}
                placeholder="Enter custom amount"
                className="block w-full pl-10 pr-3 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              />
            </div>
          </div>

          {/* Wallet Selection */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-secondary-700 mb-2">
              Select Wallet
            </label>
            
            {wallets.length === 0 ? (
              <div className="text-center py-6 border-2 border-dashed border-gray-300 rounded-lg">
                <Wallet className="w-8 h-8 mx-auto mb-2 text-gray-400" />
                <p className="text-gray-500 mb-2">No wallets connected</p>
                <p className="text-sm text-gray-400">Connect a wallet first to purchase USDC</p>
              </div>
            ) : (
              <div className="space-y-2">
                {wallets.map((wallet) => (
                  <button
                    key={wallet.address}
                    onClick={() => setSelectedWallet(wallet)}
                    className={`w-full p-3 text-left border rounded-lg transition-colors ${
                      selectedWallet?.address === wallet.address
                        ? 'border-primary-500 bg-primary-50 text-primary-700'
                        : 'border-gray-300 text-gray-700 hover:border-gray-400'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium">{wallet.name}</p>
                        <p className="text-sm font-mono">
                          {wallet.address.slice(0, 6)}...{wallet.address.slice(-4)}
                        </p>
                        {wallet.balance !== undefined && (
                          <p className="text-sm text-gray-600">
                            Balance: ${wallet.balance.toFixed(2)}
                          </p>
                        )}
                      </div>
                      {selectedWallet?.address === wallet.address && (
                        <CheckCircle className="w-5 h-5 text-primary-600" />
                      )}
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Purchase Button */}
          <button
            onClick={createPurchaseOrder}
            disabled={isLoading || !amount || !selectedWallet}
            className="w-full btn-primary flex items-center justify-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                <span>Creating Order...</span>
              </>
            ) : (
              <>
                <CreditCard className="w-5 h-5" />
                <span>Buy USDC</span>
              </>
            )}
          </button>
        </div>

        {/* Order History */}
        <div className="card">
          <h2 className="text-xl font-semibold mb-4">Recent Orders</h2>
          
          {orders.length === 0 ? (
            <div className="text-center py-8 text-secondary-500">
              <CreditCard className="w-12 h-12 mx-auto mb-3 text-secondary-300" />
              <p>No orders yet</p>
              <p className="text-sm">Your USDC purchase orders will appear here</p>
            </div>
          ) : (
            <div className="space-y-3">
              {orders.map((order) => (
                <div key={order.id} className="p-3 border border-gray-200 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium">${order.amount}</span>
                    <span className={`px-2 py-1 text-xs rounded-full ${
                      order.status === 'completed' ? 'bg-green-100 text-green-800' :
                      order.status === 'failed' ? 'bg-red-100 text-red-800' :
                      'bg-yellow-100 text-yellow-800'
                    }`}>
                      {order.status}
                    </span>
                  </div>
                  <p className="text-sm text-secondary-600 font-mono">
                    {order.walletAddress.slice(0, 6)}...{order.walletAddress.slice(-4)}
                  </p>
                  <p className="text-xs text-secondary-500 mt-1">
                    {new Date(order.createdAt).toLocaleDateString()}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
