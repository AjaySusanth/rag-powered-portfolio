import * as React from "react";

interface TimelineStepProps {
  number: number;
  title: string;
  technologies: string[];
  description: string;
  details: string[];
}

export function TimelineStep({ number, title, technologies, description, details }: TimelineStepProps) {
  return (
    <div className="relative pl-8 sm:pl-10 pb-8 last:pb-0 border-l border-border/80 last:border-l-transparent">
      {/* Circle Index Indicator */}
      <div className="absolute left-0 top-0 -translate-x-[50%] flex h-7 w-7 sm:h-8 sm:w-8 items-center justify-center rounded-full bg-background border-2 border-primary text-xs font-bold text-primary shadow-sm select-none">
        {number}
      </div>

      <div className="space-y-2">
        <div className="flex flex-wrap items-center gap-2">
          <h4 className="text-sm sm:text-base font-bold text-foreground">{title}</h4>
          <div className="flex flex-wrap gap-1">
            {technologies.map((tech) => (
              <span
                key={tech}
                className="px-1.5 py-0.5 rounded bg-muted border border-border/40 text-[9px] font-semibold text-muted-foreground"
              >
                {tech}
              </span>
            ))}
          </div>
        </div>
        <p className="text-xs text-muted-foreground max-w-3xl leading-relaxed">{description}</p>
        <ul className="list-disc pl-4 text-[11px] text-muted-foreground/80 space-y-1 max-w-3xl">
          {details.map((detail, idx) => (
            <li key={idx} className="leading-normal">
              {detail}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
