import * as React from "react";
import { ChatMessage } from "@/types/chat";
import { Message } from "./Message";

interface ConversationProps {
  messages: ChatMessage[];
  scrollRef: React.RefObject<HTMLDivElement | null>;
  onRetry?: () => void;
}

export function Conversation({ messages, scrollRef, onRetry }: ConversationProps) {
  return (
    <div
      ref={scrollRef}
      className="flex-grow overflow-y-auto space-y-4 pr-1 scrollbar-none max-h-[380px] min-h-[220px]"
    >
      {messages.map((message) => (
        <Message key={message.id} message={message} onRetry={onRetry} />
      ))}
    </div>
  );
}
