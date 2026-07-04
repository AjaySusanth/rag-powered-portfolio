"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { Sheet, SheetContent, SheetTitle } from "@/components/ui/sheet";
import { Home, Briefcase, Network, FileText, Layers, Mail } from "lucide-react";
import { Logo } from "@/components/common/Logo";

export const NAV_ITEMS = [
  { label: "AI Chat", href: "/", icon: Home },
  { label: "Projects", href: "/projects", icon: Briefcase },
  { label: "Architecture", href: "/architecture", icon: Network },
  { label: "Resume", href: "/resume", icon: FileText },
  { label: "Tech Stack", href: "/stack", icon: Layers },
  { label: "Hire Me", href: "/hire", icon: Mail },
];

interface SidebarProps extends React.HTMLAttributes<HTMLDivElement> {
  isMobile?: boolean;
  isOpen?: boolean;
  onClose?: () => void;
}

export function Sidebar({ isMobile, isOpen, onClose, className, ...props }: SidebarProps) {
  const pathname = usePathname();

  const navContent = (
    <nav className="flex flex-col space-y-1.5 p-4 md:p-6" aria-label="Main Navigation">
      {NAV_ITEMS.map((item) => {
        const Icon = item.icon;
        const isActive = pathname === item.href;

        return (
          <Link
            key={item.href}
            href={item.href}
            onClick={onClose}
            aria-current={isActive ? "page" : undefined}
            className={cn(
              "flex items-center gap-3.5 px-4 py-3 rounded-lg text-sm font-medium transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
              isActive
                ? "bg-primary/10 text-primary dark:bg-primary/20 dark:text-primary-foreground shadow-[inset_3px_0_0_0_currentColor]"
                : "text-muted-foreground hover:text-foreground hover:bg-muted/80"
            )}
          >
            <Icon className={cn("h-4.5 w-4.5", isActive ? "text-primary dark:text-primary-foreground" : "text-muted-foreground")} />
            {item.label}
          </Link>
        );
      })}
    </nav>
  );

  if (isMobile) {
    return (
      <Sheet open={isOpen} onOpenChange={(open) => !open && onClose?.()}>
        <SheetContent side="left" className="w-[280px] p-0 bg-background border-r border-border">
          <div className="flex flex-col h-full">
            <div className="flex items-center justify-between border-b border-border px-5 py-4 min-h-[64px]">
              <Logo />
            </div>
            <SheetTitle className="sr-only">Navigation Menu</SheetTitle>
            <div className="flex-1 overflow-y-auto">{navContent}</div>
          </div>
        </SheetContent>
      </Sheet>
    );
  }

  return (
    <aside className={cn("flex flex-col h-full", className)} {...props}>
      <div className="flex-1 overflow-y-auto">{navContent}</div>
    </aside>
  );
}
