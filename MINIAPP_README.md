# TradeSeer Mini App

A modern, web-based version of TradeSeer built with Next.js and MiniKit for Farcaster integration on Base network.

## 🚀 Features

- **Dashboard Analytics**: Comprehensive overview of your trading portfolio and tracked wallets
- **Wallet Tracker**: Monitor smart wallets with real-time alerts and scoring
- **Token Discovery**: Find trending tokens with AI-powered analysis and risk assessment
- **Portfolio Management**: Track your positions across multiple wallets and chains
- **Settings Panel**: Customize notifications, appearance, and trading preferences
- **Farcaster Integration**: Built with MiniKit for seamless Base network integration

## 🛠️ Tech Stack

- **Frontend**: Next.js 14, React 18, TypeScript
- **Styling**: Tailwind CSS with custom design system
- **Blockchain**: MiniKit, Wagmi, Viem for Ethereum interactions
- **Icons**: Lucide React for beautiful, consistent icons
- **Deployment**: Ready for Vercel, Netlify, or any Next.js-compatible platform

## 📋 Prerequisites

1. **Node.js 18+** and npm/yarn
2. **Coinbase Developer Platform Account** for MiniKit API key
3. **Etherscan API Key** (optional, for enhanced blockchain data)

## 🚀 Quick Start

### 1. Install Dependencies

```bash
npm install
# or
yarn install
```

### 2. Environment Configuration

Copy the environment template and configure your variables:

```bash
cp env_template_miniapp.txt .env.local
```

Edit `.env.local` with your actual values:

```env
# Required: Get this from Coinbase Developer Platform
NEXT_PUBLIC_CDP_CLIENT_API_KEY=your_api_key_here

# Required: Your app's public URL
NEXT_PUBLIC_URL=https://your-domain.com

# Optional: Customize app branding
NEXT_PUBLIC_ONCHAINKIT_PROJECT_NAME=TradeSeer
```

### 3. Development Server

```bash
npm run dev
# or
yarn dev
```

Open [http://localhost:3000](http://localhost:3000) to view your Mini App.

### 4. Build for Production

```bash
npm run build
npm start
# or
yarn build
yarn start
```

## 🔧 Configuration

### MiniKit Setup

1. Visit [Coinbase Developer Platform](https://developer.coinbase.com/)
2. Create a new project
3. Enable MiniKit integration
4. Copy your API key to `NEXT_PUBLIC_CDP_CLIENT_API_KEY`

### Customization

- **App Name**: Update `NEXT_PUBLIC_ONCHAINKIT_PROJECT_NAME`
- **Colors**: Modify `tailwind.config.ts` for brand colors
- **Assets**: Add custom hero and splash images
- **Features**: Enable/disable components in the main page

## 📱 Mini App Features

### Dashboard
- Portfolio overview with key metrics
- Recent activity feed
- Quick action buttons
- Performance indicators

### Wallet Tracker
- Add/remove wallet addresses
- Smart scoring system (0-100)
- Transaction volume tracking
- Real-time status monitoring

### Token Discovery
- Search and filter tokens
- Risk level assessment
- Social metrics analysis
- Trending score calculation

### Portfolio
- Multi-wallet support
- Token position tracking
- Value calculations
- 24h change monitoring

### Settings
- Notification preferences
- Appearance customization
- Trading parameters
- API configuration

## 🚀 Deployment

### Vercel (Recommended)

1. Connect your GitHub repository
2. Set environment variables in Vercel dashboard
3. Deploy automatically on push

### Netlify

1. Connect your repository
2. Set build command: `npm run build`
3. Set publish directory: `.next`
4. Configure environment variables

### Manual Deployment

1. Build the app: `npm run build`
2. Upload `.next` folder to your server
3. Configure your web server for Next.js

## 🔒 Security Considerations

- **API Keys**: Never commit `.env.local` to version control
- **Environment Variables**: Use `NEXT_PUBLIC_` prefix only for client-side variables
- **HTTPS**: Always use HTTPS in production
- **Rate Limiting**: Implement API rate limiting for production use

## 🧪 Testing

### Development Testing

```bash
# Run linting
npm run lint

# Type checking
npx tsc --noEmit

# Build testing
npm run build
```

### Mini App Testing

1. Test in Farcaster Frames
2. Verify MiniKit integration
3. Test wallet connections
4. Validate responsive design

## 📚 API Integration

### Current Implementation

- **Simulated Data**: Components use mock data for development
- **MiniKit Hooks**: Ready for real blockchain interactions
- **Wagmi Integration**: Ethereum wallet connection support

### Future Enhancements

- **Backend API**: Replace mock data with real endpoints
- **Database**: Add persistent storage for user data
- **Webhooks**: Implement real-time notifications
- **Analytics**: Add comprehensive trading analytics

## 🐛 Troubleshooting

### Common Issues

1. **MiniKit Not Loading**
   - Check `NEXT_PUBLIC_CDP_CLIENT_API_KEY`
   - Verify Coinbase Developer Platform setup

2. **Build Errors**
   - Clear `.next` folder: `rm -rf .next`
   - Reinstall dependencies: `rm -rf node_modules && npm install`

3. **Styling Issues**
   - Verify Tailwind CSS is properly configured
   - Check PostCSS configuration

### Getting Help

- Check the [MiniKit documentation](https://docs.base.org/base-app/build-with-minikit/)
- Review Next.js and React documentation
- Check browser console for errors

## 🔄 Migration from Python Bot

This Mini App replaces the Python-based Telegram bot with:

- **Web Interface**: Modern, responsive web UI
- **Farcaster Integration**: Native Base network support
- **Component Architecture**: Modular, maintainable code
- **TypeScript**: Type-safe development experience
- **Real-time Updates**: Live data and notifications

## 📈 Roadmap

- [ ] Real blockchain data integration
- [ ] User authentication system
- [ ] Advanced analytics dashboard
- [ ] Mobile app optimization
- [ ] Social trading features
- [ ] Multi-chain support

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Base network for MiniKit
- Farcaster community
- Next.js and React teams
- Tailwind CSS creators

---

**Ready to launch your TradeSeer Mini App?** 🚀

Follow the setup instructions above and start building the future of decentralized trading!
