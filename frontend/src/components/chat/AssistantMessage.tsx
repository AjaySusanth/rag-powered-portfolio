"use client";

import * as React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { ChatMessage } from "@/types/chat";
import { ThinkingIndicator } from "./ThinkingIndicator";
import { TypingCursor } from "./TypingCursor";
import { CitationList } from "./CitationList";
import { CodeBlock } from "./CodeBlock";
import { Button } from "@/components/ui/button";
import { AlertCircle, RotateCcw, Bot } from "lucide-react";
import { motion, useReducedMotion } from "framer-motion";

interface AssistantMessageProps {
  message: ChatMessage;
  onRetry?: () => void;
}

export function AssistantMessage({ message, onRetry }: AssistantMessageProps) {
  const isStreaming = message.status === "streaming";
  const isError = message.status === "error";
  const isEmpty = !message.content;
  const shouldReduceMotion = useReducedMotion();

  return (
    <motion.div
      initial={shouldReduceMotion ? { opacity: 1 } : { opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25, ease: "easeOut" }}
      className="flex justify-start items-start gap-3 w-full"
    >
      {/* Assistant Avatar */}
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-primary/30 bg-primary/10 text-primary shadow-sm select-none">
        <Bot className="h-4 w-4" />
      </div>

      {/* Message Bubble Container */}
      <div className="flex-1 max-w-[92%] md:max-w-[85%] rounded-2xl border border-border bg-card p-4 sm:p-5 text-sm text-foreground shadow-sm space-y-3">
        {/* 1. Loading Phase */}
        {isStreaming && isEmpty && <ThinkingIndicator />}

        {/* 2. Streaming / Complete Output Phase */}
        {(!isEmpty || isError) && (
          <div className="prose prose-sm dark:prose-invert max-w-none break-words leading-relaxed text-foreground/90 space-y-2.5">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                p: ({ children }) => <p className="mb-3 last:mb-0 leading-relaxed">{children}</p>,
                strong: ({ children }) => <strong className="font-bold text-foreground">{children}</strong>,
                a: ({ href, children }) => (
                  <a
                    href={href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-primary hover:underline font-semibold transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-primary rounded"
                  >
                    {children}
                  </a>
                ),
                ul: ({ children }) => <ul className="list-disc pl-5 mb-3 space-y-1.5">{children}</ul>,
                ol: ({ children }) => <ol className="list-decimal pl-5 mb-3 space-y-1.5">{children}</ol>,
                li: ({ children }) => <li className="leading-relaxed">{children}</li>,
                h1: ({ children }) => (
                  <h1 className="text-sm sm:text-base font-extrabold mt-5 mb-3 first:mt-0 text-foreground border-b border-border/40 pb-1">
                    {children}
                  </h1>
                ),
                h2: ({ children }) => (
                  <h2 className="text-xs sm:text-sm font-bold mt-4 mb-2 first:mt-0 text-foreground">
                    {children}
                  </h2>
                ),
                h3: ({ children }) => (
                  <h3 className="text-xs font-semibold mt-3 mb-1 first:mt-0 text-foreground/80">
                    {children}
                  </h3>
                ),
                blockquote: ({ children }) => (
                  <blockquote className="border-l-4 border-primary/60 bg-muted/20 pl-4 py-2 pr-2 my-2 rounded-r italic text-muted-foreground/90 text-xs">
                    {children}
                  </blockquote>
                ),
                table: ({ children }) => (
                  <div className="overflow-x-auto my-3 border border-border/60 rounded-xl">
                    <table className="min-w-full divide-y divide-border/60 text-xs">
                      {children}
                    </table>
                  </div>
                ),
                thead: ({ children }) => <thead className="bg-muted/40 font-bold">{children}</thead>,
                tbody: ({ children }) => <tbody className="divide-y divide-border/40">{children}</tbody>,
                tr: ({ children }) => <tr>{children}</tr>,
                th: ({ children }) => <th className="px-3 py-2 text-left font-bold text-foreground select-none">{children}</th>,
                td: ({ children }) => <td className="px-3 py-2 text-muted-foreground">{children}</td>,
                hr: () => <hr className="my-4 border-t border-border/60" />,
                img: ({ src, alt }) => (
                  <img
                    src={src}
                    alt={alt}
                    className="max-w-full h-auto rounded-lg border border-border/40 my-3"
                  />
                ),
                code: ({ className, children, ...props }) => {
                  const isInline = !className;
                  const match = /language-(\w+)/.exec(className || "");
                  const language = match ? match[1] : "";
                  const codeValue = String(children).replace(/\n$/, "");

                  if (isInline) {
                    return (
                      <code className="px-1.5 py-0.5 rounded bg-muted font-mono text-[11px] text-foreground border border-border/60">
                        {children}
                      </code>
                    );
                  }
                  return <CodeBlock language={language} value={codeValue} />;
                },
              }}
            >
              {message.content}
            </ReactMarkdown>

            {/* Natural cursor during streaming */}
            {isStreaming && <TypingCursor />}
          </div>
        )}

        {/* 3. Error Fallback state */}
        {isError && (
          <div className="flex flex-col gap-3 mt-2 p-3 rounded-lg border border-rose-500/20 bg-rose-500/5 text-rose-500 text-xs">
            <div className="flex items-center gap-2">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <span className="font-semibold">Assistant response failed</span>
            </div>
            <p className="text-muted-foreground/90">
              {message.content || "An error occurred while generating the response."}
            </p>
            {onRetry && (
              <Button
                variant="outline"
                size="sm"
                className="w-fit gap-1.5 border-rose-500/30 text-rose-500 hover:bg-rose-500/10 hover:text-rose-500 cursor-pointer self-start"
                onClick={onRetry}
              >
                <RotateCcw className="h-3.5 w-3.5" />
                Retry Question
              </Button>
            )}
          </div>
        )}

        {/* 4. Citations Display */}
        {message.status === "complete" && message.citations && (
          <CitationList citations={message.citations} />
        )}
      </div>
    </motion.div>
  );
}
