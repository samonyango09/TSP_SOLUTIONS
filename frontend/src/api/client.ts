import axios from "axios";
import type {
  AuthStatus,
  CustomerDetail,
  CustomerWithLocation,
  LocationSuggestion,
  MatchRead,
  MatchStatus,
  Outlet,
  OutletFacets,
  OutletType,
  RoutePlanResponse,
} from "./types";

const BASE_URL = "http://127.0.0.1:8000";

// withCredentials so the shared-password session cookie (set by /api/auth/login)
// is sent on every request - the backend gates every router except /api/auth
// and /api/health behind it.
const client = axios.create({ baseURL: BASE_URL, withCredentials: true });

export const api = {
  baseUrl: BASE_URL,

  authStatus: () => client.get<AuthStatus>("/api/auth/status").then((r) => r.data),
  login: (password: string) => client.post<{ authenticated: boolean }>("/api/auth/login", { password }).then((r) => r.data),
  logout: () => client.post("/api/auth/logout").then((r) => r.data),

  listOutlets: (params: { type?: OutletType; county?: string; limit?: number; offset?: number }) =>
    client.get<Outlet[]>("/api/outlets", { params }).then((r) => r.data),
  outletFacets: () => client.get<OutletFacets>("/api/outlets/facets").then((r) => r.data),

  listCustomers: (params: { status?: string; county?: string; limit?: number; offset?: number }) =>
    client.get<CustomerWithLocation[]>("/api/customers", { params }).then((r) => r.data),
  getCustomer: (id: string) => client.get<CustomerDetail>(`/api/customers/${id}`).then((r) => r.data),

  planRoute: (from: string, to: string, bufferKm?: number) =>
    client
      .get<RoutePlanResponse>("/api/route-plan", { params: { from, to, buffer_km: bufferKm } })
      .then((r) => r.data),

  searchLocations: (q: string) =>
    client.get<LocationSuggestion[]>("/api/locations/search", { params: { q } }).then((r) => r.data),

  listMatches: (status: MatchStatus = "suggested") =>
    client.get<MatchRead[]>("/api/matches", { params: { status } }).then((r) => r.data),
  confirmMatch: (id: string) => client.post<MatchRead>(`/api/matches/${id}/confirm`).then((r) => r.data),
  rejectMatch: (id: string) => client.post<MatchRead>(`/api/matches/${id}/reject`).then((r) => r.data),
};
