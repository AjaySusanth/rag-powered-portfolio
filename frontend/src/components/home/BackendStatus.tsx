import * as React from "react";
import { cn } from "@/lib/utils";
import { CheckCircle2, AlertTriangle, AlertCircle, RefreshCw } from "lucide-react";

export type StatusVariant = "Ready" | "Offline" | "Connecting" | "Error";

interface BackendStatusProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: StatusVariant;
}

export function BackendStatus({ variant = "Ready", className, ...props }: BackendStatusProps) {
  const configs = {
    Ready: {
      color: "text-emerald-500 bg-emerald-500/10 border-emerald-500/20 dark:text-emerald-400 dark:bg-emerald-400/10 dark:border-emerald-400/20",
      icon: CheckCircle2,
      label: "AI Assistant Ready",
    },
    Offline: {
      color: "text-amber-500 bg-amber-500/10 border-amber-500/20 dark:text-amber-400 dark:bg-amber-400/10 dark:border-amber-400/20",
      icon: AlertTriangle,
      label: "AI Assistant Offline",
    },
    Connecting: {
      color: "text-blue-500 bg-blue-500/10 border-blue-500/20 dark:text-blue-400 dark:bg-blue-400/10 dark:border-blue-400/20",
      icon: RefreshCw,
      label: "Connecting to AI...",
      animateIcon: "animate-spin",
    },
    Error: {
      color: "text-rose-500 bg-rose-500/10 border-rose-500/20 dark:text-rose-400 dark:bg-rose-400/10 dark:border-rose-400/20",
      icon: AlertCircle,
      label: "AI Connection Error",
    },
  };

  const config = configs[variant];
  const Icon = config.icon;

  return (
    <div
      className={cn(
        "inline-flex items-center gap-2 px-3 py-1.5 rounded-full border text-xs font-semibold transition-all duration-300",
        config.color,
        className
      )}
      aria-label={`System status: ${config.label}`}
      {...props}
    >
      <Icon className={cn("h-3.5 w-3.5 shrink-0", "animateIcon" in config && config.animateIcon)} />
      <span>{config.label}</span>
    </div>
  );
}
