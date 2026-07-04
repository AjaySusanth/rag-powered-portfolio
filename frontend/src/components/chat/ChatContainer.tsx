"use client";

import * as React from "react";
import { useState, useEffect } from "react";
import { useChat } from "@/hooks/useChat";
import { useAutoScroll } from "@/hooks/useAutoScroll";
import { Conversation } from "./Conversation";
import { ChatInput } from "./ChatInput";
import { OfflineState } from "@/components/home/OfflineState";
import { Sparkles } from "lucide-react";
import { EMPTY_CHAT_CONTENT } from "@/constants/home";

export function ChatContainer() {
  const {
    messages,
    isStreaming,
    error,
    sendMessage,
    retryLastMessage,
  } = useChat();

  const { scrollRef } = useAutoScroll(messages);

  const [inputValue, setInputValue] = useState("");
  const [selectedPromptId, setSelectedPromptId] = useState<string | null>(null);
  const [backendOffline, setBackendOffline] = useState(false);

  // Check backend liveness on mount and check for ?q= query param
  useEffect(() => {
    const checkLiveness = async () => {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      try {
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 2000);
        
        // Probe health check endpoint; if connection fails, TypeError is thrown
        await fetch(`${apiUrl}/health`, {
          method: "GET",
          signal: controller.signal,
        }).catch((e) => {
          // If fetch fails with network-level error, mark backend offline
          if (e instanceof TypeError) {
            setBackendOffline(true);
          }
        });
        clearTimeout(timeout);
      } catch {
        setBackendOffline(true);
      }
    };
    checkLiveness();

    // Read ?q= query param
    if (typeof window !== "undefined") {
      const params = new URLSearchParams(window.location.search);
      const queryPrompt = params.get("q");
      if (queryPrompt) {
        setInputValue(queryPrompt);
        // Clear param from URL to avoid repopulate on refresh
        const newUrl = window.location.pathname;
        window.history.replaceState({}, document.title, newUrl);
      }
    }
  }, []);

  const handleSelectPrompt = (promptText: string, id: string) => {
    setSelectedPromptId(id);
    setInputValue(promptText);
  };

  const handleSendMessage = (content: string) => {
    sendMessage(content);
    setInputValue("");
    setSelectedPromptId(null);
  };

  const isBrowserOffline = typeof window !== "undefined" && !navigator.onLine;
  const isOffline = isBrowserOffline || backendOffline;

  if (isOffline) {
    return <OfflineState className="my-8" />;
  }

  const hasMessages = messages.length > 0;

  return (
    <div
      id="chat"
      className="border border-border bg-card/20 rounded-2xl p-6 md:p-8 flex flex-col min-h-[440px] max-h-[580px] justify-between backdrop-blur-sm scroll-mt-20 space-y-6"
    >
      
      {/* 1. Main Chat Area */}
      {!hasMessages ? (
        <div className="flex flex-col items-center text-center max-w-2xl mx-auto my-auto space-y-4 py-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary/10 text-primary border border-primary/15 animate-pulse">
            <Sparkles className="h-5.5 w-5.5 animate-pulse" />
          </div>
          <h2 className="text-xl sm:text-2xl font-bold text-foreground">
            {EMPTY_CHAT_CONTENT.welcomeTitle}
          </h2>
          <p className="text-sm text-muted-foreground leading-relaxed">
            {EMPTY_CHAT_CONTENT.welcomeDescription}
          </p>
        </div>
      ) : (
        <Conversation
          messages={messages}
          scrollRef={scrollRef}
          onRetry={retryLastMessage}
        />
      )}

      {/* 2. Chat Input and Subtitles */}
      <div className="border-t border-border/80 pt-4 flex flex-col space-y-3 shrink-0">
        <ChatInput
          inputValue={inputValue}
          onInputChange={setInputValue}
          onSubmit={handleSendMessage}
          disabled={isStreaming}
          selectedPromptId={selectedPromptId}
          onSelectPrompt={handleSelectPrompt}
        />
        <div className="flex justify-between items-center text-[10px] text-muted-foreground/60 px-0.5 select-none">
          <span>Retrieval-Augmented Generation</span>
          <span>Powered by Gemini 2.0 & pgvector</span>
        </div>
      </div>

    </div>
  );
}
