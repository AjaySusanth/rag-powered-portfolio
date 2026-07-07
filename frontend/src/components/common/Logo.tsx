/**
 * WHY THIS DESIGN WAS CHOSEN:
 * The Logo component displays the developer's branding (icon + name + subtitle).
 * On small viewports (under 640px/sm), the logo icon container scales down to `h-8 w-8`,
 * the gap shrinks to `gap-1.5`, the name scales to `text-xs`, and the subtitle scales to `text-[8px]`.
 * This prevents layout clipping and navbar congestion on extremely narrow devices (like 320px).
 */
import Link from "next/link";
import { Cpu } from "lucide-react";

export function Logo() {
  return (
    <Link
      href="/"
      className="flex items-center gap-1.5 sm:gap-2.5 font-semibold text-base sm:text-lg tracking-tight group focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 rounded-md p-1 -m-1"
    >
      <div className="relative flex h-8 w-8 sm:h-9 sm:w-9 items-center justify-center rounded-lg bg-primary text-primary-foreground transition-all duration-200 group-hover:scale-105 group-hover:shadow-[0_0_12px_rgba(59,107,229,0.4)] dark:group-hover:shadow-[0_0_12px_rgba(92,138,255,0.4)]">
        <Cpu className="h-4.5 w-4.5 sm:h-5 sm:w-5" />
      </div>
      <div className="flex flex-col">
        <span className="font-bold leading-none text-foreground text-xs sm:text-sm md:text-base">
          Ajay Susanth
        </span>
        <span className="text-[8px] sm:text-[9px] md:text-[10px] text-muted-foreground font-semibold tracking-wider uppercase mt-0.5">
          RAG Portfolio
        </span>
      </div>
    </Link>
  );
}

