export type MessageState = "queued" | "sending" | "delivered" | "failed" | "dead_letter";
export type Direction = "above" | "below";

export interface Alert {
  id: number;
  phone: string;
  chat_id: string;
  asset: string;
  direction: Direction;
  threshold: number;
  active: boolean;
  created_at: string;
}

export interface QueueMessage {
  id: number;
  chat_id: string;
  phone: string;
  body: string;
  alert_id: number | null;
  state: MessageState;
  retry_count: number;
  next_attempt_at: string | null;
  last_error: string | null;
  created_at: string;
  updated_at: string;
}

export interface TriggerRecord {
  id: number;
  alert_id: number;
  asset: string;
  direction: Direction;
  threshold: number;
  price_at_trigger: number;
  phone: string;
  message_id: number | null;
  triggered_at: string;
}


export type Prices = Record<string, number>;
