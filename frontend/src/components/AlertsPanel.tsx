import type { Alert } from "@/types";

function maskPhone(phone: string): string {
  return phone.slice(0, -4).replace(/\d/g, "•") + phone.slice(-4);
}

interface Props {
  alerts: Alert[];
}

export function AlertsPanel({ alerts }: Props) {
  const activeCount = alerts.filter((a) => a.active).length;
  const inactiveCount = alerts.filter((a) => !a.active).length;

  return (
    <div className="bg-surface-card border border-border rounded flex flex-col">
      <div className="px-4 py-3 border-b border-border flex items-center justify-between">
        <p className="text-xs text-ink-muted uppercase tracking-widest">Active Alerts</p>
        <span className="text-xs px-2 py-0.5 rounded-full bg-surface-hover text-state-sending">
          {activeCount} active
        </span>
      </div>

      <div className="overflow-auto flex-1">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-border text-ink-muted">
              <th className="px-4 py-2 text-left font-normal">ID</th>
              <th className="px-4 py-2 text-left font-normal">Phone</th>
              <th className="px-4 py-2 text-left font-normal">Condition</th>
              <th className="px-4 py-2 text-left font-normal">Status</th>
              <th className="px-4 py-2 text-left font-normal">Created</th>
            </tr>
          </thead>
          <tbody>
            {alerts.map((alert) => (
              <tr
                key={alert.id}
                className={`border-b border-border/50 ${!alert.active ? "opacity-40" : "hover:bg-surface-hover"}`}
              >
                <td className="px-4 py-2 text-ink-dim">#{alert.id}</td>
                <td className="px-4 py-2 text-ink-muted">{maskPhone(alert.phone)}</td>
                <td className="px-4 py-2 text-ink">
                  {alert.asset}{" "}
                  <span className="text-ink-muted">{alert.direction}</span>{" "}
                  <span className="text-state-sending">${alert.threshold.toLocaleString()}</span>
                </td>
                <td className="px-4 py-2">
                  <span className={alert.active ? "text-state-delivered" : "text-ink-dim"}>
                    {alert.active ? "● active" : "○ fired"}
                  </span>
                </td>
                <td className="px-4 py-2 text-ink-muted">
                  {new Date(alert.created_at + "Z").toLocaleTimeString()}
                </td>
              </tr>
            ))}
            {alerts.length === 0 && (
              <tr>
                <td colSpan={6} className="px-4 py-6 text-center text-ink-dim">
                  No alerts yet. Text the bot to create one.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {inactiveCount > 0 && (
        <p className="px-4 py-2 text-xs text-ink-dim border-t border-border">
          {inactiveCount} fired alert{inactiveCount !== 1 ? "s" : ""} in history
        </p>
      )}
    </div>
  );
}
