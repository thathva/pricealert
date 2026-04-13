import type { Prices } from "@/types";

const ASSETS = ["BTC", "ETH", "SOL", "AVAX", "BNB"] as const;

function fmt(price: number): string {
  return `$${price.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

interface Props {
  prices: Prices;
}

export function PriceTicker({ prices }: Props) {
  return (
    <div className="bg-surface-card border border-border rounded px-4 py-3">
      <p className="text-xs text-ink-muted uppercase tracking-widest mb-3">Live Prices (simulated)</p>
      <div className="flex gap-6 flex-wrap">
        {ASSETS.map((asset) => (
          <div key={asset} className="flex flex-col">
            <span className="text-xs text-ink-muted">{asset}</span>
            <span className="text-sm font-semibold text-ink">
              {prices[asset] != null ? fmt(prices[asset]) : "—"}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
