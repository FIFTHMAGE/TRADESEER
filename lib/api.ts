// API service for connecting to TradeSeer bot backend

const API_BASE_URL = 'http://localhost:5000';

export interface DashboardStats {
  totalWallets: number;
  averageScore: number;
  totalVolume: number;
  activeWallets: number;
  recentAlerts: number;
  portfolioValue: number;
}

export interface WalletData {
  address: string;
  name?: string;
  balance: number;
  score: number;
  lastActivity: string;
  chain: string;
}

export interface TokenData {
  symbol: string;
  name: string;
  price: number;
  change24h: number;
  volume: number;
  marketCap: number;
}

export interface PurchaseOrder {
  id: string;
  amount: number;
  status: 'pending' | 'completed' | 'failed';
  walletAddress: string;
  createdAt: string;
}

export interface ConnectedWallet {
  address: string;
  name: string;
  isConnected: boolean;
  balance?: number;
}

class TradeSeerAPI {
  private baseURL: string;

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL;
  }

  // Health check
  async getHealth() {
    try {
      const response = await fetch(`${this.baseURL}/health`);
      if (!response.ok) throw new Error('Health check failed');
      return await response.json();
    } catch (error) {
      console.error('Health check error:', error);
      throw error;
    }
  }

  // Get dashboard stats
  async getDashboardStats(): Promise<DashboardStats> {
    try {
      // For now, we'll simulate real data based on bot health
      const health = await this.getHealth();
      
      // Calculate stats based on bot data
      const totalWallets = health.wallets_tracked || 0;
      const averageScore = totalWallets > 0 ? Math.floor(Math.random() * 40) + 60 : 0; // 60-100 range
      const totalVolume = totalWallets * (Math.random() * 1000 + 500); // $500-$1500 per wallet
      const activeWallets = Math.floor(totalWallets * 0.7); // 70% active
      const recentAlerts = Math.floor(Math.random() * 5) + 1; // 1-5 alerts
      const portfolioValue = totalVolume * (Math.random() * 0.5 + 0.8); // 80%-130% of volume

      return {
        totalWallets,
        averageScore,
        totalVolume,
        activeWallets,
        recentAlerts,
        portfolioValue
      };
    } catch (error) {
      console.error('Failed to get dashboard stats:', error);
      // Return default stats
      return {
        totalWallets: 0,
        averageScore: 0,
        totalVolume: 0,
        activeWallets: 0,
        recentAlerts: 0,
        portfolioValue: 0
      };
    }
  }

  // Get tracked wallets
  async getTrackedWallets(): Promise<WalletData[]> {
    try {
      console.log('API: Fetching tracked wallets from:', `${this.baseURL}/wallets`);
      
      const response = await fetch(`${this.baseURL}/wallets`);
      console.log('API: Wallets response status:', response.status);
      console.log('API: Wallets response ok:', response.ok);
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('API: Failed to fetch wallets, status:', response.status, 'error:', errorText);
        throw new Error(`Failed to fetch wallets: HTTP ${response.status}`);
      }
      
      const data = await response.json();
      console.log('API: Wallets response data:', data);
      
      if (data.status === 'success' && data.wallets) {
        const wallets = data.wallets.map((wallet: any) => ({
          address: wallet.address,
          name: wallet.name || `Wallet ${wallet.address.slice(0, 6)}...${wallet.address.slice(-4)}`,
          balance: wallet.balance || 0,
          score: wallet.score || 0,
          lastActivity: wallet.lastActivity || '24h ago',
          chain: wallet.chain || 'Base'
        }));
        console.log('API: Processed wallets:', wallets);
        return wallets;
      }
      
      console.log('API: No wallets found or invalid response format');
      return [];
    } catch (error) {
      console.error('API: Failed to get tracked wallets:', error);
      console.error('API: Error details:', {
        message: error instanceof Error ? error.message : 'Unknown error',
        stack: error instanceof Error ? error.stack : 'No stack trace',
        name: error instanceof Error ? error.name : 'Unknown error type'
      });
      return [];
    }
  }

  // Get trending tokens
  async getTrendingTokens(): Promise<TokenData[]> {
    try {
      // Sample trending token data
      return [
        {
          symbol: 'PEPE',
          name: 'Pepe',
          price: 0.00000123,
          change24h: 15.7,
          volume: 1250000,
          marketCap: 50000000
        },
        {
          symbol: 'SHIB',
          name: 'Shiba Inu',
          price: 0.00001234,
          change24h: -2.3,
          volume: 890000,
          marketCap: 75000000
        },
        {
          symbol: 'DOGE',
          name: 'Dogecoin',
          price: 0.0789,
          change24h: 8.5,
          volume: 2100000,
          marketCap: 110000000
        }
      ];
    } catch (error) {
      console.error('Failed to get trending tokens:', error);
      return [];
    }
  }

  // Create USDC purchase order
  async createUSDCOrder(amount: number, walletAddress: string): Promise<PurchaseOrder> {
    try {
      // Create a unique chat ID for this purchase
      const chatId = Date.now();
      
      const response = await fetch(`${this.baseURL}/webhook`, {
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
        const errorText = await response.text();
        console.error('USDC order creation failed:', errorText);
        throw new Error(`Failed to create order: ${errorText}`);
      }

      // Create the order record
      const order: PurchaseOrder = {
        id: chatId.toString(),
        amount,
        status: 'pending',
        walletAddress,
        createdAt: new Date().toISOString()
      };

      return order;
    } catch (error) {
      console.error('Failed to create USDC order:', error);
      throw error;
    }
  }

  // Track new wallet
  async trackWallet(address: string): Promise<boolean> {
    try {
      console.log('API: Attempting to track wallet:', address);
      console.log('API: Base URL:', this.baseURL);
      
      const payload = {
        message: {
          text: `/track ${address}`,
          chat: { id: Date.now() },
          from: { id: Date.now(), username: 'web_user' }
        }
      };
      
      console.log('API: Request payload:', payload);
      
      const response = await fetch(`${this.baseURL}/webhook`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload)
      });

      console.log('API: Response status:', response.status);
      console.log('API: Response ok:', response.ok);
      console.log('API: Response headers:', Object.fromEntries(response.headers.entries()));
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('API: Response not ok, error text:', errorText);
        throw new Error(`HTTP ${response.status}: ${errorText}`);
      }

      const responseData = await response.text();
      console.log('API: Response data:', responseData);
      
      // Check if the response indicates success
      if (responseData.includes('"status":"ok"') || responseData.includes('"status":"success"')) {
        console.log('API: Wallet tracking successful');
        return true;
      } else {
        console.log('API: Wallet tracking response indicates failure');
        return false;
      }
      
    } catch (error) {
      console.error('API: Failed to track wallet:', error);
      console.error('API: Error details:', {
        message: error instanceof Error ? error.message : 'Unknown error',
        stack: error instanceof Error ? error.stack : 'No stack trace',
        name: error instanceof Error ? error.name : 'Unknown error type'
      });
      return false;
    }
  }

  // Get wallet insights
  async getWalletInsights(address: string): Promise<any> {
    try {
      const response = await fetch(`${this.baseURL}/webhook`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: {
            text: `/insights ${address}`,
            chat: { id: Date.now() },
            from: { id: Date.now(), username: 'web_user' }
          }
        })
      });

      if (!response.ok) throw new Error('Failed to get insights');
      return await response.json();
    } catch (error) {
      console.error('Failed to get wallet insights:', error);
      throw error;
    }
  }

  // Get user's connected wallets for USDC purchase
  async getConnectedWallets(): Promise<ConnectedWallet[]> {
    try {
      const trackedWallets = await this.getTrackedWallets();
      return trackedWallets.map(wallet => ({
        address: wallet.address,
        name: wallet.name || `Wallet ${wallet.address.slice(0, 6)}...`,
        isConnected: true,
        balance: wallet.balance
      }));
    } catch (error) {
      console.error('Failed to get connected wallets:', error);
      return [];
    }
  }
}

export const api = new TradeSeerAPI();
export default TradeSeerAPI;
