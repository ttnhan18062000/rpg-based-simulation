---
status: historical
layer: core
authority: P1
audience: agent
ticket_id: TCK-20260825-METADATA-API-BACKEND-MISSING
artifact_type: test_plan
tags: [hud, content]
---

# Test Plan — TCK-20260825-METADATA-API-BACKEND-MISSING

## Normal flow
- All 8 routes return 200 with real, non-empty data against the real content catalog.
- Each route's response has exactly the documented top-level keys (no missing/extra fields).
- Real-backed domains' values match the real catalog 1:1 (counts and specific field values).

## Edge cases
- `/classes` does not require a catalog (its data source, `CLASS_REGISTRY`, is a static Python
  dict, not catalog-loaded) — must still work with no catalog present.
- Unbacked sub-fields (`ai_states`/`tiers`/`damage_types`/`skills`/`race_skills`/
  `scaling_grades`/`mastery_tiers`/`skill_targets`) return correctly-shaped empty
  collections, never fabricated placeholder content.
- `materials.walkable` and other defaulted per-entry fields are uniformly defaulted, not
  fabricated per-entry.

## Failure modes
- Catalog-backed routes (`/enums`, `/items`, `/traits`, `/attributes`, `/buildings`,
  `/resources`, `/recipes`) return 503 when no catalog is loaded.

## Regression-prone paths
- `MetadataContext.tsx`'s auth-header fix must not break its existing non-blocking-fallback
  behavior (still falls back to `EMPTY_METADATA` on a real fetch failure) — covered by the
  pre-existing `MetadataContext.test.tsx` (unchanged, still passing).
- `recipes` must keep resolving from `catalog.recipes` (confirmed as
  `RecipeRegistry`'s real bootstrap source) — a regression here would silently point at a dead
  recipe source again, the exact bug class `TCK-20260904-RECIPE-CATALOG-NAMESPACE-BRIDGE` found
  elsewhere in this codebase.

## Live verification (executed, not skipped)
- Real backend (`python3 -m src serve --port 8000 --api-key-hashes ...`) + real frontend dev
  server (`npm run dev`, port 5173) running simultaneously.
- All 8 routes curled directly against the backend (real, non-empty JSON) and again through the
  Vite dev proxy at `http://localhost:5173/api/v1/metadata/*` with the real `X-API-Key` header —
  the exact path `MetadataContext.tsx` itself uses.
- New rendering test (`LootPanel.metadata.test.tsx`) with a real fixture captured live from the
  running backend, proving `LootPanel` renders the real item name/type/rarity/gold-value.

## Commands
- `pytest tests/api/test_metadata_api.py -v`
- `pytest tests/api/ tests/unit/api -m "not slow and not extra_slow" -q` (broader regression check)
- `cd frontend && npx vitest run` (full frontend suite)
- Manual: `make dev-backend` / `make dev-frontend` (or the two direct invocations above), then
  `curl -H "X-API-Key: dev-local-key-do-not-use-in-prod" http://localhost:5173/api/v1/metadata/<domain>`
