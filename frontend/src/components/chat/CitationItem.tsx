import * as React from "react";
import { Citation } from "@/types/chat";

interface CitationItemProps {
  citation: Citation;
  index: number;
}

export function CitationItem({ citation, index }: CitationItemProps) {
  const filename = citation.file.split("/").pop() || citation.file;

  return (
    <div className="flex flex-col p-2 bg-muted/40 border border-border/50 rounded-lg text-xs">
      <div className="flex items-center justify-between gap-2 mb-1">
        <span className="font-bold text-foreground truncate max-w-[160px]" title={citation.file}>
          {filename}
        </span>
        <span className="px-1.5 py-0.5 text-[9px] font-bold rounded bg-primary/10 text-primary border border-primary/25">
          [{index}]
        </span>
      </div>
      <div className="text-[10px] text-muted-foreground space-y-0.5">
        <div>
          <span className="font-semibold text-foreground/80">Project:</span> {citation.project}
        </div>
        <div>
          <span className="font-semibold text-foreground/80">Layer:</span> Layer {citation.layer}
        </div>
      </div>
    </div>
  );
}
