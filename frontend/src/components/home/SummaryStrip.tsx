import * as React from "react";
import { HIGHLIGHT_CARDS, ROLE_BADGES } from "@/constants/home";
import { HighlightCard } from "./HighlightCard";

export function SummaryStrip() {
  return (
    <div className="space-y-6">
      
      {/* Identity Badge Strip */}
      <div className="flex flex-wrap items-center gap-2">
        {ROLE_BADGES.map((role) => (
          <span
            key={role}
            className="inline-flex items-center px-3 py-1 rounded-full bg-primary/5 text-primary border border-primary/15 dark:bg-primary/10 dark:text-primary-foreground text-xs font-bold"
          >
            {role}
          </span>
        ))}
      </div>

      {/* Highlight Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {HIGHLIGHT_CARDS.map((card, index) => (
          <HighlightCard
            key={card.id}
            icon={card.icon}
            title={card.title}
            description={card.description}
            badges={"badges" in card ? card.badges : undefined}
            index={index}
          />
        ))}
      </div>

    </div>
  );
}
