"use client";

import { useWebSocket } from "@/hooks/useWebSocket";
import { AlertsPanel } from "./AlertsPanel";
import { PriceTicker } from "./PriceTicker";
import { QueueLog } from "./QueueLog";
import { SimControls } from "./SimControls";
import { SystemHealth } from "./SystemHealth";
import { TriggerHistory } from "./TriggerHistory";

export function Dashboard() {
  const { alerts, queue, prices, history, connected } = useWebSocket();

  return (
    <main className="min-h-screen p-6 flex flex-col gap-4 max-w-screen-2xl mx-auto">
      <div className="flex items-center justify-between border-b border-border pb-4">
        <div>
          <h1 className="text-lg font-semibold text-ink">Linq Alert System</h1>
          <p className="text-xs text-ink-muted mt-0.5">Messaging infrastructure dashboard</p>
        </div>
        <div className={`flex items-center gap-2 text-xs ${connected ? "text-state-delivered" : "text-state-failed"}`}>
          <span className={`inline-block w-2 h-2 rounded-full ${connected ? "bg-state-delivered blink" : "bg-state-failed"}`} />
          {connected ? "live" : "reconnecting…"}
        </div>
      </div>

      <SystemHealth queue={queue} alerts={alerts} />
      <PriceTicker prices={prices} />

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        <div className="xl:col-span-2 flex flex-col gap-4">
          <AlertsPanel alerts={alerts} />
          <QueueLog messages={queue} />
        </div>
        <div className="flex flex-col gap-4">
          <SimControls />
          <TriggerHistory history={history} />
        </div>
      </div>
    </main>
  );
}
