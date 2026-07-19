---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260719-STATS-PHASE-OUTLIERS-EXPOSE
artifact_type: plan
tags: [dashboard, observability, agent-monitoring]
---

# Implementation Plan — TCK-20260719-STATS-PHASE-OUTLIERS-EXPOSE

## Summary

`compute_retro_metrics()` already computes `phase_status_distribution` and `outliers` and the CLI
already renders both; the only gap is the dashboard's typed API boundary
(`src/api/agent_ops_dashboard/models.py` / `ingest.py`) and the Stats tab frontend
(`dashboard-frontend/src/api.ts` / `StatsView.tsx`), which silently drop both keys today. This plan
adds two new Pydantic model groups and wires them through `get_agent_monitoring_stats()` via the
existing explicit-per-field-typed-submodel pattern (no `**metrics` passthrough), mirrors the exact
same shapes into the frontend TS interface as required (non-optional) fields, renders
`phase_status_distribution` as a table cloned from the existing "Top agents by call volume" table
and `outliers` as two separate sub-tables cloned from the existing "Slow runs" table (mirroring the
CLI's own two `###` sub-sections), wires `GlossaryTooltip` onto the cells/headers that already have
a registry category (`ok`/`failed`/`blocked`/`skipped` headers, `tier` and `agent` cell values) and
leaves ones that don't (`phase`, `median`, `ratio`, `duration_s`, `seq`, `cost_proxy_score`)
unwrapped, updates the two docs, and adds one new parity ledger entry. No change to
`compute_retro_metrics()` or `generate()` in `generate_retro.py` at any point.

**Decisions on the three open questions (made now, not deferred):**
1. **Rendering shape**: table for Phase Status Distribution (row-shaped data, same convention as
   the existing Top Agents / Slow Runs tables — confirmed by investigation's "Prior Work" section:
   `BarChart`/`GroupedBarChart` are reserved for single-numeric-value-per-label distributions, not
   row-shaped data). **Two separate sub-tables** for Outliers (one for `duration_s`, one for
   `cost_proxy_score`), mirroring the CLI's own two `###` sub-sections exactly — this is also what
   the ticket's own Scope section already specifies, not actually ambiguous.
2. **TS field optionality**: **required** (non-optional) on the `AgentMonitoringStats` TS
   interface — matches every other field in that interface, and the backend always returns these
   keys (empty dict/lists, never absent) per the empty-state ACs, so `?` would misrepresent the
   contract.
3. **Parity ledger entries**: **one** new entry, `INFRA-286` (confirmed next available ID — tail of
   `docs/parity_ledger/infrastructure.yaml` currently ends at `INFRA-285`), covering both
   `phase_status_distribution` and `outliers` dashboard-exposure together. Rationale: both
   behaviors are exposed by the same ticket, the same commit, the same two files, and the same test
   additions — splitting into two entries would fragment one atomic change into artificial halves
   with duplicated `v2_evidence`/`test_path` text. INFRA-283 and INFRA-284 are separate entries
   because they were separate tickets computing different data; this ticket's job is singular
   ("expose both already-computed fields through the typed boundary"), so one entry fits.

## Steps

### Step 1 — Backend: add Pydantic models for both new fields
**Files:** `src/api/agent_ops_dashboard/models.py`

**Change:** Immediately after the existing `SlowRunEntry` class (currently ending at line 161,
just before `class AgentMonitoringStats(BaseModel):`), add:

```python
class DurationOutlierEntry(BaseModel):
    run_id: str
    tier: str
    duration_s: int
    median: float
    ratio: float


class CostProxyOutlierEntry(BaseModel):
    run_id: str
    seq: Optional[int] = None
    phase: str
    agent: str
    cost_proxy_score: float
    median: float
    ratio: float


class OutlierStats(BaseModel):
    duration_s: List[DurationOutlierEntry]
    cost_proxy_score: List[CostProxyOutlierEntry]
```

`seq` **must** be `Optional[int] = None` — `generate_retro.py:467` builds this field via
`item.get("seq")` with no fallback, so it is legitimately `None` for legacy events; a required
`int` field raises a `ValidationError` the first time this hits real corpus data (confirmed
present: INFRA-284's own live-corpus run found 82 cost-proxy outliers).

Then add two fields to `AgentMonitoringStats` (currently lines 164–176), inserted after
`agent_status_distribution: Dict[str, Dict[str, int]]` and after `slow_runs: List[SlowRunEntry]`
respectively, to keep the field order matching `compute_retro_metrics()`'s own return-dict key
order (`agent_status_distribution` → `phase_status_distribution` → ... → `slow_runs` → `outliers`):

```python
    agent_status_distribution: Dict[str, Dict[str, int]]
    phase_status_distribution: Dict[str, Dict[str, int]]
    ...
    slow_runs: List[SlowRunEntry]
    outliers: OutlierStats
```

`phase_status_distribution` reuses the bare `Dict[str, Dict[str, int]]` type (no new submodel) —
its inner dict's key set is not guaranteed to be exactly `ok`/`failed`/`blocked`/`skipped` (raw
`Counter`-derived dict, any status string that appears in `events.jsonl` becomes a key); a fixed
submodel would raise `ValidationError` on any future/unexpected status string, unlike the open
`Dict[str, int]` shape `agent_status_distribution` already uses successfully.

**Do NOT touch:** `RunSummaryStats`, `SlowRunEntry`, `agent_status_distribution`'s own type, or any
other existing model in this file. Do not add a `PhaseStatusEntry` fixed-field submodel.

**Verify:** No standalone test for this step alone (models with no constructors called yet); it is
verified transitively by Step 3's tests, which import and instantiate these classes directly. A
quick `python3 -c "from src.api.agent_ops_dashboard.models import OutlierStats, DurationOutlierEntry, CostProxyOutlierEntry"`
sanity-import is sufficient to confirm no syntax error before moving to Step 2.

---

### Step 2 — Backend: wire both fields into `get_agent_monitoring_stats()`
**Files:** `src/api/agent_ops_dashboard/ingest.py`

**Change:** In `DashboardCache.get_agent_monitoring_stats()`'s `AgentMonitoringStats(...)`
construction (currently lines 754–780), add two lines following the exact same
explicit-per-field-typed-construction pattern every other field already uses:

```python
                agent_status_distribution=metrics["agent_status_distribution"],
                phase_status_distribution=metrics["phase_status_distribution"],
```

(direct passthrough — no submodel wrapping needed, identical treatment to
`agent_status_distribution`'s own existing line, since the field type is the same bare dict), and:

```python
                slow_runs=[SlowRunEntry(**r) for r in metrics["slow_runs"]],
                outliers=OutlierStats(
                    duration_s=[DurationOutlierEntry(**d) for d in metrics["outliers"]["duration_s"]],
                    cost_proxy_score=[
                        CostProxyOutlierEntry(**d) for d in metrics["outliers"]["cost_proxy_score"]
                    ],
                ),
```

Add `OutlierStats`, `DurationOutlierEntry`, `CostProxyOutlierEntry` to this file's existing
`from .models import (...)` import block.

**Do NOT touch:** `compute_retro_metrics` import (must stay an import, never a redefinition — this
is what `test_stats_endpoint_uses_real_compute_retro_metrics_not_reimplemented` guards). Do not
sort, re-round, or otherwise reprocess `metrics["outliers"]["duration_s"]` /
`["cost_proxy_score"]` before wrapping — `generate_retro.py` already sorts by ratio descending and
rounds `median`/`ratio` to 1 decimal; list comprehension order must be preserved exactly (no
`sorted(...)` call). Do not touch the `gate_failure_breakdown` None-key sanitization block
immediately above this construction — unrelated, already correct.

**Verify:** `python3 -m pytest tests/tools/test_agent_ops_dashboard_stats.py -q` (existing 8 tests
must still pass; new tests added in Step 3 will exercise the new fields specifically).

---

### Step 3 — Backend: add the 4 new tests
**Files:** `tests/tools/test_agent_ops_dashboard_stats.py`

**Change:** Add, mirroring `test_stats_endpoint_returns_typed_shape_for_all_time`'s fixture/assert
pattern (`_init_repo_skeleton`, `_write_runs`, `_write_events`, `_BASE_RUN`):

1. `test_stats_endpoint_includes_phase_status_distribution` — asserts
   `stats.phase_status_distribution == compute_retro_metrics(runs, events, tickets_root=...)["phase_status_distribution"]`
   for the same fixture input (import `compute_retro_metrics` directly in the test to compute the
   expected value, proving pass-through with no reshaping).
2. `test_stats_endpoint_includes_outliers_duration_and_cost_proxy` — fixture with ≥3 same-tier runs
   where one `duration_s` is >3x the tier median, and ≥3 same-phase events where one
   `cost_proxy_score` is >3x the phase median (mirror
   `test_duration_outlier_flagged_relative_to_tier_median_not_global`'s fixture shape from
   `test_generate_retro.py`). Asserts `stats.outliers.duration_s` and
   `stats.outliers.cost_proxy_score` contain the expected entries with correct field values.
3. `test_stats_endpoint_outliers_seq_field_tolerates_none` — a cost-proxy-outlier-triggering event
   with no `seq` key. Must not raise `ValidationError`; asserts the resulting entry's
   `seq is None`.
4. `test_stats_endpoint_zero_outliers_returns_empty_lists_not_missing_keys` — empty/no-events
   fixture. Asserts `stats.outliers.duration_s == []`, `stats.outliers.cost_proxy_score == []`, and
   `stats.phase_status_distribution == {}` (present and empty, never absent — the field access
   itself must not raise `AttributeError`/`KeyError`).

**Do NOT touch:** `test_stats_endpoint_uses_real_compute_retro_metrics_not_reimplemented` (existing
source-text guard) — must be re-run to confirm it still passes unmodified, not edited.

**Verify:**
```
python3 -m pytest tests/tools/test_agent_ops_dashboard_stats.py tests/tools/test_generate_retro.py -q
```
All tests (existing 8 + these 4 new + `test_generate_retro.py`'s full suite) pass.

---

### Step 4 — Frontend: extend the TS `AgentMonitoringStats` interface
**Files:** `dashboard-frontend/src/api.ts`

**Change:** Add, near the existing `SlowRunEntry` interface (currently lines 185–189):

```typescript
export interface DurationOutlierEntry {
  run_id: string
  tier: string
  duration_s: number
  median: number
  ratio: number
}

export interface CostProxyOutlierEntry {
  run_id: string
  seq: number | null
  phase: string
  agent: string
  cost_proxy_score: number
  median: number
  ratio: number
}

export interface OutlierStats {
  duration_s: DurationOutlierEntry[]
  cost_proxy_score: CostProxyOutlierEntry[]
}
```

Then add two **required** (non-optional) fields to `AgentMonitoringStats` (currently lines
191–203), in the same field-order position as Step 1's Python model change:

```typescript
  agent_status_distribution: Record<string, Record<string, number>>
  phase_status_distribution: Record<string, Record<string, number>>
  ...
  slow_runs: SlowRunEntry[]
  outliers: OutlierStats
```

**Do NOT touch:** `fetchAgentMonitoringStats()` or any other function in this file — the fetch
function needs no change since it just JSON-decodes the response into this interface; TypeScript's
structural typing means no runtime code changes here, only the type declaration.

**Verify:** `npx tsc --noEmit` (or the project's existing frontend typecheck command) fails at this
point for every call site that constructs an `AgentMonitoringStats` object without the two new
fields — this is expected; Step 7 fixes the one such call site (`makeAgentStats()` in the test
file). No standalone runtime test for a type-only change.

---

### Step 5 — Frontend: render Phase Status Distribution table
**Files:** `dashboard-frontend/src/views/StatsView.tsx`

**Change:** Add a `phaseStatusRows()` helper function (mirroring `topAgentRows()`, lines 54–67)
directly below it:

```typescript
interface PhaseStatusRow {
  phase: string
  total: number
  ok: number
  failed: number
  blocked: number
  skipped: number
}

function phaseStatusRows(stats: AgentMonitoringStats): PhaseStatusRow[] {
  return Object.entries(stats.phase_status_distribution).map(([phase, statuses]) => {
    const total = Object.values(statuses).reduce((sum, n) => sum + n, 0)
    return {
      phase,
      total,
      ok: statuses.ok ?? 0,
      failed: statuses.failed ?? 0,
      blocked: statuses.blocked ?? 0,
      skipped: statuses.skipped ?? 0,
    }
  })
}
```

(No `.sort()`/`.slice()` truncation — unlike `topAgentRows()`'s top-15 cap, phase count is small
and bounded by the number of distinct workflow phases; render all rows.)

Add a new `<table data-testid="phase-status-table">` block immediately after the existing "Top
agents by call volume" table block (after line 228, before the "Slow runs" block), same structural
pattern:
- Header row: `Phase` (unwrapped, generic label — mirrors "Agent" staying unwrapped in Top Agents),
  `Total` (unwrapped), then `Ok`/`Failed`/`Blocked`/`Skipped` each wrapped in
  `<GlossaryTooltip term="ok" glossary={glossary}>` etc. — **reuse the identical four
  `GlossaryTooltip` header cells already in the Top Agents table verbatim** (same registry terms,
  same `event-status` category).
- Body: one `<tr data-testid={`phase-status-row-${row.phase}`}>` per `phaseStatusRows(agentStats)`
  entry. The `phase` cell value is **plain text, not `GlossaryTooltip`-wrapped** — investigation
  confirmed no `phase` glossary category exists and no established precedent wraps generic
  non-enum values; wrapping it would silently no-op today but misrepresent intent.
- Empty state: when `Object.keys(agentStats.phase_status_distribution).length === 0`, render a
  single `<tr><td colSpan={6} className="...">No phase data</td></tr>` row — mirrors the existing
  "No slow runs" empty-state pattern at lines 252–258, not an empty table with only headers.

**Do NOT touch:** the existing "Top agents by call volume" table or `topAgentRows()` — this is a
new, separate table, not a merge into the agent-status table (explicit anti-drift hazard: merging
would lose the phase-vs-agent distinction that motivated `phase_status_distribution` in the first
place).

**Verify:** `'renders a Phase Status Distribution table with ok/failed/blocked/skipped columns'`
(new test, Step 7).

---

### Step 6 — Frontend: render Outliers as two sub-tables with graceful empty state
**Files:** `dashboard-frontend/src/views/StatsView.tsx`

**Change:** Add a new block after the Phase Status Distribution table (Step 5) and before/after the
existing "Slow runs" block (either position is fine structurally; place it after "Slow runs" to
match the CLI's own report ordering — Outliers is the CLI's last section). Structure:

```typescript
{(agentStats.outliers.duration_s.length > 0 || agentStats.outliers.cost_proxy_score.length > 0) ? (
  <>
    {agentStats.outliers.duration_s.length > 0 && (
      <div className="flex flex-col gap-2">
        <h3 className="...">Duration outliers (by tier)</h3>
        <table data-testid="duration-outliers-table">
          {/* headers: Run, Tier, Duration (s), Median, Ratio — only Tier's cell value wrapped */}
          {/* one <tr data-testid={`duration-outlier-row-${o.run_id}`}> per entry */}
        </table>
      </div>
    )}
    {agentStats.outliers.cost_proxy_score.length > 0 && (
      <div className="flex flex-col gap-2">
        <h3 className="...">Cost-proxy-score outliers (by phase)</h3>
        <table data-testid="cost-outliers-table">
          {/* headers: Run, Seq, Phase, Agent, Cost Proxy Score, Median, Ratio — only Agent's cell value wrapped */}
          {/* one <tr data-testid={`cost-outlier-row-${o.run_id}-${o.seq ?? 'none'}`}> per entry */}
        </table>
      </div>
    )}
  </>
) : (
  <div className="flex flex-col gap-2">
    <h3 className="...">Outliers</h3>
    <p className="text-text-secondary text-[11px]" data-testid="no-outliers-state">No outliers</p>
  </div>
)}
```

This exactly mirrors the CLI's own conditional structure (`generate_retro.py:690-720`): the overall
"Outliers" heading/content only appears when at least one list is non-empty, and *within* that,
each sub-table only renders when *its own* list is non-empty — never a broken table with headers
and zero data rows. When both lists are empty, render one single "No outliers" state, not two
empty tables.

Detail per table:
- `duration-outliers-table` row cells: `run_id` (plain), `tier` (wrapped —
  `<GlossaryTooltip term={o.tier} glossary={glossary}>{o.tier}</GlossaryTooltip>`, mirrors
  `run.final_status`'s wrap in Slow Runs), `duration_s` (plain, `tabular-nums`), `median` (plain,
  `tabular-nums`), `ratio` (plain, `tabular-nums`, render as `` `${o.ratio}x` `` matching the CLI's
  own `f"{ratio}x"` string format for readability — value formatting only, not a behavior change).
- `cost-outliers-table` row cells: `run_id` (plain), `seq` (plain, render `o.seq ?? '—'`), `phase`
  (plain — no glossary category, same reasoning as Step 5's phase cell), `agent` (wrapped —
  `<GlossaryTooltip term={o.agent} glossary={glossary}>{o.agent}</GlossaryTooltip>`, mirrors
  `row.agent`'s wrap in Top Agents), `cost_proxy_score` (plain, `tabular-nums`), `median` (plain,
  `tabular-nums`), `ratio` (plain, `tabular-nums`, `` `${o.ratio}x` ``).
- Column headers in both tables stay entirely unwrapped (`Run`, `Tier`, `Duration (s)`, `Median`,
  `Ratio`, `Seq`, `Phase`, `Agent`, `Cost Proxy Score`) — matches the existing convention that only
  enum-valued *cells*, never generic column-label *headers*, get `GlossaryTooltip` treatment
  outside the one exception (Top Agents' `ok`/`failed`/`blocked`/`skipped` headers, which are
  themselves literal enum terms, not generic labels — `Tier`/`Phase`/`Agent` as header words are
  generic labels here, not the terms themselves).

**Do NOT touch:** the existing "Slow runs" table/empty-state block — this is an additional,
separate block, not a merge (`slow_runs` and `outliers` are deliberately distinct signals per
`TCK-20260719-RETRO-OUTLIER-FLAGS`'s own Plan-phase decision, not to be re-litigated here). Do not
call `generate()` or any Markdown-rendering code from the frontend.

**Verify:** `'renders Duration and Cost-Proxy-Score outlier tables when outliers are present'`,
`'renders a graceful "no outliers" state when both outlier lists are empty, not a broken table'`,
`'wraps tier and agent values in outlier tables with GlossaryTooltip...'` (new tests, Step 7).

---

### Step 7 — Frontend: update fixture and add new tests
**Files:** `dashboard-frontend/src/test/StatsView.test.tsx`

**Change:**
1. Update `makeAgentStats()`'s default fixture object to include `phase_status_distribution: {}`
   and `outliers: { duration_s: [], cost_proxy_score: [] }` as defaults (every one of the file's 9
   dependent tests currently constructs its fixture through this function and will fail to
   typecheck without this, per Step 4's required-field change — expected, not a sign of drift).
2. Add: `'renders a Phase Status Distribution table with ok/failed/blocked/skipped columns'`,
   `'renders Duration and Cost-Proxy-Score outlier tables when outliers are present'`,
   `'renders a graceful "no outliers" state when both outlier lists are empty, not a broken
   table'`, `'wraps tier and agent values in outlier tables with GlossaryTooltip, matching existing
   Slow Runs / Top Agents cell-wrapping pattern'` — per `test_plan.md` items 7–10, each overriding
   `makeAgentStats()`'s defaults with test-specific `phase_status_distribution`/`outliers` values
   and asserting on the `data-testid`s defined in Steps 5–6.
3. Re-run (unmodified) `'renders real data from both endpoints once loaded'`,
   `'renders empty-state charts and tables for a zero-corpus/zero-runs response, without
   crashing'`, and `'never hardcodes a glossary description string in its own source — always
   sourced from the fetched glossary'` to confirm no regression and no hardcoded label string was
   introduced by Steps 5–6.

**Do NOT touch:** the `'never hardcodes a glossary description string...'` test's own assertion
logic — only let it re-run against the larger `STATS_VIEW_SOURCE` file; do not weaken it to
accommodate new code.

**Verify:**
```
npm test -- src/test/StatsView.test.tsx
```
from `dashboard-frontend/`. All (10 existing + 4 new, `makeAgentStats()` fixture update is not a
standalone test) tests pass.

---

### Step 8 — Docs: update both dashboard docs
**Files:** `docs/observability/agent_ops_dashboard_contract.md`,
`docs/guides/agent_ops_dashboard.md`

**Change:**
- `agent_ops_dashboard_contract.md`: in the `### Response models (models.py)` section's
  `AgentMonitoringStats` paragraph (currently lines 59–74), add
  `phase_status_distribution: Dict[str, Dict[str, int]]` and `outliers: OutlierStats` to the
  parenthetical field list, and add one sentence noting `OutlierStats` (`duration_s:
  List[DurationOutlierEntry]`, `cost_proxy_score: List[CostProxyOutlierEntry]`) as new submodels,
  with the same "field-for-field mirror of `compute_retro_metrics()`'s return dict" framing already
  used for the rest of the paragraph. Note the `seq: Optional[int]` nullability explicitly, same
  level of detail as the existing `gate_failure_breakdown` None-key-sanitization callout in the
  same paragraph.
- `agent_ops_dashboard.md`: in the `### Stats` section's "Agent Monitoring" bullet (currently lines
  118–122), append to the existing bullet's list: "...a table of slow runs, a table of per-phase
  status breakdown (Phase Status Distribution), and up to two outlier tables (duration-by-tier,
  cost-proxy-score-by-phase, each shown only when non-empty)." In the `## Hover tooltips` section's
  "Stats" bullet (currently line 153–154), append: "...the Phase Status Distribution table's
  `ok`/`failed`/`blocked`/`skipped` headers, and the Outliers tables' tier and agent cells."

**Do NOT touch:** any other section of either doc (Build/run/serve, Recent Activity Gantt, Replay
Timeline, Tickets view, Responsive Behavior, Known limitation, See also) — out of scope.

**Verify:** No automated test; manual read-through confirming the new prose accurately describes
Steps 1–7's actual field names/shapes (not aspirational). Per CLAUDE.md, run
`make knowledge-index-update` after these doc edits (docs under `docs/` were modified).

---

### Step 9 — Parity ledger: add one new entry
**Files:** `docs/parity_ledger/infrastructure.yaml`

**Change:** Append a new entry after the existing `INFRA-285` entry (currently ending the file), id
`INFRA-286` (confirmed next available — verify at Implement time the tail hasn't moved past 285
since this plan was written), `status: verified`, `priority: P2`, documenting: this ticket exposes
`phase_status_distribution` (INFRA-283's computation) and `outliers` (INFRA-284's computation,
explicitly deferred there) through `AgentMonitoringStats`/`get_agent_monitoring_stats()` and the
Stats tab, with zero change to `compute_retro_metrics()` or `generate()` (cross-reference, not
rewrite, of INFRA-283/284's own text). `v2_evidence` should cite `models.py`'s new
`DurationOutlierEntry`/`CostProxyOutlierEntry`/`OutlierStats` classes and the two new
`AgentMonitoringStats` fields, plus `ingest.py`'s wiring lines. `test_path` should list the 4 new
backend tests (Step 3) and the 4 new frontend tests (Step 7). `support_boundary` should note (same
pattern as INFRA-284's own entry): no change to `compute_retro_metrics()`/`generate()`, no on-disk
schema change, dashboard-exposure and rendering only.

**Do NOT touch:** INFRA-283's or INFRA-284's own entry text (investigation confirmed both remain
accurate as written — this ticket is documented as their own forward-reference via the new
INFRA-286 entry, not by editing their text). Do not create two separate entries (see Summary's
decision #3 above).

**Verify:** No test executes YAML content directly; validate the file still parses
(`python3 -c "import yaml; yaml.safe_load(open('docs/parity_ledger/infrastructure.yaml'))"`) and
conforms to `docs/parity_ledger/schema.json` if a validation script exists for it (check
`tools/` for a parity-ledger validator before Finalize).

---

### Step 10 — Live verification (runtime check, no file changes)
**Files:** none (verification only)

**Change:** N/A. Kill any stale `make dashboard-serve` process, start a fresh one, hit
`GET /api/stats/agent-monitoring` directly (e.g. `curl`) and confirm `phase_status_distribution`
and `outliers` keys are present with values numerically matching what
`python3 tools/agent-monitoring/generate_retro.py` prints for the same period (same underlying
numeric values — not byte-identical string formatting, since the CLI renders rounded/`x`-suffixed
Markdown strings while the API returns raw floats/ints, a pre-existing and accepted distinction
elsewhere in this dashboard per investigation's own "Live-verification AC" note). Then load the
Stats tab in a headless browser and visually confirm both new sections render, including hitting a
period with zero outliers to confirm the graceful empty state (not a broken table).

**Do NOT touch:** no code changes in this step; if verification surfaces a real bug, fix it in the
relevant Step 1–7 file and re-run that step's own test, not as ad hoc changes here.

**Verify:** Backs Acceptance Criteria 1 and 2 (live-verified, not just unit-tested) and Acceptance
Criterion 3 (zero-outlier graceful state) directly.

## Scope Guards

- Do not modify `compute_retro_metrics()` or `generate()` in
  `tools/agent-monitoring/generate_retro.py` — both are out of scope and protected by
  `test_stats_endpoint_uses_real_compute_retro_metrics_not_reimplemented` and
  `test_compute_retro_metrics_returns_all_documented_keys`.
- Do not add a `**metrics` or `**metrics["outliers"]` passthrough shortcut anywhere in `ingest.py`
  — every field is explicit per-field typed construction, no exceptions for the two new fields.
  Guarded by `test_stats_endpoint_never_passthrough_metrics_dict` if added per test_plan.md item 12.
- Do not sort, re-round, or otherwise reprocess the outlier lists in `ingest.py` — pass through
  `generate_retro.py`'s own already-sorted, already-rounded values unchanged, in the same list
  order.
- Do not merge `phase_status_distribution` into the existing `agent_status_distribution` table, and
  do not merge the `outliers` block into the existing `slow_runs` table — all four remain visually
  and structurally distinct sections/tables.
- Do not add new `docs/guidelines/glossary_registry.jsonl` entries — investigation confirmed none
  are needed; reuse the existing `event-status` (`ok`/`failed`/`blocked`/`skipped`), `tier`, and
  dynamically-merged `agent` categories only.
- Do not wrap `phase`, `median`, `ratio`, `duration_s`, `seq`, or `cost_proxy_score` values/headers
  with `GlossaryTooltip` — no registry category exists for any of them, and there is no existing
  precedent for wrapping generic non-enum columns.
- Do not touch real-time/polling behavior — Stats tab stays fetch-once-per-view-load.
- Do not touch `cost_proxy.py` or any weight recalibration logic — unrelated and explicitly out of
  scope per the ticket.
- Do not edit INFRA-283's or INFRA-284's existing parity ledger entry text — add a new INFRA-286
  entry instead.
- Do not touch any other `AgentMonitoringStats` field, any other `StatsView.tsx` section (Ticket
  Corpus, Gate failure/Reason code/Tier distribution charts, StatTiles), or any other file under
  `docs/observability/` or `docs/guides/` beyond the two named in Step 8.

## Dependency Map

- Step 1 (models.py) → Step 2 (ingest.py wiring) — Step 2 imports the classes Step 1 defines.
- Step 2 → Step 3 (backend tests) — tests exercise the wired construction.
- Step 4 (api.ts) → Step 5 and Step 6 (StatsView.tsx rendering) — rendering code references the new
  TS fields/types.
- Step 5, Step 6 → Step 7 (frontend tests) — tests assert on `data-testid`s Steps 5–6 introduce.
- Steps 1–7 → Step 10 (live verification) — needs real code in place to hit the running server.
- Step 8 (docs) and Step 9 (parity ledger) are independent of each other and of Step 10; both only
  need Steps 1–7's field names/shapes finalized, so they can happen any time after Step 6/Step 4
  respectively (whichever finalizes the shape they document).
- Backend steps (1–3) and frontend steps (4–7) are independent of each other and could be done in
  either order or in parallel — neither reads the other's output.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| `GET /api/stats/agent-monitoring` JSON includes both new keys, matching `compute_retro_metrics()` values, live-verified | Steps 1, 2, 10 | `test_stats_endpoint_includes_phase_status_distribution`, `test_stats_endpoint_includes_outliers_duration_and_cost_proxy` (Step 3); live curl check (Step 10) |
| Stats tab visually renders both new sections; live-verified via `make dashboard-serve` | Steps 4, 5, 6, 10 | `'renders a Phase Status Distribution table...'`, `'renders Duration and Cost-Proxy-Score outlier tables...'` (Step 7); headless browser check (Step 10) |
| A period with zero flagged outliers renders a graceful "no outliers" state | Step 6 | `'renders a graceful "no outliers" state when both outlier lists are empty, not a broken table'` (Step 7); `test_stats_endpoint_zero_outliers_returns_empty_lists_not_missing_keys` (Step 3) |
| All new/updated backend and frontend tests pass; full scoped suites still pass | Steps 3, 7 | Scoped pytest command + `npm test -- src/test/StatsView.test.tsx`, both listed in test_plan.md |
| `seq` nullability does not crash on legacy data (regression-prone path named in investigation) | Step 1 | `test_stats_endpoint_outliers_seq_field_tolerates_none` (Step 3) |
| Docs updated to describe both new fields/renderings | Step 8 | Manual read-through; no automated test |

## Anti-Drift Notes

- `CostProxyOutlierEntry.seq` must be `Optional[int] = None`, never a required `int` — this is the
  single highest-risk correctness detail in this ticket; a naive required field passes every
  fixture-based unit test that happens to include `seq` but breaks on first contact with real
  legacy corpus data lacking it.
- `phase_status_distribution` stays a bare `Dict[str, Dict[str, int]]`, never a fixed-field
  submodel — the inner dict's key set is open (any status string in `events.jsonl`), and a fixed
  submodel would silently start raising `ValidationError` the moment a new phase-status literal
  appears in future event data.
- The frontend's outlier rendering must reproduce the CLI's own conditional nesting exactly:
  outer "any outliers at all" check, then independent inner "this specific list is non-empty"
  checks per sub-table — not a single flat "both must be non-empty" or "either non-empty renders
  both tables" shortcut, which would produce a broken table with headers and zero rows for the
  currently-empty list (the common case: only 26 duration + 82 cost-proxy outliers across 677 runs
  / 3435 events all-time per INFRA-284's own live-corpus count, so most week-scoped queries will
  have zero, and partial-population states will be hit routinely, not rarely).
- `makeAgentStats()`'s fixture change in Step 7 will change every one of the 9 pre-existing
  dependent tests' constructed objects — this is expected, required work to keep the file
  typechecking, not evidence of scope creep or an unrelated regression.
- Never call `generate()` or assert against Markdown string output from any new test added in this
  ticket — that surface belongs entirely to `test_generate_retro.py` and stays untouched.
- "Byte-for-byte-equivalent to the CLI" in Acceptance Criterion 1 means same underlying numeric
  values, not identical string formatting — the CLI prints rounded values with an `x` ratio suffix
  in a Markdown table cell; the API returns raw floats/ints in JSON. This distinction already exists
  elsewhere in this dashboard (e.g. `spend_proxy_by_phase.avg`) and is not a new inconsistency this
  ticket introduces.
