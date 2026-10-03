---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260716-AGENTOPS-REPLAY-TIMELINE
artifact_type: investigation
tags: [observability, agent-monitoring]
---

# Investigation — TCK-20260716-AGENTOPS-REPLAY-TIMELINE

## Current Behavior

**The ticket's own "Related Code Areas" list is stale**, same pattern already confirmed and
documented in the sibling `AGENTOPS-ACTIVITY-GANTT` investigation. It lists
`src/api/server.py`, `src/api/routes/history.py`, `src/observability/reporting/history_query.py`,
`src/api/read_model_cache.py`, `tools/agent-monitoring/{post_tool_hook,pre_tool_hook}.py`,
`.claude/workflows/implement-ticket.js`, and `expected: frontend/src/views/ReplayTimelineView.tsx`
— all pre-date `AGENTOPS-DASHBOARD-BACKEND` and `AGENTOPS-ACTIVITY-GANTT` landing. Ground truth,
confirmed by direct read:

**Real backend surface** (`src/api/agent_ops_dashboard/main.py:71-76`):

```python
@app.get("/api/runs/{run_id}/timeline", response_model=RunTimeline)
async def get_run_timeline(run_id: str) -> RunTimeline:
    timeline = _cache.get_timeline(run_id)
    if timeline is None:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")
    return timeline
```

`DashboardCache.get_timeline` (`src/api/agent_ops_dashboard/ingest.py:530-575`):
- Joins `events_by_run` (sorted by `seq` ascending) with `tools_by_seq` to build
  `entries: List[TimelineEntry]`, each carrying its own `tool_calls: List[RawToolCall]`.
- `is_live = run_id in self._inferred_active` (the same inferred-active set the Gantt view already
  consumes via `RunSummary.is_inferred_active` — no separate liveness computation here).
- When live, `live_tail` is built from `tools_by_run_recent` rows whose `seq` has no matching
  `events.jsonl` entry yet (i.e. genuinely un-joined tail activity).
- `files_touched = extract_files_touched(entry_dicts, live_tail_raw)` (`ingest.py:264-284`):
  iterates every `tool_calls[]` item across `entries` **and** `live_tail`, keeps only
  `tool in _EDIT_TOOLS` (`ingest.py:49`, `{"Read", "Edit", "Write", "MultiEdit"}`), dedupes by
  `input_summary` (the file path) keeping the **first** `ts`/`tool` seen, in traversal order
  (`entries` first, then `live_tail`).

**Response models** (`src/api/agent_ops_dashboard/models.py:39-89`):
- `RawToolCall`: `tool`, `input_summary`, `status`, `duration_ms: Optional[int]`, `ts`.
  **No `phase`/`agent` fields at all** — not present, not merely nullable.
- `TimelineEntry`: `seq`, `phase: Optional[str]`, `agent: Optional[str]`, `status`, `summary`,
  `ts`, `tool_call_count`, `cost_proxy_score`, `reason_code`, `tool_calls: List[RawToolCall]`.
- `FileTouch`: `path`, `tool`, `ts`.
- `RunTimeline`: `run_id`, `is_live`, `entries: List[TimelineEntry]`,
  `live_tail: List[RawToolCall] = []`, `files_touched: List[FileTouch] = []`.

**Frontend scaffold** (built by `AGENTOPS-ACTIVITY-GANTT`, confirmed DONE):
- `dashboard-frontend/src/api.ts:24-64` already declares `RawToolCall`, `FileTouch`,
  `TimelineEntry`, `RunTimeline` TypeScript interfaces that mirror `models.py` field-for-field
  (including the same absence of `phase`/`agent` on `RawToolCall`). **No `fetchRunTimeline()` or
  polling/fetch hook for `/api/runs/{run_id}/timeline` exists yet** — `api.ts` only has
  `fetchRuns`/`fetchAllRunsSince`/`useRunsPolling` for `GET /api/runs`. This ticket must add the
  timeline fetch path.
- `dashboard-frontend/src/App.tsx:4,9,40-42`: `PageView` union already includes `'replay'`, the nav
  button already exists, and the render branch is a literal stub: `<div className="p-6
  text-text-secondary">Replay timeline coming soon.</div>`. This is the real integration point —
  swap this branch for the new view component.
- `dashboard-frontend/src/views/RecentActivityGantt.tsx:71-77`: each Gantt row's `onClick` is a
  stub: `console.debug('navigate to replay timeline (not yet built)', run.run_id)`, with the
  comment *"Stub only — AGENTOPS-REPLAY-TIMELINE builds the real navigation target."* This
  confirms wiring click-through navigation (Gantt row → this run's Replay timeline) is part of
  this ticket's real surface, even though it is not spelled out as its own Acceptance Criteria
  bullet — see Risks/Open Questions.
- `dashboard-frontend/package.json` already has `@radix-ui/react-slider` as a dependency (unused
  by any current component) — installed but not yet consumed by anything, a strong signal the
  Gantt ticket's scaffold anticipated this ticket's scrub control using it rather than a
  hand-rolled drag implementation.
- Test convention confirmed from the scaffold: Vitest + Testing Library, colocated under
  `dashboard-frontend/src/test/`, `npm test` → `vitest run`. `GanttBar.test.tsx` establishes the
  **`?raw` source-text import pattern** (`import GANTT_BAR_SOURCE from
  '../components/GanttBar.tsx?raw'`, then `expect(GANTT_BAR_SOURCE).not.toMatch(/.../)`) for
  anti-drift guards that need to assert something about *how* a component is implemented, not just
  its rendered output — directly reusable here (see test_plan.md).

**No `/timeline` frontend consumer test exists yet.** Backend-side, `/timeline` already has test
coverage (`tests/tools/test_agent_ops_dashboard_api.py:40`, a 404 case; and
`tests/tools/test_agent_ops_dashboard_api_boundary.py:56`, a typed-response-model boundary check)
— this ticket does not need to add backend tests, only consume the already-tested endpoint.

## Mechanics / Engine Constraints

None apply. This is presentation-layer tooling over `agent-monitoring/*.jsonl` telemetry
(`docs/agent-monitoring/schema.md`), not simulation gameplay mechanics, and touches no
`AuthoritativeState` — same conclusion as `AGENTOPS-ACTIVITY-GANTT`'s investigation. The one
repo-wide rule that applies is the API-boundary rule ("do not expose raw domain models from APIs,"
already satisfied server-side by `models.py`'s typed Pydantic responses) and its frontend mirror:
consume the typed `RunTimeline`/`TimelineEntry`/`RawToolCall`/`FileTouch` shapes as documented,
never duck-type or recompute fields the backend already computed (dedup, join order, liveness).

## Parity Ledger Overlap

None. `docs/parity_ledger/infrastructure.yaml`'s `INFRA-275` entry (`status: verified`,
`priority: P2`) already covers the backend `/api/runs` surface this ticket's sibling consumes;
the `/timeline` endpoint is the same backend product and inherits the same non-gating status — no
P0 entries, no new ledger entry required for this presentation-only frontend work.

**False-positive check, worth recording explicitly:** `mcp__knowledge-search__search_docs` for
"Run Detail Replay timeline view scrubbable playback of a run" and a grep of `docs/parity_ledger/`
for "replay" both surface only the **simulation engine's own Replay system**
(`docs/engine/contracts/replay_contract.md`, `docs/engine/contracts/concurrent_integrity_contract.md`,
parity entries under `docs/parity_ledger/infrastructure.yaml` about `ReplayManager`/
`EventRecorder`/deterministic world-state replay). That system is unrelated — it replays
simulation world state for determinism/forensics, not agent-monitoring tool-call history for a
dashboard UI. Confirmed by reading `replay_contract.md`'s Purpose section ("non-authoritative
stream of simulation events for diagnostics and forensics"). No action needed; flagging so a
future investigator doesn't chase this false lead.

## Prior Work

- `TCK-20260716-AGENTOPS-DASHBOARD-BACKEND` (done): built `main.py`/`ingest.py`/`models.py`,
  including `/timeline` and its join/dedup logic this ticket consumes read-only.
- `TCK-20260716-AGENTOPS-ACTIVITY-GANTT` (done, plus a `DOD_BLOCKED` fix-pass — see Anti-Drift
  Hazards): built the `dashboard-frontend/` scaffold this ticket extends, and established the
  conventions this ticket should reuse rather than reinvent:
  - `api.ts`'s typed-fetch + hook pattern (`fetchRuns`/`useRunsPolling`) as the template for a new
    `fetchRunTimeline`/timeline-fetch hook — noting the *scrub-must-not-fetch* constraint here
    means this new hook should **not** mirror `useRunsPolling`'s `setInterval` re-fetch loop for
    the scrub interaction itself (see Risks).
  - `GanttBar.tsx`'s mutually-exclusive style-class pattern and its `GanttBar.test.tsx` `?raw`
    source-text anti-drift guard — the template for this ticket's "never re-derive
    dedup/phase/agent client-side" guards.
  - `App.tsx`'s stub-placeholder convention for not-yet-built views, and `App.test.tsx`'s existing
    assertion that the `'replay'` branch renders `"Replay timeline coming soon."` — **this
    assertion is exactly what this ticket must invalidate/update**, not preserve (see Risks).
  - The **`DOD_BLOCKED` lesson**: `AGENTOPS-ACTIVITY-GANTT`'s first implementation pass skipped
    its own `test_plan.md`'s specified anti-drift guards (API-surface guard,
    no-client-side-re-derivation guard), which were only added in a follow-up fix pass after a
    Verify-phase gate failure. This ticket's `test_plan.md` must not repeat that gap — guards are
    listed exhaustively there and must land in the same implementation pass as the feature code.

## Risks and Open Questions

1. **`live_tail`'s `phase`/`agent` "null" framing is imprecise relative to the real model — flag,
   don't silently paper over.** `UI_INTERACTION_SPEC.md` §3a and `DATA_MODEL.md` §1 both describe
   `live_tail` items as having "`phase`/`agent` ... `null`," and this ticket's own AC #3 says
   "every live_tail item displays phase=null and agent=null explicitly." But `RawToolCall`
   (`models.py:39-44`, mirrored exactly in `api.ts:24-30`) **has no `phase`/`agent` field at all**
   — not an `Optional[str] = None` that happens to be null, simply absent from the type. Reading
   `.phase`/`.agent` off a `live_tail` item is a TypeScript compile error, not a null-check. The
   only coherent implementation is: the live-tail rendering path renders the
   "(phase unknown — run still in progress)" caption **unconditionally** for every `live_tail`
   entry, never by checking a field value. This is a wording gap between the idea docs/AC and the
   real schema, not a behavior ambiguity — but the planner should state this interpretation
   explicitly rather than an implementer discovering the type mismatch mid-build.
2. **Gantt-row click-through wiring is real scope but not a formal Acceptance Criterion.** The
   ticket's own `## Acceptance Criteria` list (four bullets) covers only the Replay view's own
   rendering/scrub/live-tail/files-touched behavior — it does not explicitly say "wire
   `RecentActivityGantt`'s `onClick` to navigate here." But `RecentActivityGantt.tsx:74`'s comment
   explicitly names this ticket as the owner of "the real navigation target," and leaving the stub
   `console.debug` in place would mean the feature is unreachable from the UI entirely (no router,
   no other entry point to a specific `run_id`'s Replay view). **Needs an explicit decision**: this
   ticket should be treated as also wiring (a) `App.tsx` state for "which run is selected" (there
   is no such state today — the `PageView` union has no run-scoped parameter) and (b)
   `RecentActivityGantt`'s `onClick` to set that state and switch to the `'replay'` view. This is a
   real design surface (state shape, prop-drilling vs. context, no `react-router` per established
   convention) that the plan must pin down, not an incidental detail.
3. **Live-run polling vs. scrub-must-not-fetch are two different concerns that must not be
   conflated.** `UI_INTERACTION_SPEC.md` §3b is explicit: "Playback never fetches new data — it
   replays the already-fetched `RunTimeline` payload client-side; polling for genuinely new data
   (the live edge, §3a) is a separate, independent refresh cycle." AC #4 only requires that
   *scrubbing* triggers no fetch — it does not by itself require this ticket to implement ongoing
   background polling for a still-live run's growing `live_tail`. Whether this ticket also
   implements that independent live-refresh cycle, or fetches the timeline exactly once per
   run-selection and leaves live-refresh for later, is an open scope question the plan should
   settle explicitly (the AC text is satisfiable either way; only the *scrub* path is pinned down).
4. `MONITORING_INSTRUMENTATION_GAP` / `idea_agent_monitoring_live_phase_label.md`'s fix (making
   `phase`/`agent` real, non-null fields on live tool-call rows) is confirmed independent and
   non-blocking — this view must render honestly with today's schema (see Risk #1), not wait on or
   attempt that fix.
5. `App.test.tsx`'s two existing assertions (`"Replay timeline coming soon."` present when the
   Replay tab is active, `recent-activity-gantt` absent) will be **falsified** by a correct
   implementation of this ticket. This is expected, in-scope test churn, not a regression to avoid
   — the test_plan.md must call this out explicitly so it isn't mistaken for "keep this test
   green as-is."

## Anti-Drift Hazards

- Do not implement or modify `/api/runs/{run_id}/timeline`, its `seq`-ordered join, or
  `extract_files_touched`'s dedup/filter logic (`ingest.py:264-284`, `530-575`) — backend-owned,
  already done and tested. Consume `RunTimeline` fields verbatim.
- Do not attempt to fix the `live_tail` `phase`/`agent` null-labeling gap — independent sibling
  idea, explicitly out of scope. Render the honest "(phase unknown — run still in progress)"
  caption unconditionally; never infer/guess a phase or agent from `tool`/`input_summary`
  heuristics.
- Do not re-implement `files_touched` deduplication or Read/Edit/Write/MultiEdit filtering
  client-side — render `RunTimeline.files_touched` as received; any client-side re-filtering risks
  silently diverging from the backend's dedup-keep-first-seen semantics.
- Do not build the Recent Activity Gantt view or Tickets table view — both explicitly out of
  scope; if Gantt-row navigation wiring is confirmed in scope (Risk #2), touch only the `onClick`
  handler and whatever minimal App-level state it needs, not the Gantt view's own rendering logic.
- Do not add Makefile targets, `vite build` production wiring, or `FastAPI` `StaticFiles`
  mounting — `AGENTOPS-BUILD-SERVE`'s scope.
- Do not introduce a routing library (`react-router` or similar) — mirror the existing
  `useState`-based view-switching convention, extended with whatever minimal selected-run state is
  needed (Risk #2), not a new dependency.
- Do not let the scrub/play control trigger any network fetch — AC #4 is explicit and testable
  (see test_plan.md); the timeline payload is fetched once (per run selection, and possibly once
  more on an independent live-refresh cycle per Risk #3) and all playback/scrub interaction
  operates purely over the already-fetched in-memory payload.
- Do not touch `src/api/server.py`, `src/api/ws/stream.py`, `src/api/routes/history.py`, or
  `src/api/read_model_cache.py` — none are this dashboard's real API surface; already guarded
  directory-wide by `tests/tools/test_agent_ops_dashboard_frontend_api_surface.py`, which will
  automatically cover any new file under `dashboard-frontend/src/` including
  `views/ReplayTimelineView.tsx` (confirmed by reading its `_frontend_source_files()` helper — a
  recursive glob over `dashboard-frontend/src`, not a hardcoded file list). No ticket-specific
  duplicate of this guard is needed.
- Carry forward the `DOD_BLOCKED` lesson explicitly: implement every anti-drift guard listed in
  test_plan.md in the same pass as the feature code. Do not defer them to a follow-up fix pass.
