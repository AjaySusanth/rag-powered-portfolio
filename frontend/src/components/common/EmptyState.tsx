import * as React from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { ArrowLeft, Hourglass } from "lucide-react";
import { cn } from "@/lib/utils";

interface EmptyStateProps extends React.HTMLAttributes<HTMLDivElement> {
  title: string;
  description: string;
  icon?: React.ReactNode;
  actionText?: string;
  actionHref?: string;
}

export function EmptyState({
  title,
  description,
  icon = <Hourglass className="h-10 w-10 text-muted-foreground/80 animate-pulse" />,
  actionText = "Go back home",
  actionHref = "/",
  className,
  ...props
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        "flex min-h-[400px] flex-col items-center justify-center rounded-xl border border-dashed border-border p-8 text-center bg-card/30 backdrop-blur-sm",
        className
      )}
      {...props}
    >
      <div className="flex h-16 w-16 items-center justify-center rounded-full bg-muted/60 mb-5">
        {icon}
      </div>
      <h3 className="text-xl font-bold text-foreground mb-2">{title}</h3>
      <p className="text-sm text-muted-foreground max-w-sm mb-6 leading-relaxed">
        {description}
      </p>
      {actionText && actionHref && (
        <Button variant="outline" size="sm" className="gap-2 hover:bg-muted/80" render={<Link href={actionHref} />}>
          <ArrowLeft className="h-4 w-4" />
          {actionText}
        </Button>
      )}
    </div>
  );
}
