import * as React from "react";
import { Code2, Server, Database, Cloud, Settings, Brain, Wrench } from "lucide-react";

interface TechCategoryProps {
  title: string;
  items: string[];
}

const iconsMap: Record<string, React.ReactNode> = {
  "Languages": <Code2 className="h-4 w-4 text-primary" />,
  "Frameworks / Libraries": <Server className="h-4 w-4 text-primary" />,
  "Databases & Cache": <Database className="h-4 w-4 text-primary" />,
  "Cloud Infrastructure": <Cloud className="h-4 w-4 text-primary" />,
  "DevOps / GitOps": <Settings className="h-4 w-4 text-primary" />,
  "AI / ML": <Brain className="h-4 w-4 text-primary" />,
  "Developer Tools": <Wrench className="h-4 w-4 text-primary" />,
};

export function TechCategory({ title, items }: TechCategoryProps) {
  if (!items || items.length === 0) return null;

  return (
    <div className="flex flex-col border border-border bg-card/30 rounded-xl p-5 hover:border-primary/35 transition-all duration-300 backdrop-blur-sm space-y-4">
      <div className="flex items-center gap-2 border-b border-border/40 pb-3">
        {iconsMap[title] || <Code2 className="h-4 w-4 text-primary" />}
        <h3 className="font-bold text-foreground text-xs tracking-wider uppercase">
          {title}
        </h3>
      </div>
      <div className="flex flex-wrap gap-2">
        {items.map((item) => (
          <div
            key={item}
            className="flex items-center px-3 py-1.5 rounded-lg bg-muted/40 border border-border/60 text-xs font-medium text-foreground hover:border-primary/45 hover:bg-muted/80 transition-all select-none"
          >
            {item}
          </div>
        ))}
      </div>
    </div>
  );
}
