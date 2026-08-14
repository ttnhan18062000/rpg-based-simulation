---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260717-DASHBOARD-RESPONSIVE-LAYOUT
artifact_type: test_plan
tags: [observability]
---

# Test Plan — TCK-20260717-DASHBOARD-RESPONSIVE-LAYOUT

## Regression Surface

All under `dashboard-frontend/` — this ticket has no backend/Python behavior change, so the frontend `vitest` suite is the primary regression surface. Group as unit/component (this SPA has no separate integration tier beyond component-render tests):

- `dashboard-frontend/src/test/App.test.tsx` — 4 tests: default-landing view, tab-switch scaffold smoke test, row-link navigation, Gantt-row-click navigation. Header markup changes must not break the `getByRole('button', { name: ... })` queries these rely on.
- `dashboard-frontend/src/test/RecentActivityGantt.test.tsx` — must keep passing in full, especially "existing hover-tooltip content is unchanged after the on-chart label addition" (asserts the literal tooltip text string) and the axis/on-chart-label tests added by TCK-20260717-GANTT-TIME-AXIS.
- `dashboard-frontend/src/test/GanttBar.test.tsx`, `dashboard-frontend/src/test/TimeAxis.test.tsx` — unaffected by this ticket's scope; must remain green as a sibling-surface guard.
- `dashboard-frontend/src/test/TicketsView.test.tsx` — unaffected (explicitly out of scope); must remain green as a sibling-surface guard.
- `dashboard-frontend/src/test/ReplayTimelineView.test.tsx`, `dashboard-frontend/src/test/useRunsPolling.test.ts` — unaffected; part of the same full-suite run.

Backend architecture guard (Python, scoped — confirms this frontend-only change didn't introduce a backend import):

- `tests/tools/test_agent_ops_dashboard_frontend_api_surface.py` — asserts the frontend never imports `src/api/server.py`, `read_model_cache.py`, `routes/history.py`, or `ws/stream.py`.

## New Tests Required

Per Acceptance Criteria:

- **AC #1 — header wraps at ≤480px.**
  - Test name: `header nav wraps to a new line / no longer overlaps title at narrow width` (or equivalent).
  - Category: unit/component (DOM-class assertion — jsdom cannot verify actual visual wrap, per the ticket's own Assumption).
  - What it verifies: renders `<App />`, asserts the header container element and/or its title/nav children carry the specific new responsive utility class(es) (e.g. `flex-wrap`, a `sm:`-prefixed class, or an added `@media`-driven class name) that the implementation adds — a structural presence check, not a rendered-layout check.
  - Location: `dashboard-frontend/src/test/App.test.tsx`.

- **AC #2 — Gantt tooltip bounded, never overflows viewport edge at 480px.**
  - Test name: `Tooltip.Content is bounded by a max-width/whitespace class so it does not extend past the viewport edge` (or equivalent).
  - Category: unit/component (DOM-class/prop assertion).
  - What it verifies: renders `<RecentActivityGantt />` with at least one run, triggers the tooltip (hover/focus per existing tooltip test pattern in the file), and asserts the rendered `Tooltip.Content` DOM node's className contains the new `max-w-*` and `whitespace-normal`/`break-words` (or equivalent) utility classes. If `collisionPadding`/`avoidCollisions` are set explicitly as props (recommended per investigation.md Risk #3), also assert those prop values are non-default/present — via a source-text guard if DOM-level prop assertion isn't feasible through Radix's rendered output.
  - Location: `dashboard-frontend/src/test/RecentActivityGantt.test.tsx`.

- **AC #3 — a component test asserts the specific responsive utility classes/media rules added to App.tsx and RecentActivityGantt.tsx are present.**
  - This AC is explicitly about *having* such a test, not a separate behavior — it is satisfied by the AC #1 and AC #2 tests above, provided each explicitly asserts the *specific* class names/props added (not just "some" class present). No additional test is required beyond making sure those two tests assert on the specific literal class strings the implementation adds. If the implementer prefers a single dedicated assertion covering both files (matching the source-text-regex anti-drift pattern TCK-20260717-GANTT-TIME-AXIS used for `TimeAxis.test.tsx`'s `toPercent`-import guard), that is an acceptable alternative — this is a structural choice for `plan.md`, not prescribed here.
  - Category: unit/component or architecture guard (source-text regex), implementer's choice.
  - Location: `dashboard-frontend/src/test/App.test.tsx` and `dashboard-frontend/src/test/RecentActivityGantt.test.tsx` (or a new dedicated test file, if isolation is preferred).

- **AC #4 — responsive-behavior doc note.**
  - No automated test required; this is a documentation-only criterion. Verify manually that `docs/guides/agent_ops_dashboard.md` or `docs/observability/agent_ops_dashboard_contract.md` gains a short section describing the new responsive behavior before closing the ticket.

## Scoped Pytest Commands

This ticket is frontend-only; `vitest` (not `pytest`) is the primary regression tool. Run, in order:

```
cd dashboard-frontend && npx vitest run
cd dashboard-frontend && npx tsc -b --noEmit
cd dashboard-frontend && npm run build
```

Scoped backend guard (Python, confirms no accidental backend coupling was introduced by this frontend change):

```
python3 -m pytest tests/tools/test_agent_ops_dashboard_frontend_api_surface.py -m "not slow"
```

Do **not** run `pytest tests/` broadly — no backend/simulation logic is touched by this ticket's scope, and the project Testing Rule requires scoping to the domain under modification.

## Anti-Drift Test Guards

- `RecentActivityGantt.test.tsx`'s existing "existing hover-tooltip content is unchanged after the on-chart label addition" test must keep passing unmodified after this ticket's change — confirms the new max-width/whitespace classes wrap rather than drop/truncate the tooltip's text content. If a `truncate`/`text-ellipsis` approach is chosen instead of wrapping, this test (and its intent — full run detail visible on hover) needs explicit re-evaluation, not a silent pass-through.
- `App.test.tsx`'s 4 existing nav/view-switch tests (`getByRole('button', { name: ... })` queries) must keep passing unchanged — confirms the header restructuring for wrap behavior doesn't alter the accessible name/structure of the nav buttons.
- A `git diff --stat` scope check confirming `TicketsView.tsx` and `TicketsView.test.tsx` are **not** touched by this ticket's diff — guards against re-solving the Tickets view's tag-wall issue here, which is explicitly Out of Scope and delegated to the already-DONE TCK-20260717-TICKETS-TAG-SEARCH.
- A `git diff --stat` scope check confirming `GanttBar.tsx`, `TimeAxis.tsx`, and `Legend.tsx` (and their tests) are **not** touched — guards against re-touching TCK-20260717-GANTT-TIME-AXIS's exclusive, already-DONE surface.
- If the implementer adds a source-text regex guard (matching the `TimeAxis.test.tsx` `toPercent`-import-guard pattern), keep its scope limited to `App.tsx` and `RecentActivityGantt.tsx` only — do not let it drift into asserting on files outside this ticket's Related Code Areas.
- Confirm no `Array.prototype.filter(` regression is introduced anywhere touched by this ticket if any list-narrowing logic is added incidentally — matching the blanket anti-drift convention `TicketsView.test.tsx` already enforces for `narrowTags()` (not expected to be relevant here, since this ticket adds CSS/props only, but flagged as a guard in case scope expands).
