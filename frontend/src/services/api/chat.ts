import { SSEEvent, Citation } from "@/types/chat";

/**
 * Parses a single raw Server-Sent Event (SSE) frame string.
 * Returns a typed SSEEvent, or null if the frame is empty/keepalive.
 */
export function parseSSEEvent(raw: string): SSEEvent | null {
  const line = raw.replace(/^data:\s*/, "").trim();
  if (!line) return null;

  if (line === "[DONE]") {
    return { type: "done" };
  }

  try {
    const parsed = JSON.parse(line);
    if (parsed.token !== undefined) {
      return { type: "token", token: parsed.token };
    }
    if (parsed.citations !== undefined) {
      return { type: "citations", citations: parsed.citations };
    }
    if (parsed.error !== undefined) {
      return {
        type: "error",
        message: parsed.error,
        retryable: parsed.retryable ?? false,
      };
    }
    return null;
  } catch (err) {
    return {
      type: "error",
      message: "Malformed SSE frame received",
      retryable: true,
    };
  }
}

/**
 * Establishes a POST request connection to the chat streaming API.
 * Reads the response body as a stream and notifies callers via callbacks.
 */
export async function createChatStream(
  message: string,
  sessionId: string,
  handlers: {
    onToken: (token: string) => void;
    onCitations: (citations: Citation[]) => void;
    onDone: () => void;
    onError: (errorMsg: string, retryable: boolean) => void;
  },
  signal: AbortSignal
): Promise<void> {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  try {
    const response = await fetch(`${apiUrl}/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        message,
        session_id: sessionId,
      }),
      signal,
    });

    if (response.status === 429) {
      handlers.onError(
        "Rate limit exceeded. Please wait a moment before sending another message.",
        false
      );
      return;
    }

    if (!response.ok) {
      const isRetryable = response.status >= 500;
      handlers.onError(
        `Server error (${response.status}). Please try again.`,
        isRetryable
      );
      return;
    }

    if (!response.body) {
      handlers.onError("No response body received from server.", true);
      return;
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const frames = buffer.split("\n\n");
      buffer = frames.pop() ?? "";

      for (const frame of frames) {
        const cleanedFrame = frame.trim();
        if (!cleanedFrame) continue;

        const event = parseSSEEvent(cleanedFrame);
        if (!event) continue;

        switch (event.type) {
          case "token":
            handlers.onToken(event.token);
            break;
          case "citations":
            handlers.onCitations(event.citations);
            break;
          case "done":
            handlers.onDone();
            return;
          case "error":
            handlers.onError(event.message, event.retryable);
            return;
        }
      }
    }

    // Fallback in case the reader completes but no [DONE] event was encountered
    handlers.onDone();
  } catch (error: any) {
    if (error.name === "AbortError") {
      // Operation aborted by user controller, do not trigger error handling
      return;
    }
    handlers.onError(
      "A network error occurred. Please check your connection to the server.",
      true
    );
  }
}
