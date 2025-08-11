import { Metadata } from 'next';
import './globals.css';

export async function generateMetadata(): Promise<Metadata> {
  const URL = process.env.NEXT_PUBLIC_URL || 'http://localhost:3000';
  return {
    title: 'TradeSeer - Smart Wallet Tracking',
    description: "AI-powered smart wallet tracking and trading insights on Base network",
    other: {
      "fc:frame": JSON.stringify({
        version: "next",
        imageUrl: `${URL}/hero-image.png`,
        button: {
          title: "Launch TradeSeer",
          action: {
            type: "launch_frame",
            name: "TradeSeer",
            url: URL,
            splashImageUrl: `${URL}/splash-image.png`,
            splashBackgroundColor: "#1e3a8a",
          },
        },
      }),
    },
  };
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-gray-50 font-sans">
        {children}
      </body>
    </html>
  );
}
