"use client";

import * as React from "react";
import { Copy } from "lucide-react";
import { toast } from "sonner";
import { PrismLight as SyntaxHighlighter } from "react-syntax-highlighter";

// Import core languages to keep client bundle size small
import tsx from "react-syntax-highlighter/dist/esm/languages/prism/tsx";
import typescript from "react-syntax-highlighter/dist/esm/languages/prism/typescript";
import javascript from "react-syntax-highlighter/dist/esm/languages/prism/javascript";
import python from "react-syntax-highlighter/dist/esm/languages/prism/python";
import yaml from "react-syntax-highlighter/dist/esm/languages/prism/yaml";
import json from "react-syntax-highlighter/dist/esm/languages/prism/json";
import bash from "react-syntax-highlighter/dist/esm/languages/prism/bash";

// Import theme
import { atomDark } from "react-syntax-highlighter/dist/esm/styles/prism";

// Register languages
SyntaxHighlighter.registerLanguage("tsx", tsx);
SyntaxHighlighter.registerLanguage("typescript", typescript);
SyntaxHighlighter.registerLanguage("javascript", javascript);
SyntaxHighlighter.registerLanguage("python", python);
SyntaxHighlighter.registerLanguage("yaml", yaml);
SyntaxHighlighter.registerLanguage("json", json);
SyntaxHighlighter.registerLanguage("bash", bash);
SyntaxHighlighter.registerLanguage("sh", bash);

interface CodeBlockProps {
  language: string;
  value: string;
}

export function CodeBlock({ language, value }: CodeBlockProps) {
  const handleCopy = () => {
    navigator.clipboard.writeText(value);
    toast.success("Code copied", {
      description: "Copied code snippet to clipboard.",
      duration: 1500,
    });
  };

  // Extract real language name
  const displayLang = language || "text";

  return (
    <div className="relative border border-border bg-card rounded-xl overflow-hidden my-4 shadow-sm w-full">
      {/* Header bar */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-border/40 bg-muted/50 text-[10px] sm:text-xs text-muted-foreground select-none">
        <span className="font-mono uppercase font-bold tracking-wider">{displayLang}</span>
        <button
          onClick={handleCopy}
          className="flex items-center gap-1.5 hover:text-foreground transition-colors cursor-pointer"
          aria-label="Copy code snippet"
        >
          <Copy className="h-3.5 w-3.5" />
          <span>Copy Code</span>
        </button>
      </div>

      {/* Code viewport */}
      <div className="text-xs sm:text-sm overflow-x-auto w-full leading-normal">
        <SyntaxHighlighter
          language={displayLang}
          style={atomDark}
          customStyle={{
            margin: 0,
            background: "transparent",
            padding: "1rem",
            fontSize: "12px",
            fontFamily: "var(--font-geist-mono), ui-monospace, monospace",
            lineHeight: "1.6",
          }}
          codeTagProps={{
            style: {
              fontFamily: "inherit",
            },
          }}
        >
          {value}
        </SyntaxHighlighter>
      </div>
    </div>
  );
}
