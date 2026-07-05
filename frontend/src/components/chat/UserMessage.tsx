"use client";

import * as React from "react";
import { ChatMessage } from "@/types/chat";
import { User } from "lucide-react";
import { motion, useReducedMotion } from "framer-motion";

interface UserMessageProps {
  message: ChatMessage;
}

export function UserMessage({ message }: UserMessageProps) {
  const shouldReduceMotion = useReducedMotion();

  return (
    <motion.div
      initial={shouldReduceMotion ? { opacity: 1 } : { opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2, ease: "easeOut" }}
      className="flex justify-end items-start gap-3 w-full"
    >
      {/* Message Bubble */}
      <div className="max-w-[85%] sm:max-w-[70%] rounded-2xl px-4 py-2.5 bg-primary text-primary-foreground font-medium text-sm shadow-sm whitespace-pre-wrap break-words">
        {message.content}
      </div>

      {/* User Avatar */}
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-border/80 bg-muted/60 text-muted-foreground shadow-sm select-none">
        <User className="h-4 w-4" />
      </div>
    </motion.div>
  );
}
