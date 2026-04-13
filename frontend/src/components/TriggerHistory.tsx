import type { TriggerRecord } from "@/types";

interface Props {
  history: TriggerRecord[];
}

export function TriggerHistory({ history }: Props) {
  return (
    <div className="bg-surface-card border border-border rounded flex flex-col">
      <div className="px-4 py-3 border-b border-border">
        <p className="text-xs text-ink-muted uppercase tracking-widest">Trigger History</p>
      </div>

      <div className="overflow-auto flex-1 max-h-80">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-border text-ink-muted sticky top-0 bg-surface-card">
              <th className="px-4 py-2 text-left font-normal">Asset</th>
              <th className="px-4 py-2 text-left font-normal">Condition → Price</th>
              <th className="px-4 py-2 text-left font-normal">Phone</th>
              <th className="px-4 py-2 text-left font-normal">Fired at</th>
            </tr>
          </thead>
          <tbody>
            {history.map((r) => (
              <tr key={r.id} className="border-b border-border/40 hover:bg-surface-hover">
                <td className="px-4 py-2 font-semibold text-ink">{r.asset}</td>
                <td className="px-4 py-2 text-state-delivered">
                  {r.direction} ${r.threshold.toLocaleString()} @ ${r.price_at_trigger.toLocaleString()}
                </td>
                <td className="px-4 py-2 text-ink-muted">
                  {"•".repeat(r.phone.length - 4) + r.phone.slice(-4)}
                </td>
                <td className="px-4 py-2 text-ink-dim whitespace-nowrap">
                  {new Date(r.triggered_at + "Z").toLocaleTimeString()}
                </td>
              </tr>
            ))}
            {history.length === 0 && (
              <tr>
                <td colSpan={4} className="px-4 py-6 text-center text-ink-dim">No triggers yet.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
