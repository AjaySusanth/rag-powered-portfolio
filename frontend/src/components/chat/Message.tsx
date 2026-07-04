import * as React from "react";
import { ChatMessage } from "@/types/chat";
import { UserMessage } from "./UserMessage";
import { AssistantMessage } from "./AssistantMessage";

interface MessageProps {
  message: ChatMessage;
  onRetry?: () => void;
}

export function Message({ message, onRetry }: MessageProps) {
  if (message.role === "user") {
    return <UserMessage message={message} />;
  }
  return <AssistantMessage message={message} onRetry={onRetry} />;
}
