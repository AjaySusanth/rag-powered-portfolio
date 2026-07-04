import * as React from "react";
import { Citation } from "@/types/chat";
import { CitationItem } from "./CitationItem";
import { ChevronDown, Library } from "lucide-react";

interface CitationListProps {
  citations: Citation[];
}

export function CitationList({ citations }: CitationListProps) {
  if (!citations || citations.length === 0) return null;

  return (
    <div className="mt-4 pt-3.5 border-t border-border/40">
      
      {/* Mobile view: collapsible accordion */}
      <details className="group md:hidden block outline-none">
        <summary className="flex items-center justify-between text-xs font-bold text-muted-foreground hover:text-foreground cursor-pointer select-none list-none outline-none">
          <div className="flex items-center gap-2">
            <Library className="h-3.5 w-3.5 text-muted-foreground" />
            <span>Sources ({citations.length})</span>
          </div>
          <ChevronDown className="h-3.5 w-3.5 text-muted-foreground transition-transform duration-200 group-open:rotate-180" />
        </summary>
        <div className="grid grid-cols-1 gap-2 mt-3 animate-fade-in">
          {citations.map((citation, index) => (
            <CitationItem key={`${citation.project}-${citation.layer}-${citation.file}-${index}`} citation={citation} index={index + 1} />
          ))}
        </div>
      </details>

      {/* Desktop view: persistent inline list */}
      <div className="hidden md:block space-y-3">
        <div className="flex items-center gap-2 text-xs font-bold text-muted-foreground select-none">
          <Library className="h-3.5 w-3.5 text-muted-foreground" />
          <span>Sources ({citations.length})</span>
        </div>
        <div className="grid grid-cols-2 lg:grid-cols-3 gap-2">
          {citations.map((citation, index) => (
            <CitationItem key={`${citation.project}-${citation.layer}-${citation.file}-${index}`} citation={citation} index={index + 1} />
          ))}
        </div>
      </div>

    </div>
  );
}
