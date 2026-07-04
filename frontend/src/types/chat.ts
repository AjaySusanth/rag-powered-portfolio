export type MessageStatus = "streaming" | "complete" | "error";

export interface Citation {
  id?: string;
  file: string;
  layer: string;
  project: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
  status: MessageStatus;
}

export type SSETokenEvent = {
  type: "token";
  token: string;
};

export type SSECitationEvent = {
  type: "citations";
  citations: Citation[];
};

export type SSEDoneEvent = {
  type: "done";
};

export type SSEErrorEvent = {
  type: "error";
  message: string;
  retryable: boolean;
};

export type SSEEvent =
  | SSETokenEvent
  | SSECitationEvent
  | SSEDoneEvent
  | SSEErrorEvent;
