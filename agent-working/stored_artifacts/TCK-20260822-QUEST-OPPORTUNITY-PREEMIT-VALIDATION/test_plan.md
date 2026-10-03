---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260822-QUEST-OPPORTUNITY-PREEMIT-VALIDATION
artifact_type: test_plan
tags: [world, content, determinism]
---

# Test Plan — TCK-20260822-QUEST-OPPORTUNITY-PREEMIT-VALIDATION

## Regression Surface

**Unit — quest generation (must pass unmodified, no test edits):**
- `tests/unit/quest/test_quest_generation.py::test_resource_crisis_quest_generated_on_depletion` (AC3-named)
- `tests/unit/quest/test_quest_generation.py::test_threat_response_quest_generated_on_high_severity` (AC3-named)
- `tests/unit/quest/test_quest_generation.py::test_quest_generation_determinism`
- `tests/unit/quest/test_quest_generation.py::test_threat_response_not_generated_for_low_severity`
- `tests/unit/quest/test_quest_generation.py::test_entity_need_quest_stub_returns_none`
- `tests/unit/quest/test_quest_lifecycle.py` (registry field + expiry sweep — upstream/downstream of
  the new filter, must be unaffected)

**Unit — world emergence phase boundary:**
- `tests/unit/domains/world_emergence/test_phase8_world_emergence_boundary.py` (all tests — the
  no-mutation and determinism guards here must still hold after the filter is added)
- `tests/unit/domains/world_emergence/test_quest_registry_wiring.py::test_world_emergence_populates_quest_registry`
  — critical regression check: builds a bare `AuthoritativeState(tick=5, seed=1)` with **empty**
  `resource_nodes`/`factions` and asserts the resulting opportunity still reaches `quest_registry`.
  This is the concrete case validating the "no matching evidence → cannot verify → pass" design
  decision from investigation.md's Risks section — if the new filter gets that backwards, this test
  fails first.

**Integration — world emergence phase:**
- `tests/integration/domains/world_emergence/test_phase8_world_emergence_phase.py` (both tests —
  confirms the phase's public `execute()` contract and event-consumption behavior are unaffected by
  the internal filtering addition)

**Unit — worldbuilding (out-of-scope-touch guard):**
- `tests/unit/worldbuilding/test_world_grammar_reachability.py`
- `tests/unit/worldbuilding/test_corpus_reachability_baseline.py`
- `tests/unit/worldbuilding/test_world_validator.py`
- These must pass **byte-identical to their current state** — they are the predecessor ticket's own
  regression surface and this ticket must not touch `src/worldbuilding/validator.py` or
  `WorldValidator` at all (per Out of Scope / Anti-Drift Hazards).

## New Tests Required

1. **`test_faction_coherence_rejects_zero_territory_faction`**
   - Category: unit
   - Verifies: a `QuestOpportunity` constructed directly with `faction_source` set to a faction ID
     that either (a) is absent from `state.factions`, or (b) is present with `territory=()`, is
     rejected by the new pre-emit check — an explicit rejection, not a silent pass. Since no live
     generator path currently sets `faction_source`, this test constructs the `QuestOpportunity`
     fixture directly (per investigation.md Risks — this negative path is not reachable through
     `QuestOpportunityGenerator` today).
   - Location: new file `tests/unit/domains/world_emergence/test_quest_opportunity_preemit_validation.py`

2. **`test_faction_coherence_accepts_faction_with_territory`**
   - Category: unit
   - Verifies: a `QuestOpportunity` with `faction_source` matching a `FactionState` entry whose
     `territory` is non-empty passes the faction-coherence check.
   - Location: same new file.

3. **`test_faction_coherence_passes_when_faction_source_is_none`**
   - Category: unit
   - Verifies: the documented AC5 behavior — `faction_source=None` auto-passes the faction-coherence
     check (no faction claim to verify). Exercised directly through the real generator output
     (`from_resource_depleted`/`from_threat_signal`, both hardcode `faction_source=None` today) to
     also serve as a live-path regression guard.
   - Location: same new file.

4. **`test_resource_availability_rejects_when_all_matching_nodes_depleted`**
   - Category: unit
   - Verifies: a `QuestOpportunity` whose `objective_chain` references a resource type (e.g.
     `"fetch:iron_ore:3"`) for which every `ResourceNodeState` in `state.resource_nodes` with
     `yields_item == "iron_ore"` has `remaining_charges == 0` is rejected.
   - Location: same new file.

5. **`test_resource_availability_passes_when_any_matching_node_has_charges`**
   - Category: unit
   - Verifies: a `QuestOpportunity` referencing a resource type where at least one matching node has
     `remaining_charges > 0` passes, even if other matching nodes are depleted.
   - Location: same new file.

6. **`test_resource_availability_passes_when_no_matching_node_exists`** (anti-regression-critical)
   - Category: unit
   - Verifies: a `QuestOpportunity` referencing a resource type with **zero** matching nodes in
     `state.resource_nodes` (including the empty-dict case) passes — "cannot verify" is not a
     violation. This directly protects `test_world_emergence_populates_quest_registry`'s AC3
     regression requirement; write it explicitly rather than relying on the integration test alone
     to catch a regression here.
   - Location: same new file.

7. **`test_passing_opportunity_reaches_quest_registry_add_unfiltered`** (AC3, byte-identical output)
   - Category: integration
   - Verifies: calling `WorldEmergencePhase.execute()` with events that produce opportunities
     passing all grammar checks yields a `quest_registry_add` list identical (by `id`, field values)
     to today's unfiltered output — i.e. the filter is a true no-op for the currently-passing case.
   - Location: `tests/unit/domains/world_emergence/test_phase8_world_emergence_boundary.py` (extend)
     or the new file — prefer extending the existing boundary test file to keep the "phase-level
     invariants" tests co-located.

8. **`test_rejected_opportunity_excluded_from_quest_registry_add`**
   - Category: integration
   - Verifies: given a state with a dispossessed faction or depleted resource node, and a
     hand-constructed `QuestOpportunity` reproducing that scenario merged into the phase's event
     pipeline (or, if the live generator can't produce faction_source != None, verifying the
     call-site filter directly against `WorldEmergencePhase`'s internal filtering function/method
     with a manually-built `quest_opps` list), the excluded opportunity does not appear in
     `update.quest_registry_add`.
   - Location: same new file, or extend
     `tests/integration/domains/world_emergence/test_phase8_world_emergence_phase.py`.

9. **`test_preemit_validation_is_deterministic_and_read_only`** (AC4)
   - Category: architecture guard
   - Verifies: calling the pre-emit check twice with identical `(QuestOpportunity,
     AuthoritativeState)` inputs gives identical verdicts, and `state` (by `to_canonical_dict()` or
     field equality) is unchanged after the call(s) — matching the existing
     `test_world_emergence_service_does_not_mutate_state_directly` pattern in
     `test_phase8_world_emergence_boundary.py`.
   - Location: same new file.

10. **`test_preemit_check_does_not_call_uuid_or_time_based_seeding`** (contract preservation)
    - Category: architecture guard
    - Verifies (by construction/inspection, or by asserting deterministic output across repeated
      calls with a fixed seed/tick as a proxy) that the new check preserves
      `QuestOpportunityGenerator`'s documented "no uuid(), no time-based seeding" contract — the new
      code must not introduce either, since it sits in the same call chain.
    - Location: same new file (can be folded into test 9 as an assertion, or kept separate for
      clarity — implementer's choice, not prescribed further here).

## Scoped Pytest Commands

```
pytest tests/unit/quest/ tests/unit/domains/world_emergence/ tests/integration/domains/world_emergence/ -m "not slow" -q
```

Anti-drift confirmation that the (correctly) untouched worldbuilding validator surface is unaffected:
```
pytest tests/unit/worldbuilding/ -m "not slow" -q
```

Never: `pytest tests/`.

## Anti-Drift Test Guards

- **`test_world_emergence_populates_quest_registry` and `test_resource_availability_passes_when_no_matching_node_exists`
  together** guard against the single most likely silent-failure mode identified in
  investigation.md: treating "no resource node found at all" as "depleted" instead of
  "cannot-verify." If either regresses, the fix must correct the check's evidence-absence handling,
  not weaken the new test.
- **`test_faction_coherence_passes_when_faction_source_is_none`** guards against a scope-creep
  temptation to "fix" the generator to start populating `faction_source` as part of this ticket —
  that is out of scope (this ticket only wires validation around existing generator output); the
  test locks in that both live generator methods keep producing `faction_source=None` and that this
  remains a defined pass-through, not a gap to be "fixed" here.
- **`tests/unit/worldbuilding/test_corpus_reachability_baseline.py` in the scoped run** guards
  against accidental modification of `WorldValidator`'s default rule set or `catalog_repo` wiring —
  any diff in that baseline's 75-violation count would indicate this ticket drifted into touching
  build-time validator code, which is explicitly out of scope.
- **A test asserting `QuestOpportunityGenerator.from_resource_depleted`/`from_threat_signal`
  signatures are unchanged** (or simply: the existing `WORLD-098`/`WORLD-099`-cited tests passing
  unmodified) guards against the filter being implemented inside the generator methods rather than
  at the `phase.py` step-5b call site, which the investigation's Anti-Drift Hazards flagged as a
  conflation risk.
- **Determinism test (new test 9) run twice in the same pytest session** (or via
  `pytest --count=2` if available, otherwise two explicit assertions in one test body) guards
  against a check that non-deterministically iterates `state.factions`/`state.resource_nodes`
  (e.g. unsorted dict iteration feeding into a first-match-wins rejection reason) producing
  different rejection messages/verdicts across runs.
