import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { Providers } from "@/components/providers";
import { SiteHeader } from "@/components/site-header";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"]
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"]
});

export const metadata: Metadata = {
  title: "Originality Earns",
  description:
    "Real-time semantic novelty scoring for X posts with on-chain rewards on Base."
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${geistSans.variable} ${geistMono.variable} min-h-dvh`}>
        <Providers>
          <div className="relative flex min-h-dvh flex-col">
            <SiteHeader />
            <main className="flex-1">{children}</main>
            <footer className="border-t py-8 text-sm text-muted-foreground">
              <div className="mx-auto flex max-w-5xl flex-col gap-2 px-6 md:flex-row md:items-center md:justify-between">
                <p>Originality Earns — semantic first-seen scoring on Base.</p>
                <p className="text-xs">
                  MVP: configure TwitterAPI.io rules + cron workers for production traffic.
                </p>
              </div>
            </footer>
          </div>
        </Providers>
      </body>
    </html>
  );
}
