# Capability 5: triage record (DRILL: the fault was injected, not a real defect)

Procedure: `docs/testing/regression_policy.md` §13. Nothing here was filed as a ticket or reported to `rpg-feature-planning`, because the fault is the pilot's own injection.

## §13.1 evidence record

| Field | Content |
|---|---|
| Source | local run, injected fault in a scratch detached worktree at a real path (`.claude/worktrees/pilot-scratch-fault`, since removed) |
| Identity | `tests/unit/resource/test_node_charge_accounting.py::test_regular_node_loses_exactly_one_charge_per_harvest` and `tests/integration/kernel/test_node_charge_cross_actor.py::test_two_actors_on_the_last_charge_yield_exactly_once`; local, no CI lane; SHA `54a2198f9de928dc1135f3c04d2ba1744aaa08ed` plus the uncommitted one-line change in `inputs/cap5_injected_fault.diff`; run time in `inputs/cap5_run_utc.txt` |
| Reproduction | apply `inputs/cap5_injected_fault.diff` (`src/core/conservation.py`: regular-node charge delta `-1` becomes `-2`), then `pytest tests/unit/resource/test_node_charge_accounting.py tests/integration/kernel/test_node_charge_cross_actor.py -q`. No seed or world needed (state built from helpers). |
| Expected vs observed | expected `charges_delta == -1` (ch03 §3: regular nodes lose 1 charge per harvest); observed `-2` (`outputs/cap5_new_tests_on_fault.txt`) |
| Rerun result | same SHA and same fault, rerun in isolation: same failure (`outputs/cap5_rerun_isolated.txt`). 2 of the 5 new tests fail; 3 pass. |
| Recent changes | the injected diff only (a real case would use the impact report's component list) |

## Classification and routing (§13.2)

- Class: **Product regression.** Distinguishing evidence: reproduces on rerun and in isolation; the change touches the behaviour path; the spec (ch03 §3) is unchanged.
- Who acts: change author; feature team for feature code. Routing: **would route to `rpg-feature-planning` per §13.4** if it were a real defect.
- Immediate action: fix the code, not the test.
- Closure condition: fix merged; the failing tests pass in their lane; a regression test exists (it does: these tests).
- Not the class: not Test defect (the oracle is the Bible sentence), not Intentional spec change (no document changed), not Order dependence (same result alone and combined).

## What else the drill showed

- The same fault was also caught by an existing test, `tests/unit/resource/test_harvest_channeling.py::test_harvest_channeling_and_yield` (see `outputs/cap5_existing_tests_on_fault.txt`: 1 failed, 35 passed, 1 skipped for three existing files). So the recorded baseline's survivor for this mutation line only says the baseline's own selected test set missed it; it does not show that no existing test in the repo covers it. The pilot therefore makes no claim about mutation-score change.
- Scratch worktree removed and confirmed gone; `git status --short src` in the pilot worktree is clean.
