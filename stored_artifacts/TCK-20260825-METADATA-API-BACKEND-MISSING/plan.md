---
status: historical
layer: core
authority: P1
audience: agent
ticket_id: TCK-20260825-METADATA-API-BACKEND-MISSING
artifact_type: plan
tags: [hud, content]
---

# Plan — TCK-20260825-METADATA-API-BACKEND-MISSING

## Decision (see investigation.md for full rationale)

Build all 8 routes now, per explicit user decision: real data everywhere a genuine backend source
exists, correctly-shaped empty/defaulted data everywhere it doesn't (never fabricated), each
decision documented inline. Reject narrowing scope to only the well-backed domains — the user
explicitly chose the broader option.

## Implementation steps

1. **`src/api/presenters/metadata_presenter.py`** (new) — `MetadataPresenter` with 8 static
   `present_*` methods, one per domain, mirroring `ManifestPresenter`'s existing shape (plain dict
   return, `CatalogRepository` input, no raw domain-model leakage). **Status: done.**
2. **`src/api/routes/metadata.py`** (new) — `APIRouter(prefix="/metadata")` with the 8 GET routes,
   mirroring `manifest.py`'s 503-on-no-catalog pattern. **Status: done.**
3. **`src/api/server.py`** — mount the new router the same way `manifest.router` is mounted
   (`prefix="/api/v1"`, `dependencies=[Depends(require_admission)]`). **Status: done.**
4. **`frontend/src/contexts/MetadataContext.tsx`** — fix a real, necessary bug found during
   live-testing: `fetchJson()` sent no `X-API-Key` header, so every new route would 401 for the
   real running app given this ticket's own auth requirement. Fixed by mirroring
   `useSimulation.ts`'s existing `API_KEY`/header convention. **Not** a change to
   `frontend/src/types/metadata.ts` or any of the 4 excluded panel components — purely the fetch
   call itself. **Status: done.**
5. **Live verification** — real backend + real frontend dev server, all 8 routes confirmed
   returning real data through the real Vite proxy path; a new rendering test
   (`LootPanel.metadata.test.tsx`) proves a real consuming panel renders real looked-up data.
   **Status: done.**
6. **Tests** — `tests/api/test_metadata_api.py` (21 tests: route-level 200/503, presenter-level
   real-vs-defaulted-field assertions per domain) plus the new frontend rendering test.
   **Status: done.**

## Explicitly out of scope (per the ticket's own text + investigation.md)
- `frontend/src/types/metadata.ts` — contract already correct, untouched.
- The 4 consuming panel components' own rendering/contract logic — untouched (only the shared
  `MetadataContext.tsx` fetch call needed a fix, not any panel).
- Historical why-was-this-domain-never-populated investigation (e.g. why no rich class/skill
  content exists) — out of scope, a separate content-authoring effort.
- Revisiting `MetadataContext.tsx`'s non-blocking-fallback mechanism's own existence — the
  ticket's last Scope bullet only asks whether a warning banner is now warranted; not built in this
  pass (visibility banners are a UI-design decision better suited to the HUD epics that actually
  consume this data, not a bare backend-completion ticket).

## Acceptance-criteria map
| AC | Satisfied by |
|---|---|
| All 8 routes exist and return real data matching the documented shapes | `metadata.py` + `metadata_presenter.py`, live-verified |
| Live-verified: MetadataContext.tsx loads real (non-empty) metadata through the real routes | Real backend + frontend dev server test, after fixing the auth-header bug |
| At least 1 of the 4 panels verified to render real looked-up data | `LootPanel.metadata.test.tsx`, real fixture |
| Existing frontend tests still pass | Full `npx vitest run` — 31/31 pass |
| New backend tests cover all 8 routes' response shapes | `tests/api/test_metadata_api.py` — 21 tests |
