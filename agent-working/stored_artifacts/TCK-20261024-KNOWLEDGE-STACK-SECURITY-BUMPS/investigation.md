---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261024-KNOWLEDGE-STACK-SECURITY-BUMPS
artifact_type: investigation
tags: [knowledge-store, security]
---

# Investigation

- Main `.venv-knowledge` had no pip (uv-built) and sentence-transformers 5.6.0 although the file pins 6.1.0; `uv pip install --python` was used.
- Index dir is fixed per worktree (`KNOWLEDGE_INDEX`), so the scratch index was built by moving the baseline index aside, building with the throwaway venv, then keeping the candidate index as the real one.
- graphifyy: no 0.8 -> 0.9 changelog upstream; behaviour tested instead (see the ticket).
- docs_to_update: none
