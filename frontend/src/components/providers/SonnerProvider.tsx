"use client";

import { Toaster } from "sonner";
import { useTheme } from "next-themes";

export function SonnerProvider() {
  const { theme } = useTheme();

  return (
    <Toaster
      theme={theme as "light" | "dark" | "system"}
      closeButton
      richColors
      position="top-right"
    />
  );
}
