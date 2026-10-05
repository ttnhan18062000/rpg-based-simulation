---
status: active
layer: ai
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261004-SESSION-LAYER-M2B-ROLE-AWARE-SESSIONSTART-AND-BINDING
phase: open
date: 2026-10-04
tags: [ai]
---

# test_plan — TCK-20261004-SESSION-LAYER-M2B-ROLE-AWARE-SESSIONSTART-AND-BINDING

`tests/tools/test_session_resolve_and_hook.py` (34): resolution table (start, resume, fork, clear, compact, plain claude, unknown title, disagreement), instance ids, diff and reduction flag, card + only own handover, fallback listing + one hint, binding per start and instance update, lease taken by writer only, foreign lease reported not stolen, digest message/silence, cross-cwd transcript hint only, second live holder flagged, fail-open on bad payloads and unreadable manifest.

## Proof Plan
- level: unit and integration with the real manifest and card templates copied to a tmp root; state in a tmp git repo
- proof kind: automated tests
- oracle source: git, /proc and the real manifest
- expected effect: as stated in the ticket's acceptance criteria
- selected commands: `pytest tests/tools/test_session_state.py tests/tools/test_session_resolve_and_hook.py tests/tools/test_session_launch.py`
