---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260924-SETTINGS-HOOK-PINNED-TEST-DRIFT
phase: done
date: 2026-09-24
tags: [ai, agent-monitoring, observability, process-improvement]
---

# TCK-20260924-SETTINGS-HOOK-PINNED-TEST-DRIFT

## Title
Update 3 pre-existing tests pinning `.claude/settings.json`'s exact hook-list shape, broken by
Batch B's two hook edits

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P0

## Request Summary
PR #242 (Batch B: context/token cost reduction) went CI-green locally on every scoped test file
this session ran directly, but the real CI run on the merged/pushed branch (`404b29235`) failed
one job: `API / tools / logging`. Reproducing that job's exact command locally (`pytest tests/api
tests/cli tests/tools tests/logging tests/engine tests/observability -m "not slow and not
extra_slow"`) found 3 real, pre-existing failures this session's own earlier commits caused but
never ran locally: `tests/tools/test_bash_secret_scan_hook.py`'s `test_new_bash_secret_scan_hook_
entry_registered` and `test_existing_bash_and_sidecar_hooks_untouched`, and `tests/tools/test_
settings_json_hooks_wiring.py`'s `test_existing_hook_writers_untouched` — three tests from prior,
unrelated tickets (`TCK-20260904-BASH-SECRET-SCAN-HOOK`, `TCK-20260904-TEST-SCOPER-HANG-GUARD`)
that pin the exact count and literal message content of `.claude/settings.json`'s `PreToolUse`
hook list. `TCK-20260923-CD-PREFIX-ADVISORY-HOOK` appended a 6th `PreToolUse` entry (a 3rd
`Bash`-matcher entry); `TCK-20260923-GREP-HOOK-SEARCH-DOCS-MENTION` changed the grep-nudge hook's
exact message text. Both were correct, intentional, user-confirmed changes — the tests pinning
the OLD shape needed updating to the new one, which this session never ran before committing
either of those two tickets.

## Scope
- `tests/tools/test_bash_secret_scan_hook.py`: `test_new_bash_secret_scan_hook_entry_registered`
  updated from `len(bash_entries) == 2` to `== 3` (grep-nudge, secret-scan, cd-prefix all coexist).
  `test_existing_bash_and_sidecar_hooks_untouched` updated from asserting the literal old string
  `"graphify: Knowledge graph exists"` to asserting the new, correct invariant: `"search_docs"` and
  `"graphify"` both present in the grep-nudge command, `"scan_for_secrets"` still absent.
- `tests/tools/test_settings_json_hooks_wiring.py`: `test_existing_hook_writers_untouched` updated
  from `len(settings["hooks"]["PreToolUse"]) == 5` to `== 6`.
- Searched broadly (`grep -rl "settings.json\|hooks\[.PreToolUse.\]"` across `tests/`) for any
  other test pinning this file's shape — two more files matched
  (`test_settings_json_edit_write_hook_sidecar_scope.py`, `test_subsystem_ownership_lifecycle_doc.py`)
  but both already passed unmodified; not touched.

## Out of Scope
- Any further change to `.claude/settings.json` itself — the hook content from Batch B's two
  tickets is correct and already user-confirmed; this ticket only updates the tests that were
  pinning its now-stale shape.
- Re-running the entire `pytest tests/` suite — scoped to the exact failing CI job's own command
  (`tests/api tests/cli tests/tools tests/logging tests/engine tests/observability`), per CLAUDE.md's
  Testing Rule and to directly reproduce the real CI failure rather than a broader, slower scope.

## Acceptance Criteria
- [x] All 3 previously-failing tests pass with updated, correct assertions (not loosened,
      weakened, or made vacuous — each still pins a real invariant about the file's shape).
- [x] The exact failing CI job's full test scope reproduced locally: 3,108 passed, 0 failed (up
      from 3,105 passed / 3 failed before this fix), confirming this closes the real gap and not
      just the 3 named tests in isolation.
- [x] Broader search for other settings.json-shape-pinning tests confirmed no other file needed
      updating.

## Related Tickets
- `TCK-20260923-CD-PREFIX-ADVISORY-HOOK` (done) — added the 3rd `Bash`-matcher `PreToolUse` entry
  that broke the count assertions.
- `TCK-20260923-GREP-HOOK-SEARCH-DOCS-MENTION` (done) — changed the grep-nudge hook's literal
  message text that one test pinned exactly.
- `TCK-20260904-BASH-SECRET-SCAN-HOOK` / `TCK-20260904-TEST-SCOPER-HANG-GUARD` (done) — the
  original tickets that wrote the now-updated pinned tests.

## Related Docs
None.

## Related Stored Artifacts
None — hotfix tier, self-evident intent, no staging artifacts required per CLAUDE.md.

## Related Code Areas
- `tests/tools/test_bash_secret_scan_hook.py`
- `tests/tools/test_settings_json_hooks_wiring.py`

## Assumptions / Open Questions
None outstanding.

## Implementation Notes
This is a genuine gap in this session's own process, disclosed directly rather than glossed over:
`TCK-20260923-CD-PREFIX-ADVISORY-HOOK` and `TCK-20260923-GREP-HOOK-SEARCH-DOCS-MENTION` each ran
their own scoped test file plus a small, hand-picked regression list before committing, but neither
ran a broad enough scope to catch tests in *other* files that pin `.claude/settings.json`'s shape
from the outside. The real, authoritative catch came from CI running the actual PR's own workflow
job (`API / tools / logging`, which includes the full `tests/tools/` directory) — reproduced
locally per CLAUDE.md's CI Failure Triage steps after the raw log fetch hit the documented
Fortiguard TLS block on `productionresultssa15.blob.core.windows.net` (confirmed via `openssl
s_client`, not assumed) and job-level annotations gave only "exit code 1" with no detail.

Classified per CLAUDE.md's CI triage: a real regression caused by this session's own changes →
hotfix ticket, full pipeline (informal, hand-orchestrated Scope→Implement→Test→Finalize), not a
silent edit-around. Every assertion was corrected to reflect the new, intentional, already-
user-confirmed state — never loosened, weakened, or deleted to force a pass; each still catches a
real drift if the underlying hook count or content changes again unexpectedly.

## Test Summary
- `pytest tests/tools/test_bash_secret_scan_hook.py tests/tools/test_settings_json_hooks_wiring.py -v`
  — 19 passed.
- `pytest tests/tools/test_settings_json_edit_write_hook_sidecar_scope.py tests/docs/test_subsystem_ownership_lifecycle_doc.py -q`
  — 17 passed (unmodified, confirmed not to need updating).
- Full CI-job-scope reproduction: `pytest tests/api tests/cli tests/tools tests/logging tests/engine tests/observability -m "not slow and not extra_slow" --tb=short -q`
  — 3,108 passed, 25 skipped, 29 deselected, 1 xfailed, 0 failed (was 3 failed before this fix).

## Files Changed
- `tests/tools/test_bash_secret_scan_hook.py` — 2 assertions updated.
- `tests/tools/test_settings_json_hooks_wiring.py` — 1 assertion updated.

## Completion Summary
Fixed a real CI failure on PR #242 (Batch B) caused by this session's own two earlier settings.json
hook edits, which never triggered a broad enough local test scope to catch three pre-existing
tests in unrelated files that pin the file's exact hook-list count and literal message content.
Reproduced the exact failing CI job's command locally (after the raw log fetch was blocked by the
documented Fortiguard TLS filter on the results blob host) rather than guessing from job names.
Updated all 3 assertions to the new, correct, already-confirmed state — every one still pins a
real invariant, none loosened to force a pass. Full CI-job-scope reproduction now shows 3,108
passed, 0 failed. No known material gap left unstated.
