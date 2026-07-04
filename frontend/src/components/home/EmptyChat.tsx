"use client";

import * as React from "react";
import { useState } from "react";
import { Sparkles } from "lucide-react";
import { EMPTY_CHAT_CONTENT } from "@/constants/home";
import { PromptSuggestions } from "./PromptSuggestions";

export function EmptyChat() {
  const [selectedPromptId, setSelectedPromptId] = useState<string | null>(null);

  const handleSelectPrompt = (promptText: string, id: string) => {
    setSelectedPromptId(id);
    // In future phases: populate chat input area state
  };

  return (
    <div
      id="chat"
      className="border border-border bg-card/20 rounded-2xl p-6 md:p-8 flex flex-col justify-between min-h-[440px] backdrop-blur-sm scroll-mt-20"
    >
      
      {/* Top Welcome / Info Row */}
      <div className="flex flex-col items-center text-center max-w-2xl mx-auto my-auto space-y-4 py-4">
        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary/10 text-primary border border-primary/15 animate-pulse">
          <Sparkles className="h-5.5 w-5.5" />
        </div>
        <h2 className="text-xl sm:text-2xl font-bold text-foreground">
          {EMPTY_CHAT_CONTENT.welcomeTitle}
        </h2>
        <p className="text-sm text-muted-foreground leading-relaxed">
          {EMPTY_CHAT_CONTENT.welcomeDescription}
        </p>
      </div>

      {/* Suggested prompts container */}
      <div className="w-full mt-6 mb-6">
        <PromptSuggestions
          selectedPromptId={selectedPromptId}
          onSelectPrompt={handleSelectPrompt}
        />
      </div>

      {/* Reserved area for input & future streaming messages */}
      <div className="border-t border-border/80 pt-4 flex flex-col space-y-3">
        <div className="w-full h-11 bg-muted/40 rounded-lg border border-border/80 flex items-center px-4 text-xs sm:text-sm text-muted-foreground/40 select-none cursor-not-allowed">
          Ask the assistant a question (chat interface coming soon)...
        </div>
        <div className="flex justify-between items-center text-[10px] text-muted-foreground/60 px-0.5">
          <span>Retrieval-Augmented Generation</span>
          <span>Powered by Gemini 2.0 & pgvector</span>
        </div>
      </div>

    </div>
  );
}
