---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261024-API-SERVER-OBSERVABILITY-UI-STATIC-PAGE
artifact_type: plan
tags: [architecture, api-design, refactor]
---

# Plan
1. Write `src/api/static_pages/observability_ui.html` from the bytes the running app serves (not from the source text), and confirm sha256 081c122a...5f91b.
2. Add `src/api/routes/observability_ui.py` with the three routes: same function names, `response_class`, route-level dependencies, no docstrings (they would change the pinned OpenAPI description; `# noqa: D103` with the reason).
3. Replace the inline routes in `create_v2_app` with `app.include_router(observability_ui.router)` at the same point, last in registration order. Module-top import (no new PLC0415).
4. `python -m codebase.health tighten --yes`.
