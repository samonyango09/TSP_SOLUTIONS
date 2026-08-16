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

// Set VITE_API_BASE_URL in the hosting provider's project settings for a
// deployed build; falls back to the local backend for `npm run dev`.
const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

const TOKEN_STORAGE_KEY = "tsp_auth_token";

// Auth is a bearer token (Authorization header), not a cookie - the
// frontend and backend are deployed on different sites (Vercel/Render),
// and browsers' third-party-cookie blocking silently drops cross-site
// cookies even with SameSite=None; Secure set correctly. See app/auth.py's
// module docstring on the backend for how that was confirmed, not assumed.
function getToken(): string | null {
  return localStorage.getItem(TOKEN_STORAGE_KEY);
}

function setToken(token: string | null): void {
  if (token) localStorage.setItem(TOKEN_STORAGE_KEY, token);
  else localStorage.removeItem(TOKEN_STORAGE_KEY);
}

const client = axios.create({ baseURL: BASE_URL });

client.interceptors.request.use((config) => {
  const token = getToken();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export const api = {
  baseUrl: BASE_URL,

  authStatus: () => client.get<AuthStatus>("/api/auth/status").then((r) => r.data),
  login: (password: string) =>
    client.post<{ authenticated: boolean; token?: string }>("/api/auth/login", { password }).then((r) => {
      setToken(r.data.token ?? null);
      return r.data;
    }),
  logout: () => setToken(null),

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
