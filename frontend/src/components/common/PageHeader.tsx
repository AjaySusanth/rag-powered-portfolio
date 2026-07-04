import * as React from "react";
import { cn } from "@/lib/utils";

interface PageHeaderProps extends React.HTMLAttributes<HTMLDivElement> {
  title: string;
  description?: string;
}

export function PageHeader({ title, description, className, ...props }: PageHeaderProps) {
  return (
    <div className={cn("space-y-2.5 pb-6 border-b border-border/60 mb-6 md:mb-8", className)} {...props}>
      <h1 className="text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
        {title}
      </h1>
      {description && (
        <p className="text-base sm:text-lg text-muted-foreground max-w-[720px] leading-relaxed">
          {description}
        </p>
      )}
    </div>
  );
}
