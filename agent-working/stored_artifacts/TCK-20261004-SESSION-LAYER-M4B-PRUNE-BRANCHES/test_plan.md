---
status: active
layer: ai
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261004-SESSION-LAYER-M4B-PRUNE-BRANCHES
phase: open
date: 2026-10-05
tags: [ai]
---

# test_plan — TCK-20261004-SESSION-LAYER-M4B-PRUNE-BRANCHES

`tests/tools/test_session_prune_branches.py` (13): merged-PR class; squash-merged branch with later unmerged commits never deletable; hint-only separate; worktree/open-PR/young skipped; `gh` unavailable skips all; dry run changes no ref; backup exists before the deletion and restore works; a moved branch is left alone; remote deleted only when tip equals the merged head and only with `--remote`; backup never overwrites; `fetch_prs` failure -> None.

## Proof Plan
- level: unit and integration with real temporary git repositories
- proof kind: automated tests, plus a run against this repository as a positive control
- oracle source: git itself, the real manifest
- expected effect: as stated in the ticket's acceptance criteria
- selected commands: `pytest tests/tools/test_session_route.py tests/tools/test_session_status.py tests/tools/test_session_prune_branches.py tests/tools/test_session_cards.py tests/tools/test_session_roster.py`
