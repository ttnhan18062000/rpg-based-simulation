---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260917-MECHANISM-IMPLEMENTED-BY-COVERAGE-EXTENSION
phase: open
date: 2026-09-17
tags: [architecture, schema, simulation-quality]
---

# TCK-20260917-MECHANISM-IMPLEMENTED-BY-COVERAGE-EXTENSION

## Title
Extend `implemented_by` coverage beyond 26 of 89 mechanisms — the unticketed precondition for both
queued detectors

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Peer review, closing out the mechanism-registry PR: extending `implemented_by` coverage beyond its
current 26 of 89 mechanisms isn't ticketed anywhere. It exists only as a stated intention across
several conversations, even though it is the hard precondition for both queued detectors
(`TCK-20260916-MECHANISM-STATUS-LANGUAGE-DETECTION` reads registry state directly, but
`TCK-20260916-MECHANISM-CHANGED-CODE-ENTRY-DRIFT-DETECTION` reads `implemented_by` specifically —
and the state-caller-mismatch detector's own future re-runs need broader, less-biased coverage to
produce a meaningful assessment). This is the same orphan-knowledge failure shape this whole arc
exists to catch, just one level up: an intention scoped in conversation, never landed as a real,
findable ticket.

**Correction to the figure itself, found while filing this ticket**: prior reports in this epic
(including this session's own PR description) said "24 of 89." Direct recount says **26 of 89** —
`len(report.bound)` in `mechanism_registry_completeness_check.py`'s own output counts *bound
`src/domains/`/`src/systems/` targets*, not *mechanisms with a binding*; several mechanisms
(`fame`, `fidelity_drift`, `belief_institution`, `commitment_pressure_consequences`) bind multiple
files each, and two (`declared_cognition_schema`, `committed_intentions`) bind
`core/cognition.py`, outside that checker's own `src/domains/`/`src/systems/` scope entirely — so
target-count and mechanism-count diverge. Use `mechanisms_with_binding` (or a direct count of
mechanisms with a non-empty `implemented_by`) for "how many mechanisms are covered," not the
completeness checker's own target count, which answers a different, narrower question.

## Scope
1. Bind a real, meaningful batch of the remaining 63 unbound mechanisms with `implemented_by`
   (symbol-level where a file mixes unrelated symbols, file-level where a file's symbols are
   genuinely one concept — same discipline as every binding done so far in this epic).
2. Prioritize mechanisms that were NOT recently hand-verified by this session, since the existing
   26 are disproportionately the mechanisms already checked while fixing known defects — exactly
   the sample-bias phase 1 and the orphan batch both flagged. A useful next batch should include
   mechanisms nobody has looked at closely yet.
3. Apply the same verification rigor as every prior binding in this epic: real caller checks, not
   assumed from the atlas's own prior narrative — several prior "confirmed orphan" and "confirmed
   done" claims in this epic turned out wrong on direct re-check.
4. Any state correction found along the way gets the same treatment as `camp`/
   `demographic_cohort_cycle`/`succession`: a real `verified` block, propagated to every consumer
   artifact, not silently absorbed.

### Coverage acceptance targets, per claim-type — added 2026-09-17, previously undeclared anywhere

Discussed but never landed in an artifact until now. **"Enough coverage" is declared per
claim-type, not as one global percentage** — a global target like "80% bound" invites binding the
easy mechanisms just to move the number, the same failure shape the claims-as-tests detectors'
exclusion lists exist to prevent, generalized one level up.

- **`orphan` → 100%, no exceptions.** `orphan` means zero callers — fully, mechanically decidable
  by a real caller check, nothing left to judgement. The measured error rate on this exact claim
  was **4 of 6** when the orphan-state batch actually checked it
  (`TCK-20260916-MECHANISM-ORPHAN-STATE-BATCH-VERIFICATION`) — a claim this cheap to verify and
  this often wrong has no honest reason to stay unchecked.
- **`gated` → 100%.** Same reasoning as `orphan`: a feature flag either exists on the entry path or
  it doesn't. Mechanically decidable, so fully bind it.
- **`done` / `partial` → no coverage target.** These are judgements about completeness, not
  mechanically decidable facts — `implemented_by` binding alone can't settle whether a `done`
  mechanism actually works; the `verified` axis (below) is what settles that, not binding coverage.
- **`verified` → no target at all.** 2 of 89 runtime-verified is the honest current state. Setting
  a target here would produce direct pressure to raise that number, which is exactly the shape of
  the fabricated/stale verdicts this whole axis exists to catch (`motivation_doctrine`'s own "still
  confirmed live" claim eight days after its code was deleted is the standing example).

This ticket's own scope (item 1, "a real, meaningful batch") is now sharpened by this: prioritize
binding every remaining `orphan` and `gated` mechanism toward their 100% targets first, since those
are the two claim-types where non-100% coverage is itself a stated gap rather than an accepted one.
`done`/`partial`/`verified` binding remains valuable (item 2's own de-biasing goal still applies)
but isn't held to a numeric target the way `orphan`/`gated` now are.

**Current state against these targets, checked 2026-09-17**: `orphan` is already at its 100%
target — all 7 `orphan`-state mechanisms are bound. `gated` is at 3 of 8 (`self_model`,
`information_trust_deception`, `knowledge_model`, `quest_generation_sourcing`,
`opportunity_rumor_seeds` remain unbound) — these 5 are this ticket's own concrete, prioritized
starting list, not an abstract "some gated mechanisms" instruction.

## Out of Scope
- Binding all remaining 63 mechanisms in one pass — this is deliberately incremental, ongoing
  work, not a single bounded task with a fixed completion count.
- Building either queued detector — both are explicitly sequenced after this ticket in
  `tickets/todos/mechanism-verification/SEQUENCE.md`.

## Acceptance Criteria
1. `implemented_by` coverage measurably increases beyond 26 of 89, with each new binding backed by
   a real, direct caller/symbol check.
2. The batch's own selection is biased toward NOT-recently-verified mechanisms, recorded
   explicitly, so the next false-positive-rate assessment isn't run against the same cleanest
   slice twice.
3. Any state correction found is propagated to every consumer artifact (atlas, capabilities,
   wiring map), not just the registry field.
4. Every remaining `orphan` and `gated` mechanism is either bound (moving that claim-type toward
   its 100% target) or explicitly recorded as a known gap against that target, with a reason — not
   silently left unbound with no note that a target exists for it.

## Related Tickets
- `TCK-20260917-EPIC-MECHANISM-VERIFICATION` — parent epic; this ticket is second in
  `SEQUENCE.md`'s own order, after `TCK-20260917-MECHANISM-IDENTITY-RULES-AND-CHANGE-TAXONOMY`
  (resequenced 2026-09-17 — a split from that ticket would otherwise divide a binding already done
  here, see that ticket's own reasoning).
- `TCK-20260916-MECHANISM-STATUS-LANGUAGE-DETECTION`,
  `TCK-20260916-MECHANISM-CHANGED-CODE-ENTRY-DRIFT-DETECTION` — both sequenced after this ticket.

## Related Docs
- `docs/plans/mechanism_claims_as_tests_initiative.md` §7 Phasing — phase 1's own explicit
  statement that its result should decide whether phases 2/3 are worth building, which requires
  coverage broader than the current biased sample.

## Related Stored Artifacts
None yet.

## Related Code Areas
- `registries/mechanisms.yaml`
- `tools/mechanism_registry/mechanism_registry_completeness_check.py`,
  `mechanism_state_caller_check.py` — both read `implemented_by`; this ticket increases what they
  can check.

## Assumptions / Open Questions
No fixed target count set deliberately — "a real, meaningful batch" is intentionally left to
whoever picks this up, informed by how much the false-positive-rate assessment needs to move to be
trustworthy.

## Implementation Notes
**Batch 1 (2026-09-19) — combat-first, per explicit user direction relayed this session.** Bound
5 of the 7 `systems: [combat]` mechanisms with real, direct code-read verification (all had
`implemented_by: None` going in):
- `combat_resolution` -> `src/engine/combat.py::CombatResolutionSystem` (single class, single file).
- `tactical_decision` -> `src/engine/tactical.py::TacticalDecisionSystem` (single class, single file).
- `movement` -> `src/engine/movement.py::MovementSystem` (single class, single file).
- `combat_engagement` -> `src/domains/combat_engagement/service.py::CombatEngagementDecisionService`
  (the posture-decision class the entry's own existing `verified` note already cites — a second
  candidate, `CombatEngagementPhase` in `phase.py`, is the per-tick integration wrapper that calls
  this service, not the decision logic itself, so it was not bound).
- `status_effects` -> `src/core/updates.py::StatusEffectUpdate` + `src/engine/patches.py::StatusEffectPatch`,
  **with a real state correction, `partial` -> `orphan`**, found while verifying the binding: a
  repo-wide check for `status_effect_update`/`StatusEffectUpdate(`/`effects_add=` outside those two
  files finds zero production callers anywhere in `src/` — the state model, schema, and apply-path
  all exist and are internally tested, but nothing ever adds a status effect during real play. Full
  evidence and consequence (the `ATTACKER_STATUS_BLOCKED` legality gate can never fire) recorded in
  the mechanism's own `verified` block in `registries/mechanisms.yaml`. Propagated to both real
  consumer artifacts per this ticket's Scope item 3 and AC #3:
  `tools/mechanism_registry/mechanism_atlas_regenerate.py` and
  `mechanism_capabilities_regenerate.py` both ran clean and each fixed exactly the one expected
  badge/tier (atlas `entity-modification#1` cls partial->orphan's mapped value; capabilities
  `modification#1` tier live->built) — no other mapped card moved, confirmed by
  `test_mechanism_artifact_convergence.py` passing afterward. The wiring map's own existing
  `status_effects` row (already badge `bug`/"Fragmented", from an earlier, narrower finding about
  `Frozen` being stored as an untyped dict key) needed no change —
  `test_real_wiring_map_has_no_drift_against_the_real_registry` still passes, so `orphan` already
  maps to the same wiring-map classdef `partial` did.

**Not bound, restraint applied (same discipline as the earlier 3-of-7 batch this session)**.
**Correction, caught by peer review**: symbol-level binding (`path::Symbol`, validated against a
real top-level class or function) already exists and is used throughout this registry (e.g. every
`::ClassName`/`::function_name` entry bound in this same batch). What's actually missing, and what
both cases below need, is **method-level** binding (`path::Class::method`) — one level finer than
what's supported today. Stating the real gap rather than "no symbol-level support," which
overstates it and points at work already done:
- `action_pacing_readiness` — real implementing code found (`LegalityServiceV2.verify_readiness()`,
  `src/engine/legality.py`), but `legality.py` is a large multi-concern file (attack legality,
  movement legality, readiness, regional suppression, engaged-hostiles resolution all live in the
  same `LegalityServiceV2` class), so a class-level binding would misattribute several unrelated
  mechanisms' logic to this one entry — only a method-level binding would be precise, and that
  granularity doesn't exist yet. Left unbound rather than force an imprecise binding.
- `skill_unlocks` — real implementing code found (`LevelingService.get_unlocked_skills()` /
  `_execute_level_up()`, `src/progression/leveling.py`), but the same class also implements
  `xp_leveling` (`process_progression()`/`get_xp_required()`) via different methods on the *same*
  class — no class-level boundary separates the two mechanisms the way `core/cognition.py`'s
  `RiskModel`/`CommitmentModel` split does for `declared_cognition_schema`/`committed_intentions`.
  Same method-level gap as above; left unbound.

Whether method-level binding is worth adding for just these two mechanisms is an open question, not
resolved here — the brittleness argument that already deferred symbol-level once (breaks on every
rename) applies with more force one level finer. Leaning toward not building it for two mechanisms
alone, but not deciding that unilaterally in this ticket.

Batch selection rationale (AC #2): this batch prioritized `systems: [combat]` per explicit user
direction for this pass, not the ticket's own default `orphan`/`gated`-first ordering (Scope's own
"Coverage acceptance targets" section) — `orphan`/`gated` remain the ticket's own next-priority
targets for a future batch (5 of 8 `gated` mechanisms — `self_model`,
`information_trust_deception`, `knowledge_model`, `quest_generation_sourcing`,
`opportunity_rumor_seeds` — are still unbound as of this batch, untouched here).

## Test Summary
`tests/unit/tools/` (206 tests) run against the real registry after the batch:
`test_mechanism_registry_completeness_check.py`, `test_mechanism_atlas_regenerate.py`,
`test_mechanism_capabilities_regenerate.py`, `test_mechanism_artifact_convergence.py`,
`test_mechanism_wiring_map_classdef.py` all pass. One pinned-baseline test
(`test_real_registry_enumeration_and_binding_counts_pinned`) updated with real recomputed numbers
(`bound` 24->25, `unbound` 37->36, `total_targets` unchanged at 64 — 4 of this batch's 5 bindings
resolve to `src/engine/`/`src/core/` targets, outside that checker's own `src/domains/`/
`src/systems/` scope, same divergence this ticket's own Request Summary already documents for
`core/cognition.py`). `registry.py`'s own `validate()` passes clean (93 mechanisms) after every
edit in this batch.

## Files Changed
- `registries/mechanisms.yaml` — 5 new `implemented_by` bindings, 1 `state` correction with a new
  `verified` block (`status_effects`).
- `docs/brainstorm/rpg_feature_atlas.html`, `docs/brainstorm/simulation_capabilities.html` —
  regenerated (surgical, tool-written) to reflect `status_effects`'s corrected state.
- `tests/unit/tools/test_mechanism_registry_completeness_check.py` — pinned baseline counts updated
  with a real-investigation comment explaining the delta.

## Completion Summary
**Partial, ongoing** (per this ticket's own explicit "deliberately incremental" out-of-scope note —
not moved to `tickets/done/`). This batch: 5 of 7 `systems: [combat]` mechanisms now bound
(`action_pacing_readiness`/`skill_unlocks` left unbound with a stated, symbol-level-boundary
reason each), plus one real state correction (`status_effects` partial->orphan) surfaced and fully
propagated per AC #3. `orphan`/`gated` coverage (this ticket's own 100%-target claim-types) is
unchanged by this batch and remains the next priority for whoever continues it.
