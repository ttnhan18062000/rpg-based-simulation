---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260716-AGENTOPS-REPLAY-TIMELINE
artifact_type: plan
tags: [observability, agent-monitoring]
---

# Implementation Plan — TCK-20260716-AGENTOPS-REPLAY-TIMELINE

## Summary

Build a frontend-only Replay timeline view (`dashboard-frontend/src/views/ReplayTimelineView.tsx`)
that fetches `GET /api/runs/{run_id}/timeline` exactly once per run selection and renders it as a
scrubbable phase-by-phase + tool-call playback, plus a static files-touched panel. The scrub
control is a new, data-agnostic `PlaybackScrubber` component built on the already-installed
`@radix-ui/react-slider`, kept deliberately ignorant of `RunTimeline`/`TimelineEntry` types so the
"scrub never fetches" constraint (AC #4) is structural, not just tested. Phase-timeline segments
reuse GanttBar.tsx's *convention* of a disjoint, mutually-exclusive status→CSS-class map, not the
component itself (its props are `RunSummary`-typed and don't apply to `TimelineEntry`). The
`live_tail` section renders the "(phase unknown — run still in progress)" caption unconditionally
per item, never from a field check, because `RawToolCall` has no `phase`/`agent` field at all. Two
open questions from investigation.md are resolved and incorporated directly: (1) Gantt-row
navigation wiring is in scope — `App.tsx` gets a plain `useState`-based `selectedRunId`, threaded
into a new `onSelectRun` prop on `RecentActivityGantt`, replacing both stubs; (2) no independent
live-refresh polling cycle is built — one fetch per run selection is sufficient for this ticket.
Every anti-drift guard from test_plan.md is planned as its own explicit step (Step 8), landing in
the same pass as the feature code, per the `DOD_BLOCKED` lesson from the sibling Gantt ticket.

## Steps

### Step 1 — Add `fetchRunTimeline` to api.ts
**Files:** `dashboard-frontend/src/api.ts`
**Change:** Add `export async function fetchRunTimeline(runId: string): Promise<RunTimeline>` that
calls `fetch(\`/api/runs/${encodeURIComponent(runId)}/timeline\`)`, throws on non-`ok` response
(mirroring `fetchRuns`'s error-message convention), and returns the parsed JSON typed as the
already-declared `RunTimeline` interface (lines 53-59, no change needed to the interface itself —
it already mirrors `models.py` field-for-field). This is a single one-shot fetch function, **not**
a polling hook — do not add a `useTimelinePolling`/`setInterval` wrapper here (see Resolution #2
in Summary; that belongs to a future ticket if ever built, not this one).
**Do NOT touch:** `fetchRuns`, `fetchAllRunsSince`, `mergeAndSortRuns`, `useRunsPolling` — leave
all existing exports unchanged. Do not add a timeline-polling hook.
**Verify:** No standalone unit test for this function; it is exercised indirectly by Step 3's
mount-fetch behavior and Step 8's "fetch fires exactly once" assertion in
`dashboard-frontend/src/test/ReplayTimelineView.test.tsx`.

### Step 2 — Build `PlaybackScrubber` (Radix slider + play/pause + speed selector)
**Files:** `dashboard-frontend/src/components/PlaybackScrubber.tsx` (new)
**Change:** A controlled, presentational component with props `{ maxIndex: number; index: number;
onIndexChange: (i: number) => void }`. Internal state: `playing: boolean` (default `false`),
`speed: 1 | 5 | 20` (default `1`). Renders `@radix-ui/react-slider`'s `Slider.Root`/`Track`/
`Range`/`Thumb` bound to `value={[index]}`, `min={0}`, `max={maxIndex}`, `step={1}`,
`onValueChange={([v]) => onIndexChange(v)}`; a play/pause toggle button; and a 1x/5x/20x speed
selector (segmented buttons) that sets `speed`. When `playing` is `true`, a `useEffect` runs a
`setInterval` (tick period `1000 / speed` ms) that calls `onIndexChange(Math.min(index + 1,
maxIndex))` each tick and auto-sets `playing` to `false` once `index === maxIndex` (nothing left to
advance to). This component imports **no** types from `api.ts` and has **no** knowledge of
`RunTimeline`/`TimelineEntry`/`RawToolCall` — it operates purely on an integer index range and a
callback, which is what makes "scrub never fetches" structural rather than merely tested.
**Do NOT touch:** Do not import `fetchRunTimeline` or any `api.ts` type here. Do not give this
component direct access to the fetched payload — all data access stays in
`ReplayTimelineView.tsx`.
**Verify:** No standalone test file (test_plan.md lists all new tests as living in
`ReplayTimelineView.test.tsx`); exercised via Step 8's "scrubbing/playback never triggers a network
fetch" and "scrub position gates the detail area's revealed tool calls progressively" tests, driven
through the parent view.

### Step 3 — `ReplayTimelineView.tsx` skeleton: fetch-once-per-`runId`, loading/error state
**Files:** `dashboard-frontend/src/views/ReplayTimelineView.tsx` (new)
**Change:** `export function ReplayTimelineView({ runId }: { runId: string })`. A `useEffect` keyed
on `[runId]` calls `fetchRunTimeline(runId)` exactly once whenever `runId` changes, storing the
result in `useState<RunTimeline | null>(null)` plus `isLoading`/`error` state, following the same
try/catch-and-`cancelled`-flag shape `useRunsPolling` uses (`api.ts:140-165`) minus the
`setInterval` re-fetch loop. Root element carries `data-testid="replay-timeline-view"`. Render
nothing (or a loading state) until `timeline` is non-null; render an error state if the fetch
rejects.
**Do NOT touch:** Do not add a `setInterval`/polling re-fetch loop for the timeline itself — a
single fetch per `runId` change is sufficient per Resolution #2. This is a deliberate divergence
from `useRunsPolling`'s pattern, not an oversight.
**Verify:** The "fetch fires exactly once on mount/run-selection" portion of the "scrubbing/
playback never triggers a network fetch" test in `ReplayTimelineView.test.tsx`.

### Step 4 — Phase-timeline segments from `entries`, seq-ascending, trusting backend order
**Files:** `dashboard-frontend/src/views/ReplayTimelineView.tsx`
**Change:** Map `timeline.entries` directly, in array order, to a horizontal row of segments — one
per entry — with **no `.sort()` call anywhere** in the file (the backend already returns them
seq-ascending, `ingest.py:536-538`). Each segment shows `entry.seq`, `entry.phase ?? '—'`,
`entry.status`. Define a small local, mutually-exclusive status→CSS-class `Record<string, string>`
map (following the *pattern* of `GanttBar.tsx`'s `STATUS_BUCKET_CLASS`/`STATUS_BUCKET_COLOR_CLASS`
— a single classification producing disjoint classes, not stacked conditionals) scoped to whatever
`TimelineEntry.status` values actually appear; do not import or extend `GanttBar.tsx` itself, since
its props are `RunSummary`-typed and its `classifyFinalStatus` bucket semantics (`DONE`/`*_BLOCKED`/
`*_FAILED`) are not guaranteed to match `TimelineEntry.status`'s value set. Clicking a segment sets
`scrubIndex` (from Step 5) to that entry's array index.
**Do NOT touch:** `dashboard-frontend/src/components/GanttBar.tsx` — do not modify it, do not
generalize `classifyFinalStatus`/`STATUS_BUCKET_CLASS` to accept both `RunSummary` and
`TimelineEntry`. Write a new, separate mapping local to this file.
**Verify:** "timeline entries render in seq-ascending order with their joined tool_calls" test, and
the "no client-side re-sort of entries" `?raw` guard (Step 8).

### Step 5 — Tool-call detail area gated by scrub position (client-side replay, no new fetch)
**Files:** `dashboard-frontend/src/views/ReplayTimelineView.tsx`
**Change:** Lift `useState<number>(0)` for `scrubIndex` (an index into `entries`, range
`0..entries.length - 1`) at the top of the component. Pass `maxIndex={entries.length - 1}`,
`index={scrubIndex}`, `onIndexChange={setScrubIndex}` to `PlaybackScrubber` (Step 2), and
`scrubIndex` down to the Step 4 phase-timeline for current-position highlighting. The detail area
renders `entries.slice(0, scrubIndex + 1)` — only entries at or before `scrubIndex` — and for each,
lists **that entry's own** `entry.tool_calls` (`tool`, `input_summary`, `status`, `duration_ms`,
`ts`), never another entry's. All of this reads only the `timeline` state already held in memory
from Step 3; `PlaybackScrubber`'s `onIndexChange` callback only ever calls `setScrubIndex` — no
code path in the scrub/play interaction calls `fetchRunTimeline` again.
**Do NOT touch:** The only `fetchRunTimeline` call site in the whole component is Step 3's
`runId`-keyed mount effect. Do not add a second call site anywhere in the scrub/play/speed-change
handlers.
**Verify:** "scrub position gates the detail area's revealed tool calls progressively" test and
"scrubbing/playback never triggers a network fetch" test.

### Step 6 — Files-touched panel: static, grouped by tool kind, rendered verbatim
**Files:** `dashboard-frontend/src/views/ReplayTimelineView.tsx`
**Change:** Render a panel from `timeline.files_touched` **unconditionally** — not read from
`scrubIndex`, not inside the Step 5 gated detail area, always showing the full list regardless of
scrub position. Group entries by `.tool` only, via a single pass (e.g. `Array.prototype.reduce` or
one `Map<string, FileTouch[]>` keyed strictly on `touch.tool`) purely for display sectioning (a
"Read" group, "Edit" group, etc.); every item within a group renders in the same relative order it
appears in `files_touched`. No item may be dropped, reordered across groups, deduped again, or have
its `path`/`ts`/`tool` recomputed.
**Do NOT touch:** Do not key any `Map`/`.filter(`/dedup construction on `.path` or
`input_summary` (that would be a second dedup pass — forbidden, see Step 8.1). Do not re-filter to
Read/Edit/Write/MultiEdit (the backend's `_EDIT_TOOLS` filter already did this). Do not read
`tool_calls` for this panel at all — source only from `RunTimeline.files_touched`. Do not gate this
panel by `scrubIndex`.
**Verify:** "files-touched panel renders RunTimeline.files_touched verbatim, without re-deriving
it" test, and the "no client-side re-derivation of files_touched dedup/filtering" `?raw` guard
(Step 8.1).

### Step 7 — `live_tail` section: unconditional "(phase unknown — run still in progress)" caption
**Files:** `dashboard-frontend/src/views/ReplayTimelineView.tsx`
**Change:** When `timeline.is_live === true` and `timeline.live_tail.length > 0`, render a
live-tail section listing each `live_tail` item's `tool`, `input_summary`, `status`, `ts`, plus a
caption rendered the same way for **every** item, unconditionally — literally
`(phase unknown — run still in progress)` — never derived from a field check (there is no
`phase`/`agent` field on `RawToolCall` to check). When `is_live === false`, render no live-tail
section at all (not an empty one — absent entirely).
**Do NOT touch:** Do not add any `tool`/`input_summary`-based heuristic to infer a phase (e.g. no
`if (tool === 'Edit') phase = ...`-style logic anywhere in the file). Do not attempt to access
`.phase` or `.agent` on a `live_tail` item (not present on the type; would not compile).
**Verify:** "live_tail entries always render an honest phase unknown caption" test (both the
`is_live=true` positive case and the `is_live=false` absence negative case), and the "no
client-side phase/agent inference for live_tail" `?raw` guard (Step 8.2).

### Step 8 — Anti-drift `?raw` source-text guards for `ReplayTimelineView.tsx`
**Files:** `dashboard-frontend/src/test/ReplayTimelineView.test.tsx` (new — same file as the
rendering tests from Steps 4-7; add these as additional `it()` blocks, following
`GanttBar.test.tsx`'s pattern: `import REPLAY_VIEW_SOURCE from '../views/ReplayTimelineView.tsx?raw'`)
**Change:** Add these source-text assertions, each a direct guard named in test_plan.md's
Anti-Drift Test Guards section:
  1. **No second files_touched dedup/filter** — assert `REPLAY_VIEW_SOURCE` contains no
     `new Map(` or `.filter(` construction keyed on `input_summary`/`path` applied to raw
     `tool_calls` data (the only permitted `.tool`-keyed grouping is Step 6's; scope the assertion
     to reject a `path`/`input_summary`-keyed second dedup pass specifically).
  2. **No client-side phase/agent inference** — assert `REPLAY_VIEW_SOURCE` never matches `\.phase\b`
     or `\.agent\b` applied to a live-tail/`RawToolCall`-shaped value, and never matches a
     `tool === '...'`-style conditional used to assign a phase label.
  3. **No client-side re-sort of `entries`** — assert `REPLAY_VIEW_SOURCE` does not match `\.sort\(`.
These three guards, plus the rendered-output tests from Steps 4/6/7 and the fetch-count test from
Step 3/5, must all land in this same file/commit as the feature code in Steps 4-7 — not deferred to
a follow-up pass (the `DOD_BLOCKED` lesson from `AGENTOPS-ACTIVITY-GANTT`).
**Do NOT touch:** Do not create a separate guard file — test_plan.md specifies all new tests
(rendering and guard) live in this one file.
**Verify:** `cd dashboard-frontend && npm test` — these assertions are themselves the verification.

### Step 9 — Wire `App.tsx`: selected-run state + real `ReplayTimelineView` render
**Files:** `dashboard-frontend/src/App.tsx`
**Change:** Add `const [selectedRunId, setSelectedRunId] = useState<string | null>(null)` alongside
the existing `currentView` state (plain `useState`, no router — matches the file's existing
convention). Replace the `currentView === 'replay'` branch's placeholder
(`<div className="p-6 text-text-secondary">Replay timeline coming soon.</div>`) with: if
`selectedRunId` is set, render `<ReplayTimelineView runId={selectedRunId} />`; otherwise render a
short "select a run from Recent Activity to view its replay" placeholder (still renders nothing
that fetches or crashes on `null`). Import `ReplayTimelineView` from `@/views/ReplayTimelineView`.
Pass `onSelectRun={(runId: string) => { setSelectedRunId(runId); setCurrentView('replay') }}` to
`<RecentActivityGantt onSelectRun={...} />` (the new prop from Step 10).
**Do NOT touch:** The `currentView === 'tickets'` branch — leave its
`"Tickets view coming soon."` stub exactly as-is. Do not introduce `react-router` or any
URL/history-based state.
**Verify:** The "App-shell scaffold smoke test" and Gantt-navigation integration tests (both
assigned to `App.test.tsx` in Step 11).

### Step 10 — Wire `RecentActivityGantt.tsx`'s `onClick` stub to real navigation
**Files:** `dashboard-frontend/src/views/RecentActivityGantt.tsx`
**Change:** Add an `onSelectRun: (runId: string) => void` prop to the `RecentActivityGantt`
function signature. Replace the stub `onClick` (currently
`() => console.debug('navigate to replay timeline (not yet built)', run.run_id)`, with its
"Stub only — AGENTOPS-REPLAY-TIMELINE builds the real navigation target" comment) with
`() => onSelectRun(run.run_id)` — using that specific row's own `run.run_id` from the `.map()`
closure, not a hardcoded or most-recently-rendered value (test_plan.md Anti-Drift Guard #8).
**Do NOT touch:** `GanttBar`, `Legend`, `Tooltip.*` usage, `useRunsPolling` call, or any other
rendering/polling logic in this file — only the `onClick` handler body and the new prop.
**Verify:** "Gantt row click navigates to that run's Replay timeline" integration test
(Step 11).

### Step 11 — Update `App.test.tsx`: replace stale assertions, add navigation + smoke tests
**Files:** `dashboard-frontend/src/test/App.test.tsx`
**Change:** Remove the two now-stale assertions (`"Replay timeline coming soon."` renders on the
Replay tab; `recent-activity-gantt` absent there) — per investigation.md Risk #5 / test_plan.md
Regression Surface, these are intentionally superseded, not a regression to preserve. Add:
  (a) **App-shell scaffold smoke test**: with no run selected, activating the Replay tab renders
      the Step 9 "select a run" placeholder (not a crash, not a fetch); activating the Tickets tab
      still renders its unchanged `"Tickets view coming soon."` stub, and `recent-activity-gantt`
      is absent in that state (test_plan.md Anti-Drift Guard #6 / out-of-scope-view guard).
  (b) **Gantt-navigation integration test**: mock `useRunsPolling` to return one fixture
      `RunSummary` (e.g. `run_id: 'run-nav-target'`), render `<App />`, click that row in the
      rendered `RecentActivityGantt`, and assert the view switches to Replay and
      `screen.getByTestId('replay-timeline-view')` is present, scoped to `run-nav-target`
      specifically (assert the rendered `run_id` string appears, not just that *a* replay view
      renders) — guards against a fixture-with-one-row false pass (test_plan.md Anti-Drift Guard
      #8). Mock `fetchRunTimeline` (from `../api`) so this test doesn't depend on network behavior.
Keep the existing Tickets-stub assertions unchanged.
**Do NOT touch:** Do not delete the Tickets-stub assertions — they are the out-of-scope-view guard
and must survive this ticket.
**Verify:** `cd dashboard-frontend && npm test` — `App.test.tsx` green with old stale assertions
removed and new ones passing.

### Step 12 — Backend-untouched + full scoped-test confirmation (Verify-phase gate)
**Files:** None changed — procedural verification only.
**Change:** Run the full scoped backend command and the frontend suite, and confirm via
`git diff --stat -- src/api/agent_ops_dashboard/` that it is empty (proves this "frontend-only"
ticket did not modify backend join/dedup logic — test_plan.md Anti-Drift Guard #7).
**Do NOT touch:** Nothing — this step changes no files.
**Verify:**
```
pytest tests/tools/test_agent_ops_dashboard_ingest.py tests/tools/test_agent_ops_dashboard_api.py tests/tools/test_agent_ops_dashboard_concurrency.py tests/tools/test_agent_ops_dashboard_api_boundary.py tests/tools/test_agent_ops_dashboard_frontend_api_surface.py tests/architecture/test_api_read_model_guard.py -m "not slow"
```
and
```
cd dashboard-frontend && npm test
```
both green, plus an empty `git diff --stat -- src/api/agent_ops_dashboard/`.

## Scope Guards

- No changes to `src/api/agent_ops_dashboard/main.py`, `ingest.py` (its `seq`-ordered join or
  `extract_files_touched` dedup/filter logic), or `models.py` — backend-owned, done, tested. Consume
  `RunTimeline`/`TimelineEntry`/`RawToolCall`/`FileTouch` fields verbatim.
- No attempt to fix the `live_tail` `phase`/`agent` null-labeling gap — independent sibling idea
  (`idea_agent_monitoring_live_phase_label.md`), explicitly out of scope. The unconditional caption
  (Step 7) is the only correct behavior against today's schema.
- No re-implementation of `files_touched` dedup or Read/Edit/Write/MultiEdit filtering client-side
  (Step 6) — render verbatim, group by `.tool` only.
- No building the Tickets table view (`AGENTOPS-TICKETS-VIEW`) — its stub in `App.tsx` must remain
  untouched (Step 9's Do-NOT-touch, Step 11's guard test).
- No modification to `RecentActivityGantt.tsx`'s own rendering (`GanttBar`, `Legend`,
  `Tooltip.*`, `useRunsPolling`) beyond the `onClick`/prop wiring in Step 10.
- No modification to `GanttBar.tsx` itself, or generalizing its `classifyFinalStatus`/
  `STATUS_BUCKET_CLASS` for reuse — Step 4 writes new, separate local logic.
- No Makefile targets, `vite build` production wiring, or FastAPI `StaticFiles` mounting —
  `AGENTOPS-BUILD-SERVE`'s scope, untouched here.
- No `react-router` or any other routing library — Step 9's `selectedRunId` is a plain `useState`,
  matching the existing `currentView` convention.
- No independent live-refresh polling cycle for a still-live run's growing `live_tail` — Resolution
  #2: a single fetch per run selection (Step 3) is sufficient for this ticket; do not add a
  `setInterval` re-fetch loop for the timeline.
- No new pytest target or Python source file — this ticket adds no backend code.
- No duplicate frontend-API-surface guard file — `tests/tools/
  test_agent_ops_dashboard_frontend_api_surface.py`'s existing recursive glob already covers every
  new file under `dashboard-frontend/src/`.

## Dependency Map

- Step 1 (api.ts fetch fn) → required by Step 3.
- Step 2 (PlaybackScrubber) → required by Step 5; independent of Steps 1/3/4 and can be built in
  parallel with them.
- Step 3 (view skeleton + fetch-once) → required by Steps 4, 5, 6, 7 (all read `timeline` state).
- Step 4 (phase-timeline segments) → feeds Step 5's current-position highlighting, but Step 5's
  detail-gating logic itself only depends on Step 3's `entries` array, not Step 4's rendering.
- Steps 4, 6, 7 are otherwise independent of each other (different sections of the same file) and
  can be implemented in any order once Step 3 exists.
- Step 8 (guards) depends on Steps 4-7's code existing in `ReplayTimelineView.tsx` to assert
  against — implement last among the feature steps, same commit.
- Step 9 (App.tsx wiring) depends on Step 3 (component to import) and defines the `onSelectRun`
  callback signature Step 10 must match.
- Step 10 (Gantt onClick wiring) depends on Step 9's callback signature; the two should land
  together.
- Step 11 (App.test.tsx update) depends on Steps 9 and 10 both being in place.
- Step 12 (verification) depends on all prior steps.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC #1 — entries render seq-ascending, each with joined tool_calls | Steps 3, 4, 5 | "timeline entries render in seq-ascending order with their joined tool_calls" (`ReplayTimelineView.test.tsx`) |
| AC #2 — files-touched panel deduped-by-path, Read/Edit/Write/MultiEdit only, first-seen ts+tool | Step 6 | "files-touched panel renders RunTimeline.files_touched verbatim, without re-deriving it" + Step 8.1 guard |
| AC #3 — live_tail items show phase=null/agent=null with honest caption, never guessed | Step 7 | "live_tail entries always render an honest phase unknown caption" + Step 8.2 guard |
| AC #4 — scrubbing replays fetched payload client-side, triggers no new fetch | Steps 2, 3, 5 | "scrubbing/playback never triggers a network fetch" + "scrub position gates the detail area's revealed tool calls progressively" |
| (Real scope, not a formal AC bullet) Gantt-row click navigates to this run's Replay view | Steps 9, 10, 11 | "Gantt row click navigates to that run's Replay timeline" (`App.test.tsx`) |

## Anti-Drift Notes

- `RawToolCall` has **no** `phase`/`agent` field at all — not `Optional`, simply absent from the
  type (`api.ts:24-30`, mirrors `models.py:39-44`). Step 7's caption must be rendered
  unconditionally per `live_tail` item; there is no field to null-check, and attempting `.phase`/
  `.agent` on a `live_tail` item would not compile.
- The backend already returns `entries` seq-ascending (`ingest.py:536-538`) and `files_touched`
  deduped-by-path-first-seen restricted to `_EDIT_TOOLS` (`ingest.py:264-284`, `49`). Trust both
  verbatim — Steps 4 and 6 must not re-sort or re-dedup.
- `App.test.tsx`'s two current assertions about `"Replay timeline coming soon."` are **expected to
  be falsified** by this ticket (Step 11) — this is in-scope test churn, not a regression to guard
  against re-introducing.
- Carry forward the `DOD_BLOCKED` lesson from `AGENTOPS-ACTIVITY-GANTT`: Step 8's guards (and
  Step 11's updated assertions) must land in the **same implementation pass** as Steps 4-7 and
  Steps 9-10's feature code — not a follow-up fix pass after a Verify-phase gate failure.
- `tests/tools/test_agent_ops_dashboard_frontend_api_surface.py` already covers
  `ReplayTimelineView.tsx`, `PlaybackScrubber.tsx`, and any new `api.ts` additions via its
  recursive glob — run it in Step 12 to confirm, but do not write a ticket-specific duplicate.
- Resolution #2 (no independent live-refresh polling cycle) means `ReplayTimelineView.tsx`
  deliberately does **not** mirror `useRunsPolling`'s `setInterval` pattern — this is an
  intentional divergence from that sibling hook, not an inconsistency to "fix" toward parity.

Both open questions flagged in investigation.md (Gantt-row navigation scope, live-refresh
polling scope) have been resolved and incorporated directly into Steps 9-11 and the Scope Guards
above — no `## Unresolved Questions` heading is included, per this batch's established convention
(the Plan-phase gate matches on literal heading presence, not content, so an empty/"None" section
would false-trigger `NEEDS_HUMAN_INPUT`).

## Deviations

Recorded during implementation (see also the ticket's Implementation Notes):

1. **`ResizeObserver` stub added to `dashboard-frontend/src/test/setup.ts`.** Not anticipated by
   this plan. jsdom has no `ResizeObserver`, and `@radix-ui/react-slider`'s internal `useSize` hook
   calls one unconditionally — every test rendering `PlaybackScrubber` (i.e. all of
   `ReplayTimelineView.test.tsx`) threw `ReferenceError: ResizeObserver is not defined` until a
   trivial no-op stub was added to the shared test setup file. This is test-infrastructure plumbing,
   not a behavior change to any Step 1-11 component.
2. **`PlaybackScrubber` (Step 2) gained a `maxIndex > 0` guard around `Slider.Root`.** Not in the
   original Step 2 spec. Radix's slider computes position as a percentage of `(max - min)`; a
   0-or-1-entry `RunTimeline` yields `maxIndex === 0`, so `min === max === 0`, producing
   `calc(NaN% + 0px)` — a value jsdom's style setter throws a `SyntaxError` on, which unmounts the
   whole React tree with no error boundary in place. Surfaced by the Step 11 navigation test's
   `run-nav-target` fixture (empty `entries`). Fix: render an inert placeholder track instead of
   `Slider.Root` when `maxIndex <= 0` — there is nothing to scrub across in that case regardless.
3. **`dashboard-frontend/src/test/RecentActivityGantt.test.tsx` was updated**, though plan.md's
   Step 11 named only `App.test.tsx` for test updates. This was a mechanical consequence of Step 10
   making `onSelectRun` a required prop on `RecentActivityGantt` — every pre-existing
   `render(<RecentActivityGantt />)` call site needed a mock prop to keep compiling. One new test
   was also added there (asserting the click handler passes the clicked row's own `run_id`, not a
   hardcoded one), which test_plan.md's Regression Surface section had already flagged as
   conditionally in-scope for this file.
