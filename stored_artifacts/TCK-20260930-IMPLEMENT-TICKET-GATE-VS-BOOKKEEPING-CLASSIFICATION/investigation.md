---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260930-IMPLEMENT-TICKET-GATE-VS-BOOKKEEPING-CLASSIFICATION
artifact_type: investigation
tags: [ai]
---

# Investigation

- `grep -c 'bash('` = 50; real call sites = 38 (the ticket's "50" counted comment mentions).
- Probe `wf_df41616a-229` (zero agents, 53 ms, user opt-in 2026-10-01): no shell global exists; `workflow()` nests one level; args pass to the child.
- Parse blockers: implement-ticket.js lines 182 and 1753 only; implement-epic.js 247 (regression from #265 versus the pilot's "parses"); simq-audit.js 475. The acorn test failure on clean main is reproduced here (venv present): it is the implement-epic.js line-247 regression.
- Consequence for the pilot's open question: gates cannot stay orchestrator-side natively, so attestation, not just classification, is the load-bearing design item.
