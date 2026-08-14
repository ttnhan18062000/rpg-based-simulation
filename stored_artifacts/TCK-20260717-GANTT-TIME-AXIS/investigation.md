---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260717-GANTT-TIME-AXIS
artifact_type: investigation
tags: [observability, agent-monitoring]
---

# Investigation — TCK-20260717-GANTT-TIME-AXIS

## RESTART NOTICE

This is a re-investigation after a session interruption mid-Implement. A prior `investigation.md`/`plan.md`/`test_plan.md` already existed in this staging directory from the interrupted attempt (this file overwrites the prior `investigation.md`; `plan.md` was left as-is for the planner to re-verify). The prior plan.md turned out to be accurate and well-executed for Steps 1-3; this document re-verifies every claim against the actual current working-tree state rather than trusting the stale artifacts, and adds a new finding the prior investigation could not have had (a second, unrelated ticket's uncommitted changes sitting in the same working tree — see "Prior Work" and "Risks").

## Current Behavior (re-verified against actual working-tree files, not git HEAD)

**`dashboard-frontend/src/views/RecentActivityGantt.tsx`** (current working-tree state, confirmed by direct read):
- L1-6: imports now include `import { TimeAxis } from '@/components/TimeAxis'` (added — not in git HEAD).
- L69-71: renders `<Legend />`, then `<TimeAxis windowStartIso={sinceIso} windowEndIso={nowIso} />`, then the `Tooltip.Provider`/scrollable row-list block — exactly the "fixed row above the scrollable list" placement the prior plan.md's Step 3 specified.
- The tooltip block (L90-94) is byte-for-byte unchanged from git HEAD: `run_id · tier · workflow · durationLabel(...) · agent_count agents`.
- **Gap vs. plan.md**: nothing else in this file changed. This file's portion of the work (Step 3) is complete and correct.

**`dashboard-frontend/src/components/GanttBar.tsx`** (current working-tree state):
- Git diff shows exactly **one line changed**: `function toPercent(...)` → `export function toPercent(...)` (L45). This is plan.md's Step 1, done correctly, nothing else touched.
- **Step 4 of the interrupted plan (add an on-chart truncated run-id `<span>` to both render branches) is NOT present.** Neither branch (inferred L56-74, authoritative L76-101) contains any `truncateRunId` helper, any `gantt-bar-run-label` testid, or any run-id text node. The inferred branch still only has the pre-existing `<span className="gantt-bar__estimate-label">~est.</span>`; the authoritative branch is still a self-closing `<div ... />` with no children.
- This is the concrete, verifiable gap: `dashboard-frontend/src/test/RecentActivityGantt.test.tsx` (see below) already contains 3 tests that assert `screen.getByTestId('gantt-bar-run-label')` exists — all 3 currently **fail** (confirmed by running `npx vitest run` directly in this investigation, not assumed).

**`dashboard-frontend/src/components/TimeAxis.tsx`** (new file, untracked, fully written):
- Exports `TimeAxis({ windowStartIso, windowEndIso })`. Imports `toPercent` from `@/components/GanttBar` (L1) — does not redeclare it, matching plan.md's Step 2 anti-drift requirement.
- Computes 7 evenly-spaced ticks (`TICK_COUNT = 7`, L3) via `tickMs = startMs + ((endMs - startMs) * index) / (TICK_COUNT - 1)` (L25) — window-duration-fraction, not fixed wall-clock interval, matching plan.md's stated rationale for tolerating `sinceIso`-frozen/`nowIso`-advancing window drift.
- Every tick's `left` position is `toPercent(tickIso, windowStartIso, windowEndIso)` (L28) — routes through the same function `GanttBar` uses, satisfying AC #3.
- Labels via `toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })` (L29).
- Root: `data-testid="gantt-time-axis"`; each tick: `data-testid="gantt-time-axis-tick"`.
- This file is complete, coherent, and matches its own test file exactly (see below). No gaps found here.

**`dashboard-frontend/src/test/TimeAxis.test.tsx`** (new file, untracked, fully written, 3 tests, all passing):
1. Anti-drift source-text guard: asserts the component source imports `toPercent` from `@/components/GanttBar` and does not contain `function toPercent` (no local redeclaration).
2. Numeric match: a known mid-window timestamp's rendered tick `left` style equals `toPercent(...)` computed directly in the test.
3. Renders immediately with no hover/interaction.
All 3 pass in isolation and as part of the full suite.

**`dashboard-frontend/src/test/RecentActivityGantt.test.tsx`** (modified, working tree ahead of git HEAD by +78 lines / 4 new tests, confirmed by direct read and diff):
- 4 new tests appended past the original 6 (which are byte-identical to HEAD and still pass):
  1. "renders a visible time axis independent of any hover state" — **passes**.
  2. "time axis end label updates as nowIso advances" (fake timers) — **passes**.
  3. "each rendered bar carries an on-chart run-id label distinct from the tooltip" — **fails** (queries `gantt-bar-run-label`, not rendered).
  4. "narrow/clamped bar label is not dropped when the bar hits its minimum width" — **fails** (same reason).
  5. "existing hover-tooltip content is unchanged after the on-chart label addition" — **fails** (asserts tooltip node `!== gantt-bar-run-label` node; `getByTestId` throws because the element doesn't exist at all).
- Confirmed via direct `npx vitest run` in `dashboard-frontend/`: **3 failed / 42 passed across the full 7-file suite (45 tests total)**. All 3 failures are in this file, all for the identical root cause (missing on-chart run-id label in `GanttBar.tsx`).

**`dashboard-frontend/src/components/Legend.tsx`**: byte-identical to git HEAD. Not touched by the interrupted attempt, consistent with plan.md's "Do NOT touch Legend.tsx" scope guard.

**`dashboard-frontend/src/test/GanttBar.test.tsx`**: byte-identical to git HEAD (no diff). The plan never scheduled a new test here — the raw-source anti-drift guards (`no Date.now()`/`new Date()`, direct `is_inferred_active` branching) still pass unmodified, confirmed by the full-suite run.

## Mechanics / Engine Constraints

None. This remains presentation-layer tooling over agent-monitoring telemetry, not simulation gameplay — no `docs/mechanics/` chapter applies and no `AuthoritativeState` is touched. Confirmed again this pass; same conclusion as the parent ticket's investigation (`stored_artifacts/TCK-20260716-AGENTOPS-ACTIVITY-GANTT/investigation.md`).

`experiments/agent_ops_dashboard/UI_INTERACTION_SPEC.md` L60 (re-read directly this pass, exact quote): "...than compressing the time axis — horizontal position must stay a true time axis, never rescaled per..." — this is the one governing constraint: bar/axis horizontal position must be a true linear time mapping. Both `GanttBar.toPercent` and the new `TimeAxis` satisfy this (same function, same linear clamp-and-scale math). §2 of that spec never specifies a rendered axis at all — confirmed again by direct grep this pass (no other `axis`/`toPercent` hits in the file) — so this ticket is closing a genuine spec gap, not fixing a regression.

`docs/observability/agent_ops_dashboard_contract.md` L91-113 (re-read this pass): describes `RecentActivityGantt.tsx` composing `useRunsPolling` with `GanttBar`/`Legend`, and `GanttBar`'s `classifyFinalStatus` bucket mapping — written before this ticket, does not mention an axis or on-chart label, consistent with this being new UI surface, not a documented-then-broken contract. **This doc will need a follow-up update once the ticket lands** (see Risks below) since it currently under-describes the view's actual composition (`Legend` + `TimeAxis` + row list) — not blocking, but should be noted for the "Related Docs" close-out.

`docs/guides/agent_ops_dashboard.md` L48-63 (re-read this pass): "Recent Activity Gantt" section describes hover-tooltip content and click-through navigation; no axis/label content currently documented. Same follow-up-doc-update note applies.

## Parity Ledger Overlap

Re-checked `docs/parity_ledger/infrastructure.yaml` directly this pass (not just trusting the stale investigation.md's claim):
- **INFRA-275** (`status: verified`, `priority: P2`, L4478-4528) — backend routes/ingest/models. Confirmed not touched by any file in this ticket's diff (frontend-only). No update required.
- **INFRA-276** (`status: verified`, `priority: P2`, L4529+) — serve.py/Makefile production-serving wiring. Confirmed not touched. No update required.
- No P0 entries in this area — no `test_path` gate is inherited.
- No dedicated Gantt-frontend parity entry exists in the ledger, and none is warranted — same conclusion as the parent ticket and the prior interrupted attempt's investigation: presentation-only UI over an already-parity-tracked read-only API is outside `docs/parity_ledger/schema.json`'s subsystem scope.

## Prior Work

- **`stored_artifacts/TCK-20260716-AGENTOPS-ACTIVITY-GANTT/`** — built `RecentActivityGantt`/`GanttBar`/`Legend` from scratch. Established the `toPercent` clamping convention, the inferred/authoritative zero-shared-class-token guarantee (tested via `classesOf` set-intersection in `RecentActivityGantt.test.tsx`), and the settle-transition mechanism (`justSettledIds`). Also documents a prior `DOD_BLOCKED` at Verify because that ticket's test_plan.md anti-drift guards were written but not actually implemented — directly relevant precedent for this restart: this ticket's own test_plan.md guards must be checked off against real code, not just described (see Anti-Drift Test Guards in test_plan.md).
- **`docs/plans/agent_ops_dashboard/proposal_ui_review_findings.md`**, finding #1 — the direct source of this ticket's Request Summary. Confirmed the same day (2026-07-17).
- **This ticket's own interrupted attempt** (staging_artifacts, prior `plan.md` — left in place, still readable): a 5-step plan (1. export `toPercent`; 2. build `TimeAxis`; 3. wire it in; 4. add truncated run-id label to `GanttBar`'s two branches; 5. full regression pass). **Steps 1-3 are fully and correctly implemented** in the current working tree, matching the plan's stated design exactly (verified line-by-line above, not assumed from the plan text). **Step 4 is entirely unimplemented** — no `truncateRunId` helper, no label span, in either `GanttBar` branch. **Step 5 was never reached.** The partial work is coherent, not half-broken: everything that exists is complete, tested, and passing; nothing is left in a broken intermediate state. Recommendation for the planner: **finish, do not redo** — re-run Step 4 and Step 5 as originally scoped; Steps 1-3 need no rework.
- **A second, unrelated ticket's finished-but-uncommitted changes are sitting in the same working tree.** `tickets/done/TCK-20260717-CSS-LAYER-PADDING-FIX.md` (hotfix tier, `phase: done`, working_log.csv entry present, `agent-monitoring/runs.jsonl` shows a completed `DONE` run 11:28:36-13:55:43Z) fixed an unlayered-CSS-reset bug in `dashboard-frontend/src/index.css` (wrapped the global `* { margin:0; padding:0; box-sizing:border-box }` reset in `@layer base`) plus a supporting `tsconfig.test.json` split and a new regression-test describe-block in `TicketsView.test.tsx`. Its own "Files Changed" section (index.css, TicketsView.test.tsx, tsconfig.app.json, tsconfig.json, tsconfig.test.json — new file) is an **exact match** for 5 of the 10 modified/untracked files `git status` reports right now. That ticket completed its full Finalize sequence (ticket moved to `tickets/done/`, `working_log.csv` appended, `agent-monitoring` run recorded DONE, removed from its `tickets/todos/agent-ops-dashboard-ui-fixes/` source subfolder) **except the final `git commit`** — those 5 files' changes were never committed before the interruption. `tickets/todos/agent-ops-dashboard-ui-fixes/SEQUENCE.md` confirms `TCK-20260717-CSS-LAYER-PADDING-FIX` is step 1 of that batch, immediately before `TCK-20260717-GANTT-TIME-AXIS` (step 2) — consistent with an `implement-epic` run that finished ticket 1, never committed it, moved straight to ticket 2, and was interrupted mid-ticket-2's Implement. **This is not scope creep from this ticket's own session — it is a separate, already-approved, fully-documented piece of work that merely needs its own commit.** Flagged explicitly in Risks below since it affects commit hygiene for the restart.

## Risks and Open Questions

1. **Commit hygiene / traceability decision needed (blocks nothing about implementation, but must be decided before Finalize).** The working tree currently mixes two tickets' uncommitted changes: `TCK-20260717-CSS-LAYER-PADDING-FIX` (index.css, TicketsView.test.tsx, tsconfig.app.json, tsconfig.json, tsconfig.test.json — done, needs only a commit) and `TCK-20260717-GANTT-TIME-AXIS` (GanttBar.tsx, RecentActivityGantt.tsx, RecentActivityGantt.test.tsx, TimeAxis.tsx, TimeAxis.test.tsx — this ticket's own work). CLAUDE.md's Commit Convention requires every commit to reference the correct ticket ID; a single combined commit would misattribute the CSS fix's changes to this ticket. **Recommend**: commit the CSS-LAYER-PADDING-FIX file set separately first (message referencing `TCK-20260717-CSS-LAYER-PADDING-FIX`, since that ticket is already fully documented and DONE — this would just be catching up a missed commit step), then implement/commit this ticket's remaining work (Step 4 + Step 5) separately. This is a process decision for whoever runs Finalize, not a code-correctness question — flagging so the planner states it explicitly rather than silently bundling both tickets' diffs into one `TCK-20260717-GANTT-TIME-AXIS:` commit.
2. **`toPercent` export and `TimeAxis` wiring (Steps 1-3) are done — no rework needed.** Re-verified directly against source, not assumed. Low risk this pass is only Step 4 + Step 5.
3. **Doc follow-up**: `docs/observability/agent_ops_dashboard_contract.md` and `docs/guides/agent_ops_dashboard.md` both currently under-describe `RecentActivityGantt`'s composition (no axis/label mention). Per CLAUDE.md's Authoritative Mechanics Rule this isn't a Mechanics Bible parity requirement (this view isn't gameplay), but the "Update related docs" Definition-of-Done item still applies generally — the plan should include a doc-touch step for these two files' Gantt sections once Step 4 lands, or explicitly note why it's deferred.
4. **On-chart label content/format**: not re-litigated here — the now-existing tests in `RecentActivityGantt.test.tsx` (already written, in the working tree) pin the exact contract: `data-testid="gantt-bar-run-label"`, `textContent` equal to the *untruncated* `run_id` for the `'run-completed'` fixture (the test asserts `.textContent).toBe('run-completed')`, not a truncated/ellipsized variant). **This is a concrete divergence from the prior plan.md's Step 4 design**, which specified truncation at 12 chars + ellipsis by default — `'run-completed'` is exactly 13 characters, so a 12-char+ellipsis truncation would render `'run-complete…'`, not `'run-completed'`, and the existing test would fail. The planner must either (a) pick a longer truncation threshold that leaves 13-char fixture IDs untouched, or (b) treat truncation as applying only past some longer boundary not exercised by current fixtures, or (c) note that the *existing test as already written* is the actual contract to satisfy and adjust the truncation design to match it rather than the stale plan text. This is a concrete, decidable implementation detail, not a blocking open question — but it must be resolved consistently with the tests that already exist in the working tree, not with the superseded plan.md prose.
5. **Narrow-bar test's expectation**: the existing "narrow/clamped bar label is not dropped" test only asserts `getByTestId('gantt-bar-run-label').textContent).toBeTruthy()` — a weak assertion (any non-empty string passes), so no further design constraint is imposed here beyond "the label element still exists and has content" even at 0.5% width.

No open question here blocks starting implementation — item 1 is a process/commit-ordering decision, item 4 is a concrete test-driven correction to the stale plan's truncation design that the planner should fold into an updated plan.md.

## Anti-Drift Hazards

- **Do not touch `TimeAxis.tsx`, `TimeAxis.test.tsx`, the `toPercent` export in `GanttBar.tsx`, or the `TimeAxis` import/wiring in `RecentActivityGantt.tsx`.** These are complete, correct, and fully tested (10 passing tests across `TimeAxis.test.tsx` and the axis-related additions to `RecentActivityGantt.test.tsx`). Re-implementing or "cleaning up" any of this risks silently breaking working code for zero benefit.
- **Do not reimplement `toPercent`'s clamping/percentage math a second time** anywhere the label logic is added — reuse the already-exported function exactly as `TimeAxis.tsx` does. (Carried forward from the original investigation; still applies to Step 4's label positioning if any is needed — though note the label is a child of the already-positioned bar `<div>`, so it likely needs no independent `toPercent` call at all.)
- **Do not remove, rename, or restructure the existing hover `Tooltip.Content` block** (`RecentActivityGantt.tsx` L~91-93) — untouched so far, must stay untouched; AC #4 and the existing "existing hover-tooltip content is unchanged" test both depend on it.
- **Do not add the label's class name to the outer bar `<div>`'s `classNames` array** in either `GanttBar` branch — the inferred/authoritative zero-shared-class-token guarantee (`RecentActivityGantt.test.tsx`'s "never shares styling..." test, still passing) only inspects the outer element's own className; a shared child-span class is safe, a shared class on the outer div is not.
- **Do not introduce `Date.now()`/`new Date()` calls inside `GanttBar.tsx`** — `GanttBar.test.tsx`'s raw-source regex guards scan the whole file, not just the pre-existing branches; a `truncateRunId`-style helper operating only on the `run.run_id` string prop needs no `Date` call and must not add one.
- **Do not bundle `TCK-20260717-CSS-LAYER-PADDING-FIX`'s uncommitted files into this ticket's `Files Changed` section or commit message** — they are a separate, already-DONE ticket's work that merely needs its own catch-up commit (see Risks #1). Conflating them breaks per-ticket traceability.
- **Do not "fix" the truncation design to match the stale plan.md's 12-char+ellipsis default** if doing so would break the already-written, already-in-the-working-tree test asserting `textContent === 'run-completed'` (13 chars, untruncated) — the existing test is the live contract now, not the superseded plan prose (Risks #4).
