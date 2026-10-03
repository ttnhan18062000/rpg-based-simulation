---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260903-INFORMATION-HUB-ACCUMULATION
artifact_type: test_plan
tags: [information, feature-flags, faction]
---

# Test Plan — TCK-20260903-INFORMATION-HUB-ACCUMULATION

## Regression Surface

**Unit — information/belief domain:**
- `tests/unit/cognition/test_information_seeking.py` — `TestInformationProviderState`,
  `TestLeadContradiction`, `TestPaidInformationTransaction`, `TestLeadRoutingSystem`,
  `TestKnowledgeStalenessDecay` classes must keep passing unchanged; this ticket adds a *new*
  accumulation branch alongside `LeadContradictionSystem`'s existing decrement branch in the same
  `information_providers_update` dict.
- `tests/unit/domains/information/test_phase5_information_source_profile.py`
- `tests/unit/domains/information/test_phase5_information_assimilation.py`
- `tests/unit/domains/information/test_phase5_information_belief_phase.py`
- `tests/unit/engine/test_information_intent_execution_phase.py`
- `tests/unit/strategic/test_belief_cycle.py`
- `tests/unit/strategic/test_belief_integration.py`

**Unit — quest / guild:**
- `tests/unit/engine/test_guild_visit_phase.py` — must keep passing; the new accumulation trigger
  must not change `GuildVisitPhase`'s existing `is_newly_completed`/`ESCORT`-reputation behavior.
- `tests/unit/ai/test_guild_need_scorer.py`
- `tests/architecture/test_guild_action_dormancy.py` — guards that `GuildAction` is referenced only
  at its one deliberate site; must not regress if this ticket touches `guild.py`/`quests.py`.
- `tests/unit/world/test_guild_pipeline.py`, `tests/unit/world/test_guild_intel.py`

**Unit — faction:**
- `tests/unit/domains/faction/test_faction_awareness.py` — `FactionAwarenessService`'s existing
  RESOURCE_DEPLETED→tension_delta behavior must be unaffected by a new, parallel
  territory/diplomatic-relations-walking consumer.
- Any existing E53B diplomatic-state-machine unit tests covering
  `src/domains/faction/diplomatic_state_machine.py` (locate via
  `tests/unit/domains/faction/` at implementation time) — must keep passing; this ticket only
  *reads* `diplomatic_relations`, it does not mutate diplomatic state.

**Integration:**
- `tests/integration/scenarios/test_phase5_information_belief_scenarios.py`
- `tests/unit/kernel/` — full-pipeline determinism/ordering tests, to confirm the new phase (if any)
  is correctly positioned in `refine()`'s deterministic phase sequence and does not break existing
  phase-ordering guarantees.

**Feature flag regression:**
- `tests/unit/config/test_phase10_feature_flags.py` — confirm the new flag is registered correctly
  and, per this repo's own established pattern (`TCK-20260807-QUEST-GUILDACTION-DEAD-WIRING`'s test
  summary), does NOT need allowlisting since it defaults OFF.

## New Tests Required

Per acceptance criteria:

1. **Accumulation mechanism exists and mutates via typed update path**
   - Test name: `test_information_provider_accumulation_field_default` /
     `test_accumulation_state_update_applies_via_authoritative_pipeline`
   - Category: unit
   - Verifies: `InformationProviderState` (or its update-path record) gains a real, typed
     accumulation field with a sane default; a `StateUpdate.information_providers_update` entry
     carrying the new field applies correctly through the authoritative apply path
     (before/after `AuthoritativeState.information_providers[id]` comparison, not just an event
     firing — matches AC #1's explicit "not just an event firing" requirement).
   - Location: `tests/unit/cognition/test_information_seeking.py` (extends
     `TestInformationProviderState`) or a new `tests/unit/domains/information/
     test_information_provider_accumulation.py`, following the existing file-naming pattern in
     that directory.

2. **Quest-report-back triggers accumulation (before/after state assertion)**
   - Test name: `test_quest_completion_increments_provider_accumulation`
   - Category: unit
   - Verifies: driving `QuestResolutionSystem.enforce()` (or the new hook Plan designs around it)
     with a completing quest whose attribution resolves to a real `InformationProviderState`
     produces an `information_providers_update` entry with the accumulation field changed from its
     prior value — asserted via direct before/after `AuthoritativeState`/`StateUpdate`
     construction (per Risk #3 in investigation.md, do NOT depend on the corpus-broken
     HUNT/GATHER/BOUNTY/LIBERATE paths; use EXPLORE or a directly-constructed `QuestState` to
     isolate from those unrelated, already-disclosed gaps).
   - Location: `tests/unit/engine/test_quest_reward_phase_information_accumulation.py` (new) or
     alongside existing `QuestResolutionSystem` tests if a test file for `src/engine/quests.py`
     already exists (confirm exact location at implementation time — not found by this
     investigation, `src/engine/quests.py` tests were not enumerated in Related Code Areas).

3. **Flag-OFF path is a true no-op**
   - Test name: `test_information_hub_accumulation_flag_off_no_state_change`
   - Category: unit (architecture-guard flavored)
   - Verifies: with the new flag left at its default (`OFF`), a scenario that would otherwise
     trigger accumulation and/or propagation leaves `information_providers`/`factions` byte-identical
     before and after (matches AC #3's explicit requirement) — mirrors the flag-OFF test shape
     already used by `test_guild_visit_phase.py` for `ENABLE_GUILD_QUEST_GENERATION`.
   - Location: same file as test 2, or a dedicated
     `tests/unit/domains/optimization/test_information_hub_flag_off.py` if the mechanism spans
     multiple phases.

4. **City-to-City propagation within the same faction**
   - Test name: `test_critical_information_propagates_within_faction_territory`
   - Category: unit
   - Verifies: critical information originating at a region owned by Faction/Country A reaches
     sibling regions in `FactionState.territory` for Faction A, using the
     `FactionAwarenessService`-style `recent_world_events`/territory-walk pattern (per
     investigation.md's "Faction territory/diplomatic propagation precedent").
   - Location: `tests/unit/domains/faction/test_critical_information_propagation.py` (new),
     mirroring `test_faction_awareness.py`'s existing structure (`_make_state()`, event-fixture
     helpers).

5. **City-to-Country propagation crosses factions correctly, gated on diplomatic relation**
   - Test name: `test_critical_information_reaches_allied_country_not_unrelated_country`
   - Category: unit
   - Verifies exactly the AC #4 scenario: critical info at a City owned by Country A reaches
     sibling Cities under Country A but NOT an unrelated Country B — plus (if Plan decides
     diplomatic-relation gating applies) a positive case showing it DOES reach an
     `ALLIED`/appropriate-relation Country C, to prove the diplomatic-relations walk is real, not
     just territory-only.
   - Location: same new file as test 4.

6. **No new topology type introduced (architecture guard)**
   - Test name: `test_no_new_faction_topology_field_added` (or an `ast`/dataclass-fields
     introspection check)
   - Category: architecture guard
   - Verifies: `FactionState`'s field set is unchanged from the current schema (`faction_id`,
     `territory`, `resources`, `diplomatic_relations`, `active_doctrines`, `military_strength`,
     `tension_level`) — directly enforces the Scope's "no new topology type" constraint and AC #4's
     "walks FactionState.territory/diplomatic_relations (no new topology type)."
   - Location: `tests/architecture/test_information_hub_no_new_topology.py` (new) or an assertion
     added to an existing `FactionState` schema-stability test if one already exists (search
     `tests/unit/` for `FactionState` field-count assertions at implementation time).

7. **Guide-to-Guide / hub-to-hub exchange does not construct a Conversation system**
   - Test name: `test_no_conversation_class_introduced` (architecture guard, grep-based) — OR, more
     durably, a doc/comment assertion if a grep-based test is judged too brittle.
   - Category: architecture guard
   - Verifies AC #5: whatever mechanism Plan designs for Guide-to-Guide exchange is implemented at
     the state/`StateUpdate` level, not via a new `Conversation`/dialogue class — matches the
     ticket's explicit Out of Scope item. If Plan scopes this out entirely (no exchange mechanism
     built), this test instead just asserts no `Conversation` class was introduced anywhere in
     `src/` (extends the zero-grep-hits fact re-confirmed in investigation.md).
   - Location: `tests/architecture/` alongside test 6, or folded into it as one architecture-guard
     module for this ticket.

## Scoped Pytest Commands

```
pytest tests/unit/cognition/test_information_seeking.py tests/unit/domains/information/ tests/unit/engine/test_information_intent_execution_phase.py tests/unit/strategic/test_belief_cycle.py tests/unit/strategic/test_belief_integration.py tests/integration/scenarios/test_phase5_information_belief_scenarios.py -v

pytest tests/unit/engine/test_guild_visit_phase.py tests/unit/ai/test_guild_need_scorer.py tests/architecture/test_guild_action_dormancy.py tests/unit/world/test_guild_pipeline.py tests/unit/world/test_guild_intel.py -v

pytest tests/unit/domains/faction/ -v

pytest tests/unit/config/test_phase10_feature_flags.py -v

pytest tests/architecture/ -k "information_hub or no_new_faction_topology or no_conversation" -v
```

Do not run `pytest tests/` — scope to the domains above (information/belief, quest/guild, faction,
feature-flag config, and the new architecture guards).

## Anti-Drift Test Guards

- **Decrement-path isolation**: a regression test confirming `LeadContradictionSystem`'s existing
  `_RELIABILITY_PENALTY`/`_RELIABILITY_FLOOR` decrement behavior (floored at 0.1) is byte-identical
  before and after this ticket's changes — catches accidental cross-talk between the new
  accumulation branch and the existing decrement branch sharing the same
  `information_providers_update` dict merge.
- **Corpus-broken-quest-kind isolation**: a test asserting the new accumulation trigger does NOT
  silently "start working" for HUNT/GATHER/BOUNTY/LIBERATE quest kinds as an unintended side effect
  of any metadata-population change made elsewhere in this ticket — catches scope creep into the
  separately-tracked `TCK-20260807-QUEST-EVALUATOR-GATHER-BOUNTY-LIBERATE-GAP` territory.
- **`ENABLE_GUILD_QUEST_GENERATION` non-interference**: a test confirming this ticket's new flag
  does not implicitly flip or depend on `ENABLE_GUILD_QUEST_GENERATION` being ON in production
  defaults — the two flags must remain independently toggleable.
- **`FactionAwarenessService` non-regression under a new consumer**: a test confirming
  `compute_tension_updates()`'s own `RESOURCE_DEPLETED`→`tension_delta=+0.1` output is unchanged
  when a new critical-information consumer also reads `state.recent_world_events` in the same tick
  — catches accidental double-counting or event-window mutation.
- **Diplomatic relation non-mutation**: a test confirming the propagation mechanism only *reads*
  `diplomatic_relations` and never emits a `FactionUpdate(diplomatic_relations_set=...)` itself —
  catches scope creep into `src/domains/faction/diplomatic_state_machine.py`'s territory (a
  separate, already-built subsystem this ticket must not touch).
