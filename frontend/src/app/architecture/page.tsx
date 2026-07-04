import * as React from "react";
import { PageContainer } from "@/components/common/PageContainer";
import { PageHeader } from "@/components/common/PageHeader";
import { EmptyState } from "@/components/common/EmptyState";
import { Network } from "lucide-react";

export default function ArchitecturePage() {
  return (
    <PageContainer>
      <PageHeader
        title="System Architecture"
        description="A technical deep-dive into the ingestion pipelines, retrieval strategies, database modeling, and deployment architectures."
      />
      <EmptyState
        title="Architecture diagrams coming soon"
        description="Detailed system maps, sequence drawings for RRF (Reciprocal Rank Fusion) logic, and Docker deployment flows will be uploaded shortly!"
        icon={<Network className="h-10 w-10 text-primary animate-pulse" />}
      />
    </PageContainer>
  );
}
