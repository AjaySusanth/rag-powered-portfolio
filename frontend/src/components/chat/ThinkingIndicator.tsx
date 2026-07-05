"use client";

import * as React from "react";
import { useReducedMotion } from "framer-motion";
import { cn } from "@/lib/utils";

export function ThinkingIndicator() {
  const shouldReduceMotion = useReducedMotion();

  return (
    <div
      className={cn(
        "flex items-center gap-2 py-1.5 px-1 text-xs text-muted-foreground font-semibold select-none",
        !shouldReduceMotion && "animate-pulse duration-1000"
      )}
      role="status"
      aria-label="AI is thinking"
    >
      <span>Searching portfolio database</span>
      <div className="flex gap-1 items-center">
        <span className="h-1 w-1 rounded-full bg-muted-foreground/60"></span>
        <span className="h-1 w-1 rounded-full bg-muted-foreground/60"></span>
        <span className="h-1 w-1 rounded-full bg-muted-foreground/60"></span>
      </div>
    </div>
  );
}
