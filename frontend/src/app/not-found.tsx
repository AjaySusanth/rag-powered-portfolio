import * as React from "react";
import { PageContainer } from "@/components/common/PageContainer";
import { EmptyState } from "@/components/common/EmptyState";
import { HelpCircle } from "lucide-react";

export default function NotFound() {
  return (
    <PageContainer className="flex items-center justify-center min-h-[60vh]">
      <EmptyState
        title="404 — Page Not Found"
        description="The resource you requested could not be located in our workspace indexes. It may have been relocated, deleted, or never existed."
        icon={<HelpCircle className="h-10 w-10 text-destructive animate-bounce" />}
        actionText="Return to Chat"
        actionHref="/"
      />
    </PageContainer>
  );
}
