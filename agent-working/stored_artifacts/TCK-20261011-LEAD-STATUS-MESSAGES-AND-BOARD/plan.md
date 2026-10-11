---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261011-LEAD-STATUS-MESSAGES-AND-BOARD
artifact_type: plan
tags: [ai, process-improvement, governance]
---

# plan — TCK-20261011-LEAD-STATUS-MESSAGES-AND-BOARD

## Steps
1. Add `status-request` and `status-report` rows to the Classes table of `docs/guides/cross_session_messages.md` and to the plan §9.0 table, same sender and receiver, plus the information-only sentence.
2. Add the lead-as-information-hub paragraph to §9.0 and the 2026-10-09/10 owner decisions to §12.3. §12.5 is left to E3.
3. Create `agent-working/lead/board.md`: frontmatter, advice-only note, the seven columns, no rows.
4. Replace the deferred comment in the lead domain's `owns` with `agent-working/lead/**`; regenerate cards.
5. Add `tests/docs/test_lead_status_protocol.py`.

## Scope guard
No fleet, heartbeat or dispatch authority for the lead; the board stays empty.
