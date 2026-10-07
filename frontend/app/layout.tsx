import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "AI-Based Network Connection Predictor",
  description: "Computer Networks Course Project - AI/ML-Powered Network Observability Platform",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <body className="bg-background text-foreground min-h-screen antialiased" suppressHydrationWarning>
        {children}
      </body>
    </html>
  );
}
