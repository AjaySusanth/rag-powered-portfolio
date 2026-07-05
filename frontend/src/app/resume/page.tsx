"use client";

import * as React from "react";
import dynamic from "next/dynamic";
import { PageContainer } from "@/components/common/PageContainer";
import { PageHeader } from "@/components/common/PageHeader";

import { ResumeSkeleton } from "@/components/common/Skeleton";

// Dynamically load the client-only PDF viewer
const ResumeViewer = dynamic(() => import("@/components/resume/ResumeViewer"), {
  ssr: false,
  loading: () => <ResumeSkeleton />,
});

export default function ResumePage() {
  return (
    <PageContainer>
      <PageHeader
        title="Resume"
        description="View and download my latest professional CV. Details work experience, system design milestones, and cloud competencies."
      />
      <div className="mt-6 w-full max-w-4xl mx-auto">
        <ResumeViewer />
      </div>
    </PageContainer>
  );
}
