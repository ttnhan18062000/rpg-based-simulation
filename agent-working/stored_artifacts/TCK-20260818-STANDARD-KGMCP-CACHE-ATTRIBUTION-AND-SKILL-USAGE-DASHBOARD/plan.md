---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260818-STANDARD-KGMCP-CACHE-ATTRIBUTION-AND-SKILL-USAGE-DASHBOARD
artifact_type: plan
tags: [observability, testing, bug]
---

# Implementation Plan — TCK-20260818-STANDARD-KGMCP-CACHE-ATTRIBUTION-AND-SKILL-USAGE-DASHBOARD

## Design Decisions

**DD1 — New table, not a schema rewrite.** `retrieval_cache_access_log` is additive and
append-only (`CREATE TABLE IF NOT EXISTS`, `migration_005_add_cache_access_log_table`, ordinal 5,
following the exact `migration_00N_*` convention). Never touches the existing 3 marker-only tables
or the L1/L2 tables' own columns — satisfies the ticket's Out-of-Scope guard against redesigning
the existing L1/L2 schema.

**DD2 — Attribution source.** Reuses `.claude/current_run`'s exact field set
(`run_id`/`seq`/`phase`/`agent`/`execution_id`/`provider`/`ticket_id`) via a new
`read_current_run_sidecar()` in `tools/retrieval_cache.py`, mirroring
`post_tool_hook.py:46-63`'s read pattern line-for-line (no shared function existed to import).

**DD3 — Sidecar staleness (Scope item 6).** Full fix (making the sidecar itself
self-invalidating, e.g. on workflow completion) is out of this ticket's scope — it would require
changing the hook/orchestrator layer that writes `.claude/current_run`, a different, riskier
surface than this ticket's own `retrieval_cache.py`/`generate_retro.py`/dashboard changes.
Partial, real, scoped mitigation implemented instead: `_sidecar_run_is_stale()` checks whether the
sidecar's effective ticket id (`ticket_id`, falling back to `run_id` when it looks like a ticket id)
resolves to a file under `tickets/done/` but NOT `tickets/inprogress/` — the exact reproduced
failure mode. Every access-log row carries a `sidecar_stale` flag; a row is never dropped or
silently trusted, just honestly flagged. Disclosed as a partial mitigation, not a full fix, in the
ticket's Completion Summary.

**DD4 — Event types.** `hit`/`write`/`invalidate` are all schema-valid, but only `hit`/`write` are
ever emitted — neither cache level has a distinct invalidation call site today (eviction happens
implicitly via `INSERT OR REPLACE`). `invalidate` is reserved for a future caller, not fabricated.

**DD5 — `compute_retro_metrics()` signature.** Investigated per Scope item 3: does Skill Usage
belong as an optional `tools` param on `compute_retro_metrics()`, or computed separately inside
`ingest.py`? Chose the `tools=None`/`kgmcp_access_log=None` optional-param route on
`compute_retro_metrics()` itself, because `TCK-20260718-RETRO-STATS-REFACTOR`'s own explicit
property ("CLI Markdown report and JSON API must stay logically consistent") is only actually
guaranteed if both consumers call the *same* function — computing `skill_usage` a second,
independent way inside `ingest.py` would let the two drift silently. Both new params default to
`None` and are computed over `[]` when omitted (never a KeyError, never an omitted dict key) —
fully additive, zero behavior change for any pre-existing caller that doesn't pass them.
`generate()` was updated to read `su`/`kce` from `compute_retro_metrics()`'s own return dict
instead of a second, separate `build_skill_usage_section()` call — proven by a monkeypatch-based
regression test (`test_generate_uses_compute_retro_metrics_skill_usage_not_a_second_call`).

**DD6 — KGMCP retro section gating.** Unlike most gated sections in `generate()`, "## KGMCP Cache
Efficiency" always renders (mirrors "## Parity Index Read-Path Usage"'s own "0 today is itself the
reportable finding" precedent) — a real, disclosed design requirement surfaced mid-task: a period
with real search/graphify activity but zero cache events must never silently disappear from the
report.

**DD7 (mid-task reinforcement) — Efficiency verdict, not just raw counts.** Added after the
orchestrator's direct framing correction: `compute_kgmcp_cache_efficiency_metrics()` now computes
four distinct signals (reuse rate, repeated-refetch detection within a 300s window, dead-write
detection — a write never hit before the next write to the same row or the end of the observed
log, and coverage vs. real `tools.jsonl` search/graphify call volume) and folds them into a
rule-based `verdict`/`verdict_explanation` pair (`_kgmcp_verdict()`) — every clause a literal
readout of an already-computed number, never a fabricated score. Both the CLI Markdown report and
the dashboard render this verdict as a first-class, glanceable callout.

**DD8 — KGMCP period scoping.** `kgmcp_access_log` is always the FULL, unfiltered corpus in both
`generate()`'s CLI callers and `ingest.py`'s API caller, regardless of `--days`/`--week`/`--all` or
the API's own period params — mirrors the pre-existing "## Retrieval Quality" section's own
established "visible under `--all` only, in spirit" precedent (these rows are sidecar-attributed
at call time, not tied to any `runs.jsonl` timestamp a period filter could meaningfully slice).

## Scope Guards

- No change to the 3 legacy marker-only tables, the L1/L2 table schemas, or any existing
  `check_*_cache`/`write_*_cache` call signature.
- No change to `retrieval_provider_result_cache_rows`/`retrieval_context_packet_cache_rows`'s own
  `hit_count`/`last_hit_at`/`last_validated_at` semantics (still wiped on `INSERT OR REPLACE`,
  unchanged) — the new log is a parallel, independent history, not a fix to that pre-existing
  behavior (explicitly Out of Scope per the ticket body).
- **Deferred, disclosed (not silently dropped):** a full `docs/parity_ledger/infrastructure.yaml`
  entry in the exhaustive format prior `retrieval_cache.py` schema-migration tickets used. This
  ticket's own "Related Docs" list names `docs/observability/agent_ops_dashboard_contract.md`,
  `docs/guides/agent_ops_dashboard.md`, and
  `docs/observability/retrieval_retention_redaction_policy.md` — all three were updated;
  `docs/engine/contracts/knowledge_gateway_mcp/cache_migration_plan.md` was additionally updated
  (not originally listed, but the authoritative migration registry this ticket's own migration
  must appear in). The parity-ledger entry itself is deferred given the ticket's already-large
  real scope (schema + instrumentation + retro + 2 API fields + 2 frontend sections, all
  implemented and tested) — disclosed explicitly, not claimed done.

## Acceptance-Criteria Map

| AC | Implementation |
|---|---|
| New cache-access-log schema exists and is populated by real hit/write events | `migration_005_add_cache_access_log_table`, `log_cache_access()`, instrumented at all 4 real call sites; verified via a real `write_provider_result_cache()`/`record_provider_result_cache_hit()` round-trip with a real sidecar file |
| `generate_retro.py` reports KGMCP cache efficiency against real accumulated data | `compute_kgmcp_cache_efficiency_metrics()` + `## KGMCP Cache Efficiency` in `generate()`; run against the real 1149-run corpus, showing a real `NOT IN USE` verdict (0 hits/writes vs. 2605 real search calls) |
| `AgentMonitoringStats` includes Skill Usage + KGMCP; API returns real, non-empty values | `SkillUsageSection`/`KgmcpCacheEfficiencyStats` models; verified via a real HTTP request to a live `uvicorn` instance of `main:app` |
| `StatsView.tsx` renders both new sections | Two new subsections added, matching existing `StatTile`/`BarChart`/table conventions; 4 new Vitest tests, all passing against real component render |
| Sidecar-staleness handled or disclosed | `_sidecar_run_is_stale()`/`sidecar_stale` column — partial, scoped mitigation (DD3), explicitly disclosed as not a full fix |
| No regression in existing dashboard/retro functionality | Full existing test suites (`test_retrieval_cache.py`, `test_generate_retro.py`, `test_agent_ops_dashboard_*.py`, frontend Vitest) re-run and passing; the one intentional Markdown-output diff (new section text) reflected in updated fixture, not hidden |
