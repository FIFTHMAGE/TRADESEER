'use client';

export default function SimpleWalletTracker() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-secondary-900 mb-2">Wallet Tracker</h1>
        <p className="text-secondary-600">Monitor smart wallets and track their activities</p>
      </div>

      <div className="card">
        <h3 className="text-lg font-semibold text-secondary-900 mb-4">Simple Test</h3>
        <p>This is a simple test component to see if the WalletTracker loads.</p>
        <p>If you can see this, the component is working!</p>
      </div>

      <div className="card">
        <h3 className="text-lg font-semibold text-secondary-900 mb-4">Debug Info</h3>
        <p>Component loaded at: {new Date().toLocaleTimeString()}</p>
        <p>Check browser console for any errors.</p>
      </div>
    </div>
  );
}
