import type { MessageState, QueueMessage } from "@/types";

const STATE_STYLES: Record<MessageState, string> = {
  queued:      "text-state-queued bg-state-queued/10",
  sending:     "text-state-sending bg-state-sending/10 blink",
  delivered:   "text-state-delivered bg-state-delivered/10",
  failed:      "text-state-failed bg-state-failed/10",
  dead_letter: "text-state-dead_letter bg-state-dead_letter/10",
};

const STATE_LABELS: Record<MessageState, string> = {
  queued:      "queued",
  sending:     "● sending",
  delivered:   "delivered",
  failed:      "failed",
  dead_letter: "dead letter",
};

interface Props {
  messages: QueueMessage[];
}

export function QueueLog({ messages }: Props) {
  const queued = messages.filter((m) => m.state === "queued").length;
  const inFlight = messages.filter((m) => m.state === "sending").length;

  return (
    <div className="bg-surface-card border border-border rounded flex flex-col">
      <div className="px-4 py-3 border-b border-border flex items-center justify-between">
        <p className="text-xs text-ink-muted uppercase tracking-widest">Message Queue</p>
        <span className="text-xs text-ink-dim">
          {queued} queued · {inFlight} in flight
        </span>
      </div>

      <div className="overflow-auto flex-1 max-h-80">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-border text-ink-muted sticky top-0 bg-surface-card">
              <th className="px-4 py-2 text-left font-normal">ID</th>
              <th className="px-4 py-2 text-left font-normal">State</th>
              <th className="px-4 py-2 text-left font-normal">Retries</th>
              <th className="px-4 py-2 text-left font-normal">Body</th>
              <th className="px-4 py-2 text-left font-normal">Updated</th>
            </tr>
          </thead>
          <tbody>
            {messages.map((msg) => (
              <tr key={msg.id} className="border-b border-border/40 hover:bg-surface-hover">
                <td className="px-4 py-2 text-ink-dim">#{msg.id}</td>
                <td className="px-4 py-2">
                  <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${STATE_STYLES[msg.state]}`}>
                    {STATE_LABELS[msg.state]}
                  </span>
                </td>
                <td className="px-4 py-2 text-center">
                  {msg.retry_count > 0
                    ? <span className="text-amber-400">{msg.retry_count}×</span>
                    : <span className="text-ink-dim">-</span>}
                </td>
                <td className="px-4 py-2 text-ink-muted max-w-xs truncate" title={msg.body}>
                  {msg.body}
                </td>
                <td className="px-4 py-2 text-ink-dim whitespace-nowrap">
                  {new Date(msg.updated_at + "Z").toLocaleTimeString()}
                </td>
              </tr>
            ))}
            {messages.length === 0 && (
              <tr>
                <td colSpan={5} className="px-4 py-6 text-center text-ink-dim">Queue is empty.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
