import * as React from "react";

export function ThinkingIndicator() {
  return (
    <div
      className="flex items-center gap-1.5 py-1 px-0.5 text-xs text-muted-foreground font-medium select-none"
      role="status"
      aria-label="AI is thinking"
    >
      <span>Searching portfolio</span>
      <div className="flex gap-1 items-center">
        <span className="h-1 w-1 rounded-full bg-muted-foreground/80 animate-bounce [animation-delay:-0.3s]"></span>
        <span className="h-1 w-1 rounded-full bg-muted-foreground/80 animate-bounce [animation-delay:-0.15s]"></span>
        <span className="h-1 w-1 rounded-full bg-muted-foreground/80 animate-bounce"></span>
      </div>
    </div>
  );
}
