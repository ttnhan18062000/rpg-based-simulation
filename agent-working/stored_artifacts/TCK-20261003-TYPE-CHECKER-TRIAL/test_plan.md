---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261003-TYPE-CHECKER-TRIAL
artifact_type: test_plan
tags: [delivery]
---

# Test Plan — TCK-20261003-TYPE-CHECKER-TRIAL

A report-only ticket: the evidence is the measurements and their reproducibility, not new code.

- Re-run the exact commands written in the decision record on the pinned clone and confirm counts match within the stated variance (error counts exactly; wall time and memory within a stated range).
- Baseline checks per tool: unrelated-edit-above and new-error cases, shown with commands and outputs.
- `tests/docs`, `test_generate_registry`, `validate_frontmatter` on the new doc; old-root guard; the docs index (`docs/REGISTRY.yaml`) regenerates.
- Static scope check: `git diff --stat` shows only the decision record, the ticket, its staging artifacts, registry and monitoring shards.
- All heavy runs one at a time under `MemoryMax=2G`, exit status checked separately; no installation into the main environment.
