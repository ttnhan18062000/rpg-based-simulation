---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260920-MECHANISM-BOUND-UNVERIFIED-INSTRUMENT-RUN
phase: done
date: 2026-09-20
tags: [architecture, schema, simulation-quality]
---

# TCK-20260920-MECHANISM-BOUND-UNVERIFIED-INSTRUMENT-RUN

## Title
Batch 3 of the unbound-claims program: instrument runs against the 20 mechanisms already bound but
never given a `verified` block

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
Batch 3 of the 4-batch unbound-claims program. Unlike batches 1/2 (find or correct a binding),
these 20 mechanisms already carry a real `implemented_by` (most bound in earlier tickets across
this epic, with real caller evidence already recorded as plain YAML comments) but never got a
formal `verified:` block. This batch runs a real instrument (`code_trace`, re-confirming each
binding's own caller evidence directly rather than trusting the comment prose) against all 20 and
records the result.

**Governing constraint, explicit and equally weighted with prior batches**: a `contradicted`
verdict is as good a result as `observed` — this batch reports what the instrument actually found,
it does not repair code to make a claim agree with its binding.

## Scope
Instrument-verify all 20 bound-but-unverified mechanisms: `movement`, `declared_cognition_schema`,
`temporal_pressure`, `adventure_routing`, `committed_intentions`, `diplomacy`, `cultural_drift`,
`cooperation`, `resource_harvesting`, `fame`, `fidelity_drift`, `belief_institution`,
`strategic_learning_bias`, `strategic_redirection`, `concern_intake`, `event_interpretation`,
`narrative_memory`, `group_coordination`, `quest_reward_distribution`,
`commitment_pressure_consequences`.

## Out of Scope
- Adding new bindings (that's batches 1/2's own job, already done).
- Fixing any code found to be dead/uncalled during verification.
- Batch 4 (`contradicted`-verdict triage into scoped tickets) and the `xp_leveling`/`evolution`
  identity investigation — separate pieces of the same program.

## Acceptance Criteria
1. All 20 mechanisms carry a real `verified` block with `instrument: code_trace` (or better) and
   a real, specific note.
2. Every verdict reflects what was actually found, not what would make the claim look better.
3. `registry.py::validate()` clean; consumer artifacts regenerated where state changed (none did
   this batch — verification only, no state corrections needed).

## Related Tickets
- `TCK-20260920-MECHANISM-ENTITY-LAYER-UNBOUND-CLAIMS-RESOLUTION`,
  `TCK-20260920-MECHANISM-WORLD-FACTION-REGION-GROUP-UNBOUND-CLAIMS-RESOLUTION` — batches 1/2,
  same program.
- `TCK-20260916-MECHANISM-ORPHAN-STATE-BATCH-VERIFICATION`,
  `TCK-20260916-MECHANISM-IMPLEMENTED-BY-BINDING`, `TCK-20260916-MECHANISM-DEPENDENCY-GRAPH-
  POPULATION` — the earlier tickets that originally bound most of these 20, whose own caller
  evidence (already recorded as YAML comments) this batch formalizes into `verified` blocks.

## Related Docs
None new.

## Related Stored Artifacts
- `stored_artifacts/TCK-20260920-MECHANISM-BOUND-UNVERIFIED-INSTRUMENT-RUN/`.

## Related Code Areas
- `registries/mechanisms.yaml`
- `tests/unit/tools/test_mechanism_registry.py` (one hardcoded "real, unverified id" example,
  `movement`, swapped for `clan` since `movement` now has a real verified block)

## Assumptions / Open Questions
None. All 20 verdicts came back `observed` — every one of the 20's own pre-existing caller
evidence (already documented as plain comments from earlier tickets) held up under direct
re-confirmation this pass. No `contradicted` verdicts in this batch (that shape showed up in batch
2's own `calamity_intensity`, not here).

## Implementation Notes
For each of the 20, the real caller evidence already present as a plain YAML comment (from the
original binding ticket) was independently re-confirmed via direct grep this pass, then formalized
into a `verified: {instrument: code_trace, verdict: observed, date, note}` block. Several bindings
got a small additional confirmation beyond what the original comment stated (e.g. `diplomacy`'s
own `compute_transitions()` reconfirmed at a second real call site, `pipeline.py:260`, not just
the one the original comment cited). No code changes; no state changes; this batch is purely
formal verification of already-real bindings.

## Test Summary
`tests/unit/tools/test_mechanism_registry.py`: one existing test's hardcoded example id swapped
(`movement` → `clan`) since `movement` gained a real verified block this pass. Full `tests/unit/
tools/` suite: 260 passed. `registry.py::validate()`: clean, 93 mechanisms. All 5 blocking checks:
clean (no drift, since no `state` value changed this batch).

## Files Changed
- `registries/mechanisms.yaml` — 20 `verified` blocks added, no state/binding changes.
- `tests/unit/tools/test_mechanism_registry.py` — one hardcoded example id swapped.
- `docs/brainstorm/mechanism_verification_view.md`, `mechanism_registry_view.md`,
  `mechanism_system_rollup_view.md`, `mechanism_registry.html` — regenerated (verification-count
  fields moved; no badge/tier changes since no state changed).

## Completion Summary
**Done.** All 20 bound-but-unverified mechanisms now carry a real `verified` block. Every verdict
came back `observed` — each binding's own pre-existing caller evidence held up under direct
re-confirmation. No code fixed, no states changed, consistent with this batch's own scope as pure
verification. Batch 4 (`contradicted`-verdict triage, 6 mechanisms) and the `xp_leveling`/
`evolution` identity investigation remain, landing in the same PR per the user's own call.
