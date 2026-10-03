---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260719-PHASE-GLOSSARY-DESCRIPTIONS
artifact_type: test_plan
tags: [dashboard, observability, workflows]
---

# Test Plan — TCK-20260719-PHASE-GLOSSARY-DESCRIPTIONS

## Regression Surface

**Backend (unit):**
- `tests/tools/test_glossary_registry.py` — all pre-existing tests, **except**
  `test_glossary_categories_is_the_expected_fixed_set` (lines 163-172), which must be **updated**
  (not merely kept passing) to include `"phase"` in the expected set — see Anti-Drift Test Guards
  below. `test_real_seeded_registry_covers_every_canonical_ticket_field_value`,
  `test_real_seeded_registry_every_entry_has_non_blank_description`,
  `test_real_seeded_registry_every_entry_has_valid_category` all run against the live seeded
  registry and must keep passing once phase entries are appended.
- `tests/tools/test_agent_ops_dashboard_glossary.py` — all 9 pre-existing tests must keep passing
  unmodified in behavior. `test_glossary_against_real_seeded_registries`'s
  `len(glossary.terms) >= 48` floor assertion is a lower bound, not exact — it will keep passing
  automatically once the registry grows by ~21 phase terms (56 term is a stronger real total post
  this ticket, but the floor assertion itself needs no edit for that reason alone).

**Frontend:**
- `dashboard-frontend/src/test/StatsView.test.tsx` — all pre-existing tests must keep passing,
  including `renders a Phase Status Distribution table with ok/failed/blocked/skipped columns`
  (asserts `phase-status-row-Investigate`/`phase-status-row-Implement` exist) and the
  `never hardcodes a glossary description string in its own source` guard (asserts
  `glossaryDescriptions` appears in `StatsView.tsx`'s own source — must keep being true, this
  ticket adds a `GlossaryTooltip` cell wiring, not a new hardcoded string).
- `dashboard-frontend/src/test/GlossaryTooltip.test.tsx` — unaffected by this ticket's changes,
  regression guard only.
- `dashboard-frontend/src/test/ReplayTimelineView.test.tsx` — regression guard only, **unless**
  Plan decides to extend the `ReplayTimelineView.tsx` `phase`/`agent` gap found during investigation
  into this ticket's scope, in which case new tests are required there too (see New Tests Required).

## New Tests Required

Backend:
- `test_add_term_accepts_phase_category` (or extend an existing category-coverage test) —
  category: unit. Verifies `add_term(term, "phase", description)` succeeds once `"phase"` is added
  to `GLOSSARY_CATEGORIES`, mirroring the existing per-category acceptance shape already implicit in
  `test_add_term_appends_entry_and_returns_it`. Location: `tests/tools/test_glossary_registry.py`.
- `test_glossary_categories_is_the_expected_fixed_set` — category: unit (update, not new). Must be
  edited to assert the new 8-element set including `"phase"`. Location:
  `tests/tools/test_glossary_registry.py`.
- `test_real_seeded_registry_covers_every_workflow_phase` (new) — category: unit/integration
  (real-corpus). Verifies every one of the 21 deduplicated `vocabulary.py::WORKFLOW_PHASES` strings
  has a real entry in the live `glossary_registry.jsonl` with `category == "phase"` and a non-blank
  description — the phase-domain equivalent of the existing
  `test_real_seeded_registry_covers_every_canonical_ticket_field_value`. This is the single
  strongest regression guard against a typo'd/missing phase term (see investigation.md's Anti-Drift
  Hazards). Location: `tests/tools/test_glossary_registry.py`. Must import
  `tools/agent-monitoring/vocabulary.py::WORKFLOW_PHASES` directly (not re-derive/hardcode the
  21-string list) so it can never silently drift from the real source if `WORKFLOW_PHASES` changes
  in the future.
- `test_glossary_route_includes_phase_terms` (new) — category: integration. Verifies
  `GET /api/glossary` (via `DashboardCache.get_glossary()` / the FastAPI route) returns entries for
  a representative phase term (e.g. `"Review"`, `"Architecture-Verify"`) under `category == "phase"`.
  Location: `tests/tools/test_agent_ops_dashboard_glossary.py`.
- `test_glossary_term_count_grows_by_real_phase_count` (new, extends the existing real-corpus test
  rather than a standalone one) — category: integration. Bumps
  `test_glossary_against_real_seeded_registries`'s `len(glossary.terms) >= 48` floor to account for
  the ~21 new phase terms (exact new floor computed once real descriptions are registered).
  Location: `tests/tools/test_agent_ops_dashboard_glossary.py`.

Frontend:
- `renders a hover description for a phase name in the Phase Status Distribution table` (new) —
  category: integration (component). Mocks the glossary fetch with a phase entry (e.g.
  `{ Investigate: { term: 'Investigate', category: 'phase', description: '...' } }`), asserts the
  `phase-status-row-Investigate` row's phase cell has the `glossary-hint-icon` test id present —
  mirrors the existing `shows a hint icon and real description on the Top Agents table` test shape.
  Location: `dashboard-frontend/src/test/StatsView.test.tsx`.
- `renders a Phase Status Distribution row plainly, with no hint icon, when the glossary has no
  entry for that phase` (new) — category: integration (component), graceful-degradation guard.
  Mirrors the existing Top Agents no-entry test. Location: `dashboard-frontend/src/test/StatsView.test.tsx`.
- Architecture guard (optional but recommended, mirrors the existing
  `never hardcodes a glossary description string in its own source` test): assert no phase
  description string literal appears hardcoded in `StatsView.tsx`'s own source — same
  `STATS_VIEW_SOURCE` regex-source-scan pattern already in the file.

Conditional (only if Plan brings `ReplayTimelineView.tsx` into scope per the investigation's flagged
gap):
- Hint-icon-present/absent tests for `entry.phase` in both the phase-timeline button strip and the
  detail-area header, and for `entry.agent` in the detail-area header — same shape as the
  StatsView pair above. Location: `dashboard-frontend/src/test/ReplayTimelineView.test.tsx`.

## Scoped Pytest Commands

```
python3 -m pytest tests/tools/test_glossary_registry.py tests/tools/test_agent_ops_dashboard_glossary.py -v
python3 -m pytest tests/tools/ -q -k "glossary or agent_ops_dashboard"
```

Frontend:
```
cd dashboard-frontend && npm run test -- --run
cd dashboard-frontend && npx tsc -b --noEmit
cd dashboard-frontend && npm run build
```

Never `pytest tests/` — scope is `tests/tools/` (glossary registry + dashboard ingest) plus the
`dashboard-frontend` test/build/typecheck trio; no `src/domains`, `src/engine`, or simulation test
paths are touched by this ticket.

## Anti-Drift Test Guards

- **`test_glossary_categories_is_the_expected_fixed_set` is the load-bearing guard that will
  correctly fail if `GLOSSARY_CATEGORIES` is extended without updating this test** — Implement must
  update it in the same change, not leave it red. Its presence at all is itself a guard against a
  category being added silently/accidentally in the future without a conscious, reviewed decision —
  do not delete or loosen it (e.g. to `<=` or `.issuperset()`) to make the diff smaller; update the
  literal expected set instead, preserving its exact-match strictness.
- **`test_real_seeded_registry_covers_every_workflow_phase` (new) must import `WORKFLOW_PHASES`
  directly from `tools/agent-monitoring/vocabulary.py`**, never a hardcoded copy of the 21 strings —
  this is the single test that would catch either (a) a phase term registered with the wrong casing/
  spacing (dead term, never matches a real event), or (b) a future new phase added to
  `WORKFLOW_PHASES` by an unrelated ticket silently going undocumented in the glossary.
- **`test_glossary_route_never_returns_raw_dict_shape`
  (`tests/tools/test_agent_ops_dashboard_glossary.py:173-181`) is an untouched architecture guard —
  confirms `GET /api/glossary`'s route return-type annotation stays the typed `GlossaryResponse`,
  never a raw dict, regardless of how many merge sources feed it.** No change needed to this test,
  but its continued pass is required evidence the new phase entries don't leak an untyped shape at
  the API boundary.
- **StatsView.test.tsx's `never hardcodes a glossary description string in its own source` guard**
  must keep passing unmodified — proves the new phase-cell wiring reads its description from the
  fetched `glossary` object (`GlossaryTooltip term={row.phase} glossary={glossary}`), never a
  literal string embedded in `StatsView.tsx` itself.
- **Do not weaken `test_glossary_against_real_seeded_registries`'s `>=` floor into an exact `==`
  count** — the existing test deliberately uses a lower bound so future unrelated registry growth
  (new tags, new layers, new agents) doesn't make this test brittle. Bump the floor, keep the `>=`.
- **Regression guard on `WORKFLOW_PHASES` itself staying untouched**: no new/modified test is
  required to assert this (Out of Scope, not a behavior this ticket owns), but any diff review
  should confirm `tools/agent-monitoring/vocabulary.py` has zero changes — a diff touching it is a
  scope-creep signal, not an expected file for this ticket.
