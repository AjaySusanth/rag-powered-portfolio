import * as React from "react";
import { useRef, useEffect } from "react";
import { SendHorizontal } from "lucide-react";
import { Button } from "@/components/ui/button";
import { PromptSuggestions } from "@/components/home/PromptSuggestions";
import { cn } from "@/lib/utils";

interface ChatInputProps {
  inputValue: string;
  onInputChange: (val: string) => void;
  onSubmit: (content: string) => void;
  disabled?: boolean;
  selectedPromptId: string | null;
  onSelectPrompt: (promptText: string, id: string) => void;
}

export function ChatInput({
  inputValue,
  onInputChange,
  onSubmit,
  disabled = false,
  selectedPromptId,
  onSelectPrompt,
}: ChatInputProps) {
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (!disabled && inputValue.trim()) {
        onSubmit(inputValue);
      }
    }
  };

  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!disabled && inputValue.trim()) {
      onSubmit(inputValue);
    }
  };

  // Adjust height of the textarea automatically
  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
  }, [inputValue]);

  return (
    <div className="w-full space-y-4">
      
      {/* Suggested Prompt Chips */}
      <PromptSuggestions
        selectedPromptId={selectedPromptId}
        onSelectPrompt={onSelectPrompt}
        disabled={disabled}
      />

      {/* Styled Input Field Form */}
      <form
        onSubmit={handleFormSubmit}
        className="relative flex items-end gap-2 border border-border bg-card/45 rounded-xl p-2 focus-within:border-primary/50 focus-within:ring-1 focus-within:ring-primary/20 transition-all duration-200"
      >
        <textarea
          ref={textareaRef}
          rows={1}
          value={inputValue}
          disabled={disabled}
          onChange={(e) => onInputChange(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={disabled ? "AI Assistant is thinking..." : "Ask me anything about my portfolio..."}
          className={cn(
            "flex-grow bg-transparent resize-none outline-none border-none py-1.5 px-2.5 text-sm max-h-[160px] scrollbar-none",
            disabled && "cursor-not-allowed opacity-50"
          )}
        />
        <Button
          type="submit"
          size="icon"
          disabled={disabled || !inputValue.trim()}
          className="h-9 w-9 rounded-lg shrink-0 cursor-pointer transition-all duration-200"
        >
          <SendHorizontal className="h-4 w-4" />
          <span className="sr-only">Send Message</span>
        </Button>
      </form>

    </div>
  );
}
