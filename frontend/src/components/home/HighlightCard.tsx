"use client";

import * as React from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

interface HighlightCardProps {
  icon: string;
  title: string;
  description: string;
  badges?: string[];
  index?: number;
  className?: string;
}

export function HighlightCard({
  icon,
  title,
  description,
  badges,
  index = 0,
  className,
}: HighlightCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, delay: index * 0.08, ease: "easeOut" }}
      className={cn(
        "flex flex-col p-5 rounded-xl border border-border bg-card text-card-foreground shadow-sm hover:shadow-md transition-all duration-200",
        className
      )}
    >
      <div className="flex items-center gap-2.5 mb-3">
        <span className="text-xl shrink-0 select-none" aria-hidden="true">
          {icon}
        </span>
        <h3 className="font-bold text-base text-foreground tracking-tight">{title}</h3>
      </div>
      <p className="text-sm text-muted-foreground leading-relaxed flex-grow">
        {description}
      </p>
      {badges && badges.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mt-4 pt-4 border-t border-border/60">
          {badges.map((badge) => (
            <span
              key={badge}
              className="inline-flex items-center px-2 py-0.5 rounded bg-muted text-[10px] font-semibold text-foreground border border-border/80"
            >
              {badge}
            </span>
          ))}
        </div>
      )}
    </motion.div>
  );
}
