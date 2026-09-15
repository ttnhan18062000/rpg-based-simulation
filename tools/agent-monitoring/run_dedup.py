"""Distinct-execution deduplication for `agent-monitoring/data/*/runs.jsonl`
(TCK-20260915-DUPLICATE-RUN-RECORDS).

**The shape this fixes**: a hand-orchestrating (or `implement-epic.js` batch) session that hits a
gate failure, fixes it, and continues within the same conceptual execution correctly keeps the
same `(run_id, execution_id, start_ts)` identity across every `writeMonitoring()` call along the
way -- each gate exit point calls it once. The result is multiple `runs.jsonl` rows for one real
execution, each a genuine snapshot of that execution's status at the time (`NEEDS_CHANGES` ->
`DOD_BLOCKED` -> `DONE`, etc.), not a blind duplicate. Measured directly against the real corpus
and cross-checked against `events.jsonl`'s own phase timeline for representative examples: 57 of
60 "identical-key" duplicate groups show a different `final_status` per row and a event timeline
that progresses continuously and coherently across the group -- confirming genuine multi-checkpoint
continuation, not noise. Naively counting `len(runs.jsonl)` therefore inflates every run-count
metric (denominator) without inflating `DONE` count (numerator) beyond what's real, meaning a
naive DONE rate is *understated*, not overstated.

**Disposition: dedupe-on-read.** This module never rewrites `runs.jsonl` (the historical baseline
stays frozen, matching `TCK-20260914-MONITORING-SURFACE-DEAD-MECHANISMS` items 1/6's own
precedent) -- it provides a pure read-side view that collapses each real execution's multiple
checkpoint rows down to the one representing its final, most-complete state, for any caller that
wants "how many real executions happened" rather than "how many rows were ever written."

**Grouping key**: `(run_id, execution_id, start_ts)` when `execution_id` is present and truthy --
this is the get exact definition this ticket's own investigation used to reproduce the corpus's own
142/82/60 split. A record with no `execution_id` (pre-`TCK-20260730-CLAUDE-EXECUTION-IDENTITY`
history, or `implement-epic.js`'s batch writer, which omits it deliberately) is NEVER merged with
another no-`execution_id` record on `start_ts` alone unless the two truly share the same run_id --
this module still does that (matching the ticket's own confirmed definition and measured baseline),
but callers should be aware pre-execution_id-era grouping is inherently less precise than the
execution_id-backed grouping used since 2026-07-30.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Iterable


def execution_key(run: dict, fallback_index: int) -> tuple:
    """Group key for one run record. `fallback_index` makes every execution_id-less OR
    start_ts-less record its own singleton group by default UNLESS it shares a truthy
    (run_id, start_ts) with another execution_id-less record -- matching this ticket's own
    measured definition of "identical" (see module docstring).

    Both `execution_id` and `start_ts` must be truthy to group two records together. A record
    missing `start_ts` (pre-schema-unification legacy shapes that used `started_at`/`ts_start`
    instead, confirmed present in the real corpus, e.g. `TCK-20260629-SIMQ-EMIT-NARRATIVE`'s two
    entirely-different-schema rows) must never collide with another such record just because both
    happen to have `start_ts is None` -- that produced a false-positive "identical outcome" match
    in this module's own first draft, caught by inspecting the group's actual content before
    shipping the ratchet baseline below."""
    run_id = run.get("run_id")
    execution_id = run.get("execution_id")
    start_ts = run.get("start_ts")
    if execution_id and start_ts:
        return (run_id, execution_id, start_ts)
    if start_ts:
        return (run_id, None, start_ts)
    return (run_id, "__no_start_ts__", fallback_index)


def group_runs_by_execution(runs: Iterable[dict]) -> list[list[dict]]:
    """Group `runs` by `execution_key`. Returns groups in first-seen order; each group has >= 1
    record. Preserves each record's own original list position within its group."""
    groups: dict[tuple, list[dict]] = defaultdict(list)
    order: list[tuple] = []
    for i, run in enumerate(runs):
        key = execution_key(run, i)
        if key not in groups:
            order.append(key)
        groups[key].append(run)
    return [groups[k] for k in order]


def latest_in_group(group: list[dict]) -> dict:
    """The record representing a group's final, most-complete state: highest `end_ts`
    (lexicographic ISO-8601 comparison is chronologically correct), falling back to highest
    `agent_count` for the rare case of a tied/missing `end_ts` -- a later checkpoint has done at
    least as much work as an earlier one."""
    return max(group, key=lambda r: (r.get("end_ts") or "", r.get("agent_count") or 0))


def dedupe_to_latest_per_execution(runs: list[dict]) -> list[dict]:
    """Collapse `runs` to one record per real execution (see module docstring for what "real
    execution" means here). Order is not guaranteed to match input order — callers that need a
    stable ordering should sort the result themselves (e.g. by `start_ts`)."""
    return [latest_in_group(g) for g in group_runs_by_execution(runs)]


def classify_duplicate_groups(runs: list[dict]) -> dict:
    """Diagnostic breakdown of every group with >1 record, split by how confidently each looks
    like a legitimate multi-checkpoint continuation vs. a genuine accidental duplicate:

    - "progressive": records in the group have more than one distinct `final_status` -- direct
      evidence of a real continuation (a later checkpoint reached a different outcome).
    - "same_status_diff_end": all records share one `final_status` but more than one `end_ts` --
      ambiguous; could be a legitimate re-run of the same terminal phase in a later session, or an
      accidental re-write. Not classified as "healthy" without further evidence.
    - "identical_outcome": all records share both `final_status` AND `end_ts` -- no signal
      distinguishes them at all. This is the narrow bucket this ticket's own ratchet watches,
      since it is the shape a genuine blind duplicate write would produce.
    """
    groups = [g for g in group_runs_by_execution(runs) if len(g) > 1]
    progressive = []
    same_status_diff_end = []
    identical_outcome = []
    for g in groups:
        statuses = {r.get("final_status") for r in g}
        end_tses = {r.get("end_ts") for r in g}
        if len(statuses) > 1:
            progressive.append(g)
        elif len(end_tses) > 1:
            same_status_diff_end.append(g)
        else:
            identical_outcome.append(g)
    return {
        "total_duplicate_groups": len(groups),
        "progressive": progressive,
        "same_status_diff_end": same_status_diff_end,
        "identical_outcome": identical_outcome,
    }
