---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261020-CI-LANES-RUN-TRAILING-BACKSLASH-AND-XDIST
phase: done
date: 2026-10-20
tags: [ai, regression]
---

# TCK-20261020-CI-LANES-RUN-TRAILING-BACKSLASH-AND-XDIST

## Title
`ci_lanes --run` runs test.yml's commands as CI does: no stray `\` argument once `--junit-xml` is stripped, and a clear stop when the venv lacks pytest-xdist

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
This is a finding from rpg-planner (2026-10-19, from rpg-implementer-2 on rpg-pre-v1-fixes b0c49820d). Every `--run` lane
(unit-infra, integration, perf-cert-arena) failed before any test ran. The same commands pass when run by hand (unit-infra 1104,
integration 1088/6 skipped, perf-cert-arena 270). The pre-push hook (check D, TCK-20261014-PRE-PUSH-CI-LANE-PARITY,
#590) recommends a `--run` that cannot succeed.

agent-working-planner verified both causes on origin/main:

1. **Trailing backslash.** `lane_commands` removes `\s*--junit-xml=\S+` from each step. In test.yml the junit flag is
   on the last line after a `\` continuation, so the stripped command ends in `... -q \`. `bash -ec` then passes a
   literal `\` to pytest as a path argument. Seen on every unit-infra step, on integration and on perf-cert-arena.
2. **xdist.** Since #659 the integration step (and Tools f–z, API/CLI/engine) carries `-n auto --dist loadgroup`. A venv
   without `pytest-xdist` (in the dev group) fails with pytest's unrecognized-argument error.

## Scope
- After stripping `--junit-xml`, also remove a line continuation (`\` plus trailing whitespace) left dangling at the end of the
  command, or at the end of any line it leaves empty. The command must otherwise run byte-for-byte as in test.yml.
- Before running any lane whose command contains `-n ` / `--dist`, check that `xdist` is importable in the interpreter
  that will run pytest. If it isn't, stop that lane with one line: name the missing plugin and the install command
  (the repo's dev-group sync). Don't strip `-n` silently: the local run must match CI's.
- `--list` output shows the same fixed commands.

## Out of Scope
- Changing test.yml (testing's).
- The pre-push hook's wording, unless a test pins the old command text.
- Other `ci_lanes` behaviour (resolution, flags, `--all`).

## Acceptance Criteria
1. A unit test over a fixture workflow, with a step whose last line is `--junit-xml=...` after `\`, shows that
   `lane_commands` returns a command that does not end in `\`. `bash -n -c` accepts it, and no argument is a lone `\`. Assert
   the latter with a runner stub that records argv after `bash -c 'printf "%s\n" ...'`, or an equivalent.
2. On origin/main's real test.yml, no command from `lane_commands` for any lane ends in `\` (a test that loads the real
   workflow).
3. A runner-stubbed test: with xdist reported unimportable, a lane whose command has `-n auto` is not run. The output
   names pytest-xdist and the install command, and the lane is reported FAIL. Lanes without `-n` still run.
4. Manual check, recorded in Test Summary: `python3 -m tools.delivery.ci_lanes --run --lane integration` in the real venv
   gets past argument parsing and runs tests.
5. `pytest tests/tools/test_delivery_ci_lanes.py -p no:randomly` passes.

## Related Tickets
- TCK-20261014-PRE-PUSH-CI-LANE-PARITY (#590): introduced `--run` and check D.
- TCK-20261019-CI-PR-WAIT-XDIST-IN-EXISTING-JOBS (#659): added `-n auto` to test.yml.

## Related Docs
- `docs/testing/migration_ci_lanes.md`
- `docs/guides/delivery_process.md` (pre-push)

## Related Stored Artifacts
None.

## Related Code Areas
- `tools/delivery/ci_lanes.py` (`_JUNIT`, `lane_commands`, `run_lanes`)
- `tests/tools/test_delivery_ci_lanes.py`
- `.github/workflows/test.yml` (read only)

## Assumptions / Open Questions
- The interpreter that runs pytest in `bash -ec` is the one on PATH, so the xdist check should probe that interpreter
  (for example `python3 -c "import xdist"` through the same runner), not `sys.executable`. Confirm this when implementing.

## Implementation Notes
`tools/delivery/ci_lanes.py`: `lane_commands` now goes through `_strip_junit`, which removes `--junit-xml=...`, collapses a `\ \` pair left mid-command, and drops any continuation left dangling at the end. `run_lanes` checks once per call that `python3` can import `xdist` (`xdist_importable`, injectable as `xdist_check`) before any lane whose command has `-n`/`--dist`; if not, it prints one line naming pytest-xdist and `uv sync --locked --no-install-project --no-group lint`, reports `FAIL: <lane>` and skips the lane. `-n` is never stripped. `--list` shows the same fixed commands. test.yml and the pre-push hook text are unchanged.

## Test Summary
`pytest tests/tools/test_delivery_ci_lanes.py -p no:randomly`: 32 tests (4 new), all passed; with `-k "ci_lanes or pre_push"` 48 passed.
New tests: trailing-backslash fixture checked with `bash -n` and a `printf` argv check (no lone `\`); mid-continuation junit flag; the real test.yml (no lane command ends in `\`); a stubbed run where xdist is unimportable (integration not run, output names pytest-xdist and the install command, lane FAIL, non-xdist lane still runs).
AC 4 manual: `python3 -m tools.delivery.ci_lanes --run --lane integration` with the repo venv on PATH printed `[integration] $ pytest tests/integration ...`, started xdist workers ("bringing up nodes") and ran tests (6% when I stopped it after 40 s). Without xdist, the system `python3` cannot import it, which is the case the new check stops.

## Files Changed
- `tools/delivery/ci_lanes.py`
- `tests/tools/test_delivery_ci_lanes.py`

## Completion Summary
`ci_lanes --run` no longer hands pytest a lone `\`, and stops an xdist lane with one clear line when pytest-xdist is missing instead of failing in argument parsing.
