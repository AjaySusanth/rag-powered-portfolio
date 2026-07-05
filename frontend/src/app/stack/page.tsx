"use client";

import * as React from "react";
import { useState, useEffect } from "react";
import { PageContainer } from "@/components/common/PageContainer";
import { PageHeader } from "@/components/common/PageHeader";
import { TechCategory } from "@/components/stack/TechCategory";
import { fetchStack } from "@/services/api/portfolio";
import { StackResponse } from "@/types/portfolio";
import { StackSkeleton } from "@/components/common/Skeleton";
import { StatusState } from "@/components/common/StatusState";

export default function StackPage() {
  const [data, setData] = useState<StackResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetchStack();
      setData(res);
    } catch (err: any) {
      setError(err.message || "Failed to load technology stack.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  return (
    <PageContainer>
      <PageHeader
        title="Technology Stack"
        description="Comprehensive inventory of languages, frameworks, databases, cloud native resources, and developer tools I work with."
      />

      <div className="mt-8 max-w-5xl mx-auto w-full">
        {loading && <StackSkeleton />}

        {error && (
          <StatusState
            type="error"
            title="Failed to Load Technology Stack"
            description="We were unable to fetch the technology inventory. Please verify that the API backend server is running."
            onRetry={loadData}
          />
        )}

        {!loading && !error && data && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <TechCategory title="Languages" items={data.languages} />
            <TechCategory title="Frameworks / Libraries" items={data.frameworks} />
            <TechCategory title="Databases & Cache" items={data.databases} />
            <TechCategory title="Cloud Infrastructure" items={data.cloud} />
            <TechCategory title="DevOps / GitOps" items={data.devops} />
            <TechCategory title="AI / ML" items={data.ai_ml} />
            <TechCategory title="Developer Tools" items={data.tools} />
          </div>
        )}
      </div>
    </PageContainer>
  );
}
