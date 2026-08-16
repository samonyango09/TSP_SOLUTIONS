# Future work

Deliberately not built in the MVP, with the reasoning for waiting - not a backlog of things that
were simply forgotten.

## AI sales assistant (RAG / MCP / agent)

A natural next feature: "which churned Meru accounts are worth revisiting this week" answered in
plain language, or an agent that runs the route-plan -> prospect -> draft-outreach flow end to end.
Not built now because the MVP's structured UI (Route Planner, Prospecting, Match Review) already
answers the brief's stated questions directly and cheaply - an LLM layer is worth adding once
there's a real question the structured UI can't answer well (open-ended "what should I do today"
synthesis across customers, say), not before.

When it's time, two working patterns already exist in this workspace to build from rather than
starting from scratch:

- `Agentic Workflow/AGENTIC PRODUCT REGISTRATION/backend/app/agent/` - a Claude Agent SDK
  orchestrator with a tool server, gated approval pattern, and streaming activity log over SSE.
  The gating pattern (`agent/gates.py`) is directly relevant if an agent here were ever given
  write access to customer/outlet data, not just read access.
- `MCP SERVER SETUP/` - a minimal MCP client/server example, useful as a starting point for
  exposing this app's data (customers, outlets, route-plan) as MCP tools/resources that a Claude
  conversation (or any MCP-compatible client) could query directly.

A reasonable first cut: an MCP server wrapping the existing `/api/customers`, `/api/outlets`, and
`/api/route-plan` endpoints as tools, with no new agent orchestration needed - the value is in
exposing the data, not in adding autonomy on day one.

## ML churn model

The current rule (`app/churn.py` - days-since-last-order normalized by the customer's own average
purchase interval) directly satisfies the brief's stated requirement and needs no training data.
A learned model would need labeled outcomes (accounts confirmed lost, not just inactive) to
outperform it, which doesn't exist yet. Worth revisiting once there's a season or two of
confirmed-churn history to train against - at that point, a simple gradient-boosted classifier
(scikit-learn or XGBoost) over purchase-pattern features (interval trend, order-size trend,
seasonality) would be a reasonable next step, not a deep model.

## Matching precision

The distinctive-token guard (see `00-discovery-and-design.md` and
`app/etl/match_customers.py`) is a large improvement over plain fuzzy scoring, but it's still a
heuristic - short or coincidentally-overlapping brand names can still produce a plausible-looking
wrong suggestion (caught in the Match Review queue, not silently accepted, but still worth
tightening). If the review queue proves too large in practice, options in rough order of effort:
tightening the generic-word stoplist further from real review-queue data, weighting a match by how
many of the customer's tokens matched (not just whether at least one did), or - if the underlying
data source ever includes it - matching on a registration/license number instead of a name, which
would sidestep fuzzy matching for that portion of customers entirely.

## Deduping PPB vs. KMHFR hospital entries

`Outlet.source` distinguishes the PPB pharma register from the KMHFR hospital register, but a
physical hospital that appears in both isn't currently deduplicated - it would show up as two
separate map markers. Not fixed now because there's no reliable shared key between the two
registers (name matching would have the same false-positive/negative issues covered in the
discovery doc) - worth a dedicated pass if duplicate markers prove confusing in practice.

## Marker clustering

`RoutePlanner.tsx` and `Prospecting.tsx` cap how many outlets render as individual map markers
(see `03-tutorial-frontend.md`) rather than clustering them. A clustering library
(`react-leaflet-cluster` or similar) would let dense areas (central Nairobi, say) show a single
"47 outlets here" bubble that expands on zoom, which scales better than a hard cap - reasonable to
add once outlet density in the map view becomes a real usability complaint rather than a
theoretical one.

## Charting

The quarterly sales bar chart is hand-rolled divs (see `03-tutorial-frontend.md`) - fine for one
chart on one page. If more chart types get added (sales trend lines, county-level heat maps of
churn), that's the point to bring in a real charting library instead of hand-rolling more of them.

## Bigger infrastructure (Snowflake, Databricks, Kubernetes)

Named in the original brief; genuinely not justified at this project's current scale (tens of
thousands of outlet rows, hundreds of customers, a 10k-user first-year target). These become worth
it at a different order of magnitude - millions of transaction rows needing a real data warehouse
(Snowflake/Databricks), or enough independent services needing independent scaling and deployment
(Kubernetes) that a single Render/Fly service stops being the bottleneck. Introducing them now
would be solving a scale problem this project doesn't have yet, at the cost of real operational
complexity it would have to carry regardless of whether it's needed.
