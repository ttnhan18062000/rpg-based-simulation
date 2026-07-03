---
status: active
layer: guidelines
authority: P1
audience: agent
ticket_id: TCK-20260703-SIMQ-UPLIFT3-PLAYBOOK-DOC
phase: open
date: 2026-07-03
tags: [simulation_quality, documentation, worldbuilding, pattern]
---

# TCK-20260703-SIMQ-UPLIFT3-PLAYBOOK-DOC

## Title
Write the "compile-time pillar activation" playbook: the schema/compiler/resolver pattern reused across FACTION and INFORMATION

## Status
OPEN

## Tier
hotfix

## Type
documentation

## Priority
P2

## Request Summary
`TCK-20260702-SIMQ-UPLIFT2-FACTION` and `TCK-20260702-SIMQ-UPLIFT2-INFORMATION` /
`TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER` independently discovered and applied the exact same
fix pattern for two different SimQ pillars stuck at C: `WorldCompiler.compile()` was silently
never constructing a durable-state field at all (`AuthoritativeState.factions` and
`AuthoritativeState.information_source_profiles`/`pending_information_responses` respectively),
so the pillar's scoring condition could never be satisfied no matter what world content existed.
The fix, in both cases: add a typed spec field to `WorldSpec`, mirror it onto
`WorldCompositionSpec`/`NormalizedWorldComposition` (composition-level, not module-level, to avoid
catalog-merge collisions), wire `WorldCompiler.compile()` to actually construct and pass the field,
add resolver passthrough, then seed real content in one target world and recalibrate.

This pattern is valuable and non-obvious enough (it took real investigation both times) that it
should be written down once, so the next SimQ pillar stuck at C — or the next engineer picking up
`TCK-20260703-SIMQ-UPLIFT3-DUAL-GATE-AUDIT`'s findings — starts from the pattern instead of
re-deriving it from scratch.

## Scope
1. Write `docs/guidelines/design_patterns.md` (or a new dedicated doc under `docs/plans/` if that
   file's scope doesn't fit — check its current structure first) a new section: "Compile-Time
   Pillar Activation Pattern" covering:
   - The failure signature: a durable-state field permanently empty/default across every world,
     confirmed by grepping the single `AuthoritativeState(...)` constructor call in
     `WorldCompiler.compile()` for the field's keyword argument.
   - The fix shape: typed spec field on `WorldSpec` → mirrored on `WorldCompositionSpec` +
     `NormalizedWorldComposition` (with the `extra="forbid"` mirroring trap called out explicitly,
     since the FACTION ticket's architecture review caught exactly this omission) → resolver
     passthrough/override application → compiler construction → composition-level (not
     module-level) world content, to avoid catalog-merge collisions like the one FACTION's
     investigation found for `data/content/social/factions.yaml`.
   - The verification shape: unit tests at each layer (schema round-trip, compiler seeding,
     resolver passthrough) + a direct-pipeline integration test + real recalibration confirming
     the calibration_hits change through the live loop, not just a compile-time assertion.
   - The known pitfall: compile-time-seeded fields are NOT carried forward by
     `ApplyPath.apply_generation()` across ticks unless explicitly added to its merge logic (as
     `factions` was, but `information_source_profiles`/`pending_information_responses` were not) —
     single-fire vs. persistent-across-ticks is a design choice that must be made explicitly, not
     assumed.
2. Cross-reference `docs/parity_ledger/faction.yaml::FAC-012` and
   `docs/parity_ledger/infrastructure.yaml::INFRA-256/257` as the two worked examples.

## Out of Scope
- Applying this pattern to any new pillar (that's `TCK-20260703-SIMQ-UPLIFT3-DUAL-GATE-AUDIT`'s
  job, if it finds a matching bug)
- Any code changes

## Acceptance Criteria
- [ ] New "Compile-Time Pillar Activation Pattern" section exists in an appropriate `docs/`
      location, covering the failure signature, fix shape, verification shape, and the
      apply_generation single-fire pitfall
- [ ] Cross-references both worked examples (FACTION, INFORMATION) with parity ledger IDs
- [ ] `make knowledge-index-update` run after the doc change

## Related Tickets
- TCK-20260702-SIMQ-UPLIFT2-FACTION (done) — first worked example
- TCK-20260702-SIMQ-UPLIFT2-INFORMATION (done) + TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER (done) — second worked example
- TCK-20260703-SIMQ-UPLIFT3-DUAL-GATE-AUDIT — likely consumer of this playbook

## Related Docs
- `docs/guidelines/design_patterns.md` — likely home for this section; read its current structure
  first to confirm fit
- `docs/parity_ledger/faction.yaml`, `docs/parity_ledger/infrastructure.yaml` — worked-example IDs

## Related Stored Artifacts
- `stored_artifacts/TCK-20260702-SIMQ-UPLIFT2-FACTION/plan.md` — the original worked-example plan
- `stored_artifacts/TCK-20260702-SIMQ-UPLIFT2-INFORMATION/plan.md`,
  `stored_artifacts/TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER/plan.md` — the second worked-example plans

## Related Code Areas
- `src/worldbuilding/schema.py`, `src/worldbuilding/compiler.py`, `src/worldassembly/schema.py`,
  `src/worldassembly/resolver.py`, `src/engine/apply.py::ApplyPath.apply_generation()`

## Assumptions / Open Questions
None — this is a documentation-only ticket summarizing already-completed, already-reviewed work.

## Implementation Notes
(to be filled during implementation)

## Test Summary
- No code tests needed (documentation only).

## Files Changed
(to be filled during implementation)

## Completion Summary
(to be filled on done)
