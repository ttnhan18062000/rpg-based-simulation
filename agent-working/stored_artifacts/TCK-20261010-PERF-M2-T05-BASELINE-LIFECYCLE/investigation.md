---
status: historical
layer: performance
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261010-PERF-M2-T05-BASELINE-LIFECYCLE
date: 2026-10-10
tags: [performance, benchmarking, documentation]
---

# Investigation: TCK-20261010-PERF-M2-T05-BASELINE-LIFECYCLE

Search order: `search_docs`, then targeted reads (graphify not needed: a new self-contained tool).

## Findings
1. The shared `docs/plans/test_architecture/reference/baseline_change_policy.md` does not exist, and `TCK-20261009-KNOWN-REDS-REGISTRY-SHARED-MODULE`
   is an unstarted ticket in another domain. That is why T05 was split and the policy cites the shared doc as a pending forward reference.
2. `BenchmarkRecord.identity.baseline_ref` already exists in schema 1.0 (`{id, schema_version, record_digest}`), so the chain needs no new field.
3. `baselines/` holds 15 `*.json` plus `__init__.py`; no consumer globs the directory (the tests name files), so adding `*.vNNNN.json` files later does not
   change an existing test.
4. The section citations of `perf_baseline_policy.md` elsewhere in `docs/` (for example `§2.2` hardware table, `§3` band tolerance) were already stale
   before this ticket: the T01 restructure had moved that content. Not touched here.
5. The rewritten policy is `authority: P1`: the owner approves it at merge.
6. The flaky `tests/integration/observability/test_baseline_comparison_flow.py::test_baseline_comparison_and_cli_flow` (found in X1) could not be sent to
   its owner: `rpg-planner` was not reachable. Noted in the PR.

## Not verified
- The tool was exercised only against temporary directories and the committed tree; no real candidate record from a real benchmark was promoted.
- The knowledge index was not rebuilt in this worktree (the planner runs it from main).
