---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260914-MONITORING-SURFACE-DEAD-MECHANISMS
phase: open
date: 2026-09-14
tags: [agent-monitoring, data-quality, process-improvement]
---

# TCK-20260914-MONITORING-SURFACE-DEAD-MECHANISMS

## Title
Six defects in the agent-monitoring surface, five of them mechanisms that exist and do not measure what they claim

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
Six defects found across 2026-09-13/14, all in the agent-monitoring/working-log surface, bundled
because they share one shape: **a mechanism exists, has tests, and does not measure the thing it
appears to measure.** Filed as one ticket rather than six because the shape is the finding — six
separate tickets would each look like a small bug and the pattern would disappear.

Every item below was verified at source on `main` (not inferred, not relayed). Counts are from
`5107e0778` and will drift — re-measure before starting.

**1. The duplicate-row detector has no caller.** `tools/validate_working_log.py` implements a
"Duplicate ticket IDs in working_log.csv" check with its own passing tests. `grep -rln
validate_working_log tools .github/workflows Makefile .claude tests` returns exactly two files: the
module itself and its test. No CI job, no Makefile target, no gate check, nothing in `.claude/`
invokes it. It has never run outside its own test.

**2. The same detector excludes the defect class it would need to catch.** Lines 41-50: rows the
tolerant parser flagged `is_duplicate=True` (exact-duplicate physical lines) are filtered out
*before* the duplicate-ID scan, as "a known, tracked defect class, not a genuine reopened/duplicate
ticket". Those are precisely the rows the `merge=union` CRLF defect produced
(`TCK-20260911-WORKING-LOG-LINE-ENDING-UNION-DUPLICATION`). So even if item 1 were fixed, this check
would skip the duplicates that actually occur.

**3. Two tests race live writes, and the failure gates a real suite.**
`tests/tools/test_agent_tool_usage_baseline.py` reads the live
`agent-monitoring/data/*/tools.jsonl` corpus twice with no snapshot between reads:
- `test_sum_of_per_agent_counts_matches_wc_l_sanity_check_on_real_corpus` (lines 141-149): globs and
  counts lines itself, then calls `load_all_tool_rows()` which re-globs and re-reads.
- `test_script_is_read_only_against_real_agent_monitoring_data` (lines 206-212): same pattern.

Every Bash call in every session fires a `PostToolUse` hook appending to that corpus. With 8+
concurrent sessions the window is hit regularly, producing `assert 221850 == 221849`. Reproduced
independently by `rpg-implementer` from its own session's activity.

**The gating consequence, verified:** `Slow regression` declares `needs: [..., api-tools, ...]` and
runs only on push-to-main, schedule, or `workflow_dispatch`. On run `34806979880` (commit
`1e075b807`, `event: push`, `head_branch: main` — so the `if:` was satisfied), `API / tools /
logging` **failed** and `Slow regression` **skipped**. On a push-to-main run the trigger condition
cannot explain that skip; `needs:` is the only remaining cause. So an intermittent failure here
converts the slow suite from a result into a **non-result**, and `skipped` reads as neutral in a job
list where `failure` would be investigated. It cost the RPG side two days of waiting for a
determinism verdict.

Refinement worth keeping (from `rpg-feature-planning`): `workflow_dispatch` satisfies the `if:` but
**not** `needs:` — a manual dispatch still skips if any needed job is red. Dispatch is necessary,
not sufficient.

Note two sibling tests (`test_output_has_exactly_16_agent_rows_plus_unattributed`,
`test_agent_row_present_with_zero_count_for_agents_with_no_real_rows`) also touch the live corpus but
assert set-membership rather than comparing two derived reads, so they do not race. Two tests, not
four — an earlier report said four.

**4. A debounce cache is tracked in git.** `.claude/.epic_staleness_state.json` is written only by
`epic_staleness_check.py`'s `--hook` branch and read only by its `_load_hook_state()` to suppress a
repeated nag (`{session_id, ts}`). `STATE_FILE` appears in exactly one place in the codebase. A
committed value carries *another session's* id and is meaningless in every other clone, while still
costing merge conflicts — four so far (#183, #184, #186, and a contamination on the parity branch).

**5. The staleness hook reads a retired path.** Same file, `--hook` branch: `find_stale_epics(...,
Path("agent-monitoring/runs.jsonl"))`. That flat file was retired by
`TCK-20260902-MONITORING-WEEKLY-SHARDING-EPIC`; it does not exist (16 `agent-monitoring/data/*/runs.jsonl`
shards do). Effect is **under-detection, not false positives**: `_read_runs_records` returns `[]` on
a missing file, `most_recent` becomes `None`, and `is_epic_stale` returns `False` when
`most_recent_activity is None`. Same defect class as
`TCK-20260904-HOTFIX-WORKFLOW-META-CONFORMANCE-SHARD-AWARENESS`, surviving in a second consumer
because nobody checked whether the retirement broke other readers.

**6. Two sanctioned writers duplicate against each other.** `record_hand_orchestrated_closure.py:207`
calls `append_working_log_row()` — `TCK-20260912-WORKING-LOG-APPEND-HELPER`'s helper — internally.
Calling the helper directly and then running the closure tool writes two rows, both through the
documented path. The closure tool's docstring warns of it, which makes it known but not prevented.
A writer-scan guard structurally cannot catch this, because both writers are legitimate; only a
content check on the artifact can.

## Scope
- Re-measure everything above before starting; these counts move continuously.
- **Item 3 first** — it is the only one currently costing other work. Fix in the shared loading
  path (snapshot the shard list once, derive both the raw count and the report from that snapshot),
  not per-test, so both racing tests are covered by one change.
- Wire item 1's detector into something that runs, and remove item 2's exclusion so it sees the
  duplicates that actually occur.
- Item 4: stop tracking the state file (gitignore it, or move it outside `.claude/`). Confirm no
  consumer depends on its being committed.
- Item 5: point the hook at the sharded layout, reusing the existing shard-aware helper rather than
  reimplementing a glob (`done_checker_static._jsonl_rows_for_run_id_across_weeks` is the precedent
  `TCK-20260904-HOTFIX-WORKFLOW-META-CONFORMANCE-SHARD-AWARENESS` used). Establish what currently
  supplies `most_recent` given the dead path — run data may have been decorative in this check since
  the sharding epic, which changes whether fixing it alters behaviour at all.
- Item 6: a content check on `tickets/working_log.csv` catching duplicate `(ticket_id, title)` rows.

## Out of Scope
- Re-litigating the `merge=union` / CRLF work — that shipped and is not in question here.
- Wave 3 agent-tools scoping, the parity ledger residual, or anything outside this subsystem.

## Acceptance Criteria
- [ ] Item 3: both racing tests derive from one snapshot; a test demonstrates the fix (e.g. an
      injected write between the two reads no longer changes the result).
- [ ] Item 1: the duplicate detector runs somewhere real (CI job, Makefile target, or gate check),
      and that wiring is pinned by a test.
- [ ] Item 2: the `is_duplicate` exclusion is removed or narrowed, with the reason recorded; the
      detector reports the duplicates the union defect produces.
- [ ] Item 6: **the content check must ratchet, not assert zero.** `main` currently carries **45**
      duplicate `(ticket_id, title)` pairs, 21 with a 2026-09 row. A check asserting zero is
      unlandable and gets disabled on day one — the same constraint that sank the parity baseline's
      exact-equality assertion (`TCK-20260913-PARITY-BASELINE-EQUALITY-GATE-PENALIZES-IMPROVEMENT`).
      Record the baseline; forbid increases.
- [ ] Item 4: the state file is untracked, and a merge of two branches that both triggered the hook
      produces no conflict on it.
- [ ] Item 5: the hook reads the sharded layout; what supplies `most_recent` today is recorded.
- [ ] Every count in this ticket re-measured at implementation time and corrected if changed.

## Related Tickets
- `TCK-20260904-HOTFIX-WORKFLOW-META-CONFORMANCE-SHARD-AWARENESS` (done) — item 5 is the same defect
  class in a second consumer.
- `TCK-20260911-WORKING-LOG-LINE-ENDING-UNION-DUPLICATION` (done) — produced the rows item 2 excludes.
- `TCK-20260912-WORKING-LOG-APPEND-HELPER` (done) — item 6's second sanctioned writer.
- `TCK-20260913-PARITY-BASELINE-EQUALITY-GATE-PENALIZES-IMPROVEMENT` (open) — the ratchet precedent
  item 6's acceptance criterion depends on.
- `TCK-20260902-MONITORING-WEEKLY-SHARDING-EPIC` (done) — the retirement item 5 missed.

## Related Docs
- `docs/plans/agent_infrastructure/reachability_verification_findings.md` — this ticket is six more
  instances of its Finding 1 (mechanisms that certify rather than detect).

## Related Stored Artifacts
None.

## Related Code Areas
- `tools/validate_working_log.py`
- `tests/tools/test_agent_tool_usage_baseline.py`
- `tools/agent-monitoring/epic_staleness_check.py`
- `tools/agent-monitoring/record_hand_orchestrated_closure.py`, `tools/working_log_writer.py`
- `.github/workflows/test.yml` (the `slow` job's `needs:`)

## Assumptions / Open Questions
- Whether item 1's detector should block CI or report. Given items 2 and 6, it will likely fire on
  existing data — decide against measured counts, not in advance.
- Whether anything outside this repo reads `.claude/.epic_staleness_state.json`. Nothing in-repo does.
- Item 5's real-world effect is unknown until `most_recent`'s actual source is established.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
