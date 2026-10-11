---
status: historical
layer: performance
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261010-PERF-M2-PERFBUDGET-RETIRE
date: 2026-10-11
tags: [performance, testing, regression]
---

# Investigation: TCK-20261010-PERF-M2-PERFBUDGET-RETIRE

Search order: `search_docs`, then `git grep` for every reference, then the tests that read the session registry.

## Findings
1. **The ticket's premise that two tests use the fixture is wrong.** `test_phase2_self_model_budget.py` and `test_phase3_adventure_decision_budget.py` contain `perf_budget` only in their function names; neither takes the fixture. No test used `PerfBudget` except its own meta-tests in `tests/unit/perf/test_perf_guard.py`. I had copied "two users" into `performance_contract.md` §5.2 (T03, #496); it is corrected here.
2. **The reference list was incomplete.** Beyond the ticket's list the live references were: `docs/guidelines/repo_tooling_layout.md` (the repo-root allowlist, parsed by the allowlist test), `docs/testing/test_taxonomy.md` section 4 (the fixture workflow and `PERF_HARDWARE_CLASS`), and the two generated role cards `.claude/agents/session-perf-{implementer,planner}.md`.
3. **The registry edit is not optional.** `tests/tools/test_session_roster.py::test_real_registry_validates` fails with "owns 'tools/perf_guard.py' resolves to no file" once the files are gone. The registry is owned by agent-working-planner and the cards are generated from it (`python3 -m tools.sessions.generate_agents`; running the file by path fails on the import).
4. **The repo-root allowlist parser reads backticked names in its section**, so a sentence that mentions the deleted file in backticks puts it back on the allowlist. Found only in a clean worktree.
5. **`test_session_agent_generator.py::test_committed_files_have_no_drift` times out (the repo's 60 s test limit) in my worktree** because it globs about 32,000 untracked files (19,000 under `data/runs` from earlier days, which are not mine to delete, and a 4,000-file `graphify-out` copy) next to 16,000 tracked ones. In a clean worktree it passes in about 20 s. CI checks out clean.
6. **A process mistake of mine, caught by the clean-worktree check.** My first `git add` named `perf_baselines.json`, a path that no longer existed, which aborts the whole command. The commit therefore held only the three deletions while its message described much more, and my cluttered worktree hid it (the files were modified on disk). Fixed before any push by squashing the two unpushed commits and recommitting with `git add -u`. Lesson: verify a commit in a clean worktree, not in the worktree you edited.
7. Remaining mentions of the names (for the record): this ticket and the contract §5.2 text recording the deletion; the ledger, schema doc and PERF-D decisions text recording it; the clause inventory (dated evidence); `docs/plans/**`, `experiments/**` and `docs/archive/**` (historical proposals); and two test function names that contain `perf_budget`.

## Not verified
- The whole CI run (pushed after this); the full suite.
