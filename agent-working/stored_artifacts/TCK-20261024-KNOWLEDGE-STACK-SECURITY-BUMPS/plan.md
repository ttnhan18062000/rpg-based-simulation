---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261024-KNOWLEDGE-STACK-SECURITY-BUMPS
artifact_type: plan
tags: [knowledge-store, security]
---

# Plan

Follow the ticket's Scope 1-6: disk check, baseline eval and five spot queries on the current pins, a throwaway venv with the three new pins, a scratch index and the same eval, an mcp stdio smoke and graphify query/update smokes, then the decision rule (all three if metrics are not lower and both smokes pass), pin update, in-place upgrade of the main venv, cleanup.
