import { Link } from "react-router-dom";
import type { CustomerWithLocation } from "../api/types";
import { CHURN_BADGE_CLASS, CHURN_LABEL, formatKes } from "../lib/display";

export default function CustomerCard({ customer }: { customer: CustomerWithLocation }) {
  return (
    <Link
      to={`/customers/${customer.id}`}
      className="block rounded-lg border border-slate-200 bg-white p-3 hover:border-slate-300 hover:shadow-sm"
    >
      <div className="flex items-start justify-between gap-2">
        <div className="font-medium text-slate-900">{customer.name}</div>
        <span className={`shrink-0 rounded-full px-2 py-0.5 text-xs font-medium ${CHURN_BADGE_CLASS[customer.churn_status]}`}>
          {CHURN_LABEL[customer.churn_status]}
        </span>
      </div>
      <div className="mt-1 text-sm text-slate-500">
        {formatKes(customer.total_sales_value)} total &middot; {customer.num_orders} orders
      </div>
      <div className="mt-0.5 text-xs text-slate-400">
        {customer.outlet ? `${customer.outlet.name}${customer.outlet.county ? ` (${customer.outlet.county})` : ""}` : "No location on file"}
        {customer.distance_km != null && ` · ${customer.distance_km.toFixed(1)} km from route`}
      </div>
    </Link>
  );
}
