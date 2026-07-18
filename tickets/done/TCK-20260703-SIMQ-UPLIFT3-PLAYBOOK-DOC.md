---
status: historical
layer: guidelines
authority: P1
audience: agent
ticket_id: TCK-20260703-SIMQ-UPLIFT3-PLAYBOOK-DOC
phase: done
date: 2026-07-03
tags: [simulation-quality, documentation, worldbuilding, pattern]
---

# TCK-20260703-SIMQ-UPLIFT3-PLAYBOOK-DOC

## Title
Write the "compile-time pillar activation" playbook: the schema/compiler/resolver pattern reused across FACTION and INFORMATION

## Status
DONE

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

Chose `docs/guidelines/design_patterns.md` over a new dedicated doc: the file already documents 5
V2 extension-point patterns in exactly this format (When to use / Structure / engine constraints /
How-to steps / reference implementations), and this is a sixth extension point of the same kind
(a repeatable recipe for wiring new content into `AuthoritativeState` at compile time), not a
one-off investigation writeup. Added as **Pattern 6 — Compile-Time Pillar Activation Pattern**,
inserted after Pattern 5 and before the "Legacy Patterns" archive section, plus a row in the
Overview table at the top of the file for discoverability.

Content covers, in order: the failure signature (grep the single `AuthoritativeState(...)`
constructor call in `WorldCompiler.compile()` for the missing keyword arg); the fix shape as a
5-stage pipeline diagram (`WorldSpec` → `WorldCompositionSpec`/`NormalizedWorldComposition` mirror
→ resolver passthrough/override → compiler construction → composition-level content), with the
`extra="forbid"` mirroring trap called out explicitly as its own subsection (citing the FACTION
ticket's "Review Fix Log" as the caught instance) and the catalog-vs-no-catalog fork (FACTION
needed an override-merge after catalog+module merge; both INFORMATION cases were direct
passthroughs); the verification shape as 5 concrete layers ending in real recalibration through
`tools/calibrate_simq.py` (with a callout that unit-level correctness alone was insufficient in
the INFORMATION-BELIEF-TRIGGER case — a separate kernel tick-alignment bug kept
`calibration_hits` at 0 through the live loop even after compile-time plumbing was proven correct
in isolation); and the apply_generation single-fire pitfall (`factions` was added to
`ApplyPath.apply_generation()`'s carry-forward/merge logic and persists across ticks;
`information_source_profiles`/`pending_information_responses` were not, so the latter is visible
to `InformationBeliefPhase.apply()` for exactly one `refine()` call at tick 0 and then resets to
`[]` on every subsequent tick — documented as intentional/Bounded, not a bug, per
`docs/guidelines/intentional_divergences.md`). Closed with a reference-implementations table
cross-referencing `FAC-012` (`docs/parity_ledger/faction.yaml`) and `INFRA-256`/`INFRA-257`
(`docs/parity_ledger/infrastructure.yaml`) as the two worked examples, matching the ticket's
Scope item 2.

Context search per Step 0b: `mcp__knowledge-search__search_docs` for "compile-time pillar
activation pattern WorldCompiler schema resolver seeding" returned the Assembly Contract's Compile
Context section and `WORLD-ASM-003`/`WORLD-PHASE9` docs (adjacent but not a direct hit — no prior
doc already covers this exact pattern, confirming a new section was warranted rather than
duplicating existing material). `graphify query "WorldCompiler compile AuthoritativeState field
seeding pattern"` returned the 3 expected core nodes (`WorldCompiler` at
`src/worldbuilding/compiler.py:108`, `compile()` at `:115`, `AuthoritativeState` at
`src/core/state.py:1080`), confirming the file:line anchors used in the new section's prose are
current.

No code was changed — documentation only, per ticket Tier/Type. `make knowledge-index-update` run
after the doc edit (see Files Changed).

## Test Summary
- No code tests needed (documentation only).

## Files Changed
- `docs/guidelines/design_patterns.md` — added "Pattern 6 — Compile-Time Pillar Activation
  Pattern" section (failure signature, fix shape incl. `extra="forbid"` mirroring trap, 5-layer
  verification shape, apply_generation single-fire pitfall, reference-implementations table
  cross-referencing FAC-012/INFRA-256/INFRA-257) and a corresponding row in the Overview table.
- `tickets/inprogress/TCK-20260703-SIMQ-UPLIFT3-PLAYBOOK-DOC.md` — this ticket's Implementation
  Notes and Files Changed sections (this file).
- Knowledge search index re-embedded via `make knowledge-index-update` (3 files re-embedded, 1837
  from cache, 0 deleted) — no tracked index artifact diff beyond the doc content change itself.

## Completion Summary
Added "Pattern 6 — Compile-Time Pillar Activation Pattern" to `docs/guidelines/design_patterns.md`,
documenting the failure signature, fix shape (including the `extra="forbid"` mirroring trap), the
5-layer verification shape, and the `apply_generation()` single-fire persistence pitfall — all
drawn from the two worked examples (FACTION `FAC-012`, INFORMATION `INFRA-256`/`INFRA-257`).
Documentation-only change, no tests required. Knowledge index re-embedded.
