"use client";

import * as React from "react";
import { AlertCircle, RefreshCw, WifiOff, FileSearch, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useReducedMotion } from "framer-motion";

interface StatusStateProps {
  type: "loading" | "empty" | "offline" | "error";
  title?: string;
  description?: string;
  onRetry?: () => void;
  retryText?: string;
  className?: string;
}

export function StatusState({
  type,
  title,
  description,
  onRetry,
  retryText = "Retry Connection",
  className,
}: StatusStateProps) {
  const shouldReduceMotion = useReducedMotion();
  
  let defaultIcon: React.ReactNode = null;
  let defaultTitle = "";
  let defaultDescription = "";

  switch (type) {
    case "loading":
      defaultIcon = <Loader2 className={cn("h-8 w-8 text-primary", !shouldReduceMotion && "animate-spin")} />;
      defaultTitle = "Loading Data";
      defaultDescription = "Retrieving the requested details from the server...";
      break;
    case "offline":
      defaultIcon = <WifiOff className="h-8 w-8 text-amber-500" />;
      defaultTitle = "Offline Mode";
      defaultDescription = "We could not establish a connection. Please verify your internet connection and try again.";
      break;
    case "empty":
      defaultIcon = <FileSearch className="h-8 w-8 text-muted-foreground/80" />;
      defaultTitle = "No Results Found";
      defaultDescription = "There is no content available for this section at the moment.";
      break;
    case "error":
      defaultIcon = <AlertCircle className="h-8 w-8 text-rose-500" />;
      defaultTitle = "API Connection Failure";
      defaultDescription = "A connection error occurred while reaching the portfolio API. Please check if the service is online.";
      break;
  }

  const activeTitle = title || defaultTitle;
  const activeDescription = description || defaultDescription;

  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center rounded-2xl border border-border bg-card/30 p-8 text-center backdrop-blur-sm transition-all duration-300 min-h-[320px] max-w-lg mx-auto w-full",
        type === "error" && "border-rose-500/15 bg-rose-500/5",
        type === "offline" && "border-amber-500/15 bg-amber-500/5",
        className
      )}
    >
      <div className={cn(
        "flex h-14 w-14 items-center justify-center rounded-full bg-muted/60 mb-5",
        type === "loading" && "bg-primary/5",
        type === "error" && "bg-rose-500/10",
        type === "offline" && "bg-amber-500/10"
      )}>
        {defaultIcon}
      </div>
      <h3 className="text-sm font-bold text-foreground mb-1.5">{activeTitle}</h3>
      <p className="text-xs text-muted-foreground max-w-xs mb-6 leading-relaxed">
        {activeDescription}
      </p>
      
      {onRetry && (
        <Button
          onClick={onRetry}
          variant="outline"
          size="sm"
          className="gap-1.5 font-bold cursor-pointer text-xs border-border/80 hover:bg-muted/80"
        >
          <RefreshCw className={cn("h-3.5 w-3.5", type === "loading" && !shouldReduceMotion && "animate-spin")} />
          {retryText}
        </Button>
      )}
    </div>
  );
}
