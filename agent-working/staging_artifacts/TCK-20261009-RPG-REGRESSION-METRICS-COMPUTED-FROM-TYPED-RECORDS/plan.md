---
status: active
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20261009-RPG-REGRESSION-METRICS-COMPUTED-FROM-TYPED-RECORDS
artifact_type: plan
tags: []
---

# Plan (proposal; needs rpg-planner's yes on the observer and on the three open questions)

1. `src/observability/run_ledger.py`: a `RunLedger` observer beside `StarvationRecorder` (same run_state hook, same WARNING-severity/closing-tally/live-header treatment). Per tick it counts accepted and rejected resolver transfers by (kind group, source_kind, transfer_kind), eaten food units by source, entity-ticks outside world bounds (with up to 5 examples), coin created outside declared sources (from the conservation record), deaths by cause and kind group, and population per kind group at sample ticks. Closing event `rpg_gate_ledger_tally`.
2. `src/observability/rpg_gate_metrics.py` (ALL definitions live here, per testing's hash constraint): `compute` reads simulation_events.jsonl + the final state and returns V1-V7 (violations + <=5 examples, oracle citation) and O1-O7 (per-seed values, each with a floor and a fiction reason), `scope: run|pooled`; `pool` combines a world's seeds (`O2.seeds_with_survivors`, V7, the hunt instance); a paired-comparison function (mean, SD, paired SE, k, drift flag).
3. `tools/test_architecture/rpg_gate_known.yaml`: owned `state: fail` entries for every validity check expected red at M0 (at least V3), each with ticket and expiry, BEFORE v1 is recorded.
4. Tests per metric: a constructed counterexample that fails it and a clean run that passes it; determinism (the per-run document identical across two runs); an architecture test that the module reads no live state and imports no engine decision logic.

## Open questions for rpg-planner
Q1. OK to add the RunLedger observer (new src file + one more hook in run_state; kernel unchanged)? The alternative (compute re-derives from events only) cannot supply V1/V2/V4/V5/V6.
Q2. V6/V2 need an initial-coin reference. Proposal: the ledger records `total_coin` at the first observed tick and at the end, plus the minting the conservation resolver already stamps as declared sources; V6 = delta not explained by declared sources.
Q3. Per-metric floors (practical floor with a fiction reason, never fitted) and k: proposals to come with the draft table; rpg-designer to confirm the fiction reasons.
