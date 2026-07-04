import * as React from "react";

export function TypingCursor() {
  return (
    <span
      className="inline-block h-3.5 w-1.5 ml-0.5 bg-primary/80 rounded-sm animate-pulse align-middle"
      aria-hidden="true"
    />
  );
}
