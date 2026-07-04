import * as React from "react";
import { cn } from "@/lib/utils";
import { PROMPT_SUGGESTIONS } from "@/constants/home";

interface PromptSuggestionsProps extends React.HTMLAttributes<HTMLDivElement> {
  selectedPromptId?: string | null;
  onSelectPrompt?: (promptText: string, id: string) => void;
  disabled?: boolean;
}

export function PromptSuggestions({
  selectedPromptId,
  onSelectPrompt,
  disabled = false,
  className,
  ...props
}: PromptSuggestionsProps) {
  return (
    <div
      className={cn(
        "w-full flex gap-2 overflow-x-auto scroll-smooth snap-x snap-mandatory pb-3 -mb-3 scrollbar-none",
        "md:overflow-x-visible md:flex-wrap md:justify-center md:pb-0 md:mb-0",
        className
      )}
      {...props}
    >
      {PROMPT_SUGGESTIONS.map((prompt) => {
        const isSelected = selectedPromptId === prompt.id;
        return (
          <button
            key={prompt.id}
            type="button"
            disabled={disabled}
            onClick={() => !disabled && onSelectPrompt?.(prompt.text, prompt.id)}
            aria-selected={isSelected}
            className={cn(
              "snap-start shrink-0 inline-flex items-center justify-center px-4 py-2.5 text-xs font-semibold rounded-full border transition-all duration-200 cursor-pointer select-none outline-none",
              "focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1 focus-visible:ring-offset-background",
              // Selected state
              isSelected && !disabled && "bg-primary text-primary-foreground border-primary shadow-[0_2px_8px_rgba(59,107,229,0.35)] dark:shadow-[0_2px_8px_rgba(92,138,255,0.35)]",
              // Default state
              !isSelected && !disabled && "bg-card text-muted-foreground border-border hover:bg-muted hover:text-foreground hover:border-muted-foreground/30",
              // Disabled state
              disabled && "opacity-40 cursor-not-allowed border-border text-muted-foreground/50 bg-muted/20"
            )}
          >
            {prompt.text}
          </button>
        );
      })}
    </div>
  );
}
