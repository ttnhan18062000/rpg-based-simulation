# Investigation — TCK-20260923-CD-PREFIX-ADVISORY-HOOK

## Source and baseline
Batch B ticket 2 of 3 (context/token cost reduction). Driver: `TCK-20260923-BASH-COMMAND-MIX-
BASELINE` measured `cd` as the single largest Bash command head, ~21.5% of all Bash calls (24,943
over W30-W39, `--ref origin/main`-pinned per `TCK-20260923-BASH-MIX-REF-PINNING`). The harness's
own Bash tool description already states the underlying fact directly: "The working directory
persists between Bash calls... never prepend `cd <current-directory>` to a git command — git
already operates on the current working tree, and the compound triggers a permission prompt."

## Context scan
`search_docs`/`graphify` for prior hook precedent surfaced no existing `cd`-specific hook.
Read `.claude/settings.json`'s existing `PreToolUse` section directly (already known from this
session's own ticket 1 work) for the exact advisory shape to match: the sidecar-check hook (inline
shell `case` on file path) and the secret-scan hook (`python3 -c` invoking
`tools/write_path_guard.py::scan_for_secrets`, wrapped in try/except, printing
`hookSpecificOutput.additionalContext` only — no `decision`/block field, ever). The secret-scan
hook is the closer precedent for this ticket since the detection logic itself (more than a one-line
shell case) benefits from being a pure, directly-testable Python function.

## Design decision: narrow, provably-redundant detection only
The measured 21.5% figure is a call-count share, not a defect count — most `cd` calls in that
figure are NOT wasteful (a worktree switch, entering a subproject, a genuine directory change all
require `cd`). Flagging every `cd` would be noisy and untrustworthy advice. The one case that is
*provably* redundant, with no legitimate counter-case, is: the command's `cd <path> && ...` prefix
targets the exact same directory the Bash call is already starting in — since the harness's own
cwd already persists between calls, re-stating it changes nothing and costs a needless prefix.
`detect_redundant_cd_prefix()` fires on exact normalized-path equality only; a `cd` into a
subdirectory, a sibling worktree, or any other different path is explicitly left unflagged by
design (see the "must NOT flag a genuine directory switch" test group).

## Verified: hook fires only on the intended case
Ran the wired hook against real payload shapes end-to-end (`echo '{"tool_input":...}' | python3
tools/agent-monitoring/cd_prefix_advisory_hook.py`): fires with the expected
`hookSpecificOutput.additionalContext` for `cd <cwd> && echo hi`, silent for a plain `echo hi`.
Confirmed `.claude/settings.json` remains valid JSON after the new `PreToolUse`/`Bash` matcher
entry was added.
