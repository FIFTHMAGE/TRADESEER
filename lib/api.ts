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
      const health = await this.getHealth();
      const walletCount = health.wallets_tracked || 0;
      
      // Generate sample wallet data
      const wallets: WalletData[] = [];
      for (let i = 0; i < walletCount; i++) {
        wallets.push({
          address: `0x${Math.random().toString(16).substr(2, 8)}...${Math.random().toString(16).substr(2, 4)}`,
          name: `Wallet ${i + 1}`,
          balance: Math.random() * 10 + 0.1, // 0.1 - 10 ETH
          score: Math.floor(Math.random() * 40) + 60, // 60-100
          lastActivity: `${Math.floor(Math.random() * 24)}h ago`,
          chain: 'Base'
        });
      }
      
      return wallets;
    } catch (error) {
      console.error('Failed to get tracked wallets:', error);
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
      const response = await fetch(`${this.baseURL}/webhook`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: {
            text: `/buy_usdc ${amount}`,
            chat: { id: Date.now() },
            from: { id: Date.now(), username: 'web_user' }
          }
        })
      });

      if (!response.ok) throw new Error('Failed to create order');

      const order: PurchaseOrder = {
        id: Date.now().toString(),
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
      const response = await fetch(`${this.baseURL}/webhook`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: {
            text: `/track ${address}`,
            chat: { id: Date.now() },
            from: { id: Date.now(), username: 'web_user' }
          }
        })
      });

      return response.ok;
    } catch (error) {
      console.error('Failed to track wallet:', error);
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
}

export const api = new TradeSeerAPI();
export default TradeSeerAPI;
