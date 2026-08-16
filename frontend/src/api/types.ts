export type OutletSource = "ppb_pharma" | "kmhfr_hospital";

export type OutletType = "distributor" | "retail_pharmacy" | "hospital" | "hospital_with_pharmacy";

export type ChurnStatus = "active" | "at_risk" | "churned" | "unknown";

export type MatchStatus = "suggested" | "auto_confirmed" | "manual_confirmed" | "rejected";

export type LocationKind = "town" | "county";

export interface Outlet {
  id: string;
  source: OutletSource;
  outlet_type: OutletType;
  name: string;
  county: string;
  town: string;
  latitude: number | null;
  longitude: number | null;
  license_status: string;
  has_pharmacy_service: boolean;
}

export interface OutletWithDistance extends Outlet {
  distance_km: number | null;
}

export interface Customer {
  id: string;
  name: string;
  total_sales_value: number;
  num_orders: number;
  average_order_value: number;
  avg_purchase_interval_days: number | null;
  last_order_date: string | null;
  churn_status: ChurnStatus;
  days_since_last_order: number | null;
}

export interface CustomerWithLocation extends Customer {
  outlet: Outlet | null;
  distance_km: number | null;
}

export interface MatchedOutlet {
  outlet: Outlet;
  confidence: number;
  status: MatchStatus;
}

export interface CustomerDetail extends Customer {
  first_order_date: string | null;
  duration_as_customer_days: number | null;
  yearly_sales: Record<string, number>;
  quarterly_sales: Record<string, number>;
  matched_outlets: MatchedOutlet[];
}

export interface RoutePlanResponse {
  from_location: string;
  to_location: string;
  route_points: [number, number][];
  buffer_km: number;
  active_customers: CustomerWithLocation[];
  at_risk_customers: CustomerWithLocation[];
  churned_customers: CustomerWithLocation[];
  prospects: OutletWithDistance[];
}

export interface MatchRead {
  id: string;
  customer_id: string;
  customer_name: string;
  outlet_id: string;
  outlet_name: string;
  outlet_county: string;
  confidence: number;
  status: MatchStatus;
}

export interface LocationSuggestion {
  name: string;
  kind: LocationKind;
  latitude: number;
  longitude: number;
  outlet_count: number;
}

export interface OutletFacets {
  types: OutletType[];
  counties: string[];
}

export interface AuthStatus {
  auth_required: boolean;
  authenticated: boolean;
}
