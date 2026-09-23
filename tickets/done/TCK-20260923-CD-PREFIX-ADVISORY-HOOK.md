---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260923-CD-PREFIX-ADVISORY-HOOK
phase: done
date: 2026-09-23
tags: [ai, agent-monitoring, observability, process-improvement]
---

# TCK-20260923-CD-PREFIX-ADVISORY-HOOK

## Title
Advisory PreToolUse hook against redundant `cd <path> &&` Bash prefixes — Batch B ticket 2 of 3

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
`TCK-20260923-BASH-COMMAND-MIX-BASELINE` measured `cd` as the single largest Bash command head,
~21.5% of all Bash calls (24,943 over W30-W39, `--ref origin/main`-pinned) — almost entirely
`cd <path> && ...` prefixes in a harness where the working directory already persists between
Bash calls (this repo's own system prompt already states this directly and calls out `git` as the
specific example). Batch B's own explicit constraint: this must be advisory only, never blocking.

## Scope
- `tools/agent-monitoring/cd_prefix_advisory_hook.py`: pure `detect_redundant_cd_prefix()`
  detecting the one provably-redundant case (the `cd` target normalizes to the exact same
  directory the Bash call already starts in), plus a thin stdin-JSON CLI wrapper emitting a
  `hookSpecificOutput.additionalContext` advisory, fail-open on any error.
- `.claude/settings.json`: new `PreToolUse` → `Bash` matcher entry invoking the module.
- `tests/tools/test_cd_prefix_advisory_hook.py`: 15 tests per `test_plan.md`.

## Out of Scope
- Flagging any `cd` beyond the exact-same-directory case — see `investigation.md`'s design
  decision; most of the measured 21.5% is legitimate directory switching, not waste.
- Blocking or modifying the Bash call in any way.
- Measuring this hook's own after-effect — `bash_command_mix.py` (ticket 1, `--ref`-pinned per
  the follow-up hotfix) is the standing instrument for that; a future measurement is a separate,
  later exercise, not part of shipping the nudge itself.

## Acceptance Criteria
- [x] Fires only when a Bash command's leading `cd <path> &&` targets the exact directory the
      call already starts in — verified by 3 explicit "must NOT flag" tests (different directory,
      subdirectory, sibling worktree) alongside the "must flag" cases.
- [x] Advisory only: `hookSpecificOutput.additionalContext` only, never a `decision`/block field;
      wrapped in try/except so a hook failure can never block the Bash call.
- [x] Wired into `.claude/settings.json`'s `PreToolUse`/`Bash` matcher list; file remains valid
      JSON after the edit.
- [x] Manually verified end-to-end against a realistic stdin payload through the wired module
      (not just the isolated pure function).
- [x] All 15 new tests pass.

## Related Tickets
- `TCK-20260923-BASH-COMMAND-MIX-BASELINE` (done) — the before-number this hook targets.
- `TCK-20260923-BASH-MIX-REF-PINNING` (done) — the reproducible-measurement follow-up that keeps
  any future before/after claim for this hook honest.
- Batch B ticket 3 (search-before-grep advisory nudge, not yet filed) — same advisory shape,
  filed next in this same session.

## Related Docs
None beyond the module's own docstring.

## Related Stored Artifacts
- `stored_artifacts/TCK-20260923-CD-PREFIX-ADVISORY-HOOK/` — `investigation.md`, `plan.md`,
  `test_plan.md`.

## Related Code Areas
- `tools/agent-monitoring/cd_prefix_advisory_hook.py` (new)
- `tests/tools/test_cd_prefix_advisory_hook.py` (new)
- `.claude/settings.json`

## Assumptions / Open Questions
- The hook reads `cwd` from the PreToolUse payload when present, falling back to `os.getcwd()`
  (the hook process's own cwd) otherwise — both are expected to equal the Bash call's own starting
  directory in this harness (per its documented "working directory persists between calls"
  behavior); not independently re-verified against harness internals beyond the manual end-to-end
  check in `investigation.md`.
- Effectiveness (does the advisory actually reduce the measured 21.5% share) is intentionally left
  unmeasured by this ticket — see Out of Scope. `bash_command_mix.py --ref origin/main` is the
  instrument a later, separate check would use.

## Implementation Notes
Detection is deliberately narrower than the measured 21.5% `cd`-share figure itself: that number
is a call-count share, not a waste count, and most `cd` calls in it are legitimate (worktree
switches, subproject entry — this repo's own CLAUDE.md worktree-per-ticket convention depends on
`cd`ing into a fresh worktree directory routinely). Flagging every `cd` would be both wrong and,
per the batch's own explicit warning against overselling small behavioral nudges, likely to erode
trust in the advisory rather than change behavior. `detect_redundant_cd_prefix()` fires on exact
normalized-path equality only, verified by three explicit tests proving it does NOT flag a
different directory, a subdirectory, or a sibling worktree path.

Followed the existing secret-scan hook's shape (pure function + thin CLI wrapper invoked as
`python3 tools/agent-monitoring/*.py 2>/dev/null || true`) rather than an inline shell one-liner
like the sidecar-check/graphify hooks, since this detection needed real logic (path normalization,
quote-stripping, tilde expansion) that's meaningfully more testable as a Python function than a
shell `case` statement — matches `tools/write_path_guard.py::scan_for_secrets`'s own precedent for
"detection logic complex enough to need its own tested module."

## Test Summary
- `pytest tests/tools/test_cd_prefix_advisory_hook.py -v` — 15 passed.
- `python3 -c "import json; json.load(open('.claude/settings.json'))"` — valid JSON confirmed
  after the hook-list edit.
- Manual end-to-end: piped a realistic stdin payload through the wired module — fired correctly
  for `cd <cwd> && echo hi`, silent for `echo hi`.

## Files Changed
- `tools/agent-monitoring/cd_prefix_advisory_hook.py` (new)
- `tests/tools/test_cd_prefix_advisory_hook.py` (new, 15 tests)
- `.claude/settings.json` — new `PreToolUse`/`Bash` matcher entry.
- `staging_artifacts/TCK-20260923-CD-PREFIX-ADVISORY-HOOK/` (new).

## Completion Summary
Shipped an advisory-only `PreToolUse` hook against the single largest Bash command-mix finding
from ticket 1 (`cd` at ~21.5% of all Bash calls): `tools/agent-monitoring/cd_prefix_advisory_hook.py`
detects only the one provably-redundant case (a `cd` target identical to the Bash call's own
starting directory), deliberately leaving every genuine directory switch un-flagged — verified by
three explicit negative tests, not just the positive cases. Wired into `.claude/settings.json`
matching the existing secret-scan hook's shape (pure function + thin CLI wrapper, fail-open,
`additionalContext`-only, never blocking). 15 new tests, all passing; manually verified end-to-end
against the wired module, not just the isolated function. No known material gap left unstated.
