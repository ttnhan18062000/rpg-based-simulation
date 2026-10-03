---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260914-MONITORING-SURFACE-DEAD-MECHANISMS
phase: done
date: 2026-09-14
tags: [agent-monitoring, data-quality, process-improvement]
---

# TCK-20260914-MONITORING-SURFACE-DEAD-MECHANISMS

## Title
Six defects in the agent-monitoring surface, five of them mechanisms that exist and do not measure what they claim

## Status
DONE

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

**Correction (2026-09-14, found during implementation).** The two affected tests do **not** share one
mechanism, and the "fix it in the shared loading path and both are covered" framing below is wrong:

- `test_sum_of_per_agent_counts_matches_wc_l_sanity_check_on_real_corpus` genuinely reads the corpus
  **twice** (its own glob+read, then `load_all_tool_rows()`'s separate read). A shared single-read
  snapshot resolves this one completely.
- `test_script_is_read_only_against_real_agent_monitoring_data` reads the corpus **once**. Its race is
  a working-tree porcelain snapshot taken before and after that single read: any *other* session's
  hook append inside that window makes the snapshot differ, and the test then misattributes that
  external write to this script. A shared snapshot does not touch that mechanism at all.

The second needs a different fix: assert the property that actually matters — this script never
truncates or deletes existing content — by comparing per-file sizes before and after, forbidding
shrinkage or deletion while tolerating growth. A concurrent hook can only append or add a new shard;
it can never shrink or remove one, so that formulation is immune to legitimate concurrent writes by
construction rather than merely less likely to collide with them.

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
- [x] Item 3a (double-read race): the `wc -l` sanity check derives both numbers from one read; an
      injected write between the reads no longer changes the result.
- [x] Item 3b (porcelain-sandwich race): the read-only test asserts no shrinkage/deletion rather than
      a byte-identical working-tree snapshot, and tolerates concurrent growth.
- [x] Item 1: the duplicate detector runs somewhere real (CI job, Makefile target, or gate check),
      and that wiring is pinned by a test. **It must ratchet, not assert zero** — the same constraint
      as item 6, not originally named here: the existing check reports **57** duplicate `ticket_id`s on
      the real corpus *with* the `is_duplicate` exclusion still active, and **39** of those ids carry
      more than one distinct title (`TCK-20260401-FINAL-CONVERGENCE` has three unrelated ones).
      Those are historical ID-reuse collisions, not the dual-writer duplication this wiring would catch
      going forward. Measured 2026-09-14; mostly disjoint from item 6's 46 pairs. A ratchet freezes
      them rather than resolving them — whether old ID reuse needs its own cleanup is a question this
      ticket deliberately does not answer.
      **Re-measured post-item-2-fix (below): the 57/39 figures above are the pre-item-2-fix baseline
      and the ratchet is correctly pinned to the post-fix number, 84 — not 57. See "Every count
      re-measured" note below for why 57 is no longer the live ceiling and why "mostly disjoint" no
      longer holds.**
- [x] Item 2: the `is_duplicate` exclusion is removed or narrowed, with the reason recorded; the
      detector reports the duplicates the union defect produces.
- [x] Item 6: **the content check must ratchet, not assert zero.** `main` currently carries **45**
      duplicate `(ticket_id, title)` pairs, 21 with a 2026-09 row. A check asserting zero is
      unlandable and gets disabled on day one — the same constraint that sank the parity baseline's
      exact-equality assertion (`TCK-20260913-PARITY-BASELINE-EQUALITY-GATE-PENALIZES-IMPROVEMENT`).
      Record the baseline; forbid increases.
      **Re-measured at implementation time: 46, not 45 (see note below) — `DUPLICATE_PAIR_CEILING`
      is correctly pinned to 46.**
- [x] Item 4: the state file is untracked, and a merge of two branches that both triggered the hook
      produces no conflict on it.
- [x] Item 5: the hook reads the sharded layout; what supplies `most_recent` today is recorded.
- [x] Every count in this ticket re-measured at implementation time and corrected if changed.
      **Corrected counts, all measured 2026-09-14 against the real corpus at implementation time:**
      - Item 6 pair count: ticket cited 45 → actual measured count is **46**
        (`DUPLICATE_PAIR_CEILING = 46`, confirmed independently by agent-working-design).
      - Item 1 duplicate-`ticket_id` count: the ticket's own AC cites 57 as the figure *with* item
        2's exclusion still active (pre-item-2-fix). Once item 2's fix landed (removing the
        exclusion), the same scan's real count is **84**, and `DUPLICATE_TICKET_ID_CEILING` is
        correctly pinned to 84, not 57 — 57 was never the live post-fix baseline, it was the
        reference figure for the *unfixed* state the ticket was describing.
      - Item 1/item 6 relationship: the AC text above states item 1's set is "mostly disjoint" from
        item 6's 46 pairs — true only against the pre-item-2-fix 57/39 figures (measured then: 19/57
        overlap). Re-measured post-item-2-fix, in a self-caught inconsistency found while writing
        item 6's own regression test: item 1's post-fix 84-id set **fully contains** all 46 of item
        6's ids (overlap = 46, not 19). This is expected, not a bug — a same-title duplicate is
        necessarily also a same-ticket_id duplicate, and item 2's fix widened item 1's scan to see
        every row item 6 already saw. The two checks remain justified as separate, non-redundant
        scopes for a semantic reason (ticket_id reuse regardless of title vs. reuse with the
        identical title), not a set-overlap argument — see `working_log_content_duplicate_check.py`'s
        module docstring and `test_item_6_ids_are_fully_contained_in_item_1_ids_on_the_real_corpus`
        for the corrected reasoning and pin.

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
Fixed in dependency order, item 3 first per Scope (the only item costing other work):

- **Item 3a/3b**: `tools/agent-monitoring/validate.py` gained
  `load_jsonl_with_line_count()`/`load_data_glob_with_line_count()`, both deriving the row list
  AND the raw line count from a single `path.read_text()` per shard, eliminating (not narrowing)
  the double-read race in `test_sum_of_per_agent_counts_matches_wc_l_sanity_check_on_real_corpus`.
  The existing `load_jsonl()`/`load_data_glob()` now delegate to these, preserving every other
  caller's behavior. `test_script_is_read_only_against_real_agent_monitoring_data` was redesigned
  around a `_file_size_snapshot()` (`{path: size}`) asserting no shrinkage/deletion, immune by
  construction to legitimate concurrent growth — a concurrent hook can only append, never shrink.
- **Item 2**: removed the `is_duplicate`-row exclusion from `validate_working_log.py`'s duplicate-
  ticket-ID scan (it was filtering out exactly the rows the `merge=union` CRLF defect produced —
  the defect class the scan most needs to catch). `run_validation()` now also returns a structured
  `duplicate_ticket_ids` field.
- **Item 1**: wired the now-corrected scan into `tools/gate_checks/working_log_duplicate_check.py`,
  a ratchet check (`DUPLICATE_TICKET_ID_CEILING = 84`, the post-item-2-fix real count — not the
  ticket's pre-fix 57 reference figure), plus a Makefile target and tests.
- **Item 4**: gitignored `.claude/.epic_staleness_state.json` (same shape as the existing
  `.retro_nudge_state.json` precedent) and `git rm --cached`'d it; added a real scratch-repo test
  proving two branches both writing the file produce no merge conflict.
- **Item 5**: `epic_staleness_check.py`'s `--hook` branch read a retired flat path
  (`agent-monitoring/runs.jsonl`, retired by `TCK-20260902-MONITORING-WEEKLY-SHARDING-EPIC`).
  Rewrote `_read_runs_records()` to call `validate.py::load_data_glob()` against the sharded
  `agent-monitoring/data/<ISO-week>/runs.jsonl` layout. Established (by reading
  `resolve_child_activity()`/`is_epic_stale()` directly) that `most_recent` had been supplied
  entirely by `tickets/working_log.csv` since the sharding epic — the fix is not behavior-neutral:
  in-progress-but-not-yet-closed epics were previously misclassified as having zero activity, since
  `working_log.csv` only gains a row on ticket close. Deviated from the ticket's named precedent
  helper (`done_checker_static._jsonl_rows_for_run_id_across_weeks`, single-run_id-keyed) in favor
  of the bulk multi-shard `validate.py::load_data_glob` built in item 3's own fix, since
  `resolve_child_activity()` needs activity across a *set* of child_ids and already expects one
  flat "all records" iterable — disclosed to the peer rather than silently substituted.
- **Item 6**: new `tools/gate_checks/working_log_content_duplicate_check.py`, a ratchet check on
  `(ticket_id, title)` duplicate rows (`DUPLICATE_PAIR_CEILING = 46`, corrected from the ticket's
  45 estimate). Self-caught during implementation: the module's own first-drafted docstring and
  regression test claimed item 1's and item 6's duplicate-id sets were "mostly disjoint" (true only
  against the *pre*-item-2-fix 57/39 figures, measured earlier in the same session). Re-measuring
  against the corpus after item 2's own fix had already landed showed item 1's post-fix 84-id set
  fully contains all 46 of item 6's ids — corrected both the docstring and the test
  (`test_item_6_ids_are_fully_contained_in_item_1_ids_on_the_real_corpus`) to state the real,
  current relationship and reframe the "why two separate checks" reasoning around the semantic
  distinction (ticket_id reuse regardless of title vs. reuse with the identical title) rather than
  a now-false disjointness claim.

## Test Summary
- `tests/tools/test_agent_tool_usage_baseline.py` — rewrote the `wc -l` sanity test to use the
  race-free line-count function; added a real injected-write regression proof; redesigned the
  read-only test around a file-size snapshot. All passing.
- `tests/tools/test_validate_working_log.py` — flipped the exclusion test to confirm flagged
  duplicate rows are now *included*, not excluded.
- `tests/tools/test_working_log_duplicate_check.py` (new, item 1) — 5 tests: ratchet pass/fail,
  ceiling-may-only-decrease pin, real-corpus check, Makefile wiring.
- `tests/tools/test_epic_staleness_check.py` — 3 new tests for item 4 (gitignore status, untracked
  status, real scratch-repo merge-conflict-free proof); refactored all fixtures from a flat
  `runs.jsonl` path to a sharded `data/` root for item 5, plus 3 new tests confirming shard
  activity is read, activity split across multiple weekly shards all contributes, and the dead flat
  path is no longer referenced.
- `tests/tools/test_working_log_content_duplicate_check.py` (new, item 6) — 9 tests: unit coverage
  of the two defect shapes (same-id-different-title is NOT caught; same-id-same-title IS caught),
  ratchet pass/fail, ceiling-may-only-decrease pin, real-corpus check, Makefile wiring, and the
  corrected item-1/item-6 containment pin.
- Ran the full relevant regression set together
  (`test_working_log_content_duplicate_check.py` + `test_working_log_duplicate_check.py` +
  `test_validate_working_log.py`, 33 tests) to confirm items 1/2/6 remain mutually consistent — all
  passing. `make working-log-content-duplicate-check` and `make working-log-duplicate-check`
  confirmed end-to-end via the actual Makefile targets, not just pytest.

## Files Changed
- `tools/agent-monitoring/validate.py` — item 3a/3b race-free reads
- `tools/agent-monitoring/agent_tool_usage_baseline.py` — item 3a wiring
- `tests/tools/test_agent_tool_usage_baseline.py` — item 3a/3b tests
- `tools/validate_working_log.py` — item 2 exclusion removal
- `tests/tools/test_validate_working_log.py` — item 2 test flip
- `tools/gate_checks/working_log_duplicate_check.py` (new) — item 1 wiring
- `.gitignore`, `.claude/.epic_staleness_state.json` (untracked) — item 4
- `tools/agent-monitoring/epic_staleness_check.py` — item 5 shard-aware fix
- `tests/tools/test_epic_staleness_check.py` — item 4/5 tests
- `tools/gate_checks/working_log_content_duplicate_check.py` (new) — item 6
- `tests/tools/test_working_log_content_duplicate_check.py` (new) — item 6 tests
- `Makefile` — `working-log-duplicate-check` and `working-log-content-duplicate-check` targets

## Completion Summary
All six defects fixed and independently re-verified by the peer session across the batch. All
counts cited in the original ticket were re-measured at implementation time per the ticket's own
Acceptance Criteria and corrected where they had drifted (item 6: 45→46; item 1: the ticket's 57
was the pre-item-2-fix figure, the live post-fix ratchet is 84; the item 1/item 6 "mostly disjoint"
relationship the ticket's own AC asserted no longer holds post-item-2-fix — now full containment,
for the reason recorded in Implementation Notes above). Two items (1 and 6) were converted from
zero-tolerance to ratchet checks per their own Acceptance Criteria, following the established
precedent from `TCK-20260913-PARITY-BASELINE-EQUALITY-GATE-PENALIZES-IMPROVEMENT` — both would
have been immediately unlandable as hard gates given the pre-existing corpus. All 6 items' own
acceptance criteria are checked off above with the corrected, current numbers.
