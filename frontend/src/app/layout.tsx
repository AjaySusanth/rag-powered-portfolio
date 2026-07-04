import type { Metadata, Viewport } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { ThemeProvider } from "@/components/providers/ThemeProvider";
import { QueryProvider } from "@/components/providers/QueryProvider";
import { SonnerProvider } from "@/components/providers/SonnerProvider";
import { AppShell } from "@/components/layout/AppShell";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Ajay Susanth | RAG-Powered Developer Portfolio",
  description: "Explore the engineering portfolio of Ajay Susanth, featuring a production-grade RAG pipeline, pgvector semantic search, and robust systems architecture.",
  openGraph: {
    title: "Ajay Susanth | RAG-Powered Developer Portfolio",
    description: "Explore the engineering portfolio of Ajay Susanth, featuring a production-grade RAG pipeline, pgvector semantic search, and robust systems architecture.",
    url: "https://ajaysusanth.com",
    siteName: "Ajay Susanth Portfolio",
    type: "website",
    locale: "en_US",
  },
  twitter: {
    card: "summary_large_image",
    title: "Ajay Susanth | RAG-Powered Developer Portfolio",
    description: "Explore the engineering portfolio of Ajay Susanth, featuring a production-grade RAG pipeline, pgvector semantic search, and robust systems architecture.",
  },
  icons: {
    icon: "/favicon.ico",
  },
};

export const viewport: Viewport = {
  themeColor: "#0B0E14",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
      suppressHydrationWarning
    >
      <body className="min-h-full flex flex-col font-sans">
        <QueryProvider>
          <ThemeProvider
            attribute="class"
            defaultTheme="dark"
            enableSystem
            disableTransitionOnChange
          >
            <AppShell>{children}</AppShell>
            <SonnerProvider />
          </ThemeProvider>
        </QueryProvider>
      </body>
    </html>
  );
}
