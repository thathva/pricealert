import type { Alert, QueueMessage } from "@/types";

interface Metrics {
  queueDepth: number;
  inFlight: number;
  delivered: number;
  failed: number;
  deadLetters: number;
  successRate: number;
  activeAlerts: number;
}

function derive(queue: QueueMessage[], alerts: Alert[]): Metrics {
  const count = (state: string) => queue.filter((m) => m.state === state).length;
  const delivered  = count("delivered");
  const failed     = count("failed");
  const deadLetters = count("dead_letter");
  const total      = queue.length;

  return {
    queueDepth:   count("queued"),
    inFlight:     count("sending"),
    delivered,
    failed:       failed + deadLetters,
    deadLetters,
    successRate:  total > 0 ? Math.round((delivered / total) * 1000) / 10 : 100,
    activeAlerts: alerts.filter((a) => a.active).length,
  };
}

interface MetricCardProps {
  label: string;
  value: string | number;
  sub?: string;
  accent?: string;
}

function MetricCard({ label, value, sub, accent = "text-ink" }: MetricCardProps) {
  return (
    <div className="bg-surface-card border border-border rounded px-4 py-3 flex-1 min-w-0">
      <p className="text-xs text-ink-muted uppercase tracking-widest mb-1">{label}</p>
      <p className={`text-2xl font-semibold ${accent}`}>{value}</p>
      {sub && <p className="text-xs text-ink-dim mt-0.5">{sub}</p>}
    </div>
  );
}

interface Props {
  queue: QueueMessage[];
  alerts: Alert[];
}

export function SystemHealth({ queue, alerts }: Props) {
  const m = derive(queue, alerts);

  const successAccent =
    m.successRate >= 95 ? "text-state-delivered" :
    m.successRate >= 80 ? "text-amber-400" :
    "text-state-failed";

  return (
    <div className="flex gap-3 flex-wrap">
      <MetricCard
        label="Queue Depth"
        value={m.queueDepth}
        sub={m.inFlight > 0 ? `${m.inFlight} in flight` : "idle"}
        accent={m.queueDepth > 10 ? "text-amber-400" : "text-ink"}
      />
      <MetricCard
        label="Success Rate"
        value={`${m.successRate}%`}
        sub={`${m.delivered} delivered · ${m.failed} failed`}
        accent={successAccent}
      />
      <MetricCard
        label="Dead Letters"
        value={m.deadLetters}
        accent={m.deadLetters > 0 ? "text-state-dead_letter" : "text-ink"}
      />
      <MetricCard
        label="Active Alerts"
        value={m.activeAlerts}
        accent="text-state-sending"
      />
    </div>
  );
}
