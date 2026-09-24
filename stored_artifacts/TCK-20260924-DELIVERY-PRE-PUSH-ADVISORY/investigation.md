---
status: active
layer: ai
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20260924-DELIVERY-PRE-PUSH-ADVISORY
date: 2026-09-24
tags: [delivery, hooks, process-improvement]
---

# Investigation — TCK-20260924-DELIVERY-PRE-PUSH-ADVISORY

## Confirmed facts

- **`cd_prefix_advisory_hook.py`'s exact shape, read in full**: pure `detect_...(command,
  current_dir) -> str | None` function, plus a thin `main()` reading `{"tool_input": {"command":
  ...}, "cwd": ...}` from stdin, wrapped in a bare `try/except: pass`, printing
  `{"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": ...}}` only when
  triggered, always returning 0.
- **Measured real `git push` command shapes** (Assumption 1's mandatory measurement, over
  `agent-monitoring/data/2026-W*/tools.jsonl`, 323 raw mentions, 1 excluded as a `grep` string
  literal, not a real invocation): **250/322 (77.6%) bare** (the whole command is just `git push
  ...`), **64/322 (19.9%) newline-chained**, **5/322 (1.6%) `&&`-chained**, **3/322 (0.9%)
  `;`-chained**. Unlike the `cd`-prefix hook's own target shape (a *prefix* before other work),
  `git push` here is overwhelmingly the *whole command* or the *last* statement in a chain — so the
  matcher must fire on `git push` appearing at the **start of the command or immediately after
  `&&`/`;`/a newline** (a statement-start position), not merely "the command contains the
  substring `git push` anywhere" — that broader form would have matched the one real false
  positive found (a `grep` whose pattern argument mentions `git push` as a literal string, never
  actually running it).
- **`.claude/settings.json`'s `PreToolUse` array currently has 6 entries** (indices 0–5). Two
  *other* tests pin **exact array indices**, not just the count: `test_bash_secret_scan_hook.py`
  reads `hooks.PreToolUse[4]`, `test_settings_json_edit_write_hook_sidecar_scope.py` reads
  `hooks.PreToolUse[3]`. `test_settings_json_hooks_wiring.py::test_existing_hook_writers_untouched`
  additionally pins the exact count (`== 6`). **A new entry must be appended at index 6 (the end),
  never inserted earlier**, or both index-pinning tests break silently — the exact failure mode
  `TCK-20260924-SETTINGS-HOOK-PINNED-TEST-DRIFT` already fixed once this batch. The count-pinning
  test's own assertion (`== 6`) must be bumped to `7` as part of this ticket's own change (matching
  how the cd-prefix-advisory-hook's own addition updated the same line from 5→6).
- **AC9's mandatory grep, run before any `.claude/settings.json` edit**: `grep -rl
  "\.claude/settings\.json\|settings\.json" tests/` found 4 files. Two (`test_bash_secret_scan_hook.py`,
  `test_settings_json_edit_write_hook_sidecar_scope.py`) pin fixed indices (3 and 4 respectively) —
  unaffected by an append at index 6, confirmed by reading both in full, not just grepping their
  names. One (`test_subsystem_ownership_lifecycle_doc.py`) mentions `.claude/settings.json` only in
  prose describing an unrelated existing hook. The fourth is `test_settings_json_hooks_wiring.py`
  itself, covered above.
- The hook script's location must be `tools/delivery/`, not `tools/agent-monitoring/` (despite
  `cd_prefix_advisory_hook.py` living there) — the epic's own explicit ordering constraint forbids
  touching `tools/agent-monitoring/` ahead of ticket 6, and this ticket runs before it.

## Design decisions

1. **Matcher regex**: `(?:^|&&|;)\s*git\s+push\b`, applied with `re.MULTILINE` so `^` also matches
   after a literal newline — covers all three real chained shapes (`&&`, `;`, newline) plus the
   dominant bare-command shape, and does not match the one confirmed false-positive shape (`git
   push` appearing mid-string after a `\|` inside a quoted `grep` pattern, which precedes none of
   the three anchors).
2. **Check C (squash-merged-and-finished) operationalized precisely**, since AC6 explicitly warns
   this is "the criterion most likely to be faked by a test that reproduces the wrong shape": fires
   only when **all** of — (a) `git rev-list --count origin/main..HEAD` > 0 (there are unpushed-or-
   ahead commits), (b) `git merge-base --is-ancestor HEAD origin/main` fails (HEAD is genuinely not
   an ancestor — rules out an ordinary behind-main branch, which the ancestor check would still
   pass), (c) the two-ref content diff `git diff origin/main HEAD` is empty (no real new content),
   and (d) the three-dot ancestor-based diff `git diff origin/main...HEAD` is non-empty (there
   *appears* to be a diff by the misleading measure). This is a real, narrow reproduction of the
   documented shape, not a "branch is behind main" false trigger.
3. **Check B's "current week"** is computed via ISO calendar week (`datetime.now(timezone.utc)
   .isocalendar()`, formatted `YYYY-Www` — matches the existing shard-folder naming exactly), then
   `git status --porcelain -- agent-monitoring/data/<week>/` checked for any output.
4. **Every git/subprocess call failure (detached HEAD, non-tracking branch, no `origin/main` ref
   locally) degrades that one check to silent no-finding, never a traceback** — matches
   Assumption 4 and the hook's own advisory-only contract; a `try/except: pass` around the whole
   `main()` is the final backstop, matching `cd_prefix_advisory_hook.py`'s own pattern exactly.
