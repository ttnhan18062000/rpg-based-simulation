# Plan — TCK-20260912-BEHAVIOR-ANALYTICS-PIPELINE-NEVER-STARTED-API-INERT

## Mechanism

Add `RuntimeProfile.enable_behavior_analytics_api: bool = False` (`src/config/profiles.py`),
matching `api_key_hashes`'s own fail-closed-by-default precedent — env-var configurable for free
via `ConfigLoader`'s existing generic bool-field loop, no new loader code.

In `src/api/server.py::create_v2_app()`, wrap the existing
`app.include_router(behavior.router, ...)` call in `if profile.enable_behavior_analytics_api:`.
When off (default), FastAPI has no matching route for any `/api/v1/behavior/*` path — a genuine
404 ("capability not exposed"), not the misleading empty-list/404 a mounted-but-unpopulated route
would give.

## Not doing

- Not changing `behavior.py`'s own route handlers or their empty-state response shape — the gate
  itself is the "explicit, intentional" signal this ticket's own original AC asked for (a caller
  either can't reach the capability at all, or reaches it fully aware it's unpopulated); no
  separate handler-level change needed once the disposition is "gate," not "wire" or "redesign the
  empty-state response."
- Not touching `search.py` — confirmed a different problem shape, filed separately.
- Not fixing `behavior.py`'s own hardcoded-adapter acquisition pattern — recorded as a cost input
  to this ticket's own still-open wire-vs-defer decision, not part of gating.

## Shared implementation

Same PR as `TCK-20260912-CAMPAIGN-CHRONICLE-API-REGISTRY-NEVER-POPULATED-IN-PRODUCTION` — both
gates land together (`enable_campaign_chronicle_api` alongside this one), same mechanism, same
`server.py` edit pass.
