---
status: active
layer: testing
authority: P2
audience: agent
date: 2026-10-08
tags: [delivery, planning]
---

# Import-linter soak review (INTERIM, 2026-10-08)

Covers `TCK-20261005-IMPORT-LINTER-FLIP-AND-TEST-RETIREMENT` (scope bullet 1, acceptance criterion 1). Window: from
`e9585eb02` (PR #351 merged, 2026-10-05T13:40:06Z) to 2026-10-19T13:40Z. This draft reads the window up to
2026-10-08 (`origin/main` `0d75424dc`, 3.9 days of 14); the flip ticket finishes it on 2026-10-19. Method as in
`python_code_craft_structure_soak_review.md`, with one difference: the `Code health` job logs **were** readable through
`gh api repos/<r>/actions/jobs/<id>/logs` in this session, so each run's outcome below is the step's own summary line
`**Import contracts (advisory):** N kept, M broken`, not an annotation. The log carries only that count line, not the
contract names or module pairs; those were obtained by running `lint-imports` at the same commit (section 3).

## 1. Runs on main

`Tests` workflow, `push` events on `main`, every run created at or after `e9585eb02` (87 runs; the one run before it,
on `0b3023d7a`, is outside the window; its `Code health` job is not counted). The job is `Code health (advisory)` in the first two runs and `Code health`
afterwards; the step name is `Import contracts` throughout.

| Outcome (run conclusion `success` or `failure`) | Runs |
|---|---|
| `17 kept, 0 broken` | 48 |
| `16 kept, 1 broken` | 11 |
| counted total | 59 |
| cancelled (listed, not counted) | 28 |
| all runs in the window | 87 |

The 28 cancelled runs are superseded pushes. In 24 of them the `Code health` step had already finished with
`17 kept, 0 broken` before the cancel; in the other 4 the job was cancelled before the step reported: `6334efe98`
(2026-10-07T04:01Z), `1e67cba52` (2026-10-07T07:14Z), `3a9f93c33` (2026-10-08T02:40Z) and `5216cb1c4`
(2026-10-08T11:43Z). `3a9f93c33` is the KNOW-04 commit (#412) that introduced three of the breaks in section 3, so its
own run never reported; its breaks were first seen on the next commit. None of the 28 shows a broken contract.

Step conclusion was `success` in all 59 counted runs: the step is advisory and exits 0, so a broken contract never
failed a run or a PR. (The 11 counted runs that ended `failure`, including `e9585eb02` and `eb5ebf03b`, failed on
`Slow regression`, not on this step, and all reported `17 kept, 0 broken`.)

Broken runs, in order. Every one is `16 kept, 1 broken`; the count is **contracts, not module pairs** (see the surprise in
section 3).

| Run | Commit | Created (UTC) | What broke (from `lint-imports` at that commit) |
|---|---|---|---|
| 37587585899 | `7a39acc5d` (#406) | 2026-10-07T07:28:59Z | core -> ai (1 pair) |
| 37588837614 | `6e7ef56ec` | 2026-10-07T07:40:59Z | same 1 pair |
| 37605524379 | `0a03c2448` | 2026-10-07T10:09:32Z | same 1 pair |
| 37617405823 | `ae3352361` | 2026-10-07T11:55:39Z | same 1 pair |
| 37640555117 | `05460b139` | 2026-10-07T14:53:48Z | same 1 pair |
| 37645752611 | `75225fd51` | 2026-10-07T15:40:03Z | same 1 pair |
| 37648230040 | `a514e2025` | 2026-10-07T15:57:47Z | same 1 pair |
| 37715748058 | `57ae37c85` (#413) | 2026-10-08T02:00:44Z | same 1 pair |
| 37716593688 | `c2e18b182` (#414) | 2026-10-08T02:10:49Z | 2 pairs (core -> ai, engine -> ai) |
| 37719069533 | `33360e617` (#417) | 2026-10-08T02:41:03Z | 5 pairs |
| 37720583589 | `71f8f2e9e` (#419) | 2026-10-08T02:59:52Z | 5 pairs |

- **First broken run:** `7a39acc5d` (PR #406), 2026-10-07T07:28:59Z.
- **Last broken run:** `71f8f2e9e` (PR #419), 2026-10-08T02:59:52Z.
- **First clean run after #420:** `753f98ea9` (PR #420), 2026-10-08T03:17:02Z, `17 kept, 0 broken`. All 19 counted runs
  after it, up to `0d75424dc` (2026-10-08T11:43:34Z), are clean (plus cancelled ones that also showed clean).
- Clean before the first break: `c8c355459` (#329), `f8f1b69fd`, `80811968a`, and the two earliest runs
  `e9585eb02` and `eb5ebf03b`: all `17 kept, 0 broken`.

## 2. Broken-contract runs on PRs

`Tests` run on each PR's last head commit, `Code health` job, `Import contracts` step:

| PR | Head | Merged (UTC) | Result on the PR head |
|---|---|---|---|
| #406 | `6f622e2c4` | 2026-10-07T07:28:57Z | `16 kept, 1 broken` |
| #412 | `a64b2344f` | 2026-10-08T02:40:19Z | `16 kept, 1 broken` |
| #414 | `ac1f9b7f9` | 2026-10-08T02:10:46Z | `16 kept, 1 broken` |
| #420 | `5fb6891e3` | 2026-10-08T03:17:00Z | `17 kept, 0 broken` |

Each of #406, #412 and #414 merged with the advisory step showing the break, as designed. Not scanned: the other PRs
that touched `src/` in the window (the main-branch runs in section 1 cover every merged commit).

## 3. Breaks found

All 5 module pairs are **real** layer-order violations (the `Registry layer order` contract), not false positives. All
were fixed in #420 (`753f98ea9`, `TCK-20261008-CORE-STRATEGIC-IMPORTS-AI-GOALS-FOR-A-TYPE-HINT`), whose diff touches
nothing under `codebase/`: no `ignore_imports` entry and no baseline line was added. See
`handoffs/handoff_to_rpg.md` "Update 2026-10-08".

| # | Pair (importer -> imported) | Introduced by | Introduced (UTC) | Fixed | Time on main |
|---|---|---|---|---|---|
| 1 | `src.core.strategic -> src.ai.goals.base` (l.11, `TYPE_CHECKING`) | #406 `7a39acc5d` | 2026-10-07T07:28:56Z | #420 `753f98ea9`, 2026-10-08T03:16:59Z | about 19 h 48 min |
| 2 | `src.engine.tactical_rest -> src.ai.goals.need_pull` (l.17) | #414 `c2e18b182` | 2026-10-08T02:10:46Z | #420 | about 1 h 06 min |
| 3 | `src.worldbuilding.compiler -> src.cognition.common_knowledge` (l.12) | #412 `3a9f93c33` (KNOW-04) | 2026-10-08T02:40:19Z | #420 | about 37 min |
| 4 | `src.worldassembly.entity_spawner -> src.cognition.common_knowledge` (l.5) | #412 `3a9f93c33` | 2026-10-08T02:40:19Z | #420 | about 37 min |
| 5 | `src.cognition.common_knowledge -> src.engine.behavior_consumers` (l.25) | #412 `3a9f93c33` | 2026-10-08T02:40:19Z | #420 | about 37 min |

How #420 resolved them (from its diff): `with_live_current_score` in core no longer imports `src.ai` (a `Protocol` in
`src/core/strategic.py`); `need_pull.py` moved from `src/ai/goals/` to `src/engine/`; the KNOW-04 seeding moved to the new
`src/content/common_knowledge_seed.py` so the compiler and spawner no longer import cognition; and
`src/engine/behavior_consumers.py` now installs the catalog provider (`install_warm_catalog_provider`) so
`common_knowledge` no longer imports it.

**Surprise worth acting on: the CI count under-reports.** The step line says `1 broken` for the whole window, but that
counts contracts, not pairs. `lint-imports` at `33360e617` and `71f8f2e9e` lists 5 broken pairs inside that one contract,
and the line stayed `16 kept, 1 broken` while the pair count went 1 -> 2 -> 5. Nothing in the job log or annotations
names the pairs (only `lint-imports` itself does, and the advisory step prints just the count). Once the step is
blocking this does not matter for pass/fail, but while it is advisory a reader of the summary line cannot tell that a
second or third break arrived on top of an open one. The planner decided on 2026-10-08 that the summary must name the broken pairs and that this is in the flip ticket's scope;
it is not a false positive and no config changed here.

Each of #414 and #412 was written while #406's break was already open on main and visible only as the same count, which
is how the number of open breaks grew from 1 to 5 inside about 20 hours without the summary line changing.

## 4. Stale `ignore_imports`

At `origin/main` `0d75424dc` (this branch's base), run once under a 2 GB memory cap:

- `uvx --from import-linter==2.15 lint-imports --config codebase/structure/importlinter.toml`: exit 0,
  `Contracts: 17 kept, 0 broken.` No unmatched-ignore warning (`unmatched_ignore_imports_alerting = "warn"` is set on
  every contract) and no other warning in the output. `Registry layer order` reports 135 ignored imports, equal to the
  135 lines of `codebase/structure/import_layers_baseline.txt`; the other contracts report 4, 6, 7, 4, 9, 4 and 1 ignored
  imports, all matched.
- `python3 -m codebase.structure.import_contracts --check`: `import contracts: up to date`, exit 0 (the generated block
  matches the registry and the baseline).

Nothing is stale. #420 moved `need_pull.py` and added `common_knowledge_seed.py`, but no baselined pair involved either
module, so no entry became unmatched. Report only; no config changed.

## 5. False-positive classes

None so far. The contracts count a `TYPE_CHECKING` import on purpose (`exclude_type_checking_imports = false`, see the
header of `codebase/structure/importlinter.toml`: a contract may not be looser than the test it replaces). The
`src.core.strategic -> src.ai.goals.base` finding is the case that rule exists for: the import is annotation-only, yet
it closes a real loop (`src/ai/goals/base.py` imports `GoalKind` from `src.core.strategic`). All 5 findings in the window
were real and fixed at the source. No contract was relaxed and no `ignore_imports` or baseline entry was added during
the window.

## 6. Verdict (interim, 2026-10-08)

No false-positive class and no stale entry so far; 5 real breaks were found and fixed by the code owner within 37 min to
about 20 h, with no baseline added. The evidence is 3.9 of 14 days, so the flip is not yet supported on soak alone.
Remaining before the flip (earliest 2026-10-19T13:40Z):

1. The window's remaining runs on `main` to 2026-10-19T13:40Z, re-read the same way (count line per run, then
   `lint-imports` at any broken commit), and a re-run of section 4 at the flip commit.
2. The owner's yes to making the step a required check on `main` (ruleset change and merge in one sitting; never before
   `main` has produced the check name).
3. `phase19`'s `test_hot_path_does_not_import_heavy_analyzers` still waits on rpg's decision about `kernel.py`'s
   function-local imports (`handoff_to_rpg.md`); it is an expectation change, not a retirement.
4. Decided 2026-10-08 (codebase-planner): the summary names broken pairs; in the flip ticket's scope.
