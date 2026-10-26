---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261023-PAIRED-ARMS-RUN-OFF-THE-SHARED-HOST
phase: open
date: 2026-10-23
tags: [testing, performance, determinism]
---

# TCK-20261023-PAIRED-ARMS-RUN-OFF-THE-SHARED-HOST

## Title
Paired arms can run on GitHub-hosted runners through a testing-owned workflow_dispatch workflow, and their results are compared by the existing paired.py

## Status
INPROGRESS

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Draft T2 of `docs/plans/architecture/faster_feature_testing_draft_tickets.md` (#719, #724), filed by testing-planner with the split agreed with rpg-planner on 2026-10-23.

`tools/rpg_measure/paired.py` defaults to `--jobs 2` ("the reaper kills at 3 heavy processes"). The shared u24 host has 6 cores and 8.7 GB, swap is full and there was a global OOM on 2026-10-22, so a 5-seed step takes about 2-3 h and blocks other work. The gate already shards per world on CI (`rpg-gate-report.yml`), but paired arms have no CI path.

Platform's runner facts (#593 issuecomment-6345851046):
- no self-hosted runner exists;
- GitHub-hosted is 4 vCPU / 16 GB with a 6 h job limit, and free on a public repo;
- the CPU model varies, so runner identity is a description and not a pinned machine;
- both arms of a pair should run in the same job on one VM.

**Split (rpg-planner, 2026-10-23):**
- testing owns the workflow;
- rpg WRITES the `paired.py` "compare collected results" option and testing reviews it (rpg child ticket);
- `arm_child.py` is unchanged.

## Scope
1. `.github/workflows/paired-arms.yml` (testing-owned).
   - Trigger: `workflow_dispatch` only. Inputs: `base_sha`, `new_sha`, `step`, `worlds`, `seeds`, `ticks` and `self_check` (seed42 | full | off).
   - Concurrency `paired-arms-${{ inputs.step }}`, `cancel-in-progress: false`.
   - Pinned actions by SHA, per the pin guard.
2. A matrix over (world, seed). Each job:
   - checks out both SHAs into separate trees;
   - runs BOTH arms on that VM through the unchanged `arm_child.py`, with `PYTHONHASHSEED=0` and the same cache key `<sha>-<child hash>-<ticks>`;
   - writes the arm documents plus a runner-identity record: `runner.name`, image name and version, CPU model, nproc, MemTotal, Python version, OS. This is recorded once per job;
     (changed 2026-10-26 at rpg-planner's request, accepted by testing-planner: the record is written beside EACH result as `<world>_<seed>.cost.json` `runner`, per the contract of rpg's TCK-20261026-PAIRED-COMPARES-COLLECTED-OFF-HOST-RESULTS, because the merged layout has no per-job directory and the repeat arm is its own result);
   - uploads `paired-arms-<step>-<world>-s<seed>`.

   The base-vs-base self-check runs the same way, as its own matrix entries.
3. An aggregate job downloads every arm artifact and runs `paired.py`'s collected-results option (rpg's). It writes the step's verdict to the step summary and uploads it. That option must still apply `require_host_independent_runs` / `--legacy-base` and the STOP rule unchanged (rpg's condition).
4. **Identity rule (PERF-D2 / DET-PORT-0):**
   - base and new arms of one (world, seed) always come from the same job;
   - the aggregate refuses to compare arms whose runner-identity records differ in Python version or OS;
   - an off-host result is never compared with a local result, except in AC1's one-time equality proof.
5. Every arm run's `wall_seconds` and `peak_rss_mb` go into the job's result. If TCK-20261023-MEASURED-STEP-RUN-AND-RERUN-LEDGER is on main, a ledger row goes in the aggregate artifact too.
6. The workflow is never a required check (roadmap principle 8), and it never runs on `pull_request` or `push`.

## Out of Scope
- Changing what paired runs measure or prove, the STOP rule or the stats.
- A self-hosted runner (a platform ticket plus an owner decision on hardware).
- Writing the paired.py option (rpg).
- Running the gate through this workflow (the gate already has rpg-gate-report.yml).

## Acceptance Criteria
- [ ] AC1: on one real step (rpg names it), the off-host verdict document equals the local one byte for byte, apart from the runner-identity and wall-time fields, which are listed explicitly. The comparison command and both outputs go in Test Summary.
- [x] AC2: the runner identity is recorded with the results, and the aggregate refuses a mixed Python version or OS, with a test on fake artifacts.
- [ ] AC3: per-arm wall time and peak RSS are in the results (T1).
- [x] AC4: the workflow is pinned (the pin guard passes), it is `workflow_dispatch`-only, and a static test asserts that it has no `pull_request` / `push` trigger and that its concurrency does not cancel.
- [ ] AC5: rpg's collected-results option (its own PR) is reviewed by testing-planner, and the STOP and host-independence refusals are tested there.

## Related Tickets
- TCK-20261023-MEASURED-STEP-RUN-AND-RERUN-LEDGER (T1)
- the rpg child ticket for the paired.py collected-results option (rpg-planner files it)
- T3, `no_replay` for paired arms (rpg files it and implements it; testing-planner reviews). The gate stays in Mode 1 until T3's proof passes.

## Related Docs
- docs/plans/architecture/faster_feature_testing_draft_tickets.md (T2)
- docs/plans/architecture/engine_execution_modes_proposal.md §6 (T2 runner facts)
- docs/plans/architecture/conformance_suite_design.md §8

## Related Stored Artifacts
- none

## Related Code Areas
- .github/workflows/paired-arms.yml (new)
- tools/rpg_measure/paired.py, arm_child.py (rpg; read-only here)

## Assumptions / Open Questions
- The GitHub Actions minutes cost for a 5-seed step is unmeasured. AC1's run measures it. If one step needs more than 3 runner-hours, tell the owner before the second use.

## Implementation Notes
Testing half built 2026-10-26; see the staging investigation.md / plan.md. Contract with rpg-planner for `paired.py --collected` is recorded there (cost.json per result with the runner record; `--verdict-json`; exit 0/1/2; one extra `- runners:` line). Choices beyond the ticket text: runner identity lives in each result's cost.json (rpg's request), not a per-job file; a boolean `legacy_base` input passes `--legacy-base`; `--neutral`, `--report-only`, `--legacy-new`, `--div` are not offered; the plan job imports paired.py's WORLDS and TERRAIN_WORLD (no copy, per testing-planner). The aggregate calls rpg's option and fails with a clear message until it is on main. The T1 ledger row waits for T1 on main.

## Test Summary
- tests/static/test_ci_paired_arms_workflow_shape.py (new, 10) and tests/unit/tools/test_paired_arms.py (new, ~30, fake artifacts): pass, with the rest of tests/static (196 passed together with the workflow-support tests). AC2 refusals (mixed Python or OS) tested on fake artifacts; AC4 static test and the pin and context guards cover the workflow.
- AC1 (off-host table equals the local one except the `- runners:` line) and AC3's ledger row are pending: they need a dispatch on main after rpg's `--collected` and T1. No heavy run was done locally.

## Files Changed
- .github/workflows/paired-arms.yml (new)
- tools/test_architecture/paired_arms.py (new)
- docs/plans/test_architecture/reference/paired_arms_off_host.md (new)
- tests/static/test_ci_paired_arms_workflow_shape.py (new)
- tests/unit/tools/test_paired_arms.py (new)
- tests/static/test_workflow_actions_pinned_by_sha.py, tests/static/test_workflow_run_blocks_take_github_context_via_env.py (cover the new workflow)

## Completion Summary
OPEN. The testing half is built (AC2, AC4). AC1 needs a real dispatch after rpg's TCK-20261026-PAIRED-COMPARES-COLLECTED-OFF-HOST-RESULTS and T1 are on main; AC5 is testing-planner's review of rpg's PR; AC3's ledger row waits for T1.
