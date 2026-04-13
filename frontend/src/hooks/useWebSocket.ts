"use client";

import { useEffect, useRef, useState } from "react";
import type { Alert, Prices, QueueMessage, TriggerRecord } from "@/types";

export interface DashboardState {
  alerts: Alert[];
  queue: QueueMessage[];
  prices: Prices;
  history: TriggerRecord[];
  connected: boolean;
}

const INITIAL: DashboardState = {
  alerts: [],
  queue: [],
  prices: {},
  history: [],
  connected: false,
};

const WS_BASE = process.env.NEXT_PUBLIC_WS_URL ?? "ws://localhost:8000";

export function useWebSocket(): DashboardState {
  const [state, setState] = useState<DashboardState>(INITIAL);
  const retryDelay = useRef(1000);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    let ws: WebSocket;
    let cancelled = false;

    function connect() {
      ws = new WebSocket(`${WS_BASE}/api/ws`);

      ws.onopen = () => {
        retryDelay.current = 1000;
        setState((s) => ({ ...s, connected: true }));
      };

      ws.onmessage = (e: MessageEvent<string>) => {
        const { event, data } = JSON.parse(e.data) as { event: string; data: unknown };
        setState((s) => {
          switch (event) {
            case "alerts":  return { ...s, alerts:  data as Alert[] };
            case "queue":   return { ...s, queue:   data as QueueMessage[] };
            case "prices":  return { ...s, prices:  data as Prices };
            case "history": return { ...s, history: data as TriggerRecord[] };
            default:        return s;
          }
        });
      };

      ws.onclose = () => {
        if (cancelled) return;
        setState((s) => ({ ...s, connected: false }));
        timerRef.current = setTimeout(() => {
          retryDelay.current = Math.min(retryDelay.current * 2, 30_000);
          connect();
        }, retryDelay.current);
      };

      ws.onerror = () => ws.close(); // delegate retry to onclose
    }

    connect();

    return () => {
      cancelled = true;
      if (timerRef.current) clearTimeout(timerRef.current);
      ws.close();
    };
  }, []);

  return state;
}
