---
status: active
layer: ai
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261004-SESSION-LAYER-M4A-STATUS-DISK-AND-RETIREMENT-REPORT
phase: open
date: 2026-10-05
tags: [ai]
---

# test_plan — TCK-20261004-SESSION-LAYER-M4A-STATUS-DISK-AND-RETIREMENT-REPORT

`tests/tools/test_session_status.py` (11): seeded repo with 5 worktrees incl. mid-rebase; every field; a before/after file hash snapshot proves no change; disk warning at 85% (not 84%) in size order; retirement report excludes dirty/unique/rebase/PR/unknown-PR/current; `gh` missing, nonzero and garbage -> `pr: unknown`; missing state directory -> unknown not none; prunable worktree; a run against the real repo.

## Proof Plan
- level: unit and integration with real temporary git repositories
- proof kind: automated tests, plus a run against this repository as a positive control
- oracle source: git itself, the real manifest
- expected effect: as stated in the ticket's acceptance criteria
- selected commands: `pytest tests/tools/test_session_route.py tests/tools/test_session_status.py tests/tools/test_session_prune_branches.py tests/tools/test_session_cards.py tests/tools/test_session_roster.py`
