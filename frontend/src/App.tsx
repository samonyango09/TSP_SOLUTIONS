import { useEffect, useState } from "react";
import { NavLink, Route, Routes } from "react-router-dom";
import { api } from "./api/client";
import CustomerDetail from "./pages/CustomerDetail";
import MatchReview from "./pages/MatchReview";
import Prospecting from "./pages/Prospecting";
import RoutePlanner from "./pages/RoutePlanner";

const NAV_LINK_CLASS = "rounded-md px-3 py-1.5 text-sm font-medium text-slate-600 hover:bg-slate-100 aria-[current=page]:bg-slate-900 aria-[current=page]:text-white";

function AppShell() {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto max-w-6xl px-6 py-4">
          <h1 className="text-lg font-semibold">TSP Solutions</h1>
          <p className="text-sm text-slate-500">Pharma sales route planning, prospecting, and churn tracking</p>
          <nav className="mt-3 flex gap-2">
            <NavLink to="/route-planner" className={NAV_LINK_CLASS}>
              Route Planner
            </NavLink>
            <NavLink to="/prospecting" className={NAV_LINK_CLASS}>
              Prospecting
            </NavLink>
            <NavLink to="/match-review" className={NAV_LINK_CLASS}>
              Match Review
            </NavLink>
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-6 py-8">
        <Routes>
          <Route path="/" element={<RoutePlanner />} />
          <Route path="/route-planner" element={<RoutePlanner />} />
          <Route path="/prospecting" element={<Prospecting />} />
          <Route path="/match-review" element={<MatchReview />} />
          <Route path="/customers/:id" element={<CustomerDetail />} />
        </Routes>
      </main>
    </div>
  );
}

function LoginScreen({ onLoggedIn }: { onLoggedIn: () => void }) {
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await api.login(password);
      onLoggedIn();
    } catch {
      setError("Incorrect password");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50">
      <form onSubmit={handleSubmit} className="w-72 space-y-3 rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <h1 className="text-base font-semibold text-slate-900">TSP Solutions</h1>
        <input
          type="password"
          autoFocus
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full rounded-md border border-slate-300 px-3 py-1.5 text-sm"
        />
        {error && <p className="text-xs text-red-600">{error}</p>}
        <button type="submit" disabled={submitting} className="w-full rounded-md bg-slate-900 px-3 py-1.5 text-sm font-medium text-white disabled:opacity-50">
          {submitting ? "Signing in..." : "Sign in"}
        </button>
      </form>
    </div>
  );
}

export default function App() {
  const [authRequired, setAuthRequired] = useState(false);
  const [authenticated, setAuthenticated] = useState(false);
  const [checked, setChecked] = useState(false);

  useEffect(() => {
    api
      .authStatus()
      .then((s) => {
        setAuthRequired(s.auth_required);
        setAuthenticated(s.authenticated);
      })
      .catch(() => {
        // Backend unreachable - fall through to the app shell so requests
        // fail visibly per-page rather than getting stuck on a blank screen.
        setAuthenticated(true);
      })
      .finally(() => setChecked(true));
  }, []);

  if (!checked) return null;
  if (authRequired && !authenticated) return <LoginScreen onLoggedIn={() => setAuthenticated(true)} />;
  return <AppShell />;
}
