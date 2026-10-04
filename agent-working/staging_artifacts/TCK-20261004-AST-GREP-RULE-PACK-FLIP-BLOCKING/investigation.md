---
status: active
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261004-AST-GREP-RULE-PACK-FLIP-BLOCKING
artifact_type: investigation
tags: [architecture, delivery]
---

# Investigation — TCK-20261004-AST-GREP-RULE-PACK-FLIP-BLOCKING

- After ticket 1, `ast_grep` is report-only only because it is named in `REPORT_ONLY_TOOLS`; it is not skippable, so a missing `ast-grep` binary already exits 2.
- `codebase/gates/sarif_feedback.py` already includes ast-grep (since #318); nothing more to decide there (decision 8.19).
- 111 `ast_grep` rows were seeded by #315 (rules N3, N4, E3). Per-rule counts and a sample review are the soak review's job.
- The flip changes exactly one frozenset and the tests/docs that pin it.
