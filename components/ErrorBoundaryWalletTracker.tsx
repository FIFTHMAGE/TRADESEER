'use client';

import { Component, ReactNode } from 'react';
import WalletTracker from './WalletTracker';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: any) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="space-y-6">
          <div>
            <h1 className="text-3xl font-bold text-secondary-900 mb-2">Wallet Tracker</h1>
            <p className="text-secondary-600">Monitor smart wallets and track their activities</p>
          </div>
          
          <div className="card bg-red-50 border-red-200">
            <h3 className="text-lg font-semibold text-red-800 mb-2">Component Error</h3>
            <p className="text-red-700 mb-4">
              The WalletTracker component encountered an error and could not load.
            </p>
            <details className="text-sm text-red-600">
              <summary className="cursor-pointer">Error Details</summary>
              <pre className="mt-2 p-2 bg-red-100 rounded text-xs overflow-auto">
                {this.state.error?.toString()}
              </pre>
            </details>
            <button
              onClick={() => this.setState({ hasError: false })}
              className="mt-4 btn-primary"
            >
              Try Again
            </button>
          </div>
        </div>
      );
    }

    return <WalletTracker />;
  }
}

export default ErrorBoundary;
