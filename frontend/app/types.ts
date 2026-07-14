export type Role = "user" | "assistant";

export interface Message {
  id: string;
  conversation_id: string;
  role: Role;
  content: string;
  position: number;
  created_at: string;
}

export interface ConversationSummary {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface ConversationDetail extends ConversationSummary {
  messages: Message[];
}

export type StreamEvent =
  | { type: "user"; message: Message }
  | { type: "meta"; assistant_message_id: string }
  | { type: "token"; content: string }
  | { type: "done"; message: Message }
  | { type: "error"; message: string };
