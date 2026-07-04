import * as React from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { AlertCircle, FileText, Layers, Mail, FolderGit } from "lucide-react";
import { cn } from "@/lib/utils";

interface OfflineStateProps extends React.HTMLAttributes<HTMLDivElement> {}

export function OfflineState({ className, ...props }: OfflineStateProps) {
  const offlineLinks = [
    { label: "Projects", href: "/projects", icon: FolderGit },
    { label: "Resume", href: "/resume", icon: FileText },
    { label: "Tech Stack", href: "/stack", icon: Layers },
    { label: "Hire Me", href: "/hire", icon: Mail },
  ];

  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center text-center p-6 border border-warning/20 bg-warning/5 rounded-xl max-w-lg mx-auto backdrop-blur-sm",
        className
      )}
      {...props}
    >
      <div className="flex h-12 w-12 items-center justify-center rounded-full bg-warning/10 text-warning mb-4">
        <AlertCircle className="h-6 w-6" />
      </div>
      <h3 className="text-lg font-bold text-foreground mb-2">AI Assistant Offline</h3>
      <p className="text-sm text-muted-foreground mb-6 leading-relaxed max-w-sm">
        AI assistant is temporarily unavailable. You can still explore my portfolio.
      </p>
      <div className="flex flex-wrap justify-center gap-2">
        {offlineLinks.map((link) => {
          const Icon = link.icon;
          return (
            <Button
              key={link.href}
              variant="outline"
              size="sm"
              className="gap-2 hover:bg-muted"
              render={<Link href={link.href} />}
              nativeButton={false}
            >
              <Icon className="h-3.5 w-3.5 text-muted-foreground" />
              {link.label}
            </Button>
          );
        })}
      </div>
    </div>
  );
}
