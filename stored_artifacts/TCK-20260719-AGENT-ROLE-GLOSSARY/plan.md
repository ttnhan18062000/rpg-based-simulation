---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260719-AGENT-ROLE-GLOSSARY
artifact_type: plan
tags: [dashboard, observability]
---

# Implementation Plan — TCK-20260719-AGENT-ROLE-GLOSSARY

## Summary

Extend `GET /api/glossary`'s three-source merge (registry + layer) with a
third source: every `.claude/agents/*.md` role file's own frontmatter
`description:` field, under `category="agent"`. Wire the Stats view's Top
Agents table `Agent` column to show it on hover via the existing
`GlossaryTooltip` component, matching the pattern already used for that
table's `Ok`/`Failed`/`Blocked`/`Skipped` column headers.

## Steps

### Step 1 — Backend: `_load_agent_role_descriptions()` helper + merge wiring

`src/api/agent_ops_dashboard/ingest.py`: add a module-level function reading
every `.claude/agents/*.md` file's frontmatter via `extract_frontmatter`,
returning `{name: description}` for files with both fields present.
Tolerant of a missing `.claude/agents/` directory (returns `{}`) and of
individual files with malformed/absent frontmatter (skipped, never raises).
Wire into `get_glossary()` as a third merge loop after the existing
registry/layer loops, same `if term in terms: continue` shadow-guard.

### Step 2 — Backend tests

`tests/tools/test_agent_ops_dashboard_glossary.py`: add coverage for the
happy-path merge, the missing-`.claude/agents/`-directory tolerance
(critical — every existing `tmp_path`-based test in this file relies on
this exact tolerance already), and a role file with no `description:`
being skipped. Extend the real-corpus test to assert a real agent term is
present and bump its `len(glossary.terms) >= N` floor.

### Step 3 — Frontend: wire the Top Agents table's Agent column

`dashboard-frontend/src/views/StatsView.tsx`: wrap `row.agent` in the
existing `GlossaryTooltip` component (already imported, already used for
this same table's column headers and the Slow Runs status cell) — the most
consistent fit for a plain `<td>` cell, more so than the
flattened-`descriptions`-map pattern `BarChart`/`GroupedBarChart` use for
chart rows.

### Step 4 — Frontend tests

`dashboard-frontend/src/test/StatsView.test.tsx`: hint-icon-present test for
a matching agent, hint-icon-absent test for a non-matching one (graceful
degradation).

### Step 5 — Docs

`docs/observability/agent_ops_dashboard_contract.md`'s existing
`get_glossary()` paragraph: extend to describe the new third source in the
same paragraph, not a disconnected new section.

### Step 6 — Verification

Live-verify `/api/glossary`'s term count grows from 54 to 67. Headless-browser
hover-test both a real agent-role name (must show its real description) and
a non-agent-file label (must show no icon/tooltip, no console error).

## Scope Guards

- No new descriptions written from scratch — every description already
  exists in each role file's own frontmatter.
- No change to what values `agent-monitoring/events.jsonl`'s `agent` field
  can hold.
- No change to the existing registry/layer merge sources or their tests.

## Dependency Map

Step 1 before Step 2/3 (both need the merge/helper to exist). Step 3 before
Step 4. Step 5/6 after all code lands.

## Acceptance Criteria Map

- AC1 (13 real agent descriptions live in `/api/glossary` under
  `category="agent"`) → Step 1, verified Step 6.
- AC2 (Top Agents table shows hover description for a matching agent name)
  → Step 3, verified Step 6.
- AC3 (non-agent-file labels degrade gracefully, no crash) → Step 1's
  tolerance + Step 3's existing `GlossaryTooltip` graceful-degradation
  behavior, verified Step 6.
- AC4 (docs describe the new merge) → Step 5.

## Anti-Drift Notes

**Deviation from normal Scope→Investigate→Plan→Review→Implement ordering,
self-flagged per this project's traceability rule**: this ticket's
implementation began before this plan.md/investigation.md were written.
The work was originally dispatched to a background execution context which
stalled/hit session limits three times in a row partway through
implementation — the second stall left `ingest.py` in a genuinely broken
state (calling `_load_agent_role_descriptions()` before it was ever
defined, confirmed via a real pre-fix test run showing 6 `NameError`
failures). Given the repeated interruptions, the coordinating session
finished the remaining implementation directly (defining the missing
helper, wiring the frontend, adding tests, updating docs) rather than
risking a fourth stall, then wrote this ticket and its staging artifacts
retroactively to document the completed, verified work — all claims below
were independently re-verified via real test runs and live browser checks
by the coordinating session itself, not merely asserted.

A second, unrelated pre-existing bug was found and fixed along the way:
`dashboard-frontend/src/api.ts`'s `useGlossary()` hook caches its fetch in a
module-level `_glossaryPromise` that was never reset between tests — any
test file mounting a view that calls `useGlossary()` more than once with
different mocked glossary content would silently reuse an earlier test's
resolved value. Added `_resetGlossaryCacheForTests()` (test-only export) and
wired it into `StatsView.test.tsx`'s `afterEach` — the new hint-icon
presence/absence test pair genuinely fails without this reset (confirmed by
temporarily disabling the reset call and re-running).
