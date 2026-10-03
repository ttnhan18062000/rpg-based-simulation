---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260717-DASHBOARD-RESPONSIVE-LAYOUT
artifact_type: investigation
tags: [observability]
---

# Investigation — TCK-20260717-DASHBOARD-RESPONSIVE-LAYOUT

## Current Behavior

### `dashboard-frontend/src/App.tsx` (L14-59)

- `App()` (L14-57) renders `<div className="h-screen flex flex-col overflow-hidden">` (L24) containing a `<header>` (L25-42) and a content region (L43-54).
- `<header className="flex items-center px-5 h-14 border-b border-border shrink-0">` (L25): fixed height `h-14` (56px), `shrink-0` (never compresses), `flex items-center` — a single-row flex container with **no `flex-wrap`**.
- `<h1 className="text-base font-semibold mr-4">Agent Ops Dashboard</h1>` (L26) and `<nav className="flex items-center gap-1">` (L27-41, three nav buttons) sit as row siblings inside that non-wrapping flex row. At narrow widths there is nothing to make the nav drop to a second line — it will overflow/crowd against the title exactly as the ticket's Request Summary describes.
- Zero Tailwind breakpoint prefixes (`sm:`/`md:`/`lg:`) anywhere in the file — confirmed by direct read, matching the ticket's own "greenfield UX work" framing.

### `dashboard-frontend/src/views/RecentActivityGantt.tsx` (L1-101)

- Current composition (post both sibling tickets): `Legend` (L70) → `TimeAxis` (L71, added by TCK-20260717-GANTT-TIME-AXIS) → `Tooltip.Provider` wrapping the scrollable bar-row list (L72-98).
- Tooltip block, L75-95: `Tooltip.Root` → `Tooltip.Trigger asChild` (the bar row div) → `Tooltip.Portal` → `Tooltip.Content`.
- `Tooltip.Content` (L91-93) currently reads:
  ```
  <Tooltip.Content className="rounded-md bg-bg-tertiary px-2 py-1 text-[11px] text-text-primary border border-border">
    {run.run_id} · {run.tier} · {run.workflow} · {durationLabel(run, nowIso)} · {run.agent_count} agents
  </Tooltip.Content>
  ```
  No `max-w-*`, no `whitespace-*`/`break-words`/`truncate` class, and **no `collisionPadding` or `avoidCollisions` prop** is passed. This is confirmed to be byte-for-byte the pre-existing block — TCK-20260717-GANTT-TIME-AXIS's own Implementation Notes state "The existing `Tooltip.Content` block was left byte-for-byte unchanged," and the on-disk read here matches that claim. The only structural change from that ticket was inserting the `<TimeAxis>` row at L71, above the `Tooltip.Provider` — it does not touch tooltip sizing/positioning.
- The tooltip text is a single unbroken interpolated string (run_id + tier + workflow + duration label + agent count), which can be long. Since Radix Popper-based positioning (which `@radix-ui/react-tooltip` uses) defaults `avoidCollisions=true` and `collisionPadding=0`, the tooltip will already attempt to flip/shift on collision, but with **no width bound**, a wide unbroken content block can still overflow the viewport at 480px when the trigger bar sits near the right edge and there isn't room on either side to fit the full width.

### `dashboard-frontend/src/index.css` (L1-47)

- No `@media` rules anywhere in the file (0 matches on `@media` across `dashboard-frontend/src/`, confirmed by grep). Only `@theme` (design tokens), `@layer base` (a project-wide margin/padding/box-sizing reset — this is the exact reset TCK-20260717-CSS-LAYER-PADDING-FIX moved inside `@layer base` so it stops overriding Tailwind's padding utilities; still in effect here and relevant if any new padding-bearing classes are added), and one decorative `.gantt-bar--inferred-pattern` class. No collision with anything this ticket needs to add.

### `dashboard-frontend/src/test/App.test.tsx` (L1-148)

- 4 existing tests, all about view-switching/navigation (`getByRole('button', {name: ...})` queries against nav buttons, `getByTestId` on each view root). None currently assert anything about the header's own layout/classes. Adding responsive classes to the header must not break these `getByRole` queries (i.e., must not restructure the button's accessible name).

### `dashboard-frontend/package.json`

- `@radix-ui/react-tooltip: ^1.2.8` is already a direct dependency (L17) — `collisionPadding`/`avoidCollisions` props on `Tooltip.Content` are available today with no new dependency required, matching the ticket Scope's phrasing ("in combination with Radix's existing collisionPadding/avoidCollisions").

## Mechanics / Engine Constraints

None apply. This is dashboard tooling (`dashboard-frontend/`), not gameplay/simulation logic — the Mechanics Bible (`docs/mechanics/`) and Engine Contracts (`docs/engine/`) govern simulation laws and do not reach the SPA's presentational layer. The one binding constraint from `docs/guides/agent_ops_dashboard.md` (L11-14) is architectural, not mechanical: the dashboard is "purely presentational... it never mutates `tickets/`, `agent-monitoring/`, or any `AuthoritativeState`." A CSS/layout-only change trivially stays inside that boundary — no state, API call, or data model is touched by this ticket's scope.

`docs/observability/agent_ops_dashboard_contract.md`'s "Architecture Law" section (static-file-mount isolation, port allocation, no-Node-at-runtime for `dashboard-serve`) governs backend/build plumbing exclusively and is unaffected by a frontend CSS change.

## Parity Ledger Overlap

None. The two parity entries covering this feature area are both explicitly backend/build-only:

- **INFRA-275** (`docs/parity_ledger/infrastructure.yaml:4478`, status `verified`, priority P2) — covers the FastAPI backend routes, ingest/cache, ticket-run join, inferred-active heuristic. Text and evidence are scoped to `src/api/agent_ops_dashboard/{main,ingest,models}.py`; no frontend files are cited.
- **INFRA-276** (`docs/parity_ledger/infrastructure.yaml:4585`) — covers `serve.py`/Makefile build-serve tooling, also backend/build-only.

Both prior frontend-only sibling tickets (TCK-20260717-TICKETS-TAG-SEARCH, TCK-20260717-GANTT-TIME-AXIS) confirmed no parity ledger entry was needed for their frontend-only presentational changes ("this was a frontend-only presentational fix" — TICKETS-TAG-SEARCH Completion Summary). This ticket is the same category of change (frontend layout/CSS only) and is expected to require **no** parity ledger update. Flagging this explicitly rather than silently assuming it, per the Authoritative Mechanics Rule's requirement not to leave a material gap unstated.

No P0 parity entries are touched by this ticket's scope.

## Prior Work

- **TCK-20260717-TICKETS-TAG-SEARCH** (DONE, `tickets/done/TCK-20260717-TICKETS-TAG-SEARCH.md`): touched `TicketsView.tsx`, `TicketsView.test.tsx`, `api.ts`, `package.json` — none of this ticket's four Related Code Areas files. Replaced the flat ~1,309-tag button dump with a search-narrowed control capped at `MAX_VISIBLE_TAGS = 40` (`narrowTags()` helper, manual loop, no `Array.prototype.filter`). The tag-button wrapper (`data-testid="filter-tags"`, inside `data-testid="tickets-filter-bar"`) uses a pre-existing (untouched by that ticket) `flex flex-wrap items-end gap-3` container, so tags already wrap onto multiple lines rather than overflowing horizontally. Net effect: the vertical space the tag control can consume at a narrow viewport dropped from "up to ~1,309 buttons, effectively unbounded" to "at most 40 buttons, wrapped." No collapse/expand-on-click toggle was added — all ≤40 matching buttons render simultaneously whenever the tag search box narrows or is empty (bounded, not collapsible). That ticket's own Test Summary ran only `vitest`/`tsc`/`vite build` plus backend contract pytest — **no real-browser or viewport-driven visual check** was performed, so whether 40 wrapped pills still meaningfully push the ticket table below the fold at 480px width has not been empirically verified either way (see Risks below).
- **TCK-20260717-GANTT-TIME-AXIS** (DONE, `tickets/done/TCK-20260717-GANTT-TIME-AXIS.md`): touched `RecentActivityGantt.tsx` (added `<TimeAxis>` import + render at L71), `GanttBar.tsx` (exported `toPercent`, added on-chart run-id label), `TimeAxis.tsx` (new), and their tests. Confirmed by that ticket's own notes and by direct read here: `Tooltip.Content` (L91-93) was left byte-for-byte unchanged by that ticket — the block this ticket must now bound is in its original, pre-existing state, not something altered by the sibling.
- **TCK-20260717-CSS-LAYER-PADDING-FIX** (DONE): moved the universal margin/padding/box-sizing reset in `index.css` inside `@layer base`. Relevant only as background — confirms `index.css`'s current reset (L18-24, read above) is already the corrected, `@layer`-scoped version; no further action needed there for this ticket unless new base-level rules are added.
- No `docs/REGISTRY.yaml`-driven search beyond the explicitly named sibling tickets was needed — the ticket itself named the relevant prior work directly (both DONE tickets touching the exact files/areas in scope here), and both were read in full above.

## Risks and Open Questions

1. **jsdom cannot verify real overflow.** Per the ticket's own Assumptions, the test runner (jsdom via vitest) does not perform real CSS layout — new tests can only assert that the correct responsive classes/props exist in markup, not that they visually prevent overlap/overflow at an actual 480px viewport. This bounds what AC #1/#2 can be proven by automated test versus what remains a manual/visual verification gap.
2. **Whether the Tickets view's narrow-viewport height issue is "fully" resolved is inferred, not proven.** The tag control went from unbounded (~1,309) to bounded (≤40), which is a large structural improvement, and no collapse-on-click exists (all ≤40 visible whenever untyped/narrowed). Whether 40 wrapped pills still meaningfully push the table below the fold at 480px was never empirically checked in a real browser by the sibling ticket. Because this ticket's own Out of Scope explicitly delegates that concern to the sibling and the sibling is DONE, **no further action on the Tickets view is required in this ticket** — but this is a delegation of scope, not a verified closure. If a future UI audit reproduces height pressure at 40 tags, that would need a new ticket, not a reopening of this one.
3. **Radix defaults vs. explicit props.** The ticket's Scope phrase "in combination with Radix's existing collisionPadding/avoidCollisions" implies these props should be used, not merely relied upon as unset defaults. `avoidCollisions` defaults to `true` and `collisionPadding` defaults to `0` on Radix Popper-based content — flipping/shifting alone does not bound content *width*, only its *position*. AC #2 ("never extends past the right viewport edge") most robustly requires **both** an explicit `collisionPadding` (e.g. a small nonzero value so the tooltip never sits flush against the viewport edge) **and** a `max-w-*`/`whitespace-normal` (or truncate) Tailwind class on `Tooltip.Content` — position-only fixes (collision avoidance) do not by themselves cap width. This is an implementation decision for `plan.md`, not resolved here.
4. **No responsive precedent exists anywhere in this codebase.** This ticket sets the first `@media`/breakpoint-prefix pattern in `dashboard-frontend/`. Neither Tailwind breakpoint prefixes (`sm:`) nor raw `@media` in `index.css` is preferred by any existing convention — an open implementation choice for the plan, not a fact to guess at here.
5. **AC #4 (docs note) has no existing section to extend.** Neither `docs/guides/agent_ops_dashboard.md` nor `docs/observability/agent_ops_dashboard_contract.md` currently has any "responsive"/"viewport" content (confirmed by full read) — this is a net-new addition, not an edit to existing prose.

## Anti-Drift Hazards

- **Do not touch `TicketsView.tsx` / `TicketsView.test.tsx`.** That is TCK-20260717-TICKETS-TAG-SEARCH's exclusive, already-closed surface; this ticket's Out of Scope explicitly excludes re-solving the Tickets view's own layout there.
- **Do not touch `GanttBar.tsx`, `TimeAxis.tsx`, or `Legend.tsx`** (or their tests) — TCK-20260717-GANTT-TIME-AXIS's exclusive surface. Only `RecentActivityGantt.tsx`'s own `Tooltip.Content` JSX (L90-94) is in scope on the Gantt side.
- **Preserve the tooltip's exact text content.** `RecentActivityGantt.test.tsx`'s "existing hover-tooltip content is unchanged after the on-chart label addition" test asserts on the literal interpolated string (`{run.run_id} · {run.tier} · ...`). Adding `max-w-*`/`whitespace-normal` classes must not alter the text nodes themselves — wrapping is safe, but if a `truncate`/`text-ellipsis` approach is chosen instead, re-verify that test still passes and reconsider whether visual truncation defeats the tooltip's purpose (showing full run detail on hover).
- **Fixed header height risk.** `<header ... h-14 shrink-0>` (App.tsx L25) has a hardcoded height. If wrapping is introduced (e.g. `flex-wrap` on the header) without also relaxing `h-14` at the narrow breakpoint, a wrapped second line will be clipped by the fixed height rather than visibly resolving the crowding — this would technically add wrap classes without satisfying AC #1's actual intent. The implementer must handle header height together with wrap behavior, not wrap-only.
- **Don't widen scope into the other `proposal_ui_review_findings.md` items** — #3 (Tier/Layer column spacing, already fixed by TCK-20260717-CSS-LAYER-PADDING-FIX), #4 (duplicate Ticket/Title columns), and #6 (unpaginated 1,109-row table) are separate, already-tracked or out-of-scope concerns, not part of this ticket.
- **Don't add a router library or change `PageView`/`NAV_ITEMS` semantics** while touching `App.tsx`'s header — scope is layout/wrapping only, not navigation-model changes.
