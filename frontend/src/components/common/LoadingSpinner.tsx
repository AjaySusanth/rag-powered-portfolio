import * as React from "react";
import { cn } from "@/lib/utils";

interface LoadingSpinnerProps extends React.HTMLAttributes<HTMLDivElement> {
  size?: "sm" | "md" | "lg";
}

export function LoadingSpinner({ size = "md", className, ...props }: LoadingSpinnerProps) {
  const sizeClasses = {
    sm: "h-4 w-4 border-2",
    md: "h-8 w-8 border-[3px]",
    lg: "h-12 w-12 border-4",
  };

  return (
    <div className={cn("flex items-center justify-center p-4", className)} {...props}>
      <div
        className={cn(
          "animate-spin rounded-full border-solid border-t-primary border-r-transparent border-b-primary/20 border-l-primary/20",
          sizeClasses[size]
        )}
      />
    </div>
  );
}
