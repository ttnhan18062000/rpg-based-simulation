---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260828-REPUTATION-WITNESSED-EVENT-WIRING
artifact_type: plan
tags: [social, cognition, progression]
---

# Implementation Plan — TCK-20260828-REPUTATION-WITNESSED-EVENT-WIRING

## Summary

This plan wires `ReputationUpdateService.process_witnessed_event()` (currently a zero-caller,
orphaned static method) to a real, live production event: `QuestKind.ESCORT` quest completion,
detected in `QuestResolutionSystem.enforce()`. This is the resolved decision from
investigation.md (Option 1) — not re-litigated here. The approach is: (1) add the enum value,
(2) fix a narrowly-scoped, real compiler bug that currently silently miscompiles 6 world-content
files' `type: "escort"` quests to `QuestKind.EXPLORE`, (3) insert a merge-safe reputation-update
call into `QuestResolutionSystem.enforce()`'s existing per-quest completion loop, following the
exact `NearDeathHardeningPhase.apply()` base-cognition precedent to avoid clobbering
`MemoryUpdatePhase`'s same-tick writes, (4) add parity ledger entry `SOC-252`, (5) correct two
stale doc references to name the real call site, and (6) add the five required tests (unit +
integration + architecture guard) proving the wiring, the compiler fix, the non-escort no-op
guard, and the merge-safety property. Each step is independently verifiable and touches exactly
one file (or one tightly-coupled pair: code + its direct test).

## Steps

### Step 1 — Add `QuestKind.ESCORT` enum member
**Files:** `src/core/models/quests.py`

**Change:** In the `QuestKind` enum (`src/core/models/quests.py:7-12`, currently `HUNT, GATHER,
EXPLORE, LIBERATE, BOUNTY`, all via `auto()`), append `ESCORT = auto()` as a new final member,
after `BOUNTY`. Verified non-breaking: `src/api/presenters/state_presenter.py:90` serializes via
`q.quest_kind.name`, never the `auto()`-assigned int, so appending at the end does not disturb
any existing serialized value or ordering-dependent comparison. No other writer touches this
enum's member list.

**Do NOT touch:** `QuestStatus`, `QuestOpportunityStatus`, or any other enum in this file. Do not
reorder existing members.

**Verify:** `test_quest_kind_escort_enum_value_is_new_member_only` (Step 6).

---

### Step 2 — Fix `get_quest_kind()` to map `"escort"` correctly
**Files:** `src/worldbuilding/compiler.py`

**Change:** In `get_quest_kind(kind_str)` (`src/worldbuilding/compiler.py:85-98`), the function
upper-cases `kind_str` and checks substring membership for `HUNT`/`GATHER`/`EXPLORE`/`LIBERATE`/
`BOUNTY` only, falling through to `return QuestKind.EXPLORE` (line 98) for anything else,
including `"escort"`. Add one new `elif` branch, before the existing `elif "BOUNTY" in k:` branch
(or after — order among the 5 existing branches does not matter since quest kind strings are
mutually exclusive in practice): `elif "ESCORT" in k: return QuestKind.ESCORT`. This is confirmed
live: `data/content/world_modules/{bandit_road_trade_pressure,forest_warden_grove,
frontier_village_core,orc_clan_territory,settled_quarter,trading_company_hub}.yaml` all currently
author `type: "escort"` (6 files, confirmed via investigation.md's direct grep) and are silently
miscompiled to `EXPLORE` today via this exact fallthrough.

**Other writers to this function/resource:** `get_quest_kind()` has no other writers — it is a
pure mapping function with one definition site. Its only "consumers" are call sites inside
`src/worldbuilding/compiler.py` that construct `QuestState`/`QuestDefinition` objects from
authored YAML; none of those call sites need changes since they all just call `get_quest_kind()`
and use its return value.

**Do NOT touch:** The `"fetch"`, `"defend"`, `"investigate"` cases, which also silently fall
through to `EXPLORE` today (confirmed same function, same fallthrough). This is a real,
pre-existing bug affecting those 3 literals too, but fixing them is explicitly out of scope per
the ticket and investigation.md's Anti-Drift Hazards — leave their fallthrough untouched.

**Verify:** `test_compiler_maps_escort_to_escort_quest_kind` (Step 6, extends
`test_helper_enum_mappers`).

**Dependency:** Requires Step 1 (`QuestKind.ESCORT` must exist before this branch can reference
it).

---

### Step 3 — Wire the merge-safe reputation-update call into `QuestResolutionSystem.enforce()`
**Files:** `src/engine/quests.py`

**Change:** In `QuestResolutionSystem.enforce()` (`src/engine/quests.py:154-231`), the per-entity
loop (`for e_id in sorted(list(update.entity_updates.keys())):`, line 168) contains a nested
per-quest-update loop (`for qu in q_updates:`, line 181) that already computes
`is_newly_completed = (updated_quest.quest_status == QuestStatus.COMPLETED and
project.quest_status == QuestStatus.ACTIVE)` (line 195), with `project` — the pre-update
`QuestState`, carrying `.quest_kind` — already in scope. Insert, inside the `if is_newly_completed
or is_retry_pending:` block (line 198) but gated additionally on `is_newly_completed and
project.quest_kind == QuestKind.ESCORT`:

1. Import `ReputationUpdateService` from `src.domains.commitment.reputation` as an inline import
   inside `enforce()`, matching this function's existing inline-import style (lines 160-163 already
   do `from src.core.updates import ...`, `from dataclasses import replace`, `from src.core.quests
   import QuestStatus`, `from src.quests.service import QuestService`). Also import `QuestKind`
   from `src.core.models.quests` the same way (not currently imported in this function — confirmed
   by reading lines 160-163, no existing `QuestKind` import in `enforce()`'s body).
2. Thread a per-entity `base_cognition` accumulator through the `for qu in q_updates:` loop (not a
   fresh read per `qu` — so that multiple ESCORT completions for the same entity in the same tick,
   e.g. via `multi_updates`, compose onto each other rather than each starting fresh from
   pre-tick state). Before the loop, initialize `cognition_touched = False` and `base_cognition =
   ent_upd.cognition_bundle_set if ent_upd.cognition_bundle_set is not None else entity.cognition`
   — this is the exact `NearDeathHardeningPhase.apply()` pattern
   (`src/engine/pipeline_phases/hardening.py:92-96`, confirmed by direct read: `base_cognition =
   entity_update.cognition_bundle_set if entity_update.cognition_bundle_set is not None else
   entity.cognition`). This is mandatory because `QuestRewardPhase`'s `quest_rewards` pipeline
   phase (`src/engine/pipeline.py:319`) runs after `MemoryUpdatePhase`'s `memory_update` phase
   (`src/engine/pipeline.py:156`), which unconditionally writes `cognition_bundle_set =
   new_entity.cognition` for every active entity every tick
   (`src/domains/memory/phase.py:51`, confirmed by investigation.md's direct read) — reading
   `entity.cognition` unconditionally here would silently discard that same-tick write.
3. When the ESCORT-completion condition fires: `updated_profile =
   ReputationUpdateService.process_witnessed_event(base_cognition.relationships.public_reputation,
   "successful_escort")` (fields confirmed live: `CognitionModel.relationships` at
   `src/core/cognition.py:552`, `RelationshipModel.public_reputation` at
   `src/core/cognition.py:529`, both read directly). Then `new_relationships =
   replace(base_cognition.relationships, public_reputation=updated_profile)`, `base_cognition =
   replace(base_cognition, relationships=new_relationships)`, `cognition_touched = True`. Continue
   the loop with the updated `base_cognition` as the new base for any subsequent `qu` in the same
   per-entity loop.
4. After the `for qu in q_updates:` loop ends (i.e. inside the same per-`e_id` iteration, alongside
   the existing `refined_entity_updates[e_id] = replace(ent_upd, resource_transfers=...,
   quest=new_q_upd)` at lines 226-229), extend that same `replace(...)` call to also set
   `cognition_bundle_set=base_cognition if cognition_touched else ent_upd.cognition_bundle_set`.
   This is required so an untouched entity's pre-existing `cognition_bundle_set` (e.g. set earlier
   this tick by `MemoryUpdatePhase`) is never clobbered to `None` — `replace()` only overrides the
   field you pass, so passing `ent_upd.cognition_bundle_set` unchanged when `cognition_touched` is
   `False` is a correct no-op, and passing the accumulated `base_cognition` when `True` is the
   real update.

**Other writers to this shared resource (`EntityUpdate.cognition_bundle_set` for the same
`e_id`/tick):**
- `MemoryUpdatePhase.apply()` (`src/domains/memory/phase.py:51`, pipeline phase `memory_update`,
  `src/engine/pipeline.py:156`) — runs *before* `quest_rewards`. This step's `base_cognition`
  read (point 2 above) already accounts for this: it reads whatever `MemoryUpdatePhase` staged as
  the starting point, so the two compose (memory changes preserved, reputation change layered on
  top) rather than racing or double-writing.
- `NearDeathHardeningPhase.apply()` (`src/engine/pipeline_phases/hardening.py:91-107`, pipeline
  phase `near_death_hardening`, `src/engine/pipeline.py:357`) — runs *after* `quest_rewards`
  (confirmed by investigation.md's phase ordering: `memory_update` (156) → ... → `quest_rewards`
  (319) → `near_death_hardening` (357)). Because `NearDeathHardeningPhase` itself follows the same
  base-cognition-if-set pattern reading `entity_update.cognition_bundle_set` first, this step's
  write (if it fires) will correctly become *its* base, so no clobbering occurs in that direction
  either. No code change needed in `hardening.py` — its existing pattern already handles a
  populated `cognition_bundle_set` arriving from an earlier phase.
- `CooperationPhase.execute()` (`src/domains/cooperation/phase.py`, pipeline phase `cooperation`,
  `src/engine/pipeline.py:189`) — runs between `memory_update` and `quest_rewards`, but confirmed
  by investigation.md to write no `cognition_bundle_set` at all today (only
  `social`/`strategic`/`property_updates`). No interaction — irrelevant to this step, not touched.
- `EntityUpdate.merge()` (`src/core/updates.py:59-91`, line 91: `if other.cognition_bundle_set is
  not None: changes["cognition_bundle_set"] = other.cognition_bundle_set`) performs a wholesale
  replace, not a deep merge, when both sides of a `.merge()` call set this field. This step does
  not call `.merge()` on `cognition_bundle_set` directly — it uses `dataclasses.replace()` on the
  single `ent_upd` for this `e_id`, which is a plain field assignment, not a merge of two competing
  `EntityUpdate` objects. Confirmed no other code path merges two `EntityUpdate`s for the same
  `e_id` within `enforce()`'s own scope.

**Do NOT touch:** `is_retry_pending` handling (leave unconditional reward-intent emission as-is
for all quest kinds); the `HUNT`/`GATHER`/`EXPLORE`/`LIBERATE`/`BOUNTY` branches (no new
conditional logic for them — the `project.quest_kind == QuestKind.ESCORT` gate must be the only
new condition); `CooperationPhase`, `ContractService`, `AbandonmentEvaluator`, or any
`"betrayal"`/`"clear_camp"` event_kind wiring (Option 2, out of scope per the resolved decision).

**Verify:** `test_successful_escort_completion_updates_reputation`,
`test_quest_completion_non_escort_kind_does_not_touch_reputation`,
`test_quest_reward_phase_preserves_memory_update_cognition_writes` (all Step 6).

**Dependency:** Requires Step 1 (`QuestKind.ESCORT` must exist). Independent of Step 2 (Step 2
only affects newly-*compiled* quests reaching `QuestKind.ESCORT`; Step 3's tests construct
`QuestState(quest_kind=QuestKind.ESCORT, ...)` directly, not via the compiler, so Step 3 can be
implemented and tested without Step 2 having landed — but both are required for the ticket's full
acceptance criteria).

---

### Step 4 — Add parity ledger entry `SOC-252`
**Files:** `docs/parity_ledger/social_narrative.yaml`

**Change:** Append a new entry after the current last entry `SOC-251`
(`docs/parity_ledger/social_narrative.yaml:3597`, confirmed via `grep -n "id: SOC-25"` — no
`SOC-252` exists yet, so `SOC-252` is the correct next ID, not a reused/updated one):

```yaml
- id: SOC-252
  text: Successful escort-quest completion is a witnessed event that updates the completing
    entity's public reputation profile (reliable label).
  status: verified
  priority: P1
  legacy_evidence: null
  v2_evidence: '`src/engine/quests.py` (`QuestResolutionSystem.enforce()`, ESCORT-completion
    branch) calls `src/domains/commitment/reputation.py`
    (`ReputationUpdateService.process_witnessed_event()`, event_kind="successful_escort") and
    applies the result via `EntityUpdate.cognition_bundle_set`, following the merge-safe
    base-cognition pattern established by `NearDeathHardeningPhase.apply()`
    (`src/engine/pipeline_phases/hardening.py:91-99`)'
  proof_type: parity
  test_path: '`tests/integration/scenarios/test_phase15_commitment_reputation_scenarios.py::test_successful_escort_completion_updates_reputation`'
  divergence_note: null
  support_boundary: null
```

This repo's writers to `social_narrative.yaml`: manual append (this step) and
`tools/parity_ledger_writer.py` (the sanctioned schema-validating tool for larger rewrites, per
project memory on parity-updater risk). Since this is a single new entry appended after the
existing last line, a direct `Edit` append is safe and does not risk the "full-file YAML rewrite"
corruption pattern that memory flags for ad-hoc scripts — no existing entries are touched or
reordered.

**Do NOT touch:** Any existing `SOC-*` entry in this file, including `SOC-001`
(`docs/parity_ledger/social_narrative.yaml:1-14`, which already covers a *different* betrayal
mechanism — private betrayal history gating recruitment, unrelated to
`ReputationUpdateService`). Do not touch any other parity ledger file
(`substrate.yaml`, `combat_movement.yaml`, etc.).

**Verify:** The `test_path` cited must exist and pass — i.e. this step is only complete once Step
6's `test_successful_escort_completion_updates_reputation` exists and passes (see Dependency
Map). Also confirm `python3 tools/layer_registry.py`/frontmatter-equivalent parity schema
validation (if any exists — check `docs/parity_ledger/schema.json`) accepts the new entry's shape
before considering this step done.

**Dependency:** The `test_path` field's target must exist (Step 6) before this step's addition is
considered verified, though the YAML text itself can be written concurrently.

---

### Step 5 — Correct stale doc references to name the real call site
**Files:** `docs/simulation/domains/commitment_contract.md`

**Change:** Two locations currently describe an aspirational/generic call site, confirmed by
direct read:
1. Line 44 (Inline-utility bullet list): `- **Engine event handlers** — call
   ReputationUpdateService.process_witnessed_event() when a social event is witnessed.` → change
   to name the real site: `- **QuestResolutionSystem.enforce()** (` + backtick +
   `src/engine/quests.py` + backtick + `, quest_rewards pipeline phase) — calls
   ReputationUpdateService.process_witnessed_event() when an ESCORT quest transitions to
   COMPLETED.`
2. Line 185 (Domain Interactions table, "Engine event handlers" row): `| **Engine event handlers**
   | Calls into commitment | ReputationUpdateService.process_witnessed_event() called when social
   events (escort, betrayal, camp_clear) are witnessed |` → change to: `|
   **QuestResolutionSystem.enforce()** (` + backtick + `src/engine/quests.py` + backtick + `) |
   Calls into commitment | ReputationUpdateService.process_witnessed_event() called with
   event_kind="successful_escort" when an ESCORT quest transitions ACTIVE→COMPLETED |` — do not
   claim `betrayal`/`camp_clear` are wired; only `successful_escort` is real after this ticket.

Match the precision style `NearDeathHardeningPhase.apply()`'s own docstring already uses for
naming its real call site (per investigation.md's Docs Requiring Update section).

**Other writers to this doc:** No other ticket/agent is known to be concurrently editing
`commitment_contract.md` (no in-progress ticket references it per `Related Tickets` scan). Not a
shared/concurrently-written resource in the same sense as source files above — safe to edit
directly.

**Do NOT touch:** `docs/simulation/social_systems_contract.md`'s Reputation section (wrong label
names/deltas) or Contracts section (stale `ESCORT ContractKind` reference) — both confirmed
pre-existing drift, explicitly flagged by investigation.md as out-of-scope future cleanup, not
this ticket's job. Do NOT touch `docs/mechanics/04_strategic_cognition.md` §6.9 (unrelated
`escort_target_id` route-scoring mechanism).

**Verify:** No automated test covers doc prose; verify by direct diff review that both locations
now name `QuestResolutionSystem.enforce()` / `src/engine/quests.py` and that no other line in the
file was altered.

**Dependency:** None (can be done independently of Steps 1-4, but should follow Step 3 so the
doc's description matches the actually-implemented behavior rather than a plan-stage guess).

---

### Step 6 — Add required tests
**Files:**
- `tests/integration/scenarios/test_phase15_commitment_reputation_scenarios.py` (extend — add new
  test functions alongside the existing 2)
- `tests/unit/quest/test_quest_rewards.py` (extend, for the non-escort no-op guard) — or co-locate
  alongside the integration test above if a pipeline-level fixture is required; implementer's call
  based on what fixtures `test_phase15_commitment_reputation_scenarios.py` already has available
- `tests/unit/worldbuilding/test_world_compiler.py` (extend `test_helper_enum_mappers`, line
  552-563, confirmed current content: asserts `"hunt"`/`"gather"`/`"explore"` only, no `"escort"`
  assertion yet)
- `tests/unit/quest/test_quest_system.py` (extend, for the enum-stability guard)

**Change:** Add the five tests specified in test_plan.md's "New Tests Required" section:

1. `test_successful_escort_completion_updates_reputation` — integration, in
   `test_phase15_commitment_reputation_scenarios.py`. Construct an entity with
   `QuestState(quest_kind=QuestKind.ESCORT, quest_status=QuestStatus.ACTIVE, ...)`, run it through
   `QuestResolutionSystem.enforce()` (or the fuller `AuthoritativeApplyPipeline` if the existing
   file's fixtures already do full-pipeline runs — check existing 2 tests' pattern first and match
   it), transition to COMPLETED, and assert the resulting `EntityUpdate.cognition_bundle_set
   .relationships.public_reputation.labels["reliable"]` increased by exactly `+0.1` (capped at
   `1.0`) relative to the pre-tick value — asserting the real service's actual delta, not a
   hand-constructed expected value (per test_plan.md's explicit anti-drift instruction).
2. `test_quest_completion_non_escort_kind_does_not_touch_reputation` — unit or integration.
   Construct a HUNT (or any of GATHER/EXPLORE/LIBERATE/BOUNTY) quest reaching
   `is_newly_completed`, assert the resulting `EntityUpdate.cognition_bundle_set` is unchanged
   from its pre-`enforce()` value (i.e. `None` if nothing else set it, or unchanged if something
   else did) — guards the new branch staying conditional on `QuestKind.ESCORT` specifically.
3. `test_quest_reward_phase_preserves_memory_update_cognition_writes` — architecture guard, new
   test in the integration file or a new `tests/integration/pipeline/` file. Construct a scenario
   where the *same* entity, in the *same* tick, has both a real `MemoryUpdatePhase` causal/spatial
   memory write staged AND an ESCORT quest reaching `is_newly_completed`; assert the post-`enforce()`
   `cognition_bundle_set` contains BOTH the memory write (non-empty/updated
   `cognition.memory.causal.entries`) AND the reputation change (`relationships.public_reputation
   .labels["reliable"]` increased) — the direct regression test for the merge-safety hazard.
4. `test_compiler_maps_escort_to_escort_quest_kind` — unit, extends
   `test_helper_enum_mappers` (`tests/unit/worldbuilding/test_world_compiler.py:552-563`) with one
   additional assertion line: `assert get_quest_kind("escort") == QuestKind.ESCORT`, matching the
   file's existing style for `"hunt"`/`"gather"`/`"explore"`. Do NOT add assertions for
   `"fetch"`/`"defend"`/`"investigate"` in this same test (scope guard, see Step 2).
5. `test_quest_kind_escort_enum_value_is_new_member_only` — architecture guard, in
   `tests/unit/quest/test_quest_system.py`. Assert `QuestKind.ESCORT` exists; assert
   `{k.name for k in QuestKind} == {"HUNT", "GATHER", "EXPLORE", "LIBERATE", "BOUNTY", "ESCORT"}`;
   assert `QuestState()`'s default `quest_kind` is still `QuestKind.HUNT` (unaffected default —
   confirm this default by reading `QuestState`'s dataclass definition before asserting it, do not
   assume).

**Other writers to these test files:** None known — no concurrent in-progress ticket touches
these same 4 test files (checked via `Related Tickets`/`Related Code Areas` in the ticket; only
this ticket's own `Related Code Areas` list overlaps).

**Do NOT touch:** `tests/unit/domains/commitment/test_phase15_reputation_update.py` (must keep
passing unmodified — this ticket does not change `ReputationUpdateService`'s internal delta
logic, only adds a caller); any Option-2/cooperation-domain test file (out of scope, decision
already resolved to Option 1).

**Verify:** Run the scoped pytest commands from test_plan.md:
```
pytest tests/unit/domains/commitment/ -v
pytest tests/integration/scenarios/test_phase15_commitment_reputation_scenarios.py -v
pytest tests/unit/quest/ -v
pytest tests/unit/worldbuilding/test_world_compiler.py -v
pytest tests/arena/test_arena_quests.py -v
pytest tests/unit/systems/test_quest_activation_pathway.py -v
```
All must pass, including the pre-existing 2 tests in `test_phase15_commitment_reputation_scenarios.py`
unmodified in behavior.

**Dependency:** Requires Steps 1-3 (tests exercise the actual enum/compiler/wiring code). Test 4
requires Step 2. Test 5 requires Step 1. Tests 1-3 require Step 3 (and transitively Step 1).

## Scope Guards

- Do NOT touch `clear_camp` event kind — no existing quest-kind or event constant matches it
  today; out of scope per the ticket's own Out of Scope section.
- Do NOT touch `ReputationService` (`src/systems/social_systems/reputation.py`) — separately
  orphaned, zero-caller, unrelated class; explicitly out of scope.
- Do NOT attempt to fix the systemic "compiled quests never get `target_*` progress-driving
  metadata" gap (`src/worldbuilding/compiler.py` never populates `target_archetype_id`/
  `target_faction_id`/`target_kind`/`target_pos`/`target_position`/`target_region_id` for any
  `QuestKind`) — confirmed pre-existing, affects all 5 (now 6, including ESCORT) `QuestKind`
  values equally, explicitly out of scope. This means a world-content-authored ESCORT quest will
  compile correctly (Step 2) but will not visibly progress to completion in a live simulation run
  until a future, separate ticket closes this gap — the wiring itself (Step 3) is still real and
  correct, and is directly testable via manually-constructed `QuestState` objects (Step 6, tests
  1-3), matching the parent investigation's accepted `BuildingSabotageSystem` precedent for
  "wired but not yet end-to-end reachable."
- Do NOT wire `CooperationLearningService`'s betrayal branch (Option 2) — not chosen. Do not add
  any call from `CooperationPhase` into `ReputationUpdateService`.
- Do NOT widen the `get_quest_kind()` compiler fix (Step 2) beyond the `"ESCORT"` branch — leave
  `"fetch"`/`"defend"`/`"investigate"` mishandling alone, including in tests (Step 6, test 4 must
  not assert on these 3 literals).
- Do NOT touch `docs/simulation/social_systems_contract.md`'s pre-existing drift (wrong label
  names/deltas in its Reputation section; stale `ESCORT ContractKind` reference in its Contracts
  section) — flagged by investigation.md as a separate future cleanup ticket, not this ticket's
  job.
- Do NOT touch `GroupState.escort_target_id` (`src/core/state.py:568`) or
  `AdventureRouteScorer`/`docs/mechanics/04_strategic_cognition.md` §6.9's route-scoring escort
  mechanism — a wholly unrelated "escort" concept; confirmed `escort_target_id` has zero write
  sites anywhere in the codebase, and this ticket must not become the first writer to it.
- Do NOT modify `EntityUpdate.merge()` (`src/core/updates.py:59-91`) or its `cognition_bundle_set`
  wholesale-replace semantics — this plan works within that existing contract via the
  base-cognition-read pattern, not by changing `.merge()` itself.
- Do NOT touch any other parity ledger file besides `docs/parity_ledger/social_narrative.yaml`,
  and within it, do not touch any entry other than the new `SOC-252` append.

## Dependency Map

- Step 1 (enum) — no dependencies. Must land before Steps 2, 3, and the parts of Step 6 that
  reference `QuestKind.ESCORT`.
- Step 2 (compiler fix) — depends on Step 1. Independent of Step 3.
- Step 3 (wiring) — depends on Step 1. Independent of Step 2 (Step 3's own tests construct
  `QuestState` directly, bypassing the compiler).
- Step 4 (parity entry) — text can be written any time, but its `test_path` is only truly
  "passing" once Step 6's test 1 exists and passes; treat Step 4 as logically after Step 6 for
  verification purposes even though the YAML edit itself has no code dependency.
- Step 5 (docs) — no hard code dependency, but should be done after Step 3 so the prose reflects
  the actually-implemented call site rather than a plan-stage description.
- Step 6 (tests) — depends on Step 1 (all), Step 2 (test 4 specifically), Step 3 (tests 1-3
  specifically).

Suggested implementation order: Step 1 → Step 2 → Step 3 → Step 6 → Step 4 → Step 5. (Steps 2 and
3 could be swapped since they're mutually independent given Step 1; Step 4/5 are documentation
and are safe to do last once behavior is final and tested.)

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| A planning decision is made and documented for which real event source `process_witnessed_event()` will attach to | Already resolved in investigation.md (Option 1 / QuestKind.ESCORT); this plan sequences it, does not re-decide it | N/A (decision-level AC, not a test) |
| `ReputationUpdateService.process_witnessed_event()` is called from that real, production event source — not a synthetic/unreachable trigger | Step 1 (enum), Step 2 (compiler mapping so real content can reach ESCORT), Step 3 (the actual call site in `QuestResolutionSystem.enforce()`) | `test_successful_escort_completion_updates_reputation`, `test_compiler_maps_escort_to_escort_quest_kind` (both Step 6) |
| The returned `PublicReputationProfile` is applied via `EntityUpdate.cognition_bundle_set` through the authoritative apply path | Step 3 | `test_successful_escort_completion_updates_reputation`, `test_quest_reward_phase_preserves_memory_update_cognition_writes` (both Step 6) |
| A parity ledger entry exists for this mechanism with a passing `test_path` | Step 4 | `SOC-252`'s `test_path` = `test_successful_escort_completion_updates_reputation` (Step 6); entry only considered done once this test passes |
| Regression tests in `tests/unit/domains/commitment/`, `tests/integration/scenarios/test_phase15_commitment_reputation_scenarios.py`, and quest-kind stability guards all pass | Step 6 (new tests co-located with regression suite; existing tests left untouched by Steps 1-5's scope guards) | Full scoped pytest commands listed in Step 6's Verify section |

## Anti-Drift Notes

- The merge-safety pattern in Step 3 is not optional polish — it is the single most-flagged hazard
  in investigation.md. Any implementation that reads `entity.cognition` unconditionally (instead
  of `ent_upd.cognition_bundle_set` first, falling back to `entity.cognition`) will silently
  discard `MemoryUpdatePhase`'s same-tick causal/spatial memory writes for that entity. Step 6's
  test 3 exists specifically to catch this regression and must not be skipped or weakened.
- Step 2's compiler fix is real and evidence-backed (6 world-content files currently silently
  miscompile), but it does not by itself make ESCORT quests completable in a live run — the
  systemic `target_*` metadata gap (Scope Guards, item 3) means this wiring is "real but not yet
  end-to-end reachable from static content," matching the accepted `BuildingSabotageSystem`
  precedent. Do not treat this plan as incomplete for not closing that separate gap — it is
  explicitly out of scope.
- `docs/simulation/domains/commitment_contract.md`'s existing prose (before Step 5's fix) already
  states the caller is responsible for "writing the updated profile back into the entity's
  cognition state" and to "verify at integration point whether the caller routes this through the
  authoritative pipeline or applies it as a direct replace" — Step 3 satisfies this by using
  `cognition_bundle_set`, the only typed authoritative path (no per-field
  `relationships_set`/`public_reputation_set` update type exists in `src/core/updates.py`).
- Do not confuse this ticket's `QuestKind.ESCORT` with the Mechanics Bible's §6.9 "Escort Route
  Scoring" (SOC-230, `docs/mechanics/04_strategic_cognition.md`) — two independent "escort"
  concepts that happen to share an English word. `SOC-252` (this ticket's new entry) is unrelated
  to `SOC-230`.
- The `AC` wording naming `tests/unit/engine/test_quests*.py` is aspirational/approximate per
  test_plan.md (no such file exists today) — the real regression surface is
  `tests/unit/quest/test_quest_system.py` and siblings, per test_plan.md's confirmed enumeration;
  Step 6 targets the real files, not the AC's literal (inexact) path.

## Unresolved Questions

None. The central open question (event-source choice) was resolved in investigation.md before
this planning phase began, per the orchestrator's explicit instruction not to re-litigate it. No
new unresolved question surfaced during fact-verification for this plan — every file, line,
field, and function cited above was directly read and confirmed to exist as described.

## Deviations

- **Step 3 variable naming**: this plan's prose describes threading a `cognition_touched: bool`
  flag alongside a `base_cognition` accumulator. The implementation instead uses a single
  `reputation_cognition_update: Optional[CognitionModel]` local, initialized to `None` before the
  `for qu in q_updates:` loop, whose None-ness *is* the "touched" flag (no separate boolean
  needed) — functionally identical to the plan's intent (merge-safe base-cognition read, ESCORT-only
  gate, compose across multiple same-tick completions, omit the `cognition_bundle_set` kwarg
  entirely when untouched so `replace()`'s default-preserve semantics apply). No behavior differs
  from what Step 3 specifies; only the local variable shape differs from the plan's exact prose.
- **Step 6 test-file distribution**: `test_quest_completion_non_escort_kind_does_not_touch_reputation`
  was placed in `tests/unit/quest/test_quest_rewards.py` (calls `QuestResolutionSystem.enforce()`
  directly with a manually constructed `StateUpdate`/`QuestUpdate`, matching that file's existing
  `enforce()`-adjacent fixtures) rather than requiring a new pipeline-level fixture, per the plan's
  own "implementer's call based on what fixtures are already available" allowance. Tests 1 and 3
  (escort completion + merge-safety) both landed in
  `tests/integration/scenarios/test_phase15_commitment_reputation_scenarios.py` as planned. Test 4
  (compiler mapping) extended `test_helper_enum_mappers` in `test_world_compiler.py` as planned.
  Test 5 (enum-stability guard) landed in `tests/unit/quest/test_quest_system.py` as planned.
