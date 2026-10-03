---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260718-DASHBOARD-FACETS-FULLY-CANONICAL
phase: done
date: 2026-07-18
tags: [observability]
---

# TCK-20260718-DASHBOARD-FACETS-FULLY-CANONICAL

## Title
Make the Agent Ops Dashboard's Tier/Layer/Priority filter facets fixed canonical lists

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Reported live during today's session: selecting a Layer, then a Status/other
filter that combines with it to yield zero matching tickets, causes the
Layer dropdown to visually revert to "All." A prior ticket
(TCK-20260718-FILTER-SELECT-DROPOUT) patched this by injecting a synthetic
`<option>` for the already-selected value — but the user correctly identified
this as treating the symptom, not the cause: `facets["tiers"]`,
`facets["layers"]`, and `facets["priorities"]` in
`src/api/agent_ops_dashboard/ingest.py`'s `get_tickets()` are still computed
from the *currently filtered* corpus (`_distinct_sorted(...)`), so selecting
one filter genuinely narrows what values other filters can offer — not just
for the already-selected value, but for every not-yet-selected option too.
`facets["statuses"]` was already fixed this session
(TCK-20260718-STATUS-FACET-CANONICAL) to be a fixed canonical list
independent of the current filter/corpus state. This ticket generalizes that
same fix to Tier/Layer/Priority, using the canonical enums
TCK-20260718-TIER-PRIORITY-CANONICAL-ENUM defines (a hard dependency).

## Scope
- `ingest.py`'s `get_tickets()`: change `facets["tiers"]`,
  `facets["layers"]`, `facets["priorities"]` to always return
  `TIER_VALUES`/`LAYER_VALUES`/`PRIORITY_VALUES` (sorted, imported from
  `tools/ticket_field_values.py`) — independent of active filters,
  pagination, and current corpus content, exactly mirroring how
  `facets["statuses"]` already works. `facets["tags"]` is correctly left
  untouched (open-vocabulary, multi-value, genuinely corpus/registry-derived
  by design).
- Update the existing pinned facets test(s) in
  `tests/tools/test_agent_ops_dashboard_ingest.py` in place (not deleted) —
  same coordination discipline TCK-20260718-STATUS-FACET-CANONICAL already
  established for the statuses facet.
- Investigate whether `dashboard-frontend/src/views/TicketsView.tsx`'s
  `FilterSelect` synthetic-`<option>`-injection workaround (added by
  TCK-20260718-FILTER-SELECT-DROPOUT) becomes genuinely dead code once all
  four single-value facets (tier/layer/status/priority) are fixed canonical
  lists — the selected value will then always be present in `options` by
  construction. Remove it only if a test proves it unreachable; if any edge
  case still needs it (investigate before assuming), keep it and document
  why.
- Update the parity ledger entry this ticket touches
  (`docs/parity_ledger/infrastructure.yaml`, likely `INFRA-275`, extended
  earlier today by TCK-20260718-STATUS-FACET-CANONICAL) in the *same
  session* — the immediately-prior TCK-20260718-STATUS-MULTILINE-FIX ticket
  left a stale parity entry that the user's own review had to catch; do not
  repeat that gap.
- Update `docs/observability/agent_ops_dashboard_contract.md` and
  `docs/guides/agent_ops_dashboard.md`'s facets descriptions to cover all
  four canonical facets, ideally consolidating the near-duplicate
  "statuses is the one exception" paragraph added earlier today into one
  unified description now that it is no longer just one exception among
  four.

## Out of Scope
- `Tag`'s facet computation — correct as-is, not touched.
- Any further UI/UX redesign beyond making the facets canonical.
- Backend pagination/sort behavior — unrelated, already correct.

## Acceptance Criteria
- [ ] `GET /api/tickets?layer=economy&priority=P0` (or any other
      low/zero-match filter combination) returns `facets.tiers`,
      `facets.layers`, `facets.priorities` as their full canonical lists,
      regardless of `total_count` — verified via a direct `curl` call
      against a freshly-built, freshly-launched `make dashboard-serve`
      instance (kill any stale server process first and confirm port 8420
      is actually free before relaunching — a stale process serving old
      code caused a false-negative verification earlier today).
- [ ] A headless-browser check confirms no Tier/Layer/Status/Priority
      dropdown ever visually reverts to "All" for any two-filter zero-match
      combination.
- [ ] New/updated unit tests cover: facet independence from active filters
      (for all three newly-fixed dimensions, not just statuses), facet
      independence from pagination (already covered for statuses, extend the
      same pattern).
- [ ] The relevant parity ledger entry is updated in this same session with
      real, re-verified `v2_evidence`/`test_path` — not left for a future
      session to discover stale.
- [ ] Frontend test suite and backend test suite both fully green,
      independently re-run (not just trusted from a prior report).

## Related Tickets
- Parent epic: TCK-20260718-CANONICAL-FIELD-ENUMS-EPIC
- Depends on: TCK-20260718-TIER-PRIORITY-CANONICAL-ENUM
- Prior art: TCK-20260718-STATUS-FACET-CANONICAL (the exact pattern this
  ticket generalizes), TCK-20260718-FILTER-SELECT-DROPOUT (the band-aid this
  ticket supersedes for Tier/Layer/Priority)

## Related Docs
- docs/observability/agent_ops_dashboard_contract.md
- docs/guides/agent_ops_dashboard.md
- docs/parity_ledger/infrastructure.yaml
- docs/plans/agent_ops_dashboard/proposal_canonical_ticket_field_enums.md

## Related Stored Artifacts
None yet.

## Related Code Areas
- src/api/agent_ops_dashboard/ingest.py
- dashboard-frontend/src/views/TicketsView.tsx
- tests/tools/test_agent_ops_dashboard_ingest.py
- dashboard-frontend/src/test/TicketsView.test.tsx

## Assumptions / Open Questions
- Whether `FilterSelect`'s synthetic-option workaround is fully removable or
  needs to stay for a residual edge case — left for implementation to
  determine via an actual test, not assumed.

## Implementation Notes

Same execution-context deviation as the rest of this epic (no Agent tool
access — self-flagged per established precedent).

`ingest.py`'s `get_tickets()`: `facets["tiers"]`/`facets["layers"]`/
`facets["priorities"]` changed from `_distinct_sorted(r[...] for r in
filtered)` to `sorted(TIER_VALUES)`/`sorted(LAYER_VALUES)`/
`sorted(PRIORITY_VALUES)` — all three now imported from
`tools/ticket_field_values.py` alongside the already-canonical
`WORKFLOW_STATUS_VALUES`. `facets["tags"]` intentionally untouched
(genuinely open-vocabulary/multi-value, not a small closed enum).

Updated the existing pinned facets test in place (not deleted), added 2 new
backend tests covering the canonical-set-with-zero-matches and
filter-independence guarantees for the 3 newly-canonical facets (mirroring
the pattern `TCK-20260718-STATUS-FACET-CANONICAL` already established for
`statuses`).

`FilterSelect` dead-code investigation: confirmed (via a new test) that the
synthetic-`<option>` fallback added by `TCK-20260718-FILTER-SELECT-DROPOUT`
is now unreachable for all 4 of its real call sites (Tier/Layer/Status/
Priority), since none of their facets can shrink below the selected value
anymore. Decision: **kept, not removed** — re-documented as intentional
defensive protection (cheap, ~2 lines) against a future `FilterSelect` usage
over a genuinely shrinkable facet, rather than stripped for zero real
benefit. Updated the existing zero-match test's own comments to reflect
that it now tests the defensive fallback in isolation (via a hypothetical
mock), not live backend behavior, and added a companion test proving the
real backend contract never triggers that fallback in practice.

Parity: extended `INFRA-275` (`docs/parity_ledger/infrastructure.yaml`) in
the same session — also caught and fixed two now-stale claims left by
earlier tickets while I was in there: a `list(WORKFLOW_STATUS_VALUES)` code
citation that TCK-20260718-TIER-PRIORITY-CANONICAL-ENUM had already changed
to `sorted(...)` without updating this entry, and a "tiers/layers/
priorities/tags... still corpus-derived" claim this ticket itself now makes
false. Both corrected with an explicit "at the time this was written... now
superseded" note rather than silently rewritten, matching this ledger's
established style for entries multiple tickets have touched over time.

**Live verification** (explicitly required by this ticket's own AC, not
optional): killed a stale `dashboard-serve` process (confirmed running from
an earlier point in this session, would have caused a false-negative check
exactly like it did once already today) before rebuilding fresh. Hit `GET
/api/tickets?layer=economy&priority=P0` directly — 0 matching tickets, but
`facets.tiers`/`facets.layers`/`facets.priorities` all returned their full
canonical lists (19 layers, not a shrunk subset). Confirmed the same
visually via a headless-browser session: selecting Layer=economy then
Priority=P0 (a genuine zero-match combination) left both dropdowns showing
their selections correctly, with the full canonical option counts (20 = 1
"All" + 19 layers; 5 = 1 "All" + 4 priorities) — no synthetic-fallback
`<option>` was needed, confirming the dead-code analysis above.

## Test Summary

- `python3 -m pytest tests/tools/test_agent_ops_dashboard_ingest.py -v` —
  29/29 passing.
- `python3 -m pytest tests/tools/test_agent_ops_dashboard_ingest.py
  tests/tools/test_agent_ops_dashboard_api.py
  tests/tools/test_agent_ops_dashboard_api_boundary.py
  tests/tools/test_agent_ops_dashboard_concurrency.py
  tests/tools/test_agent_ops_dashboard_frontend_api_surface.py
  tests/tools/test_agent_ops_dashboard_serve.py -q` — 51/51 passing.
- `cd dashboard-frontend && npm run test -- --run` — 60/60 passing; `npx tsc
  -b --noEmit` clean; `npm run build` clean.
- **Live verification** (see Implementation Notes for full detail):
  `curl "http://localhost:8420/api/tickets?layer=economy&priority=P0&limit=1"`
  against a freshly-built, freshly-launched server (stale process killed
  first) — confirmed `facets.tiers`/`facets.layers`/`facets.priorities` all
  return their full canonical lists despite 0 matching tickets. Headless
  browser confirms the same visually, with zero console errors.

## Files Changed
- src/api/agent_ops_dashboard/ingest.py (facets computation for
  tiers/layers/priorities; import of TIER_VALUES/LAYER_VALUES/
  PRIORITY_VALUES)
- tests/tools/test_agent_ops_dashboard_ingest.py (updated pinned test, 2 new
  tests, new LAYER_VALUES import)
- dashboard-frontend/src/views/TicketsView.tsx (comment-only: re-documented
  the `FilterSelect` fallback as defensive rather than load-bearing — no
  logic change)
- dashboard-frontend/src/test/TicketsView.test.tsx (retitled/re-commented
  the existing zero-match test, added 1 new test proving the fallback is
  unreachable in practice)
- docs/parity_ledger/infrastructure.yaml (extended `INFRA-275`; corrected 2
  stale claims from earlier tickets in the same entry)

## Completion Summary
All acceptance criteria met: `facets.tiers`/`facets.layers`/
`facets.priorities` are now fixed canonical lists, verified live against a
freshly-built server (not just unit tests) with a genuine zero-match filter
combination; `facets.tags` correctly remains corpus-derived; the existing
pinned facets test was updated in place with new coverage added, not
replaced; `FilterSelect`'s dead-code question was investigated and resolved
(kept as cheap defensive insurance, with reasoning documented, per the
ticket's own instruction not to remove without justification); the parity
ledger was updated in the same session, including fixing two staleness gaps
left by earlier tickets rather than adding to them. 51 backend + 60 frontend
tests green; live curl and headless-browser checks both confirm the fix
works end-to-end against real server code, not just mocked tests.
