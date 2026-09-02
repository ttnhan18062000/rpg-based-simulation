---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260902-SOCIAL-CANONICAL-HASH-GAP
phase: open
date: 2026-09-02
tags: [social, determinism]
---

# TCK-20260902-SOCIAL-CANONICAL-HASH-GAP

## Title
Close the SocialComponent/SocialBond canonical-hash coverage gap

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
`EntityState.to_canonical_dict()` (`src/core/state.py`) includes a `"social"` sub-dict but covers only
10 of `SocialComponent`/`SocialBond`'s 15 real fields. A same-seed divergence confined to the other 5
fields would go completely undetected by the canonical determinism hash — the authoritative hash used
for `world_compile_report.json`'s `state_hash`, distinct from `StateFingerprinter`'s already-known,
explicitly-non-canonical near-zero coverage. Full field inventory, current coverage table, and the
required direction are already worked out in
`docs/brainstorm/2026-09-02-core-rpg-social-relationship-axis-proposal.md` §3.1 — this ticket promotes
that finding into an implementable repair.

## Scope
- Enumerate the exact 5 uncovered fields (per the axis proposal doc's §3.1 table) and, for each one,
  decide: add it to `to_canonical_dict()`, or document explicitly why it is legitimately excluded
  (e.g. genuinely non-authoritative / derived / presentation-only).
- Implement the decided coverage change in `src/core/state.py`.
- Update `docs/parity_ledger/social_narrative.yaml` (or the correct shard) with the new/confirmed status
  per field, using `tools/parity_ledger_writer.py` (never a raw YAML edit).
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
- [ ] All 5 currently-uncovered fields have an explicit, recorded decision (covered or justified-excluded).
- [ ] `to_canonical_dict()` changes (if any) are covered by a new or updated determinism test that fails
      before the fix and passes after, on the specific field(s) added.
- [ ] Existing canonical-hash/replay determinism tests still pass unchanged.
- [ ] Parity ledger entries reflect the new status with real evidence (no fabricated citations).

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
- `src/core/state.py` (`EntityState.to_canonical_dict()`, `SocialComponent`, `SocialBond`)
- `docs/parity_ledger/social_narrative.yaml`

## Assumptions / Open Questions
- Whether all 5 missing fields should be added, or whether some are legitimately excluded (e.g. derived
  fields with no independent authoritative meaning) — this is the ticket's own central decision, not
  pre-resolved by the source investigation.
- Adding fields to the canonical hash changes `state_hash` for any world compiled after this lands —
  confirm whether existing golden/reference `world_compile_report.json` fixtures need regeneration.

## Implementation Notes
(fill in during implementation)

## Test Summary
(fill in during implementation)

## Files Changed
(fill in during implementation)

## Completion Summary
(fill in during implementation)
