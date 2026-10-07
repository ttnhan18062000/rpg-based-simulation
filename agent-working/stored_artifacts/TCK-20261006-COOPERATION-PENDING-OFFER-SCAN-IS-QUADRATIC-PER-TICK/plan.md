---
status: active
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20261006-COOPERATION-PENDING-OFFER-SCAN-IS-QUADRATIC-PER-TICK
artifact_type: plan
tags: [performance, cooperation, regression]
---

# Plan

1. Index live OFFERED RECRUITMENT contracts by target id once per tick (`build_pending_offer_index`), preserving the first-live choice (lowest offerer id, then lowest contract id; offerer alive and active; offer not expired; no self-offers).
2. `find_pending_incoming_offer` reads the index; `CooperationPhase.execute` builds it once and reuses it. Prove the loop never changes a contract or an active/alive flag before the loop ends (all changes are deferred into the returned update).
3. Split `select` into `accept_pending_offer` and `select_for_own_needs` so the phase can pass the index without a sixth parameter (blocking ratchet). `select` keeps its signature and behaviour.
4. Tests: ordering contract, excluded offers, differential against the verbatim old scan on seeded random worlds, build-once spy. Measure: canonical hashes on six worlds under `audit_mode`, `movement[5000]` before and after.
5. Out of scope: `combat_engagement` and `collection` costs, richer acceptance criteria, perf thresholds.
