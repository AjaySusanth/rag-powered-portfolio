"use client";

import * as React from "react";
import { useState, useEffect } from "react";
import { PageContainer } from "@/components/common/PageContainer";
import { PageHeader } from "@/components/common/PageHeader";
import { AvailabilityCard } from "@/components/hire/AvailabilityCard";
import { PreferenceCard } from "@/components/hire/PreferenceCard";
import { ContactCard } from "@/components/hire/ContactCard";
import { fetchHire, getResumeUrl } from "@/services/api/portfolio";
import { HireResponse } from "@/types/portfolio";
import { Loader2, AlertCircle, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function HirePage() {
  const [data, setData] = useState<HireResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetchHire();
      setData(res);
    } catch (err: any) {
      setError(err.message || "Failed to load hire information.");
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
        title="Hire Me"
        description="Connect with me regarding employment opportunities, project consultancy, or general engineering inquiries."
      />

      <div className="mt-8 max-w-5xl mx-auto w-full">
        {loading && (
          <div className="flex flex-col items-center justify-center py-20 space-y-2">
            <Loader2 className="h-8 w-8 text-primary animate-spin" />
            <span className="text-xs text-muted-foreground font-medium">Fetching details...</span>
          </div>
        )}

        {error && (
          <div className="flex flex-col items-center justify-center py-16 border border-rose-500/15 bg-rose-500/5 rounded-2xl p-6 text-center space-y-4">
            <AlertCircle className="h-8 w-8 text-rose-500" />
            <div>
              <h3 className="text-sm font-bold text-foreground">API Connection Issue</h3>
              <p className="text-xs text-muted-foreground mt-1 max-w-md">
                Unable to retrieve hiring preferences. Please verify that the backend API service is running.
              </p>
            </div>
            <Button onClick={loadData} size="sm" className="gap-1.5 font-semibold cursor-pointer">
              <RefreshCw className="h-3.5 w-3.5" />
              Retry Connection
            </Button>
          </div>
        )}

        {!loading && !error && data && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <AvailabilityCard
              currentlyAvailable={data.currently_available}
              status={data.status}
              employmentTypes={data.employment_types}
              workAuthorization={data.work_authorization}
            />
            <PreferenceCard
              preferredRoles={data.preferred_roles}
              preferredLocations={data.preferred_locations}
            />
            <ContactCard
              email={data.contact.email}
              linkedin={data.contact.linkedin}
              github={data.contact.github}
              portfolio={data.contact.portfolio}
              resumeUrl={getResumeUrl()}
            />
          </div>
        )}
      </div>
    </PageContainer>
  );
}
