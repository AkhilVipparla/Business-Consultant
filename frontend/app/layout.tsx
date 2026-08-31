import type { Metadata } from "next";
import { Fraunces, Inter } from "next/font/google";
import "./globals.css";

// Warm Retro Editorial typography — see anchor.md/UI_UX_GUIDELINES.md
const fraunces = Fraunces({
  variable: "--font-fraunces",
  subsets: ["latin"],
});

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "VentureMind AI",
  description:
    "An AI-powered Venture Studio that validates, improves, and evaluates startup ideas using a team of specialized AI agents.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${fraunces.variable} ${inter.variable} bg-cream font-sans text-charcoal antialiased`}
      >
        {children}
      </body>
    </html>
  );
}
