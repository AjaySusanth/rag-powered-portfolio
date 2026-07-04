import * as React from "react";
import { PageContainer } from "@/components/common/PageContainer";
import { PageHeader } from "@/components/common/PageHeader";
import { EmptyState } from "@/components/common/EmptyState";
import { MessageSquare } from "lucide-react";

export default function Home() {
  return (
    <PageContainer>
      <PageHeader
        title="AI Portfolio Assistant"
        description="Ask me anything about my engineering experience, system architecture, or tech stack. The AI is grounded in design docs, code challenges, and schemas using a hybrid RAG pipeline."
      />
      <EmptyState
        title="AI Chat coming soon"
        description="We are currently fine-tuning our vector indexing and RRF query logic. The interactive chatbot will be online shortly!"
        icon={<MessageSquare className="h-10 w-10 text-primary animate-pulse" />}
      />
    </PageContainer>
  );
}
