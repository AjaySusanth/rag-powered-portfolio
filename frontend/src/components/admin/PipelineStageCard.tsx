"use client";

/**
 * WHY THIS DESIGN WAS CHOSEN:
 * PipelineStageCard is designed as a reusable, modular visual step in the RAG retrieval pipeline.
 * It uses interactive Tailwind CSS structures and Lucide icons to present complex pipeline step metrics
 * (latency, duplicate filtering counts, score ranges, and source metadata) with expandable details.
 * This ensures that interviewers or developers can visually trace the flow of chunks without cluttering
 * the main executive dashboard with dense data structures.
 */

import { useState } from "react";
import { ChevronDown, ChevronUp, FileCode, Clock, Hash, Percent, Trash, CheckCircle2, XCircle } from "lucide-react";
import { ChunkTrace } from "@/types/tracing";

interface PipelineStageCardProps {
  title: string;
  description?: string;
  latencyMs: number;
  candidateCount?: number;
  scoreRange?: [number, number] | null;
  duplicatesRemoved?: number | null;
  chunks?: ChunkTrace[];
  rejectedChunks?: ChunkTrace[] | null;
  children?: React.ReactNode;
}

export function PipelineStageCard({
  title,
  description,
  latencyMs,
  candidateCount,
  scoreRange,
  duplicatesRemoved,
  chunks = [],
  rejectedChunks = [],
  children,
}: PipelineStageCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const getLayerColor = (layer: string) => {
    switch (layer.toLowerCase()) {
      case "identity":
      case "1":
        return "bg-emerald-500/10 text-emerald-400 border-emerald-500/20";
      case "design":
      case "2":
        return "bg-blue-500/10 text-blue-400 border-blue-500/20";
      case "artifact":
      case "3":
        return "bg-amber-500/10 text-amber-400 border-amber-500/20";
      default:
        return "bg-muted text-muted-foreground border-border";
    }
  };

  const hasContent = chunks.length > 0 || (rejectedChunks && rejectedChunks.length > 0) || !!children;

  return (
    <div className="group border border-border/80 bg-card/10 backdrop-blur-sm rounded-xl transition-all duration-200 hover:border-primary/30 hover:bg-card/25 shadow-md">
      {/* Card Header */}
      <div
        onClick={() => hasContent && setIsExpanded(!isExpanded)}
        className={`flex items-center justify-between p-5 select-none ${
          hasContent ? "cursor-pointer" : ""
        }`}
      >
        <div className="flex flex-col gap-1 pr-4">
          <h3 className="font-semibold text-foreground text-base tracking-wide flex items-center gap-2">
            {title}
          </h3>
          {description && <p className="text-xs text-muted-foreground">{description}</p>}
        </div>

        {/* Badges and Expand Button */}
        <div className="flex items-center gap-3">
          {/* Latency badge */}
          <div className="flex items-center gap-1 text-xs text-muted-foreground bg-muted/50 dark:bg-muted/30 px-2.5 py-1 rounded-full border border-border/40">
            <Clock className="h-3.5 w-3.5 text-primary/75" />
            <span>{latencyMs.toFixed(1)} ms</span>
          </div>

          {/* Counts badge */}
          {candidateCount !== undefined && (
            <div className="flex items-center gap-1 text-xs text-muted-foreground bg-muted/50 dark:bg-muted/30 px-2.5 py-1 rounded-full border border-border/40">
              <Hash className="h-3.5 w-3.5 text-secondary/75" />
              <span>{candidateCount} items</span>
            </div>
          )}

          {/* Score range badge */}
          {scoreRange && scoreRange[0] !== undefined && (
            <div className="hidden sm:flex items-center gap-1 text-xs text-muted-foreground bg-muted/50 dark:bg-muted/30 px-2.5 py-1 rounded-full border border-border/40">
              <Percent className="h-3.5 w-3.5 text-indigo-400" />
              <span>
                [{scoreRange[0].toFixed(2)} - {scoreRange[1].toFixed(2)}]
              </span>
            </div>
          )}

          {/* Duplicates badge */}
          {duplicatesRemoved !== undefined && duplicatesRemoved !== null && duplicatesRemoved > 0 && (
            <div className="hidden md:flex items-center gap-1 text-xs text-rose-400 bg-rose-500/10 px-2.5 py-1 rounded-full border border-rose-500/20">
              <Trash className="h-3.5 w-3.5" />
              <span>{duplicatesRemoved} filtered</span>
            </div>
          )}

          {hasContent && (
            <div className="text-muted-foreground group-hover:text-foreground transition-colors duration-150 pl-2">
              {isExpanded ? <ChevronUp className="h-4.5 w-4.5" /> : <ChevronDown className="h-4.5 w-4.5" />}
            </div>
          )}
        </div>
      </div>

      {/* Card Content */}
      {isExpanded && hasContent && (
        <div className="border-t border-border/50 bg-card/5 p-5 space-y-4 max-h-[600px] overflow-y-auto">
          {children}

          {/* Render Accepted Chunks */}
          {chunks.length > 0 && (
            <div className="space-y-3">
              {rejectedChunks && rejectedChunks.length > 0 && (
                <h4 className="text-xs font-semibold text-emerald-400 flex items-center gap-1.5 uppercase tracking-wider pb-1">
                  <CheckCircle2 className="h-3.5 w-3.5" /> Accepted Chunks ({chunks.length})
                </h4>
              )}
              {chunks.map((chunk, idx) => (
                <div
                  key={chunk.chunk_id || `acc-${idx}`}
                  className="border border-emerald-500/20 bg-emerald-500/5 dark:bg-emerald-950/10 rounded-lg p-4 space-y-2 hover:border-emerald-500/40 transition-colors duration-150"
                >
                  {/* Chunk Header */}
                  <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border/30 pb-2">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/10">
                        Rank {chunk.rank !== undefined ? chunk.rank : idx + 1}
                      </span>
                      <div className="flex items-center gap-1 text-xs text-muted-foreground">
                        <FileCode className="h-3.5 w-3.5 text-emerald-500/70" />
                        <span className="font-medium max-w-[150px] sm:max-w-xs truncate" title={chunk.source_file}>
                          {chunk.source_file}
                        </span>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${getLayerColor(chunk.layer)}`}>
                        Layer {chunk.layer}
                      </span>
                      {chunk.project && chunk.project !== "__global__" && (
                        <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full border border-indigo-500/20 bg-indigo-500/10 text-indigo-400">
                          {chunk.project}
                        </span>
                      )}
                      <span className="text-xs font-mono font-bold text-emerald-400">
                        Score: {chunk.score.toFixed(4)}
                      </span>
                    </div>
                  </div>

                  {/* Chunk Content Preview */}
                  <p className="text-xs leading-relaxed text-foreground/90 font-mono whitespace-pre-wrap bg-background/40 p-2.5 rounded border border-border/10">
                    {chunk.content_preview}
                  </p>
                </div>
              ))}
            </div>
          )}

          {/* Render Rejected Chunks */}
          {rejectedChunks && rejectedChunks.length > 0 && (
            <div className="space-y-3 pt-2">
              <h4 className="text-xs font-semibold text-rose-400 flex items-center gap-1.5 uppercase tracking-wider pb-1">
                <XCircle className="h-3.5 w-3.5" /> Rejected Chunks ({rejectedChunks.length})
              </h4>
              {rejectedChunks.map((chunk, idx) => (
                <div
                  key={chunk.chunk_id || `rej-${idx}`}
                  className="border border-rose-500/20 bg-rose-500/5 dark:bg-rose-950/10 rounded-lg p-4 space-y-2 hover:border-rose-500/40 transition-colors duration-150"
                >
                  {/* Chunk Header */}
                  <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border/30 pb-2">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-mono text-rose-400 bg-rose-500/10 px-2 py-0.5 rounded border border-rose-500/10">
                        Index {chunk.rank !== undefined ? chunk.rank : idx + 1}
                      </span>
                      <div className="flex items-center gap-1 text-xs text-muted-foreground">
                        <FileCode className="h-3.5 w-3.5 text-rose-500/70" />
                        <span className="font-medium max-w-[150px] sm:max-w-xs truncate" title={chunk.source_file}>
                          {chunk.source_file}
                        </span>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${getLayerColor(chunk.layer)}`}>
                        Layer {chunk.layer}
                      </span>
                      {chunk.project && chunk.project !== "__global__" && (
                        <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full border border-indigo-500/20 bg-indigo-500/10 text-indigo-400">
                          {chunk.project}
                        </span>
                      )}
                      <span className="text-xs font-mono font-bold text-rose-400">
                        Score: {chunk.score.toFixed(4)}
                      </span>
                    </div>
                  </div>

                  {/* Rejection reason badge */}
                  {chunk.reason && (
                    <div className="text-xs text-rose-400/90 bg-rose-500/10 px-3 py-1.5 rounded-md border border-rose-500/20 font-sans flex items-start gap-1">
                      <strong className="shrink-0">Reason:</strong>
                      <span className="italic">{chunk.reason}</span>
                    </div>
                  )}

                  {/* Chunk Content Preview */}
                  <p className="text-xs leading-relaxed text-muted-foreground font-mono whitespace-pre-wrap bg-background/40 p-2.5 rounded border border-border/10">
                    {chunk.content_preview}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
