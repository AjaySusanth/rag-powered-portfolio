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
import { HireSkeleton } from "@/components/common/Skeleton";
import { StatusState } from "@/components/common/StatusState";

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
        {loading && <HireSkeleton />}

        {error && (
          <StatusState
            type="error"
            title="Failed to Load Preferences"
            description="We were unable to retrieve employment preferences. Please check if the portfolio service is online."
            onRetry={loadData}
          />
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
