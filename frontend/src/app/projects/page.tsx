import * as React from "react";
import { PageContainer } from "@/components/common/PageContainer";
import { PageHeader } from "@/components/common/PageHeader";
import { ProjectCard } from "@/components/projects/ProjectCard";
import { PROJECTS } from "@/constants/projects";

export default function ProjectsPage() {
  return (
    <PageContainer>
      <PageHeader
        title="Projects"
        description="Explore the architecture, implementation choices, and key challenges of the systems I have designed and deployed."
      />
      
      {/* Responsive Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-8 max-w-5xl mx-auto">
        {PROJECTS.map((project) => (
          <ProjectCard key={project.name} project={project} />
        ))}
      </div>
    </PageContainer>
  );
}
