import * as React from "react";
import { PageContainer } from "@/components/common/PageContainer";
import { PageHeader } from "@/components/common/PageHeader";
import { EmptyState } from "@/components/common/EmptyState";
import { Layers } from "lucide-react";

export default function StackPage() {
  return (
    <PageContainer>
      <PageHeader
        title="Tech Stack"
        description="A comprehensive listing of the programming languages, cloud providers, systems infrastructure, and databases that I develop with daily."
      />
      <EmptyState
        title="Tech stack coming soon"
        description="We are preparing the layout grouping for Languages, Databases, Cloud services, and AI/ML libraries, backed by our /stack metadata API."
        icon={<Layers className="h-10 w-10 text-primary animate-pulse" />}
      />
    </PageContainer>
  );
}
