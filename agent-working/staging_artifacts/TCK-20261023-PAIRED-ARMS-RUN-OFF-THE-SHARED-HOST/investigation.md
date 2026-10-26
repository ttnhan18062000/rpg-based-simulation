---
status: active
layer: testing
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261023-PAIRED-ARMS-RUN-OFF-THE-SHARED-HOST
phase: open
date: 2026-10-26
tags: [testing, performance, determinism]
---

# TCK-20261023-PAIRED-ARMS-RUN-OFF-THE-SHARED-HOST: investigation

## Facts read from the code (2026-10-26)
- `paired.py` caches by `<sha12>-<child hash8>-<ticks>[-repeat]/<world>_<seed>.json`; the child hash is `sha256(arm_child.py of the tool checkout)[:8]`. `run_arm` unlinks a repeat before running it and never caches it. `prepare_tree` extracts a commit by `git archive` from `--repo`. `run_one` runs `arm_child.py` with cwd and PYTHONPATH set to the tree and `PYTHONHASHSEED=0`.
- The module imports `src.observability.reporting.run_determinism`, so anything calling it needs the repo checkout and `uv sync` (the plan job does not import paired: it carries the world constants and a test pins their equality).
- The self-check set paired expects: seed 42 of every world for `seed42` (regardless of `--seeds`), every job for `full`.

## Contract with rpg-planner (2026-10-26, rpg ticket TCK-20261026-PAIRED-COMPARES-COLLECTED-OFF-HOST-RESULTS)
`paired.py --collected DIR --base <40-hex> --new <40-hex> ...` reads DIR as a cache root, never executes anything, refuses (exit 2) with the missing (arm, world, seed) keys, rejects `--jobs` / `--clean-cache`. It reads `<world>_<seed>.cost.json` = {wall_seconds, peak_rss_mb|null, runner{name,image,cpu_model,nproc,mem_total_mb,python,os}} beside each result (a missing one is not a refusal) and refuses python/os/image differing between base, new and repeat of a key. `--verdict-json PATH` writes {outcome, mode, detail}. Exit 0 report, 1 neutral mismatch, 2 REFUSED. The table gains exactly one `- runners:` line.

## Design decisions
1. Runner identity lives in each result's cost.json (rpg's request: the merged layout has no per-job directory and the repeat is its own result), not in a per-job runner.json.
2. All arm execution goes through paired's own functions, called from `paired_arms run-arm`, one process per arm so the children's max RSS is that arm's. No copy of the cache key or the child call in testing code or YAML.
3. `assemble` is testing's pre-check (python/os across jobs; python/os/image within a key; both arms of a pair job from the same job; byte-identical overlap), in addition to rpg's identical refusals.
4. A self job re-runs the base arm and its repeat on one VM; its base result must equal the pair job's byte for byte or assemble refuses (that is the self-check failing, reported as such).
5. Inputs reach shell only through `env:` (the context guard); no step pipes a refusable command into tee (the default shell has no pipefail).
6. `legacy_base` is a boolean input added beyond the ticket's seven, because rpg's contract requires the aggregate to be able to pass `--legacy-base`. `--neutral`, `--report-only`, `--legacy-new` and `--div` are not offered.

## Open
- The ledger row in the aggregate artifact waits for T1 on main. AC1 (byte-equality proof on a real step) and AC5 (rpg's PR review) need dispatches and rpg's PR after merge, so the ticket stays open.
