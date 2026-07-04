import * as React from "react";
import { PageContainer } from "@/components/common/PageContainer";
import { PageHeader } from "@/components/common/PageHeader";
import { EmptyState } from "@/components/common/EmptyState";
import { FolderGit } from "lucide-react";

export default function ProjectsPage() {
  return (
    <PageContainer>
      <PageHeader
        title="Projects"
        description="Explore the architecture, implementation choices, and key challenges of the systems I have designed and deployed."
      />
      <EmptyState
        title="Project list coming soon"
        description="The detailed showcases of core projects are currently being written. Soon, you will be able to review architecture schemas, code samples, and lessons learned."
        icon={<FolderGit className="h-10 w-10 text-primary animate-pulse" />}
      />
    </PageContainer>
  );
}
