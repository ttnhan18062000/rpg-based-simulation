---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260930-SKILL-PATH-MONITORING-NULL-TS-AND-VERDICT-STRICTNESS
artifact_type: investigation
tags: [ai]
---

# Investigation

- `record_events.py` line 17 `REQUIRED` includes `ts`; a null-ts event aborts the whole batch atomically (exit 1, nothing written). implement-ticket.js pushes the Parity-skipped event with no ts (~L1403) and the prompt tells the agent to set it to END_TS; on the skill path a hand-executor can miss it.
- Verdict gates compare against exact strings; the schema enum is only a prompt hint on the skill path.
- Decision rationale is in the ticket's Implementation Notes.
