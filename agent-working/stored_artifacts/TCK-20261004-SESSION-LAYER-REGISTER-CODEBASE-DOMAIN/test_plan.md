---
status: historical
layer: ai
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261004-SESSION-LAYER-REGISTER-CODEBASE-DOMAIN
date: 2026-10-05
tags: [ai, process-improvement, governance]
---

# Test Plan: TCK-20261004-SESSION-LAYER-REGISTER-CODEBASE-DOMAIN

Validator and generator drift check, plus the session tests. Two pinned counts change with reasons.

## Proof Plan

- Level: unit and registry validation.
- Proof kind: executable validator and tests.
- Oracle source: the ticket's acceptance criteria and `tools/sessions/validate.py`.
- Expected effect: validate reports 0 findings for 12 roles; generate_agents --check reports no drift; no existing card changes.
- Selected commands: `python3 -m tools.sessions.validate`; `python3 -m tools.sessions.generate_agents --check`; `pytest tests/tools -k session`.
