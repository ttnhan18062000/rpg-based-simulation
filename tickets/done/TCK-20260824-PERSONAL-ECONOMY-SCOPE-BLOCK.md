---
status: historical
layer: economy
authority: P1
audience: agent
ticket_id: TCK-20260824-PERSONAL-ECONOMY-SCOPE-BLOCK
phase: done
date: 2026-08-24
tags: [economy, cognition]
---

# TCK-20260824-PERSONAL-ECONOMY-SCOPE-BLOCK

## Title
Scope Personal Economy & Material Ambition, Blocked on MotivationModel.values Foundation

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
The author wants Personal Economy & Material Ambition attached to MotivationModel.values (ValuePreferenceProfile), which is independently confirmed dead-on-arrival -- never populated above 0.5 defaults. This ticket scopes the target design but explicitly does not start implementation until a separate foundation ticket for MotivationModel.values exists.

## Scope
- Create the ticket in a scoping-only/BLOCKED state -- document target design for a Personal Economy & Material Ambition motivation axis attached to MotivationModel.values (ValuePreferenceProfile), with no implementation.
- State the verified dead-on-arrival fact with file:line evidence: ValuePreferenceProfile's 7 fields all default to 0.5, zero production call sites construct MotivationModel/ValuePreferenceProfile with non-default values, so MotivationBiasService.compute_bias_multiplier's (values.X-0.5) deltas are mathematically always 0.0 in every real run.
- Name the not-yet-existing MotivationModel.values foundation ticket as a hard blocking dependency in Related Tickets/Assumptions (no such ticket exists yet anywhere in docs/tickets/stored_artifacts).
- State eventual (unblocked) implementation acceptance criteria as conditional/deferred.
- Set ticket body Status to BLOCKED, not OPEN.

### Dead-on-Arrival Evidence (transcribed from investigation.md, verified against source)
- `ValuePreferenceProfile` dataclass, `src/core/cognition.py:382-402` -- all 7 fields
  (`survival`, `reward`, `knowledge`, `loyalty`, `pride`, `curiosity`, `caution`) default to `0.5`.
- `MotivationModel.values` field, `src/core/cognition.py:440-444` (line 443:
  `values: ValuePreferenceProfile = field(default_factory=ValuePreferenceProfile)`).
- `MotivationBiasService.compute_bias_multiplier`, `src/domains/motivation/service.py:14-72`,
  Value-Preference-Profile delta block at lines 49-63 (4 of 7 fields consumed --
  `survival` line ~57, `pride` line ~59, `curiosity` line ~61, `reward` line ~63 -- each via
  `(values.X - 0.5) * 0.5`); the other 3 fields (`knowledge`, `loyalty`, `caution`) are never read
  anywhere in the method.
- `src/core/builder.py:111` (`self._cognition = CognitionModel()`) is the single zero-argument
  production `CognitionModel` construction path in `src/` -- it default-factories the whole chain
  (`MotivationModel` -> `ValuePreferenceProfile`) to all-`0.5`.
- A full repo grep of `MotivationModel(` and `ValuePreferenceProfile(` across `src/` returns zero
  non-default production construction sites; every non-default construction found anywhere in the
  repository is test-only (`tests/unit/domains/motivation/test_phase14_bias_service.py`,
  `tests/integration/scenarios/test_phase18_cognition_hierarchy_e2e.py`,
  `tests/integration/scenarios/test_phase14_motivation_doctrine_scenarios.py`).
- Mathematical consequence: `(values.X - 0.5)` evaluates to `0.0` for all 4 consumed fields, for
  every entity, on every call, in every production run -- the Value Preference Profile branch of
  `compute_bias_multiplier` is a permanent no-op contribution in production today.

## Out of Scope
- Any src/ code changes while blocked.
- Designing the content-schema/emergent-derivation mechanism for populating MotivationModel.values -- that belongs to the separate, not-yet-scoped foundation ticket.

## Acceptance Criteria
- [x] Ticket is created and moved to a scoping-only/BLOCKED state -- documents target design, contains no implementation.
- [x] Ticket names the not-yet-existing MotivationModel.values foundation ticket as a hard blocking dependency in Related Tickets/Assumptions.
- [x] Ticket body states the verified dead-on-arrival fact with file:line evidence so future readers don't re-derive it.
- [x] Eventual (unblocked) implementation ACs are stated as conditional/deferred.
- [x] No src/ changes are made under this ticket while blocked.

### Conditional / Deferred Implementation Acceptance Criteria (only apply once unblocked)
- [ ] (Deferred) A `material_ambition` field is added to `ValuePreferenceProfile` (the Personal Economy & Material Ambition motivation axis) with a defined weight/derivation contract, once the MotivationModel.values foundation ticket has landed and values are populated above static defaults in production call sites.
- [ ] (Deferred) MotivationBiasService.compute_bias_multiplier produces non-zero, entity-differentiated deltas for `material_ambition` in real runs, verified by a passing test with concrete non-default entity data.
- [ ] (Deferred) Behavior change is reflected in the relevant Mechanics Bible chapter (docs/mechanics/04_strategic_cognition.md, which currently has zero Motivation/values coverage to update -- this deferred AC adds a new section, not an update to an existing one) and the corresponding parity ledger entry (docs/parity_ledger/strategic_cognition.yaml, which currently has no entry for ValuePreferenceProfile defaults -- this deferred AC adds a new entry).

## Related Tickets
None. No foundation ticket for MotivationModel.values exists yet anywhere in docs/tickets/stored_artifacts -- confirmed via a grep across `tickets/`, `docs/`, and `stored_artifacts/` for `MotivationModel.values`/`ValuePreferenceProfile` that matched 15 files, none of which is a population effort (closest are `TCK-20260619-E62C-MOTIVATION-OVERLAY` and `TCK-20260619-E62-CULTURE-DRIFT`, which explicitly keep the cultural overlay transient and non-durable, and `docs/plans/rpg_design_roadmap/rpg_m1_quick_wins_epic.md:115-119,132-133,148` Idea 24, which originates this exact blocker). A separate ticket must be filed and completed first to populate MotivationModel.values (ValuePreferenceProfile) above static 0.5 defaults in production call sites; this ticket is hard-blocked on that not-yet-existing ticket.

## Related Docs
- docs/architecture/cognition_domain_ownership.md
- docs/mechanics/04_strategic_cognition.md
- docs/plans/rpg_design_roadmap/rpg_m1_quick_wins_epic.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/core/cognition.py
- src/domains/motivation/service.py

## Assumptions / Open Questions
- No foundation ticket for MotivationModel.values exists yet anywhere in docs/tickets/stored_artifacts -- cannot cite a concrete ticket ID; this must be stated explicitly as "no foundation ticket filed yet" rather than guessed at.
- This concern independently restates an identical blocker already documented in the M1 epic doc's own Idea 24, supporting scope-only/blocked treatment rather than full implementation now.
- `layer: economy` was chosen over `cognition`-adjacent layers (`strategy`, `core`) because the ticket's subject matter (Personal Economy & Material Ambition) is an economy-domain motivation axis; the blocking dependency lives in cognition/motivation code, reflected via the `cognition` tag instead.

## Implementation Notes
Target Design Sketch pointer (condensed; full sketch lives in
`staging_artifacts/TCK-20260824-PERSONAL-ECONOMY-SCOPE-BLOCK/investigation.md`, section "Target
Design Sketch for Personal Economy & Material Ambition axis" -- this is a summary/pointer only,
not a duplicate, so design authority stays in one place):
- A genuinely new 8th field `material_ambition: float = 0.5` on `ValuePreferenceProfile`, distinct
  from `reward` (generic loot/gold desirability) -- `material_ambition` is about durable
  possession/status (property, stockpiled goods, market position), not momentary route-tag gain.
- Derivation/weight contract is deferred to the not-yet-existing foundation ticket: whatever
  mechanism that ticket uses to populate `ValuePreferenceProfile` fields above 0.5 in production
  (content-schema-driven, emergent-derivation, or otherwise), `material_ambition` should be wired
  through that same pipeline as a normal 8th consumer, not a bespoke special case.
- `MotivationBiasService.compute_bias_multiplier` would consume it via one new `elif` branch
  following the exact existing pattern at `service.py:49-63`:
  `elif tag in (...): multiplier += (values.material_ambition - 0.5) * 0.5` -- illustrative tag
  vocabulary and the `0.5` weight coefficient are not final; finalized in the eventual
  implementation ticket's own plan.md.
- Explicit non-goal: this sketch does not design the content-schema/emergent-derivation population
  mechanism for `MotivationModel.values` generally -- that is the foundation ticket's job.

No `src/` or `tests/` files were touched by this ticket; it is scope-only per its own Acceptance
Criteria and Out of Scope. This Implement phase's work consisted entirely of: (1) transcribing the
dead-on-arrival file:line evidence from `investigation.md` into the ticket's `## Scope` section,
(2) tightening `## Related Tickets` to cite the confirmed 15-file search scope, (3) adding this
condensed Target Design Sketch pointer, (4) aligning the Deferred Acceptance Criteria to the
concrete `material_ambition` field name and confirming their doc targets, (5) confirming `##
Status` stays `BLOCKED` and frontmatter remains valid, and (6) closing out these final ticket
sections. No design decisions were made beyond what `investigation.md` had already verified against
source.

## Test Summary
No automated tests apply to this ticket's own scope -- every Acceptance Criterion here is
documentation/scoping content, not runtime behavior, per
`staging_artifacts/TCK-20260824-PERSONAL-ECONOMY-SCOPE-BLOCK/test_plan.md`'s "New Tests Required:
None". The optional sanity-check command listed in `test_plan.md`
(`pytest tests/unit/domains/motivation/test_phase14_bias_service.py
tests/unit/motivation/test_motivation_bias_culture.py
tests/unit/domains/motivation/test_phase14_motivation_models.py -v`) was not run, since no
`src/`/`tests/` files changed and it is explicitly not required for this ticket's own Definition of
Done.

## Files Changed
- tickets/inprogress/TCK-20260824-PERSONAL-ECONOMY-SCOPE-BLOCK.md

## Completion Summary
This ticket was scoped and closed out as scope-only per its own design: it documents the
target design for a Personal Economy & Material Ambition motivation axis attached to
`MotivationModel.values`, records the independently-verified dead-on-arrival fact (all 7
`ValuePreferenceProfile` fields default to 0.5, zero non-default production construction sites in
`src/`, so `MotivationBiasService.compute_bias_multiplier`'s Value Preference Profile deltas are
always 0.0 in production) with file:line citations, and names the not-yet-existing
`MotivationModel.values` foundation ticket as a hard blocking dependency. No implementation was
performed and no `src/` or `tests/` file was created, modified, or deleted.

**Status = DONE clarification:** `## Status: DONE` above means this scoping/documentation ticket's
own work is complete and the ticket itself is closed -- it does **not** mean the underlying
Personal Economy & Material Ambition feature was implemented. The feature remains conditionally
blocked: it cannot move to implementation until a separate, not-yet-existing foundation ticket
lands that populates `MotivationModel.values` (`ValuePreferenceProfile`) above its static 0.5
defaults in production call sites (see `## Related Tickets` and the Deferred Acceptance Criteria
above). Filing and completing that foundation ticket is future work, out of scope here.

