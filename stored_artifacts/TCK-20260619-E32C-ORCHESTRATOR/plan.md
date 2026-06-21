---
ticket_id: TCK-20260619-E32C-ORCHESTRATOR
date: 2026-06-21
phase: plan
status: complete
---

# Implementation Plan — TCK-20260619-E32C-ORCHESTRATOR

## Overview

CampaignOrchestrator drives multi-episode runs. It owns a `CampaignManifest`
(sequence of `SimulationScenarioDefinition` + seed + carry-forward rules),
runs each episode via `ScenarioRuntimeService`, extracts entity/faction
carry-forward data from the final `AuthoritativeState`, seeds the next
episode's kernel with that data, and accumulates `CampaignState` across
episodes.

Two small changes are required in `ScenarioRuntimeService` before the
orchestrator can be written. Everything else is net-new in the campaigns domain.

---

## Dependency Map

```
Step 1 (scenario_runtime.py changes)
    └─► Step 3 (CampaignOrchestrator — calls final_state + initial_state)

Step 2 (CampaignManifest + CarryForwardRules types)
    └─► Step 3 (CampaignOrchestrator imports CampaignManifest)

Step 3 (CampaignOrchestrator implementation)
    ├─► Step 4 (unit tests — mock svc; test orchestrator logic)
    ├─► Step 5 (integration tests — real kernel; test AC end-to-end)
    └─► Step 6 (architecture guard tests — import/isolation guards)
```

Steps 1 and 2 have no inter-dependency; they can be done in either order.
Steps 4, 5, 6 all depend on Step 3.

---

## Ordered Implementation Steps

---

### Step 1 — Extend `ScenarioRuntimeService` with `final_state` property and `initial_state` init parameter

**File:** `src/engine/scenario_runtime.py`

**What to change:**

1. Add `"_initial_state"` to `__slots__` (tuple at L118–126).

2. Update `__init__` signature to accept an optional initial state:
   ```python
   def __init__(
       self,
       spec: SimulationScenarioDefinition,
       initial_state: Optional["AuthoritativeState"] = None,
   ) -> None:
   ```
   Store it: `self._initial_state = initial_state`.

3. Update `_build_kernel()` (L293–313): if `self._initial_state is not None`,
   pass it to the Kernel instead of building a fresh `AuthoritativeState(tick=0, seed=0)`.
   Also update `DeterministicRNG` to use the same seed — both state and RNG must
   agree for determinism (INFRA-101/102):
   ```python
   if self._initial_state is not None:
       state = self._initial_state
       rng = DeterministicRNG(base_seed=self._initial_state.seed)
   else:
       state = AuthoritativeState(tick=0, seed=0)
       rng = DeterministicRNG(base_seed=0)
   ```
   This ensures that when an episode seed is injected via `initial_state`, the
   kernel's RNG also starts from that seed — otherwise all episodes would share
   the seed-0 RNG start state, breaking determinism.

4. Add `final_state` property after the `alive_entity_count` property (L225–233):
   ```python
   @property
   def final_state(self) -> Optional["AuthoritativeState"]:
       """Return the kernel's AuthoritativeState after a terminal episode.

       Returns None if the kernel has not been started yet (episode not begun).
       Available in all states including ABORTED — callers should check
       objective_state before relying on the contents.
       """
       if self._kernel is None:
           return None
       return self._kernel.state
   ```

**Scope guards:**
- Do NOT change `start()`, `pause()`, `resume()`, `step()`, `abort()` logic.
- Do NOT expose `self._kernel` directly — only `final_state` (the state).
- Do NOT change `_evaluate_after_tick()` or `_run_loop()`.
- The `TYPE_CHECKING` block at L24–26 already imports `AuthoritativeState` —
  no new import needed at module level; add `Optional` to runtime import only
  if not already present (it is: L22).

**Verifiable outcome:**
- `ScenarioRuntimeService(spec, initial_state=my_state)` stores the state.
- `svc.final_state` returns `None` before `start()` and the kernel's state after.
- Existing unit tests in `tests/unit/engine/test_scenario_runtime_service.py` still pass.

**Acceptance criteria satisfied:** (partial — unblocks Steps 3/5)

---

### Step 2 — Create `CampaignManifest` and `CarryForwardRules` types

**File:** `src/domains/campaigns/orchestrator.py` (new file — define types in the same
module as the orchestrator to keep the domain self-contained; no separate `manifest.py`
needed at this scope)

**What to add (at top of the new file, before the class):**

```python
@dataclass
class CarryForwardRules:
    """Boolean toggles controlling which entity/faction data carries between episodes.

    All fields default to True (full carry-forward). Set to False to disable a
    specific category — e.g., carry_equipment=False for a permadeath campaign.
    """
    carry_xp: bool = True
    carry_level: bool = True
    carry_equipment: bool = True
    carry_reputation: bool = True
    carry_injury: bool = True          # alive=False entities carried but not spawned
    carry_faction_state: bool = True   # faction tension and alive status carried


@dataclass(frozen=True)
class CampaignManifest:
    """Orchestration-layer campaign definition.

    Distinct from the analysis-domain CampaignSpec in src/domains/campaigns/schema.py.
    CampaignManifest owns: the ordered episode sequence, the base RNG seed, and
    the carry-forward rule set.

    episode seed derivation: episode N uses seed = base_seed + N (deterministic).
    """
    id: str
    episodes: List[SimulationScenarioDefinition]
    base_seed: int = 0
    carry_forward_rules: CarryForwardRules = field(default_factory=CarryForwardRules)
```

**Imports needed in `orchestrator.py`:**
```python
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from src.scenarios.schema import SimulationScenarioDefinition
    from src.core.state import AuthoritativeState

from src.domains.campaigns.state import (
    CampaignState,
    EntityCarryForward,
    EpisodeSummary,
    FactionCarryForward,
)
```

**Scope guards:**
- `CampaignManifest` must NOT be named `CampaignSpec` — `schema.py` already
  owns that name for the analysis domain.
- Do NOT add `episodes` or `carry_forward_rules` to the existing `CampaignSpec`
  in `schema.py`.
- `CarryForwardRules` is NOT frozen — it is a simple mutable config dataclass
  whose fields may be toggled in test setup. No `__slots__`.

**Verifiable outcome:**
- `from src.domains.campaigns.orchestrator import CampaignManifest, CarryForwardRules`
  succeeds.
- `CampaignManifest(id="x", episodes=[...])` constructs with defaults.
- `CarryForwardRules()` has all fields True.

**Acceptance criteria satisfied:** (partial — unblocks Step 3)

---

### Step 3 — Implement `CampaignOrchestrator` class

**File:** `src/domains/campaigns/orchestrator.py` (same file as Step 2 types)

**Class skeleton and method contract:**

```python
class CampaignOrchestrator:
    """Drives a sequence of episodes defined by a CampaignManifest.

    Owns one CampaignState across the full campaign lifetime.
    Each call to run_episode() runs episode N, extracts carry-forward data,
    updates CampaignState, and increments episode_index.
    """

    def __init__(self, manifest: CampaignManifest) -> None:
        self._manifest = manifest
        self._state = CampaignState(
            campaign_id=manifest.id,
            episode_index=0,
        )

    @property
    def state(self) -> CampaignState:
        """Current mutable CampaignState. Read-only property; do not replace."""
        return self._state

    def run_episode(self) -> EpisodeSummary:
        """Run the current episode and return its summary.

        Raises RuntimeError if episode_index >= len(episodes).
        """
        idx = self._state.episode_index
        if idx >= len(self._manifest.episodes):
            raise RuntimeError(
                f"No more episodes: campaign '{self._manifest.id}' has "
                f"{len(self._manifest.episodes)} episodes, "
                f"episode_index is {idx}."
            )
        spec = self._manifest.episodes[idx]
        episode_seed = self._manifest.base_seed + idx

        initial_state = self._build_initial_state(episode_seed)
        from src.engine.scenario_runtime import ScenarioRuntimeService
        svc = ScenarioRuntimeService(spec, initial_state=initial_state)
        svc.start()

        final = svc.final_state          # AuthoritativeState after terminal tick
        completed_tick = svc.tick

        summary = EpisodeSummary(
            episode_index=idx,
            completed_tick=completed_tick,
        )
        self._advance_state(final, summary)
        return summary

    def _advance_state(
        self,
        final_state: "AuthoritativeState",
        summary: EpisodeSummary,
    ) -> None:
        """Update CampaignState from completed episode's final kernel state."""
        rules = self._manifest.carry_forward_rules

        entity_cfs = self._extract_entity_carry_forwards(final_state)
        faction_cfs = self._extract_faction_carry_forwards(final_state)

        self._state.persistent_entities.update(entity_cfs)
        self._state.persistent_factions.update(faction_cfs)
        self._state.episode_history.append(summary)
        self._state.episode_index += 1

    def _extract_entity_carry_forwards(
        self,
        state: "AuthoritativeState",
    ) -> Dict[int, EntityCarryForward]:
        """Extract EntityCarryForward for every entity in the final state.

        Uses entity.lifecycle.active (NOT entity.combat.alive) for alive field.
        Equipment EquipSlot enum keys are stringified to match the declared
        EntityCarryForward.equipment format {"slots": {...}, "durability": {...}}.
        """
        rules = self._manifest.carry_forward_rules
        result: Dict[int, EntityCarryForward] = {}
        for entity_id, entity in state.entities.items():
            slots = {
                str(slot): item_id
                for slot, item_id in entity.equipment.slots.items()
            } if rules.carry_equipment else {}
            durability = {
                str(slot): dur
                for slot, dur in entity.equipment.durability.items()
            } if rules.carry_equipment else {}
            result[entity_id] = EntityCarryForward(
                entity_id=entity_id,
                level=entity.identity.evolution_level if rules.carry_level else 1,
                xp=entity.identity.evolution_points if rules.carry_xp else 0,
                equipment={"slots": slots, "durability": durability},
                reputation=entity.social.public_reputation if rules.carry_reputation else 0.0,
                alive=entity.lifecycle.active,
            )
        return result

    def _extract_faction_carry_forwards(
        self,
        state: "AuthoritativeState",
    ) -> Dict[str, FactionCarryForward]:
        """Synthesize FactionCarryForward by grouping entities by faction int.

        Faction alive = at least one entity with that faction int has lifecycle.active=True.
        Faction ID string: f"faction_{faction_int}".
        Tension defaults to 0.0 (E32D will enrich this from world pressure data).
        """
        if not self._manifest.carry_forward_rules.carry_faction_state:
            return {}
        faction_alive: Dict[int, bool] = {}
        for entity in state.entities.values():
            fac_int = entity.identity.faction
            if fac_int not in faction_alive:
                faction_alive[fac_int] = False
            if entity.lifecycle.active:
                faction_alive[fac_int] = True
        return {
            f"faction_{fac_int}": FactionCarryForward(
                faction_id=f"faction_{fac_int}",
                alive=alive,
                tension=0.0,
            )
            for fac_int, alive in faction_alive.items()
        }

    def _build_initial_state(self, episode_seed: int) -> "AuthoritativeState":
        """Construct an AuthoritativeState seeded with carry-forward entity data.

        For episode 0 (no prior persistent_entities): returns a fresh
        AuthoritativeState(tick=0, seed=episode_seed).
        For episode N>0: reconstructs EntityState objects from EntityCarryForward
        snapshots and injects them into the new state.

        Only alive entities (lifecycle.active=True) are spawned in the new episode.
        Dead entities remain in persistent_entities for history but are not injected.
        """
        from src.core.state import AuthoritativeState, EntityState

        alive_carry_forwards = {
            eid: cf
            for eid, cf in self._state.persistent_entities.items()
            if cf.alive
        }

        if not alive_carry_forwards:
            # Episode 0 or no surviving entities — start fresh
            return AuthoritativeState(tick=0, seed=episode_seed)

        # Reconstruct minimal EntityState objects from carry-forward snapshots.
        # Fields not captured in EntityCarryForward (e.g. combat state, current
        # HP) are left at EntityState defaults — the scenario's setup_tags and
        # world_composition govern spawn placement.
        entities: Dict[int, EntityState] = {}
        for eid, cf in alive_carry_forwards.items():
            base = EntityState(entity_id=eid)
            # Apply carried fields via replace (EntityState components are frozen)
            # Identity
            identity = base.identity.replace(
                evolution_level=cf.level,
                evolution_points=cf.xp,
            )
            # Equipment
            from src.core.state import EquipmentComponent, EquipSlot
            slots_enum = {
                EquipSlot[k]: v
                for k, v in cf.equipment.get("slots", {}).items()
            }
            durability_enum = {
                EquipSlot[k]: v
                for k, v in cf.equipment.get("durability", {}).items()
            }
            equipment = base.equipment.replace(
                slots=slots_enum,
                durability=durability_enum,
            )
            # Social
            social = base.social.replace(public_reputation=cf.reputation)
            entities[eid] = base.replace(
                identity=identity,
                equipment=equipment,
                social=social,
            )

        return AuthoritativeState(tick=0, seed=episode_seed, entities=entities)

    def _get_spawn_entities(self) -> Dict[int, EntityCarryForward]:
        """Return only alive entities from persistent state (for episode spawn)."""
        return {
            eid: cf
            for eid, cf in self._state.persistent_entities.items()
            if cf.alive
        }

    def _get_spawn_factions(self) -> Dict[str, FactionCarryForward]:
        """Return only alive factions from persistent state (for episode spawn)."""
        return {
            fid: cf
            for fid, cf in self._state.persistent_factions.items()
            if cf.alive
        }
```

**Scope guards:**
- Do NOT import `ScenarioRuntimeService` at module level — import inside
  `run_episode()` to keep the module importable without triggering engine
  construction (avoids circular import and test overhead).
- Do NOT add engine imports to `src/domains/campaigns/state.py`.
- Do NOT mutate `AuthoritativeState` objects directly — they are frozen;
  use `replace()` (dataclass `replace` from `dataclasses` module).
- The `_build_initial_state` method must use `.replace()` pattern for frozen
  component dataclasses. If `EntityState.replace()` is not a native method,
  use `dataclasses.replace(base, identity=identity, ...)`.
- Do NOT implement `world_timeline` population in this step — that is E32D scope.
- The `tension=0.0` default in `_extract_faction_carry_forwards` is intentional
  — a comment noting "E32D will enrich" is sufficient.

**Verifiable outcome:**
- `CampaignOrchestrator(manifest)` constructs; `state.campaign_id` and
  `state.episode_index == 0`.
- `run_episode()` increments `episode_index`, appends to `episode_history`.
- `run_episode()` raises `RuntimeError` when `episode_index >= len(episodes)`.

**Acceptance criteria satisfied:** (primary implementation — unblocks Steps 4/5/6)

---

### Step 4 — Unit tests (mocked kernel, orchestrator logic)

**File:** `tests/unit/campaigns/test_campaign_orchestrator.py` (new file)

**Test cases:** TC-4 through TC-13 as specified in `test_plan.md`.

**Fixture pattern:**

```python
# Minimal manifest fixture
def make_manifest(n_episodes=3):
    from unittest.mock import MagicMock
    from src.scenarios.schema import SimulationScenarioDefinition
    episodes = [MagicMock(spec=SimulationScenarioDefinition) for _ in range(n_episodes)]
    return CampaignManifest(id="test_campaign", episodes=episodes, base_seed=0)

# Mock ScenarioRuntimeService
def make_mock_svc(objective_state, tick=50, final_state=None):
    svc = MagicMock()
    svc.objective_state = objective_state
    svc.tick = tick
    svc.final_state = final_state or MagicMock()
    return svc
```

**For TC-5 and TC-11/TC-12 (entity extraction):**
Build a mock `AuthoritativeState` with controlled `entities` dict containing
`MagicMock` EntityState objects where `identity.evolution_level`, `identity.evolution_points`,
`lifecycle.active`, `social.public_reputation`, `equipment.slots`, and
`equipment.durability` are set explicitly. Use `EquipSlot.MAIN_HAND` (or similar)
as the enum key; assert the extracted dict uses `"MAIN_HAND"` (string) as key.

**For TC-7 (run_episode appends history):**
Patch `ScenarioRuntimeService` at `src.domains.campaigns.orchestrator.ScenarioRuntimeService`
(since it is imported inside `run_episode()`), or inject via a subclass hook.
Alternatively, pass a pre-built `svc` by monkeypatching the import. Use
`unittest.mock.patch("src.engine.scenario_runtime.ScenarioRuntimeService")` or
inject by making `_make_svc()` a protected factory method on the orchestrator.

**Preferred injection pattern (avoids deep patching):**
Add an optional `_svc_factory` parameter or override `_make_svc()` in a test
subclass. Or: patch the constructor call inside `run_episode()`.

Implementation note: if patching is awkward due to the deferred import, refactor
`run_episode()` to accept an optional `_svc_override` parameter (default `None`)
for test injection — this is a narrow, documented test seam and avoids deep
mock.patch gymnastics.

**All TC-4 through TC-13 must pass before Step 5 begins.**

**Scope guards:**
- No real Kernel ticks in unit tests.
- Do NOT use `pytest.mark.slow` on any test in this file.
- Fixtures must be self-contained — no world config files.

**Acceptance criteria satisfied:** TC-4/TC-5/TC-6/TC-7/TC-8/TC-9/TC-10/TC-11/TC-12/TC-13

---

### Step 5 — Integration tests (real kernel, acceptance criteria)

**File:** `tests/integration/scenarios/test_campaign_runtime.py` (new file)

**Test cases:** TC-1, TC-2, TC-3 from `test_plan.md`.

**Fixture approach:**
Reuse the pattern from `tests/integration/scenarios/test_scenario_runtime_service.py`
for minimal world config. Each episode needs a `SimulationScenarioDefinition` with:
- A small `tick_limit` victory condition (e.g., `tick_limit: 10`) to keep tests fast.
- At least 1 entity with a non-zero faction int for TC-2.
- For TC-1: the entity must have `evolution_level >= 1` before episode 1 ends.

**TC-1 implementation note:**
After `run_episode()` twice, read `orchestrator.state.persistent_entities[entity_id]`
and assert `.level == entity.identity.evolution_level` from the episode-1 final state.
For the level assertion to be non-trivial, the test scenario must ensure the entity
actually has `evolution_level > 0` (set via `initial_conditions` or a setup action
in the scenario definition). If the real kernel does not advance levels in 10 ticks,
pre-seed the entity at level 5 via `initial_state` and verify it is preserved, rather
than requiring the kernel to level-up during the test.

**TC-2 implementation note:**
Build an `initial_state` for episode 0 that contains an entity with `faction=2`
and `lifecycle.active=False` from tick 0 (or advance the scenario until it dies).
After episode 0 completes, `persistent_factions["faction_2"].alive` must be `False`.
After `run_episode()` for episode 1, assert no entity with `faction=2` in the
new episode's kernel. Access via `svc.final_state` or check
`orchestrator.state.persistent_factions["faction_2"].alive is False` without
running episode 1 (sufficient for the AC).

All three tests carry `@pytest.mark.slow` and run with real kernel ticks.

**Scope guards:**
- Use minimal world config — no full world assembly.
- Tests must complete in < 30 s each.
- Do NOT assert on internal kernel state beyond `final_state`.

**Acceptance criteria satisfied:** TC-1 (entity level persists), TC-2 (dead faction absent), TC-3 (episode_history length)

---

### Step 6 — Architecture guard tests

**File:** `tests/unit/campaigns/test_campaign_orchestrator.py` (append to Step 4 file)

**TC-14: No engine imports via state.py**

```python
def test_state_module_has_no_engine_imports():
    """Re-verify Guard-4: state.py must not import from src.engine or src.core.state."""
    import ast, pathlib
    src = pathlib.Path("src/domains/campaigns/state.py").read_text()
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            mod = getattr(node, "module", "") or ""
            names = [alias.name for alias in getattr(node, "names", [])]
            assert not mod.startswith("src.engine"), (
                f"state.py must not import from src.engine: {mod}"
            )
            assert not mod.startswith("src.core.state"), (
                f"state.py must not import from src.core.state: {mod}"
            )
```

**TC-15: CampaignState and CampaignOrchestrator co-importable**

```python
def test_campaign_state_importable_alongside_orchestrator():
    """state.py and orchestrator.py must co-exist without ImportError."""
    from src.domains.campaigns.state import CampaignState
    from src.domains.campaigns.orchestrator import CampaignOrchestrator
    # Both imports succeeded
    assert CampaignState is not None
    assert CampaignOrchestrator is not None
```

**Scope guards:**
- AST guard (TC-14) must not import the module under test — AST parsing only.
- These tests must NOT have `@pytest.mark.slow`.

**Acceptance criteria satisfied:** No cross-contamination of domains; `CampaignManifest`/`CampaignSpec` naming collision absent.

---

## Files Changed (per step)

| Step | File | Change type |
|---|---|---|
| 1 | `src/engine/scenario_runtime.py` | Modify — add `_initial_state` slot, update `__init__`, update `_build_kernel`, add `final_state` property |
| 2 | `src/domains/campaigns/orchestrator.py` | Create — `CarryForwardRules`, `CampaignManifest` |
| 3 | `src/domains/campaigns/orchestrator.py` | Extend — `CampaignOrchestrator` class |
| 4 | `tests/unit/campaigns/test_campaign_orchestrator.py` | Create — TC-4 through TC-13 |
| 5 | `tests/integration/scenarios/test_campaign_runtime.py` | Create — TC-1, TC-2, TC-3 |
| 6 | `tests/unit/campaigns/test_campaign_orchestrator.py` | Extend — TC-14, TC-15 |

**No other files should be modified.** In particular:
- `src/domains/campaigns/schema.py` — do NOT modify.
- `src/domains/campaigns/state.py` — do NOT modify.
- `src/domains/campaigns/spec.py` — do NOT modify.
- `src/scenarios/schema.py` — do NOT modify.
- `docs/simulation/domains/campaigns_contract.md` — update in the Finalize phase
  (after implementation is complete), not during implementation.

---

## Acceptance Criteria → Step Mapping

| Acceptance Criterion | Steps | Test case |
|---|---|---|
| HERO at level 5 in ep1 → starts ep2 at level 5 | 3, 5 | TC-1 |
| Faction destroyed in ep1 not spawned in ep2 | 3, 5 | TC-2 |
| `episode_history` has 2 entries after 2 episodes | 3, 4, 5 | TC-3, TC-7 |
| `_extract_entity_carry_forwards` uses `lifecycle.active` | 3, 4 | TC-12 |
| Equipment keys are strings (not EquipSlot enum) | 3, 4 | TC-11 |
| `FactionCarryForward.alive` = ≥1 active entity | 3, 4 | TC-6 |
| Faction ID format is `f"faction_{faction_int}"` | 3, 4 | TC-6 |
| `run_episode()` raises when no episodes remain | 3, 4 | TC-8 |
| `CampaignState` importable alongside `CampaignOrchestrator` | 6 | TC-15 |
| `state.py` has no engine imports after E32C | 6 | TC-14 |
| Episode seed = `base_seed + episode_index` (determinism) | 3 | (verified in Step 3 code; no isolated test needed) |

---

## Parity Ledger Update (Finalize phase)

Add **INFRA-218** to `docs/parity_ledger/infrastructure.yaml`:

```yaml
- id: INFRA-218
  text: >
    CampaignOrchestrator drives multi-episode runs via ScenarioRuntimeService.
    EntityCarryForward extracted from entity.lifecycle.active (not combat.alive),
    entity.identity.evolution_level/points, entity.social.public_reputation, and
    entity.equipment.slots/durability (EquipSlot keys stringified).
    FactionCarryForward synthesized: alive = any active entity with that faction int.
    Dead entities and destroyed factions excluded from next episode spawn.
    episode_history accumulated after each run_episode() call.
    Episode RNG seed = CampaignManifest.base_seed + episode_index.
  status: verified
  priority: P1
  v2_evidence: tests/integration/scenarios/test_campaign_runtime.py
  test_path: pytest tests/integration/scenarios/test_campaign_runtime.py -x -v -m slow
  divergence_note: ""
```

Also update **INFRA-214** `v2_evidence` to note that `final_state` and
`initial_state` were added to `ScenarioRuntimeService` in E32C.

---

## Open Questions Resolved (no unresolved questions)

All OQs from the investigation are resolved:

| OQ | Resolution |
|---|---|
| OQ-1 | Option A: `initial_state` parameter on `ScenarioRuntimeService.__init__` |
| OQ-2 | `final_state: Optional[AuthoritativeState]` property on `ScenarioRuntimeService` |
| OQ-3 | `f"faction_{faction_int}"` string format |
| OQ-4 | `base_seed + episode_index` per-episode seed in `CampaignManifest` |
| OQ-5 | New type named `CampaignManifest` (avoids collision with `CampaignSpec`) |
| OQ-6 | `CarryForwardRules` dataclass with boolean fields, all default `True` |

---

## Deviations

_None yet. Update this section if implementation diverges from plan._

---

## Scoped Test Commands (reference)

```bash
# Step 1 regression check
pytest tests/unit/engine/test_scenario_runtime_service.py -x -v

# Steps 4 + 6 (unit tests, fast)
pytest tests/unit/campaigns/test_campaign_orchestrator.py -x -v
pytest tests/unit/campaigns/ -x -v

# Step 5 (integration, slow)
pytest tests/integration/scenarios/test_campaign_runtime.py -x -v -m slow

# Full scope before finalization
pytest tests/unit/campaigns/ tests/unit/engine/test_scenario_runtime_service.py \
      tests/integration/scenarios/ -x -v -m "not slow"
pytest tests/integration/scenarios/test_campaign_runtime.py -x -v -m slow
```
