"use client";

import { useState } from "react";
import { Header } from "./Header";
import { Sidebar } from "./Sidebar";
import { Footer } from "./Footer";

interface AppShellProps {
  children: React.ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  const [isMobileOpen, setIsMobileOpen] = useState(false);

  return (
    <div className="flex h-screen flex-col overflow-hidden bg-background">
      
      {/* Skip to Content Link */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:rounded-md focus:bg-primary focus:px-4 focus:py-2 focus:text-primary-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
      >
        Skip to content
      </a>

      {/* Header */}
      <Header onMenuToggle={() => setIsMobileOpen(true)} />

      {/* Main Body */}
      <div className="flex flex-1 overflow-hidden">
        
        {/* Permanent Desktop Sidebar */}
        <Sidebar className="hidden md:flex w-64 border-r border-border bg-card/15" />

        {/* Mobile Navigation Drawer */}
        <Sidebar
          isMobile
          isOpen={isMobileOpen}
          onClose={() => setIsMobileOpen(false)}
        />

        {/* Main Content Area + Footer */}
        <div 
          className="flex flex-1 flex-col overflow-y-auto focus-visible:outline-none"
          id="main-content" 
          tabIndex={-1}
        >
          <main className="flex-1">
            {children}
          </main>
          <Footer />
        </div>

      </div>

    </div>
  );
}
