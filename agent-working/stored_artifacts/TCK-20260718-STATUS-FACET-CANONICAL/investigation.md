---
status: active
layer: observability
authority: P1
audience: agent
artifact_type: investigation
ticket_id: TCK-20260718-STATUS-FACET-CANONICAL
phase: open
date: 2026-07-18
tags: []
---

# Investigation — TCK-20260718-STATUS-FACET-CANONICAL

## Current Behavior (file:line refs)

`src/api/agent_ops_dashboard/ingest.py`'s `get_tickets()` computes
`facets["statuses"]` via `_distinct_sorted(r["workflow_status"] for r in
filtered)` (was line ~527, pre-fix) — the same corpus-derived pattern used
for `tiers`/`layers`/`priorities`/`tags`. This means a status value with
zero matching tickets in the *currently filtered* result never appears as a
selectable option in the dashboard's Status filter dropdown at all.

User request: display all possible statuses, even ones with zero matching
tickets right now, so the filter always shows the complete set of valid
values a ticket could hold.

## Canonical Status Set — Derivation

- `CLAUDE.md`'s Ticket Format section documents the body `## Status` field's
  enum literally: `## Status  (OPEN | INPROGRESS | BLOCKED | DONE)`.
- `TCK-20260718-STATUS-DRIFT-REPAIR` and `TCK-20260718-STATUS-MULTILINE-FIX`
  (both closed earlier the same session) established `EPIC_SCOPED` as the
  sole legitimate epic-tier terminal Status value, normalizing away every
  prior `SCOPED`/`DONE (...)`/`DONE\nINPROGRESS`/legacy-bold-text variant in
  the corpus.
- Full corpus scan (`tickets/{done,inprogress,todos}/**/*.md`, `TCK-`-prefixed
  files only, using the real `parse_body_section`/`_strip_frontmatter`
  extraction — the same function the dashboard itself calls) found exactly
  three distinct values present: `DONE` (1046), `OPEN` (12), `EPIC_SCOPED`
  (6). Zero occurrences of `INPROGRESS` or `BLOCKED` exist anywhere in the
  live corpus right now — this is precisely the scenario the user described:
  a status that should still be selectable even with no current matches.
  Zero non-canonical values found outside the already-deferred exemptions
  (pre-`TCK-`-naming legacy files, the 6 same-line colon-format tickets, the
  78 empty-`workflow_status` tickets).

Canonical set confirmed: `{OPEN, INPROGRESS, BLOCKED, DONE, EPIC_SCOPED}` —
5 values.

## Existing Test/Parity Coordination

- `tests/tools/test_agent_ops_dashboard_ingest.py::test_facets_source_reflects_full_filtered_corpus_not_just_current_page`
  pins `results.facets["statuses"] == ["BLOCKED", "DONE", "INPROGRESS",
  "OPEN"]` (4 values) against a fixture that happens to have exactly those 4
  values present. This assertion needs updating to the 5-value canonical
  list once `EPIC_SCOPED` unconditionally appears.
- `docs/parity_ledger/infrastructure.yaml`'s `INFRA-275` entry documents the
  current `facets` computation as "sorted(set(...)) over
  tier/layer/workflow_status/priority/tags" — stale once `statuses` becomes
  fixed/canonical rather than corpus-derived; requires the same-session
  update per `CLAUDE.md`'s Parity rule (a gap the immediately-prior
  `STATUS-MULTILINE-FIX` ticket itself missed, caught only during the user's
  independent post-close review — do not repeat that mistake here).
- `tools/gate_checks/status_drift_check.py`'s `EPIC_TIER_VALUES = {"EPIC_SCOPED",
  "SCOPED"}` still exempts bare `SCOPED` — now inconsistent with the
  dashboard's canonical set (which only recognizes `EPIC_SCOPED`) now that
  the corpus's one remaining bare-`SCOPED` ticket has been normalized away.
  `tests/tools/test_status_drift_check.py::test_epic_tier_exception_ignored_by_value`
  pins the old two-value exemption and needs splitting: `EPIC_SCOPED` stays
  exempt (unchanged assertion), bare `SCOPED` becomes a new flagged-as-drift
  case.

## Scope Decision — Statuses Facet Only

Deliberately narrow: only `facets["statuses"]` changes to a fixed canonical
list. `tiers`/`layers`/`priorities`/`tags` keep deriving from the filtered
corpus exactly as today — the user asked specifically about statuses, and
those other facets don't have the same "user needs to discover a status
exists but has zero current tickets" motivation (a tier/layer/priority
combination with zero matches is a much rarer, less actionable case than a
whole status bucket being invisible).

## Frontend Impact

`dashboard-frontend/src/views/TicketsView.tsx` renders `optionsFacets.statuses`
directly as filter options — no special-casing, no client-side derivation.
Confirmed via grep: zero frontend code changes required. All frontend tests
that reference `statuses` mock the fetch response directly with a hardcoded
value (`statuses: ['OPEN']`), never exercising real backend logic — none
break.

## Risks and Open Questions

None outstanding — canonical set independently re-verified against the live
corpus before hardcoding; existing pinned test and parity entry both updated
in this same session, closing the gap class that slipped through on the
immediately-prior ticket.

## Anti-Drift Hazards

- `WORKFLOW_STATUS_VALUES` must stay a Python `list`/`set` literal, not a
  computed derivation from the corpus — the whole point is independence
  from corpus content. A future refactor that "simplifies" this back to
  `_distinct_sorted(...)` would silently regress this ticket's fix.
- `EPIC_TIER_VALUES` in `status_drift_check.py` and `WORKFLOW_STATUS_VALUES`
  in `ingest.py` now both encode the same canonical epic-terminal-value
  belief (`EPIC_SCOPED` only) independently in two files — if a future
  ticket ever legitimately needs a second epic terminal value, both must be
  updated together or the checker and the dashboard will silently disagree
  about what's canonical.
