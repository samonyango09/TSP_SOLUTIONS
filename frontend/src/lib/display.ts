import type { ChurnStatus, OutletType } from "../api/types";

export const OUTLET_TYPE_LABEL: Record<OutletType, string> = {
  distributor: "Distributor / Wholesaler",
  retail_pharmacy: "Retail Pharmacy",
  hospital: "Hospital",
  hospital_with_pharmacy: "Hospital (with pharmacy)",
};

export const OUTLET_TYPE_COLOR: Record<OutletType, string> = {
  distributor: "#7c3aed",
  retail_pharmacy: "#0891b2",
  hospital: "#64748b",
  hospital_with_pharmacy: "#059669",
};

export const CHURN_LABEL: Record<ChurnStatus, string> = {
  active: "Active",
  at_risk: "At risk",
  churned: "Churned",
  unknown: "Unknown",
};

export const CHURN_COLOR: Record<ChurnStatus, string> = {
  active: "#16a34a",
  at_risk: "#d97706",
  churned: "#dc2626",
  unknown: "#94a3b8",
};

export const CHURN_BADGE_CLASS: Record<ChurnStatus, string> = {
  active: "bg-green-100 text-green-800",
  at_risk: "bg-amber-100 text-amber-800",
  churned: "bg-red-100 text-red-800",
  unknown: "bg-slate-100 text-slate-600",
};

export function formatKes(value: number): string {
  return new Intl.NumberFormat("en-KE", { style: "currency", currency: "KES", maximumFractionDigits: 0 }).format(
    value,
  );
}
