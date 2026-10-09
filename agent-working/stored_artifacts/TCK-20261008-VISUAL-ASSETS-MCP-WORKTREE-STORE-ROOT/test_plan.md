---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261008-VISUAL-ASSETS-MCP-WORKTREE-STORE-ROOT
artifact_type: test_plan
date: 2026-10-09
tags: [architecture, testing]
---

# Test plan

- `test_store_root.py` (13): default, env selection and derived roots (fresh interpreter), four refusals, four store-format-version refusals, committed catalog version, refusal stops an interpreter, label shape.
- `drawing/test_store_root_stdio.py` (5): submit_candidate stages into the named checkout and not the real one, label in every store tool result, default label, refusal stops the server, root printed on stderr.
- Mutants A-G (`mutant_proof.txt`). Scoped suites: `pytest tests/visual_assets tests/docs tests/static tests/architecture`.
