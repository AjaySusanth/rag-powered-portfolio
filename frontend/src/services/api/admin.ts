import { PipelineTrace } from "@/types/tracing";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * Verifies if the provided admin key is valid by hitting /admin/verify.
 */
export async function verifyAdminKey(adminKey: string): Promise<boolean> {
  try {
    const response = await fetch(`${API_URL}/admin/verify`, {
      method: "GET",
      headers: {
        "X-Admin-Key": adminKey,
      },
    });
    return response.ok;
  } catch (error) {
    console.error("Error verifying admin key:", error);
    return false;
  }
}

/**
 * Triggers a query trace using the provided admin key.
 */
export async function fetchRetrievalTrace(
  query: string,
  adminKey: string,
  sessionId?: string
): Promise<PipelineTrace> {
  const response = await fetch(`${API_URL}/admin/retrieval-trace`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Admin-Key": adminKey,
    },
    body: JSON.stringify({
      query,
      session_id: sessionId || null,
    }),
  });

  if (!response.ok) {
    if (response.status === 401 || response.status === 403) {
      throw new Error("Authentication failed: Invalid admin key.");
    }
    const errorData = await response.json().catch(() => ({}));
    const message = errorData.detail || `HTTP error ${response.status}`;
    throw new Error(message);
  }

  return response.json();
}
