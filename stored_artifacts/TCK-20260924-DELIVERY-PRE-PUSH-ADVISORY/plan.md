---
status: active
layer: ai
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20260924-DELIVERY-PRE-PUSH-ADVISORY
date: 2026-09-24
tags: [delivery, hooks, process-improvement]
---

# Plan — TCK-20260924-DELIVERY-PRE-PUSH-ADVISORY

## Module: `tools/delivery/pre_push_advisory_hook.py`

Mirrors `cd_prefix_advisory_hook.py`'s shape exactly: pure detection functions + thin stdin-JSON
`main()`, wrapped in `try/except: pass`, always exits 0, emits `hookSpecificOutput.additionalContext`
(newline-joined findings) only when there is something to report.

### Functions
- `is_git_push_command(command) -> bool` — the measured regex (investigation.md decision 1).
- `check_commit_subjects(run_command, base_ref, tickets_root) -> list[str]` — `git log
  <base>..HEAD --format=%h%x09%s`; for each line, extract `TCK-` ID; no ID → finding naming the
  short SHA and subject; ID with no file anywhere under `tickets_root` (via `rglob`, same as
  `pr_render.find_ticket_file`, reused directly — not a fourth parser) → a distinct finding.
- `check_monitoring_shard_staged(run_command) -> list[str]` — current ISO week via
  `datetime.now(timezone.utc).isocalendar()`; `git status --porcelain -- agent-monitoring/data/
  <week>/`; any output → one finding naming the dirty/untracked paths.
- `check_squash_merged_finished(run_command, base_ref) -> list[str]` — investigation.md decision 2's
  four-condition check; on fire, the finding names cutting a fresh branch off `origin/main` as the
  action and states never pushing further to this one.
- `run_all_checks(run_command, base_ref, tickets_root) -> list[str]` — concatenates all three;
  empty list means "all clear, print nothing" (Assumption 3: no all-clear text on a silent pass).
- `main()` — reads stdin, checks `is_git_push_command` on `tool_input.command`, runs all three
  checks, emits `additionalContext` only if any finding exists, always returns 0.

## `.claude/settings.json` change
**Append one new entry at PreToolUse index 6** (matcher `"Bash"`, command
`python3 tools/delivery/pre_push_advisory_hook.py 2>/dev/null || true`) — never inserted earlier.
Update `tests/tools/test_settings_json_hooks_wiring.py::test_existing_hook_writers_untouched`'s
`== 6` to `== 7`, and its comment listing which tickets each PreToolUse index traces to, adding this
one. No other line in that file changes — indices 3 and 4 (pinned by the two other test files)
stay untouched by construction.

## Tests: `tests/tools/test_delivery_pre_push_advisory.py`
FakeRunner pattern (same as `test_delivery_pr_status.py`), plus real throwaway git repos for Check
C per AC6's own warning (mirrors `tests/integrity/test_merge_union_crlf_duplication_repro.py`'s
real-repo pattern — a fixture that only asserts against faked `git` output cannot prove the
ancestor/content distinction is real).

1. AC1 — all-clear fixture (every commit has a real ticket ID, shard clean, not squash-finished) →
   empty findings, exit 0.
2. AC2 — a commit subject with no `TCK-` ID → finding names that commit.
3. AC3 — a commit citing a `TCK-` ID with no matching file → a *distinct* finding from AC2's shape.
4. AC4 — a ticket that moved to `tickets/done/` mid-branch is not reported missing (fixture: file
   present under `done/`, not `inprogress/`).
5. AC5 — dirty/untracked current-week shard → finding names the path(s).
6. AC6 — **real throwaway git repo**: commit A on `main`, branch off it, commit B, squash the
   branch's content into a new commit C on `main` (simulating the GitHub squash-merge), then add a
   no-op commit D on the original branch (still based on B, never rebased) — D is not an ancestor of
   `main` (now at C) while its content is already present. Assert the finding fires and names
   cutting a fresh branch. A second fixture — branch merely behind `main`, no squash shape — asserts
   no finding (the explicit "wrong shape" AC6 warns against).
7. AC7 — every fixture from 1–6 plus a forced internal exception path: assert exit code 0 in every
   case via the CLI `main()`.
8. AC8 — malformed JSON on stdin, and empty stdin: no traceback, exit 0, no output.
9. AC9 — recorded in Implementation Notes: the exact grep run and its result (investigation.md).
10. Regression: `tests/tools/test_settings_json_hooks_wiring.py` and the two index-pinning files
    (`test_bash_secret_scan_hook.py`, `test_settings_json_edit_write_hook_sidecar_scope.py`) still
    pass unchanged (except the one bumped `== 6` → `== 7` line and its comment).
11. Measured-coverage regression guard: a static test asserting the module's own matcher regex,
    run against a corpus sample of the 322 real shapes recorded in investigation.md (embedded as a
    small fixture list, not re-reading the live corpus at test time — deterministic), matches all of
    them and the one false-positive sample.

## Out-of-scope guardrails
- No exit code ever non-zero except a genuine internal error in the hook's own code, and even that
  case is caught by the outer `try/except: pass` per the existing hook's own pattern — so in
  practice this hook can never fail a push.
- No auto-fix, no auto-stage, no branch creation, no history rewrite anywhere in this module.
