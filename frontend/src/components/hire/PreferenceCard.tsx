import * as React from "react";
import { Briefcase, MapPin } from "lucide-react";

interface PreferenceCardProps {
  preferredRoles: string[];
  preferredLocations: string[];
}

export function PreferenceCard({ preferredRoles, preferredLocations }: PreferenceCardProps) {
  return (
    <div className="flex flex-col border border-border bg-card/30 rounded-xl p-5 backdrop-blur-sm space-y-4 hover:border-primary/20 transition-all duration-300">
      <div className="flex items-center gap-2 border-b border-border/40 pb-3">
        <Briefcase className="h-4 w-4 text-primary" />
        <h3 className="font-bold text-foreground text-xs uppercase tracking-wider">Preferences</h3>
      </div>
      <div className="space-y-3.5 text-xs">
        <div>
          <span className="font-bold text-foreground/90 block mb-1">Preferred Roles:</span>
          <ul className="list-disc pl-4 text-muted-foreground space-y-1">
            {preferredRoles.map((role) => (
              <li key={role}>{role}</li>
            ))}
          </ul>
        </div>
        <div>
          <span className="font-bold text-foreground/90 block mb-1">Target Locations:</span>
          <div className="flex flex-wrap gap-1.5">
            {preferredLocations.map((loc) => (
              <span key={loc} className="flex items-center gap-1 px-2 py-0.5 rounded bg-muted text-[10px] font-medium text-foreground">
                <MapPin className="h-2.5 w-2.5 text-muted-foreground" />
                {loc}
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
