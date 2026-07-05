"use client";

import * as React from "react";
import { useReducedMotion } from "framer-motion";
import { cn } from "@/lib/utils";

export function TypingCursor() {
  const shouldReduceMotion = useReducedMotion();

  return (
    <span
      className={cn(
        "inline-block h-3.5 w-1.5 ml-1 bg-primary rounded-sm align-middle",
        !shouldReduceMotion && "animate-[pulse_0.8s_infinite]"
      )}
      style={{ animationDuration: "0.8s" }}
      aria-hidden="true"
    />
  );
}
