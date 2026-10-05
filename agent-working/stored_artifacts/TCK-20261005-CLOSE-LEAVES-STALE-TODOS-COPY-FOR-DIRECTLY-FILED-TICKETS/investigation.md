---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261005-CLOSE-LEAVES-STALE-TODOS-COPY-FOR-DIRECTLY-FILED-TICKETS
artifact_type: investigation
tags: []
---

# Investigation
Verified against `origin/main`: CLAUDE.md "After Work" deletes only `todos/{folder}/` source copies; `done_checker_static` had no sibling-copy check; `find_closed_ticket_resurrections` in `tools/validate_frontmatter.py` is reached only by a corpus test at PR time (hit by #347).
Reuse: the closure tool already knows the closing ticket's id and the active dirs, so removal lives there; the checker only needs a basename scan of `todos/`.
