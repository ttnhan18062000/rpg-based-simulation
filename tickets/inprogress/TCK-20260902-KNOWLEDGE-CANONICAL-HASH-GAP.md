---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260902-KNOWLEDGE-CANONICAL-HASH-GAP
phase: open
date: 2026-09-02
tags: [cognition, determinism]
---

# TCK-20260902-KNOWLEDGE-CANONICAL-HASH-GAP

## Title
Close the StrategicComponent canonical-hash coverage gap (including live source_trust)

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P0

## Request Summary
`StrategicComponent`'s canonical hash (`src/core/state.py:768-783`) covers only `current_project_id`
and omits `hypotheses`, `source_trust`, `contracts`, and 3 other fields (6 total) — with no comment
explaining why. This is more severe than the parallel `SocialComponent` gap (see Related Tickets):
`source_trust` (`SourceTrustEntry`) is a real, live scoring input to detour selection
(`belief_and_detour_contract.md`'s documented `source_trust_bonus` term), so this gap can let a real
behavioral divergence between two same-seed runs go completely undetected by the determinism hash — not
a hypothetical risk. Full field inventory and required direction are in
`docs/brainstorm/2026-09-02-core-rpg-knowledge-belief-axis-proposal.md` §2.2 — this ticket promotes that
finding into an implementable repair. Priority is P0 (vs. the Social gap's P1) specifically because
`source_trust` is confirmed behaviorally live, not merely a coverage/audit concern.

## Scope
- Enumerate the exact 6 uncovered `StrategicComponent` fields (per the axis proposal doc's §2.2 table)
  and, for each, decide: add to `to_canonical_dict()`, or document explicitly why legitimately excluded.
- Implement the decided coverage change in `src/core/state.py`.
- Specifically confirm and resolve `source_trust`'s exclusion — given it is a live behavioral input, the
  default expectation is that it MUST be added unless a specific, recorded reason says otherwise.
- Update the relevant `docs/parity_ledger/` shard (`strategic_cognition.yaml`) via
  `tools/parity_ledger_writer.py` (never a raw YAML edit).
- Update `docs/core/state.md` if its canonical-hash coverage claims reference `StrategicComponent`.

## Out of Scope
- The `BeliefEntry`/`KnowledgeFact` unreconciled-parallel-systems question (tracked separately, see
  Related Tickets) — that is an architecture-reconciliation question, not a coverage gap.
- `SocialComponent`'s parallel gap (separate ticket) — land independently.
- Any change to `source_trust`'s own scoring formula or `source_trust_bonus` behavior — this ticket adds
  hash coverage only, it does not change how the field is used.

## Acceptance Criteria
- [ ] All 6 currently-uncovered fields have an explicit, recorded decision (covered or justified-excluded).
- [ ] `source_trust` specifically is either added to the canonical hash or has an explicit, reviewed
      rationale on record for exclusion despite being behaviorally live.
- [ ] New or updated determinism test demonstrates the fix actually catches a divergence in the added
      field(s) (fails before, passes after).
- [ ] Existing canonical-hash/replay determinism tests still pass unchanged.
- [ ] Parity ledger entries reflect the new status with real evidence (no fabricated citations).

## Related Tickets
- TCK-20260902-SOCIAL-CANONICAL-HASH-GAP (parallel gap, SocialComponent — separate PR)

## Related Docs
- `docs/brainstorm/2026-09-02-core-rpg-knowledge-belief-axis-proposal.md` (source investigation, §2.2)
- `docs/cognition/belief_and_detour_contract.md`
- `docs/core/state.md`

## Related Stored Artifacts
(none yet — investigation already captured in the brainstorm doc above; standard staging artifacts to
be created when this ticket is picked up for implementation)

## Related Code Areas
- `src/core/state.py` (`EntityState.to_canonical_dict()`, `StrategicComponent`, lines 768-783)
- `docs/parity_ledger/strategic_cognition.yaml`

## Assumptions / Open Questions
- Whether all 6 missing fields should be added, or whether some (e.g. `contracts`, `hypotheses`) are
  legitimately excluded as derived/non-authoritative — needs a field-by-field decision, not a blanket one.
- Whether `source_trust`'s exclusion has ever caused an observed real-world replay mismatch (worth a
  quick check of existing replay-mismatch incident history before implementing, per the axis doc's own
  open question).
- Adding fields to the canonical hash changes `state_hash` for any world compiled after this lands —
  confirm whether existing golden/reference `world_compile_report.json` fixtures need regeneration.
- Coordinate with the concurrent M3 implementation session before touching `src/core/state.py` — this is
  a shared, central file; confirm no active M3 work is mid-flight on the same lines first.

## Implementation Notes
(fill in during implementation)

## Test Summary
(fill in during implementation)

## Files Changed
(fill in during implementation)

## Completion Summary
(fill in during implementation)
