---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260717-DASHBOARD-RESPONSIVE-LAYOUT
artifact_type: plan
tags: [observability]
---

# Implementation Plan — TCK-20260717-DASHBOARD-RESPONSIVE-LAYOUT

## Summary

This ticket introduces the first responsive layout pattern in `dashboard-frontend/` by fixing two narrow-viewport (≤480px) defects: the header's non-wrapping nav row crowding the title in `App.tsx`, and the Gantt hover tooltip's unbounded-width `Tooltip.Content` overflowing the viewport edge in `RecentActivityGantt.tsx`. The approach uses Tailwind breakpoint prefixes exclusively (no raw `@media` rules, matching the codebase's all-utility-class convention): the header drops its fixed `h-14` at narrow widths, gains `flex-wrap`, and reapplies `h-14` only at `sm:` and above so a wrapped second nav line gets real vertical room instead of being clipped. The tooltip gets an explicit `collisionPadding` prop (position bound) plus a `max-w-*`/`whitespace-normal` Tailwind class (width bound) — both together, since Radix's default collision avoidance alone only repositions, it does not cap content width. Two component tests assert the specific classes/props added, and a short doc note records the new responsive behavior. All work is confined to `App.tsx`, `RecentActivityGantt.tsx`, their two test files, and one docs file — no other files from the two sibling tickets' surfaces are touched.

## Steps

### Step 1 — App.tsx header responsive wrap
**Files:** `dashboard-frontend/src/App.tsx`

**Change:** On the `<header>` element (currently line 25: `className="flex items-center px-5 h-14 border-b border-border shrink-0"`), replace the class string with one that:
- Removes the unconditional `h-14` and reapplies it only at `sm:` and above (`sm:h-14`), so narrow widths get auto height driven by content instead of a fixed 56px box.
- Adds `flex-wrap` so the `<h1>` title and `<nav>` can drop onto a second line when they don't fit on one row.
- Adds vertical breathing room for the wrapped (narrow) state — e.g. `py-2` — and neutralizes it at the wide breakpoint so the original visual spacing is preserved there — e.g. `sm:py-0`.

Concretely, target className: `flex flex-wrap items-center gap-y-2 px-5 py-2 sm:py-0 sm:h-14 border-b border-border shrink-0`.

Leave the `<h1>` (line 26) and `<nav>` (line 27) elements, `NAV_ITEMS` (lines 8-12), `PageView` type (line 6), and all button `onClick`/className logic (lines 28-40) exactly as they are — only the `<header>` element's own `className` string changes.

**Do NOT touch:** `NAV_ITEMS` array contents or ordering, the `PageView` type, any nav `<button>` element's accessible name/text/onClick, the content region below the header (lines 43-54), or any other file. Do not introduce a router library or change navigation semantics — this step is layout-only.

**Verify:** The Step 3 test in `App.test.tsx` asserting the header element carries `flex-wrap` and `sm:h-14` (or the exact class strings chosen) in its className, plus all 4 pre-existing `App.test.tsx` nav/view-switch tests (`getByRole('button', { name: ... })` queries) continue to pass unmodified.

### Step 2 — RecentActivityGantt.tsx Tooltip.Content bounding
**Files:** `dashboard-frontend/src/views/RecentActivityGantt.tsx`

**Change:** On `Tooltip.Content` (currently lines 91-93):
```
<Tooltip.Content className="rounded-md bg-bg-tertiary px-2 py-1 text-[11px] text-text-primary border border-border">
  {run.run_id} · {run.tier} · {run.workflow} · {durationLabel(run, nowIso)} · {run.agent_count} agents
</Tooltip.Content>
```
- Add `collisionPadding={8}` as an explicit prop on `Tooltip.Content` (Radix defaults `avoidCollisions=true` already, so it does not need to be set explicitly, but `collisionPadding` currently defaults to `0` and must be set so the tooltip never sits flush against the viewport edge when it flips/shifts).
- Append `max-w-[280px] whitespace-normal` to the existing className string (keep every existing class — `rounded-md bg-bg-tertiary px-2 py-1 text-[11px] text-text-primary border border-border` — and add the two new ones).
- Do not change the interpolated text content between the tags (`{run.run_id} · {run.tier} · ...`) — wrapping via `whitespace-normal` bounds the box, it does not alter the text nodes.

Resulting element: `<Tooltip.Content collisionPadding={8} className="rounded-md bg-bg-tertiary px-2 py-1 text-[11px] text-text-primary border border-border max-w-[280px] whitespace-normal">`.

**Do NOT touch:** `GanttBar.tsx`, `TimeAxis.tsx`, `Legend.tsx`, or any of their tests (TCK-20260717-GANTT-TIME-AXIS's exclusive, already-closed surface). Do not touch `Tooltip.Root`, `Tooltip.Trigger`, or `Tooltip.Portal` elements, the `Tooltip.Provider delayDuration={200}` wrapper, or any other JSX in this file outside the `Tooltip.Content` element itself. Do not change the tooltip text string or switch to a `truncate`/`text-ellipsis` approach — the ticket and existing test require full text to remain visible, wrapped rather than clipped.

**Verify:** The Step 3 test in `RecentActivityGantt.test.tsx` asserting the rendered `Tooltip.Content` DOM node carries `max-w-[280px]` and `whitespace-normal` (or the exact class strings chosen) plus a non-default `collisionPadding`, and the pre-existing "existing hover-tooltip content is unchanged after the on-chart label addition" test continues to pass unmodified.

### Step 3 — Component tests for the specific responsive classes/props
**Files:** `dashboard-frontend/src/test/App.test.tsx`, `dashboard-frontend/src/test/RecentActivityGantt.test.tsx`

**Change:**
- In `App.test.tsx`, add one test (e.g. `header wraps and relaxes fixed height at narrow widths`) that renders `<App />`, queries the header element (e.g. via `container.querySelector('header')` or a `role="banner"` query since no `data-testid` currently exists on it), and asserts its `className` string contains the literal class tokens added in Step 1 (`flex-wrap` and `sm:h-14`, matching whatever exact strings Step 1 lands on). Assert on the specific literal tokens, not just "some new class exists."
- In `RecentActivityGantt.test.tsx`, add one test (e.g. `Tooltip.Content is bounded by a max-width/whitespace class and explicit collisionPadding`) that renders `<RecentActivityGantt />` with at least one run (reuse the existing fixture/mock pattern already in the file), triggers the tooltip the same way the existing hover-tooltip test does, and asserts the rendered `Tooltip.Content` node's className contains `max-w-[280px]` and `whitespace-normal` (matching Step 2's exact strings). If the `collisionPadding` prop value is not observable through Radix's rendered DOM output in jsdom, fall back to a source-text regex guard against the component file (matching the pattern `TimeAxis.test.tsx` used for the `toPercent`-import guard) asserting `collisionPadding={8}` appears in the source — scoped only to `RecentActivityGantt.tsx`.
- Both tests must assert the *specific* literal class/prop strings chosen in Steps 1 and 2, not a generic "has some class" check — this is what satisfies AC #3.

**Do NOT touch:** Any other test file (`GanttBar.test.tsx`, `TimeAxis.test.tsx`, `TicketsView.test.tsx`, `ReplayTimelineView.test.tsx`, `useRunsPolling.test.ts`) — these must remain green as unmodified sibling-surface guards. Do not modify any of the 4 pre-existing `App.test.tsx` tests or the pre-existing tooltip-content test in `RecentActivityGantt.test.tsx` beyond what's needed to keep them passing against the Step 1/2 changes (they should need no changes at all if Steps 1-2 are additive-only, as specified).

**Verify:** `cd dashboard-frontend && npx vitest run` — full suite green, including the two new tests and all pre-existing tests listed in `test_plan.md`'s Regression Surface section.

### Step 4 — Doc note on responsive behavior
**Files:** `docs/guides/agent_ops_dashboard.md`

**Change:** Add a short new section (e.g. `## Responsive Behavior`) documenting: (1) at viewport widths ≤480px (roughly `sm:` breakpoint and below), the header's nav wraps to a second line below the title instead of crowding it, with the header's height no longer fixed at narrow widths; (2) the Recent Activity Gantt view's hover tooltip is bounded to a max width and wraps text rather than overflowing the viewport edge. Keep this to a few sentences — a behavior note, not a full UX spec. Do not add this section to `docs/observability/agent_ops_dashboard_contract.md` as well (the ticket only requires one of the two locations); `agent_ops_dashboard.md` is chosen because it is the user-facing guide, and UI/UX behavior notes fit its existing structure better than the contract doc's architecture-law framing.

**Do NOT touch:** Any other section of `agent_ops_dashboard.md`, or `docs/observability/agent_ops_dashboard_contract.md` at all. Do not run `make knowledge-index-update` until this step lands (it's required once any `docs/` file changes, per project workflow — do it after this step, not before).

**Verify:** Manual review — AC #4 has no automated test per `test_plan.md`; confirm the new section exists and accurately describes the Step 1/2 behavior before closing the ticket.

## Scope Guards

- Do not touch `dashboard-frontend/src/views/TicketsView.tsx` or `dashboard-frontend/src/test/TicketsView.test.tsx` — exclusive, already-closed surface of TCK-20260717-TICKETS-TAG-SEARCH. That sibling ticket's tag-control cap (≤40 buttons) is treated as sufficient resolution of the Tickets view's narrow-viewport height concern for this ticket's purposes; do not re-open or re-solve it here.
- Do not touch `dashboard-frontend/src/components/GanttBar.tsx`, `dashboard-frontend/src/components/TimeAxis.tsx`, `dashboard-frontend/src/components/Legend.tsx`, or their tests — exclusive, already-closed surface of TCK-20260717-GANTT-TIME-AXIS. Only `RecentActivityGantt.tsx`'s own `Tooltip.Content` JSX is in scope on the Gantt side.
- Do not perform a full mobile-first redesign of the Recent Activity, Tickets, or Replay views beyond the header (`App.tsx`) and the Gantt tooltip (`RecentActivityGantt.tsx`) — explicitly Out of Scope in the ticket.
- Do not add raw `@media` rules to `dashboard-frontend/src/index.css` — use Tailwind breakpoint prefixes exclusively, consistent with the codebase's existing all-utility-class convention (no `@media` precedent exists anywhere in the codebase today).
- Do not add a router library, or change `PageView` type semantics or `NAV_ITEMS` contents/ordering, while touching `App.tsx`'s header.
- Do not alter the Gantt tooltip's interpolated text content or switch to a `truncate`/`text-ellipsis` approach that would hide run detail on hover — wrapping only.
- Do not touch items #3 (Tier/Layer column spacing — already fixed elsewhere), #4 (duplicate Ticket/Title columns), or #6 (unpaginated table) from `proposal_ui_review_findings.md` — unrelated, separately tracked concerns.
- Do not update any `docs/parity_ledger/` file — this is a frontend-only presentational change with no parity ledger overlap (confirmed in investigation.md; matches the pattern of both prior sibling frontend tickets).
- Do not add the doc note to both `docs/guides/agent_ops_dashboard.md` and `docs/observability/agent_ops_dashboard_contract.md` — one location only, per Step 4.

## Dependency Map

- Step 1 (App.tsx header) and Step 2 (RecentActivityGantt.tsx tooltip) are fully independent — different files, no shared state, can be done in either order or in parallel.
- Step 3 depends on both Step 1 and Step 2 landing first — its assertions reference the exact literal class/prop strings those steps introduce.
- Step 4 (docs) has no code dependency but should be written last so the described behavior matches what Steps 1-2 actually implemented, not a planned approximation.
- Recommended order: Step 1 → Step 2 → Step 3 → Step 4 (matches the ticket's own step ordering).

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC #1 — header nav wraps / no longer overlaps title at ≤480px | Step 1 | `App.test.tsx` new test (Step 3) asserting `flex-wrap`/`sm:h-14` classes present; pre-existing 4 nav tests still pass |
| AC #2 — Tooltip.Content bounded by max-width, wraps, never extends past viewport edge at 480px | Step 2 | `RecentActivityGantt.test.tsx` new test (Step 3) asserting `max-w-[280px]`/`whitespace-normal`/`collisionPadding` present; pre-existing tooltip-content-unchanged test still passes |
| AC #3 — component test asserts the specific responsive classes/media rules added to both files | Step 3 | Step 3's two new tests themselves, by asserting literal class/prop strings (not generic presence checks) |
| AC #4 — short responsive-behavior doc note added | Step 4 | Manual review (no automated test per test_plan.md) |

## Anti-Drift Notes

- jsdom (vitest's test runner) does not perform real CSS layout — the Step 3 tests can only assert that the correct responsive classes/props are present in markup, not that they visually prevent overlap/overflow at an actual 480px browser viewport. This is a known, accepted verification gap per the ticket's own Assumptions — do not attempt to work around it with a headless-browser or visual-regression tool, that would be scope creep beyond this ticket.
- Radix's `avoidCollisions` already defaults to `true` — do not add it as an explicit prop unnecessarily; the missing piece is `collisionPadding` (defaults to `0`, must be set) and the Tailwind width/wrap classes (position-only fixes don't bound content width).
- Before finalizing, run a `git diff --stat` scope check confirming `TicketsView.tsx`, `TicketsView.test.tsx`, `GanttBar.tsx`, `TimeAxis.tsx`, and `Legend.tsx` (and their tests) do not appear in the diff — these are the two sibling tickets' exclusive, already-closed surfaces.
- Keep the `RecentActivityGantt.test.tsx` "existing hover-tooltip content is unchanged after the on-chart label addition" test passing unmodified — it is the concrete guard that Step 2's wrapping approach didn't drop or truncate any text.
- Keep all 4 pre-existing `App.test.tsx` nav/view-switch tests passing unmodified — they are the concrete guard that Step 1's header restructuring didn't alter any nav button's accessible name or click behavior.
- No parity ledger entry is needed for this ticket (frontend-only presentational change, confirmed in investigation.md) — do not create one speculatively.
- Run `make knowledge-index-update` after Step 4 lands, since it modifies a file under `docs/`.

## Deviations

One implementation-detail deviation from Step 3's test guidance, discovered while writing the
`RecentActivityGantt.test.tsx` new test:

- The plan anticipated asserting `max-w-[280px]`/`whitespace-normal` directly on the node returned by
  `screen.findByText(...)` (mirroring the pre-existing tooltip-content test's pattern). In practice,
  Radix's `Tooltip.Content` renders the interpolated text twice — once in the visible content div,
  and once inside an inner `VisuallyHidden` `<span role="tooltip">` used for `aria-describedby`
  accessibility wiring — and Testing Library's `findByText`/`getByText` matching returns only the
  deepest ("leaf") element whose own text matches, which is the hidden `<span>`, not the
  `Tooltip.Content` div carrying the className. Confirmed via a throwaway debug test that dumped
  `document.body.innerHTML`. Fixed by walking up from the matched node with
  `tooltip.closest('[data-side]')` — `data-side` is a Radix-emitted attribute unique to the actual
  `Tooltip.Content` div — to reach the element that actually carries `max-w-[280px] whitespace-normal`.
  This does not change what is asserted (the exact literal class strings from Step 2), only how the
  correct DOM node is located. No change to Steps 1, 2, or 4 as planned.
