"use client";

import { useEffect, useRef, useState } from "react";
import { useReducedMotion } from "framer-motion";

export function useAutoScroll(dependency: any) {
  const scrollRef = useRef<HTMLDivElement | null>(null);
  const [isUserScrolled, setIsUserScrolled] = useState(false);
  const shouldReduceMotion = useReducedMotion();

  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;

    const handleScroll = () => {
      const threshold = 60; // Threshold to detect manual user scroll-up
      const distanceFromBottom = el.scrollHeight - el.scrollTop - el.clientHeight;
      setIsUserScrolled(distanceFromBottom > threshold);
    };

    el.addEventListener("scroll", handleScroll, { passive: true });
    return () => el.removeEventListener("scroll", handleScroll);
  }, []);

  useEffect(() => {
    const el = scrollRef.current;
    if (!el || isUserScrolled) return;

    // Smoothly scroll to bottom, respecting prefers-reduced-motion
    el.scrollTo({
      top: el.scrollHeight,
      behavior: shouldReduceMotion ? "auto" : "smooth",
    });
  }, [dependency, isUserScrolled, shouldReduceMotion]);

  return { scrollRef, isUserScrolled };
}
