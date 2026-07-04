import { StackResponse, HireResponse } from "@/types/portfolio";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export function getResumeUrl(): string {
  return `${API_URL}/resume`;
}

export async function fetchStack(): Promise<StackResponse> {
  const response = await fetch(`${API_URL}/stack`);
  if (!response.ok) {
    throw new Error(`Failed to fetch tech stack (HTTP ${response.status})`);
  }
  return response.json();
}

export async function fetchHire(): Promise<HireResponse> {
  const response = await fetch(`${API_URL}/hire`);
  if (!response.ok) {
    throw new Error(`Failed to fetch hire information (HTTP ${response.status})`);
  }
  return response.json();
}

export async function healthCheck(): Promise<boolean> {
  try {
    const response = await fetch(`${API_URL}/health`, { signal: AbortSignal.timeout(3000) });
    return response.ok;
  } catch {
    return false;
  }
}
