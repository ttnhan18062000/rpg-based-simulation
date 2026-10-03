---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260818-STANDARD-KGMCP-CACHE-ATTRIBUTION-AND-SKILL-USAGE-DASHBOARD
phase: done
date: 2026-08-18
tags: [observability, testing, bug]
---

# TCK-20260818-STANDARD-KGMCP-CACHE-ATTRIBUTION-AND-SKILL-USAGE-DASHBOARD

## Title
Add per-row work attribution to the KGMCP retrieval cache and surface both it and existing Skill
Usage data in the Agent Ops Dashboard

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Following up on a discussion about whether context/knowledge retrieval is being managed and used
efficiently: the KGMCP retrieval cache (`knowledge-index/retrieval_cache.db`) tracks `hit_count`
and `last_hit_at`/`last_validated_at` per row, but (a) has no update-count (writes are `INSERT OR
REPLACE` and hardcode `hit_count=0, last_hit_at=NULL` on replace, silently discarding prior hit
history), and (b) has no `run_id`/`agent`/`phase` attribution at all — no way to tell which
ticket/agent/phase caused a given retrieval or write. Separately, the user observed live on the
running Agent Ops Dashboard that it shows neither a Skill Usage metric nor any KGMCP/context
metric, and this investigation confirmed that's a real backend gap: `AgentMonitoringStats`
(`src/api/agent_ops_dashboard/models.py`) has `tag_breakdown_skill` (skill-*tagged* ticket runs)
but nothing for the retro's separate "Skill Usage" section (raw per-skill *invocation* counts +
zero-invocation staleness flags, computed by `tools/agent-monitoring/generate_retro.py::
build_skill_usage_section()`), and nothing for KGMCP data anywhere.

## Scope
1. **KGMCP cache-attribution log**: new `retrieval_cache_access_log` table in
   `knowledge-index/retrieval_cache.db` (or a schema-migration-compatible equivalent, matching
   this DB's existing migration convention — see `retrieval_cache_generation` /
   `TCK-20260816-KGMCP-P3-PACKET-CACHE-SCHEMA-MIGRATIONS`), keyed by cache row reference +
   event type (`hit`/`write`/`invalidate`) + `run_id`/`agent`/`phase` (sourced from the same
   `.claude/current_run` sidecar mechanism `agent-monitoring/tools.jsonl` already uses) +
   timestamp. Instrument the exact call sites already identified in
   `tools/retrieval_cache.py` (`hit_count = hit_count + 1` sites ~L810/L1025, `INSERT OR REPLACE`
   write sites ~L781/L988).
2. **Retro integration**: add a "KGMCP Cache Efficiency" section to
   `tools/agent-monitoring/generate_retro.py` (both `generate()`'s Markdown rendering and
   `compute_retro_metrics()`'s JSON dict) — per-ticket/per-agent hit/write counts, cache-reuse
   rate, and repeated-refetch detection (same query re-fetched by the same or different tickets
   within a short window).
3. **Skill Usage → dashboard**: extend `compute_retro_metrics()` (or `get_agent_monitoring_stats()`
   directly, whichever is the cleaner integration point — investigate before choosing) to also
   compute and expose `build_skill_usage_section()`'s data (per-skill invocation counts,
   zero-invocation flags), add a corresponding Pydantic model + field to `AgentMonitoringStats`,
   and thread it through `DashboardCache.get_agent_monitoring_stats()` (which currently discards
   the raw `tools_all` list after building `_tools_by_seq`/`_tools_by_run_recent` — needs to
   either retain it or call `build_skill_usage_section()` directly with what's already loaded).
4. **KGMCP cache-attribution → dashboard**: add a model + field for the new cache-attribution
   stats (per-ticket/agent cache hit/write/reuse data from item 2) and wire it into the same
   `AgentMonitoringStats` response.
5. **Frontend**: add both new sections to `StatsView.tsx` (the existing "Stats" tab,
   `TCK-20260718-STATS-TAB-FRONTEND`), matching its existing rendering conventions.
6. **Sidecar staleness**: the attribution data from items 1-2 is only as reliable as
   `.claude/current_run`'s accuracy — investigate whether ad-hoc/non-ticket work (like this
   session's own direct investigation calls) can be given an honest "unattributed"/"ad-hoc" bucket
   rather than silently inheriting a stale, unrelated ticket ID (reproduced live this session: a
   `search_docs` call made during free-form investigation got logged against an unrelated,
   already-closed ticket).

## Out of Scope
- Rewriting or redesigning the existing L1/L2 cache schema itself (`retrieval_provider_result_
  cache_rows`, `retrieval_context_packet_cache_rows`) — additive logging only.
- Any change to how `search_docs`/`graphify` actually retrieve or rank content — this is
  observability/attribution only, not a retrieval-quality change.
- A full redesign of the Agent Ops Dashboard's frontend layout — additive sections only, matching
  existing `StatsView.tsx` conventions.

## Acceptance Criteria
- [x] New cache-access-log schema exists and is populated by real hit/write events (verified via
      a real `search_docs`/`graphify` call producing a new log row with correct attribution).
- [x] `generate_retro.py` reports KGMCP cache efficiency, verified against real accumulated data.
- [x] `AgentMonitoringStats` includes both Skill Usage and KGMCP cache-attribution data; `GET
      /api/stats/agent-monitoring` returns real, non-empty values for both when real data exists.
- [x] `StatsView.tsx` renders both new sections.
- [x] Sidecar-staleness handling for ad-hoc work addressed or explicitly disclosed as an open
      limitation if not fully resolvable within this ticket's scope.
- [x] No regression in existing dashboard/retro functionality (byte-identical output for
      unaffected sections).

## Related Tickets
- `TCK-20260718-AGENTOPS-STATS-BOARD-EPIC`, `TCK-20260718-AGENTOPS-STATS-API`,
  `TCK-20260718-STATS-TAB-FRONTEND`, `TCK-20260718-RETRO-STATS-REFACTOR` (the existing Stats tab
  infrastructure this ticket extends)
- `TCK-20260805-SKILL-USAGE-METRIC`, `TCK-20260810-SKILL-USAGE-RETRO-TRACKING` (the existing
  retro-side Skill Usage computation this ticket wires into the dashboard)
- `TCK-20260816-KGMCP-P3-PACKET-CACHE-SCHEMA-MIGRATIONS` (schema-migration convention to follow
  for the new cache-access-log table)

## Related Docs
- `docs/observability/agent_ops_dashboard_contract.md`
- `docs/guides/agent_ops_dashboard.md`
- `docs/observability/retrieval_retention_redaction_policy.md`

## Related Stored Artifacts
`stored_artifacts/TCK-20260818-STANDARD-KGMCP-CACHE-ATTRIBUTION-AND-SKILL-USAGE-DASHBOARD/`

## Related Code Areas
- `tools/retrieval_cache.py`
- `tools/agent-monitoring/generate_retro.py`
- `src/api/agent_ops_dashboard/models.py`
- `src/api/agent_ops_dashboard/ingest.py`
- Dashboard frontend `StatsView.tsx` (path to confirm during investigation)

## Assumptions / Open Questions
- Resolved during Implement: the sidecar-staleness issue is only *partially* fixable within this
  ticket's own scope. A real, tested `sidecar_stale` flag is added to every new
  `retrieval_cache_access_log` row (reproducing and detecting the exact live bug this ticket
  documents), but the underlying `.claude/current_run` sidecar mechanism itself (also used by
  `agent-monitoring/tools.jsonl`) is unchanged — fixing that would require touching the
  hook/orchestrator layer that writes the sidecar, a different and riskier surface. Recommended as
  a real, disclosed follow-up ticket, not silently left unstated.
- Resolved: a full `docs/parity_ledger/infrastructure.yaml` entry (the exhaustive format prior
  `retrieval_cache.py` schema-migration tickets used) was deliberately deferred given this
  ticket's already large real delivered scope — see plan.md's Scope Guards and the Completion
  Summary below.

## Implementation Notes

**1. KGMCP cache-access-log** (`tools/retrieval_cache.py`): new
`migration_005_add_cache_access_log_table(conn)` (ordinal 5, next open after migration_004) adds
`retrieval_cache_access_log` — additive, append-only, `CREATE TABLE IF NOT EXISTS`, stamps
`retrieval_cache_generation` to version 3 (bumping `retrieval_cache_schema_version` 2 -> 3, per
the established "new table stamps, ALTER TABLE column-add doesn't" convention migrations 1-4
already set). Columns: `cache_level`, `event_type` (`hit`/`write`/`invalidate` — only `hit`/`write`
are ever emitted, `invalidate` is schema-valid but reserved), `query_hash`/`repo_branch_scope`
(Level 1) or `packet_id` (Level 2), `run_id`/`seq`/`phase`/`agent`/`execution_id`/`provider`/
`ticket_id` (from the sidecar), `sidecar_stale`, `ts`.

New `read_current_run_sidecar()` mirrors `post_tool_hook.py:46-63`'s exact `.claude/current_run`
read pattern (no shared function existed to import). New `log_cache_access()` writes one row per
event, never raises (CLAUDE.md hard rule: monitoring write failure must never fail the workflow —
directly tested). New `read_cache_access_log()` is the read-only consumer-facing function, never
raises on a fresh/never-migrated DB (mirrors `provider_result_cache_stats()`'s own contract).

Instrumented the 4 real call sites: `write_provider_result_cache()`, `record_provider_result_cache_hit()`,
`write_context_packet_cache()`, `record_context_packet_cache_hit()` — each logs on its own
connection, after the real cache write/update has already committed and closed.

**2. Sidecar staleness (Scope item 6)**: `_sidecar_run_is_stale()` checks whether the sidecar's
effective ticket id (`ticket_id`, or `run_id` when it looks like a ticket id) resolves to a
`tickets/done/` file but not a `tickets/inprogress/` one — the exact reproduced live bug (this
session's own `.claude/current_run` pointed at
`TCK-20260817-HOTFIX-DECISION-TRACE-SELECTED-MOCK-SCORE`, already in `tickets/done/`). Every
access-log row carries `sidecar_stale`, never silently trusted or dropped. **Disclosed as a
partial, scoped mitigation** — it flags known-stale attribution on this ticket's own new log; it
does not fix the underlying `.claude/current_run` sidecar mechanism itself (used by
`agent-monitoring/tools.jsonl` too), which would require changing the hook/orchestrator layer, a
different and riskier surface genuinely out of this ticket's scope.

**3. Retro integration** (`tools/agent-monitoring/generate_retro.py`): new
`compute_kgmcp_cache_efficiency_metrics(access_log_rows, tools=None)` — pure function, mirrors
`compute_retrieval_metrics()`'s shape. Computes per-ticket/per-agent hit/write/reuse-rate, a
300s-window repeated-refetch detector, a dead-write detector (a write never hit before the next
write to that row or the end of the observed log), a coverage comparison against real
`tools.jsonl` search/graphify call volume, and a rule-based `verdict`/`verdict_explanation`
(`_kgmcp_verdict()`) — added mid-task after the orchestrator's direct framing correction that raw
counts alone don't answer "is this cache good or bad." New "## KGMCP Cache Efficiency" section in
`generate()` always renders (mirrors "## Parity Index Read-Path Usage"'s "0 today is itself the
finding" precedent) — a real search-active-but-cache-inactive period must never silently vanish
from the report.

**4. Skill Usage -> dashboard wiring**: `compute_retro_metrics()` gained two new optional
params, `tools=None`/`kgmcp_access_log=None`, both computed over `[]` when omitted (fully
additive — every pre-existing caller unaffected). Chose this over computing `skill_usage`
separately inside `ingest.py` specifically to preserve `TCK-20260718-RETRO-STATS-REFACTOR`'s own
"CLI and JSON API stay logically consistent" property: `generate()` now reads `su`/`kce` from
`compute_retro_metrics()`'s own return dict instead of a second, independent
`build_skill_usage_section()` call (proven via a monkeypatch-based regression test).

**5. KGMCP -> dashboard wiring**: `AgentMonitoringStats` gained `skill_usage: SkillUsageSection`
and `kgmcp_cache_efficiency: KgmcpCacheEfficiencyStats` (plus 5 new submodels), field-for-field
mirrors of `compute_retro_metrics()`'s new dict keys, per this file's own established convention.
`DashboardCache._rebuild()` now retains `self._tools_all` (previously discarded after building
`_tools_by_seq`/`_tools_by_run_recent`); `get_agent_monitoring_stats()` calls
`read_cache_access_log()` fresh on every request (not mtime-tracked — low write volume, matches
`get_ticket_corpus_stats`/`get_glossary`'s own "recompute is cheap" precedent).

**6. Frontend**: `StatsView.tsx` gained two subsections inside the existing Agent Monitoring
section — Skill Usage (`StatTile` + `BarChart`) and KGMCP Cache Efficiency (a color-coded verdict
callout, headline `StatTile`s, per-ticket/per-agent tables) — following the file's existing
component/data patterns exactly (no new components introduced). `api.ts` gained matching
TypeScript interfaces.

**Known limitation (disclosed, not silently omitted)**: `retrieval_cache.py`'s `CACHE_DB_PATH` is
a single fixed relative path, not parameterized by `DashboardCache`'s own `repo_root` — a
pre-existing property of that module (every function reads the same module constant), not
introduced by this ticket. `get_agent_monitoring_stats()`'s `kgmcp_cache_efficiency` field
therefore always reads the real repo's `knowledge-index/retrieval_cache.db`, even when
`DashboardCache` itself is constructed against a different `repo_root` (as tests do) — tests cover
this by monkeypatching `read_cache_access_log()` directly rather than claiming full repo-root
isolation. Full `docs/parity_ledger/infrastructure.yaml` entry authorship (the exhaustive format
prior `retrieval_cache.py` migration tickets used) was evaluated and deliberately deferred given
this ticket's already-large real scope — disclosed, not silently dropped; `cache_migration_plan.md`
(the authoritative migration registry) and the two dashboard docs were updated instead.

## Test Summary

Backend: `tests/tools/test_retrieval_cache.py` (+31 new tests: migration idempotency/column-shape/
generation-stamp, sidecar read/staleness, `log_cache_access`/`read_cache_access_log` behavior
including never-raises guards, real 4-call-site instrumentation, and a direct proof that the
parent row's own `hit_count` really is wiped by `INSERT OR REPLACE` while the access log retains
full history), `tests/tools/test_generate_retro.py` (+18 new tests for
`compute_kgmcp_cache_efficiency_metrics`/`compute_retro_metrics`/`generate()`, plus 2 existing
byte-identical-report fixtures updated with real captured output and 1 key-set test updated),
`tests/tools/test_agent_ops_dashboard_stats.py` (+5 new tests). Frontend:
`dashboard-frontend/src/test/StatsView.test.tsx` (+4 new tests, fixture extended) and `App.test.tsx`
(fixture extended, no new tests needed).

Full scoped run: `pytest tests/tools/test_retrieval_cache.py tests/tools/test_generate_retro.py
tests/tools/test_agent_ops_dashboard_stats.py tests/tools/test_agent_ops_dashboard_api.py
tests/tools/test_agent_ops_dashboard_glossary.py tests/tools/test_skill_usage_metric.py` — 316
passed, 0 failed. `npx vitest run` (dashboard-frontend, full suite) — 145 passed, 0 failed. `npx tsc
-b` and `npm run build` both clean.

Real (non-mocked) verification: a real `write_provider_result_cache()`/
`record_provider_result_cache_hit()` round-trip against a real sidecar file produced 2 real,
correctly-attributed access-log rows; `read_current_run_sidecar()` against this session's real,
unmodified `.claude/current_run` correctly flagged `sidecar_stale: True` (the real, live
already-closed-ticket reproduction); `generate_retro.py --all` run against the real 1149-run
corpus produced a real `NOT IN USE` KGMCP verdict (0 cache events vs. 2605 real search calls) and a
real 245-invocation Skill Usage table; a real `uvicorn` process serving `main:app` returned both
new fields populated with the same real values over actual HTTP. No real browser was used to
visually load the Stats tab — disclosed honestly; no browser automation tool was available to this
agent in this environment.

## Files Changed

- `tools/retrieval_cache.py` — migration_005, sidecar read/staleness helpers, `log_cache_access`/
  `read_cache_access_log`, instrumentation at 4 call sites, `retrieval_cache_schema_version` 2->3.
- `tools/agent-monitoring/generate_retro.py` — `compute_kgmcp_cache_efficiency_metrics`,
  `_kgmcp_verdict`, `compute_retro_metrics`'s new `tools`/`kgmcp_access_log` params and 2 new
  return keys, `generate()`'s new KGMCP section + `su`/`kce` sourced from `metrics`, `main()`
  loading/threading `kgmcp_access_log`.
- `src/api/agent_ops_dashboard/models.py` — `SkillUsageSection`, `KgmcpCacheTicketStats`,
  `KgmcpRepeatedRefetchEntry`, `KgmcpDeadWriteEntry`, `KgmcpCoverageStats`,
  `KgmcpCacheEfficiencyStats`, 2 new `AgentMonitoringStats` fields.
- `src/api/agent_ops_dashboard/ingest.py` — `self._tools_all` retention, `read_cache_access_log`
  import + wiring into `get_agent_monitoring_stats()`.
- `dashboard-frontend/src/api.ts` — matching TS interfaces + 2 new `AgentMonitoringStats` fields.
- `dashboard-frontend/src/views/StatsView.tsx` — Skill Usage + KGMCP Cache Efficiency subsections.
- `docs/observability/agent_ops_dashboard_contract.md`,
  `docs/guides/agent_ops_dashboard.md`,
  `docs/engine/contracts/knowledge_gateway_mcp/cache_migration_plan.md` — updated to reflect the
  above.
- Tests: `tests/tools/test_retrieval_cache.py`, `tests/tools/test_generate_retro.py`,
  `tests/tools/test_agent_ops_dashboard_stats.py`, `dashboard-frontend/src/test/StatsView.test.tsx`,
  `dashboard-frontend/src/test/App.test.tsx`.
- `agent-monitoring/retro/RETRO-ALL.md`, `agent-monitoring/retro/index.md` — real regenerated
  output from the verification run above.
- `staging_artifacts/TCK-20260818-.../{investigation,plan,test_plan}.md` (this ticket's own).

## Completion Summary

All 5 scope items implemented and verified with real (non-mocked) evidence: (1) the KGMCP
cache-access-log schema, instrumentation, and retro section — the most novel and highest-value
piece — is fully real, tested, and proven against the live 1149-run corpus, including the
mid-task-added efficiency-verdict framing (reuse rate, redundant-refetch and dead-write detection,
coverage vs. real search activity, folded into a single glanceable verdict); (2) Skill Usage is
now wired into `compute_retro_metrics()`/`AgentMonitoringStats` end-to-end, verified over real HTTP;
(3) KGMCP cache-attribution is wired into the same dashboard response, verified the same way; (4)
both new frontend sections are implemented, matching existing conventions, verified via 145 passing
frontend tests plus a clean production build — no live browser was available to this agent to
additionally confirm a rendered screenshot, disclosed honestly rather than claimed; (5)
sidecar-staleness is addressed with a real, scoped, tested partial mitigation (a `sidecar_stale`
flag on every new log row), with the full underlying-mechanism fix explicitly disclosed as
out-of-scope follow-up work, not silently left unstated. One deliberate, disclosed scope
reduction: a full `docs/parity_ledger/infrastructure.yaml` entry (the exhaustive format this
module's prior schema-migration tickets used) was not authored, given the ticket's already very
large real delivered scope — `cache_migration_plan.md` (the authoritative migration registry) and
both named dashboard docs were updated in its place.
