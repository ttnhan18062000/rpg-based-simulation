---
status: active
layer: testing
authority: P2
audience: agent
date: 2026-10-04
tags: [architecture, delivery]
---

# Import-linter adoption (advisory) — ticket brief

**From:** `codebase-planner`, 2026-10-04. **To:** `codebase-implementer`. Batch branch: `import-linter-adoption`
(own worktree, from `origin/main`). One PR for the batch, including the planning commit.

## Owner decision (2026-10-04, this session)

- **Yes** to `TCK-20261004-IMPORT-LINTER-ADOPTION`, advisory first.
- **Accept the 20 `src.<pkg>` root entries**: no `__init__.py` is added to `src/`. `src/` stays frozen; the batch has no `src/` diff.
- The handover notes of both codebase roles travel as committed copies on this batch's branch (see "Handover copies").

## Constraints already agreed (do not re-open)

Testing's four conditions (#322, recorded in the ticket):
1. A class E test is retired **only in or after the PR that makes its replacement contract a required check**.
   So **this batch retires no test**. This overrides the evaluation's "adoption retires the tests in the same
   change" (`import_linter_evaluation.md` recommendation 5): during the advisory soak the contracts and the
   tests both run. That is an accepted, time-boxed double copy, and the flip ticket below ends it.
2. Parity is shown per test: the injected violation, the test's result, the contract's result (a table in the
   ticket's Test Summary, made in a scratch copy, never in this checkout).
3. phase19 `test_hot_path_does_not_import_heavy_analyzers`: rpg (engine/observability) has not yet decided about
   `kernel.py`'s function-local imports (149/304/305/316/1241). Its contract ships with those five imports in
   `ignore_imports` with the reason "pending rpg decision, handoff_to_rpg.md". Do not edit the phase19 test.
4. The blind spots and the stale allowlist entry from evaluation Section 4 are covered by contracts. The `or True`
   assert (`tests/unit/observability/test_decision_trace.py:376`) belongs to testing. Leave it alone.

## Scope of this batch

Ticket 1 (rescope the existing ticket): **TCK-20261004-IMPORT-LINTER-ADOPTION**, standard, OPEN, out of BLOCKED.
- Exact-pin `import-linter` in the `lint` group; `uv.lock`; `requirements.txt` export if the lane requires it.
  After the pin, re-run `tests/static` (the uv/pin tests, memory: rerun CI pin tests after dep change).
- `[tool.importlinter]` in `pyproject.toml`: root packages = the 20 `src.<pkg>` namespace roots (+ `src` if the
  evaluation's reproduction needs it), `include_external_packages = true`. Pick the single global
  `exclude_type_checking_imports` value, list per contract whose semantics change, and say why.
- A `layers` contract **generated** from `codebase/structure/package_registry.jsonl`. Baseline = the 99/113
  current violations (whichever matches the TC choice) in `ignore_imports`, `unmatched_ignore_imports_alerting`
  so a fixed import shows as stale.
- Contracts for the 8 class E rules and the loopholes (plain `import`, `from pkg import module`). `visual_assets`
  only if the evaluation shows a root for it without adding a file to `src/`.
- Registry sync: a test (in `tests/codebase/`) that every `src.<pkg>` root in the registry is a root package in
  the config, and that the generated `layers` contract matches the registry. A generator command
  (`python3 -m codebase.structure.<module>`) that rewrites the contract, plus a `--check` mode.
- CI: **one advisory step**, a step summary and one `::warning::` annotation on a broken contract, never a failing
  exit. Put it in the job that runs the package-registry validator, as the last step, with `continue-on-error`
  if the job may be blocking. Keep the YAML diff to that one step: PR #329 edits the same file, see below.
  Keep the scenario lane `PERF_RE` pin (`tests/unit/tools/test_scenario_lane_paths.py`) and the job-set pins in
  `tests/static/` green.
- Docs: `docs/guidelines/agent_working_environment.md` (how to read the step, how to run it locally), roadmap M5
  row and Section 8 note (decision 8.20: the owner's yes and the 20 roots), `import_linter_evaluation.md` Section 7
  answered. Parity ledger: an `infrastructure.yaml` entry only if the repo pattern for the other codebase gates
  has one.

Ticket 2 (new, file it BLOCKED): **TCK-YYYYMMDD-IMPORT-LINTER-FLIP-AND-TEST-RETIREMENT**, standard.
- After a two-week soak from this batch's merge (write the dates at merge): step becomes blocking, the owner
  makes it a required check (the same rule as the gates flip: never before main produces the check name), then
  retire the class E tests whose contract is required, with the parity table re-shown. phase19 waits on rpg.
- Add it to `todos/python-code-craft-structure/SEQUENCE.md` as a follow-up.

## Interactions to manage

- **PR #329** (gates flip, merge 2026-10-18) edits `.github/workflows/test.yml`, `pyproject.toml`? (check),
  the roadmap, `agent_working_environment.md` and **this same ticket file**. Base this batch on `origin/main`.
  If this batch merges first, #329 merges main on merge day (the expected conflict grows by these files).
  If #329 merges first, merge `origin/main` into this branch before the PR is final. Either order is fine;
  tell me which files conflict before resolving.
- If the step lands in the `Code health` job, after the flip that job is required: the step must still never
  fail the job (continue-on-error or exit 0). Test that explicitly.
- Testing domain: tag `test-architecture-reviewer` on the PR; add a short "Update" to
  `docs/plans/codebase_health/handoffs/handoff_to_testing.md` (it rides in this PR): contracts added, no test
  retired, flip ticket filed.
- rpg: add a line to `handoff_to_rpg.md`: condition 3 still open, its five imports are allowlisted pending the
  decision.

## Handover copies (owner instruction: push the handover so work can continue on another machine)

`.claude/handover/` is gitignored. Copy `.claude/handover/codebase-planner.md` and
`.claude/handover/codebase-implementer.md` to `docs/plans/codebase_health/handoffs/session/` (same file names, a
frontmatter block so `validate_frontmatter` passes; check how the other handoff docs in that folder do it).
Re-copy them at every push of this branch, so the remote always has the latest. The planner updates its own file
first and tells you. The owner's instruction is the yes for pushing these copies, **only on this batch branch**;
every other push or merge still needs its own question.

## Done means

- No `src/` path in `git diff --stat origin/main...HEAD`.
- Contracts run locally and in CI advisory; summary + warning shown by a demo (a throwaway injection on a
  scratch branch PR is OK only with the owner's yes; otherwise show it locally and in the step's unit test).
- Parity table for all 8 rules in the ticket.
- Ticket 2 filed BLOCKED; SEQUENCE updated; handoffs updated; REGISTRY regenerated.
