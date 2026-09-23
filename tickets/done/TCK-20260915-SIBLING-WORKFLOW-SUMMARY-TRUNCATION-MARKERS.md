---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260915-SIBLING-WORKFLOW-SUMMARY-TRUNCATION-MARKERS
phase: done
date: 2026-09-15
tags: [agent-monitoring, data-quality]
---

# TCK-20260915-SIBLING-WORKFLOW-SUMMARY-TRUNCATION-MARKERS

## Title
`create-tickets.js`, `simq-audit.js`, and `implement-epic.js` still truncate event summaries with a
silent `.slice(0, 200)` — the same defect `TCK-20260915-EVENT-SUMMARY-TRUNCATION` fixed only in
`implement-ticket.js`

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P3

## Request Summary
`TCK-20260915-EVENT-SUMMARY-TRUNCATION` fixed `implement-ticket.js`'s `pushEvent()` (and 10
call-site-level pre-slices) by replacing a silent `.slice(0, 200)` with a `truncateSummary()`
helper that appends a visible `' […]'` marker only when a real cut occurs. That ticket's own scope
named `implement-ticket.js` only (`Related Code Areas` listed only that file's `pushEvent` call
sites).

Peer review of that closed ticket found the identical unmarked-truncation pattern still present in
3 sibling workflows, each with its own central `pushEvent` doing a raw `.slice(0, 200)`:

- `create-tickets.js`:110 (own `pushEvent`) and a second pre-slice at :885
- `simq-audit.js`:35 (own `pushEvent`) and pre-slices at :127, :291, :325
- `implement-epic.js`:356 (a single direct assignment, no `pushEvent` wrapper)

Measured real impact across the corpus (894 summaries sit at exactly 200 chars total, i.e. the
truncation boundary — 838 of those are from `implement-ticket.js`/`implement-epic.js`'s own
`TCK-*`-prefixed runs, already fixed for `implement-ticket.js`'s share):

| `run_id` prefix | Workflow | Truncated / Total events |
|---|---|---|
| `TCK-*` | implement-ticket / implement-epic | 838 / 9,592 |
| `FOLDER-*` | implement-epic | 16 / 218 |
| `CREATE-TICKETS-*` | create-tickets | 15 / 488 |
| `SIMQ-AUDIT-*` | simq-audit | 9 / 25 |

`implement-ticket.js`'s fix covers the large majority of the raw count, but `simq-audit.js`'s own
rate (9/25 = 36%) is the worst of any workflow measured, despite the small absolute count.

## Scope
- Add the same `truncateSummary()`-shaped helper (or import/share the one already defined in
  `implement-ticket.js`, if these files already share any common module — check before
  duplicating) to `create-tickets.js` and `simq-audit.js`'s own `pushEvent` functions, and to
  `implement-epic.js`'s single direct-assignment site.
- Fix each file's own pre-slicing call sites the same way `TCK-20260915-EVENT-SUMMARY-TRUNCATION`
  did: remove redundant pre-slices that feed into the file's own `pushEvent`, and apply the helper
  directly at any site that builds an event object without going through `pushEvent`.

## Out of Scope
- `implement-ticket.js` itself — already fixed.
- Rewriting historical truncated summaries in any of these 3 workflows' own past events.

## Acceptance Criteria
- [x] `create-tickets.js`, `simq-audit.js`, and `implement-epic.js` each apply a visible-marker
      truncation helper at every summary-producing call site (central `pushEvent` and any
      direct-assignment site), mirroring `implement-ticket.js`'s fix.
- [x] No raw `.slice(0, 200)` remains in any of the 3 files (regression-tested, mirroring
      `tests/tools/test_event_summary_truncation.py`'s own file-wide assertion).
- [x] `docs/agent-monitoring/schema.md`'s `summary` field row is updated to note the same
      writer/marker behavior now applies uniformly across all 4 workflow files, not just
      `implement-ticket.js`.

## Related Tickets
- `TCK-20260915-EVENT-SUMMARY-TRUNCATION` (the fix this ticket extends to sibling workflows)
- `TCK-20260915-MONITORING-ANOMALY-DETECTION-EPIC` (the epic during which the fixed ticket, and
  this follow-on gap, were found — this ticket is NOT a child of that epic; it was scoped after
  the epic's own 9-ticket child list was already fixed, and is tracked independently so it does
  not retroactively expand that epic's already-agreed scope)

## Related Docs
- `docs/agent-monitoring/schema.md`

## Related Stored Artifacts
- None — hotfix tier, self-evident intent per this ticket's own body.

## Related Code Areas
- `.claude/workflows/create-tickets.js` (`pushEvent` at :104/:110, second pre-slice at :893)
- `.claude/workflows/simq-audit.js` (`pushEvent` at :29/:35, pre-slices at :135, :299, :333)
- `.claude/workflows/implement-epic.js` (:356, direct assignment)

## Assumptions / Open Questions
- Whether these 4 workflow files already share (or should share) one common summary-truncation
  helper module — checked, not assumed: no `require()`/`import` of a shared JS module exists
  between any of the 4 workflow files (each is a standalone script; the only `import`/`require`
  lines present are Python imports embedded inside `python3 -c` string literals, unrelated).
  Duplicated the small helper per-file, same shape as `implement-ticket.js`'s own local `const`,
  rather than introducing a new shared-module abstraction for a single 4-line function across 4
  independent scripts.

## Implementation Notes
Real line numbers had shifted slightly from the ticket's own filing-time numbers (re-verified via
grep before editing, per the ticket's own Implementation Notes caution) but all 7 named call
sites were confirmed present and fixed at their real current locations.

- `create-tickets.js`: added a local `truncateSummary()` (identical shape to
  `implement-ticket.js`'s own), applied inside `pushEvent()`. Removed the redundant
  `linkText.slice(0, 200)` pre-slice at the `link-epic` call site — `pushEvent` now handles
  truncation itself; the `|| \`Linked to ${epicId}\`` fallback behavior is unchanged since an
  empty string is still falsy either way.
- `simq-audit.js`: same helper added, applied inside `pushEvent()`. Removed 3 redundant pre-slices
  (`recalText`, `syncDocsText`, `parityText`) at their respective `pushEvent` call sites.
- `implement-epic.js`: this file has no central `pushEvent` cluster at all (confirmed by grep —
  only one summary-producing site exists, a direct object-literal assignment inside
  `batchEvents`). Added the helper locally at that one use site rather than inventing a
  file-wide event-pushing abstraction that doesn't otherwise exist here.
- `docs/agent-monitoring/schema.md`'s `summary` field row rewritten to describe the now-uniform
  4-file behavior instead of naming only `implement-ticket.js`.
- Verified JS syntax validity directly (`node --check`) on all 3 edited files — no syntax errors.
- Confirmed no other file under `.claude/workflows/` still has a raw `.slice(0, 200)`
  (repo-wide grep, not just the 3 named files).

## Test Summary
```
/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3 -m pytest \
  tests/tools/test_sibling_workflow_summary_truncation.py \
  tests/tools/test_event_summary_truncation.py -v
# 19 passed
```
New file `tests/tools/test_sibling_workflow_summary_truncation.py` mirrors
`test_event_summary_truncation.py`'s exact static-source-parsing pattern, parametrized across all
3 files: helper defined, caps-at-200-with-marker, no raw slice remains, `pushEvent` uses the
helper (the 2 files that have one), plus 3 file-specific tests for `implement-epic.js`'s
direct-assignment site and each file's own named pre-slice sites.

Also ran the broader set of every other test file referencing any of the 3 edited files (checked
for regressions, not assumed clean): `test_epic_create_tickets_sidecar_orchestrator.py`,
`test_workflow_meta_conformance.py`, `test_epic_tracking_doc_static.py`,
`test_monitoring_bypass_fix.py`, `test_step0_ts_orchestrator.py`,
`test_implement_epic_close_step.py`, `test_ticket_scoper_relevance_check.py`,
`test_tag_skill_mapping_check.py`, `test_create_tickets_tag_scope.py`, `test_generate_retro.py`,
`test_record_events.py`, `test_retrieval_event_wrapper_single_source.py`,
`test_concern_investigator_agent_definition.py` — 314 passed, 1 xfailed, 0 failed total across
both runs.

## Files Changed
- `.claude/workflows/create-tickets.js` — local `truncateSummary()` added, applied in `pushEvent`;
  redundant `link-epic` pre-slice removed.
- `.claude/workflows/simq-audit.js` — local `truncateSummary()` added, applied in `pushEvent`; 3
  redundant pre-slices removed.
- `.claude/workflows/implement-epic.js` — local `truncateSummary()` added at its one
  direct-assignment summary site.
- `docs/agent-monitoring/schema.md` — `summary` field row updated for the now-uniform 4-file
  behavior.
- `tests/tools/test_sibling_workflow_summary_truncation.py` (new) — regression tests for all 3
  files.
- `docs/REGISTRY.yaml` — regenerated unconditionally as part of this closure.

## Completion Summary
Extended `TCK-20260915-EVENT-SUMMARY-TRUNCATION`'s visible-truncation-marker fix from
`implement-ticket.js` alone to all 3 named sibling workflows (`create-tickets.js`,
`simq-audit.js`, `implement-epic.js`), removing every raw `.slice(0, 200)` silent-truncation site
repo-wide under `.claude/workflows/`. No shared module was introduced — checked first that none
already existed between these standalone scripts, then duplicated the small helper per-file,
matching `implement-ticket.js`'s own established local-`const` shape. `docs/agent-monitoring/
schema.md` updated to reflect the now-uniform behavior across all 4 workflow files. All 3 of the
ticket's own AC met; regression tests added mirroring the precedent ticket's own test shape,
extended and parametrized across the 3 new files; no logic beyond summary slicing was touched.
