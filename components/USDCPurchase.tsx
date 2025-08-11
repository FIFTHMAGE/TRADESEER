'use client';

import { useState, useEffect } from 'react';
import { DollarSign, CreditCard, Wallet, ArrowRight, CheckCircle, AlertCircle } from 'lucide-react';
import { api, PurchaseOrder } from '@/lib/api';

export default function USDCPurchase() {
  const [amount, setAmount] = useState<string>('100');
  const [walletAddress, setWalletAddress] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);
  const [purchaseUrl, setPurchaseUrl] = useState<string>('');
  const [showSuccess, setShowSuccess] = useState(false);
  const [error, setError] = useState<string>('');
  const [orders, setOrders] = useState<PurchaseOrder[]>([]);

  const presetAmounts = [50, 100, 250, 500, 1000];

  useEffect(() => {
    // Load user's connected wallets (this would come from your wallet connection)
    const loadWallets = async () => {
      try {
        // For demo purposes, using a placeholder
        setWalletAddress('0x1234...5678');
      } catch (error) {
        console.error('Error loading wallets:', error);
      }
    };

    loadWallets();
  }, []);

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

    if (!walletAddress) {
      setError('Please connect a wallet first');
      return;
    }

    setIsLoading(true);
    setError('');

    try {
      // Use the API service to create the order
      const newOrder = await api.createUSDCOrder(parseFloat(amount), walletAddress);
      
      setOrders(prev => [newOrder, ...prev]);
      setShowSuccess(true);
      
      // Generate purchase URL (this would come from your onramp service)
      const demoUrl = `https://buy.example.com?amount=${amount}&wallet=${walletAddress}`;
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

          {/* Wallet Address */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-secondary-700 mb-2">
              Wallet Address
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Wallet className="h-5 w-5 text-gray-400" />
              </div>
              <input
                type="text"
                value={walletAddress}
                onChange={(e) => setWalletAddress(e.target.value)}
                placeholder="Enter wallet address"
                className="block w-full pl-10 pr-3 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              />
            </div>
          </div>

          {/* Purchase Button */}
          <button
            onClick={createPurchaseOrder}
            disabled={isLoading || !amount || !walletAddress}
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

          {/* Purchase URL */}
          {purchaseUrl && (
            <div className="mt-4">
              <button
                onClick={openPurchaseUrl}
                className="w-full btn-secondary flex items-center justify-center space-x-2"
              >
                <span>Complete Purchase</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          )}
        </div>

        {/* Order History */}
        <div className="card">
          <h2 className="text-xl font-semibold mb-4">Order History</h2>
          
          {orders.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <CreditCard className="w-12 h-12 mx-auto mb-3 text-gray-300" />
              <p>No orders yet</p>
              <p className="text-sm">Create your first USDC purchase order</p>
            </div>
          ) : (
            <div className="space-y-3">
              {orders.map((order) => (
                <div key={order.id} className="border border-gray-200 rounded-lg p-3">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium">${order.amount} USDC</span>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      order.status === 'completed' ? 'bg-green-100 text-green-800' :
                      order.status === 'failed' ? 'bg-red-100 text-red-800' :
                      'bg-yellow-100 text-yellow-800'
                    }`}>
                      {order.status.charAt(0).toUpperCase() + order.status.slice(1)}
                    </span>
                  </div>
                  <div className="text-sm text-gray-600">
                    <p>Wallet: {order.walletAddress}</p>
                    <p>Created: {new Date(order.createdAt).toLocaleDateString()}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Features */}
      <div className="card">
        <h2 className="text-xl font-semibold mb-4">Why Buy USDC?</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="text-center">
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mx-auto mb-3">
              <DollarSign className="w-6 h-6 text-blue-600" />
            </div>
            <h3 className="font-medium text-secondary-900 mb-1">Stable Value</h3>
            <p className="text-sm text-secondary-600">USDC maintains a 1:1 peg with USD</p>
          </div>
          <div className="text-center">
            <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mx-auto mb-3">
              <CreditCard className="w-6 h-6 text-green-600" />
            </div>
            <h3 className="font-medium text-secondary-900 mb-1">Easy Purchase</h3>
            <p className="text-sm text-secondary-600">Buy with credit card, bank transfer, or Apple Pay</p>
          </div>
          <div className="text-center">
            <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mx-auto mb-3">
              <Wallet className="w-6 h-6 text-purple-600" />
            </div>
            <h3 className="font-medium text-secondary-900 mb-1">Instant Delivery</h3>
            <p className="text-sm text-secondary-600">Receive USDC directly in your wallet</p>
          </div>
        </div>
      </div>
    </div>
  );
}
