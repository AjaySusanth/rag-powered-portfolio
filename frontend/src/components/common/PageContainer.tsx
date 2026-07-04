import * as React from "react";
import { cn } from "@/lib/utils";

interface PageContainerProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
}

export function PageContainer({ children, className, ...props }: PageContainerProps) {
  return (
    <div
      className={cn(
        "mx-auto w-full max-w-[1280px] px-4 sm:px-6 md:px-8 py-6 md:py-8",
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}
