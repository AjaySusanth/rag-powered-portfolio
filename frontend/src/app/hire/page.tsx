import * as React from "react";
import { PageContainer } from "@/components/common/PageContainer";
import { PageHeader } from "@/components/common/PageHeader";
import { EmptyState } from "@/components/common/EmptyState";
import { Mail } from "lucide-react";

export default function HirePage() {
  return (
    <PageContainer>
      <PageHeader
        title="Hire Me"
        description="Connect with me regarding employment opportunities, project consultancy, or general engineering questions."
      />
      <EmptyState
        title="Contact system coming soon"
        description="The availability status card and the email message form are being finalized. Soon you will be able to dispatch message packages directly."
        icon={<Mail className="h-10 w-10 text-primary animate-pulse" />}
      />
    </PageContainer>
  );
}
