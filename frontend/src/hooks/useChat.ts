"use client";

import { useState, useRef, useEffect } from "react";
import { ChatMessage, Citation } from "@/types/chat";
import { createChatStream } from "@/services/api/chat";

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<{ message: string; retryable: boolean } | null>(null);

  const sessionIdRef = useRef<string | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  // Initialize session ID once on mount
  useEffect(() => {
    if (typeof window !== "undefined") {
      let stored = sessionStorage.getItem("chat_session_id");
      if (!stored) {
        stored = crypto.randomUUID();
        sessionStorage.setItem("chat_session_id", stored);
      }
      sessionIdRef.current = stored;
    }

    // Cleanup abort controllers on unmount
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  const sendMessage = async (content: string) => {
    if (!content.trim()) return;

    // 1. Abort existing active stream before starting a new one
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    abortControllerRef.current = new AbortController();

    const userMessageId = crypto.randomUUID();
    const assistantMessageId = crypto.randomUUID();

    const userMessage: ChatMessage = {
      id: userMessageId,
      role: "user",
      content: content.trim(),
      status: "complete",
    };

    const assistantMessage: ChatMessage = {
      id: assistantMessageId,
      role: "assistant",
      content: "",
      status: "streaming",
    };

    setMessages((prev) => [...prev, userMessage, assistantMessage]);
    setIsStreaming(true);
    setError(null);

    const activeSignal = abortControllerRef.current.signal;

    await createChatStream(
      content.trim(),
      sessionIdRef.current || crypto.randomUUID(),
      {
        onToken: (token) => {
          if (activeSignal.aborted) return;
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMessageId
                ? { ...msg, content: msg.content + token }
                : msg
            )
          );
        },
        onCitations: (citations) => {
          if (activeSignal.aborted) return;
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMessageId ? { ...msg, citations } : msg
            )
          );
        },
        onDone: () => {
          if (activeSignal.aborted) return;
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMessageId ? { ...msg, status: "complete" } : msg
            )
          );
          setIsStreaming(false);
          abortControllerRef.current = null;
        },
        onError: (message, retryable) => {
          if (activeSignal.aborted) return;
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMessageId ? { ...msg, status: "error" } : msg
            )
          );
          setIsStreaming(false);
          setError({ message, retryable });
          abortControllerRef.current = null;
        },
      },
      activeSignal
    );
  };

  const retryLastMessage = () => {
    const lastUserMessage = [...messages].reverse().find((m) => m.role === "user");
    if (!lastUserMessage) return;

    // Clear failed messages starting from the user's last message, and retry
    setMessages((prev) => {
      const idx = prev.findIndex((m) => m.id === lastUserMessage.id);
      if (idx === -1) return prev;
      return prev.slice(0, idx);
    });

    sendMessage(lastUserMessage.content);
  };

  const clearError = () => {
    setError(null);
  };

  return {
    messages,
    isStreaming,
    error,
    sendMessage,
    retryLastMessage,
    clearError,
  };
}
