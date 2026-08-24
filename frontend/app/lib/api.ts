import type {
  ConversationDetail,
  ConversationSummary,
  IdentityProfile,
  StreamEvent,
} from "../types";
import { identityHeaders } from "./identity";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ||
  (process.env.NODE_ENV === "production"
    ? "https://my-assistant-gpt-clone-production.up.railway.app/api"
    : "http://localhost:8000/api");

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  headers.set("Content-Type", "application/json");
  for (const [name, value] of Object.entries(identityHeaders())) {
    headers.set(name, value);
  }
  let response: Response;
  try {
    response = await fetch(API_URL + path, {
      ...init,
      headers,
    });
  } catch (error) {
    throw new Error(
      `Failed to connect to the API at ${API_URL}. Please ensure the backend is running and CORS is configured.`
    );
  }

  if (!response.ok) {
    let message = "The request failed.";
    try {
      const payload = (await response.json()) as { detail?: string };
      message = payload.detail || message;
    } catch {
      message = response.statusText || message;
    }
    throw new Error(message);
  }

  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

export function getIdentityProfile(): Promise<IdentityProfile> {
  return request("/identity");
}

export function listConversations(): Promise<ConversationSummary[]> {
  return request("/conversations");
}

export function getConversation(id: string): Promise<ConversationDetail> {
  return request("/conversations/" + id);
}

export function createConversation(): Promise<ConversationDetail> {
  return request("/conversations", {
    method: "POST",
    body: JSON.stringify({ title: "New chat" }),
  });
}

export function renameConversation(
  id: string,
  title: string,
): Promise<ConversationDetail> {
  return request("/conversations/" + id, {
    method: "PATCH",
    body: JSON.stringify({ title }),
  });
}

export function deleteConversation(id: string): Promise<void> {
  return request("/conversations/" + id, { method: "DELETE" });
}

function parseEvent(block: string): StreamEvent | null {
  let eventName = "";
  const dataLines: string[] = [];

  for (const line of block.split(/\r?\n/)) {
    if (line.startsWith("event:")) {
      eventName = line.slice(6).trim();
    } else if (line.startsWith("data:")) {
      dataLines.push(line.slice(5).trim());
    }
  }

  if (!eventName || dataLines.length === 0) {
    return null;
  }

  const data = JSON.parse(dataLines.join("\n")) as Record<string, unknown>;
  return { type: eventName, ...data } as StreamEvent;
}

export async function streamConversation(
  conversationId: string,
  content: string | null,
  regenerate: boolean,
  onEvent: (event: StreamEvent) => void,
  signal: AbortSignal,
): Promise<void> {
  const path =
    "/conversations/" +
    conversationId +
    (regenerate ? "/regenerate" : "/messages");
  let response: Response;
  try {
    response = await fetch(API_URL + path, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...identityHeaders() },
      body: regenerate ? undefined : JSON.stringify({ content }),
      signal,
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw error;
    }
    throw new Error(
      `Failed to connect to the API at ${API_URL}. Please ensure the backend is running and CORS is configured.`
    );
  }

  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as {
      detail?: string;
    } | null;
    throw new Error(payload?.detail || "The assistant request failed.");
  }
  if (!response.body) {
    throw new Error("Streaming is not supported by this browser.");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    buffer += decoder.decode(value, { stream: !done });
    const blocks = buffer.split(/\r?\n\r?\n/);
    buffer = blocks.pop() || "";

    for (const block of blocks) {
      const event = parseEvent(block);
      if (event) {
        onEvent(event);
      }
    }

    if (done) {
      if (buffer.trim()) {
        const event = parseEvent(buffer);
        if (event) {
          onEvent(event);
        }
      }
      break;
    }
  }
}
