# Frontend tutorial

## Stack

- **React 19 + TypeScript + Vite** - Vite is the dev server/bundler (fast HMR, no webpack config).
- **react-router-dom** - client-side routing (`App.tsx`'s `<Routes>`), so navigating between pages
  doesn't reload the whole app.
- **Tailwind CSS** - utility classes directly in JSX (`className="rounded-lg border ..."`) instead
  of separate CSS files per component. `tailwind.config.js` + `postcss.config.js` wire it into the
  Vite build.
- **axios** - the HTTP client (`src/api/client.ts`), configured with `withCredentials: true` so the
  auth session cookie is sent on every request.
- **react-leaflet** - React bindings for Leaflet, the map library.

## The API layer (`src/api/`)

`types.ts` mirrors the backend's Pydantic schemas by hand (not code-generated) - for a project this
size, keeping one TypeScript file in sync manually is simpler than adding an OpenAPI-to-TS codegen
step to the build. `client.ts` wraps every endpoint in one typed function inside an `api` object
(`api.listOutlets(...)`, `api.planRoute(...)`, etc.) so a component never constructs a URL string
or casts a response type itself - one place to update if a backend route changes.

## Auth flow (`App.tsx`)

On mount, `App` calls `api.authStatus()`. If the backend has no `APP_PASSWORD` configured,
`auth_required` is `false` and the app renders straight through - this is what makes local dev
(`npm run dev` against a backend with no `.env`) work without ever seeing a login screen. If auth
*is* required and the session cookie isn't valid, `LoginScreen` renders instead of the app shell;
submitting the password calls `api.login()`, which sets the cookie, and `onLoggedIn()` flips local
state to render the real app - no page reload needed, since the cookie is already there for the
next API call.

## Why `CircleMarker`, not `Marker`

`MapView.tsx` renders every point as a Leaflet `CircleMarker` (a plain colored circle) instead of
the default `Marker` (a pin icon). This sidesteps a well-known Leaflet-in-a-bundler issue: the
default marker icon is loaded from image files at specific relative paths that don't resolve
correctly once Vite bundles everything, and normally requires manually re-pointing Leaflet's
default icon URLs. Using `CircleMarker` avoids that class of problem entirely, and as a bonus makes
it trivial to color-code markers by outlet type or churn status (see `src/lib/display.ts` for the
color/label lookup tables shared across pages).

## Why prospects are capped on the map (`RoutePlanner.tsx`)

A route corridor easily returns several thousand candidate outlets (the backend already sorts them
closest-first). Rendering all of them as individual Leaflet markers doesn't scale in a browser -
`MAX_PROSPECT_MARKERS` caps how many actually become map markers, while the full count is still
shown in the list and in the "showing closest N of M" note. This isn't a workaround for a bug; it's
a deliberate scale decision documented here because it's easy to mistake for one. Marker clustering
(e.g. `react-leaflet-cluster`) would let all of them render usefully at once and is a natural
follow-up - see `05-future-work.md`.

## Debounced search (`LocationInput.tsx`)

The from/to autocomplete doesn't fire a request on every keystroke - it waits 250ms after the user
stops typing (`setTimeout` in a `useEffect`, cleared and re-set on every keystroke via the
`clearTimeout` in the effect's cleanup function). This is the standard debounce pattern: without
it, typing "Nairobi" would fire seven separate search requests, one per character, most of which
would be thrown away before they even finished.

## Quarterly sales chart (`CustomerDetail.tsx`)

`QuarterlyChart` is a small inline component, not a chart library - it renders one `<div>` per
quarter with `height` set to a percentage of that quarter's value relative to the maximum quarter
(`(value / max) * 100%`), which is enough to show relative sales trends at a glance without adding
a charting dependency (Chart.js, Recharts, etc.) for what is otherwise one bar chart on one page.
If more chart types are needed later, that's the point to reconsider adding a real charting
library - see `05-future-work.md`.
