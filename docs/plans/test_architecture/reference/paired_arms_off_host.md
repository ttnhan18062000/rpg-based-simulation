---
status: active
layer: testing
authority: P1
audience: agent
tags: [testing, performance, determinism]
---

# Paired arms off the shared host

`TCK-20261023-PAIRED-ARMS-RUN-OFF-THE-SHARED-HOST` (T2 of `docs/plans/architecture/faster_feature_testing_draft_tickets.md`). Testing owns `.github/workflows/paired-arms.yml` and
`tools/test_architecture/paired_arms.py`; rpg owns `tools/rpg_measure/paired.py` and its `--collected` option (`TCK-20261026-PAIRED-COMPARES-COLLECTED-OFF-HOST-RESULTS`).

**Why.** The shared development host has 6 cores and 8.7 GB, so a 5-seed step takes about 2-3 h and blocks other work. GitHub-hosted runners (4 vCPU, 16 GB, free on a public
repo, 6 h job limit) run the arms in parallel. No self-hosted runner exists; the CPU model varies between runners, so a runner identity is a description, never a pinned machine.

**Use.** Dispatch `Paired arms (off-host)` (manual only, never a required check, never on `pull_request` / `push`) with `base_sha`, `new_sha` (full 40-hex), `step`, and optionally
`worlds` (paired's three, plus `highland_traverse` for `--terrain`), `seeds`, `ticks`, `self_check` (`seed42` | `full` | `off`) and `legacy_base`. Dispatch it only after rpg's `--collected`
option is on main; the aggregate job says so and fails otherwise.

## What runs

1. `plan`: validates the inputs and builds the matrix: a `pair` job per (world, seed), plus `self` jobs for the base-vs-base repeat (seed 42 of every world for `seed42`, as `paired.py` expects whatever `seeds` holds, so `seed42` always adds them; every run for `full`). The world set is paired's own `WORLDS` (+ `TERRAIN_WORLD`), imported at plan time, never copied.
2. `arms`, one job per entry: a `pair` job runs the base AND the new arm on one VM; a `self` job runs the base arm and its `-repeat` on one VM. Each arm goes through `paired_arms run-arm`, which calls paired's own `prepare_tree`, `result_path` and `run_one`: the unchanged `arm_child.py`, `PYTHONHASHSEED=0` and the cache key `<sha12>-<child hash8>-<ticks>`. Every job checks out the same dispatched ref, because `<child hash8>` is the hash of `arm_child.py` in the TOOL checkout, not of the base or new tree.
3. `aggregate`: downloads every artifact, runs `paired_arms assemble`, then `paired.py --collected collected --base … --new … --verdict-json verdict.json --out table.md`.

Each result carries `<world>_<seed>.cost.json` = `{"wall_seconds", "peak_rss_mb" | null, "runner": {name, image, cpu_model, nproc, mem_total_mb, python, os}}` (the contract fixed with rpg-planner on 2026-10-26). A cached arm records `wall_seconds` 0 and no RSS.

## Identity rule (PERF-D2 / DET-PORT-0)

- The base and new arms of one (world, seed) always come from the same job; `assemble` refuses a pair job lacking either.
- `assemble` refuses a set whose jobs differ in Python version or OS, arms of one key that differ in Python, OS or image, and two jobs that wrote different bytes to the same result (for a `self` job, the base arm not reproducing). `paired.py --collected` refuses the same conditions again, so a bypassed pre-check still stops there.
- An off-host result is never compared with a local one, except in AC1's one-time byte-equality proof.

## Exit codes and the AC1 comparison

`paired.py --collected`: 0 report produced (STOP verdicts are in the table), 1 a `--neutral` mismatch, 2 REFUSED. Read `verdict.json` (`{"outcome": PASS|STOP|REFUSED, "mode", "detail"}`, the run-ledger values), not the exit code. The workflow does not offer `--neutral`.
AC1: on one real step, the CI table equals the local table byte for byte except the one `- runners:` line collected mode adds; strip that line before `diff`. Record the command and both outputs in the ticket's Test Summary, and the Actions minutes the run cost (the ticket asks the owner be told if one step needs more than 3 runner-hours).

## Not done here

The run-ledger row (T1) in the aggregate artifact is added once T1 is on main; until then the per-arm wall time and RSS are in the `cost.json` files. Nothing uploads the ledger, and no CI job gates on any of this.
