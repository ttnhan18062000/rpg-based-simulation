---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260718-FILTER-SELECT-DROPOUT
phase: done
date: 2026-07-18
tags: [debugging]
---

# TCK-20260718-FILTER-SELECT-DROPOUT

## Title
Fix Tier/Layer/Priority filter dropdowns visually reverting to "All" when a combined filter selection yields zero matches

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
The Agent Ops Dashboard's Tickets view filter dropdowns (Tier/Layer/Priority)
visually revert to "All" when combined with another active filter yields
zero matching tickets, even though the underlying filter is still actually
applied. Reported by the user and reproduced live: selecting Layer=economy
correctly shows the dropdown as "economy". Selecting Status=BLOCKED next
(this combination has zero matching tickets) causes the Layer dropdown to
visually revert to blank/"All" even though the actual filter state never
changed. The user confirmed this generalizes to any combination of
Tier/Layer/Priority filters that together yield zero matches, not just this
one example.

## Scope
- Fix `FilterSelect` in `dashboard-frontend/src/views/TicketsView.tsx` so
  its rendered `<option>` list always includes an entry for the
  currently-selected filter value, even when that value is absent from the
  `options` prop (which happens whenever the backend's corpus-derived facet
  for that dimension collapses to `[]` under the current combined filter).
- Add regression test coverage for this exact scenario.
- Live-verify the fix against the real running dashboard and real ticket
  corpus (not just the unit test's mocked fixture).

## Out of Scope
- Any change to `src/api/agent_ops_dashboard/ingest.py`'s facets
  computation or its intentional "derived from the filtered corpus"
  behavior for tiers/layers/priorities/tags — that behavior itself is
  correct and unchanged; only the frontend rendering gap it exposes is
  being fixed.
- The Status facet's canonical-list behavior
  (`TCK-20260718-STATUS-FACET-CANONICAL`, already closed) — not revisited.

## Acceptance Criteria
- [x] Selecting a Tier/Layer/Priority value, then a second filter whose
      combined result has zero matching tickets, no longer causes the first
      filter's dropdown to visually revert to "All" — it continues to show
      the actually-selected value.
- [x] A new test in `TicketsView.test.tsx` covers this exact scenario and
      fails without the fix (verified via `git stash` before closing).
- [x] The fix does not alter `filters` React state or the query params sent
      to the backend on subsequent filter changes — confirmed the
      "invisible" filter is still included in the next request URL.
- [x] Live-verified against the real running dashboard (`make
      dashboard-serve` + headless browser) reproducing the user's exact
      reported scenario (Layer=economy, then Status=BLOCKED).

## Related Tickets
- TCK-20260718-STATUS-FACET-CANONICAL (established the precedent this
  ticket follows for Status specifically; this ticket covers the remaining
  Tier/Layer/Priority dimensions' rendering gap)
- TCK-20260717-TICKETS-TAG-SEARCH (introduced `FilterSelect`'s sibling tag
  filter UI in the same view)

## Related Docs
None — this is a UI rendering bug fix with no documented-behavior change.

## Related Stored Artifacts
None (hotfix — self-evident intent captured in this ticket, no staging artifacts created).

## Related Code Areas
- `dashboard-frontend/src/views/TicketsView.tsx`
- `dashboard-frontend/src/test/TicketsView.test.tsx`

## Assumptions / Open Questions
None.

## Implementation Notes
Executed directly (Read/Edit/Bash/Write tool calls) rather than via the
standard Scope→Investigate→Plan→Review→Implement→Architecture-Verify→Test→
Parity→Verify→Finalize multi-agent pipeline — this execution context (a
forked worker) had no Agent-tool access (hard runtime rule prohibiting
further subagent spawns), matching the pattern several prior tickets this
session hit. All the same work products (investigation.md, plan.md,
test_plan.md, this ticket file, the code/test changes, and the verification
steps below) were produced directly instead.

Root cause confirmed live before any fix was written: `curl
"http://localhost:8420/api/tickets?layer=economy&status=BLOCKED&limit=1"`
returns `total_count: 0, facets.layers: []`. A Playwright script driving the
real running app confirmed the Layer `<select>`'s DOM value silently changed
from `"economy"` to `""` after selecting that Status, with its rendered
`<option>` count dropping from several to 1.

Fix: `FilterSelect` (TicketsView.tsx ~95-114) now computes
`selectedValueMissingFromOptions = value !== '' && !options.includes(value)`
and, when true, renders a synthetic `<option value={value}>{value}</option>`
alongside the corpus-derived `options` list — guaranteeing the `<select>`
always has a matching `<option>` for its true current value. Used
`.includes(`, not `.filter(`, to keep the existing anti-drift source-text
guard (`TicketsView.test.tsx`'s `not.toMatch(/\.filter\(/)`) passing —
confirmed via direct test run.

Added one new test (`'Layer select keeps showing the selected value (not
"All") when a combined filter yields zero matches and an empty layers
facet'`) that reproduces the exact bug via mocked fetch responses. Verified
the test genuinely catches the regression: `git stash`'d the fix, re-ran
just this test, confirmed it fails with `AssertionError: expected '' to be
'economy'` — the exact symptom reported — then restored the fix via `git
stash pop` and confirmed all 59 tests pass again.

Live re-verified post-fix: re-ran the identical Playwright reproduction
script against a freshly-built `make dashboard-serve` instance (had to kill
a stale server process left running from earlier in the session on the same
port, which caused one false-negative live-check before the restart) —
confirmed the Layer select's value now correctly stays `"economy"` after
selecting Status=BLOCKED, with 2 rendered options (All + the synthetic
economy entry, since the real backend facets.layers came back empty for
that zero-match combination).

Confirmed frontend-only per scope guard: `git status --porcelain` after
Implement shows only `dashboard-frontend/src/views/TicketsView.tsx` and
`dashboard-frontend/src/test/TicketsView.test.tsx` changed — no
`src/api/agent_ops_dashboard/` or `docs/parity_ledger/` file touched, so no
parity ledger entry is needed for this ticket.

## Test Summary
- `cd dashboard-frontend && npm test -- --run` — 59/59 passing (58
  pre-existing + 1 new).
- `cd dashboard-frontend && npx tsc -b --noEmit` — clean, no errors.
- `cd dashboard-frontend && npm run build` — production build succeeds.
- Regression-catching verified: new test fails (`AssertionError: expected
  '' to be 'economy'`) against the pre-fix code via `git stash`, passes
  again after `git stash pop` restores the fix.
- Live verification: `make dashboard-serve` + Playwright script reproducing
  the user's exact reported scenario against the real running app and real
  ticket corpus — Layer select value confirmed to stay `"economy"` after
  selecting Status=BLOCKED (previously became `""`).

## Files Changed
- `dashboard-frontend/src/views/TicketsView.tsx` (`FilterSelect`: synthetic
  fallback `<option>` for a selected value missing from `options`)
- `dashboard-frontend/src/test/TicketsView.test.tsx` (new regression test)

## Completion Summary
Fixed a frontend rendering bug where the Tickets view's Tier/Layer/Priority
filter dropdowns visually reverted to "All" whenever a combined filter
selection yielded zero matching tickets, even though the underlying filter
was still correctly applied — root cause was an HTML `<select>`'s inability
to display a `value` for which no matching `<option>` exists once the
backend's corpus-derived facet for that dimension collapsed to `[]`. Fixed
by always rendering a synthetic `<option>` for the currently-selected value
when the corpus-derived options list doesn't already include it. Frontend-
only change (confirmed via git diff scope), no parity ledger entry needed.
59/59 tests passing, fix verified to actually catch the regression via a
stash/restore cycle, and re-verified live against the real running app
reproducing the user's exact reported scenario.
