import * as React from "react";
import { Terminal, Database, Server, Cpu, Cloud, Code } from "lucide-react";

export function Footer() {
  const techStack = [
    { name: "FastAPI", icon: Cpu },
    { name: "Next.js", icon: Code },
    { name: "PostgreSQL", icon: Database },
    { name: "Redis", icon: Server },
    { name: "Azure", icon: Cloud },
    { name: "GitHub", icon: Terminal },
  ];

  return (
    <footer className="border-t border-border bg-card/10 py-6">
      <div className="mx-auto max-w-[1280px] px-4 sm:px-6 md:px-8 flex flex-col md:flex-row items-center justify-between gap-4">
        <p className="text-xs text-muted-foreground text-center md:text-left">
          © {new Date().getFullYear()} Ajay Susanth. All rights reserved.
        </p>
        <div className="flex flex-col sm:flex-row items-center gap-3 sm:gap-4">
          <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
            Built With
          </span>
          <div className="flex flex-wrap items-center justify-center gap-2">
            {techStack.map((tech) => {
              const Icon = tech.icon;
              return (
                <span
                  key={tech.name}
                  className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-muted/50 border border-border/80 text-xs font-medium text-foreground transition-colors hover:bg-muted"
                >
                  <Icon className="h-3 w-3 text-muted-foreground" />
                  {tech.name}
                </span>
              );
            })}
          </div>
        </div>
      </div>
    </footer>
  );
}
