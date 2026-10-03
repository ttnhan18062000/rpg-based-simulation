---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260716-AGENTOPS-REPLAY-TIMELINE
artifact_type: test_plan
tags: [observability, agent-monitoring]
---

# Test Plan — TCK-20260716-AGENTOPS-REPLAY-TIMELINE

## Regression Surface

This ticket is frontend-only (TypeScript/React, extending the existing `dashboard-frontend/`
scaffold). No Python source under `src/api/agent_ops_dashboard/` should be modified — the backend
regression suite is a **sanity check that nothing was inadvertently touched**, not a suite this
ticket's changes should affect:

- unit/integration (backend, must stay green, unmodified):
  - `tests/tools/test_agent_ops_dashboard_ingest.py` — including
    `test_files_touched_dedup_by_path_restricted_to_edit_tools` (`ingest.py`'s dedup/filter logic
    this view must trust, not reimplement).
  - `tests/tools/test_agent_ops_dashboard_api.py` — including the `/timeline` 404 case (line 40).
  - `tests/tools/test_agent_ops_dashboard_concurrency.py`.
  - `tests/tools/test_agent_ops_dashboard_api_boundary.py` — including the `/timeline` typed-
    response-model boundary check (line 56).
- architecture guard, must stay green:
  - `tests/architecture/test_api_read_model_guard.py` — no new coupling from
    `src/api/agent_ops_dashboard/` into `src/api/read_model_cache.py`/`src/api/server.py`.
  - `tests/tools/test_agent_ops_dashboard_frontend_api_surface.py` — **directory-wide** glob over
    `dashboard-frontend/src/**/*.{ts,tsx}` (confirmed via `_frontend_source_files()`), so it
    automatically covers the new `views/ReplayTimelineView.tsx` and any new `api.ts`
    additions/hooks without a ticket-specific duplicate. Must stay green with zero references to
    `src/api/server.py`, `src/api/read_model_cache.py`, `src/api/routes/history.py`, or
    `src/api/ws/stream.py`.
- frontend, **must be updated, not merely kept passing as-is**:
  - `dashboard-frontend/src/test/App.test.tsx` — its two current assertions
    (`"Replay timeline coming soon."` renders when the Replay tab is active;
    `recent-activity-gantt` is absent in that state) are **expected to be falsified** by a correct
    implementation of this ticket (see investigation.md Risk #5). This file must be edited as part
    of this ticket's own changes — treat the old assertions as intentionally superseded, not as a
    regression to preserve. The updated file should assert the real `ReplayTimelineView` (or
    equivalent testid) renders instead, and that `Tickets` still renders its unchanged placeholder
    stub (see Anti-Drift Test Guards below).
  - `dashboard-frontend/src/test/RecentActivityGantt.test.tsx` — if Gantt-row navigation wiring is
    confirmed in scope (investigation.md Risk #2), this file needs a new/updated test replacing
    the implicit "click does nothing but `console.debug`" behavior with an assertion on whatever
    navigation callback/state change now fires. If a plan-time decision instead defers navigation
    wiring, this file requires no change and that deferral must be recorded in Implementation
    Notes.
  - `dashboard-frontend/src/test/GanttBar.test.tsx`, `useRunsPolling.test.ts` — unrelated to this
    ticket's surface, must stay green unmodified (sanity check only).

## New Tests Required

Per this ticket's Acceptance Criteria
(`tickets/inprogress/TCK-20260716-AGENTOPS-REPLAY-TIMELINE.md`), plus the navigation-wiring and
live-tail-schema findings in investigation.md. All new tests are Vitest + Testing Library,
colocated under `dashboard-frontend/src/test/` — run locally, not CI-gated (frontend has zero CI
coverage repo-wide, unchanged by this ticket, same as `AGENTOPS-ACTIVITY-GANTT`).

- **`timeline entries render in seq-ascending order with their joined tool_calls`**
  Category: unit (component)
  Verifies: AC #1 — given a `RunTimeline` fixture with `entries` in `seq` order (and, separately,
  a fixture constructed with entries deliberately out of insertion order but correct `seq` values,
  to prove the component orders by `seq` rather than array position), the rendered phase-timeline
  segments appear left-to-right by ascending `seq`, and each segment's detail area (or expandable
  detail) reflects that entry's own `tool_calls`, not another entry's.
  Location: `dashboard-frontend/src/test/ReplayTimelineView.test.tsx`

- **`files-touched panel renders RunTimeline.files_touched verbatim, without re-deriving it`**
  Category: unit (component)
  Verifies: AC #2 — given a `files_touched` fixture that is deliberately *not* already sorted or
  deduped the way a naive client-side re-implementation might produce it (e.g. two entries with
  the same `path` — which should never occur since the backend already dedupes, but the test
  proves the component doesn't additionally filter/dedup/re-sort), the rendered panel shows
  exactly the fixture's list, in fixture order, with no entry dropped, reordered, or merged.
  Location: `dashboard-frontend/src/test/ReplayTimelineView.test.tsx`

- **`live_tail entries always render an honest "phase unknown" caption, never a guessed phase/agent`**
  Category: unit (component) — direct guard against investigation.md Risk #1 and AC #3
  Verifies: AC #3 — given `is_live=true` and a non-empty `live_tail` fixture, every rendered
  live-tail item shows the literal `(phase unknown — run still in progress)` caption (or
  equivalent testid) and never renders a phase/agent label of any kind for that item (there is no
  `phase`/`agent` field on `RawToolCall` to source one from — see investigation.md Risk #1). Also
  assert this caption is **absent** when `is_live=false` (no live_tail section rendered at all for
  a completed run) — the negative case.
  Location: `dashboard-frontend/src/test/ReplayTimelineView.test.tsx`

- **`scrubbing/playback never triggers a network fetch`**
  Category: unit (component), mocked fetch call-count assertion — the single highest-value test
  in this ticket, direct guard against AC #4 and investigation.md's scrub-must-not-fetch
  constraint
  Verifies: AC #4 — render the view with a mocked `global.fetch` for the initial
  `GET /api/runs/{run_id}/timeline` call (asserting it fires exactly once on mount/run-selection),
  then drive the scrubber through several positions (drag, or whatever control primitive is used)
  and toggle play/pause and speed selection, and assert `fetch` call count is **still exactly 1**
  after all of that interaction.
  Location: `dashboard-frontend/src/test/ReplayTimelineView.test.tsx`

- **`scrub position gates the detail area's revealed tool calls progressively`**
  Category: unit (component) — not a standalone AC bullet, but the mechanic that makes this a
  "replay" rather than a static list (`UI_INTERACTION_SPEC.md` §3b/3c); without this test the
  scrub control could satisfy AC #4's letter (no fetch) while rendering all tool calls at once
  regardless of scrub position, silently dropping the feature's actual purpose.
  Verifies: with the scrubber positioned at an early point in the timeline, only tool calls at or
  before that position are shown in the detail area; advancing the scrubber reveals more, never
  fewer, and never all of them at once from the start.
  Location: `dashboard-frontend/src/test/ReplayTimelineView.test.tsx`

- **`Gantt row click navigates to that run's Replay timeline`** (conditional on investigation.md
  Risk #2's scope decision — include only if the plan confirms navigation wiring is in scope for
  this ticket)
  Category: integration (component)
  Verifies: clicking a `RecentActivityGantt` row for `run_id=X` switches `App`'s active view to
  Replay and renders `ReplayTimelineView` scoped to `run_id=X` (not a different/most-recent run) —
  replaces the old stub-only `console.debug` behavior.
  Location: `dashboard-frontend/src/test/App.test.tsx` or
  `dashboard-frontend/src/test/RecentActivityGantt.test.tsx` (whichever owns the navigation
  callback per the plan's chosen state shape)

- **`App-shell scaffold smoke test: Replay tab renders the real ReplayTimelineView, Tickets remains a stub`**
  Category: integration / architecture guard
  Verifies: replaces `App.test.tsx`'s now-stale "Replay timeline coming soon." assertions (see
  Regression Surface) with: activating the Replay tab renders real `ReplayTimelineView` content
  (not the placeholder string), while activating the Tickets tab still renders its unchanged
  placeholder stub — guards against this ticket accidentally implementing
  `AGENTOPS-TICKETS-VIEW` ahead of schedule (mirrors the Gantt ticket's own "scope-creep guard for
  sibling views").
  Location: `dashboard-frontend/src/test/App.test.tsx`

## Scoped Pytest Commands

This ticket adds no Python source, so no new pytest target is introduced. The only pytest
obligation is confirming the untouched backend + its architecture/API-surface guards are still
green after this ticket's frontend-only changes land:

```
pytest tests/tools/test_agent_ops_dashboard_ingest.py tests/tools/test_agent_ops_dashboard_api.py tests/tools/test_agent_ops_dashboard_concurrency.py tests/tools/test_agent_ops_dashboard_api_boundary.py tests/tools/test_agent_ops_dashboard_frontend_api_surface.py tests/architecture/test_api_read_model_guard.py -m "not slow"
```

Never: `pytest tests/`.

Frontend test command (existing convention, unchanged):

```
cd dashboard-frontend && npm test
```

## Anti-Drift Test Guards

Given `AGENTOPS-ACTIVITY-GANTT`'s `DOD_BLOCKED` history — its `test_plan.md`'s anti-drift guards
were specified but skipped in the first Implement pass, causing a Verify-phase gate failure that
required a dedicated follow-up fix pass — **every guard below must be implemented in the same
pass as the feature code**, not deferred.

1. **API-surface guard — already covered, no new test needed.** `tests/tools/
   test_agent_ops_dashboard_frontend_api_surface.py` globs recursively over
   `dashboard-frontend/src/**/*.{ts,tsx}` (`_frontend_source_files()`), so it automatically picks
   up `views/ReplayTimelineView.tsx` and any new `api.ts` additions without modification. The
   guard obligation here is procedural, not a new file: **run this test as part of Verify and
   confirm it passes** rather than assuming "frontend-only work can't fail a Python test." This is
   exactly the class of guard that was silently skipped in the Gantt ticket's first pass.

2. **No client-side re-derivation of `files_touched` dedup/filtering.** A `?raw` source-text guard
   (mirroring `GanttBar.test.tsx`'s pattern:
   `import REPLAY_VIEW_SOURCE from '../views/ReplayTimelineView.tsx?raw'`) asserting the component
   source contains no second dedup-by-path construction over `tool_calls`/`files_touched` (e.g. no
   `new Map(` or `.filter(` keyed on `input_summary`/`path` applied to raw `tool_calls` data) —
   the component must read `RunTimeline.files_touched` directly and render it, not reconstruct it.
   Paired with the rendered-output test above (files-touched panel renders verbatim).

3. **No client-side phase/agent inference for `live_tail`.** Two-part guard:
   - Source-text (`?raw`): assert the component never accesses `.phase` or `.agent` on a
     `live_tail`/`RawToolCall` item (would be a TypeScript compile error today given the real
     type, but a raw-string guard is still cheap defense against a future object-literal reshape
     that silently adds those fields with a guessed value instead of leaving them genuinely
     unknown), and never branches on `tool`/`input_summary` to assign a phase label heuristically
     (e.g. no `if (tool === 'Edit') phase = 'Implement'`-style logic anywhere in the file).
   - Rendered-output: the "always show the honest caption for every live_tail item, never a
     phase/agent value" test already listed under New Tests Required.

4. **No client-side re-sort of `entries`.** Source-text guard: assert the component contains no
   `.sort(` call applied to `entries` — the backend already returns them `seq`-ascending
   (`ingest.py:536-538`), and this view must trust that order rather than re-deriving it from
   `ts` or any other key, which could silently diverge if the backend's sort key ever changes.

5. **Scrub-triggers-no-fetch guard** (already listed under New Tests Required as the
   highest-value test in this ticket) — restated here because it is the single most
   AC-critical guard: without it, a naive implementation that re-fetches
   `/api/runs/{run_id}/timeline` on every scrub-position change would pass every rendering test
   above today (current data volume, fast local network) and only surface as a real problem under
   load or in a slower environment — exactly the kind of drift a rendering-only test suite would
   never catch.

6. **Out-of-scope-view guard** (the updated `App.test.tsx` test above) — asserts the Tickets view
   still renders its unchanged stub placeholder even after this ticket lands, catching accidental
   early implementation of `AGENTOPS-TICKETS-VIEW`.

7. **Backend-untouched guard** — the Scoped Pytest Command above, run as part of Verify, is itself
   the anti-drift guard proving this "frontend-only" ticket did not modify
   `src/api/agent_ops_dashboard/ingest.py`'s join/dedup logic instead of consuming it (a green
   diff on that command with zero changes under `src/api/agent_ops_dashboard/` in `git diff` is
   the actual verification, not just "tests still pass" — tests could still pass against
   accidentally-modified-but-compatible backend code).

8. **Navigation-wiring scope guard** (conditional on investigation.md Risk #2's resolution) — if
   the plan confirms Gantt-row navigation wiring is in scope, the new navigation test above must
   assert the callback carries the correct `run_id` (not a hardcoded or most-recently-rendered
   one) — guards against a superficially-working implementation that happens to work only because
   a fixture has a single row.
