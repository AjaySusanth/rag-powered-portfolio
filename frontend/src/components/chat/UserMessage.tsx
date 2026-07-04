import * as React from "react";
import { ChatMessage } from "@/types/chat";

interface UserMessageProps {
  message: ChatMessage;
}

export function UserMessage({ message }: UserMessageProps) {
  return (
    <div className="flex justify-end w-full">
      <div className="max-w-[85%] sm:max-w-[70%] rounded-2xl px-4 py-2.5 bg-primary text-primary-foreground font-medium text-sm shadow-sm whitespace-pre-wrap break-words">
        {message.content}
      </div>
    </div>
  );
}
