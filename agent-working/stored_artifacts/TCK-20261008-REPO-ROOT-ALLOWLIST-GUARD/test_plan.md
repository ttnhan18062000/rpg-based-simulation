---
status: historical
layer: architecture
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261008-REPO-ROOT-ALLOWLIST-GUARD
phase: done
date: 2026-10-08
tags: [architecture, delivery]
---

# test_plan — TCK-20261008-REPO-ROOT-ALLOWLIST-GUARD

Normal flow: real tracked root equals the allowlist.
Edge: new files under src/, tools/, a domain root do not change the root set; the parse is not vacuous.
Failure mode: a new root file or directory fails with a message naming the guideline; a tracked entry removed from the repo but still listed also fails.
Mutation: stage `zz_extra.txt`, expect the real test to fail, then remove it.

## Proof Plan
- level: unit plus one real-repo static check
- proof kind: automated tests and one manual mutation
- oracle source: `git ls-files` and the guideline's allowlist section
- expected effect: passes on the real root; fails on an extra tracked root entry, naming the guideline
- selected commands: `pytest tests/codebase/test_repo_root_allowlist.py` (4 passed); mutation: `git add zz_extra.txt` then the same command (failed as expected), then `git rm -f zz_extra.txt`
