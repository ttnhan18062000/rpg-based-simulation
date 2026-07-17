---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260717-DASHBOARD-RESPONSIVE-LAYOUT
phase: done
date: 2026-07-17
tags: []
---

# TCK-20260717-DASHBOARD-RESPONSIVE-LAYOUT

## Title
Add responsive layout to the dashboard header and Gantt tooltip for narrow viewports

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
At a 480px viewport width, the header nav crowds directly against the "Agent Ops Dashboard" title with no wrapping or spacing, and the Gantt tooltip box overflows/clips past the right edge of the viewport instead of repositioning. Investigation confirmed there is zero responsive design anywhere in dashboard-frontend today — no Tailwind breakpoint prefixes (sm:/md:/lg:) and no @media rules exist in the codebase at all. This is greenfield UX work, not a fix to a documented-but-broken behavior.

## Scope
- Add responsive wrapping to App.tsx's header container (nav + title) so they no longer overlap/crowd at narrow widths.
- Bound RecentActivityGantt.tsx's Tooltip.Content with a max-width/whitespace constraint so it never extends past the viewport edge at 480px width, in combination with Radix's existing collisionPadding/avoidCollisions.
- Add a test asserting the specific responsive utility classes/media rules added to App.tsx and RecentActivityGantt.tsx are present.

## Out of Scope
- Fixing the Tickets view's tag-button wall layout itself — that is covered by TCK-20260717-TICKETS-TAG-SEARCH; this ticket depends on that one landing so the Tickets view's narrow-viewport height issue resolves jointly rather than being re-solved here.
- Full mobile-first redesign of all three views beyond the header and Gantt tooltip.

## Acceptance Criteria
- [ ] At viewport widths <=480px, App.tsx's header nav wraps to a new line or otherwise no longer overlaps the "Agent Ops Dashboard" title.
- [ ] RecentActivityGantt.tsx's Tooltip.Content is bounded by a max-width and wraps or truncates so its rendered box never extends past the right viewport edge at 480px width.
- [ ] A component test asserts the specific responsive utility classes/media rules added to App.tsx and RecentActivityGantt.tsx are present.
- [ ] A short responsive-behavior note is added to docs/guides/agent_ops_dashboard.md or docs/observability/agent_ops_dashboard_contract.md.

## Related Tickets
- TCK-20260717-TICKETS-TAG-SEARCH
- TCK-20260716-AGENTOPS-DASHBOARD-BACKEND

## Related Docs
- docs/guides/agent_ops_dashboard.md
- docs/observability/agent_ops_dashboard_contract.md

## Related Stored Artifacts
None.

## Related Code Areas
- dashboard-frontend/src/App.tsx
- dashboard-frontend/src/views/RecentActivityGantt.tsx
- dashboard-frontend/src/index.css
- dashboard-frontend/src/test/App.test.tsx

## Assumptions / Open Questions
- jsdom (the existing test runner) does not perform real CSS layout, so new tests can only assert responsive classes/props are present in markup, not verify actual browser-rendered overflow at 480px.
- No responsive requirement is currently documented anywhere in the dashboard's docs — this is greenfield UX work.

## Implementation Notes
Implemented per `staging_artifacts/TCK-20260717-DASHBOARD-RESPONSIVE-LAYOUT/plan.md` Steps 1-4, in order.

- **Step 1** (`dashboard-frontend/src/App.tsx`): `<header>` className changed from
  `flex items-center px-5 h-14 border-b border-border shrink-0` to
  `flex flex-wrap items-center gap-y-2 px-5 py-2 sm:py-0 sm:h-14 border-b border-border shrink-0`
  — exactly the string specified in the plan. No other JSX in the file touched.
- **Step 2** (`dashboard-frontend/src/views/RecentActivityGantt.tsx`): `Tooltip.Content` gained
  `collisionPadding={8}` as an explicit prop and `max-w-[280px] whitespace-normal` appended to its
  className, matching the plan's target element exactly. Interpolated text content and all other JSX
  untouched.
- **Step 3** (tests): added one test to each file.
  - `App.test.tsx`: `header wraps and relaxes fixed height at narrow widths` — queries
    `container.querySelector('header')` and asserts the className contains the literal tokens
    `flex-wrap` and `sm:h-14`, and does not contain an unconditional (non-`sm:`-prefixed) `h-14` via a
    negative-lookbehind regex, confirming the unconditional fixed height was actually removed rather
    than just having `sm:h-14` appended alongside it.
  - `RecentActivityGantt.test.tsx`: `Tooltip.Content is bounded by a max-width/whitespace class and
    explicit collisionPadding` — reuses the exact hover-trigger sequence (`pointerenter`/`pointermove`/
    `focus`) from the pre-existing tooltip-content test. One deviation from the plan's literal text
    (documented below): `screen.findByText` on the interpolated string returns the visually-hidden
    accessibility `<span role="tooltip">` leaf node (Radix renders the same text twice — once visibly,
    once in a `VisuallyHidden` span for `aria-describedby` — and Testing Library's text query returns
    only leaf-level matches), not the `Tooltip.Content` div itself, so the test walks up via
    `tooltip.closest('[data-side]')` to reach the actual content div carrying the className. Also added
    a source-text regex guard (`RECENT_ACTIVITY_GANTT_SOURCE` via Vite's `?raw` import, same pattern
    `TimeAxis.test.tsx` uses for its `toPercent`-import guard) asserting `collisionPadding={8}` appears
    literally in `RecentActivityGantt.tsx`, since `collisionPadding` is consumed internally by Radix's
    Popper positioning and is not otherwise observable as a DOM attribute in jsdom.
  - All pre-existing tests in both files (4 in `App.test.tsx`, 10 in `RecentActivityGantt.test.tsx`)
    pass unmodified.
- **Step 4** (`docs/guides/agent_ops_dashboard.md`): added a "Responsive Behavior" section (before
  "Known limitation") describing the header wrap/height relaxation at the `sm:` breakpoint and the
  Gantt tooltip's max-width/wrap bounding. This step was **done, not deferred** — confirmed present in
  the file before ticket close. Ran `make knowledge-index-update` afterward (required since a
  `docs/` file changed); completed successfully (4 files re-embedded, 5897 chunks total).

No deviations from the plan's architecture or scope guards. `docs/parity_ledger/infrastructure.yaml`
was not touched, per the plan's explicit instruction (frontend-only presentational change, no wire
contract).

## Test Summary
`cd dashboard-frontend && npx vitest run` — 7 test files, 56 tests, all passing (including the 2 new
tests from Step 3). Also ran `npx tsc --noEmit` (clean) and `npm run build` (clean, `vite build`
succeeded) to confirm no type or build regressions from the className/prop changes.

Scope-guard check: `git diff --stat` confirms no changes to `TicketsView.tsx`, `TicketsView.test.tsx`,
`GanttBar.tsx`, `TimeAxis.tsx`, `Legend.tsx`, or their tests as part of this ticket's work (those files
show pre-existing uncommitted changes from sibling tickets TCK-20260717-TICKETS-TAG-SEARCH and
TCK-20260717-GANTT-TIME-AXIS already present in the working tree before this session started — this
ticket's own diff to `RecentActivityGantt.tsx` is limited to the `Tooltip.Content` element only, as
confirmed by direct `git diff` inspection of that file's hunks).

## Files Changed
- `dashboard-frontend/src/App.tsx`
- `dashboard-frontend/src/views/RecentActivityGantt.tsx`
- `dashboard-frontend/src/test/App.test.tsx`
- `dashboard-frontend/src/test/RecentActivityGantt.test.tsx`
- `docs/guides/agent_ops_dashboard.md`
- `tickets/inprogress/TCK-20260717-DASHBOARD-RESPONSIVE-LAYOUT.md` (this file)
- `staging_artifacts/TCK-20260717-DASHBOARD-RESPONSIVE-LAYOUT/plan.md` (Deviations section)

## Completion Summary
All 4 acceptance criteria met: (1) header nav wraps and the fixed `h-14` height is relaxed to
`sm:h-14` so a wrapped second line has room at narrow widths; (2) `Tooltip.Content` is bounded by
`max-w-[280px] whitespace-normal` plus an explicit `collisionPadding={8}`; (3) both `App.test.tsx` and
`RecentActivityGantt.test.tsx` carry new tests asserting the literal class/prop strings added, not
generic presence checks; (4) a "Responsive Behavior" section was added to
`docs/guides/agent_ops_dashboard.md` (done, not deferred) and `make knowledge-index-update` was run
afterward. No parity ledger update was needed or made (frontend-only presentational change, per
investigation.md and the plan's explicit scope guard). Full `vitest` suite (56 tests), `tsc --noEmit`,
and `vite build` all pass clean.
