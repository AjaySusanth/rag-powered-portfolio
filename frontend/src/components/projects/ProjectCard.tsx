/**
 * WHY THIS DESIGN WAS CHOSEN:
 * The ProjectCard component displays software projects with their technology stack and links.
 * On mobile viewports, the repository and live demo links are wrapped in a 44x44px (`h-11 w-11`)
 * touch container to meet accessibility guidelines. The "Ask AI" CTA button is also expanded to 44px
 * (`h-11 sm:h-7`) height on mobile to ensure a comfortable touch target, while maintaining its original
 * layout on larger viewports.
 */
"use client";

import { Project } from "@/constants/projects";
import { Button } from "@/components/ui/button";
import { ExternalLink, MessageSquare, Terminal } from "lucide-react";
import { navigateToChat } from "@/utils/navigation";

function GithubIcon(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="currentColor"
      className="h-4.5 w-4.5"
      {...props}
    >
      <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
    </svg>
  );
}

interface ProjectCardProps {
  project: Project;
}

export function ProjectCard({ project }: ProjectCardProps) {
  return (
    <div className="group relative flex flex-col justify-between overflow-hidden rounded-2xl border border-border bg-card/30 p-6 transition-all duration-300 hover:border-primary/45 hover:shadow-lg hover:shadow-primary/5 hover:translate-y-[-2px] backdrop-blur-sm">
      
      {/* Decorative hover glow */}
      <div className="absolute -inset-px -z-10 rounded-2xl bg-gradient-to-br from-primary/10 to-transparent opacity-0 transition-opacity duration-300 group-hover:opacity-100" />
      
      <div className="space-y-4">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2">
            <Terminal className="h-5 w-5 text-primary" />
            <h3 className="text-lg font-bold text-foreground transition-colors group-hover:text-primary">
              {project.name}
            </h3>
          </div>
          
          <div className="flex gap-1 items-center -mr-2 -mt-2">
            <a
              href={project.githubUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="flex h-11 w-11 items-center justify-center rounded-full hover:bg-muted/40 text-muted-foreground hover:text-foreground transition-colors cursor-pointer"
              title="View Repository"
            >
              <GithubIcon />
            </a>
            {project.liveUrl && (
              <a
                href={project.liveUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="flex h-11 w-11 items-center justify-center rounded-full hover:bg-muted/40 text-muted-foreground hover:text-foreground transition-colors cursor-pointer"
                title="View Live Demo"
              >
                <ExternalLink className="h-4.5 w-4.5" />
              </a>
            )}
          </div>
        </div>

        {/* Short Description */}
        <p className="text-sm text-foreground/80 leading-relaxed">
          {project.shortDescription}
        </p>

        {/* Problem Solved */}
        <div className="rounded-lg bg-muted/30 border border-border/40 p-3 text-xs leading-relaxed">
          <span className="font-bold text-foreground block mb-1">Problem Solved:</span>
          <span className="text-muted-foreground">{project.problemSolved}</span>
        </div>

        {/* Engineering Highlights */}
        <div className="space-y-1.5">
          <span className="text-xs font-bold text-foreground">Engineering Highlights:</span>
          <ul className="list-disc pl-4 text-xs text-muted-foreground/90 space-y-1">
            {project.highlights.map((highlight, idx) => (
              <li key={idx} className="leading-normal">
                {highlight}
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* Footer (Tech Badges + Ask AI) */}
      <div className="mt-6 space-y-4 pt-4 border-t border-border/50">
        {/* Tech badges */}
        <div className="flex flex-wrap gap-1.5">
          {project.technologies.map((tech) => (
            <span
              key={tech}
              className="px-2 py-0.5 text-[10px] font-semibold rounded bg-primary/10 text-primary border border-primary/20"
            >
              {tech}
            </span>
          ))}
        </div>

        {/* Ask AI CTA Button */}
        <Button
          onClick={() => navigateToChat(project.aiPrompt)}
          variant="outline"
          size="sm"
          className="w-full h-11 sm:h-7 gap-1.5 text-xs font-semibold hover:bg-primary hover:text-primary-foreground border-primary/30 text-primary cursor-pointer transition-colors"
        >
          <MessageSquare className="h-3.5 w-3.5" />
          Ask AI about this project
        </Button>
      </div>

    </div>
  );
}



