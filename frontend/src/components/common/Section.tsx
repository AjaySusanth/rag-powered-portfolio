import * as React from "react";
import { cn } from "@/lib/utils";

interface SectionProps extends React.HTMLAttributes<HTMLElement> {
  children: React.ReactNode;
}

export function Section({ children, className, ...props }: SectionProps) {
  return (
    <section
      className={cn("py-6 md:py-10 first:pt-0 last:pb-0", className)}
      {...props}
    >
      {children}
    </section>
  );
}
