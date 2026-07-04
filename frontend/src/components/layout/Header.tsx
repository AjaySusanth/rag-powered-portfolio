"use client";

import { useEffect, useState } from "react";
import { useTheme } from "next-themes";
import { Menu, Sun, Moon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Logo } from "@/components/common/Logo";

// Local SVG component for GitHub to ensure cross-version compatibility
function GithubIcon(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="currentColor"
      className="h-5 w-5"
      {...props}
    >
      <path d="M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12" />
    </svg>
  );
}

interface HeaderProps {
  onMenuToggle: () => void;
}

export function Header({ onMenuToggle }: HeaderProps) {
  const { resolvedTheme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  // Prevent hydration mismatch
  useEffect(() => {
    setMounted(true);
  }, []);

  return (
    <header className="sticky top-0 z-40 w-full border-b border-border bg-background/95 backdrop-blur-md supports-[backdrop-filter]:bg-background/60">
      <div className="flex h-16 items-center px-4 md:px-8 gap-4 justify-between">
        
        {/* Left Side: Menu Trigger + Logo + Title */}
        <div className="flex items-center gap-3">
          {/* Mobile menu trigger */}
          <Button
            variant="ghost"
            size="icon"
            onClick={onMenuToggle}
            className="md:hidden h-9 w-9 text-muted-foreground hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring"
            aria-label="Open menu"
          >
            <Menu className="h-5 w-5" />
          </Button>

          {/* Logo */}
          <Logo />

          {/* Project Title (Visual divider + Text) */}
          <div className="hidden sm:flex items-center gap-2">
            <div className="h-4 w-[1px] bg-border" aria-hidden="true" />
            <span className="text-xs font-semibold text-muted-foreground uppercase tracking-widest">
              Dev Showcase
            </span>
          </div>
        </div>

        {/* Right Side: GitHub + Theme Toggle */}
        <div className="flex items-center gap-2">
          {/* GitHub Link */}
          <Button
            variant="ghost"
            size="icon"
            className="h-9 w-9 text-muted-foreground hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring"
            aria-label="GitHub Profile"
            nativeButton={false}
            render={
              <a
                href="https://github.com/AjaySusanth"
                target="_blank"
                rel="noopener noreferrer"
              />
            }
          >
            <GithubIcon className="h-5 w-5" />
          </Button>

          {/* Theme Toggle */}
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setTheme(resolvedTheme === "dark" ? "light" : "dark")}
            className="h-9 w-9 text-muted-foreground hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring"
            aria-label="Toggle theme"
          >
            {mounted ? (
              resolvedTheme === "dark" ? (
                <Sun className="h-5 w-5" />
              ) : (
                <Moon className="h-5 w-5" />
              )
            ) : (
              <div className="h-5 w-5 rounded-full border border-dashed border-muted-foreground animate-spin" />
            )}
          </Button>
        </div>

      </div>
    </header>
  );
}
