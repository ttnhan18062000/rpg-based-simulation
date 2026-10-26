---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261026-PAIRED-COMPARES-COLLECTED-OFF-HOST-RESULTS
phase: inprogress
date: 2026-10-26
tags: [testing, performance, determinism]
---

# TCK-20261026-PAIRED-COMPARES-COLLECTED-OFF-HOST-RESULTS

## Title
paired.py compares arm results collected off this host (`--collected DIR`), never executing a run

## Status
INPROGRESS

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
This is the rpg half of T2, TCK-20261023-PAIRED-ARMS-RUN-OFF-THE-SHARED-HOST. Draft: docs/plans/architecture/faster_feature_testing_draft_tickets.md §T2. testing-implementer builds `.github/workflows/paired-arms.yml`:
- one matrix job per (world, seed), running the unchanged `tools/rpg_measure/arm_child.py` with cwd=tree, PYTHONPATH=tree and PYTHONHASHSEED=0;
- results written in paired's own cache layout;
- an aggregate job that merges the artifacts and runs paired's comparison.

paired.py today always executes missing arms locally. This ticket adds a load-only comparison mode. The CLI contract below was agreed with testing-implementer on 2026-10-26, so do not change it without telling testing.

## Scope
1. `--collected DIR`: DIR is a paired cache root. `DIR/results/<sha12>-<child hash8>-<ticks>[-repeat]/<world>_<seed>.json` is the existing layout.
   - `--base` and `--new` must be full 40-hex shas. There is no git call and no tree extraction, so `--repo` is not needed.
   - Nothing is executed.
   - A missing result returns REFUSED (exit 2) and lists the missing (arm, world, seed) keys.
   - A repeat result is read, never unlinked. The local repeat path unlinks first, and `--collected` must not.
   - `--jobs` and `--clean-cache` are rejected together with `--collected`.
   - The expected job set is derived from the flags exactly as it is locally (worlds × seeds; the -repeat set per `--self-check`; `--legacy-new` repeat; `--neutral` at NEUTRAL_TICKS).
2. The child hash is sha256 of the TOOL checkout's `arm_child.py`, unchanged. Document in the module docstring that the off-host jobs must run arm_child.py from the same tool commit as the aggregate job.
3. A cost and identity file sits beside each result: `<world>_<seed>.cost.json` = `{"wall_seconds": float, "peak_rss_mb": float|null, "runner": {"name","image","cpu_model","nproc","mem_total_mb","python","os"}}`.
   - REFUSED (exit 2) if runner.python, runner.os or runner.image differ across the base, new and repeat results of any key. This is the DET-PORT-0 condition.
   - A missing cost.json is not a refusal: that run's wall and RSS are null.
   - The report gains one runner line.
4. `--verdict-json PATH` (also valid in local mode) writes `{"outcome": "PASS"|"STOP"|"REFUSED", "mode": "step"|"neutral"|"report_only", "detail": str|null}`. The values match run-ledger/v1. Exit codes are unchanged: 0 = the report was produced (STOP is in the table), 2 = REFUSED.
5. Once TCK-20261023-PAIRED-WRITES-ONE-RUN-LEDGER-ROW-PER-INVOCATION lands, collected runs are written as runs[] with cached=false and wall/RSS taken from cost.json. That wiring belongs to the hook ticket if it lands second.

## Out of Scope
- The workflow, matrix, artifact merge and identity pre-check (testing, T2).
- Any change to what paired measures or to its verdict rules.
- Making the job a required check.

## Acceptance Criteria
- On one real step, a `--collected` run over the cache a normal local run produced gives a table byte-identical to the local run except the one `- runners:` line (planner ruling 2026-10-26; the unit test asserts the diff is that single line).
- Unit tests cover:
  - a missing result is REFUSED with its keys;
  - a mismatched runner python, os or image is REFUSED;
  - a repeat file is not deleted;
  - `--jobs` and `--clean-cache` are rejected with `--collected`;
  - a short sha is rejected;
  - the verdict-json values match for PASS, STOP, REFUSED and report_only;
  - a missing cost.json gives null wall/RSS.
- The local mode's output is unchanged: the same table on the same cache.

## Related Tickets
- TCK-20261023-PAIRED-ARMS-RUN-OFF-THE-SHARED-HOST (testing, T2)
- TCK-20261023-PAIRED-WRITES-ONE-RUN-LEDGER-ROW-PER-INVOCATION (T1 hook)
- TCK-20261023-MEASURED-STEP-RUN-AND-RERUN-LEDGER (testing, T1)
- TCK-20261023-PAIRED-ARMS-RUN-WITHOUT-THE-PER-TICK-REPLAY-DIGEST (T3)

## Related Docs
- docs/plans/architecture/faster_feature_testing_draft_tickets.md (§T2)

## Related Stored Artifacts
- none

## Related Code Areas
- tools/rpg_measure/paired.py (main, run_arm, result_path, neutral)
- tools/rpg_measure/arm_child.py (read only: child hash)

## Assumptions / Open Questions
- The PERF-D2 tier note in the T2 draft: a CI runner stays DET-PORT-0 only if its runtime identity matches. The python/os/image refusal enforces this on the rpg side, and testing also pre-checks it.

## Implementation Notes
Owner Lane B (`rpg-implementer-2`), branch `rpg-paired-collected`, dispatched by `rpg-planner` 2026-10-26. Plan in `agent-working/staging_artifacts/TCK-20261026-PAIRED-COMPARES-COLLECTED-OFF-HOST-RESULTS/plan.md`.

## Test Summary
Unit: `tests/unit/tools/test_rpg_measure_collected.py` (14 test functions, 18 cases with the parametrized ones, staged results, no simulation) plus the existing `test_rpg_measure.py`: 31 pass. Local mode checked against `origin/main`'s paired.py on a staged cache for the default, `--self-check full|off` and `--report-only`: identical output and exit code. Real step (2026-10-26, read-only): `--collected /mnt/data/scratch-rpg-measure --base 341f700d0b54ab00deab0f9b84f87321f101ca48 --new 265162719fa74e059931d52b82d321606873c2bc --step an-acting-hostile --self-check seed42` gives exit 0, verdict-json STOP/step (crowded_frontier), and `diff` against Lane A's local table (`/mnt/data/scratch-rpg-implementer/stepB/paired`) shows exactly one added line, the `- runners:` line ("none recorded": that cache has no cost.json). The tool-checkout `arm_child.py` hash (72320cac) equals 265162719's, so the result dirs matched; nothing was executed or unlinked.

## Files Changed
- `tools/rpg_measure/paired.py` (`--collected`, `--verdict-json`, cost/identity helpers; `main` body moved to `_run`)
- `tests/unit/tools/test_rpg_measure_collected.py`

## Completion Summary
