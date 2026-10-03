---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260902-SOCIAL-CANONICAL-HASH-GAP
phase: done
date: 2026-09-02
tags: [social, determinism]
---

# TCK-20260902-SOCIAL-CANONICAL-HASH-GAP

## Title
Close the SocialComponent/SocialBond canonical-hash coverage gap

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
**Correction on pickup (2026-09-03):** re-verified directly against current code — same discipline
applied to the parallel Knowledge-axis ticket, which found real drift. Here the field count itself was
undercounted at scoping time (not code drift since 2026-09-02, unlike the Knowledge ticket — no
`SocialComponent` fields were added by M3): `EntityState.to_canonical_dict()`'s `"social"` sub-dict
covers 10 of `SocialComponent`'s **17** real fields (not 15 as originally counted), leaving **7**
uncovered, not 5: `debt_history`, `salience_history`, `nemesis_ids`, `place_attachment`,
`betrayal_records`, `last_offer_tick`, `rejection_count`. Also corrected: the consumer claim.
`world_compile_report.json`'s `state_hash` is NOT this hash — that comes from the separate,
already-lightweight `StateFingerprinter.get_fingerprint()`. The real consumer is
`CanonicalStateHasher.to_canonical_data()`/`get_hash()` (`src/engine/checkpoint.py`), used directly by
`src/engine/kernel.py`'s per-tick and final-run determinism checks (see
`TCK-20260902-KNOWLEDGE-CANONICAL-HASH-GAP` for the full verification of this consumer chain, not
re-derived here).

All 7 fields confirmed real, actively-consumed durable state, not derived: `nemesis_ids` gates cognition
target evaluation (`src/engine/cognition.py`), `rejection_count` feeds contract appraisal
(`src/systems/social_systems/appraisal.py`), `salience_history` gates memory pruning
(`src/systems/social_systems/memory.py`), and all 7 are read/written in
`src/systems/social_systems/relationships.py`. Notably `betrayal_records` (the actual event list) was
uncovered while `betrayal_count` (its own derived count) was already covered — an inconsistent partial
gap, not a deliberate exclusion.

## Scope
- Add all 7 confirmed-live fields to `EntityState.to_canonical_dict()`'s `"social"` sub-dict:
  `debt_history`, `salience_history`, `nemesis_ids`, `place_attachment`, `betrayal_records`,
  `last_offer_tick`, `rejection_count`.
- Update `docs/parity_ledger/social_narrative.yaml` (or the correct shard) with the new status, using
  `tools/parity_ledger_writer.py` (never a raw YAML edit).
- Update `docs/core/state.md` if its canonical-hash coverage claims reference `SocialComponent` field
  counts.

## Out of Scope
- The `RelationshipRole`/`nemesis_ids` reconciliation question (tracked separately, see Related Tickets).
- Any change to `SocialComponent`/`SocialBond`'s own field semantics, clamp ranges, or decay behavior —
  this ticket is coverage-only, not a behavior change to social mechanics themselves.
- `StrategicComponent`'s parallel gap (separate ticket, see Related Tickets) — do not batch the two
  fixes into one PR; they touch different components and should land independently so a determinism
  test failure in one doesn't block the other.

## Acceptance Criteria
- [x] All 7 currently-uncovered fields have an explicit, recorded decision (covered or justified-excluded).
      All 7 added — none legitimately excludable, all confirmed real, consumed durable state.
- [x] `to_canonical_dict()` changes (if any) are covered by a new or updated determinism test that fails
      before the fix and passes after, on the specific field(s) added. 2 new tests added, both passing.
- [x] Existing canonical-hash/replay determinism tests still pass unchanged. 405 passed, 1 skipped
      (pre-existing, unrelated) across `tests/unit/core/`, `tests/unit/engine/`, `tests/unit/kernel/`,
      `tests/certification/`; 259 passed across `tests/unit/social/` + strategic social-contract tests.
- [x] Parity ledger entries reflect the new status with real evidence (no fabricated citations).
      `SOC-263` added via `tools/parity_ledger_writer.py`, index confirmed FRESH.

## Related Tickets
- TCK-20260902-KNOWLEDGE-CANONICAL-HASH-GAP (parallel gap, StrategicComponent — separate PR)

## Related Docs
- `docs/brainstorm/2026-09-02-core-rpg-social-relationship-axis-proposal.md` (source investigation, §3.1)
- `docs/simulation/social_systems_contract.md`
- `docs/plans/rpg_design_roadmap/rpg_social_narrative_mechanics_hardening_plan.md`
- `docs/core/state.md`

## Related Stored Artifacts
(none yet — investigation already captured in the brainstorm doc above; standard staging artifacts to
be created when this ticket is picked up for implementation)

## Related Code Areas
- `src/core/state.py` (`EntityState.to_canonical_dict()`, `"social"` sub-dict, ~line 800)
- `src/core/models/social.py` (`SocialComponent`, `SocialBond`, `BetrayalRecord`)
- `src/engine/checkpoint.py` (`CanonicalStateHasher` — the real consumer)
- `src/engine/kernel.py` (per-tick and final hash computation call sites)
- `docs/parity_ledger/social_narrative.yaml`

## Assumptions / Open Questions
- Whether all 5 missing fields should be added, or whether some are legitimately excluded (e.g. derived
  fields with no independent authoritative meaning) — this is the ticket's own central decision, not
  pre-resolved by the source investigation.
- Adding fields to the canonical hash changes `state_hash` for any world compiled after this lands —
  confirm whether existing golden/reference `world_compile_report.json` fixtures need regeneration.

## Implementation Notes
Re-verification against current code found the original field count undercounted (17 real fields, not
15; 7 uncovered, not 5) — unlike the parallel Knowledge ticket, this wasn't code drift from M3 (no
`SocialComponent` fields were added since the investigation), just an undercount at scoping time. Also
corrected the same consumer-chain claim as the Knowledge ticket (`CanonicalStateHasher` via
`src/engine/kernel.py`, not `world_compile_report.json`). All 7 fields were confirmed real,
actively-consumed durable state via direct grep against `src/engine/cognition.py`,
`src/systems/social_systems/{appraisal,memory,relationships}.py` — none had a documented derivation
rationale (unlike `StrategicComponent.profile`), so no exclusions were made. `nemesis_ids` (a `Set[int]`)
is serialized via `sorted(...)` rather than `asdict`, matching how other non-dataclass collection fields
are handled elsewhere in the same method.

## Test Summary
- 2 new tests added to `tests/unit/core/test_entity_integrity.py`:
  `test_social_seven_newly_covered_fields_participate_in_canonical_hash` (all 7 fields, one loop),
  `test_social_nemesis_ids_participates_in_canonical_hash_end_to_end` (dedicated end-to-end
  `CanonicalStateHasher.get_hash()` check, mirroring the Knowledge ticket's `source_trust` test). Both
  pass.
- Full scoped run: `pytest tests/unit/core/ tests/unit/engine/test_hash_scheduler.py
  tests/unit/engine/test_resource_budget_gate.py tests/unit/kernel/ tests/certification/ -m "not slow"` →
  405 passed, 1 skipped (pre-existing, unrelated), 0 failed.
- Also ran `tests/unit/social/` + `tests/unit/strategic/test_strategic_social_contracts.py` +
  `tests/unit/strategic/test_social_contract_materialization.py` → 259 passed.

## Files Changed
- `src/core/state.py` — `EntityState.to_canonical_dict()`'s `"social"` sub-dict: added 7 fields.
- `tests/unit/core/test_entity_integrity.py` — 2 new tests.
- `docs/parity_ledger/social_narrative.yaml` — new entry `SOC-263`, written via
  `tools/parity_ledger_writer.py`.
- `tickets/inprogress/TCK-20260902-SOCIAL-CANONICAL-HASH-GAP.md` → moved to `tickets/done/`.

## Completion Summary
Closed the `SocialComponent` canonical-hash coverage gap. The real gap (7 fields, not the originally
estimated 5) is now fully covered in `EntityState.to_canonical_dict()` — `debt_history`,
`salience_history`, `nemesis_ids`, `place_attachment`, `betrayal_records`, `last_offer_tick`,
`rejection_count`, all confirmed real and actively consumed. Corrected the same consumer-chain
misattribution found in the parallel Knowledge ticket along the way. All existing determinism/social
tests still pass unchanged; 2 new tests lock in the fix. Landed independently from
`TCK-20260902-KNOWLEDGE-CANONICAL-HASH-GAP`, per that ticket's own explicit "do not batch" scope guard.
