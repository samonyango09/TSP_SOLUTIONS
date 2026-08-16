import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { Outlet, OutletFacets, OutletType } from "../api/types";
import FilterBar from "../components/FilterBar";
import MapView, { type MapPoint } from "../components/MapView";
import { OUTLET_TYPE_COLOR, OUTLET_TYPE_LABEL } from "../lib/display";

// Enough to browse a county/type slice usefully without rendering
// thousands of markers at once - see RoutePlanner's MAX_PROSPECT_MARKERS
// for the same reasoning.
const OUTLET_FETCH_LIMIT = 300;

export default function Prospecting() {
  const [facets, setFacets] = useState<OutletFacets | null>(null);
  const [type, setType] = useState<OutletType | "">("");
  const [county, setCounty] = useState("");
  const [outlets, setOutlets] = useState<Outlet[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.outletFacets().then(setFacets).catch(() => setFacets(null));
  }, []);

  useEffect(() => {
    setLoading(true);
    api
      .listOutlets({ type: type || undefined, county: county || undefined, limit: OUTLET_FETCH_LIMIT })
      .then(setOutlets)
      .catch(() => setOutlets([]))
      .finally(() => setLoading(false));
  }, [type, county]);

  const points: MapPoint[] = outlets
    .filter((o) => o.latitude != null && o.longitude != null)
    .map((o) => ({ id: o.id, lat: o.latitude!, lon: o.longitude!, color: OUTLET_TYPE_COLOR[o.outlet_type], label: o.name }));

  return (
    <div className="space-y-4">
      <FilterBar facets={facets} type={type} county={county} onTypeChange={setType} onCountyChange={setCounty} />

      {loading ? (
        <p className="text-sm text-slate-500">Loading...</p>
      ) : (
        <>
          <p className="text-sm text-slate-500">
            {outlets.length}
            {outlets.length === OUTLET_FETCH_LIMIT ? "+" : ""} outlets{county ? ` in ${county}` : ""}
            {type ? ` · ${OUTLET_TYPE_LABEL[type]}` : ""}
          </p>
          <MapView points={points} height="450px" />
          <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-3">
            {outlets.slice(0, 60).map((o) => (
              <div key={o.id} className="rounded-lg border border-slate-200 bg-white p-3 text-sm">
                <div className="font-medium text-slate-900">{o.name}</div>
                <div className="text-xs text-slate-400">
                  {OUTLET_TYPE_LABEL[o.outlet_type]} · {o.county || "Unknown county"}
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
