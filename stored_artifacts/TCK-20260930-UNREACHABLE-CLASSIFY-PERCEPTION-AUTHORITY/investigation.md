---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260930-UNREACHABLE-CLASSIFY-PERCEPTION-AUTHORITY
artifact_type: investigation
tags: [investigation, root-cause, corpus, cognition]
---

# Investigation — TCK-20260930-UNREACHABLE-CLASSIFY-PERCEPTION-AUTHORITY

Confirm-not-rederive pass on the last corpus ticket. Verdict `UNDECLARED` confirmed; the full evidence, the declaration inventory
and the decision facts are in `TCK-20260920-PERCEPTION-UPDATE-PHASE-NEVER-INSTANTIATED`'s Implementation Notes (epic Deliverable 2).

Key results at branch tip `d96abd0d5`: the phase is uninstantiated (2 scenario tests pass); nothing reads `PerceptionModel`; the phase's
input `world_signals` also has no production producer (`LegendFactService.to_world_signal`, tests only); strategy uses the raw
`nearby_entities(radius=10.0)` query; tactics use `PerceptionGate` per target with a permissive exception fallback. The covered
ticket's "nothing declares" is partly wrong: the Mechanics Bible §5 (+ parity `STRAT-238`) declares the radius view, and
`perception_contract.md` (+ `STRAT-261`, registry `perception`) declares a `PerceptionModel` pipeline that does not exist. Bible-wins
precedence deliberately not applied (it settles legacy-vs-Bible, not Bible-vs-domain-contract). Decision needs a human; none is made.
