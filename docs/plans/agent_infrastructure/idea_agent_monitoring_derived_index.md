---
status: idea
layer: observability
authority: P2
audience: developer
maturity: idea
date: 2026-07-11
tags: [idea, agent-infrastructure, observability, data-quality, schema]
---

# Idea: Derived SQLite Index Over agent-monitoring/*.jsonl (Read Path Only)

## Problem

`agent-monitoring/` is 3 append-only JSONL files (`runs.jsonl` 582 lines, `events.jsonl` 2,724 lines, `tools.jsonl` 46,984 lines) read by 4 independent consumers, each of which re-implements its own interpretation of the same data:

- `tools/agent-monitoring/query.py` (120 lines) — full in-memory linear scan, list-comprehension filters. **Has zero test coverage** (`tests/tools/test_query.py` does not exist).
- `tools/agent-monitoring/generate_retro.py` (507 lines) — hand-rolls `_resolve_status()`, `_is_legacy_event()`, `_is_gate_fail()` to interpret the same legacy record shapes.
- `tools/agent-monitoring/validate.py` — its own, separately-maintained `LEGACY_COMPLETION_FIELDS`/`LEGACY_TERMINAL_STATUS_VALUES` allowlists (documented in `docs/agent-monitoring/schema.md`'s Known Limitations — at least 5 historical `runs.jsonl` schema generations coexist).
- `done-checker`'s static check (`check_monitoring_write_recorded`) — existence-only, non-blocking.

None of these share a normalization layer. When `TCK-20260705-MONITORING-RUNID-JOIN` audited join integrity and `TCK-20260708-AGENT-MONITORING-SCHEMA-ENFORCEMENT` audited vocabulary drift, both had to write bespoke one-off Python against the raw files — the same thing happened again in `TCK-20260711-MONITORING-TOOLCOUNT-SIDECAR-COLLISION`'s cross-check of `tool_call_count` against `tools.jsonl` ground truth. Every one of these investigations re-derives the same kind of grouping/joining logic from scratch because there is no shared, queryable, pre-normalized representation of this data — only 3 raw append logs and N independent readers of them.

This is explicitly **not** a performance problem at current volume — 47k small JSON lines is instant to scan in Python either way. It's a query-expressiveness and DRY problem: every cross-file join (`events` × `tools` by `(run_id, seq)`, `runs` × `events` by `run_id`, date-bucketing, legacy-shape normalization) gets reinvented per investigation instead of asked once as SQL against a clean schema.

## Idea

Add a **derived, read-only SQLite index**, rebuilt from the 3 JSONL files, modeled directly on this repo's own existing precedent: `knowledge-index/knowledge.db` is built from `docs/`/`tickets/` by `tools/knowledge_search.py build`, is gitignored, and is never the source of truth — the markdown files are. Same shape here:

- **The JSONL files stay exactly as they are** — append-only, hook-written, source of truth. No change to `pre_tool_hook.py`/`post_tool_hook.py`/`writeSidecar`/`writeMonitoring`'s write path at all. This is deliberate: those hooks fire synchronously on every tool call, and CLAUDE.md's hard rule ("monitoring write failure must never fail the workflow") is far easier to guarantee for a bare file-append than for anything requiring a DB connection/lock.
- A new build script (e.g. `tools/agent-monitoring/build_index.py`) reads all 3 files once, normalizes every legacy shape **in one place** (the same interpretation `generate_retro.py` and `validate.py` currently duplicate), and writes 3 tables (`runs`, `events`, `tools`) plus perhaps one normalized view (e.g. a `resolved_status` column computed once, replacing `_resolve_status()`).
- **Full rebuild only — no incremental-build logic.** `knowledge_search.py`'s incremental mode exists because re-embedding is genuinely expensive (model inference over hundreds of docs). Parsing 47k small JSON lines into SQLite has no equivalent cost — a full rebuild is sub-second. Deliberately *not* copying the incremental-diff machinery avoids introducing a second surface for exactly the kind of subtle staleness bug this session's two tickets were both about. One Make target: `make agent-monitoring-index` (no `-update` variant needed).
- The index is gitignored, like `knowledge-index/`. It is a convenience layer for querying/reporting, never a dependency for the write path or for anything gating a workflow.
- Consumers migrate opportunistically, not as one big-bang rewrite: `query.py` (currently untested — lowest risk, and gets net-new test coverage as part of migrating) is the natural first target. `validate.py`'s two `compute_*_drift_report()` functions and `generate_retro.py`'s status/legacy-shape resolution are natural second/third targets, since consolidating their duplicated normalization logic is the actual DRY payoff.

### What this does not fix (orthogonal, already known)

- Uneven writer coverage across the 4 workflows (`implement-epic`/`create-tickets` still have incomplete or zero sidecar registration) — a storage-format change doesn't add missing instrumentation.
- `writeMonitoring` still being LLM-executed bookkeeping rather than fully deterministic orchestrator code (`idea_agent_bookkeeping_determinism.md`'s remaining scope, archived — shipped, see its 2026-07-12 Amendment) — same, orthogonal.
- `done-checker`'s existence-only, non-blocking verification — a policy decision (warn vs. gate), not a format question.
- Historical data corruption — not backfilled either way, regardless of storage format.

## Natural Integration Points

| Existing component | How this idea attaches |
|---|---|
| `tools/knowledge_search.py` (`build`) | Direct structural precedent — derived/gitignored/rebuildable index pattern, reused wholesale rather than invented fresh |
| `tools/agent-monitoring/query.py` | Lowest-risk first migration target — currently has zero tests; migrating is also the moment to add them |
| `tools/agent-monitoring/validate.py` | `compute_drift_report()` and `compute_tool_count_drift_report()` (`TCK-20260711-MONITORING-TOOLCOUNT-SIDECAR-COLLISION`) both re-derive groupings by hand today — natural second migration target |
| `tools/agent-monitoring/generate_retro.py` | `_resolve_status()`/`_is_legacy_event()`/`_is_gate_fail()` are exactly the kind of build-time normalization this index would centralize |
| [`idea_agent_monitoring_schema_enforcement.md`](../archive/agent_infrastructure/idea_agent_monitoring_schema_enforcement.md) (archived — shipped) | That idea's vocabulary/null-field drift-checking is a read-time concern this index's build step could absorb as a `CHECK` constraint or build-time warning, instead of a separate read-time pass |
| [`idea_agent_cost_observability.md`](idea_agent_cost_observability.md) | Its spend-by-phase/spend-by-agent retro breakdown is exactly the kind of aggregation query this index makes trivial instead of hand-rolled |
| `TCK-20260711-EVAL-SEARCH-DOCID-ANCHOR-FIX`, `TCK-20260711-MONITORING-TOOLCOUNT-SIDECAR-COLLISION` | Both tickets that directly motivated this idea — each required writing bespoke one-off Python to answer "is this derived metric actually correct," which a queryable index would make a one-line query instead |

## Open Questions

- Should `query.py` gain its (currently nonexistent) test suite *before* migrating it to the index, or as part of the same change? Migrating untested code and adding tests in the same diff is more risk than doing them as two small, sequenced steps.
- Should the build step encode a single `resolved_status` (or similar normalized) column/view, or should normalization stay entirely in Python helper functions that happen to run once at build time instead of once per reader? The former is more SQL-native; the latter is a smaller diff from what exists today.
- Is a Make target the right home, or should this be a `tools/agent-monitoring/` CLI subcommand alongside `record_run.py`/`record_events.py`/`validate.py` (this repo has both conventions already)?
- If `agent-monitoring/tools.jsonl` grows by orders of magnitude in the future (unlikely at current usage patterns, but not impossible), should incremental build be revisited then — or is "always full-rebuild" a durable enough simplification given this is a read-only convenience layer, not a live-critical path?
- Should the index ever be built automatically (e.g. a post-commit hook mirroring `install-hooks`' knowledge-index pattern), or should it stay strictly on-demand (`make agent-monitoring-index` run manually before an investigation) given it's not relied on by any gating check?

---

*Raised: 2026-07-11, directly from investigating whether `TCK-20260711-EVAL-SEARCH-DOCID-ANCHOR-FIX`'s and `TCK-20260711-MONITORING-TOOLCOUNT-SIDECAR-COLLISION`'s pattern (a derived signal nobody could cheaply cross-check against ground truth) generalizes across the whole `agent-monitoring/` subsystem, not just the one field each of those tickets fixed. Not yet scheduled — no epic/ticket created for this idea yet, pending a decision on scope/sequencing.*
