---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260720-PROGRESS-TIMELINE-VIEW
artifact_type: investigation
tags: [dashboard, observability]
---

# Investigation — TCK-20260720-PROGRESS-TIMELINE-VIEW

## Current Behavior

### `dashboard-frontend/src/views/RecentActivityGantt.tsx` (105 lines, being replaced)
- `RecentActivityGantt({ onSelectRun })`: fixed 24h window (`SINCE_WINDOW_MS`), `nowIso` ticks
  every 1s (`NOW_TICK_MS`), calls `useRunsPolling(sinceIso)` (L36) for the run list.
- Renders `<Legend />`, `<TimeAxis windowStartIso windowEndIso />`, then one row per run inside a
  Radix `Tooltip.Provider`/`Tooltip.Root` — each row is a `<div className="relative h-6 mb-1" onClick={() => onSelectRun(run.run_id)}>` wrapping `<GanttBar .../>` (L74-88). This
  `.relative.h-6` click wrapper + `onClick` is the entire row-click-through mechanism; App.test.tsx
  drives it today via a raw DOM `MouseEvent('click')` dispatched on that wrapper (see below).
- `justSettledIds`/`previousActiveByRunIdRef` (L38-58) manage a 300ms CSS transition
  (`gantt-bar--settling`) when a run flips from inferred-active to settled — this is local UI
  polish state with no bearing on `toChartOption`'s pure data shape, but is currently the *only*
  place `is_inferred_active` transitions are observed client-side.
- Tooltip content (L95): `` `${run.run_id} · ${run.tier} · ${run.workflow} · ${durationLabel(run, nowIso)} · ${run.agent_count} agents` `` — a plain `·`-joined string, confirming the ticket's
  claim about GanttBar's tooltip shape. **Gap vs. the new AC**: it has no `phase`/`agent`/`status`
  field at all today (only run-level fields) — the new tooltip.formatter's `phase`/`agent`/`status`
  fields are new information, not carried over from an existing per-run string.

### `dashboard-frontend/src/components/GanttBar.tsx` (112 lines, deleted this ticket)
- Exports: `StatusBucket` (type), `classifyFinalStatus()` (L8-16, `DONE`→`done`,
  `*_BLOCKED`/`*_FAILED`/`CONFLICTS_DETECTED`→`failed`, else→`neutral`), `STATUS_BUCKET_CLASS`
  (L18-22), `GanttBarProps` (L44-50), `toPercent()` (L52-61), `GanttBar()` (L63-111).
- `toPercent(ts, windowStartIso, windowEndIso)`: clamps `ts` into `[windowStart, windowEnd]`,
  returns a 0-100 percent. Confirmed this is the **only** definition — `TimeAxis.tsx` imports it
  rather than redeclaring it (enforced by its own test, `TimeAxis.test.tsx:8-11`).
- `GanttBar()` branches on `run.is_inferred_active` (never re-derives activity from timestamps —
  enforced by `GanttBar.test.tsx`'s anti-drift guard at L29-85, which regexes the source for
  `Date.now()`/`new Date(` and asserts the `if (run.is_inferred_active)` branch literally exists).
- **Confirmed no other importer.** `grep -rn "GanttBar\|TimeAxis\|Legend\b\|toPercent"` across
  `dashboard-frontend/src` (excluding the three files' own definitions) returns only:
  `RecentActivityGantt.tsx` (the view being replaced), `GanttBar.test.tsx`, `TimeAxis.test.tsx`,
  and two prose-only comment mentions in `ReplayTimelineView.tsx` (not real imports — that file
  intentionally does *not* reuse `classifyFinalStatus`, per its own comment). Deletion of all
  three files is safe once `RecentActivityGantt.tsx` itself is replaced.
- **CSS not listed in the ticket's Related Code Areas**: `dashboard-frontend/src/index.css:37-46`
  defines `.gantt-bar--inferred-pattern` (diagonal-stripe background for the "~est." live bar),
  used only by `GanttBar.tsx`. This becomes dead CSS once `GanttBar.tsx` is deleted and is a real
  gap in the ticket's file list — should be removed in the same change, not left orphaned.

### `dashboard-frontend/src/components/TimeAxis.tsx` / `Legend.tsx`
- `TimeAxis`: 7 fixed ticks (`TICK_COUNT`), each positioned via `GanttBar`'s `toPercent()`. No
  independent state.
- `Legend`: static 4-item legend (done/failed/neutral/inferred), reads `STATUS_BUCKET_CLASS` from
  `GanttBar.tsx`. Neither has any importer outside its own test and `RecentActivityGantt.tsx` —
  same confirmation as above.

### `dashboard-frontend/src/App.tsx` (62 lines)
- `PageView = 'activity' | 'tickets' | 'replay' | 'stats'` (L7). `NAV_ITEMS` (L9-14) is
  `[{view:'activity', label:'Recent Activity'}, ...]`. Nav buttons render `item.label` and set
  `currentView` on click (L30-42).
- `currentView === 'activity' && <RecentActivityGantt onSelectRun={handleSelectRun} />` (L46).
  `handleSelectRun(runId)` (L20-23) sets `selectedRunId` and flips `currentView` to `'replay'` —
  this is the entire row-click-through wiring; `ProgressTimelineView` only needs to accept the
  same `onSelectRun: (runId: string) => void` prop and call it, exactly like `RecentActivityGantt`
  does today. Nothing else in App.tsx couples to `RecentActivityGantt` by name beyond the import
  and this one conditional render line.
- AC #5 explicitly requires the `'activity'` `PageView` value and the click-through wiring to be
  **preserved** — confirmed there is nothing else referencing `'activity'` as a string that would
  need touching (grep confirms `'activity'` appears only in `App.tsx`'s own type union, its
  `NAV_ITEMS` entry, and the `currentView === 'activity'` conditional).

### `dashboard-frontend/src/api.ts` (447 lines)
- `useRunsPolling(sinceIso, intervalMs = 5000)` (L414-447) — the sibling pattern
  `useRunTimelinesPolling` must mirror: `useState` for the result + `isLoading`/`error`, an
  `useEffect` closing over a `cancelled` flag, an async `poll()` called immediately then on
  `setInterval(poll, intervalMs)`, cleanup clears the interval and sets `cancelled = true`.
  `fetchAllRunsSince()` (L380-394) is the pagination-loop precedent (`while` via `for (;;)`,
  looping `offset += RUNS_PAGE_LIMIT` until a short page), and `mergeAndSortRuns()` (L396-406) is
  the dedupe-by-`run_id` + `localeCompare` descending sort on `start_ts ?? inferred_start_ts ?? ''`
  that `toChartOption`'s "newest-first" ordering must match.
- **The bulk timeline endpoint has zero frontend consumption today.** No `BulkRunTimeline`
  interface, no `fetchRunTimelines`/`fetchAllRunTimelinesSince` function, no
  `useRunTimelinesPolling` hook exist anywhere in `api.ts` yet — confirmed by reading the full
  file. This is expected: `TCK-20260720-BULK-RUN-TIMELINE`'s own Anti-Drift Hazards explicitly
  state "Frontend (`dashboard-frontend/src/api.ts`) is explicitly out of scope... that's the
  downstream `ProgressTimelineView` ticket's job" — this ticket is the first to add it, not a
  regression.
- `RunTimeline`/`TimelineEntry`/`RawToolCall`/`FileTouch` TS interfaces (L24-57) already exist and
  mirror `models.py` field-for-field (per the file's own header convention) — `toChartOption`'s
  `entriesByRun: Record<string, TimelineEntry[]>` parameter should reuse the existing
  `TimelineEntry` interface, not redeclare it, and the new `BulkRunTimeline` interface must mirror
  `models.py::BulkRunTimeline` exactly: `{ entries_by_run: Record<string, TimelineEntry[]> }`.

### `src/api/agent_ops_dashboard/main.py` / `models.py` / `ingest.py` (backend, already DONE — read-only context, not touched by this ticket)
- `GET /api/runs/timeline` (`main.py:77-84`) → `BulkRunTimeline(entries_by_run: Dict[str,
  List[TimelineEntry]])` (`models.py:272-273`). **No `RunSummary` fields are in this response** —
  it is entries-only, confirmed by reading `models.py` and `ingest.py:737-770`
  (`DashboardCache.get_bulk_timeline`). This means `toChartOption(runs, entriesByRun, nowIso)`'s
  `runs: RunSummary[]` parameter must come from a **separate** call — i.e. `ProgressTimelineView`
  needs both `useRunsPolling(sinceIso)` (existing, for `RunSummary[]`/newest-first ordering/
  `is_inferred_active`) **and** the new `useRunTimelinesPolling(sinceIso)` (for
  `entries_by_run`), and pass both into `toChartOption` — not a single combined hook. This is an
  implementation detail the ticket text doesn't spell out explicitly but the backend contract
  forces.
- `get_bulk_timeline`'s own pagination (`limit` default 50, max 100 — same bound as `/api/runs`)
  means `useRunTimelinesPolling` needs the same `fetchAllRunsSince`-style offset-loop-until-short-
  page pattern as `useRunsPolling`, not a single unpaginated fetch, to avoid silently truncating a
  busy window (mirrors `api.ts`'s own comment at L375-377 about `/api/runs` having no total-count
  field).
- Backend route ordering note (from the BULK-RUN-TIMELINE ledger entry, INFRA-301): `/api/runs/
  timeline` is registered **before** `/api/runs/{run_id}` in `main.py` specifically to avoid the
  literal string `"timeline"` being captured by the `{run_id}` wildcard — not a frontend concern,
  but confirms the route path itself (`/api/runs/timeline`) is exactly as the ticket names it.

### `dashboard-frontend/src/lib/phasePalette.ts` (85 lines, already DONE — confirmed real exports)
- `WorkflowPhase` (union of the 21 literal phase strings), `PhaseFamily` (8-member union),
  `PHASE_FAMILY: Record<WorkflowPhase, PhaseFamily>`, `PHASE_PALETTE: Record<WorkflowPhase, string>`
  (hex per phase), `getPhaseColor(phase): string` (pure passthrough). All four names match the
  ticket's own claim exactly.
- **No color exists for the "live"/in-progress segment.** The palette module covers only the 21
  settled `WORKFLOW_PHASES` strings — there is no `LIVE_COLOR` or equivalent export, and
  `TCK-20260720-ECHARTS-PHASE-PALETTE`'s own investigation/plan never mention a live-state color
  (its scope was explicitly "21 distinct WORKFLOW_PHASES strings" only). The old `GanttBar.tsx`
  signaled "live" via a CSS diagonal-stripe pattern (`.gantt-bar--inferred-pattern`) plus a "~est."
  text label, not a solid color — there is no direct color precedent to reuse for the "visually
  distinguishable... trailing 'live' segment" AC. **This is a real gap Plan must resolve**, not an
  oversight in this investigation (see Risks below).
- `dashboard-frontend/src/lib/chartPalette.ts` (`CHART_SERIES_1`/`CHART_SERIES_2`) is a sibling,
  unrelated 2-color module used by `BarChart`/`GroupedBarChart` — not part of this ticket's scope
  and should not be touched.

### `dashboard-frontend/package.json`
- `echarts": "^6.1.0"` and `"echarts-for-react": "^3.0.6"` are already declared under
  `dependencies` (confirmed — added by `TCK-20260720-ECHARTS-PHASE-PALETTE`) and `node_modules/`
  already has them installed (`echarts/core.js`, `echarts/charts.js`, `echarts/components.js`,
  `echarts/renderers.js` all present; `echarts-for-react`'s `package.json` shows
  `main: lib/index.js`, `module: esm/index.js`, default export `ReactECharts`). No install step is
  needed for this ticket.
- **Confirmed no `echarts`/`ReactECharts` usage exists anywhere in `dashboard-frontend/src`
  today** (`grep -rln "echarts|ReactECharts" src --include="*.tsx" --include="*.ts"` returns
  nothing) — `ProgressTimelineView.tsx` will be the first real consumer, exactly as the palette
  ticket's own investigation predicted ("no echarts usage code here... deferred to the downstream
  ProgressTimelineView ticket").
- `tests/tools/test_agent_ops_dashboard_frontend_api_surface.py::test_no_source_file_imports_full_echarts_bundle`
  (L70-85) is a **live, currently-passing architecture guard** that will fail the moment
  `ProgressTimelineView.tsx` (or any new file) contains a bare `from 'echarts'`/`require('echarts')`
  import — this ticket's own new file is now within that test's scanned surface and must use only
  `echarts/core` + tree-shaken submodule paths (`echarts/charts`, `echarts/components`,
  `echarts/renderers` per the actually-installed package layout confirmed above).

### `dashboard-frontend/src/components/GlossaryTooltip.tsx` / `GlossaryHintIcon.tsx`
- `GlossaryTooltip({ term, glossary, children })`: a **React component** — wraps `children` in a
  Radix `Tooltip.Root`/`Tooltip.Trigger`/`Tooltip.Portal`/`Tooltip.Content` tree, rendering
  `entry.description` as JSX children inside `Tooltip.Content` (L32-49). Confirmed the ticket's
  claim is accurate in substance: this component's *implementation* (JSX + Radix component
  wiring, mount/hover lifecycle managed by React + Radix's own Portal/positioning logic) genuinely
  cannot execute inside an ECharts `tooltip.formatter` callback, which runs outside React's render
  tree and must return either a plain string (ECharts inserts it as the tooltip DOM node's
  `innerHTML`) or a raw `HTMLElement` — not a React element tree.
- **However, the underlying description *text* is not locked inside the component.** `glossary`
  (type `GlossaryTerms = Record<string, GlossaryEntry>`, from `useGlossary()` in `api.ts`) is a
  flat map keyed directly by term string — confirmed via `src/api/agent_ops_dashboard/ingest.py`'s
  `get_glossary()` (L902-948): phase terms (`category="phase"`, e.g. `"Scope"`) and agent-role
  terms (`category="agent"`, e.g. `.claude/agents/*.md` `name:` values like `"implementer"`) are
  merged into the **same flat dict**, not namespaced by category. So `glossary["Scope"]` and
  `glossary["implementer"]` both resolve directly with no collision (the backend's own merge logic
  has explicit shadow-protection comments confirming no current term collisions across the three
  merged sources). This means the *data* GlossaryTooltip renders is fully available to a plain
  string-building function — only the component's *rendering mechanism* is unusable, not the data.
- 21 `category="phase"` glossary entries confirmed present in `docs/guidelines/glossary_registry.jsonl`
  (one per `WORKFLOW_PHASES` string, from `TCK-20260719-PHASE-GLOSSARY-DESCRIPTIONS`). No
  `category="agent"` entries exist in that same file — agent-role descriptions are sourced live
  from `.claude/agents/*.md` frontmatter at request time (`_load_agent_role_descriptions()`), not
  stored in the static registry file, but they still land in the same `GlossaryResponse.terms`
  dict the frontend consumes identically either way.

### Existing test files (coverage shape to preserve/replace)
- `RecentActivityGantt.test.tsx` (11 tests): DOM class-based bucket assertions
  (`gantt-bar--authoritative`/`--inferred`), `data-run-id`/`data-start`/`data-end` attribute
  checks, `toPercent`-derived `bar.style.width` assertion, Radix tooltip content-string assertion,
  row-click via raw `MouseEvent` dispatch on `.relative.h-6`. All of this is DOM-shape-coupled to
  the div/CSS rendering model being retired — none of it can survive verbatim once ECharts owns
  rendering (confirms the ticket's own framing).
- `GanttBar.test.tsx` (anti-drift guard, source-regex-based) and `TimeAxis.test.tsx`
  (`toPercent`-reuse guard) both test files/exports being deleted — deleted wholesale, not
  rewritten.
- `App.test.tsx`: **7 occurrences** of `screen.getByTestId('recent-activity-gantt')` /
  `queryByTestId('recent-activity-gantt')` across 5 `it()` blocks (L130, 142, 145, 150, 187, 197,
  200). One test in particular — `'Gantt row click navigates to that run\'s Replay timeline...'`
  (L174-188) — drives the row click via `document.querySelector('[data-run-id="run-nav-target"]')`
  then `.closest('.relative.h-6')` then a raw DOM `click`. **This DOM-query approach cannot survive
  the rewrite even with a testid rename** — ECharts custom-series data points are canvas-rendered,
  not real DOM elements with `data-run-id` attributes, so this specific test must be restructured
  around whatever click-dispatch mechanism `ProgressTimelineView` actually wires (see Risks).
- `useRunsPolling.test.ts` (2 tests): pagination-loop and single-page cases — the direct template
  `useRunTimelinesPolling.test.ts` should mirror, adapted to the bulk endpoint's response shape
  (`entries_by_run` merge instead of a flat array).
- `phasePalette.test.ts` (already DONE, 4 tests): literal 21-key completeness, WCAG contrast floor
  (WARN-allowlisted), purity, 8-family cap — read for context only, not modified by this ticket.

## Mechanics / Engine Constraints

None. This is `layer: observability` dashboard/agent-tooling work over `tickets/**` and
`agent-monitoring/*.jsonl` — it does not touch `AuthoritativeState`, and no chapter of
`docs/mechanics/` or contract in `docs/engine/` governs it. Matches every prior Agent Ops
Dashboard ticket's investigation finding (both prerequisite tickets' investigations state the same
"None" verbatim, citing `docs/parity_ledger/infrastructure.yaml`'s `support_boundary` notes across
INFRA-275 through INFRA-302).

## Parity Ledger Overlap

`docs/parity_ledger/infrastructure.yaml` is the only ledger file with dashboard entries. Directly
relevant, both `status: verified`, `priority: P2` (no P0 — dashboard tooling has never carried a
P0 entry in this ledger):

- **INFRA-301** (`TCK-20260720-BULK-RUN-TIMELINE`) — the bulk endpoint this ticket consumes.
  `test_path: tests/tools/test_agent_ops_dashboard_api.py::test_bulk_run_timeline_route_matches_per_run_route_for_same_run_id`
  — confirmed this test file/test name exists and passes today (read directly). Its own
  `v2_evidence` explicitly notes "No frontend consumption wired in this ticket... deferred to the
  downstream ProgressTimelineView ticket" — i.e. this ticket is the one that discharges that
  deferral.
- **INFRA-302** (`TCK-20260720-ECHARTS-PHASE-PALETTE`) — the palette/dependency this ticket
  consumes. `test_path: dashboard-frontend/src/test/phasePalette.test.ts` — confirmed exists and
  passes today. Its `v2_evidence` explicitly notes "no rendering/UI integration in this ticket...
  both deferred to the downstream ProgressTimelineView ticket."
- Next available entry number is **INFRA-303** (INFRA-302 is the current last entry, confirmed by
  reading the file tail) — this ticket should add a new entry documenting `ProgressTimelineView.tsx`,
  `useRunTimelinesPolling`, `toChartOption`, and the deletion of `GanttBar`/`TimeAxis`/`Legend`,
  following the established "new capability → new entry, don't edit prior entries" pattern (same
  precedent both prerequisite entries themselves followed).
- No P0 entries anywhere in the ledger reference this module — no `test_path` gate beyond the
  project's general "tests were run/updated" rule applies.

## Prior Work

- **`TCK-20260720-BULK-RUN-TIMELINE`** (`stored_artifacts/`) — backend endpoint this ticket
  consumes; confirmed its Anti-Drift Hazards explicitly defer frontend wiring to this ticket.
- **`TCK-20260720-ECHARTS-PHASE-PALETTE`** (`stored_artifacts/`) — dependency + color module this
  ticket consumes; confirmed its Anti-Drift Hazards explicitly defer ECharts *usage* code (only
  the dependency declaration and color module were added) to this ticket, and its own Risk #2
  already pre-resolved that pattern/texture must not be the default within-family distinguisher
  (lightness is) — relevant precedent for how to visually encode the "live" segment (see Risks).
- **`TCK-20260718-GLOSSARY-TOOLTIPS-FRONTEND`** / **`TCK-20260719-PHASE-GLOSSARY-DESCRIPTIONS`** /
  **`TCK-20260719-AGENT-ROLE-GLOSSARY`** (`tickets/done/`) — established `GlossaryTooltip`, the
  flat `GlossaryTerms` map, and authored all 21 phase + agent-role descriptions this ticket's
  tooltip.formatter should surface (not re-author).
- **`TCK-20260717-GANTT-TIME-AXIS`** / **`TCK-20260716-AGENTOPS-ACTIVITY-GANTT`** (`tickets/done/`)
  — origin tickets for the components being retired; read for context on why the current
  DOM-percent model exists, not reused.
- `docs/plans/agent_ops_dashboard/proposal_progress_timeline.md` — the proposal this ticket was
  carved from; its "Concerns for Comprehend/Investigate" §3 is this ticket's own scope verbatim,
  confirmed already resolved/consistent with everything found above.

## Risks and Open Questions

1. **Open Question 1 — tooltip.formatter and glossary text. Recommendation (concrete, for Plan to
   formalize):** Do **not** attempt to render `<GlossaryTooltip>` (or any React component) inside
   `tooltip.formatter` — it cannot run there (see Current Behavior above). Instead, have
   `ProgressTimelineView` call the existing shared `useGlossary()` hook (already module-cached,
   fetched once per page load) and build the formatter's return value as a manually-constructed
   HTML string, looking up `glossary[phase]?.description` and `glossary[agent]?.description`
   directly from the same flat `GlossaryTerms` map `GlossaryTooltip` itself reads — i.e. reuse the
   *data*, not the *component*. Append each description (HTML-escaped) as a secondary line under
   the phase/agent fields; if an entry is missing (registry gap, or glossary still loading),
   omit that line entirely — mirroring `GlossaryTooltip`'s own graceful-degradation contract
   (never blocks the primary tooltip fields). This keeps "no hardcoded description text" intact
   (the established rule per `api.ts`'s own header comment) without depending on JSX.
2. **Open Question 2 — nav label/testid rename. Recommendation (concrete, for Plan to formalize):**
   Keep `App.tsx`'s `PageView` value `'activity'` and the visible nav button text `'Recent
   Activity'` **unchanged** — AC #5 explicitly requires the `'activity'` view to be "preserved,"
   and "Recent Activity" is a generic content-freshness label with no "Gantt" naming collision to
   resolve (the proposal's "drop Gantt naming" directive is about the *chart-type* name, not this
   unrelated tab label). **Do** rename the view root's `data-testid` from `"recent-activity-gantt"`
   to `"progress-timeline-view"` — every sibling view (`TicketsView`→`tickets-view`,
   `StatsView`→`stats-view`, `ReplayTimelineView`→`replay-timeline-view`) uses exactly this
   kebab-case-of-component-name convention, and keeping a testid that literally contains "gantt"
   on a component explicitly renamed away from that concept would be an inconsistency, not a
   preservation. This requires updating **7 occurrences** across 5 `it()` blocks in
   `App.test.tsx` (L130, 142, 145, 150, 187, 197, 200) — confirmed exact count via grep — while the
   `getByRole('button', { name: 'Recent Activity' })` assertions need no change.
3. **DOM-based row-click test cannot be testid-renamed alone — it must be restructured.**
   App.test.tsx's `'Gantt row click navigates...'` test (L174-188) drives the click via
   `document.querySelector('[data-run-id=...]').closest('.relative.h-6')` — both of those are
   artifacts of the div-based `GanttBar` rendering model, which ECharts' canvas-based custom
   series does not reproduce (no real DOM node per segment carries `data-run-id`). This is not
   solvable by a rename; it requires either (a) mocking `echarts-for-react`'s `<ReactECharts>` in
   tests (capturing the `onEvents.click` handler passed as a prop and invoking it directly with a
   synthetic ECharts click-event object), or (b) `ProgressTimelineView` exposing a plain DOM
   affordance for the click-through path (e.g. wiring `onEvents={{click: ...}}` on
   `<ReactECharts>` and testing that wiring via a mocked component). This must be resolved in
   `plan.md`, not assumed — flagging as blocking-for-Plan, not blocking-for-Investigate.
4. **No color exists today for the "live"/in-progress trailing segment.** `phasePalette.ts` covers
   only the 21 settled phase strings (see Current Behavior) — there is no precedent hex or export
   for a "visually distinguishable... live" state. AC #2 requires this segment be "visually
   distinguishable from settled segments" but does not specify how. **Not blocking** (a reasonable
   default exists — e.g. a neutral gray/pattern via ECharts' built-in `decal` fill, echoing the old
   CSS diagonal-stripe treatment, or a fixed `text-secondary`-toned solid fill reused from
   `GanttBar`'s Tailwind class) but Plan must make and document this call explicitly rather than
   inventing an ungoverned 22nd color outside `phasePalette.ts`'s 8-family cap.
5. **jsdom has no real `<canvas>` rendering support** (`devDependencies` confirmed: `jsdom`, no
   `canvas`/node-canvas polyfill package). A test that fully mounts `<ReactECharts>` and expects
   pixel-accurate canvas output will not work reliably in this test environment. This strongly
   supports (and is likely why) the ticket's own AC explicitly asks only for "a smoke test that
   ReactECharts receives a non-null option" rather than pixel assertions — Plan should mock
   `echarts-for-react` in `ProgressTimelineView`'s own test file (assert on the `option`/`onEvents`
   props passed to the mocked component) rather than attempt real canvas rendering, mirroring how
   `RecentActivityGantt.test.tsx` already mocks `useRunsPolling` rather than hitting real `fetch`.
6. **`entries_by_run` and `runs` come from two independent polling hooks, not one.** The bulk
   endpoint's response has no `RunSummary` fields (see Current Behavior) — `ProgressTimelineView`
   must call both `useRunsPolling(sinceIso)` (existing) and the new
   `useRunTimelinesPolling(sinceIso)`, and the two responses are not guaranteed to be
   perfectly in sync tick-to-tick (independent 5s polls). `toChartOption` should tolerate a
   `run_id` present in `runs` but absent from `entriesByRun` (e.g. a just-started run with zero
   settled entries yet) without crashing — worth an explicit edge-case test.
7. **`index.css`'s `.gantt-bar--inferred-pattern` rule is an unlisted deletion target.** Not in the
   ticket's Related Code Areas or Scope bullets — flagging so Plan adds it explicitly rather than
   leaving dead CSS behind once `GanttBar.tsx` is deleted.
8. **C5 docs update is correctly deferred, but leaves two docs actively wrong once this ticket
   lands.** Confirmed both `docs/guides/agent_ops_dashboard.md` (L51, 72, 136, 161-173) and
   `docs/observability/agent_ops_dashboard_contract.md` (L219, 230-264, 285-310) describe
   `RecentActivityGantt`/`GanttBar`/`Legend`/`TimeAxis` by name and behavior in detail — this is
   already an explicit known-gap per the ticket's own Assumptions section, restated here only for
   completeness, not a new finding.

## Anti-Drift Hazards

- **Do not re-derive `is_inferred_active` from raw timestamps anywhere in the new code** — the
  same rule `GanttBar.test.tsx`'s anti-drift guard enforces today (never call `Date.now()`/`new
  Date()` to judge activity; always branch on the backend-computed `run.is_inferred_active`
  field). `toChartOption` must carry this rule forward even though the old guard test is deleted —
  recommend an equivalent regex-based guard in the new test suite.
- **Do not touch `useRunsPolling`, `mergeAndSortRuns`, or `fetchAllRunsSince`** — `toChartOption`'s
  "newest-first, matching mergeAndSortRuns' sort" requirement means *matching* the existing sort
  behavior (`start_ts ?? inferred_start_ts ?? ''`, `localeCompare` descending), not modifying the
  function itself; `useRunTimelinesPolling` is a new, separate function, not a rewrite of the
  existing hook.
- **Do not modify `src/api/agent_ops_dashboard/{main,ingest,models}.py`** — the bulk endpoint is
  DONE and out of scope; this ticket only consumes it via a new frontend fetch/hook.
- **Do not modify `phasePalette.ts`'s existing 21-key `PHASE_PALETTE`/`PHASE_FAMILY` exports** —
  any new "live" color must be either a new, separately-named export in that same module (kept
  within its own 8-family governance) or a component-local constant explicitly out of the phase
  palette's key set — never silently expand `PHASE_PALETTE` to 22 keys, which would break
  `phasePalette.test.ts`'s literal-21 completeness assertion.
- **Do not import the bare `'echarts'` bundle** — `test_no_source_file_imports_full_echarts_bundle`
  is a live, passing guard that will fail on any `ProgressTimelineView.tsx` code using a
  non-tree-shaken import.
- **Do not leave `RecentActivityGantt.test.tsx`, `GanttBar.test.tsx`, or `TimeAxis.test.tsx` as
  dead files** — deleting the source components without deleting or rewriting their test files
  leaves failing imports in the test suite (and `GanttBar.test.tsx`'s source-regex assertions
  would otherwise silently pass-by-absence, defeating the guard's purpose).
- **Do not touch `docs/guides/agent_ops_dashboard.md` or
  `docs/observability/agent_ops_dashboard_contract.md`** — explicitly deferred to the separate C5
  follow-up ticket per this ticket's own Out of Scope; resist the temptation to "fix the obviously
  stale doc" here.
- **Do not wire filtering/grouping-by-tier/workflow, or the range-control preset UI** — both
  explicitly out of scope per the proposal doc (Concerns #4 and the "Explicitly out of scope"
  section) and this ticket's own Out of Scope bullets.
