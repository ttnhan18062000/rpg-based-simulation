---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260811-RELATIONSHIP-AWARE-FORM-PARTY
artifact_type: test_plan
tags: [cognition, adventure, social]
---

# Test Plan — TCK-20260811-RELATIONSHIP-AWARE-FORM-PARTY

## Regression Surface

Existing tests that must keep passing, grouped by domain:

**Unit — party composition (`src/systems/social_systems/party_composition.py` — the primary changed file):**
- `tests/unit/social/test_party_composition.py` — all 16 tests: `infer_party_role` (5), `score_role_diversity` (3),
  `score_ocean_compatibility` (3), `score()` (2: `test_score_empty_returns_zero`,
  `test_score_balanced_party_higher_than_homogeneous`), and 3 `AdventureRouteGenerator.generate()` FORM_PARTY
  tests (`test_form_party_route_generated_when_sociable_and_candidates_exist`,
  `test_form_party_route_not_generated_when_low_sociability`,
  `test_form_party_benefit_reflects_composition_score`). All existing `score()` calls are positional/entities-only
  — any new parameter must default to reproducing today's exact numeric output for these tests.

**Unit — adventure scoring (`src/domains/adventure/scoring.py` consumers, only if Plan touches this file per Risk 1):**
- `tests/unit/domains/adventure/test_phase3_route_scoring.py` — in particular
  `test_sociability_weight_is_0_40_on_form_party_route` (line 200), `test_scoring_does_not_use_hidden_world_truth`
  (150), `test_route_scoring_is_deterministic` (160)
- `tests/unit/domains/adventure/test_depletion_scoring.py` — unrelated family (`GATHER_RESOURCE`) but same file;
  must show zero interaction with a FORM_PARTY-only change
- `tests/unit/domains/adventure/test_memory_informed_scoring.py` — sibling `memory_adjustment` term already has a
  FORM_PARTY branch (`boost_party_trust` → `+1.0`); must not regress if a new FORM_PARTY term is added alongside it
- `tests/unit/domains/adventure/test_capability_confidence_scoring.py` — sibling `confidence_bonus` term; confirms
  it stays FORM_PARTY-inert (gated to GATHER_RESOURCE/CRAFT_UPGRADE only)

**Unit — social systems (adjacent, must show zero behavior change unless explicitly touched):**
- `tests/unit/social/test_betrayal_consequence.py`, `tests/unit/social/test_recruitment.py`,
  `tests/unit/social/test_social_memory.py` — establish/exercise the `trust_history` read/construction pattern this
  ticket reuses; must remain unaffected since this ticket does not modify `RelationshipService` or `SocialComponent`
- `tests/unit/social/test_party_lifecycle.py` — party defection/fair-share/leadership logic, same subsystem
  (`src/systems/social_systems/`), must show zero interaction
- `tests/unit/campaigns/test_grief_urgency.py` — covers SOC-232 (nemesis blocker), the mechanism sharing
  `generator.py`'s FORM_PARTY code region; must remain unaffected/still pass if the new trust/bonds read is added
  next to it

**Integration:**
- `tests/integration/domains/adventure/test_phase3_adventure_decision_phase.py`
- `tests/integration/scenarios/test_phase3_adventure_decision_scenarios.py`
- `tests/unit/ai/goals/test_adventure_goal_scorer.py` — confirms the live `AdventureGoalScorer` → `generate()`/
  `score()` call chain remains unaffected by internal FORM_PARTY enrichment

**Arena-combat:** None — this ticket touches only party-formation scoring, not combat resolution.

## New Tests Required

Per acceptance criteria. Test 1-3 are unconditional; Test 4-6 depend on Plan's Risk-1 decision (whether `scoring.py`
also gains a term, per the open question in investigation.md) — write them if Plan wires that layer, otherwise mark
`xfail`/omit and record the decision in plan.md.

1. **`test_party_composition_score_reflects_candidate_trust_history`**
   - Category: unit
   - Verifies: two otherwise-identical candidate pools, differing only in one candidate's `trust_history`/`bonds`
     value as seen from the acting entity's perspective, produce **different** `PartyCompositionScorer.score()`
     return values (directly satisfies AC2's literal wording, at the layer where per-candidate iteration actually
     happens). Construct via `V2EntityBuilder(...).social(trust_history={candidate_id: score})` (established pattern
     from `test_recruitment.py`/`test_betrayal_consequence.py`).
   - Location: `tests/unit/social/test_party_composition.py` (alongside `test_score_balanced_party_higher_than_homogeneous`)

2. **`test_party_composition_score_unchanged_when_trust_param_omitted`**
   - Category: unit, backward-compatibility guard
   - Verifies: calling `PartyCompositionScorer.score(entities)` with no acting-entity/trust argument (exactly as
     every existing call site does, including `generator.py:139`) produces numerically identical output to today's
     behavior — guards AC4's "additive, not replacement" requirement and every pre-existing positional call site.
   - Location: `tests/unit/social/test_party_composition.py`

3. **`test_form_party_route_benefit_differs_with_candidate_trust`**
   - Category: integration (through `AdventureRouteGenerator.generate()`)
   - Verifies: two `_FakeState`s differing only in one FORM_PARTY candidate's `trust_history`/`bonds` produce
     different `route.expected_benefit` (and/or `route.confidence`, if Plan wires trust into that generation-time
     term too) for the generated FORM_PARTY route — end-to-end version of Test 1, following
     `test_form_party_benefit_reflects_composition_score`'s existing shape.
   - Location: `tests/unit/social/test_party_composition.py`

4. **(Conditional on Plan wiring `scoring.py`) `test_sociability_weight_still_0_40_with_trust_term_present`**
   - Category: unit, regression guard for AC4
   - Verifies: with a nonzero trust/bonds-derived signal present, `AdventureRouteScorer.score()`'s `personality_bias`
     for a FORM_PARTY route with `sociability=1.0` is still exactly `0.40` (the existing sociability term is
     untouched; the new term is a separate additive quantity, checked independently).
   - Location: `tests/unit/domains/adventure/test_phase3_route_scoring.py` (directly alongside
     `test_sociability_weight_is_0_40_on_form_party_route`) or a new `test_relationship_aware_form_party_scoring.py`
     following the sibling tickets' one-new-file-per-ticket naming precedent.

5. **(Conditional) `test_relationship_term_is_additive_not_replacement`**
   - Category: unit
   - Verifies: the new scoring.py-level term (if any) is a separately-named/separately-tracked additive contribution
     to `final_score` — not folded into or replacing `personality_bias`/`confidence_bonus`'s existing formula.
   - Location: same new file as Test 4.

6. **(Conditional) `test_relationship_term_reads_only_entity_owned_social_state`**
   - Category: architecture guard (information-opacity boundary, mirrors `test_scoring_does_not_use_hidden_world_truth`)
   - Verifies: the trust/bonds-derived term reads only `entity.social` (the acting entity's own subjective
     relationship record), never any global/omniscient counterparty state.
   - Location: same new file as Test 4.

7. **`test_party_composition_trust_lookup_does_not_mutate_social_state`**
   - Category: architecture guard
   - Verifies: calling the (possibly-extended) `PartyCompositionScorer.score()` does not change
     `entity.social.trust_history`/`bonds` for either the acting entity or any candidate — confirms the read is a
     local, throwaway computation, never written back to durable entity state (CLAUDE.md durable-state rule).
   - Location: `tests/unit/social/test_party_composition.py`

8. **`test_party_composition_trust_lookup_defaults_safely_for_unknown_candidate`**
   - Category: unit, edge case
   - Verifies: a candidate with no entry in the acting entity's `trust_history`/`bonds` dicts does not raise and
     falls back to a neutral default (e.g. `0.0`) — the common case for a never-before-met candidate.
   - Location: `tests/unit/social/test_party_composition.py`

## Scoped Pytest Commands

```
.venv/bin/python3 -m pytest tests/unit/social/test_party_composition.py tests/unit/social/test_party_lifecycle.py tests/unit/social/test_betrayal_consequence.py tests/unit/social/test_recruitment.py tests/unit/social/test_social_memory.py -v
.venv/bin/python3 -m pytest tests/unit/domains/adventure/ -v
.venv/bin/python3 -m pytest tests/unit/campaigns/test_grief_urgency.py tests/unit/ai/goals/test_adventure_goal_scorer.py -v
.venv/bin/python3 -m pytest tests/integration/domains/adventure/test_phase3_adventure_decision_phase.py tests/integration/scenarios/test_phase3_adventure_decision_scenarios.py -v
```

Never `pytest tests/` — scoped to party-composition + adventure-scoring + directly-adjacent social/campaign domains,
matching both sibling tickets' scoping pattern.

## Anti-Drift Test Guards

- **Test 2** (`test_party_composition_score_unchanged_when_trust_param_omitted`) is the primary guard against
  silently breaking every pre-existing positional call site of `PartyCompositionScorer.score()` (`generator.py:139`
  plus 3 direct test call sites) — a signature change that isn't fully backward-compatible would fail this first.
- **Test 4** (conditional) is the direct guard for AC4's bit-identical requirement on the existing
  `sociability × 0.40` term — the single most explicit acceptance criterion in this ticket.
- **Test 7** guards against the trust/bonds read silently becoming a write — the same class of guard the capability-
  confidence sibling ticket used (`test_capability_confidence_does_not_mutate_entity_self_model`).
- **Test 6** (conditional) guards the information-opacity boundary the whole `scoring.py` module is built on,
  mirroring `test_scoring_does_not_use_hidden_world_truth`.
- Existing `test_party_lifecycle.py` and `test_grief_urgency.py` (SOC-232 nemesis mechanism) suites running
  **unchanged** guard against the new trust-aware read being accidentally conflated with the separate nemesis-block
  mechanism that lives in the same `generator.py` code region.
- STRAT-227 (if `scoring.py` is touched) and the new social_narrative.yaml parity entry (see investigation.md, Docs
  Requiring Update) should each list every new test file added here in their `test_path` in the same commit that
  changes `v2_evidence`/`text` — a lagging parity-ledger update on a `verified`/`P1` entry is itself a drift signal
  Verify should catch.
