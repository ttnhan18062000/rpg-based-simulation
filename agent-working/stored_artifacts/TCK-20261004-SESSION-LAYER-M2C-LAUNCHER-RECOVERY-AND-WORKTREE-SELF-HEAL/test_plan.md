---
status: active
layer: ai
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261004-SESSION-LAYER-M2C-LAUNCHER-RECOVERY-AND-WORKTREE-SELF-HEAL
phase: open
date: 2026-10-04
tags: [ai]
---

# test_plan — TCK-20261004-SESSION-LAYER-M2C-LAUNCHER-RECOVERY-AND-WORKTREE-SELF-HEAL

`tests/tools/test_session_launch.py` (21): command forms incl. --resume <id> and `<role>-N`; every roster role has its generated launcher-only agent file; dry-run never execs; live refused; killed -> recovery; released/none fresh; real mid-rebase flagged NEVER; self-heal (removed, deleted behind git's back, missing branch, no branch, dry-run); transcripts by customTitle across project dirs; replace never deletes; non-interactive never chooses; default-action regression.

## Proof Plan
- level: unit and integration with real git repositories, a real mid-rebase, real kill -9, and one live claude rehearsal
- proof kind: automated tests
- oracle source: git, /proc and the real manifest
- expected effect: as stated in the ticket's acceptance criteria
- selected commands: `pytest tests/tools/test_session_state.py tests/tools/test_session_resolve_and_hook.py tests/tools/test_session_launch.py`
