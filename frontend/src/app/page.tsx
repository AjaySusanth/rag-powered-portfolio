import * as React from "react";
import { PageContainer } from "@/components/common/PageContainer";
import { HeroSection } from "@/components/home/HeroSection";
import { SummaryStrip } from "@/components/home/SummaryStrip";
import { EmptyChat } from "@/components/home/EmptyChat";

export default function Home() {
  return (
    <PageContainer className="max-w-4xl space-y-12 md:space-y-16 py-8 md:py-12">
      
      {/* 1. Hero Section */}
      <HeroSection />

      {/* 2. Summary Strip */}
      <SummaryStrip />

      {/* 3. Empty Chat Area */}
      <EmptyChat />

    </PageContainer>
  );
}
