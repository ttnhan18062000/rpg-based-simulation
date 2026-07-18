---
status: active
layer: observability
authority: P1
audience: agent
artifact_type: plan
ticket_id: TCK-20260718-STATUS-FACET-CANONICAL
phase: open
date: 2026-07-18
tags: []
---

# Implementation Plan — TCK-20260718-STATUS-FACET-CANONICAL

## Summary

Make `GET /api/tickets`'s `facets.statuses` field always return the fixed
5-value canonical set (`OPEN`, `INPROGRESS`, `BLOCKED`, `DONE`,
`EPIC_SCOPED`) regardless of what's currently present in the filtered
ticket corpus, so the dashboard's Status filter dropdown always shows every
valid status — including ones with zero matching tickets right now — rather
than silently hiding them. Every other facet (tiers/layers/priorities/tags)
is unchanged.

## Steps

### Step 1 — Add the canonical constant and change facets computation

File: `src/api/agent_ops_dashboard/ingest.py`

- Add `WORKFLOW_STATUS_VALUES: list[str] = sorted({"OPEN", "INPROGRESS",
  "BLOCKED", "DONE", "EPIC_SCOPED"})` as a module-level constant near
  `_distinct_sorted`, with a docstring-comment explaining why it's fixed
  rather than derived (mirrors `tools/validate_frontmatter.py`'s
  `LAYER_VALUES`/`STATUS_VALUES` naming convention).
- In `get_tickets()`'s facets dict construction, change
  `"statuses": _distinct_sorted(r["workflow_status"] for r in filtered)` to
  `"statuses": list(WORKFLOW_STATUS_VALUES)`.

### Step 2 — Tighten `EPIC_TIER_VALUES` for consistency

File: `tools/gate_checks/status_drift_check.py`

- Change `EPIC_TIER_VALUES = {"EPIC_SCOPED", "SCOPED"}` to
  `EPIC_TIER_VALUES = {"EPIC_SCOPED"}`, with a comment explaining the
  tightening and citing this ticket.
- Update the module's docstring/function docstring references to the old
  two-value set.

### Step 3 — Update tests

Files: `tests/tools/test_agent_ops_dashboard_ingest.py`,
`tests/tools/test_status_drift_check.py`

- Update `test_facets_source_reflects_full_filtered_corpus_not_just_current_page`'s
  `statuses` assertion from the 4-value fixture-derived list to the 5-value
  canonical list.
- Add `test_statuses_facet_is_canonical_full_set_regardless_of_corpus_content`
  — a fixture with only `OPEN`/`DONE` tickets (no `INPROGRESS`/`BLOCKED`/
  `EPIC_SCOPED` anywhere), asserting the facet still lists all 5.
- Add `test_statuses_facet_unaffected_by_status_query_param` — filtering by
  `status=DONE` must not shrink the facet to `["DONE"]`.
- Split `test_epic_tier_exception_ignored_by_value`: keep the `EPIC_SCOPED`-
  only exemption assertion, add
  `test_bare_scoped_no_longer_exempt_after_tightening` asserting bare
  `SCOPED` is now correctly flagged as drift.

### Step 4 — Update docs

Files: `docs/observability/agent_ops_dashboard_contract.md`,
`docs/guides/agent_ops_dashboard.md`

- Correct the "distinct tier/layer/status/priority/tag values" facets
  description to exclude `status` from the corpus-derived list, and add a
  paragraph naming `WORKFLOW_STATUS_VALUES` and explaining the exception.
- Add a sentence to the Tickets-view guide section naming the 5 canonical
  values and explaining why Status behaves differently from the other
  filter dropdowns.

### Step 5 — Update the parity ledger in the same session

File: `docs/parity_ledger/infrastructure.yaml`

- `INFRA-275`: correct the stale "sorted(set(...)) over
  tier/layer/workflow_status/priority/tags" claim (drop `workflow_status`),
  append a paragraph describing `WORKFLOW_STATUS_VALUES` and the
  `EPIC_TIER_VALUES` tightening, append the new/updated test names to
  `test_path` with a fresh re-run confirmation.
- Do this in the same session as the code change — the immediately-prior
  ticket (`STATUS-MULTILINE-FIX`) missed exactly this step for its own
  parity entry and it was only caught during independent post-close review;
  do not repeat that gap.

### Step 6 — Full verification

- Re-run the full dashboard backend test suite plus the checker's own test
  file.
- Re-run the frontend suite as a regression guard (no frontend file
  expected to change).
- Re-verify both pytest commands cited in the parity `test_path` field
  actually produce the claimed pass counts, live, right before closing.

## Scope Guards

- Do NOT change `tiers`/`layers`/`priorities`/`tags` facet computation —
  those stay corpus-derived exactly as today. If a compelling reason to
  change them surfaces during implementation, flag it as a follow-up
  ticket, don't fold it in here.
- Do NOT touch `dashboard-frontend/` code — confirmed via investigation
  that `TicketsView.tsx` already renders whatever `optionsFacets.statuses`
  the backend returns with no special-casing.
- Do NOT re-litigate the 78 empty-`workflow_status` tickets or the 6
  same-line colon-format tickets — both remain explicitly deferred per the
  two predecessor tickets' own scope decisions.

## Dependency Map

Step 1 -> Step 3 (tests exercise Step 1's code) -> Step 5 (parity cites
Step 1/2's line numbers and Step 3's test names) -> Step 6 (final
verification of everything). Step 2 is independent of Step 1 but should
land in the same commit for narrative consistency (both are "tighten to
the canonical EPIC_SCOPED-only set"). Step 4 is independent, can happen any
time after Step 1.

## Acceptance Criteria Map

| AC | Step |
|---|---|
| `facets.statuses` always contains all 5 canonical values, independent of corpus content and active filters | Step 1, verified by Step 3's new tests |
| `tiers`/`layers`/`priorities`/`tags` facets unchanged (still corpus-derived) | Step 1 (no change to those lines), verified by existing untouched tests still passing |
| `EPIC_TIER_VALUES` consistent with the dashboard's canonical set | Step 2, verified by Step 3's split test |
| Docs describe the new behavior accurately | Step 4 |
| Parity ledger entry updated in the same session, no stale claims | Step 5 |
| No frontend changes needed | Verified in investigation.md, re-confirmed by unchanged frontend test suite in Step 6 |

## Anti-Drift Notes

See investigation.md's Anti-Drift Hazards section — `WORKFLOW_STATUS_VALUES`
must stay a fixed literal, never re-derived from the corpus, and
`EPIC_TIER_VALUES`/`WORKFLOW_STATUS_VALUES` must be kept in sync if either
is ever extended with a new epic-terminal value.
