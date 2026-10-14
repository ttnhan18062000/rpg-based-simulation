---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261011-SESSION-START-FOR-ROLE-ISSUES
artifact_type: investigation
tags: [ai, process-improvement, governance]
---

# investigation — TCK-20261011-SESSION-START-FOR-ROLE-ISSUES

- The hook's context is assembled in `bind()`; the handover note is its last part, so the issue list goes right after it.
- `compact` re-injects an already-loaded context; skipping the call there avoids a pointless network wait.
- `subprocess.run(timeout=...)` kills the child on timeout; the stub uses `exec sleep` so no grandchild holds the pipe in the hang test.
- Existing hook tests call `build_context` directly; without an opt-out they would shell out to the real `gh`. A tools-wide autouse env var is the smallest guard.
- Issue titles come from anyone with write access to the repo: they are rendered on one line, cut at 100 chars and labelled as data.
