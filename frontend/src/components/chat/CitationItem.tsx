/**
 * WHY THIS DESIGN WAS CHOSEN:
 * The CitationItem component renders individual citation source cards.
 * To support narrow viewports, the filename utilizes `flex-1 min-w-0 truncate` rather than a hardcoded max-width,
 * ensuring it scales dynamically and truncates gracefully. The metadata badges are wrapped using `flex-wrap`
 * to avoid overflowing the card edges on extremely small screens (320px-360px).
 */
import * as React from "react";
import { Citation } from "@/types/chat";
import { FileText, FileCode, Settings, File } from "lucide-react";

interface CitationItemProps {
  citation: Citation;
  index: number;
}

function getDocumentIcon(filename: string) {
  const ext = filename.split(".").pop()?.toLowerCase();
  switch (ext) {
    case "md":
      return <FileText className="h-3.5 w-3.5 text-primary shrink-0" />;
    case "py":
      return <FileCode className="h-3.5 w-3.5 text-emerald-500 shrink-0" />;
    case "yml":
    case "yaml":
      return <Settings className="h-3.5 w-3.5 text-amber-500 shrink-0" />;
    default:
      return <File className="h-3.5 w-3.5 text-muted-foreground shrink-0" />;
  }
}

export function CitationItem({ citation, index }: CitationItemProps) {
  const filename = citation.file.split("/").pop() || citation.file;

  return (
    <div className="group flex flex-col p-3 bg-muted/30 border border-border/80 rounded-xl text-xs hover:border-primary/35 hover:bg-muted/50 transition-all duration-200 select-none min-w-0">
      
      {/* File details */}
      <div className="flex items-center justify-between gap-2 mb-2 pb-1.5 border-b border-border/30 min-w-0">
        <div className="flex items-center gap-1.5 min-w-0 flex-1">
          {getDocumentIcon(filename)}
          <span
            className="font-extrabold text-foreground truncate group-hover:text-primary transition-colors flex-1"
            title={citation.file}
          >
            {filename}
          </span>
        </div>
        <span className="px-1.5 py-0.5 text-[9px] font-bold rounded bg-primary/10 text-primary border border-primary/20 shrink-0">
          [{index}]
        </span>
      </div>


      {/* Metadata tags */}
      <div className="flex flex-wrap gap-1.5">
        <span className="px-1.5 py-0.5 rounded bg-muted/60 border border-border/40 text-[9px] font-semibold text-muted-foreground tracking-wide">
          {citation.project}
        </span>
        <span className="px-1.5 py-0.5 rounded bg-muted/60 border border-border/40 text-[9px] font-semibold text-muted-foreground tracking-wide">
          Layer {citation.layer}
        </span>
      </div>

    </div>
  );
}
