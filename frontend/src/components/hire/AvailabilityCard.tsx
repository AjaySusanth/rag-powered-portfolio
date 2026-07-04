import * as React from "react";
import { Calendar, CheckCircle2, AlertCircle } from "lucide-react";

interface AvailabilityCardProps {
  currentlyAvailable: boolean;
  status: string;
  employmentTypes: string[];
  workAuthorization: string;
}

export function AvailabilityCard({
  currentlyAvailable,
  status,
  employmentTypes,
  workAuthorization,
}: AvailabilityCardProps) {
  return (
    <div className="flex flex-col border border-border bg-card/30 rounded-xl p-5 backdrop-blur-sm space-y-4 hover:border-primary/20 transition-all duration-300">
      <div className="flex items-center gap-2 border-b border-border/40 pb-3">
        <Calendar className="h-4 w-4 text-primary" />
        <h3 className="font-bold text-foreground text-xs uppercase tracking-wider">Availability & Status</h3>
      </div>
      <div className="space-y-3.5 text-xs">
        <div className="flex items-center gap-2">
          {currentlyAvailable ? (
            <span className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-500 font-semibold border border-emerald-500/20">
              <CheckCircle2 className="h-3 w-3" />
              Open for Offers
            </span>
          ) : (
            <span className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-500 font-semibold border border-amber-500/20">
              <AlertCircle className="h-3 w-3" />
              Passive Search
            </span>
          )}
          <span className="text-muted-foreground">{status}</span>
        </div>
        <div>
          <span className="font-bold text-foreground/90 block mb-1">Employment Types:</span>
          <div className="flex flex-wrap gap-1.5">
            {employmentTypes.map((type) => (
              <span key={type} className="px-2 py-0.5 rounded bg-muted text-[10px] font-medium text-foreground">
                {type}
              </span>
            ))}
          </div>
        </div>
        <div>
          <span className="font-bold text-foreground/90 block mb-1">Work Authorization:</span>
          <span className="text-muted-foreground">{workAuthorization}</span>
        </div>
      </div>
    </div>
  );
}
