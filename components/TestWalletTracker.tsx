'use client';

import { useState, useEffect } from 'react';

export default function TestWalletTracker() {
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    console.log('TestWalletTracker: Component mounted');
    
    // Test API call
    const testAPI = async () => {
      try {
        console.log('TestWalletTracker: Testing API call...');
        const response = await fetch('http://localhost:5000/health');
        const data = await response.json();
        console.log('TestWalletTracker: API response:', data);
        setIsLoading(false);
      } catch (err) {
        console.error('TestWalletTracker: API error:', err);
        setError('API call failed');
        setIsLoading(false);
      }
    };

    testAPI();
  }, []);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <h1 className="text-3xl font-bold text-secondary-900 mb-2">Test Wallet Tracker</h1>
        <p>Loading...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <h1 className="text-3xl font-bold text-secondary-900 mb-2">Test Wallet Tracker</h1>
        <p className="text-red-600">Error: {error}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-secondary-900 mb-2">Test Wallet Tracker</h1>
      <p className="text-green-600">✅ Component loaded successfully!</p>
      <p>This is a test component to debug the WalletTracker issue.</p>
      <p>Check the browser console for debugging information.</p>
    </div>
  );
}
