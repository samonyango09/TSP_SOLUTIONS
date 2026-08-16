import { useState } from "react";
import { api } from "../api/client";
import type { RoutePlanResponse } from "../api/types";
import CustomerCard from "../components/CustomerCard";
import LocationInput from "../components/LocationInput";
import MapView, { type MapPoint } from "../components/MapView";
import { CHURN_COLOR, OUTLET_TYPE_COLOR } from "../lib/display";

// Rendering every prospect as its own map marker doesn't scale - a wide
// corridor easily returns several thousand candidate outlets, which would
// freeze the browser as individual Leaflet markers. They're already sorted
// closest-first by the backend, so capping here just means "show the
// nearest N" rather than losing anything meaningful.
const MAX_PROSPECT_MARKERS = 150;

export default function RoutePlanner() {
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  const [bufferKm, setBufferKm] = useState(15);
  const [result, setResult] = useState<RoutePlanResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handlePlan(e: React.FormEvent) {
    e.preventDefault();
    if (!from.trim() || !to.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const data = await api.planRoute(from.trim(), to.trim(), bufferKm);
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not plan that route");
      setResult(null);
    } finally {
      setLoading(false);
    }
  }

  const points: MapPoint[] = result
    ? [
        ...result.active_customers.map((c) => toPoint(c.id, c.outlet, CHURN_COLOR.active, c.name)),
        ...result.at_risk_customers.map((c) => toPoint(c.id, c.outlet, CHURN_COLOR.at_risk, c.name)),
        ...result.churned_customers.map((c) => toPoint(c.id, c.outlet, CHURN_COLOR.churned, c.name)),
        ...result.prospects.slice(0, MAX_PROSPECT_MARKERS).map((o) => ({
          id: o.id,
          lat: o.latitude!,
          lon: o.longitude!,
          color: OUTLET_TYPE_COLOR[o.outlet_type],
          label: `${o.name} (prospect)`,
        })),
      ].filter((p): p is MapPoint => p !== null)
    : [];

  return (
    <div className="space-y-6">
      <form onSubmit={handlePlan} className="flex flex-wrap items-end gap-4 rounded-lg border border-slate-200 bg-white p-4">
        <div className="w-48"><LocationInput label="From" value={from} onChange={setFrom} /></div>
        <div className="w-48"><LocationInput label="To" value={to} onChange={setTo} /></div>
        <div className="w-32">
          <label className="mb-1 block text-xs font-medium text-slate-500">Corridor (km)</label>
          <input
            type="number"
            min={1}
            max={100}
            className="w-full rounded-md border border-slate-300 px-3 py-1.5 text-sm"
            value={bufferKm}
            onChange={(e) => setBufferKm(Number(e.target.value))}
          />
        </div>
        <button type="submit" disabled={loading} className="rounded-md bg-slate-900 px-4 py-1.5 text-sm font-medium text-white disabled:opacity-50">
          {loading ? "Planning..." : "Plan route"}
        </button>
      </form>

      {error && <p className="text-sm text-red-600">{error}</p>}

      {result && (
        <>
          <MapView points={points} routeLine={result.route_points} height="450px" />

          <div className="grid grid-cols-1 gap-6 md:grid-cols-4">
            <CustomerColumn title="Active" customers={result.active_customers} />
            <CustomerColumn title="At risk" customers={result.at_risk_customers} />
            <CustomerColumn title="Churned" customers={result.churned_customers} />
            <div>
              <h3 className="mb-2 text-sm font-semibold text-slate-700">
                Prospects ({result.prospects.length})
                {result.prospects.length > MAX_PROSPECT_MARKERS && (
                  <span className="ml-1 font-normal text-slate-400">showing closest {MAX_PROSPECT_MARKERS} on map</span>
                )}
              </h3>
              <div className="max-h-96 space-y-2 overflow-y-auto pr-1">
                {result.prospects.slice(0, 50).map((o) => (
                  <div key={o.id} className="rounded-lg border border-slate-200 bg-white p-3 text-sm">
                    <div className="font-medium text-slate-900">{o.name}</div>
                    <div className="text-xs text-slate-400">
                      {o.county || "Unknown county"} · {o.distance_km?.toFixed(1)} km from route
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

function CustomerColumn({ title, customers }: { title: string; customers: RoutePlanResponse["active_customers"] }) {
  return (
    <div>
      <h3 className="mb-2 text-sm font-semibold text-slate-700">
        {title} ({customers.length})
      </h3>
      <div className="max-h-96 space-y-2 overflow-y-auto pr-1">
        {customers.map((c) => (
          <CustomerCard key={c.id} customer={c} />
        ))}
      </div>
    </div>
  );
}

function toPoint(id: string, outlet: { latitude: number | null; longitude: number | null } | null, color: string, label: string): MapPoint | null {
  if (!outlet || outlet.latitude == null || outlet.longitude == null) return null;
  return { id, lat: outlet.latitude, lon: outlet.longitude, color, label };
}
