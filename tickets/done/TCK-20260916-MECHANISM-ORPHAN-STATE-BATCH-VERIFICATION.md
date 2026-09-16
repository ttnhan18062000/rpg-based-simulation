---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260916-MECHANISM-ORPHAN-STATE-BATCH-VERIFICATION
phase: done
date: 2026-09-16
tags: [architecture, schema, simulation-quality]
---

# TCK-20260916-MECHANISM-ORPHAN-STATE-BATCH-VERIFICATION

## Title
Bind and verify every `orphan`-state mechanism as one batch — the registry's least reliable state,
and the direct test of claims-as-tests phase 2's own premise

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Peer review, following `demographic_cohort_cycle`'s own correction: `orphan` is empirically the
registry's least reliable state (2 of 5 known state errors were wrong `orphan` claims — the
highest observed error rate of any state), it is the only state that is fully mechanically
decidable (zero callers, full stop, unlike `done`/`partial`'s completeness judgments), and binding
every `orphan` mechanism and running the caller-count check directly tests whether claims-as-tests
phase 2's own premise ("declaring `orphan` *is* the assertion zero callers") holds registry-wide —
the actual go/no-go signal for phase 2, not a synonym for "how accurate is the registry."

**Limitation stated up front, per peer's own explicit instruction**: this is a targeted pass at the
state most likely to be wrong. Its defect rate does not generalize to the other 58 mechanisms —
that would require a separate, random-sample exercise.

## Scope
1. All 11 `orphan`-state mechanisms, as one batch (5 already bound in earlier tickets, not
   re-investigated; 6 newly investigated here: `succession`, `genetics_aptitude`,
   `declared_cognition_schema`, `emotion`, `committed_intentions`,
   `cross_episode_social_consequences`).
2. Real caller/flag-gating check for each of the 6, directly against code — never trusting the
   atlas's own prior narrative at face value.
3. Any mechanism found wrong corrected with the same rigor as `causal_spatial_memory`/
   `demographic_cohort_cycle`: real `verified` block, propagated to every consumer artifact.
4. Confirmed-orphan mechanisms bound with `implemented_by`, symbol-level where the file mixes
   written and unwritten symbols.
5. Any finding that contradicts an existing peer-authored registry entry is flagged with full
   evidence, not silently overwritten.

## Out of Scope
- Extending `implemented_by` beyond the 11 `orphan` mechanisms to the remaining unbound
  mechanisms — a separate, larger, ongoing task.
- Resolving `succession`'s own contradiction unilaterally — explicitly left to peer.
- Any further generalization of this batch's own defect rate to the registry as a whole.

## Acceptance Criteria
1. All 11 `orphan` mechanisms have a real, checked disposition (confirmed correct, corrected, or
   explicitly flagged as an open contradiction) — none left silently unchecked.
2. Every correction is propagated to every consumer (atlas prose+badge, capabilities, wiring map),
   not just the registry field.
3. The batch's own defect rate is reported with the explicit non-generalization caveat, not left
   to be misread as an estimate of overall registry accuracy.
4. A contradiction with an existing peer-authored finding is surfaced with full, checkable
   evidence, not resolved unilaterally.
5. Full scoped suite passes, including with `graphify-out/` genuinely moved aside and restored.

## Related Tickets
- `TCK-20260916-MECHANISM-STATE-CALLER-MISMATCH-DETECTION`,
  `TCK-20260916-MECHANISM-IMPLEMENTED-BY-SYMBOL-LEVEL-BINDING` — the detector and schema this
  batch exercises.
- `TCK-20260916-EPIC-MECHANISM-REGISTRY` — this batch adds 3 more confirmed real state errors
  (`genetics_aptitude`, `emotion`, `cross_episode_social_consequences`) to the epic's own running
  count, plus one open, evidence-backed dispute (`succession`).

## Related Docs
None new.

## Related Stored Artifacts
- `stored_artifacts/TCK-20260916-MECHANISM-ORPHAN-STATE-BATCH-VERIFICATION/investigation.md` —
  full per-mechanism evidence, the genetics_aptitude/atlas-Revision-10 correction, and the full
  `succession` evidence trail.

## Related Code Areas
- `docs/brainstorm/mechanisms.yaml`, `docs/brainstorm/rpg_feature_atlas.html`,
  `docs/brainstorm/simulation_capabilities.html`, `docs/brainstorm/rpg_simulation_wiring_map.html`

## Assumptions / Open Questions
`succession`'s own state is genuinely open, not resolved by this ticket. Direct code evidence
(`LifecycleSystem._select_default_heir()`, a real fallback heir-selection algorithm added
2026-08-31, writing via the `heir_entity_id_set` patch-field naming convention) appears to
contradict an existing, dated, peer-authored `verified` block asserting the opposite. See
investigation.md for the full evidence trail. Flagged to peer directly; not acted on unilaterally.

## Implementation Notes
See `stored_artifacts/TCK-20260916-MECHANISM-ORPHAN-STATE-BATCH-VERIFICATION/investigation.md` for
the full per-mechanism evidence and the atlas Revision 10 correction (genetics_aptitude's own
atlas card claimed "no individual reproduction exists at all," itself wrong —
`src/world/reproduction_humanoid.py`, predating the registry's own seed by 12 days, implements
exactly that, gated off by default).

Symbol-level binding was used deliberately for `declared_cognition_schema`
(`core/cognition.py::RiskModel`) and `committed_intentions` (`core/cognition.py::CommitmentModel`)
rather than file-level, since `core/cognition.py` also defines `PerceptionModel` (written, a
separately-registered mechanism) — a file-level binding would have repeated
`demographic_cohort_cycle`'s own aggregation mistake in a new file.

## Test Summary
See `stored_artifacts/TCK-20260916-MECHANISM-ORPHAN-STATE-BATCH-VERIFICATION/test_plan.md`. 181
tests passing in the full scoped suite, both with `graphify-out/` present and with it genuinely
moved aside and restored.

## Files Changed
- `docs/brainstorm/mechanisms.yaml` — `genetics_aptitude` (orphan→gated), `emotion`
  (orphan→done), `cross_episode_social_consequences` (orphan→done), each with a `verified` block;
  `declared_cognition_schema`, `committed_intentions` bound with symbol-level `implemented_by`
  (state unchanged, confirmed correct)
- `docs/brainstorm/rpg_feature_atlas.html` — 3 cards hand-corrected (badge cls, badge text, and
  prose — not just cls-regenerated)
- `docs/brainstorm/simulation_capabilities.html` — `mind#4` tier regenerated
- `docs/brainstorm/rpg_simulation_wiring_map.html` — `EMO` node corrected
- `docs/brainstorm/mechanism_verification_view.md`, `docs/brainstorm/mechanism_priority_view.md`,
  `docs/brainstorm/mechanism_registry_view.md`, `docs/brainstorm/mechanism_registry.html` —
  regenerated
- `tests/unit/tools/test_mechanism_registry_completeness_check.py`,
  `test_mechanism_state_caller_check.py` — pinned counts/findings updated
- `docs/REGISTRY.yaml` — regenerated at Finalize

## Completion Summary
Closed, with one item explicitly left open rather than force-closed. Of the 6 newly-investigated
`orphan` mechanisms, 3 were wrong (`genetics_aptitude`→gated, `emotion`→done,
`cross_episode_social_consequences`→done — all corrected with real evidence and propagated to
every consumer), 2 were confirmed correct and bound (`declared_cognition_schema`,
`committed_intentions`), and 1 (`succession`) surfaced a direct, evidence-backed contradiction with
an existing peer-authored `verified` block — not resolved here, reported to peer with the full
trail instead.

**Headline, stated with the explicit non-generalization caveat this ticket exists to enforce**: 3
of 6 newly-checked orphans were wrong (50%), and a 4th is under real dispute — combined with the
2 errors already known, that is up to 5 of 11 `orphan` mechanisms found or suspected wrong when
actually checked. This is a real, substantial signal specifically about the `orphan` state, on a
targeted sample chosen because it was suspected weakest — it does not estimate the other 58
mechanisms' own accuracy, which would need a separate, random sample. As the direct test of
claims-as-tests phase 2's premise, this result argues the premise itself (caller-count as a real
proxy for the `orphan` claim) holds up well where it was actually checked — every miss found here
was a real, findable code fact, not a case where caller-count detection itself gave an ambiguous or
unreliable answer.

A second, unplanned correction surfaced along the way: `genetics_aptitude`'s own atlas card
(Revision 10) claimed no individual parent-child reproduction exists in the simulation at all —
also wrong, corrected in the same pass.
