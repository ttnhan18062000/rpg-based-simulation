---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261007-SESSION-GUARD-QUOTED-TEXT-FALSE-POSITIVE
phase: done
date: 2026-10-07
tags: [ai, process-improvement]
---

# TCK-20261007-SESSION-GUARD-QUOTED-TEXT-FALSE-POSITIVE

## Title
Guard classifier treats heredoc bodies and quoted text as commands, so read-only notes mentioning push/merge ask the owner

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
A `python3 - "$f" <<'EOF' ... EOF` heredoc editing a handover note (body mentioning commit/push/PR, unbalanced `'''` and `;`) made `_SEGMENT_SPLIT` cut the body, shlex fail ("unparseable"), and `critical_text` match "push", so the guard asked the owner. Dispatched by agent-working-planner (owner pain).

## Scope
`tools/sessions/classify.py`: `strip_text` removes heredoc bodies and quoted text strings before segment splitting, `mentions_governed`, `_AUTHORITY_WORDS` and `critical_text` (guard.py calls it). Kept as code: `eval`/`sh -c` payloads, heredocs fed to a shell, command substitutions inside double quotes, heredocs with no terminator, unbalanced quotes (fail closed). A redirect to a file other than /dev/null makes a segment non-read-only (`cat > CLAUDE.md <<EOF` is `governing_file_edit`).

## Out of Scope
Python/other interpreter code in a quoted `-c` payload (guardrail, not a sandbox).

## Acceptance Criteria
- [x] the handover-note heredoc shape is allowed, no ask
- [x] `bash -c "git push origin main"` still asks
- [x] `git commit -m "$(cat <<'EOF' ... push ... EOF)"` is commit only
- [x] `cat > CLAUDE.md <<EOF`, `sed -i ... settings.json` still `governing_file_edit`
- [x] unbalanced quote with an authority word still asks
- [x] `pytest tests/tools -k "session or guard or classify"` green (792 passed)

## Related Tickets
TCK-20261007-SESSION-GUARD-CRITICAL-ONLY-ASKS (#410)

## Related Docs
docs/plans/agent_infrastructure/session_layer_working_process.md section 10

## Related Stored Artifacts
None (hotfix).

## Related Code Areas
tools/sessions/classify.py, tools/sessions/guard.py, tests/tools/test_session_classify.py

## Assumptions / Open Questions
Known residual: a quoted `python3 -c "...os.system('git push')"` payload is now treated as text (planner's spec strips quoted strings except shell payloads).

## Implementation Notes
See Scope. A quoted plain word (`"main"`) is kept as an operand.

## Test Summary
11 new tests in test_session_classify.py; 792 passed in the session/guard/classify selection.

## Files Changed
tools/sessions/classify.py, tools/sessions/guard.py, tests/tools/test_session_classify.py, this ticket, monitoring shards, retro/RETRO-2026-W41.md (planner's retro, folded in on request).

## Completion Summary
Heredoc bodies and quoted text no longer count as commands; write targets, shell payloads and substitutions still do.
