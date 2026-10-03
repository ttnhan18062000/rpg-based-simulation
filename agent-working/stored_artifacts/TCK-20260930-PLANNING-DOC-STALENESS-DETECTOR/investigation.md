---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260930-PLANNING-DOC-STALENESS-DETECTOR
artifact_type: investigation
tags: [documentation]
---

# Investigation

- Premise re-verified against origin/main on 2026-09-30: `idea_agent_monitoring_active_duration.md` is still `status: idea` although `TCK-20260822-DURATION-ACTIVE-IDLE-SPLIT` is done; `standalone_items.md` items 3-4 still say "ready, schedule later" although `TCK-20260904-WORKING-LOG-CSV-PARSER` and `TCK-20260904-PROVIDER-PORTABILITY-CONFORMANCE-TEST` are done. Both real drift cases stand.
- The folder `tickets/todos/planning-doc-status-drift/` held exactly one ticket (no SEQUENCE.md).
- First cut (identity text = every heading, no date guard) returned 17 findings, most false: 2026-06-19 E-series tickets matched idea docs written later purely on shared words. Restricting the idea-doc identity text to file stem + H1, lowering the threshold to 75% (needed for `DURATION-ACTIVE-IDLE-SPLIT`, whose "split" is not in the doc) and adding the ticket-not-older-than-doc guard gave 5 findings: the 3 expected and 2 real extras (`idea_semantic_entity_index.md` vs `TCK-20260822-SEMANTIC-ENTITY-INDEX`, `idea_world_rendering_core.md` vs `TCK-20260820-EPIC-WORLD-RENDERING-CORE`). The semantic-index doc already carries a "Superseded" banner but its frontmatter still says `idea`.
- Limitation, unchanged: no structured back-link from tickets to planning docs exists, so matching is by title keywords and will miss renamed work.
- The five findings are left for a person to resolve (the ticket's Out of Scope); the idea doc that motivated this ticket was archived because this ticket ships it.
