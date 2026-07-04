import * as React from "react";

interface ArchitectureSectionProps {
  id: string;
  title: string;
  badge?: string;
  description: string;
  children: React.ReactNode;
}

export function ArchitectureSection({ id, title, badge, description, children }: ArchitectureSectionProps) {
  return (
    <section
      id={id}
      className="scroll-mt-20 border border-border/80 bg-card/25 rounded-2xl p-6 md:p-8 backdrop-blur-sm space-y-4 transition-all duration-300 hover:border-primary/20 hover:shadow-sm"
    >
      <div className="flex flex-wrap items-center gap-3 border-b border-border/40 pb-4">
        <h2 className="text-base sm:text-lg font-bold text-foreground">{title}</h2>
        {badge && (
          <span className="px-2.5 py-0.5 text-[9px] font-bold rounded-full bg-primary/10 text-primary border border-primary/20 tracking-wide uppercase">
            {badge}
          </span>
        )}
      </div>
      <p className="text-xs sm:text-sm text-muted-foreground leading-relaxed max-w-4xl">
        {description}
      </p>
      <div className="pt-2">{children}</div>
    </section>
  );
}
