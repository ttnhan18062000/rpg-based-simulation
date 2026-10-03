# Investigation — TCK-20260822-DASHBOARD-DURATION-GAP-AWARE

## Real code surveyed
- `src/api/agent_ops_dashboard/models.py`: `SlowRunEntry` (L162-165), `DurationOutlierEntry`
  (L168-173) — neither declares `model_config = ConfigDict(extra="forbid")`, so Pydantic's
  default `extra="ignore"` applies.
- `src/api/agent_ops_dashboard/ingest.py` L857-892 (the real stats passthrough construction site,
  not the L349-383 `_build_run_summary`/`RunSummary` site the ticket also names — that's a
  *different*, dormant raw-passthrough field, see below): `SlowRunEntry(**r) for r in
  metrics["slow_runs"]` and `DurationOutlierEntry(**d) for d in
  metrics["outliers"]["duration_s"]`.
- `dashboard-frontend/src/api.ts` L185-196: `SlowRunEntry`/`DurationOutlierEntry` TS interfaces.
- `dashboard-frontend/src/views/StatsView.tsx` L348-377 (Slow runs `SearchableTable`), L379-413
  (Duration outliers `SearchableTable`) — `SearchableTableColumn<T>` (`components/
  SearchableTable.tsx`) requires `accessor: (row) => string | number` (sort/search key) plus an
  optional `render` display override.
- `tests/tools/test_agent_ops_dashboard_stats.py`: 17 tests, all currently pass against the
  sibling ticket's already-shipped additive shape change (empirically confirmed — Pydantic
  silently drops the new fields today since no model forbids extras).

## Correction to this ticket's own text
This ticket's Request Summary claims `SlowRunEntry(**r)`-style unpacking "breaks outright" once
the sibling ticket ships new keys. **Empirically false**, verified directly: Pydantic's default
`extra="ignore"` (neither model sets `extra="forbid"`) silently drops unrecognized kwargs rather
than raising `ValidationError`. `tests/tools/test_agent_ops_dashboard_stats.py` (17/17) already
passed against the sibling ticket's shipped shape before this ticket began. This does not change
this ticket's own scope (the fields should still be surfaced, not silently dropped) — it changes
the *severity framing* from "fixes an outright break" to "surfaces data that was being silently
discarded." Recorded here rather than carried forward silently, per this session's own working
discipline.

## RunSummary.duration_s (the OTHER site, L349-383)
Confirmed genuinely dormant and unrendered by any frontend site (no `run_summary.duration_s`
reference found in `StatsView.tsx` or any other `.tsx` file) — per the ticket's own scope, flagged
in a comment only, not touched.

## Plan
1. `models.py`: add `active_duration_s: Optional[float] = None` and `idle_gap_s: Optional[float]
   = None` to both `SlowRunEntry` and `DurationOutlierEntry`.
2. `ingest.py`: no change needed at the construction site itself — `SlowRunEntry(**r)`/
   `DurationOutlierEntry(**d)` already forward whatever keys `r`/`d` contain; once the Pydantic
   models declare the new fields, they're captured automatically. Add one comment at
   `_build_run_summary` (L349) flagging `RunSummary.duration_s` as the dormant second
   passthrough, per ticket scope bullet 6.
3. `api.ts`: add `active_duration_s: number | null` and `idle_gap_s: number | null` to both TS
   interfaces.
4. `StatsView.tsx`: add "Active" and "Idle" columns to both tables, rendered in minutes with a
   "—" placeholder for null, mirroring the Python-side rendering style from the sibling ticket.
5. Tests: extend `test_agent_ops_dashboard_stats.py` (new fields present, backward-compatible
   default None) and `StatsView.test.tsx` (new columns render).
6. Parity ledger: update `INFRA-392` (sibling ticket's entry) — no, that entry is about
   duration_utils.py itself, not the dashboard; this ticket gets its own new entry per its own
   Related Docs pointer to `docs/parity_ledger/infrastructure.yaml` (settled during Plan, per the
   ticket's own explicitly-flagged open question).
