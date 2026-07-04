"use client";

import * as React from "react";
import { useState, useEffect } from "react";
import { PageContainer } from "@/components/common/PageContainer";
import { PageHeader } from "@/components/common/PageHeader";
import { TechCategory } from "@/components/stack/TechCategory";
import { fetchStack } from "@/services/api/portfolio";
import { StackResponse } from "@/types/portfolio";
import { Loader2, AlertCircle, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";

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
        {loading && (
          <div className="flex flex-col items-center justify-center py-20 space-y-2">
            <Loader2 className="h-8 w-8 text-primary animate-spin" />
            <span className="text-xs text-muted-foreground font-medium">Fetching stack configurations...</span>
          </div>
        )}

        {error && (
          <div className="flex flex-col items-center justify-center py-16 border border-rose-500/15 bg-rose-500/5 rounded-2xl p-6 text-center space-y-4">
            <AlertCircle className="h-8 w-8 text-rose-500" />
            <div>
              <h3 className="text-sm font-bold text-foreground">API Connection Issue</h3>
              <p className="text-xs text-muted-foreground mt-1 max-w-md">
                Unable to establish a connection with the backend portfolio service. Please verify that the backend application is running.
              </p>
            </div>
            <Button onClick={loadData} size="sm" className="gap-1.5 font-semibold cursor-pointer">
              <RefreshCw className="h-3.5 w-3.5" />
              Retry Connection
            </Button>
          </div>
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
