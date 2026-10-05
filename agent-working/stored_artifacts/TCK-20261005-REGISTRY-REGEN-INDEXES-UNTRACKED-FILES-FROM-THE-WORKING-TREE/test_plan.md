---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261005-REGISTRY-REGEN-INDEXES-UNTRACKED-FILES-FROM-THE-WORKING-TREE
artifact_type: test_plan
tags: []
---

# Test plan
`tests/tools/test_close_sequence_repairs.py` (temporary git repos): untracked ticket and untracked doc not indexed while a tracked one is; staged file indexed; `include` indexes the untracked closing ticket (file, glob for nested epic ticket, directory); untracked artifact files dropped from a tracked ticket's list; non-git root indexed as before; subdirectory of a repo not filtered; `--check` agrees with the committed tree despite an untracked draft; CLI `--include-untracked`.
Existing `tests/tools/test_generate_registry.py` and `test_done_checker_static.py` re-run.

## Proof Plan

- level: unit (generation) plus the real-tree `--check`
- proof kind: regression tests plus `generate_registry.py --check` on this worktree with both drafts untracked
- oracle source: the committed tree (what CI sees) is the registry's contract
- expected effect: untracked files never reach the registry; the closing ticket still does
- selected commands: `pytest tests/tools tests/docs`; `generate_registry.py --output docs/REGISTRY.yaml --check`
