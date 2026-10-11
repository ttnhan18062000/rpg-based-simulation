---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261011-SESSION-START-FOR-ROLE-ISSUES
artifact_type: plan
tags: [ai, process-improvement, governance]
---

# plan — TCK-20261011-SESSION-START-FOR-ROLE-ISSUES

## Design
- `role_issues_text(role)` in `tools/sessions/session_start_hook.py`: one `gh issue list --label for:<role> --state open --json number,title,createdAt --limit 11`, `subprocess.run(timeout=3.0, stdin=DEVNULL)`; any exception, non-zero exit or non-list JSON returns "".
- Called from `bind()` after the handover note, only for `startup`, `resume` and `clear`. A second instance uses `role.role` for the label.
- Timeout fixed at 3 s (`ISSUE_TIMEOUT_S`): long enough for a healthy `gh`, short enough that a TLS stall costs one bounded wait.
- Cap 10 shown, then "... and more" (the limit is 11, so the true total is unknown).
- Opt-out `SESSION_START_ISSUES=off`; `tests/tools/conftest.py` sets it for every tools test so no test reaches the network. The new tests unset it and stub `gh` on PATH.
- Convention documented in `docs/guides/cross_session_messages.md`.

## Scope guard
No fleet count (E2), no label management, no issue bodies, no GitHub writes.
