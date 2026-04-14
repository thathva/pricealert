"use client";

import { useState } from "react";

const ASSETS = ["BTC", "ETH", "SOL", "AVAX", "BNB"] as const;

export function SimControls() {
  const [overrides, setOverrides] = useState<Record<string, string>>({});
  const [overrideStatus, setOverrideStatus] = useState<string | null>(null);

  async function applyOverride(asset: string) {
    const raw = overrides[asset];
    const price = parseFloat(raw);
    if (isNaN(price) || price <= 0) return;

    setOverrideStatus(`Setting ${asset} to $${price}…`);
    try {
      const res = await fetch("/api/sim/prices", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ asset, price }),
      });
      if (!res.ok) {
        setOverrideStatus(`Error: server returned ${res.status}`);
      } else {
        setOverrideStatus(`${asset} set to $${price} - alerts evaluated`);
      }
    } catch {
      setOverrideStatus("Error: could not reach server");
    }
    setTimeout(() => setOverrideStatus(null), 3000);
  }

  return (
    <div className="bg-surface-card border border-border rounded p-4 flex flex-col gap-5">
      <p className="text-xs text-ink-muted uppercase tracking-widest">Simulation Controls</p>

      <div className="flex flex-col gap-3">
        <p className="text-sm text-ink">Price Override</p>
        <p className="text-xs text-ink-muted -mt-2">Set a price to instantly evaluate alert thresholds.</p>
        {ASSETS.map((asset) => (
          <div key={asset} className="flex items-center gap-2">
            <span className="text-xs text-ink-muted w-10 shrink-0">{asset}</span>
            <input
              type="number"
              placeholder="price"
              value={overrides[asset] ?? ""}
              onChange={(e) => setOverrides((o) => ({ ...o, [asset]: e.target.value }))}
              onKeyDown={(e) => e.key === "Enter" && applyOverride(asset)}
              className="flex-1 bg-surface-hover border border-border rounded px-2 py-1 text-xs text-ink placeholder-ink-dim focus:outline-none focus:border-state-sending"
            />
            <button
              onClick={() => applyOverride(asset)}
              className="text-xs px-2 py-1 border border-border rounded text-ink-muted hover:border-state-sending hover:text-state-sending transition-colors"
            >
              Set
            </button>
          </div>
        ))}
        {overrideStatus && <p className="text-xs text-state-delivered">{overrideStatus}</p>}
      </div>
    </div>
  );
}
