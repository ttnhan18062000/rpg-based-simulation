---
status: historical
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20260914-COOPERATION-FIND-PENDING-OFFER-COST-OBSERVED
artifact_type: investigation
date: 2026-10-14
tags: [performance, social]
---

# Investigation: TCK-20260914-COOPERATION-FIND-PENDING-OFFER-COST-OBSERVED

Checked on origin/main 0fba246ed with `git show`, not the working tree.

- `git log -1 56cfd0410`: "engine: Pending-offer lookup uses a per-tick index: cooperation phase from about 11 s to about 4 ms per tick on movement[5000] (1 ticket) (#394)".
- `src/domains/cooperation/phase.py:91` builds `pending_offers = build_pending_offer_index(state)` once per tick, and `:119` calls `CooperationDecisionService.find_pending_incoming_offer(entity, state, pending_offers)` with that index. So the per-call scan this ticket measured (about 2.0 s over 4500 calls) is gone.
- `agent-working/tickets/done/` holds the fixing ticket `TCK-20261006-COOPERATION-PENDING-OFFER-SCAN-IS-QUADRATIC-PER-TICK`.
- Still open, and not this ticket's: PERF-M2-T08 (2026-10-13) measured cooperation at about 30-260 ms per tick in the strategic_100 and mixed_200 scenarios under the canonical variants. That is a separate cost-growth question for perf's tick-cost-growth investigation (filed after the owner's (i)/(ii)/(iii) decision), which starts from this ticket's A/B per-phase table.
