---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260925-STATIC-CHECK-HARDCODED-VENV-INTERPRETER-PATH
phase: done
date: 2026-09-25
tags: [testing]
---

# TCK-20260925-STATIC-CHECK-HARDCODED-VENV-INTERPRETER-PATH

## Title

Add a static guard against hardcoding a machine-specific venv interpreter path in a subprocess call

## Status

DONE

## Tier

hotfix

## Type

chore

## Priority

P2

## Request Summary

`TCK-20260925-HOTFIX-HARDCODED-VENV-PATH-IN-TESTS` (closed earlier today) is the **second**
occurrence of the exact same defect class as `TCK-20260904-HOTFIX-CI-SUBPROCESS-PYTHON3-INTERPRETER-MISMATCH`:
a test/tool subprocess call hardcodes one specific dev machine's absolute venv interpreter path
instead of `sys.executable`. This project has two dev machines with different venv locations
(`u24desktop` at `.venv/bin/python3`, `vboxuser` at `/home/vboxuser/Work/venv/bin/python3`) plus
CI, which has neither — a path that works for whoever writes the test is broken for the other two
environments, with a plain `FileNotFoundError` that is 100% deterministic on CI and never
reproducible locally on the machine where the path happens to be valid. Suggested by
agent-working-design after the second occurrence, on the reasoning that a recurring defect with an
identical fix both times is worth a guard rather than a third fix later.

## Scope

- Add `tests/static/test_no_hardcoded_venv_interpreter_path.py`: scans every `.py` file under
  `tests/` and `tools/` for a venv-interpreter-path string literal used as the first element of a
  subprocess command list (the exact shape both real bugs had).
- Deliberately narrow, not a blanket "no absolute path" rule — confirmed by grepping the current
  corpus first (see Implementation Notes) that a broad rule would false-positive on legitimate
  machine-specific path literals used as pure string *data*, not as an interpreter to execute.
- Prove detection works, not just clean reporting on the already-fixed corpus: a planted-violation
  test using a synthetic bad file.

## Out of Scope

- Any broader "no hardcoded absolute path" rule — deliberately rejected; see Implementation Notes
  for the two confirmed-legitimate cases this would have wrongly flagged.
- Rewriting the existing subprocess-spawn pattern into a shared helper (a real, reasonable DRY
  improvement, out of scope for both prior tickets in this class too).
- `docs/`, `Makefile`, or any non-`.py` file — the two real bugs were both in test-file Python
  source; a documentation example or Makefile fallback probe (confirmed legitimate, see
  `docs/guidelines/agent_working_environment.md`'s own venv table) is a different, deliberate case.

## Acceptance Criteria

1. The new test passes against the current (already-fixed) corpus: zero violations.
2. A planted synthetic violation (same shape as the real bugs) is detected — proven, not assumed.
3. The two known legitimate machine-specific-path occurrences
   (`tests/tools/test_mcp_launcher_hardening.py`'s `.index(...)` calls,
   `tools/perf/live_map_ws_payload_measure.py`'s docstring CLI example) are NOT flagged.
4. Full `tests/static/` suite still passes.

## Related Tickets

- `TCK-20260925-HOTFIX-HARDCODED-VENV-PATH-IN-TESTS` — the second occurrence that prompted this
  guard.
- `TCK-20260904-HOTFIX-CI-SUBPROCESS-PYTHON3-INTERPRETER-MISMATCH` — the first occurrence, same
  fix pattern (`sys.executable`).

## Related Docs

None requiring update.

## Related Stored Artifacts

None (hotfix tier, no staging artifacts required).

## Related Code Areas

- `tests/static/test_no_hardcoded_venv_interpreter_path.py` (new)

## Assumptions / Open Questions

None.

## Implementation Notes

Grepped the current corpus first (`grep -rn "venv/bin/python" --include="*.py" tests/ tools/`)
before designing the rule, to confirm scope and rule out a broad rule producing false positives:
exactly 3 hits found, none of which are the bug pattern any more (the two real occurrences are
already fixed by the sibling ticket) —
`tests/tools/test_mcp_launcher_hardening.py` (twice, a path passed to `str.index(...)` as pure
string data — checking a launcher script's own source text for an intentional, legitimate
multi-machine fallback probe, not itself hardcoding a subprocess interpreter) and
`tools/perf/live_map_ws_payload_measure.py` (a CLI usage example inside a docstring, never
executed). Designed the regex to match only a venv-path string literal immediately following a
`[` (the first element of a command list) — this precisely targets the shape both real bugs had
and does not match either of the two legitimate cases, confirmed by dedicated tests for both the
detection and the non-false-positive cases, not just by inspection.

## Test Summary

- `python3 -m pytest tests/static/test_no_hardcoded_venv_interpreter_path.py -v` — **3 passed**
  (clean-corpus check, planted-violation detection via a synthetic bad file, non-false-positive
  check against the real `.index(...)` usage shape).
- Full `tests/static/` suite: `python3 -m pytest tests/static/ -v` — **52 passed**, 0 failed.
- Confirmed `tests/static/` is already wired into two CI jobs (`grep -n "tests/static"
  .github/workflows/test.yml` — lines 531, 578) — no workflow change needed for this new test to
  run in CI.

## Files Changed

- `tests/static/test_no_hardcoded_venv_interpreter_path.py` — new.
- `docs/REGISTRY.yaml` — regenerated as part of ticket close (routine, unconditional per the
  Finalize rule), picking up this ticket's own `tickets/done/` entry.

## Completion Summary

Added `tests/static/test_no_hardcoded_venv_interpreter_path.py`, a narrow static guard against the
exact defect class that bit twice now (`TCK-20260904-HOTFIX-CI-SUBPROCESS-PYTHON3-INTERPRETER-MISMATCH`,
`TCK-20260925-HOTFIX-HARDCODED-VENV-PATH-IN-TESTS`): a hardcoded machine-specific venv interpreter
path used as a subprocess command's first argument, which works only on the one machine that
happens to have that exact path and fails deterministically everywhere else, including CI.

Deliberately scoped narrow rather than a blanket "no absolute path" rule, confirmed by grepping the
real corpus first: two legitimate machine-specific-path occurrences exist today
(`tests/tools/test_mcp_launcher_hardening.py`'s `.index(...)` calls checking a launcher script's
own fallback-probe text, `tools/perf/live_map_ws_payload_measure.py`'s docstring CLI example) and
neither is the bug shape. The regex targets only a venv-path literal as the first element of a
`[...]` command list — proven to both catch the real shape (planted-violation test with a synthetic
bad file) and not flag either legitimate case (dedicated non-false-positive test), not just
asserted by inspection. `tests/static/` is already wired into two CI jobs, so no workflow change
was needed.

No known material gap. Test-infrastructure-only; no production code touched.
