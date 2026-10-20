---
status: active
layer: testing
authority: P2
audience: agent
tags: [architecture, delivery, planning]
---

# Brief: batch `import-linter-flip` (codebase-planner → codebase-implementer)

Written 2026-10-10 by codebase-planner on the owner's request, so the batch can start the moment the soak ends.
**Earliest start: 2026-10-19T13:40Z** (two weeks after #351 merged, squash `e9585eb02`, 2026-10-05T13:40:06Z).
One branch: the existing local `import-linter-flip` (worktree `~/Work/rpg-import-linter-flip`, base `0d75424dc`,
head `54f923283`, two reviewed commits: interim soak review + flip-ticket scope edit). One PR. Commit only. The
owner says yes to push, PR and merge, each in your own session.

## Step 0: before any code (on or after 10-19T13:40Z)

1. Merge `origin/main` into `import-linter-flip`. The base is 11+ days old. Report the merge sha.
2. `make import-contracts` (or `python3 -m codebase.structure.import_contracts advisory` with `.venv/bin` on PATH) on
   the merged head. Expect `17 kept, 0 broken`. If anything is broken, stop and report: the flip waits until
   the owning domain fixes it, or the owner accepts it into the baseline. **Never baseline a break yourself to make the flip pass.**
3. Check `docs/plans/codebase_health/handoffs/handoff_to_rpg.md` (around line 237) and rpg's replies for an answer to
   **testing condition 3** (`kernel.py` function-local imports at 149/304/305/316/1241: allowed with a reason, or an
   engine ticket). As of 2026-10-10 there is **no answer**. If there is still none, rule 2 (phase19) stays a test and
   its `ignore_imports` reason stays "pending rpg decision".

## Ticket 1: `TCK-20261005-IMPORT-LINTER-FLIP-AND-TEST-RETIREMENT` (standard; move it from todos/ to inprogress/)

### 1a. Finish the soak review (`docs/plans/codebase_health/import_linter_soak_review.md`)
- Sections 1–3: extend the run tables from 2026-10-08 to the 10-19 cut-off: main runs, PR runs with a broken
  contract, and each break found with its cause and its fix PR. The job summary shows only the count, so get the
  pairs by running `lint-imports` at that commit (your handover has the recipe).
- Section 4: re-run the stale-`ignore_imports` check on the merged head.
- Section 5: false-positive classes. AC: none open.
- Section 6: verdict FINAL, date it, and drop "INTERIM" from the title.

### 1b. Name the broken pairs (already in the ticket's scope, commit 54f923283)
The step summary and annotations list each broken contract's pairs (importer -> imported, line). A test pins a
contract with 2+ broken pairs, and every pair must appear.

### 1c. Make the step blocking
- **Correction to the ticket text.** The ticket says "the owner adds the check as required on `main`". The step is
  part of the `Code health` job, and that job has been a required check since 2026-10-06 (ruleset 14220945). So
  **there is no ruleset change and no new required-check name.** "Required" here means the step can fail
  `Code health`. Rewrite that scope line and AC 2 to say so. AC 2 then becomes "owner's yes to making the step
  blocking, recorded with date and who". It is still the owner's yes, just not a settings change.
- Add a blocking mode to `codebase.structure.import_contracts` (keep `advisory` for local use), e.g. `ci`:
  - exit 1 on a broken contract or a stale `ignore_imports` entry;
  - exit 2 when it cannot run, which fails the job. This matches the `Package registry` step, where exit 2 fails `Code health`.
  - It keeps the summary and annotations, with `::error::` instead of `::warning::`.
- `test.yml`: switch the step to that mode and remove its `continue-on-error`. Update the comment, which says "advisory
  and never blocking". `test.yml` is testing's file, so this edit goes under decision 8.11, with a notice (1f).
- Tests:
  - unit tests for the exit codes (broken / stale / could not run / clean);
  - the static workflow pins that encode "this step is advisory" (`tests/static/test_ci_uv_install.py` and its
    `continue-on-error` allowlist, and any other pins you find), updated under 8.11;
  - a test that the step is blocking: a required check must be able to fail.
- Live proof: the gates flip used a throwaway draft PR (#331) with an injected import. Do the same here: a probe
  branch off the batch head with one injected layer break. It needs the owner's yes; I'll ask. Show that
  `Code health` fails at `Import contracts` with the pair named. Never merge it, and delete it after an owner yes.

### 1d. Retire the class E tests whose contract is now required (testing conditions 1, 2, 4)
- Condition 1 holds within this PR, because the step becomes blocking in the same PR.
- **Retire only where the contract catches everything the test catches.** Re-run the parity table on the
  merged head in a scratch copy (`git archive`), as in `TCK-20261004-IMPORT-LINTER-ADOPTION`'s Test Summary. For
  each retired test, show the injected violation and the contract going BROKEN on it (condition 2). Any row where
  the test FAILS and the contract stays KEPT blocks that test's retirement: report it, don't retire it.
- Rule 2 / phase19 `test_hot_path_does_not_import_heavy_analyzers`: **not retired** unless condition 3 was answered
  (step 0.3). Even then, it's an expectation change routed to testing, not a retirement.
- Out of scope, unchanged from the ticket: the 42 rules that stay tests, and the `or True` assert at
  `tests/unit/observability/test_decision_trace.py:376`.
- Retired files live under `tests/architecture/` (testing-planner's route), so the 8.11 notice in 1f lists every
  removed node id and its replacement contract id.

### 1e. Docs
- `docs/guidelines/agent_working_environment.md`, "Reading the import-contract result (advisory)": rewrite it for
  blocking.
- Roadmap: the M5 row and decision 8.20.
- `import_linter_evaluation.md` if it states advisory as current.
- `infrastructure.yaml` parity entry only if the other codebase gates have one (same rule as adoption).

### 1f. Handoffs
- `handoff_to_testing.md`: one `## Update 2026-10-19 (import-linter flip): decision 8.11 notice`. It covers the
  `test.yml` step change, the edited static pins, the retired tests (node id → contract id, parity rows), and
  whether phase19 stayed.
- `handoff_to_rpg.md`: one line. Contracts are blocking from this merge, so a new layer break fails `Code health`;
  fix it in your PR, or ask the codebase planner for a baseline entry with a reason. Condition 3 still open (or answered).

## (Moved) Ticket 2: mypy exact pin
T2 landed standalone as `TCK-20261012-MYPY-DEV-PIN` (PR #N, branch `mypy-dev-pin`), with one `uv.lock` metadata line. It is no longer in this batch.

## (Moved) Parity-ledger baseline tighten
Moved out of this batch on 2026-10-10. It ships now, with the closure of `TCK-20261003-PARITY-LEDGER-REMEDIATION-EPIC` (owner decision 2026-10-10).

## Close-out
- Hand-orchestrated closure for each ticket: `record_hand_orchestrated_closure.py`, which writes the working_log row,
  so don't write a second one. Then `done_checker_static.py --ticket-id`, the mechanism-registry advisory, and
  `make knowledge-index-update`. If that times out, say so in the PR body.
- Standard-tier ticket 1 needs `plan/investigation/test_plan` in `stored_artifacts`, including a `## Proof Plan`.
- Stage `docs/REGISTRY.yaml` and `agent-monitoring/`. Use `pr_render.py`. Run `git status -sb` before every push question.
- `git diff --stat origin/main...HEAD`: nothing under `src/`.
- After the merge, report to me. The re-check of main's first runs after the flip is mine.
