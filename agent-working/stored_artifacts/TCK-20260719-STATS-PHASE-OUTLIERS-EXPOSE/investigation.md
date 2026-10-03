---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260719-STATS-PHASE-OUTLIERS-EXPOSE
artifact_type: investigation
tags: [dashboard, observability, agent-monitoring]
---

# Investigation — TCK-20260719-STATS-PHASE-OUTLIERS-EXPOSE

## Current Behavior

**`compute_retro_metrics()`** (`tools/agent-monitoring/generate_retro.py:256-505`) already computes
and returns both keys the ticket wants exposed:

- `phase_status_distribution` (built at `:363-377`, returned at `:492`): `Dict[str, Dict[str, int]]`
  — identical shape to the already-exposed `agent_status_distribution` (`:376`), keyed by
  `_normalize_phase(e)` instead of `_normalize_agent(e)`. Each inner dict is a raw `Counter`-derived
  `{status: count}` map where status is whatever literal string is in the event (`ok`/`failed`/
  `blocked`/`skipped` in practice, per `docs/guidelines/glossary_registry.jsonl`'s `event-status`
  category, but the dict is not restricted to those four keys — any status string that appears in
  events.jsonl will appear as a key).
- `outliers` (built at `:438-475`, returned at `:501-504`): a two-key dict —
  - `outliers["duration_s"]`: `List[Dict]`, each item exactly
    `{"run_id": str, "tier": str, "duration_s": int, "median": float, "ratio": float}` (`:443-452`).
  - `outliers["cost_proxy_score"]`: `List[Dict]`, each item exactly
    `{"run_id": str, "seq": int|None, "phase": str, "agent": str, "cost_proxy_score": float,
    "median": float, "ratio": float}` (`:464-474`). Note `seq` can be `None` (`item.get("seq")`,
    no fallback) — the new Pydantic model must declare this field `Optional[int]`, not `int`.

Both are already rendered in the CLI Markdown report: `## Phase Status Distribution`
(`generate()` `:624-638`, unconditional — prints `_No events recorded._` when empty, same as
`## Agent Status Distribution` immediately above it) and `## Outliers` (`:690-720`, conditionally
rendered only `if outliers["duration_s"] or outliers["cost_proxy_score"]`, with two sub-`###`
sections — `Duration outliers (by tier)` and `Cost-proxy-score outliers (by phase)` — each its own
table, only rendered if that specific list is non-empty).

**Dashboard side — confirmed gap, exactly as the ticket states.**
`AgentMonitoringStats` (`src/api/agent_ops_dashboard/models.py:164-176`) has no
`phase_status_distribution` or `outliers` field. `DashboardCache.get_agent_monitoring_stats()`
(`src/api/agent_ops_dashboard/ingest.py:700-780`) builds the response via explicit per-field typed
submodel construction (`:754-780`) and never reads `metrics["phase_status_distribution"]` or
`metrics["outliers"]` at all — both keys are silently dropped when `compute_retro_metrics()`'s
return dict crosses this typed boundary. This is the exact "not automatic" gap INFRA-283 and
INFRA-284 both explicitly flagged and deferred (see Parity Ledger Overlap below).

Frontend: `dashboard-frontend/src/api.ts`'s `AgentMonitoringStats` TS interface (`:191-203`) mirrors
`models.py` field-for-field and likewise has no `phase_status_distribution`/`outliers` fields.
`StatsView.tsx` renders `agent_status_distribution` as the "Top agents by call volume" `<table>`
(`:182-228`, using a `GlossaryTooltip`-wrapped `ok`/`failed`/`blocked`/`skipped` header row) and
`slow_runs` as its own `<table>` (`:230-261`, with an explicit "No slow runs" empty-state row at
`:252-258`) — these are the two patterns the ticket's Scope section says to mirror.

## Mechanics / Engine Constraints

None. This subsystem is explicitly outside the Mechanics Bible / Engine Contracts — the Agent Ops
Dashboard backend is "a standalone FastAPI app... It never touches `AuthoritativeState` or the tick
loop" (`docs/observability/agent_ops_dashboard_contract.md:13-17`). The one binding architectural
rule that does apply here (from that same contract doc, `models.py:1-9`'s own module docstring):
every route returns typed Pydantic models built by per-field explicit construction — "never a raw
dict... never `**metrics` passthrough." This ticket's whole job is to extend that existing pattern
by two fields, not to introduce a new one.

## Parity Ledger Overlap

- **INFRA-283** (`docs/parity_ledger/infrastructure.yaml:5223-5283`, status `verified`, priority
  `P2`) — introduced `phase_status_distribution` into `compute_retro_metrics()`. Its own
  `test_path` already lists `test_agent_ops_dashboard_stats.py` (8/8) as passing evidence that the
  new key "doesn't break the dashboard's typed API-boundary mapping" — but that entry's text never
  claims the key is *exposed*, only that adding it didn't crash the existing (unrelated) dashboard
  tests. **No update needed to INFRA-283's own text** — it's still accurate. A new entry (or an
  amendment noting a forward-reference) is the right home for "now exposed" evidence; see below.
- **INFRA-284** (`:5285-5353`, status `verified`, priority `P2`) — introduced `outliers`. Its text
  is explicit and unambiguous: *"Explicitly does NOT expose the new key to the Agent Ops Dashboard
  ... the new key is silently absent there until a separate, deliberate future ticket wires it
  through."* This ticket **is** that separate, deliberate future ticket. INFRA-284's own text
  should not be rewritten (it accurately describes what that ticket did), but a forward pointer or
  a new entry documenting the dashboard-exposure follow-through is expected.
- **INFRA-285** — unrelated (weight-sensitivity CLI promotion), no overlap; included in the ticket
  prompt's context-gathering list only because it's adjacent in the same batch, not because it
  needs updating.
- Neither INFRA-283 nor INFRA-284 is P0, so neither strictly *requires* a passing `test_path` as a
  blocking gate — but both already have real, passing `test_path`s, and this ticket should add a
  **new** parity ledger entry (next available `INFRA-3xx` id — check the tail of
  `infrastructure.yaml` at Plan/Implement time since more entries may have landed since this
  investigation) documenting the dashboard-exposure behavior change itself, with its own
  `test_path` pointing at the new/updated tests in `tests/tools/test_agent_ops_dashboard_stats.py`
  and `dashboard-frontend/src/test/StatsView.test.tsx`.

## Prior Work

- **TCK-20260719-PHASE-AGENT-CASE-FOLD** (done) — added `phase_status_distribution` and the
  normalization helpers it depends on (`_normalize_phase`/`_normalize_agent`). Directly produces
  the exact shape this ticket must mirror in `models.py`.
- **TCK-20260719-RETRO-OUTLIER-FLAGS** (done, full ticket read above) — added `outliers`. Its own
  ticket body explicitly documents the two Plan-phase decisions already made (tier-scoped median
  for duration_s, kept `slow_runs` and `outliers` as two distinct unmerged signals) — this ticket
  should **not** re-litigate either decision, just render both list shapes as-is.
- **TCK-20260718-AGENTOPS-STATS-API** (done, `stored_artifacts/TCK-20260718-AGENTOPS-STATS-API/`) —
  established the explicit-per-field-typed-submodel construction pattern in `ingest.py` this ticket
  must follow exactly (no `**metrics` passthrough shortcut, even though it would technically work).
- **TCK-20260718-STATS-TAB-FRONTEND** (done, `stored_artifacts/TCK-20260718-STATS-TAB-FRONTEND/`) —
  established the table-vs-chart rendering conventions in `StatsView.tsx` (`BarChart`/
  `GroupedBarChart` for distributions with a natural single numeric value per label; a plain
  `<table>` for row-shaped data like agent call volume and slow runs). Both new sections in this
  ticket are row-shaped (a per-phase 4-column breakdown; a list of outlier records with 5-7 columns
  each) — table is the consistent choice per this established convention, confirming the ticket's
  own "recommended table"/"recommended two tables" open questions.
- **TCK-20260718-GLOSSARY-TOOLTIPS-EPIC / TCK-20260719-AGENT-ROLE-GLOSSARY** (done) — established
  `GlossaryTooltip` (`dashboard-frontend/src/components/GlossaryTooltip.tsx`): wraps a label,
  degrades to unwrapped `children` when `glossary[term]` has no entry — never blocks rendering.
  Column *headers* only get wrapped when the header text itself is a literal registry term (e.g.
  `ok`/`failed`/`blocked`/`skipped` in the existing Top Agents table); generic column labels like
  "Agent", "Total", "Duration (s)" are never wrapped. Cell *values* get wrapped when the value
  itself might be a registry term (e.g. `row.agent`, `run.final_status`).
- **`docs/guidelines/glossary_registry.jsonl`** (35 entries, read in full) — categories present:
  `ticket-status`, `tier`, `priority`, `type`, `run-status`, `reason-code`, `event-status`. No
  category exists for generic column concepts (there is no "duration outlier"/"cost outlier"/
  "phase status" entry anywhere, and none is needed — see Risks below).

## Risks and Open Questions

- **`seq` nullability in `CostProxyOutlierEntry`**: `outliers_cost_proxy_score` items use
  `item.get("seq")` with no fallback (`generate_retro.py:467`) — this field can legitimately be
  `None` for legacy events lacking a `seq`. The new Pydantic model **must** declare
  `seq: Optional[int] = None`, not `int` — a naive `int` field would raise a `ValidationError` on
  real legacy data the first time this endpoint is hit against the live corpus (INFRA-284's own
  evidence already found real outliers in the live corpus — 26 duration + 82 cost-proxy — so this
  is not a hypothetical edge case, it will be exercised on first live use).
- **`phase_status_distribution` inner-dict key openness**: unlike `outliers`, this dict's inner
  value is a raw `dict(Counter)` with no guaranteed key set — the ticket's suggested
  `Dict[str, Dict[str, int]]` (reusing `agent_status_distribution`'s exact type, per the ticket's
  own instruction) is correct and matches the existing pattern exactly; flagging this only so
  Implement doesn't over-engineer a `PhaseStatusEntry` submodel with fixed `ok`/`failed`/`blocked`/
  `skipped` fields (a status string outside that set, e.g. a future workflow phase status, would
  silently fail Pydantic validation with a fixed-field model but pass fine with `Dict[str, int]`).
- **Live-verification AC** ("byte-for-byte-equivalent to what the CLI retro report already renders
  for the same period", "live-verified via headless browser against `make dashboard-serve`") is not
  something Investigation can pre-verify — it's an Implement/Test-phase runtime check. Flagging
  that the CLI report's Markdown values are strings with specific rounding (`round(x, 1)`,
  `f"{ratio}x"`) while the JSON API values will be raw floats — "byte-for-byte-equivalent" should be
  read as "same underlying numeric values," not "same string formatting," since the two surfaces
  (Markdown table cell vs. JSON API field) have never been required to match formatting elsewhere
  in this dashboard (e.g. `avg_duration_min` is an int in both, but `spend_proxy_by_phase.avg` is
  already a rendered-differently float in each). No blocking ambiguity — just a formatting-vs-value
  distinction to keep in mind when writing the "byte-for-byte" AC's actual test.
- **Glossary registry gap — resolved, not a real gap**: the ticket asks Investigation/Plan to check
  whether new glossary terms are needed. Finding: **no new registry entries are needed.** Phase
  Status Distribution's column headers are literally `ok`/`failed`/`blocked`/`skipped` — already
  registered under `event-status` and already the exact pattern the Top Agents table uses today, so
  it mirrors that table's `GlossaryTooltip` wiring with zero new registry entries. The Outliers
  tables' `tier` values (`hotfix`/`standard`/`epic`) are already registered under the `tier`
  category — wrapping `o.tier` with `GlossaryTooltip` the same way `run.final_status` is wrapped in
  the existing Slow Runs table is possible and free (no new registry entries). The Outliers tables'
  `agent` values are already covered by the dynamically-merged `agent` category (from
  `.claude/agents/*.md` descriptions) — wrapping `o.agent` the same way `row.agent` is wrapped in
  the Top Agents table is also possible and free. There is no `phase` glossary category and no
  established pattern of wrapping generic non-enum column headers (e.g. "Duration (s)" in Slow Runs
  is never wrapped) — so `median`/`ratio`/`duration_s`/`cost_proxy_score`/`seq`/`phase` column
  headers should stay plain, consistent with existing precedent, not because of an oversight.

## Anti-Drift Hazards

- **Do not touch `compute_retro_metrics()` or `generate()`** in `generate_retro.py` — both are
  explicitly out of scope and must stay byte-identical (protected by
  `test_stats_endpoint_uses_real_compute_retro_metrics_not_reimplemented`, which source-greps
  `ingest.py` to confirm it imports rather than redefines the function).
- **Do not add a `**metrics` passthrough shortcut** anywhere in `get_agent_monitoring_stats()` —
  every existing field is explicit per-field typed construction; adding the two new fields must
  follow the exact same pattern (`phase_status_distribution=metrics["phase_status_distribution"]`
  directly, since it needs no submodel wrapping — same as `agent_status_distribution`'s existing
  line; `outliers=OutlierStats(...)` built from the two sub-lists, same as `summary_quality`'s
  pattern of one nested submodel).
- **Do not sort/reformat/re-round the outlier lists** in `ingest.py` — `generate_retro.py` already
  sorts `outliers["duration_s"]`/`outliers["cost_proxy_score"]` by ratio descending
  (`_flag_outliers:252`) and rounds `median`/`ratio` to 1 decimal (`:449,472`); the API boundary
  should pass these through unchanged, not recompute or re-sort them (a second sort could silently
  diverge from the CLI's own order if the two ever use different tie-breaking).
- **Do not merge `phase_status_distribution` into the existing `agent_status_distribution` table**
  — the ticket explicitly wants two separate renderings (mirroring the CLI's own two separate `##`
  sections), and merging would silently lose the phase-vs-agent distinction that motivated
  INFRA-283 in the first place (Review's true failure rate).
- **Do not silently drop the `## Outliers` section's conditional-empty framing** — the CLI only
  renders `## Outliers` when at least one list is non-empty, and even then only renders each
  sub-table when *that* specific list is non-empty (duration/cost-proxy are independent). The
  frontend's "graceful no-outliers state" AC should mirror this: an empty overall state, not two
  empty tables with header rows and no data (matches the existing "No slow runs" single-row
  precedent at `StatsView.tsx:252-258`, not a broken empty `<table>`).
- **`StatsView.test.tsx`'s `makeAgentStats()` fixture is stale by construction** — it currently has
  no `phase_status_distribution`/`outliers` keys. If the new TS fields are added as required
  (non-optional) on `AgentMonitoringStats`, every existing call site of `makeAgentStats()` (used in
  9 of the file's 10 tests) will fail to typecheck until the fixture's default object is updated —
  this is expected, necessary work, not a sign that something else is wrong.
