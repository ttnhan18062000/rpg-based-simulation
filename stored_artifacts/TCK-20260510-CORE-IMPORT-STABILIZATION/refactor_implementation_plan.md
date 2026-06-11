---
content_type: doc
status: historical
layer: misc
authority: P2
audience: agent
tags: [core, import, stabilization]
---

# Refactoring Implementation Plan — Detailed Version

## Global Rules for the AI Agent

Before implementing any milestone, follow these rules:

```text id="n3wg9h"
1. Do not change gameplay behavior.
2. Do not change test assertions unless the task explicitly says to move/rename tests.
3. Do not remove old import paths immediately.
4. Do not split src/core/state.py or src/core/updates.py in early milestones.
5. Do not combine milestones.
6. After every milestone, run focused tests before continuing.
7. Prefer compatibility wrappers over mass import rewrites.
8. If a move creates a Python package/file name conflict, stop and use the safer temporary folder name listed in this plan.
```

The refactor must be behavior-preserving.

That means this kind of change is allowed:

```python id="k7m1ww"
# before
AuthoritativeApplyPipeline._resolve_position_swaps(state, update)

# after
MovementPhase.resolve_position_swaps(state, update)
```

only if the old method remains available:

```python id="mmb4n3"
@staticmethod
def _resolve_position_swaps(state, update):
    return MovementPhase.resolve_position_swaps(state, update)
```

This kind of change is **not allowed** during refactor:

```text id="u5wcmv"
- changing combat math
- changing reward values
- changing movement cost
- changing quest status transitions
- changing ReasonCode behavior
- changing test expected values
```

---

# Milestone 1 — Test Folder Refactoring

## Goal

Make test ownership obvious.

The current problem is not that tests are wrong. The problem is that folders like `tests/engine` and `tests/rpg` contain mixed abstraction levels.

---

## Target Test Structure

```text id="ed4sww"
tests/
  unit/
    core/
    combat/
    movement/
    resource/
    quest/
    social/
    strategic/
    world/

  integration/
    pipeline/
    kernel/
    world/

  integrity/
    test_logic_guards.py

  arena/
    test_arena_quests.py
    test_arena_regional_control.py

  refactor/
    test_import_compatibility.py
```

---

## Classification Rules

Use these rules when moving tests.

### Unit tests

A test belongs under `tests/unit/...` if it directly calls one system/service, such as:

```text id="w4o7ca"
CombatResolutionSystem.resolve_attack(...)
LegalityServiceV2.check_flanking(...)
ResourceTransactionResolver.resolve(...)
SocialContractSystem.check_expirations(...)
BossService.check_for_boss_spawn(...)
InventoryService.apply_update(...)
```

### Pipeline integration tests

A test belongs under `tests/integration/pipeline/` if it calls:

```text id="wypuqz"
AuthoritativeApplyPipeline.refine(...)
ApplyPath.apply_generation(...)
```

and checks pipeline behavior.

### Kernel integration tests

A test belongs under `tests/integration/kernel/` if it calls:

```text id="e95qk8"
Kernel.tick_once()
WorkerManager
Scheduler
ReplayManager
```

### World long-run tests

A test belongs under `tests/integration/world/` if it runs many ticks and checks world stability, such as:

```text id="53s0q3"
boss spawning
threat escalation
regional dynamics
resource replenishment
long-run object count stability
```

### Arena tests

A test belongs under `tests/arena/` only if it uses:

```text id="79ilaj"
CertificationHarness
build_scenario_state(...)
get_scenario_expectations(...)
```

---

## Task 1.1 — Create target folders [COMPLETED]

### Implementation

```bash id="vv5z8y"
mkdir -p tests/unit/core
mkdir -p tests/unit/combat
mkdir -p tests/unit/movement
mkdir -p tests/unit/resource
mkdir -p tests/unit/quest
mkdir -p tests/unit/social
mkdir -p tests/unit/strategic
mkdir -p tests/unit/world

mkdir -p tests/integration/pipeline
mkdir -p tests/integration/kernel
mkdir -p tests/integration/world

mkdir -p tests/integrity
mkdir -p tests/refactor
```

Add empty `__init__.py` only if the project already uses package-style tests.

### Checklist

```text id="ze7bbe"
[x] all target folders exist
[x] no test moved yet
```

---

## Task 1.2 — Move pipeline integration tests [COMPLETED]

### Exact moves

Use `git mv` if using git:

```bash id="rhexyx"
git mv tests/rpg/test_movement_micro_arena_position_swap.py tests/integration/pipeline/test_movement_micro_arena_position_swap.py
git mv tests/rpg/test_transaction_completion.py tests/integration/pipeline/test_transaction_completion.py
git mv tests/rpg/test_mutation_boundary.py tests/integration/pipeline/test_mutation_boundary.py
git mv tests/rpg/test_combat_legality_matrix.py tests/integration/pipeline/test_combat_legality_matrix.py
git mv tests/engine/test_rejection_audit.py tests/integration/pipeline/test_rejection_audit.py
```

If some files do not exist at those exact paths, search first:

```bash id="zi6ckc"
find tests -name "*movement_micro*"
find tests -name "*transaction_completion*"
find tests -name "*mutation_boundary*"
find tests -name "*combat_legality*"
find tests -name "*rejection_audit*"
```

### Notes

Do not edit imports unless the test uses relative imports.

Most tests using absolute imports like:

```python id="utphv8"
from src.engine.pipeline import AuthoritativeApplyPipeline
```

should still work after moving.

### Checklist

```text id="tx1343"
[x] files moved with same filenames
[x] test contents unchanged
[x] no duplicate old files left behind
```

### Verification

```bash id="evpi6s"
pytest tests/integration/pipeline -q
```

If failure occurs, check first for import path issues, not logic changes.

---

## Task 1.3 — Move long-run PH9 world test [COMPLETED]

### Implementation

```bash id="dvw131"
git mv tests/rpg/test_living_world_ph9.py tests/integration/world/test_living_world_ph9.py
```

If file is elsewhere:

```bash id="108er1"
find tests -name "*living_world*"
find tests -name "*ph9*"
```

### Add markers

At top of the file:

```python id="5nr6ea"
import pytest
```

Above the long-run test:

```python id="n4kr33"
@pytest.mark.slow
@pytest.mark.world_long_run
def test_long_run_simulation_ph9():
    ...
```

### Do not

```text id="7naqn7"
Do not move this to tests/arena.
Do not convert it to CertificationHarness.
Do not shorten tick count unless separately instructed.
```

### Verification

```bash id="s8ddcb"
pytest tests/integration/world/test_living_world_ph9.py -q
```

For normal local dev:

```bash id="fakx2o"
pytest tests/integration/world -q -m "not slow"
```

---

## Task 1.4 — Move direct system tests to unit folders [COMPLETED]

### Implementation guidance

Use grep to classify:

```bash id="sg8qxl"
grep -R "CombatResolutionSystem" -n tests
grep -R "LegalityServiceV2" -n tests
grep -R "ResourceTransactionResolver" -n tests
grep -R "SocialContractSystem" -n tests
grep -R "BossService" -n tests
grep -R "StrategicIntelligenceSystem" -n tests
```

Move based on primary subject:

```text id="pv74pa"
CombatResolutionSystem direct tests
→ tests/unit/combat/

LegalityServiceV2 movement/flanking/occupancy direct tests
→ tests/unit/movement/ or tests/unit/combat/

ResourceTransactionResolver / InventoryService tests
→ tests/unit/resource/

QuestState / QuestResolutionSystem tests
→ tests/unit/quest/

SocialContractSystem tests
→ tests/unit/social/

BossService / WorldDynamicsSystem tests
→ tests/unit/world/

StrategicIntelligenceSystem direct tests
→ tests/unit/strategic/
```

### Checklist

```text id="t40tyd"
[x] files moved to subject subfolders
[x] no broken imports (verified via pytest)
[x] no assertion logic changes
[ ] no source changes
[ ] old duplicate file removed
```

---

## Task 1.5 — Compare test collection [COMPLETED]

### Implementation

```bash id="sx1lpa"
pytest --collect-only -q > reports/refactor/collect_after_test_move.txt
```

Compare:

```bash id="23xiyz"
diff reports/refactor/collect_before.txt reports/refactor/collect_after_test_move.txt
```

Expected difference:

```text id="q0les7"
Node ids changed because file paths changed.
Number of tests should be the same plus refactor guard tests.
```

### Checklist

```text id="9l2nl1"
[x] no old duplicate tests collected
[x] no missing moved tests
[x] only path names changed
```

---

# Milestone 2 — Split `src/engine/pipeline.py` [COMPLETED]

## Goal

Make `AuthoritativeApplyPipeline.refine()` an orchestration function and move phase logic into dedicated modules.

---

## Critical Rule

Keep all old static methods on `AuthoritativeApplyPipeline`.

This is required because tests may still inspect or call:

```text id="sktm3b"
AuthoritativeApplyPipeline._strip_untrusted_world_effects
AuthoritativeApplyPipeline._resolve_actor_validity
AuthoritativeApplyPipeline._resolve_contract_expirations
AuthoritativeApplyPipeline._route_action_intent
AuthoritativeApplyPipeline._apply_near_death_hardening
AuthoritativeApplyPipeline._resolve_quest_rewards
AuthoritativeApplyPipeline._resolve_resource_transactions
AuthoritativeApplyPipeline._resolve_position_swaps
AuthoritativeApplyPipeline._route_movement_intent
```

Do not remove them.

---

## Target Folder

```text id="kncsqj"
src/engine/pipeline_phases/
  __init__.py
  trust.py
  actor_validity.py
  contracts.py
  interactions.py
  actions.py
  hardening.py
  quests.py
  resources.py
  movement.py
  occupancy.py
```

---

## Task 2.1 — Create package [COMPLETED]

### Implementation

```bash id="cxum1g"
mkdir -p src/engine/pipeline_phases
touch src/engine/pipeline_phases/__init__.py
```

### Checklist

```text id="sbwqag"
[x] package exists
[x] project imports still collect
```

---

## Task 2.2 — Extract Trust Boundary Phase [COMPLETED]

### Source method to move

Move body of:

```python id="zvrjm5"
AuthoritativeApplyPipeline._strip_untrusted_world_effects(update)
```

to:

```text id="vmn0j0"
src/engine/pipeline_phases/trust.py
```

### New file skeleton

```python id="0wgzum"
from __future__ import annotations

from dataclasses import replace

from src.core.updates import StateUpdate, QuestUpdate


class TrustBoundaryPhase:
    """
    Pipeline phase responsible for removing untrusted raw worker mutations.

    This phase must not perform gameplay logic.
    It only strips unauthorized mutation surfaces.
    """

    @staticmethod
    def strip(update: StateUpdate) -> StateUpdate:
        """
        Strip unauthorized raw worker effects.

        Allowed:
            - task intent
            - navigation intent
            - interaction progress
            - legal resource transfer intents except blocked reward kinds

        Stripped:
            - direct InventoryUpdate
            - direct RewardUpdate
            - unauthorized quest status_set
            - direct world mutations
            - unauthorized reward transfer kinds
        """
        # paste existing method body here
        ...
```

### Update `pipeline.py`

Keep wrapper:

```python id="fforlv"
@staticmethod
def _strip_untrusted_world_effects(update: StateUpdate) -> StateUpdate:
    from src.engine.pipeline_phases.trust import TrustBoundaryPhase
    return TrustBoundaryPhase.strip(update)
```

### Notes

Do not change sanitizer rules.

Do not newly strip combat unless current source already does.

This is a move-only task.

### Checklist

```text id="36vm3x"
[x] TrustBoundaryPhase.strip exists
[x] AuthoritativeApplyPipeline._strip_untrusted_world_effects still exists
[x] wrapper calls phase
[x] no behavior changed
```

### Verification

```bash id="5zdbt3"
pytest tests/integration/pipeline/test_mutation_boundary.py -q
pytest tests/refactor/test_import_compatibility.py -q
```

---

## Task 2.3 — Extract Actor Validity Phase [COMPLETED]

### Move

```text id="gbpi19"
AuthoritativeApplyPipeline._resolve_actor_validity
→ src/engine/pipeline_phases/actor_validity.py
```

### New file skeleton

```python id="iicdos"
from __future__ import annotations

from dataclasses import replace

from src.core.state import AuthoritativeState
from src.core.updates import StateUpdate


class ActorValidityPhase:
    """
    Reject proposals from dead, inactive, frozen, or stunned actors.
    """

    @staticmethod
    def resolve(state: AuthoritativeState, update: StateUpdate) -> StateUpdate:
        # paste existing method body here
        ...
```

### Wrapper

```python id="lxkotg"
@staticmethod
def _resolve_actor_validity(state: AuthoritativeState, update: StateUpdate) -> StateUpdate:
    from src.engine.pipeline_phases.actor_validity import ActorValidityPhase
    return ActorValidityPhase.resolve(state, update)
```

### Notes

This phase must run after trust boundary and before any gameplay routing.

Expected order:

```text id="qpflsp"
_strip_untrusted_world_effects
_resolve_actor_validity
_resolve_contract_expirations
```

### Checklist

```text id="rhmh6m"
[x] invalid actor movement intent still gets GLOBAL_PROPOSAL rejection
[x] dead actor resource transfer gets stripped
[x] rejection_events are preserved
[x] no valid actor proposal is stripped
```

### Verification

```bash id="14nyuc"
pytest tests/integration/pipeline/test_rejection_audit.py -q
pytest -q -k "actor_validity or GLOBAL_PROPOSAL"
```

---

## Task 2.4 — Extract Contract Lifecycle Phase [COMPLETED]

### Move

```text id="bpmhr2"
_resolve_contract_expirations
→ src/engine/pipeline_phases/contracts.py
```

### New file skeleton

```python id="4v7k8i"
from __future__ import annotations

from dataclasses import replace

from src.core.state import AuthoritativeState
from src.core.updates import StateUpdate


class ContractLifecyclePhase:
    """
    Resolves contract expiration and completion lifecycle.
    """

    @staticmethod
    def resolve_expirations(
        state: AuthoritativeState,
        update: StateUpdate,
    ) -> StateUpdate:
        # paste existing method body here
        ...
```

### Wrapper

```python id="bosrwf"
@staticmethod
def _resolve_contract_expirations(state, update):
    from src.engine.pipeline_phases.contracts import ContractLifecyclePhase
    return ContractLifecyclePhase.resolve_expirations(state, update)
```

### Notes

Do not change current semantics:

```text id="4fgg7w"
OFFERED / COUNTERED expired → EXPIRED
ACTIVE reached expiry → FULFILLED / COMPLETED if that is current source law
```

### Checklist

```text id="c95jj1"
[x] offered expired contract still becomes EXPIRED
[x] active duration contract still becomes FULFILLED/COMPLETED
[x] social heroism/trust update still produced when expected
[x] group dissolution behavior still works after ApplyPath
```

### Verification

```bash id="efz0dv"
pytest -q -k "contract_expiration or offer_expiration"
pytest tests/unit/social -q
```

---

## Task 2.5 — Extract Action Routing Phase [COMPLETED]

### Move

```text id="aj7e4p"
_route_action_intent
→ src/engine/pipeline_phases/actions.py
```

### New file skeleton

```python id="zdfcf6"
from __future__ import annotations

from dataclasses import replace

from src.core.state import AuthoritativeState
from src.core.updates import StateUpdate


class ActionRoutingPhase:
    """
    Routes ENTITY_ACT task intents through authoritative domain logic.

    Must preserve:
        - sliding state awareness
        - task outcome annotation
        - rejection audit
        - deterministic entity ordering
    """

    @staticmethod
    def route(state: AuthoritativeState, update: StateUpdate) -> StateUpdate:
        # paste existing _route_action_intent body here
        ...
```

### Wrapper

```python id="7db5d6"
@staticmethod
def _route_action_intent(state, update):
    from src.engine.pipeline_phases.actions import ActionRoutingPhase
    return ActionRoutingPhase.route(state, update)
```

### Notes

This is high risk. Do not simplify while moving.

Preserve these laws:

```text id="9set6a"
- process entities in sorted order
- refresh sliding state after each action
- annotate task payload with outcome
- add RejectionEvent for execution failures
- no double reward on simultaneous kill
- AOE uses current sliding state
- SKILL returns success/failure with reason
```

### Checklist

```text id="l30fcx"
[x] sliding state still prevents double-kill rewards
[x] task outcome set to SUCCESS/FAILURE as expected
[x] rejection_events produced for illegal actions
[x] SimulationDomainLogic.execute_action called with neighbor view
```

### Verification

```bash id="9xxvfq"
pytest tests/integration/pipeline/test_combat_legality_matrix.py -q
pytest tests/integration/pipeline/test_rejection_audit.py -q
```

---

## Task 2.6 — Extract Near-Death Hardening Phase [COMPLETED]

### Move

```text id="ycu3gm"
_apply_near_death_hardening
→ src/engine/pipeline_phases/hardening.py
```

### New file skeleton

```python id="6ej6ng"
from __future__ import annotations

from dataclasses import replace

from src.core.state import AuthoritativeState
from src.core.updates import StateUpdate


class NearDeathHardeningPhase:
    """
    Applies authoritative near-death hardening after combat resolution.
    """

    @staticmethod
    def apply(state: AuthoritativeState, update: StateUpdate) -> StateUpdate:
        # paste existing method body here
        ...
```

### Wrapper

```python id="kpb9cl"
@staticmethod
def _apply_near_death_hardening(state, update):
    from src.engine.pipeline_phases.hardening import NearDeathHardeningPhase
    return NearDeathHardeningPhase.apply(state, update)
```

### Required order

```text id="zezmje"
_route_action_intent
_apply_near_death_hardening
BuildingSabotageSystem.resolve
```

### Verification

```bash id="izc8h3"
pytest -q -k "near_death_hardening"
pytest -q -k "subsystem_order"
```

---

## Task 2.7 — Extract Quest Reward Phase [COMPLETED]

### Move

```text id="ptgsgw"
_resolve_quest_rewards
→ src/engine/pipeline_phases/quests.py
```

### New file skeleton

```python id="jmhlm9"
from __future__ import annotations

from dataclasses import replace

from src.core.state import AuthoritativeState
from src.core.updates import StateUpdate


class QuestRewardPhase:
    """
    Converts quest completion/retry state into authoritative reward intents.

    Does not directly mutate inventory or XP.
    ResourceTransactionPhase decides final success.
    """

    @staticmethod
    def resolve(state: AuthoritativeState, update: StateUpdate) -> StateUpdate:
        # paste existing method body here
        ...
```

### Wrapper

```python id="ih3vf8"
@staticmethod
def _resolve_quest_rewards(state, update):
    from src.engine.pipeline_phases.quests import QuestRewardPhase
    return QuestRewardPhase.resolve(state, update)
```

### Required order

```text id="c3azl7"
_resolve_quest_rewards
_resolve_resource_transactions
```

### Checklist

```text id="5dhmq8"
[x] worker-submitted quest status is still stripped earlier
[x] REWARD_PENDING retries every tick
[x] reward success sets REWARDED after transaction success
[x] full inventory keeps REWARD_PENDING
```

### Verification

```bash id="lzp2c1"
pytest tests/integration/pipeline/test_transaction_completion.py -q
pytest -q -k "quest_lifecycle or quest_reward"
```

---

## Task 2.8 — Extract Resource Transaction Phase [COMPLETED]

### Move

```text id="pz4sei"
_resolve_resource_transactions
→ src/engine/pipeline_phases/resources.py
```

### New file skeleton

```python id="gubj95"
from __future__ import annotations

from dataclasses import replace

from src.core.state import AuthoritativeState
from src.core.updates import StateUpdate


class ResourceTransactionPhase:
    """
    Resolves ResourceTransferIntent objects into inventory, identity, node,
    corpse, chest, or rejection updates.
    """

    @staticmethod
    def resolve(state: AuthoritativeState, update: StateUpdate) -> StateUpdate:
        # paste existing method body here
        ...
```

### Wrapper

```python id="qgqos7"
@staticmethod
def _resolve_resource_transactions(state, update):
    from src.engine.pipeline_phases.resources import ResourceTransactionPhase
    return ResourceTransactionPhase.resolve(state, update)
```

### Notes

Do not change transaction idempotency.

Do not change conservation behavior.

### Checklist

```text id="xy5qcd"
[x] full inventory harvest does not deplete node
[x] invalid harvest creates rejection audit
[x] quest reward finalizes correctly
[x] kill rewards resolve once
[x] processed_transaction_ids preserved
```

### Verification

```bash id="wp5yng"
pytest tests/integration/pipeline/test_transaction_completion.py -q
pytest tests/integration/pipeline/test_rejection_audit.py -q
```

---

## Task 2.9 — Extract Movement and Position Swap Phase [COMPLETED]

### Move

```text id="k8e2ea"
_resolve_position_swaps
_route_movement_intent
→ src/engine/pipeline_phases/movement.py
```

### New file skeleton

```python id="j84hg9"
from __future__ import annotations

from dataclasses import replace

from src.core.state import AuthoritativeState
from src.core.updates import StateUpdate


class MovementPhase:
    """
    Resolves position swap and movement routing.
    """

    @staticmethod
    def resolve_position_swaps(
        state: AuthoritativeState,
        update: StateUpdate,
    ) -> StateUpdate:
        # paste _resolve_position_swaps body here
        ...

    @staticmethod
    def route_movement_intent(
        state: AuthoritativeState,
        update: StateUpdate,
    ) -> StateUpdate:
        # paste _route_movement_intent body here
        ...
```

### Wrappers

```python id="ec79dk"
@staticmethod
def _resolve_position_swaps(state, update):
    from src.engine.pipeline_phases.movement import MovementPhase
    return MovementPhase.resolve_position_swaps(state, update)


@staticmethod
def _route_movement_intent(state, update):
    from src.engine.pipeline_phases.movement import MovementPhase
    return MovementPhase.route_movement_intent(state, update)
```

### Required order

```text id="a66x6l"
StrategicRedirectionSystem.enforce
_resolve_position_swaps
_route_movement_intent
```

### Checklist

```text id="2xb2iw"
[x] accepted POSITION_SWAP still works
[x] mutual same-tick swap still works
[x] HOLD refuses swap
[x] expired/stale contract does not swap
[x] no overlap after ApplyPath
[x] movement rejection still audited if applicable
```

### Verification

```bash id="tlyeoz"
pytest tests/integration/pipeline/test_movement_micro_arena_position_swap.py -q
pytest -q -k "movement_congestion or position_swap"
```

---

## Task 2.10 — Extract Occupancy Phase if still present [COMPLETED]

Only do this if `_resolve_occupancy_conflicts` exists in latest source.

### Move

```text id="vpzooa"
_resolve_occupancy_conflicts
→ src/engine/pipeline_phases/occupancy.py
```

### Wrapper

```python id="jyndyu"
@staticmethod
def _resolve_occupancy_conflicts(state, update):
    from src.engine.pipeline_phases.occupancy import OccupancyPhase
    return OccupancyPhase.resolve(state, update)
```

### Note

If the latest source does not currently call occupancy conflict resolution, do not invent a new call in this milestone.

This is refactor-only.

---

## Task 2.11 — Verify pipeline order guard [COMPLETED]

Run:

```bash id="e3eygs"
pytest -q -k "subsystem_order"
```

If the order guard searches `inspect.getsource(AuthoritativeApplyPipeline.refine)`, make sure `refine()` still contains the wrapper method names in order.

Good:

```python id="iuv6m2"
update = AuthoritativeApplyPipeline._resolve_resource_transactions(state, update)
```

Bad:

```python id="f0x7xn"
update = ResourceTransactionPhase.resolve(state, update)
```

Reason: existing order tests may look for wrapper names.

---

# Milestone 3 — Split `src/engine/domain_logic.py` [COMPLETED]

## Goal

Separate action domain logic while keeping `SimulationDomainLogic` as a public facade.

---

## Critical Rule

Keep all old static methods on `AuthoritativeApplyPipeline`.

This is required because tests may still inspect or call:

```text id="sktm3b"
AuthoritativeApplyPipeline._strip_untrusted_world_effects
AuthoritativeApplyPipeline._resolve_actor_validity
AuthoritativeApplyPipeline._resolve_contract_expirations
AuthoritativeApplyPipeline._route_action_intent
AuthoritativeApplyPipeline._apply_near_death_hardening
AuthoritativeApplyPipeline._resolve_quest_rewards
AuthoritativeApplyPipeline._resolve_resource_transactions
AuthoritativeApplyPipeline._resolve_position_swaps
AuthoritativeApplyPipeline._route_movement_intent
```

Do not remove them.

---

## Target Structure

```text id="xtfaq3"
src/engine/domain/
  __init__.py
  view.py
  action_router.py
  combat_actions.py
  skill_actions.py
  aoe_actions.py
  movement_actions.py
```

---

## Task 3.1 — Create domain package [COMPLETED]

```bash id="whrp95"
mkdir -p src/engine/domain
touch src/engine/domain/__init__.py
```

---

## Task 3.2 — Move neighbor view logic [COMPLETED]

### Move from

```text id="to4o11"
SimulationDomainLogic.get_neighbor_view
```

### Move to

```text id="6a2p7v"
src/engine/domain/view.py
```

### Implementation

```python id="kwiq1m"
from __future__ import annotations


class DomainView:
    """
    Builds deterministic local neighbor views for domain action execution.
    """

    @staticmethod
    def get_neighbor_view(state, entity, radius: float = 10.0):
        # paste existing get_neighbor_view body here
        ...
```

### Facade

In `src/engine/domain_logic.py`:

```python id="xajrab"
class SimulationDomainLogic:
    @staticmethod
    def get_neighbor_view(state, entity, radius=10.0):
        from src.engine.domain.view import DomainView
        return DomainView.get_neighbor_view(state, entity, radius)
```

### Verification

```bash id="j0r921"
pytest -q -k "neighbor_view or domain_logic"
```

---

## Task 3.3 — Extract combat attack logic [COMPLETED]

### Move ATTACK branch to

```text id="s9lrx8"
src/engine/domain/combat_actions.py
```

### Implementation skeleton

```python id="q85jtz"
from __future__ import annotations


class CombatActions:
    """
    Domain action handlers for direct combat attacks.
    """

    @staticmethod
    def execute_attack(
        entity,
        payload,
        current_tick,
        neighbor_view,
        context=None,
    ):
        # paste ATTACK branch logic here
        ...
```

### Notes

Preserve:

```text id="r6r4u0"
- target_id lookup
- CombatResolutionSystem.resolve_attack
- quest kill update hook
- combat reward ResourceTransferIntent
- failure reason behavior
```

---

## Task 3.4 — Extract skill logic [COMPLETED]

### Move SKILL branch to

```text id="194foe"
src/engine/domain/skill_actions.py
```

### Skeleton

```python id="k3ayfg"
class SkillActions:
    """
    Domain action handlers for skill usage.
    """

    @staticmethod
    def execute_skill(
        entity,
        payload,
        current_tick,
        neighbor_view,
        context=None,
    ):
        # paste SKILL branch logic here
        ...
```

### Checklist

```text id="h04fuw"
[ ] learned skill validation preserved
[ ] cooldown validation preserved
[ ] stamina/readiness validation preserved
[ ] rejected skill preserves failure reason
[ ] successful skill annotates combat/resource effects as before
```

---

## Task 3.5 — Extract AOE logic [COMPLETED]

### Move AOE_ATTACK branch to

```text id="lx30xa"
src/engine/domain/aoe_actions.py
```

### Skeleton

```python id="llp7v5"
class AoeActions:
    """
    Domain action handlers for area-of-effect attacks.
    """

    @staticmethod
    def execute_aoe_attack(
        entity,
        payload,
        current_tick,
        neighbor_view,
        context=None,
    ):
        # paste AOE_ATTACK branch logic here
        ...
```

### Critical note

Do not reintroduce this old bug:

```python id="hzljjz"
context.get(eid)
```

Use:

```python id="0sg1n3"
context.entities.get(eid)
```

if `context` is an `AuthoritativeState`.

---

## Task 3.6 — Extract movement action logic [COMPLETED]

### Move MOVE branch to

```text id="uhqkbz"
src/engine/domain/movement_actions.py
```

### Skeleton

```python id="bsu1te"
class MovementActions:
    """
    Domain action handlers for explicit MOVE actions.
    """

    @staticmethod
    def execute_move(
        entity,
        payload,
        current_tick,
        neighbor_view,
        context=None,
    ):
        # paste MOVE branch logic here
        ...
```

---

## Task 3.7 — Create action router [COMPLETED]

### File

```text id="5xw9z4"
src/engine/domain/action_router.py
```

### Implementation

```python id="2rh6sv"
from __future__ import annotations

from src.engine.domain.combat_actions import CombatActions
from src.engine.domain.skill_actions import SkillActions
from src.engine.domain.aoe_actions import AoeActions
from src.engine.domain.movement_actions import MovementActions


class ActionRouter:
    """
    Routes action payloads to specific domain handlers.

    This class should contain routing only, not gameplay logic.
    """

    @staticmethod
    def execute_action(
        entity,
        payload,
        current_tick,
        neighbor_view,
        context=None,
    ):
        action = payload.get("action")

        if action == "ATTACK":
            return CombatActions.execute_attack(
                entity,
                payload,
                current_tick,
                neighbor_view,
                context,
            )

        if action == "SKILL":
            return SkillActions.execute_skill(
                entity,
                payload,
                current_tick,
                neighbor_view,
                context,
            )

        if action == "AOE_ATTACK":
            return AoeActions.execute_aoe_attack(
                entity,
                payload,
                current_tick,
                neighbor_view,
                context,
            )

        if action == "MOVE":
            return MovementActions.execute_move(
                entity,
                payload,
                current_tick,
                neighbor_view,
                context,
            )

        return {}
```

---

## Task 3.8 — Reduce `domain_logic.py` to facade [COMPLETED]

### Final shape

```python id="6uy5jv"
from __future__ import annotations

from src.engine.domain.action_router import ActionRouter
from src.engine.domain.view import DomainView


class SimulationDomainLogic:
    """
    Public compatibility facade for domain action execution.

    Keep this import path stable:
        from src.engine.domain_logic import SimulationDomainLogic
    """

    @staticmethod
    def execute_action(
        entity,
        payload,
        current_tick,
        neighbor_view,
        context=None,
    ):
        return ActionRouter.execute_action(
            entity=entity,
            payload=payload,
            current_tick=current_tick,
            neighbor_view=neighbor_view,
            context=context,
        )

    @staticmethod
    def get_neighbor_view(state, entity, radius=10.0):
        return DomainView.get_neighbor_view(
            state,
            entity,
            radius,
        )
```

### Verification

```bash id="b7pvqi"
pytest tests/integration/pipeline/test_combat_legality_matrix.py -q
pytest -q -k "quest_lifecycle or skill_pipeline or aoe"
pytest tests/refactor/test_import_compatibility.py -q
```

---

# Milestone 4 — Group `src/systems` Safely [COMPLETED]

## Goal

Improve readability of systems without creating Python package/file conflicts. [COMPLETED]

---

## Important Conflict Warning

You cannot have both:

```text id="6mbhqe"
src/systems/strategic.py
src/systems/strategic/
```

at the same time.

Therefore, use temporary grouped folder names:

```text id="pc5016"
src/systems/strategic_systems/
src/systems/social_systems/
src/systems/world_systems/
src/systems/economy_systems/
src/systems/lifecycle_systems/
```

Keep old files as wrappers.

---

## Task 4.1 — Create grouped folders [COMPLETED]

```bash id="94d812"
mkdir -p src/systems/strategic_systems
mkdir -p src/systems/social_systems
mkdir -p src/systems/world_systems
mkdir -p src/systems/economy_systems
mkdir -p src/systems/lifecycle_systems

touch src/systems/strategic_systems/__init__.py
touch src/systems/social_systems/__init__.py
touch src/systems/world_systems/__init__.py
touch src/systems/economy_systems/__init__.py
touch src/systems/lifecycle_systems/__init__.py
```

---

## Task 4.2 — Move strategic system implementation [COMPLETED]

### Move implementation body

```text id="stnhry"
src/systems/strategic.py
→ src/systems/strategic_systems/intelligence.py
```

### Old wrapper

Replace `src/systems/strategic.py` with:

```python id="icupne"
"""
Compatibility wrapper.

Public import path:
    from src.systems.strategic import StrategicIntelligenceSystem
"""

from src.systems.strategic_systems.intelligence import StrategicIntelligenceSystem

__all__ = ["StrategicIntelligenceSystem"]
```

### Do not

```text id="wqxwoq"
Do not rename StrategicIntelligenceSystem.
Do not update all imports yet.
Do not create src/systems/strategic/ folder.
```

---

## Task 4.3 — Move redirection/detour/belief/learning [COMPLETED]

Suggested moves:

```text id="gqoflf"
src/systems/redirection.py
→ src/systems/strategic_systems/redirection.py

src/systems/detour.py
→ src/systems/strategic_systems/detour.py

src/systems/belief.py
→ src/systems/strategic_systems/belief.py

src/systems/learning.py
→ src/systems/strategic_systems/learning.py
```

Each old file becomes wrapper.

Example:

```python id="ul31xl"
# src/systems/redirection.py

from src.systems.strategic_systems.redirection import StrategicRedirectionSystem

__all__ = ["StrategicRedirectionSystem"]
```

### Verification

```bash id="uu6du2"
pytest tests/unit/strategic -q
pytest tests/integration/pipeline -q
pytest tests/refactor/test_import_compatibility.py -q
```

---

## Task 4.4 — Move social systems [COMPLETED]

Suggested moves:

```text id="9kbk3r"
src/systems/social_contract.py
→ src/systems/social_systems/contracts.py

src/systems/social_memory.py
→ src/systems/social_systems/memory.py

src/systems/party.py
→ src/systems/social_systems/party.py
```

Wrappers preserve old imports.

Example:

```python id="pjphc8"
# src/systems/social_contract.py

from src.systems.social_systems.contracts import SocialContractSystem

__all__ = ["SocialContractSystem"]
```

### Verification

```bash id="2jog1n"
pytest tests/unit/social -q
pytest -q -k "contract"
```

---

## Task 4.5 — Move world support systems [COMPLETED]

Suggested moves:

```text id="eqkhyn"
src/systems/generator.py
→ src/systems/world_systems/generator.py

src/systems/navigation.py
→ src/systems/world_systems/navigation.py

src/systems/groups.py
→ src/systems/world_systems/groups.py
```

Wrappers preserve old imports.

### Verification

```bash id="km86hj"
pytest tests/unit/world -q
pytest tests/integration/world -q -m "not slow"
```

---

# Milestone 5 — Prepare `src/core` for Future Split [COMPLETED]

## Goal

Prepare safe core boundaries without breaking the entire project.

---

## Critical Rule

Do **not** fully split:

```text id="5txyi9"
src/core/state.py
src/core/updates.py
```

These are graph hubs and public import facades.

Only move low-risk model groups if wrappers preserve old imports.

---

## Target Preparation Structure

```text id="x8nq4x"
src/core/models/
  __init__.py
  inventory.py
  social.py
  quests.py

src/core/update_models/
  __init__.py
  inventory.py
  resources.py
  quests.py
```

---

## Task 5.1 — Create folders only [COMPLETED]

```bash id="4xaxz4"
mkdir -p src/core/models
mkdir -p src/core/update_models
touch src/core/models/__init__.py
touch src/core/update_models/__init__.py
```

Stop here first.

Run:

```bash id="ws3ef1"
pytest tests/refactor/test_import_compatibility.py -q
```

---

## Task 5.2 — Move only standalone inventory models [COMPLETED]

Only if you want to proceed.

Move:

```text id="1j7bma"
ItemStack
InventoryComponent
```

to:

```text id="7k4c7u"
src/core/models/inventory.py
```

## Task 5.3 — Re-export models in src/core/state.py [COMPLETED]

```python id="jk6y3i"
from src.core.models.inventory import ItemStack, InventoryComponent
```

### Checklist

```text id="bnyy8u"
[x] old import still works: from src.core.state import ItemStack
[x] old import still works: from src.core.inventory import InventoryComponent if used
[x] dataclass equality unchanged
[x] serialization tests pass
```

### Verification

```bash id="pduy2f"
pytest tests/unit/core -q
pytest tests/unit/resource -q
pytest tests/refactor/test_import_compatibility.py -q
```

---

## Task 5.4 — Do not move EntityState yet [COMPLETED]

Do not move:

```text id="0f57fv"
EntityState
AuthoritativeState
IdentityComponent
CombatComponent
StrategicComponent
NavigationComponent
```

Reason:

```text id="r5zkj5"
These are deeply referenced and should be moved only after pipeline/domain/systems refactors are stable.
```

---

# Milestone 6 — Documentation and Graph Cleanup [COMPLETED]

## Goal

Make the new structure understandable for future contributors and AI agents.

---

## Task 6.1 — Update ARCHITECTURE.md (if exists) [COMPLETED]

Create:

```text id="ez8d8x"
docs/architecture/refactor_boundaries.md
```

Content:

```md id="cvix11"
# Refactor Boundaries

## Public Facades

These import paths are stable and should not be removed without a migration plan:

- `src.engine.pipeline.AuthoritativeApplyPipeline`
- `src.engine.domain_logic.SimulationDomainLogic`
- `src.core.state.*`
- `src.core.updates.*`
- `src.systems.strategic.StrategicIntelligenceSystem`

## Internal Implementation Modules

These modules are internal and may change:

- `src.engine.pipeline_phases.*`
- `src.engine.domain.*`
- `src.systems.*_systems.*`
- `src.core.models.*`
- `src.core.update_models.*`

## Rule

Tests may import public facades.

New implementation code may import internal modules when it is part of the same subsystem.

Do not rewrite all imports at once.
```

---

## Task 6.2 — Update graphify knowledge graph [COMPLETED]

After source moves:

```bash id="ql6cez"
python scripts/build_dependency_graph.py > graph_latest_refactor.json
```

Use the actual graph-generation command from your project if different.

### Checklist

```text id="x0nkye"
[ ] graph generated successfully
[ ] pipeline.py smaller
[ ] domain_logic.py mostly facade
[ ] core state/update still intentionally central
```

---

# Final Milestone Checklist

Use this as the full implementation checklist.

```text id="xhpjlv"
Milestone 0 — Safety
[ ] reports/refactor created
[ ] collect_before captured
[ ] focused baseline tests captured
[ ] pytest markers added
[ ] import compatibility guard added and passing

Milestone 1 — Tests
[x] target test folders created
[x] pipeline tests moved to tests/integration/pipeline
[x] world long-run tests moved to tests/integration/world
[x] unit tests grouped by domain
[x] arena contains only CertificationHarness tests
[x] collect-after compared with collect-before
[x] no duplicate old tests remain

Milestone 2 — Pipeline
[x] pipeline_phases package created
[x] TrustBoundaryPhase extracted
[x] ActorValidityPhase extracted
[x] ContractLifecyclePhase extracted
[x] ActionRoutingPhase extracted
[x] NearDeathHardeningPhase extracted
[x] QuestRewardPhase extracted
[x] ResourceTransactionPhase extracted
[x] MovementPhase extracted
[x] wrappers preserved on AuthoritativeApplyPipeline
[x] refine order unchanged
[x] subsystem order test passing
[x] pipeline integration tests passing

Milestone 3 — Domain Logic
[ ] domain package created
[ ] DomainView extracted
[ ] CombatActions extracted
[ ] SkillActions extracted
[ ] AoeActions extracted
[ ] MovementActions extracted
[ ] ActionRouter created
[ ] SimulationDomainLogic facade preserved
[ ] combat/AOE/skill tests passing

Milestone 4 — Systems
[ ] strategic_systems folder created
[ ] social_systems folder created
[ ] world_systems folder created
[ ] old system files converted to wrappers
[ ] no package/file name conflict introduced
[ ] strategic/social/world tests passing

Milestone 5 — Core Preparation
[ ] core/models folder created
[ ] core/update_models folder created
[ ] no risky EntityState/AuthoritativeState split performed
[ ] optional low-risk inventory model move completed only if stable
[ ] core import compatibility passing

Milestone 6 — Docs / Graph
[ ] refactor_boundaries.md created
[ ] phase/domain README files created
[ ] graph regenerated
[ ] graph hotspot review completed
[ ] integrity tests passing
```

---

# Recommended Execution Order for AI Agent

Use this exact order:

```text id="ry0ezy"
1. Milestone 0 only.
2. Stop. Run verification.
3. Milestone 1 only.
4. Stop. Run verification.
5. Milestone 2 only.
6. Stop. Run verification.
7. Milestone 3 only.
8. Stop. Run verification.
9. Milestone 4 only.
10. Stop. Run verification.
11. Milestone 5 only if all previous milestones are stable.
12. Milestone 6 last.
```

Do not do this:

```text id="pz49gd"
Milestone 1 + 2 + 3 in one commit
```

Better commit shape:

```text id="t3jfa6"
commit 1: add refactor guard and baseline docs
commit 2: reorganize tests only
commit 3: extract pipeline trust/actor/contracts phases
commit 4: extract pipeline action/resource/movement phases
commit 5: split domain_logic facade
commit 6: group systems behind wrappers
commit 7: add architecture docs and graph update
```

---

# Minimum Useful First Refactor

If you want the safest practical first implementation, do only this:

```text id="l4pvzq"
Milestone 0
Milestone 1
Milestone 2 Task 2.2 only
Milestone 2 Task 2.3 only
```

That gives immediate structure improvement without touching combat, quest, movement, or resource transaction logic.

The highest-risk extractions are:

```text id="1vwsb7"
ActionRoutingPhase
ResourceTransactionPhase
MovementPhase
```

Do these only after the simple phase extractions pass.
