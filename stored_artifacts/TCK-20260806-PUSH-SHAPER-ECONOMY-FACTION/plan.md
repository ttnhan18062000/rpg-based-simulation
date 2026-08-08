---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260806-PUSH-SHAPER-ECONOMY-FACTION
artifact_type: plan
tags: [observability, engine, economy, faction, simulation-quality]
---

# plan.md — TCK-20260806-PUSH-SHAPER-ECONOMY-FACTION

## Unresolved Questions

None — all deferral verdicts re-confirmed against fresh source reads; the one open design
question (`_seen_diplo_pairs` per-tick vs. per-call scoping) resolved by direct comparison against
the old extractor's own scoping (per-call, matched).

## Steps

1. Extend `src/observability/event_shapers.py` with `EconomyShaper` (7 events) and `FactionShaper`
   (8 events), both registered in `SHAPER_REGISTRY`.
2. New test file `tests/unit/observability/test_event_shapers_economy_faction.py` (20 tests).
3. Real kernel integration verification against `dungeon_crawl` — no code change from this, purely
   a correctness check.

## Scope guard

`event_extractor.py`, `apply.py`, `apply_plan.py`, `kernel.py` all unmodified by this ticket —
confirmed via `git diff`. The 6 deferred events (see investigation.md) are not implemented in any
form, not even partially — no silent scope creep into them.

## Acceptance-criteria map

| Ticket AC | Satisfied by |
|---|---|
| EconomyShaper implements 7 MIGRATE events | Implementation, `test_event_shapers_economy_faction.py` |
| FactionShaper implements 8 MIGRATE events | Same |
| 6 deferred events re-confirmed and disclosed | investigation.md |
| Both registered, no registry redesign | `SHAPER_REGISTRY` extension only |
| Unit tests incl. dedup behavior | `test_diplomatic_transition_deduped_per_ordered_pair_per_call` |
| SHADOW-mode inertness with all 3 shapers | Real kernel integration run, zero live delivery |
| event_extractor.py untouched | Scope guard |
| Scoped pytest passes | 793/793 in tests/unit/observability/ |
