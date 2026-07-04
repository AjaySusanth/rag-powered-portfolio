"use client";

import * as React from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { BackendStatus } from "./BackendStatus";
import { HERO_CONTENT } from "@/constants/home";
import { MessageSquare, FileText, Mail } from "lucide-react";

function GithubIcon(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" className="h-3.5 w-3.5" {...props}>
      <path d="M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12" />
    </svg>
  );
}

export function HeroSection() {
  const { greeting, name, title, introduction, ctas } = HERO_CONTENT;

  return (
    <motion.section
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45, ease: "easeOut" }}
      className="space-y-6"
    >
      <div className="space-y-2">
        <h2 className="text-xs sm:text-sm font-semibold tracking-wider text-primary uppercase">
          {greeting}
        </h2>
        <h1 className="text-4xl font-extrabold tracking-tight text-foreground sm:text-5xl md:text-6xl">
          {name}
        </h1>
        <p className="text-base sm:text-lg md:text-xl font-medium text-muted-foreground tracking-tight">
          {title}
        </p>
      </div>

      <p className="text-sm sm:text-base md:text-lg text-muted-foreground max-w-3xl leading-relaxed">
        {introduction}
      </p>

      {/* CTA Buttons */}
      <div className="flex flex-wrap gap-3 items-center">
        <Button
          variant="default"
          className="gap-2 px-5 font-semibold"
          render={<a href={ctas.chat.href} />}
        >
          <MessageSquare className="h-4 w-4" />
          {ctas.chat.label}
        </Button>

        <Button
          variant="outline"
          className="gap-2 hover:bg-muted font-semibold"
          render={<Link href={ctas.resume.href} />}
        >
          <FileText className="h-4 w-4 text-muted-foreground" />
          {ctas.resume.label}
        </Button>

        <Button
          variant="outline"
          className="gap-2 hover:bg-muted font-semibold"
          render={<Link href={ctas.hire.href} />}
        >
          <Mail className="h-4 w-4 text-muted-foreground" />
          {ctas.hire.label}
        </Button>

        <Button
          variant="outline"
          className="gap-2 hover:bg-muted font-semibold"
          render={
            <a
              href={ctas.github.href}
              target="_blank"
              rel="noopener noreferrer"
            />
          }
        >
          <GithubIcon />
          {ctas.github.label}
        </Button>
      </div>

      {/* Status indicator directly beneath CTAs */}
      <div className="pt-1.5">
        <BackendStatus variant="Ready" />
      </div>
    </motion.section>
  );
}
