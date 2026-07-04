"use client";

import { useEffect, useRef, useState } from "react";

export function useAutoScroll(dependency: any) {
  const scrollRef = useRef<HTMLDivElement | null>(null);
  const [isUserScrolled, setIsUserScrolled] = useState(false);

  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;

    const handleScroll = () => {
      const threshold = 100; // threshold in px to detect if user manually scrolled up
      const distanceFromBottom = el.scrollHeight - el.scrollTop - el.clientHeight;
      setIsUserScrolled(distanceFromBottom > threshold);
    };

    el.addEventListener("scroll", handleScroll, { passive: true });
    return () => el.removeEventListener("scroll", handleScroll);
  }, []);

  useEffect(() => {
    const el = scrollRef.current;
    if (!el || isUserScrolled) return;

    // Pin scroll position directly to the bottom (snappy for fast token streaming)
    el.scrollTop = el.scrollHeight;
  }, [dependency, isUserScrolled]);

  return { scrollRef, isUserScrolled };
}
