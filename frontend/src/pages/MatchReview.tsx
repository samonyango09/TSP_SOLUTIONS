import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { MatchRead } from "../api/types";

export default function MatchReview() {
  const [matches, setMatches] = useState<MatchRead[]>([]);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState<string | null>(null);

  function load() {
    setLoading(true);
    api
      .listMatches("suggested")
      .then(setMatches)
      .finally(() => setLoading(false));
  }

  useEffect(load, []);

  async function resolve(id: string, action: "confirm" | "reject") {
    setBusyId(id);
    try {
      await (action === "confirm" ? api.confirmMatch(id) : api.rejectMatch(id));
      setMatches((prev) => prev.filter((m) => m.id !== id));
    } finally {
      setBusyId(null);
    }
  }

  if (loading) return <p className="text-sm text-slate-500">Loading...</p>;

  return (
    <div className="space-y-3">
      <p className="text-sm text-slate-500">
        {matches.length} customer-to-outlet matches need review. These scored below the auto-confirm threshold - confirm
        the ones that are genuinely the same business, reject the rest.
      </p>
      {matches.length === 0 && <p className="text-sm text-slate-400">Nothing to review right now.</p>}
      <div className="space-y-2">
        {matches.map((m) => (
          <div key={m.id} className="flex items-center justify-between gap-4 rounded-lg border border-slate-200 bg-white p-3">
            <div className="min-w-0 flex-1">
              <div className="text-sm font-medium text-slate-900">{m.customer_name}</div>
              <div className="text-xs text-slate-400">
                &rarr; {m.outlet_name} {m.outlet_county && `(${m.outlet_county})`} &middot; {m.confidence.toFixed(0)}%
                confidence
              </div>
            </div>
            <div className="flex shrink-0 gap-2">
              <button
                disabled={busyId === m.id}
                onClick={() => resolve(m.id, "confirm")}
                className="rounded-md bg-green-600 px-3 py-1 text-xs font-medium text-white disabled:opacity-50"
              >
                Confirm
              </button>
              <button
                disabled={busyId === m.id}
                onClick={() => resolve(m.id, "reject")}
                className="rounded-md bg-slate-200 px-3 py-1 text-xs font-medium text-slate-700 disabled:opacity-50"
              >
                Reject
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
