import * as React from "react";
import { PageContainer } from "@/components/common/PageContainer";
import { PageHeader } from "@/components/common/PageHeader";
import { EmptyState } from "@/components/common/EmptyState";
import { FileText } from "lucide-react";

export default function ResumePage() {
  return (
    <PageContainer>
      <PageHeader
        title="Resume"
        description="View and download my latest professional CV. Details work experience, system design milestones, and cloud competencies."
      />
      <EmptyState
        title="Resume viewer coming soon"
        description="We are integrating the interactive react-pdf engine. In the meantime, you'll soon be able to download the resume directly."
        icon={<FileText className="h-10 w-10 text-primary animate-pulse" />}
      />
    </PageContainer>
  );
}
