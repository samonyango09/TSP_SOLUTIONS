import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api/client";
import type { CustomerDetail as CustomerDetailType } from "../api/types";
import MapView, { type MapPoint } from "../components/MapView";
import { CHURN_BADGE_CLASS, CHURN_LABEL, formatKes, OUTLET_TYPE_COLOR, OUTLET_TYPE_LABEL } from "../lib/display";

export default function CustomerDetail() {
  const { id } = useParams<{ id: string }>();
  const [customer, setCustomer] = useState<CustomerDetailType | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    api
      .getCustomer(id)
      .then(setCustomer)
      .catch(() => setError("Customer not found"));
  }, [id]);

  if (error) return <p className="text-sm text-red-600">{error}</p>;
  if (!customer) return <p className="text-sm text-slate-500">Loading...</p>;

  const points: MapPoint[] = customer.matched_outlets
    .filter((m) => m.outlet.latitude != null && m.outlet.longitude != null)
    .map((m) => ({
      id: m.outlet.id,
      lat: m.outlet.latitude!,
      lon: m.outlet.longitude!,
      color: OUTLET_TYPE_COLOR[m.outlet.outlet_type],
      label: `${m.outlet.name} (${m.status}, ${m.confidence.toFixed(0)}%)`,
    }));

  return (
    <div className="space-y-6">
      <Link to="/route-planner" className="text-sm text-slate-500 hover:underline">
        &larr; Back
      </Link>

      <div className="flex items-start justify-between">
        <h2 className="text-xl font-semibold text-slate-900">{customer.name}</h2>
        <span className={`rounded-full px-2.5 py-1 text-xs font-medium ${CHURN_BADGE_CLASS[customer.churn_status]}`}>
          {CHURN_LABEL[customer.churn_status]}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <Metric label="Total sales" value={formatKes(customer.total_sales_value)} />
        <Metric label="Orders" value={String(customer.num_orders)} />
        <Metric label="Avg order value" value={formatKes(customer.average_order_value)} />
        <Metric
          label="Avg purchase interval"
          value={customer.avg_purchase_interval_days ? `${customer.avg_purchase_interval_days.toFixed(0)} days` : "-"}
        />
        <Metric label="First order" value={customer.first_order_date ?? "-"} />
        <Metric label="Last order" value={customer.last_order_date ?? "-"} />
        <Metric label="Days since last order" value={customer.days_since_last_order != null ? String(customer.days_since_last_order) : "-"} />
        <Metric
          label="Customer for"
          value={customer.duration_as_customer_days ? `${Math.round(customer.duration_as_customer_days / 365)} yrs` : "-"}
        />
      </div>

      <QuarterlyChart quarterlySales={customer.quarterly_sales} />

      <div>
        <h3 className="mb-2 text-sm font-semibold text-slate-700">Matched outlets ({customer.matched_outlets.length})</h3>
        {points.length > 0 && <MapView points={points} height="350px" />}
        <div className="mt-3 space-y-2">
          {customer.matched_outlets.map((m) => (
            <div key={m.outlet.id} className="flex items-center justify-between rounded-lg border border-slate-200 bg-white p-3 text-sm">
              <div>
                <div className="font-medium text-slate-900">{m.outlet.name}</div>
                <div className="text-xs text-slate-400">
                  {OUTLET_TYPE_LABEL[m.outlet.outlet_type]} · {m.outlet.county || "Unknown county"}
                </div>
              </div>
              <div className="text-right text-xs">
                <div className="font-medium text-slate-600">{m.confidence.toFixed(0)}% confidence</div>
                <div className="text-slate-400">{m.status.replace("_", " ")}</div>
              </div>
            </div>
          ))}
          {customer.matched_outlets.length === 0 && <p className="text-sm text-slate-400">No outlet matches found or confirmed yet.</p>}
        </div>
      </div>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-3">
      <div className="text-xs text-slate-400">{label}</div>
      <div className="mt-0.5 font-medium text-slate-900">{value}</div>
    </div>
  );
}

function QuarterlyChart({ quarterlySales }: { quarterlySales: Record<string, number> }) {
  const entries = Object.entries(quarterlySales).sort(([a], [b]) => a.localeCompare(b));
  if (entries.length === 0) return null;
  const max = Math.max(...entries.map(([, v]) => v), 1);

  return (
    <div>
      <h3 className="mb-2 text-sm font-semibold text-slate-700">Quarterly sales</h3>
      <div className="flex items-end gap-1 overflow-x-auto rounded-lg border border-slate-200 bg-white p-3" style={{ height: 160 }}>
        {entries.map(([quarter, value]) => (
          <div key={quarter} className="flex h-full min-w-10 flex-col items-center justify-end gap-1" title={`${quarter}: ${formatKes(value)}`}>
            <div className="w-full rounded-t bg-cyan-600" style={{ height: `${(value / max) * 100}%` }} />
            <span className="whitespace-nowrap text-[10px] text-slate-400">{quarter}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
