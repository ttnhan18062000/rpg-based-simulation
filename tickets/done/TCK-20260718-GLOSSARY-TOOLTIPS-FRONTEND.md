---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260718-GLOSSARY-TOOLTIPS-FRONTEND
phase: done
date: 2026-07-18
tags: [dashboard, observability, api-design]
---

# TCK-20260718-GLOSSARY-TOOLTIPS-FRONTEND

## Title
Hover tooltips across the dashboard sourced from the backend-owned glossary

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Child of `TCK-20260718-GLOSSARY-TOOLTIPS-EPIC`, depends on `TCK-20260718-GLOSSARY-API`. Wire
hover tooltips onto closed-enum labels across the dashboard (Tickets, Replay, Stats views),
fetching descriptions from `/api/glossary` — never hardcoded in the frontend.

## Scope
- `api.ts`: `fetchGlossary()` + `useGlossary()` hook (fetch-once singleton, graceful degradation).
- `components/GlossaryTooltip.tsx` (new): shared tooltip wrapper, renders children unwrapped on
  no-match.
- `views/TicketsView.tsx`: Tier/Layer/workflow-status/Priority cells wrapped.
- `views/ReplayTimelineView.tsx`: event `status` wrapped.
- `components/BarChart.tsx` / `GroupedBarChart.tsx`: optional `descriptions` prop appending a
  second tooltip-content line.
- `views/StatsView.tsx`: glossary wired into all 5 chart usages + Slow Runs `final_status` cell.
- Tests: `GlossaryTooltip.test.tsx` (new, 5), `BarChart.test.tsx` (+2), `StatsView.test.tsx` (+3).

## Out of Scope
- `GanttBar.tsx` / `Legend.tsx` — checked and deliberately excluded (see investigation.md):
  `GanttBar.tsx` renders only `run.run_id` as text, never a raw status string; `Legend.tsx`'s
  three items are hand-written descriptive prose, not a single glossary term.
- Ticket frontmatter `status` (`active`/`historical`/...) — different doc-lifecycle enum, not in
  the glossary registry's category set.
- Replay's `call.status`/`tailCall.status` (tool-call-level status) — different, unconfirmed
  vocabulary from event-status.
- `TCK-20260718-GLOSSARY-DOCS-UPDATE`'s scope (docs updates).

## Acceptance Criteria
- [x] Tier/Layer/ticket-status/Priority cells in Tickets view show real backend descriptions on
      hover.
- [x] Event status in Replay view and gate-failure/reason-code/distribution bar labels + Slow Runs
      status in Stats view show real backend descriptions on hover.
- [x] Zero hardcoded description strings in `dashboard-frontend/src/` — enforced by a source-string
      anti-drift test guard.
- [x] Glossary fetched exactly once per app load — `fetchGlossary(` has exactly one call site
      (inside `useGlossary()`'s module-level singleton), confirmed by grep.
- [x] Graceful degradation: no crash when a term is null, unmatched, or glossary hasn't loaded —
      verified at two code layers and by dedicated tests.
- [x] 82/82 frontend tests passing, `tsc -b --noEmit` clean, `npm run build` clean.
- [x] Live-verified via headless Chromium against a freshly rebuilt `make dashboard-serve`: 5
      distinct label types across Tickets and Stats views show real backend-sourced description
      text on hover, zero console errors.
- [x] Deliberate Gantt/Legend exclusion re-confirmed by direct source read and documented, not
      silently skipped.

## Related Tickets
- TCK-20260718-GLOSSARY-TOOLTIPS-EPIC (parent epic)
- TCK-20260718-GLOSSARY-API (depended on)
- TCK-20260718-GLOSSARY-REGISTRY (transitively depended on)
- TCK-20260718-GLOSSARY-DOCS-UPDATE (depends on this ticket)

## Related Docs
- docs/plans/agent_ops_dashboard/proposal_glossary_tooltips.md

## Related Stored Artifacts
- stored_artifacts/TCK-20260718-GLOSSARY-TOOLTIPS-FRONTEND/

## Related Code Areas
- dashboard-frontend/src/api.ts
- dashboard-frontend/src/components/GlossaryTooltip.tsx
- dashboard-frontend/src/components/BarChart.tsx
- dashboard-frontend/src/components/GroupedBarChart.tsx
- dashboard-frontend/src/views/TicketsView.tsx
- dashboard-frontend/src/views/ReplayTimelineView.tsx
- dashboard-frontend/src/views/StatsView.tsx

## Assumptions / Open Questions
None — the one open implementation question (StatsView-level jsdom hover flake) was resolved by
moving the real hover-content proof to `BarChart.test.tsx` in isolation; see investigation.md.

## Implementation Notes
Executed directly (Read/Edit/Bash/Write) — no Agent-tool subagent access in this execution
context, consistent with tickets 1 and 2 of this epic. Implementation work (all `api.ts`,
`GlossaryTooltip.tsx`, view wiring, and test files) was completed before a session-limit cutoff
interrupted the work mid-way through writing `BarChart.test.tsx`'s hover tests; this ticket file
itself — following this session's established "implement first, document last" per-ticket
pattern — was written after the cutoff, once the remaining implementation, live verification, and
scope-exclusion re-confirmation were completed. No file was ever created then removed; the ticket
file simply had not yet been written when the cutoff hit.

Re-verified after resuming: `BarChart.test.tsx` in isolation still 5/5 passing (survived the
cutoff intact), full frontend suite 82/82, `tsc -b --noEmit` clean, `npm run build` clean, zero
hardcoded-description grep hits in `views/*.tsx`/`components/*.tsx`.

Live verification required killing/confirming no stale `dashboard-serve` process (recurring
false-negative this session — confirmed via `pgrep -af`/`curl` this time, none was running),
rebuilding fresh, then driving real headless-Chromium hover interactions. One hover attempt
(`OPEN` ticket-status cell) showed no tooltip on the first pass using a fixed-delay wait; re-tested
immediately with `page.waitForSelector(..., {timeout: 2000})` instead of a fixed sleep and the
tooltip appeared correctly with the real backend description — traced to a timing race in the
verification script itself, not a product defect.

## Test Summary
`cd dashboard-frontend && npm run test -- --run` — 11 files / 82 tests passing.
`npx tsc -b --noEmit` — clean. `npm run build` — clean (72 modules, `dist/assets/index-BTY5NTAg.js
285.02 kB`). Live headless-Chromium verification: 5/5 target hovers (Tickets Layer/ticket-status/
Priority cells, Stats reason-code bar row, Stats Slow Runs run-status cell) showed real
backend-sourced text, zero console errors.

## Files Changed
- dashboard-frontend/src/api.ts (`fetchGlossary`/`useGlossary`)
- dashboard-frontend/src/components/GlossaryTooltip.tsx (new)
- dashboard-frontend/src/components/BarChart.tsx (`descriptions` prop)
- dashboard-frontend/src/components/GroupedBarChart.tsx (`descriptions` prop)
- dashboard-frontend/src/views/TicketsView.tsx (glossary wiring)
- dashboard-frontend/src/views/ReplayTimelineView.tsx (glossary wiring)
- dashboard-frontend/src/views/StatsView.tsx (glossary wiring)
- dashboard-frontend/src/test/GlossaryTooltip.test.tsx (new)
- dashboard-frontend/src/test/BarChart.test.tsx (+2 tests)
- dashboard-frontend/src/test/StatsView.test.tsx (+3 tests, `mockFetch` extended)

## Completion Summary
Hover tooltips are live across Tickets, Replay, and Stats views, sourced entirely from
`/api/glossary` — zero hardcoded description strings, enforced by an anti-drift source guard.
Fetched once per app load. Gantt/Legend deliberately excluded (no 1:1 enum-to-term mapping exists
there) and that decision is now documented, not silent. Live-verified via headless Chromium
against a freshly rebuilt server. Unblocks `TCK-20260718-GLOSSARY-DOCS-UPDATE`.
