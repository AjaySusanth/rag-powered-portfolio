import * as React from "react";
import { cn } from "@/lib/utils";

interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {}

export function Skeleton({ className, ...props }: SkeletonProps) {
  return (
    <div
      className={cn("animate-pulse rounded bg-muted/65", className)}
      {...props}
    />
  );
}

export function ResumeSkeleton() {
  return (
    <div className="w-full max-w-4xl mx-auto space-y-4">
      {/* PDF Controls skeleton */}
      <div className="flex items-center justify-between p-3 border border-border/80 bg-card/25 rounded-xl">
        <div className="flex gap-2">
          <Skeleton className="h-8 w-16" />
          <Skeleton className="h-8 w-16" />
        </div>
        <div className="flex gap-2">
          <Skeleton className="h-8 w-8 rounded-full" />
          <Skeleton className="h-8 w-8 rounded-full" />
        </div>
      </div>
      {/* PDF Viewport skeleton */}
      <div className="border border-border/85 bg-card/10 rounded-2xl p-6 flex flex-col items-center justify-center min-h-[580px]">
        <Skeleton className="h-[520px] w-full max-w-2xl rounded-xl" />
      </div>
    </div>
  );
}

export function StackSkeleton() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 w-full">
      {Array.from({ length: 6 }).map((_, idx) => (
        <div key={idx} className="flex flex-col border border-border bg-card/30 rounded-xl p-5 space-y-4">
          <div className="flex items-center gap-2 border-b border-border/40 pb-3">
            <Skeleton className="h-4 w-4 rounded-full" />
            <Skeleton className="h-4 w-32" />
          </div>
          <div className="flex flex-wrap gap-2">
            {Array.from({ length: 6 }).map((_, tagIdx) => (
              <Skeleton key={tagIdx} className="h-6 w-20 rounded-lg" />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

export function HireSkeleton() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 w-full">
      {/* Availability Card Skeleton */}
      <div className="flex flex-col border border-border bg-card/30 rounded-xl p-5 space-y-4">
        <div className="flex items-center gap-2 border-b border-border/40 pb-3">
          <Skeleton className="h-4 w-4 rounded-full" />
          <Skeleton className="h-3.5 w-28" />
        </div>
        <div className="space-y-4">
          <Skeleton className="h-5.5 w-24 rounded-full" />
          <div className="space-y-1.5">
            <Skeleton className="h-3 w-24" />
            <div className="flex gap-1.5">
              <Skeleton className="h-5 w-16" />
              <Skeleton className="h-5 w-16" />
            </div>
          </div>
          <div className="space-y-1.5">
            <Skeleton className="h-3 w-28" />
            <Skeleton className="h-3.5 w-36" />
          </div>
        </div>
      </div>

      {/* Preference Card Skeleton */}
      <div className="flex flex-col border border-border bg-card/30 rounded-xl p-5 space-y-4">
        <div className="flex items-center gap-2 border-b border-border/40 pb-3">
          <Skeleton className="h-4 w-4 rounded-full" />
          <Skeleton className="h-3.5 w-24" />
        </div>
        <div className="space-y-4">
          <div className="space-y-1.5">
            <Skeleton className="h-3 w-24" />
            <Skeleton className="h-3.5 w-full" />
            <Skeleton className="h-3.5 w-2/3" />
          </div>
          <div className="space-y-1.5">
            <Skeleton className="h-3 w-28" />
            <div className="flex gap-1.5">
              <Skeleton className="h-5 w-20" />
              <Skeleton className="h-5 w-20" />
            </div>
          </div>
        </div>
      </div>

      {/* Contact Card Skeleton */}
      <div className="flex flex-col border border-border bg-card/30 rounded-xl p-5 space-y-4">
        <div className="flex items-center gap-2 border-b border-border/40 pb-3">
          <Skeleton className="h-4 w-4 rounded-full" />
          <Skeleton className="h-3.5 w-32" />
        </div>
        <div className="space-y-4">
          <div className="space-y-2.5">
            <Skeleton className="h-4.5 w-full" />
            <Skeleton className="h-4.5 w-full" />
            <Skeleton className="h-4.5 w-full" />
            <Skeleton className="h-4.5 w-full" />
          </div>
          <div className="pt-3 border-t border-border/45">
            <Skeleton className="h-8.5 w-full rounded-lg" />
          </div>
        </div>
      </div>
    </div>
  );
}
