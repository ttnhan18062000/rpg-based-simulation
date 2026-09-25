---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260925-HOTFIX-HARDCODED-VENV-PATH-IN-TESTS
phase: done
date: 2026-09-25
tags: [testing]
---

# TCK-20260925-HOTFIX-HARDCODED-VENV-PATH-IN-TESTS

## Title

Replace hardcoded local absolute venv path with `sys.executable` in two test-spawned subprocess calls

## Status

DONE

## Tier

hotfix

## Type

bug

## Priority

P1

## Request Summary

Root cause of the `API / tools / logging` job's deterministic `tests/tools` CI failure on PR #246
(four confirmed CI runs, zero local reproduction under any isolation model), finally identified via
`TCK-20260925-CI-JUNIT-FAILURE-ANNOTATIONS`'s new `::error::` annotations on the very first CI run
after it landed:

```
FAILED tests.tools.test_monitoring_consolidation::test_done_checker_static_suite_still_passes
  - FileNotFoundError: [Errno 2] No such file or directory:
    '/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3'
FAILED tests.tools.test_delivery_cost_measurement::test_bash_command_mix_own_tests_unaffected
  - FileNotFoundError: [Errno 2] No such file or directory:
    '/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3'
```

Both tests hardcode the exact local absolute path to this dev machine's (`u24desktop`) venv
interpreter in a `subprocess.run([...])` call, instead of `sys.executable` (the interpreter pytest
itself is actually running under). That path exists on `u24desktop` and nowhere else — it never
exists on a fresh `actions/setup-python`-provisioned CI runner (or on `vboxuser`, the project's
other documented dev environment). This is the exact same defect class as
`TCK-20260904-HOTFIX-CI-SUBPROCESS-PYTHON3-INTERPRETER-MISMATCH` (which fixed 16 occurrences of a
bare literal `"python3"` across 12 files) — this ticket's version is strictly worse, a full absolute
path rather than a `PATH`-resolved bare command, which is exactly why it failed **deterministically
on every CI run** while never reproducing locally on `u24desktop` (where that literal path is
genuinely correct) under any isolation model tried across several rounds of investigation
(standalone directory runs, sequential-step-mimicking chains, and a real `git worktree` checkout at
the exact CI-tested SHA).

Both hardcoded occurrences were introduced by this session's own earlier work today (the ticket 6
and ticket 8 implementations of the `github-delivery-process-epic`), not by any other session or
pre-existing code — this is a self-inflicted regression, correctly root-caused rather than
attributed elsewhere.

## Scope

1. Replace the hardcoded literal
   `"/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3"` with `sys.executable` in:
   - `tests/tools/test_monitoring_consolidation.py::test_done_checker_static_suite_still_passes`
   - `tests/tools/test_delivery_cost_measurement.py::test_bash_command_mix_own_tests_unaffected`
2. Add `import sys` to `tests/tools/test_delivery_cost_measurement.py` (not already imported there;
   `tests/tools/test_monitoring_consolidation.py` already imports it).
3. Re-run both affected tests, and the two test files' full suites, to confirm no other issue was
   masked behind this one.

## Out of Scope

- Any other file — grepped the whole repo for the same literal path pattern; confirmed these are
  the only two occurrences (see Implementation Notes).
- Rewriting the subprocess-spawn pattern into a shared helper — a reasonable future DRY
  improvement (both call sites are near-identical, mirroring the same observation
  `TCK-20260904-HOTFIX-CI-SUBPROCESS-PYTHON3-INTERPRETER-MISMATCH` made and also left out of
  scope), not this hotfix's job.
- The `docs/guidelines/agent_working_environment.md` two-venv guidance itself — not wrong, just a
  likely contributing factor to why an absolute path got hardcoded instead of `sys.executable`
  being used from the start; noted, not changed here.

## Acceptance Criteria

1. Neither test file contains the literal string `/home/u24desktop/` anywhere.
2. Both affected tests pass when run with `sys.executable` in place of the hardcoded path.
3. `grep -rln "/home/u24desktop/" --include="*.py" .` returns exactly the two benign, confirmed-safe
   pre-existing hits (`tests/tools/test_cd_prefix_advisory_hook.py`'s synthetic string-data fixtures,
   `stored_artifacts/.../investigate_measurement_script.py`, uncollected by CI) plus this ticket's
   own file (which quotes the bug for documentation) — never the two files this ticket fixes.
4. Full `tests/tools/` regression suite (not just the two directly-touched files) still passes, to
   catch any other test relying on behavior these two tests exercise.

## Related Tickets

- `TCK-20260904-HOTFIX-CI-SUBPROCESS-PYTHON3-INTERPRETER-MISMATCH` — identical defect class
  (hardcoded local interpreter path instead of `sys.executable`), same fix pattern.
- `TCK-20260925-CI-JUNIT-FAILURE-ANNOTATIONS` — the diagnostic tool that surfaced this failure's
  exact test names and messages on its very first real CI run, ending several rounds of
  hypothesis-driven investigation (loaded-runner concurrency, vocabulary-drift ratchet via
  merge-ref) that all turned out not to be the cause.
- `TCK-20260925-CI-API-TOOLS-LOGGING-PER-DIRECTORY-STEPS` — first narrowed the failure to the
  `tests/tools` directory.

## Related Docs

None requiring update — test-infrastructure-only, no documented behavior change.

## Related Stored Artifacts

None (hotfix tier, no staging artifacts required).

## Related Code Areas

- `tests/tools/test_monitoring_consolidation.py`
- `tests/tools/test_delivery_cost_measurement.py`

## Assumptions / Open Questions

None — root cause confirmed directly from real CI annotation output, not inferred.

## Implementation Notes

Grepped the whole repo (`grep -rln "/home/u24desktop/" --include="*.py" .`) before touching
anything, to confirm scope was exactly these two occurrences and not a wider pattern. Found 4 hits,
of which 2 are genuinely this bug and 2 are not:
- `tests/tools/test_monitoring_consolidation.py`, `tests/tools/test_delivery_cost_measurement.py`
  — the two real occurrences fixed here.
- `tests/tools/test_cd_prefix_advisory_hook.py` — 15 occurrences, but every one is a synthetic
  *string literal* passed as a pure-data argument to `detect_redundant_cd_prefix(command, cwd)`, a
  string-parsing function under test. It never touches the filesystem or spawns a process; the
  path is illustrative input, not a real interpreter/file reference. Confirmed by reading the
  function's own signature and every call site before excluding it — not assumed safe from the
  filename alone.
- `stored_artifacts/TCK-20260816-KGMCP-P5-REPEATED-DEMAND-MEASUREMENT/investigate_measurement_script.py`
  — a past ticket's stored investigation script, not under `tests/` and never named in
  `.github/workflows/test.yml`'s explicit per-directory pytest invocations; not collected by CI
  regardless of its content.

Both real call sites are otherwise identical in
shape — a `subprocess.run([<interpreter>, "-m", "pytest", "<some other test file>", "-q"],
capture_output=True, text=True)` check that a sibling test file's own suite still passes, used as a
"did my change to a shared module break someone else's test file" regression guard. Fixed both by
swapping the hardcoded literal for `sys.executable`, matching the established, previously-shipped
fix pattern from `TCK-20260904-HOTFIX-CI-SUBPROCESS-PYTHON3-INTERPRETER-MISMATCH` exactly, rather
than inventing a new approach for what is the same underlying defect.

## Test Summary

- `python3 -m pytest tests/tools/test_monitoring_consolidation.py tests/tools/test_delivery_cost_measurement.py -v`
  — **24 passed**, including both previously-failing tests
  (`test_done_checker_static_suite_still_passes`, `test_bash_command_mix_own_tests_unaffected`),
  both now genuinely exercising their subprocess check via `sys.executable` rather than the
  hardcoded path (AC2).
- `grep -n "u24desktop" tests/tools/test_monitoring_consolidation.py
  tests/tools/test_delivery_cost_measurement.py` — no hits (AC1).
- `grep -rln "/home/u24desktop/" --include="*.py" .` — exactly the two confirmed-benign
  pre-existing hits plus this ticket's own file; neither of the two fixed files appears (AC3).
- Full regression: `python3 -m pytest tests/tools/ -m "not slow and not extra_slow" -q` — **3026
  passed**, 25 skipped, 28 deselected, 1 xfailed, 0 failed (AC4).

## Files Changed

- `tests/tools/test_monitoring_consolidation.py` — 1 hardcoded path → `sys.executable`.
- `tests/tools/test_delivery_cost_measurement.py` — `import sys` added, 1 hardcoded path →
  `sys.executable`.
- `docs/REGISTRY.yaml` — regenerated as part of ticket close (routine, unconditional per the
  Finalize rule), picking up this ticket's own `tickets/done/` entry.

## Completion Summary

Root-caused and fixed the entire `tests/tools` CI mystery: two test files
(`test_monitoring_consolidation.py`, `test_delivery_cost_measurement.py`, both introduced by this
session's own earlier work today) hardcoded this exact dev machine's absolute venv path in a
`subprocess.run([...])` call instead of `sys.executable`. That literal path exists only on
`u24desktop`, so it failed with a plain `FileNotFoundError` on every CI runner — 100%
deterministic, and un-reproducible locally on the one machine where the path happens to be
correct, which is exactly the "deterministic on CI, zero local reproduction" shape that drove
several rounds of investigation (loaded-runner concurrency hypothesis, vocabulary-drift ratchet
via merge-ref hypothesis — both directly disconfirmed by evidence, not just dropped) before
`TCK-20260925-CI-JUNIT-FAILURE-ANNOTATIONS` surfaced the exact test names and messages on its very
first real CI run. Same defect class as the previously-shipped
`TCK-20260904-HOTFIX-CI-SUBPROCESS-PYTHON3-INTERPRETER-MISMATCH`, same fix.

Grepped the whole repo before touching anything rather than assuming scope; found two additional
matches for the same literal string and confirmed both benign by reading their actual usage (one
is synthetic string-data in a parser test, one is an uncollected past-ticket artifact script) —
not excluded on the filename alone.

No known material gap. Did not touch the annotations feature or any other file outside the two
named in Scope.
