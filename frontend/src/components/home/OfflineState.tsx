import * as React from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { FileText, Layers, Mail, FolderGit } from "lucide-react";
import { cn } from "@/lib/utils";
import { StatusState } from "@/components/common/StatusState";

interface OfflineStateProps extends React.HTMLAttributes<HTMLDivElement> {}

export function OfflineState({ className, ...props }: OfflineStateProps) {
  const offlineLinks = [
    { label: "Projects", href: "/projects", icon: FolderGit },
    { label: "Resume", href: "/resume", icon: FileText },
    { label: "Tech Stack", href: "/stack", icon: Layers },
    { label: "Hire Me", href: "/hire", icon: Mail },
  ];

  return (
    <div className={cn("space-y-5 w-full max-w-lg mx-auto", className)} {...props}>
      <StatusState
        type="offline"
        title="AI Assistant Offline"
        description="The AI Portfolio Assistant is temporarily unavailable. You can still explore static portfolio sections using the links below."
      />
      <div className="flex flex-wrap justify-center gap-2.5">
        {offlineLinks.map((link) => {
          const Icon = link.icon;
          return (
            <Button
              key={link.href}
              variant="outline"
              size="sm"
              className="gap-1.5 hover:bg-muted text-xs font-semibold cursor-pointer"
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
