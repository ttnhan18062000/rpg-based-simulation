---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261026-PAIRED-COMPARES-COLLECTED-OFF-HOST-RESULTS
artifact_type: plan
tags: [testing, performance, determinism]
---

# Plan: paired --collected

The CLI contract is the ticket's Scope 1 to 4 and is not changed.

## Code (tools/rpg_measure/paired.py only)
1. **Flags.** `--collected DIR` and `--verdict-json PATH`. `--jobs` default moves from 2 to None (resolved to 2 in local mode) so an explicit `--jobs` can be told from the default. With `--collected`, `ap.error` (exit 2) on: `--jobs`, `--clean-cache`, a `--base`/`--new` that is not 40 lowercase hex.
2. **Expected job set** from one helper used by both modes: worlds x seeds; `check_jobs` per `--self-check` (off: none; full: all; seed42: (w,42)); legacy-new repeat of the new arm over `check_jobs`; `--neutral` at NEUTRAL_TICKS, 3 worlds x seed 42, both arms. Local mode is unchanged (it keeps `run_arm`); collected mode calls `load_collected(cache, sha, jobs, ticks, repeat)`, which only reads `result_path(...)`.
3. **Missing result** -> collect every missing (arm, world, seed, repeat) across all arms first, print `REFUSED: missing results for ...` listing each key, return 2. Nothing is executed, nothing is unlinked (the local repeat `unlink` stays in `run_arm`, never reached).
4. **Cost and identity.** `cost_path(result)` = `<world>_<seed>.cost.json` beside the result. `load_cost` returns None when absent or unreadable-as-absent (null wall/RSS, not a refusal). Per (world, seed), the base, new and repeat costs that exist must agree on `runner.python`, `runner.os`, `runner.image`; otherwise REFUSED (2) naming the key and the differing fields. The report gets one `- runners:` line (distinct name/image/python/os, in collected mode only), so local output is byte-for-byte unchanged.
5. **Verdict JSON** `{"outcome","mode","detail"}`: mode is `neutral`, `report_only`, else `step`. Outcome: REFUSED for any exit-2 path and for `NonAuditRunError` (the exception still propagates, exit behaviour unchanged); STOP when not report-only and any world row has verdict STOP or non-empty extinction stop (neutral: a differing hash); else PASS. `detail` names the stopping worlds or the refusal reason, else null. Written in both local and collected mode. Exit codes unchanged (0 report produced, 2 REFUSED, neutral FAIL stays 1).
6. **Structure.** The body of `main` moves into `_run(a, verdict)` that fills a verdict dict; `main` wraps it and writes the JSON in a `finally`. No change to `world_section`, `watch_rows`, `stats`, `arm_child.py`.
7. **Docstring:** the off-host jobs must run `arm_child.py` from the same tool commit as the aggregate job, because `child_hash()` (sha256 of the tool checkout's arm_child.py) names the result directories.
8. Item 5 of the ticket (ledger rows with cached=false and cost.json wall/RSS) is left to the hook ticket; `load_cost` is the seam.

## Tests (tests/unit/tools/test_rpg_measure.py or a sibling file; staged result JSON, no simulation)
missing result REFUSED with keys; mismatched python, os and image each REFUSED; repeat file survives; `--jobs` and `--clean-cache` rejected; short sha rejected; verdict-json values for PASS, STOP, REFUSED, report_only (and neutral); missing cost.json gives null wall/RSS; local and collected give the same table on one staged cache (runner line excluded).

## Byte-identical AC (after Lane A's run exits)
Read-only: `python -m tools.rpg_measure.paired --collected /mnt/data/scratch-rpg-measure ...` with the full shas of an existing cached step, diffed against the local-mode table for the same step (the local run is also from cache, so nothing executes). No new runs.

## Out of scope
Workflow, matrix, merge, identity pre-check; any change to what paired measures.
