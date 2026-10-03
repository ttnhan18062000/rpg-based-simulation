---
status: active
layer: simulation
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20260906-CAMPAIGN-SCORECARD-EVALUATOR-FIELDS
date: 2026-09-06
---

# Test Plan: TCK-20260906-CAMPAIGN-SCORECARD-EVALUATOR-FIELDS

## Regression Surface
- `tests/unit/domains/campaigns/test_phase9_semantic_campaign_scorecard.py` — must keep passing unmodified except for new test additions (existing 7 fields untouched).
- `tests/unit/progression/test_lifecycle.py` — idea 55/58's own existing unit tests must keep passing (this ticket adds a new, separate deterministic Kernel-tick test, does not modify `lifecycle.py`).
- `tests/integration/scenarios/test_campaign_runtime.py` — real Kernel-driven `CampaignOrchestrator` tests must keep passing (this ticket adds a new sibling test file, does not modify orchestrator.py).

## New Tests Required (per AC)
1. **AC1 + AC3** (`tests/unit/domains/campaigns/test_phase9_semantic_campaign_scorecard.py`):
   - `test_reputation_inheritance_check_fails_when_seed_unset_after_death_with_heir` — hand-built `EntityArcReport` with a `major_events` "died" entry carrying `heir_entity_id` set but `inherited_reputation_seed` absent → `reputation_inheritance_check == "fail"`.
   - `test_reputation_inheritance_check_passes_when_seed_present` — same but with `inherited_reputation_seed` set → `"pass"`.
   - `test_nemesis_transfer_check_passes_and_fails_correctly` — one case with `nemesis_transferred=True` → `"pass"`; one with a nemesis-bearing death but `nemesis_transferred` absent/False → `"fail"`.
   - `test_new_fields_default_partial_when_no_death_occurs` — no "died" events at all → both fields `"partial"` (not exercised this run), matching the existing `"partial"` semantics used elsewhere in the evaluator.
2. **AC2, piece A (idea 55+58)** — new file `tests/integration/campaigns/test_lineage_dispatch_deterministic_kernel_tick.py`: one real `Kernel.tick_once()` test with a hand-built `AuthoritativeState` (deceased at `age_ticks >= max_age_ticks` for deterministic OLD_AGE death, pre-set `strategic.blockers["nemesis_3"]`, a real `social.bonds` entry pointing at the heir) asserting the heir's post-tick state carries `strategic.blockers["inherited_nemesis_3"]` at half severity and `cognition.motivation.named_intention` referencing the same antagonist.
3. **AC2, piece B (idea 55 cross-episode / idea 62)** — new file `tests/integration/campaigns/test_nemesis_relation_and_chronicle_fidelity_campaign.py`: a real 4-episode `CampaignOrchestrator` run (`frontier_living_world`) asserting `orch.state.nemesis_relations` gets populated after repeated antagonism recorded in `social_memories`, and `orch.state.historical_drift` shows `fidelity < 1.0` for an episode-0 event once episode 3 completes (2nd Era begins).
4. **AC2, piece C (idea 53)** — same new file or a small addition to `tests/unit/social/test_reputation.py` (whichever already exists): asserts `combine_public_reputation(1.6, 0.4) == 1.0`, and a `V2EntityBuilder(...).birth_record(parent_a_public_reputation=1.6, parent_b_public_reputation=0.4)` child has `social.public_reputation == 1.0`.

## Scoped Pytest Commands
```
pytest tests/unit/domains/campaigns/ tests/integration/campaigns/ tests/unit/progression/test_lifecycle.py tests/unit/social/ -q
```

## Anti-Drift Test Guards
- The AC3 fail-path test must assert `== "fail"` literally (not just `!= "pass"`) — a tautology-guard.
- The deterministic Kernel test must assert the DECEASED's own `lifecycle.active is False` too, confirming the death actually fired (not a false positive from a heir already carrying an unrelated blocker).
