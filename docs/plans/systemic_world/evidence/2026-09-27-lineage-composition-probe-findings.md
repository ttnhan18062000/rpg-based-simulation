---
status: historical
layer: architecture
authority: P2
audience: agent
tags: [architecture, documentation, roadmap]
---

> Dated evidence snapshot supporting `docs/plans/systemic_world/roadmap.md`, copied from the local working file `lineage-scenario-findings.md` on 2026-09-27. Where the roadmap has since corrected a claim, the roadmap is authoritative.

# Lineage feasibility gate — composition probe findings (fork report)

Directive: compose the two already-proven single-tick lineage transitions
(`succession`, `aging_death`) into a longer, reproducible seeded run to answer gate
question 1's fuller form (composition) and question 3 (chronology/continuity);
sketch a minimal provisional observer position and evidence packet; answer gate
question 4 as three separate sub-questions. Investigation only — no production
code changed, no new files under `tests/`.

---

## 1. Composition attempt: result and exact run evidence

### 1a. Tick 0 — real, composed inheritance (succeeded)

Built a 3-entity scenario (grandparent → parent → grandchild) reusing the exact
`V2EntityBuilder`/`Kernel` technique from
`tests/simulation_quality/test_heir_inventory_transfer_corpus.py` and
`tests/integration/campaigns/test_lineage_dispatch_deterministic_kernel_tick.py`.

- **Seed**: 42 (`DeterministicRNG(42)`, `AuthoritativeState(tick=0, seed=42, ...)`).
- **Starting state**: entity 1 (grandparent) staged already past `max_age_ticks`
  (`age_ticks=999_999_999, max_age_ticks=1, heir_entity_id=2`), carrying
  `iron_sword` (a real, registered item — see negative note below) and a
  Campaign-mode nemesis blocker `nemesis_99` (severity 0.8). Entity 2 (parent)
  starts alive and ordinary, carrying `healing_potion`. Entity 3 (grandchild)
  starts alive and ordinary, uninvolved at this point.
- **Run**: one real `kernel.tick_once()` (tick 0).
- **Result, read directly from `kernel.state` after the tick**:
  - `entities[1].lifecycle.active = False`, `death_reason = "OLD_AGE"`.
  - `entities[2].inventory.items` = `{healing_potion, iron_sword}` — both the
    parent's own item and the grandparent's item, confirming real, same-tick
    inheritance through `LifecycleSystem.resolve_lifecycle`.
  - `entities[2].strategic.blockers` = `{inherited_nemesis_99}` (severity
    `0.8 * 0.5 = 0.4`, per `LifecycleSystem.INHERITED_NEMESIS_SEVERITY_MULTIPLIER`).
  - `entities[2].cognition.motivation.named_intention` = a dying wish, text
    `"avenge me against 99"`, `source_entity_id=1`, `status="PENDING"`.
- **Note on a false start**: the very first attempt used invented item ids
  (`ancestral_blade`, `parents_own_ring`) and the transfer silently produced an
  *empty* inherited inventory. Root cause: `InventoryService.can_add_items`
  (`src/core/inventory.py:74-75`) returns `False` for the whole transfer batch
  the instant any item in it has no `ItemRegistry` entry ("Law: Unknown items
  cannot be added"). This was a scripting error, not a simulation edge — fixed
  by using real registered item ids (`iron_sword`, `healing_potion`, the same
  ones the two repo tests already use). Recorded here because it is exactly the
  kind of confound the investigation instruction warns against mistaking for a
  real blocker.

### 1b. Extending to a second, later-tick hop: blocked, narrowest cause identified

The interesting claim (gate Q1's fuller form, Q3) needs the parent (entity 2) to
*later* die and pass the tick-0-inherited items on again to entity 3 — a real
two-hop chain where an earlier event provably alters a later world state. Two
attempts, in order:

**Attempt A — direct state mutation between ticks** (mirroring how the two repo
tests build their *initial* state, and how
`tests/mechanic_scenarios/test_aging_death_value_differential.py` stages a field
directly rather than waiting out real per-tick aging):

```python
staged_parent = replace(
    par0,
    lifecycle=replace(par0.lifecycle, age_ticks=999_999_999, max_age_ticks=1, heir_entity_id=3),
)
kernel.state.entities[2] = staged_parent   # attempted BETWEEN ticks, not at construction
```

Result: `src.core.state.ReadOnlyError: Authoritative mutation attempted during
read-only phase.` (raised at `src/core/state.py:44`, the container's own
`__setitem__` guard). This is a real, currently-enforced architecture boundary —
the engine itself refuses this exact shortcut once a `Kernel` is running, so it
could not be used to fabricate mid-run "time passing."

**Attempt B — let the parent age to death through ordinary per-tick
progression** (no manual mutation at all): `age_ticks=0, max_age_ticks=3`,
`heir_entity_id=3` set at construction, then `kernel.tick_once()` run 5 times in
a plain loop, reading `kernel.state` after every tick.

**This surfaced a genuine, previously-unconfirmed defect**, verified
empirically (not just from a code trace):

```
tick= 1 subject.age_ticks=1 active=True  death_reason=None      heir.inventory=[]
tick= 2 subject.age_ticks=2 active=True  death_reason=None      heir.inventory=[]
tick= 3 subject.age_ticks=3 active=False death_reason=None      heir.inventory=[]
tick= 4 subject.age_ticks=4 active=False death_reason=None      heir.inventory=[]
tick= 5 subject.age_ticks=5 active=False death_reason=None      heir.inventory=[]
```

The subject goes inactive at tick 3 and **stays that way forever with
`death_reason=None`** — `LifecycleSystem.resolve_lifecycle`'s own OLD_AGE branch
never fires, and the heir's inventory never receives anything.

**Root cause, cited precisely**:

- `LifecycleSystem.resolve_lifecycle`'s OLD_AGE check
  (`src/systems/lifecycle_systems/lifecycle.py:193-194`,
  `if entity.lifecycle.age_ticks >= entity.lifecycle.max_age_ticks: is_dead = True`)
  reads `entity.lifecycle.age_ticks` from `state.entities` — the value
  **persisted at the end of the prior tick** (stale for the current tick).
- `ApplyPath._compute_entity_changes` (`src/engine/apply.py:94-99`) — which
  commits later in the *same* tick, via `apply.py:210` →
  `Kernel`'s own commit calls at `kernel.py:781` / `kernel.py:835` — independently
  computes `new_age = life.age_ticks + 1` and sets
  `active = (new_hp > 0 and new_age < life.max_age_ticks)`, **one tick ahead**
  of what `resolve_lifecycle` just checked in the same tick.
- On the tick where `new_age` first reaches `max_age_ticks`, this passive branch
  commits `active=False` with **no `death_reason` and no heir dispatch** — a
  full tick before `resolve_lifecycle`'s own check would ever see
  `age_ticks >= max_age_ticks`.
- Next tick, `resolve_lifecycle`'s own loop
  (`src/systems/lifecycle_systems/lifecycle.py:147`,
  `if not entity.lifecycle.active: continue`) finds the entity **already
  inactive** and skips it entirely — succession, heirloom/inventory transfer,
  nemesis-feud transfer, and dying-wish seeding **never fire**.

**Why the two existing repo tests don't hit this**: both stage `age_ticks`
already massively past `max_age_ticks` *from the tick-0 starting snapshot* —
`resolve_lifecycle`'s own check fires immediately, in the very first tick,
before the passive branch ever gets a chance to race ahead of it on some later
tick. The race only exists for a death that would otherwise happen "naturally,"
gradually, in the ordinary run of the simulation.

**Narrowest confirmed blocker, stated exactly as requested**: composing a
second, later-tick death through *ordinary* per-tick aging is not merely
untested — it is a confirmed simulation edge (an unresolved dual-writer race on
`entity.lifecycle.active`, the same *class* of defect the roadmap's §3.1 already
names for regional-sovereignty: two independent systems writing the same
authoritative field with no declared precedence rule). It is not a scenario-setup
problem, not a missing runtime integration, and not a missing evidence-production
gap — it is a real, reproducible defect in how old-age death is dispatched
outside the deliberately-staged case. I did not attempt a combat-triggered death
as an alternative second hop (combat death is set by an earlier same-tick phase
and, per a static read, does not appear to share this specific age-based race) —
that remains a genuinely open, untried option, out of this probe's bound.

**Scripts** (throwaway investigation code, not committed, not under `tests/`):
- `scratchpad/lineage_composition_probe.py` — the tick-0 three-entity inheritance
  run and the blocked mid-run mutation attempt.
- `scratchpad/natural_aging_race_probe.py` — the 5-tick natural-aging race probe
  and its printed verdict.

Both scripts' full text is reproduced in the Appendix below.

---

## 2. Minimal provisional observer position + evidence packet

This is a design check only — **not** a real player-observation exercise, and
`PLAYER-EXPERIENCED` is not being claimed here for anything.

**Position**: a townsperson NPC with an existing `SocialComponent.bonds` entry to
the deceased or the heir, physically co-located at the settlement where the
death occurred.

**Early clue** (shortly after the tick-0 death): the observer can legitimately
perceive an ordinary state fact — the heir is now visibly carrying an item
(`iron_sword`) never seen on them before, shortly after witnessing (or hearing
of) a death nearby. This is a legitimate in-world trace (inventory/equipment
state), not a developer-only log.

**Reasonable hypothesis available from that clue alone**: "this person is the
deceased's heir/family." In this run it happens to be true, but the clue alone
cannot prove it — the fallback heir selector
(`LifecycleSystem._select_default_heir`) picks the highest-bond-scored living
candidate when no explicit heir is set, not necessarily a *socially designated*
heir, and mere item possession cannot distinguish "true heir" from "opportunistic
looter who reached the body first." The hypothesis is reasonable, not certain.

**Later clue that could revise the hypothesis**: if the heir is later observed
acting on the inherited grudge (`inherited_nemesis_99`) or the dying wish — e.g.
pursuing the named antagonist — that would strengthen the "heir" hypothesis into
something closer to confirmed. **Nothing in the current code path produces that
observable action** (see negative check 1) — so today, this later, confirming
clue cannot actually occur without further work, and the hypothesis stays at
"reasonable but unconfirmed" indefinitely.

**Negative check 1 — an outcome with no discoverable trace at all**: the
inherited nemesis blocker and the dying wish are pure cognition/strategic
internal state. `LifecycleSystem._seed_dying_wish`'s own docstring states
plainly: "nothing in this codebase reads `NamedIntentionBundle.status` to force
an action." No system converts either of these into any player-observable
signal (no dialogue line, no behavior change, no visible marker). If the product
ever expects a player to notice "this NPC now secretly resents someone," it
currently has **zero** discoverable trace leading to that fact — exactly the
failure case the roadmap's §5 evaluation criterion warns against. If it's
intended to stay a private internal hook for later systems to consume, that's a
fine, intentional design state — just not yet exposed, and this should not be
read as evidence against the underlying mechanism.

**Negative check 2 — a specific leak-risk example**: any future biography/HUD
projection that directly renders `entity.cognition.motivation.named_intention.text`
or `entity.strategic.blockers` verbatim to the player would leak literal internal
world-truth (the omniscient "avenge me against 99" string, with its exact
`source_entity_id` and `severity`) as if it were ordinary public knowledge —
exactly the silent-leak risk §2's epistemic principle warns against, and the
same discipline `KnowledgeModelService`'s "hidden world truth is never injected"
invariant already enforces for NPCs. Name these two fields precisely as the leak
surface for any future projection work to guard against:
`EntityState.cognition.motivation.named_intention` and
`EntityState.strategic.blockers`.

---

## 3. Gate question 4 — three separate answers (not one)

- **Does the *tested* world transition need another simulation edge?** No — the
  single tick-0 hop (grandparent → parent: item transfer, nemesis-feud transfer,
  dying-wish seeding) is real, correct, and reproducible as tested. This part of
  Q4 is answered cleanly in the affirmative (no missing edge) for that one hop
  only.
- **Does its evidence production exist today?** No. There is no dedicated
  provenance/evidence producer for an inheritance event — no record of "this
  item passed through N owners," no in-world trace of the nemesis-feud transfer
  or the dying wish (see negative check 1). Confirmed absent by direct
  inspection, not merely unchecked.
- **Could a situated projection be built from it?** Only for the single,
  already-proven hop, and only once an evidence producer exists for it (the
  point above). A projection across a *second* hop is blocked by the confirmed
  defect in §1b, not by projection-design work — that distinction (a simulation
  defect blocking composition vs. an unbuilt projection layer) is itself new
  information this probe surfaces, and the two should not be conflated in the
  roadmap's gate table.

---

## Appendix: full script text

### `scratchpad/lineage_composition_probe.py`

```python
"""Throwaway investigation script (NOT a repo test) -- third-round external review of
docs/plans/systemic_world_roadmap.md: does the lineage single-tick transition compose into a
longer, real, two-hop causal sequence (grandparent -> parent -> grandchild), each hop through the
real authoritative pipeline (LifecycleSystem.resolve_lifecycle via Kernel.tick_once())?

Technique: same "already at max_age_ticks" deterministic-death staging the two existing repo tests
use (tests/simulation_quality/test_heir_inventory_transfer_corpus.py,
tests/integration/campaigns/test_lineage_dispatch_deterministic_kernel_tick.py). Between the two
real ticks, entity 2's lifecycle fields are staged directly (mutating the live AuthoritativeState's
entities dict) to make its own death fire on the next tick -- the same "stage the field directly
rather than wait out the real per-tick increment" convention already established in
tests/mechanic_scenarios/test_aging_death_value_differential.py (per registries/mechanisms.yaml's
own aging_death note). This is a test-harness convenience, not a claim that this mutation path is
authoritative-pipeline-correct for production use.
"""
from __future__ import annotations

from dataclasses import replace

from src.config.profiles import PROD_SMALL
from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState, ItemStack
from src.core.strategic import BlockerState, BlockerKind
from src.engine.kernel import Kernel
from src.platform.rng import DeterministicRNG

SEED = 42

# Entity 1: grandparent, staged for an immediate OLD_AGE death on tick 0.
grandparent = (
    V2EntityBuilder(1)
    .location(0.0, 0.0)
    .lifecycle(active=True, age_ticks=999_999_999, max_age_ticks=1, heir_entity_id=2)
    .inventory(items=[ItemStack(item_id="iron_sword", quantity=1)])
    .strategic(blockers={
        "nemesis_99": BlockerState(id="nemesis_99", kind=BlockerKind.SOCIAL, subject="99", severity=0.8),
    })
    .build()
)
# Entity 2: parent/heir. Alive and ordinary at tick 0; staged for death between tick 0 and tick 1.
parent = (
    V2EntityBuilder(2)
    .location(5.0, 0.0)
    .lifecycle(active=True)
    .inventory(items=[ItemStack(item_id="healing_potion", quantity=1)])
    .build()
)
# Entity 3: grandchild/heir of entity 2. Alive, ordinary, never dies in this run.
grandchild = (
    V2EntityBuilder(3)
    .location(10.0, 0.0)
    .lifecycle(active=True)
    .build()
)

state = AuthoritativeState(tick=0, seed=SEED, entities={1: grandparent, 2: parent, 3: grandchild})
kernel = Kernel(profile=PROD_SMALL, state=state, rng=DeterministicRNG(SEED), flags={"no_frame_pacing": True})

print("=== TICK 0 (grandparent dies, parent inherits) ===")
kernel.tick_once()

gp0 = kernel.state.entities[1]
par0 = kernel.state.entities[2]
print(f"grandparent.active={gp0.lifecycle.active} death_reason={gp0.lifecycle.death_reason}")
print(f"parent.inventory item_ids={[s.item_id for s in par0.inventory.items]}")
print(f"parent.strategic.blockers={sorted(par0.strategic.blockers.keys())}")
nw = par0.cognition.motivation.named_intention
print(f"parent.named_intention={nw.text if nw else None} source={nw.source_entity_id if nw else None}")

assert gp0.lifecycle.active is False and gp0.lifecycle.death_reason == "OLD_AGE"
assert "iron_sword" in {s.item_id for s in par0.inventory.items}, "tick0 inheritance must land before tick1"

print()
print("=== STAGING (no tick advance): mark entity 2 for death next tick, heir=3 ===")
staged_parent = replace(
    par0,
    lifecycle=replace(par0.lifecycle, age_ticks=999_999_999, max_age_ticks=1, heir_entity_id=3),
)
kernel.state.entities[2] = staged_parent
print(f"parent.inventory BEFORE tick1 (unchanged by staging) = {[s.item_id for s in kernel.state.entities[2].inventory.items]}")

print()
print("=== TICK 1 (parent dies, grandchild inherits) ===")
kernel.tick_once()

par1 = kernel.state.entities[2]
gc1 = kernel.state.entities[3]
print(f"parent.active={par1.lifecycle.active} death_reason={par1.lifecycle.death_reason}")
print(f"grandchild.inventory item_ids={sorted(s.item_id for s in gc1.inventory.items)}")
print(f"grandchild.strategic.blockers={sorted(gc1.strategic.blockers.keys())}")
nw2 = gc1.cognition.motivation.named_intention
print(f"grandchild.named_intention={nw2.text if nw2 else None} source={nw2.source_entity_id if nw2 else None}")

kernel.shutdown()

print()
print("=== RESULT ===")
gc_items = {s.item_id for s in gc1.inventory.items}
print(f"iron_sword (originated entity 1, tick0) reached entity 3 at tick1: {'iron_sword' in gc_items}")
print(f"healing_potion (originated entity 2) reached entity 3 at tick1: {'healing_potion' in gc_items}")
print(f"grandchild inherited a nemesis_* blocker (would require 2-hop feud cascade): {any(k.startswith('nemesis_') for k in gc1.strategic.blockers)}")
print(f"grandchild inherited an inherited_nemesis_* blocker (from parent's OWN nemesis_ blockers, of which there are none): {any(k.startswith('inherited_nemesis_') for k in gc1.strategic.blockers)}")
```

**Actual run output** (after fixing item ids to real registered items):

```
=== TICK 0 (grandparent dies, parent inherits) ===
grandparent.active=False death_reason=OLD_AGE
parent.inventory item_ids=['healing_potion', 'iron_sword']
parent.strategic.blockers=['inherited_nemesis_99']
parent.named_intention=avenge me against 99 source=1

=== STAGING (no tick advance): mark entity 2 for death next tick, heir=3 ===
Traceback (most recent call last):
  ...
  File ".../src/core/state.py", line 44, in __setitem__
    raise ReadOnlyError("Authoritative mutation attempted during read-only phase.")
src.core.state.ReadOnlyError: Authoritative mutation attempted during read-only phase.
```

(Tick 0's composed inheritance is real and confirmed; tick 1 never ran because
the staging step itself is architecturally refused.)

### `scratchpad/natural_aging_race_probe.py`

```python
"""Probe: does ORDINARY, gradual per-tick aging (not the deliberate 'already past max_age'
staging trick the two repo tests use) actually reach LifecycleSystem.resolve_lifecycle's own
OLD_AGE branch and fire succession/heir-transfer -- or does the independent passive-decay branch
in ApplyPath._compute_entity_changes (src/engine/apply.py:94-99) race it and set active=False one
tick earlier, silently skipping succession entirely?

Hypothesis from static code trace:
  - resolve_lifecycle's own OLD_AGE check (src/systems/lifecycle_systems/lifecycle.py) reads
    entity.lifecycle.age_ticks from state.entities -- the value PERSISTED AT THE END OF THE PRIOR
    tick (stale, pre-increment for THIS tick).
  - ApplyPath._compute_entity_changes (apply.py:94-99) computes new_age = age_ticks + 1 and sets
    active = (new_hp > 0 and new_age < max_age_ticks) for THIS tick's persisted value -- one step
    AHEAD of what resolve_lifecycle just checked, in the SAME tick's commit.
  - So on the tick where new_age first reaches max_age_ticks, the passive branch already writes
    active=False (with no death_reason, no heir dispatch) BEFORE resolve_lifecycle ever sees
    age_ticks >= max_age_ticks. Next tick, resolve_lifecycle's `if not entity.lifecycle.active:
    continue` skips the now-already-inactive entity -- succession/heirloom/dying-wish never fires.

This script builds an entity with a SMALL max_age_ticks and age_ticks=0 (ordinary start), a
pre-assigned heir, and runs enough real kernel.tick_once() calls (no manual state mutation) to
watch which branch actually wins.
"""
from __future__ import annotations

from src.config.profiles import PROD_SMALL
from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState, ItemStack
from src.engine.kernel import Kernel
from src.platform.rng import DeterministicRNG

SEED = 42
MAX_AGE = 3  # small, deterministic, reached via ordinary +1/tick aging (lifecycle cadence=1 default)

subject = (
    V2EntityBuilder(1)
    .location(0.0, 0.0)
    .lifecycle(active=True, age_ticks=0, max_age_ticks=MAX_AGE, heir_entity_id=2)
    .inventory(items=[ItemStack(item_id="iron_sword", quantity=1)])
    .build()
)
heir = (
    V2EntityBuilder(2)
    .location(5.0, 0.0)
    .lifecycle(active=True)
    .build()
)

state = AuthoritativeState(tick=0, seed=SEED, entities={1: subject, 2: heir})
kernel = Kernel(profile=PROD_SMALL, state=state, rng=DeterministicRNG(SEED), flags={"no_frame_pacing": True})

for t in range(MAX_AGE + 2):
    kernel.tick_once()
    s = kernel.state.entities[1]
    h = kernel.state.entities[2]
    print(
        f"tick={kernel.state.tick:>2} "
        f"subject.age_ticks={s.lifecycle.age_ticks} active={s.lifecycle.active} "
        f"death_reason={s.lifecycle.death_reason!r} "
        f"heir.inventory={sorted(i.item_id for i in h.inventory.items)}"
    )

kernel.shutdown()

final = kernel.state.entities[1]
heir_final = kernel.state.entities[2]
print()
print("=== VERDICT ===")
print(f"subject inactive: {not final.lifecycle.active}")
print(f"subject.death_reason set (resolve_lifecycle actually ran its OLD_AGE branch): {final.lifecycle.death_reason == 'OLD_AGE'}")
print(f"heir received inheritance (iron_sword): {'iron_sword' in {i.item_id for i in heir_final.inventory.items}}")
print(
    "RACE CONFIRMED (passive decay deactivated before resolve_lifecycle's own OLD_AGE dispatch "
    "ever fired)" if (not final.lifecycle.active and final.lifecycle.death_reason != "OLD_AGE")
    else "no race observed -- resolve_lifecycle's own dispatch fired normally"
)
```

**Actual run output**:

```
tick= 1 subject.age_ticks=1 active=True death_reason=None heir.inventory=[]
tick= 2 subject.age_ticks=2 active=True death_reason=None heir.inventory=[]
tick= 3 subject.age_ticks=3 active=False death_reason=None heir.inventory=[]
tick= 4 subject.age_ticks=4 active=False death_reason=None heir.inventory=[]
tick= 5 subject.age_ticks=5 active=False death_reason=None heir.inventory=[]

=== VERDICT ===
subject inactive: True
subject.death_reason set (resolve_lifecycle actually ran its OLD_AGE branch): False
heir received inheritance (iron_sword): False
RACE CONFIRMED (passive decay deactivated before resolve_lifecycle's own OLD_AGE dispatch ever fired)
```
