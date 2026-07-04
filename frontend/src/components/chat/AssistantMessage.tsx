import * as React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { ChatMessage } from "@/types/chat";
import { ThinkingIndicator } from "./ThinkingIndicator";
import { TypingCursor } from "./TypingCursor";
import { CitationList } from "./CitationList";
import { Button } from "@/components/ui/button";
import { AlertCircle, RotateCcw } from "lucide-react";

interface AssistantMessageProps {
  message: ChatMessage;
  onRetry?: () => void;
}

export function AssistantMessage({ message, onRetry }: AssistantMessageProps) {
  const isStreaming = message.status === "streaming";
  const isError = message.status === "error";
  const isEmpty = !message.content;

  return (
    <div className="flex justify-start w-full">
      <div className="max-w-[95%] md:max-w-[85%] rounded-2xl border border-border bg-card p-4 sm:p-5 text-sm text-foreground shadow-sm space-y-3">
        
        {/* 1. Loading Phase */}
        {isStreaming && isEmpty && <ThinkingIndicator />}

        {/* 2. Streaming / Complete Output Phase */}
        {(!isEmpty || isError) && (
          <div className="prose prose-sm dark:prose-invert max-w-none break-words leading-relaxed text-foreground/90 space-y-2">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                strong: ({ children }) => <strong className="font-bold text-foreground">{children}</strong>,
                a: ({ href, children }) => (
                  <a
                    href={href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-primary hover:underline font-semibold"
                  >
                    {children}
                  </a>
                ),
                ul: ({ children }) => <ul className="list-disc pl-5 mb-2 space-y-1">{children}</ul>,
                ol: ({ children }) => <ol className="list-decimal pl-5 mb-2 space-y-1">{children}</ol>,
                li: ({ children }) => <li>{children}</li>,
                h1: ({ children }) => <h1 className="text-base sm:text-lg font-bold mt-4 mb-2 first:mt-0 text-foreground">{children}</h1>,
                h2: ({ children }) => <h2 className="text-sm sm:text-base font-bold mt-3 mb-2 first:mt-0 text-foreground">{children}</h2>,
                h3: ({ children }) => <h3 className="text-xs sm:text-sm font-bold mt-2 mb-1 first:mt-0 text-foreground">{children}</h3>,
                code: ({ className, children, ...props }) => {
                  const isInline = !className;
                  if (isInline) {
                    return (
                      <code className="px-1.5 py-0.5 rounded bg-muted font-mono text-xs text-foreground border border-border/60">
                        {children}
                      </code>
                    );
                  }
                  return (
                    <pre className="p-3 my-2 rounded bg-muted/60 border border-border/80 overflow-x-auto font-mono text-xs text-foreground/90 leading-normal">
                      <code>{children}</code>
                    </pre>
                  );
                },
              }}
            >
              {message.content}
            </ReactMarkdown>

            {/* Blink cursor during streaming text load */}
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
    </div>
  );
}
