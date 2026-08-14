---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260719-RETRO-OUTLIER-FLAGS
artifact_type: plan
tags: []
---

# Implementation Plan — TCK-20260719-RETRO-OUTLIER-FLAGS

## Summary

Add a new `outliers` key to `compute_retro_metrics()`'s return dict flagging `duration_s` values
(grouped by tier) and `cost_proxy_score` values (grouped by normalized phase) exceeding 3x their
group's median, plus a matching conditionally-rendered "## Outliers" Markdown section. Two Plan
decisions the ticket explicitly requires: tier-scoped median for duration_s (no phase field on
runs.jsonl); keep `slow_runs` unmerged, clearly distinguished as answering a different question.

## Anti-Drift Notes

**Deviation from normal Scope→Investigate→Plan→Review→Implement ordering, self-flagged per this
project's traceability rule**: implemented directly in the same pass as investigation; this file
and `investigation.md`/`test_plan.md` were written retroactively, after implementation, full test
verification, and a real end-to-end run against the live corpus — same pattern as the two preceding
tickets in this same batch.

## Decisions (required by the ticket's own Assumptions/Open Questions, made here)

1. **`duration_s` median basis: tier-scoped, not global.** `runs.jsonl` has no `phase` field. A
   global median across hotfix/standard/epic tiers would be meaningless (their natural durations
   differ by design) and would flag nearly every epic as "an outlier" for no real reason.
2. **`slow_runs` relationship: kept, unmerged, explicitly distinguished.** `slow_runs` (fixed
   1800s absolute threshold) and the new `outliers.duration_s` (relative, Nx tier median) answer
   different questions and may both flag the same run — the rendered report opens the Outliers
   section with a sentence distinguishing the two, immediately after Slow Runs, so they don't read
   as redundant/conflicting.

## Steps

### Step 1 — `_flag_outliers()` generic helper + constants

**Files:** `tools/agent-monitoring/generate_retro.py`
`OUTLIER_MEDIAN_MULTIPLIER = 3`, `_OUTLIER_MIN_GROUP_SIZE = 3`. `_flag_outliers(items,
group_key_fn, value_fn, multiplier)` groups by `group_key_fn`, excludes `None` `value_fn` results
from both grouping and median, skips groups below the minimum size, computes
`statistics.median`, and returns items exceeding `multiplier * median`, sorted by ratio descending.

### Step 2 — Wire duration_s and cost_proxy_score outlier detection

**Files:** `tools/agent-monitoring/generate_retro.py`
`_flag_outliers(runs, group_key_fn=lambda r: r.get("tier", "unknown"), value_fn=lambda r:
r.get("duration_s"))` for duration; `_flag_outliers(scored_events, group_key_fn=lambda e:
_normalize_phase(e) or "?", value_fn=lambda e: e.get("cost_proxy_score"))` for cost-proxy-score
(reusing `TCK-20260719-PHASE-AGENT-CASE-FOLD`'s `_normalize_phase`). Shape each result list into
the documented per-item dict (`run_id`/`tier`/`duration_s`/`median`/`ratio` for duration;
`run_id`/`seq`/`phase`/`agent`/`cost_proxy_score`/`median`/`ratio` for cost). Add `"outliers":
{"duration_s": ..., "cost_proxy_score": ...}` to the returned dict.

### Step 3 — Render the new section

**Files:** `tools/agent-monitoring/generate_retro.py`
New "## Outliers" section in `generate()`, placed immediately after "## Slow Runs", conditionally
rendered only when at least one item is flagged in either category (mirrors the existing
Reason-Codes/Tag-Breakdown conditional-render pattern). Opens with an explanatory sentence
distinguishing it from Slow Runs.

### Step 4 — Update/add tests

**Files:** `tests/tools/test_generate_retro.py`
Update `test_compute_retro_metrics_returns_all_documented_keys` for the new key. Add: tier-scoped
vs. global median proof, null-exclusion (duration and cost), minimum-group-size skip,
normalized-phase-grouping proof, section-omitted-when-empty, section-rendered-with-content.

### Step 5 — Real-data end-to-end verification

Run `python3 tools/agent-monitoring/generate_retro.py --all` against the live corpus, confirm the
rendered "## Outliers" section appears with real, sane content, and specifically confirm D25's own
originally-cited 34,837 cost_proxy_score finding is now surfaced automatically.

### Step 6 — Parity ledger

**Files:** `docs/parity_ledger/infrastructure.yaml`
New entry (next available ID after `INFRA-283`), `status: verified`, citing the new function/
constants and the 7 new/updated tests, matching `INFRA-281`/`282`/`283`'s established
"agent-orchestration/monitoring tooling, no simulation behavior" pattern.

## Scope Guards

- No changes to `src/api/agent_ops_dashboard/models.py` or `ingest.py` — explicitly out of scope;
  the ticket body must state this plainly (already does, per its own Request Summary).
- No changes to `slow_runs`'s existing computation or rendering — kept exactly as-is.
- No fix for the unrelated `generate_retro.py --days N` crash found during verification (a
  non-string `start_ts` in real data) — confirmed pre-existing via `git stash`, out of scope, noted
  for a future ticket.

## Dependency Map

Step 1 before Step 2 (Step 2 calls the helper Step 1 defines). Step 3 depends on Step 2 (renders
the key Step 2 adds). Step 4 depends on Steps 1-3. Step 5 depends on Steps 1-4 (verifies the landed
behavior against real data). Step 6 depends on all prior steps.

## Acceptance Criteria Map

- AC1 (new top-level `outliers` key, both categories, nulls excluded from flagging and median
  basis) → Steps 1-2.
- AC2 (new "## Outliers" section renders conditionally) → Step 3.
- AC3 (`test_compute_retro_metrics_returns_all_documented_keys` updated) → Step 4.
- AC4 (ticket body states dashboard does NOT get this automatically, records dashboard exposure as
  future follow-up) → already present in the ticket body itself, verified accurate during
  investigation (re-confirmed by reading `ingest.py`/`models.py` directly, not just trusting the
  proposal's original claim).

## Deviations

None from this plan itself (written retroactively to describe the actual landed implementation
exactly) — see Anti-Drift Notes above for the one deviation that matters: staging artifacts were
written after implementation, not before.
