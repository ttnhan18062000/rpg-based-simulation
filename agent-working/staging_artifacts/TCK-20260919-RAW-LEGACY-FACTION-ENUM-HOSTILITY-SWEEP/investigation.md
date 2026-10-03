---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260919-RAW-LEGACY-FACTION-ENUM-HOSTILITY-SWEEP
artifact_type: investigation
tags: [combat, faction, root-cause]
---

# Investigation — raw legacy-`Faction`-enum hostility sweep

The ticket body carries the original 2026-09-19 sweep and the three 2026-10-02 corrections. **This file
is the verified inventory and the ranking.** It does not restate either.

## 1. The defect in one paragraph

`Faction` is a **4-value `IntEnum`** (`src/core/enums.py:33-37`: `HERO_GUILD=0`, `MONSTER_HORDE=1`,
`TOWN_COUNCIL=2`, `NEUTRAL=3`). Every content faction collapses onto one of those four buckets —
`bandit_company`, `goblin_warband` and `orc_clan` all become `MONSTER_HORDE`. So
`a.identity.faction != b.identity.faction` answers "are these in different legacy buckets", not "are
these hostile". The authoritative answer comes from the content catalog, reached via
`get_faction_semantics_service().is_hostile_compat(...)`; the reference implementation is
`LegalityServiceV2._is_engagement_hostile` (`src/engine/legality.py:516-544`), whose own docstring
records that the raw comparison it replaced **"was measured to disagree with it on 34%-97% of every pair
either source flagged as hostile"** (`TCK-20260919-COMBAT-ENGAGED-HOSTILES-UNIFY-CATALOG-SEMANTICS`).

Two error directions, both real, and they are not symmetric:
- **Over-detection** (different bucket, catalog-friendly) → treats an ally as an enemy.
- **Under-detection** (same bucket, catalog-hostile) → treats an enemy as an ally. This is the one that
  makes cross-faction monster conflict impossible, since all three monster factions share one bucket.

## 2. Verified inventory, `origin/main` = `4c133297b`

Swept by **shape**, not by name — `grep -rn "identity\.faction *[!=]= *[a-z_]*\.identity\.faction" src/`
— because the original arc's fourth instance was a structurally different function found only by a
failing test. 12 raw hits, classified:

| # | site | current line | ticket said | classification |
|---|---|---|---|---|
| 1 | `src/ai/goals/scorers.py` `CombatEngageScorer` | 108 | 108 ✓ | **NOT THIS TICKET** — item 1's |
| 2 | `src/engine/legality.py` `has_hostile_at` (flanking) | 451 | 451 ✓ | real defect |
| 3 | `src/engine/combat.py` splash friendly-fire | **507** | 538 ✗ | real defect, **line drifted −31** |
| 4 | `src/systems/world_systems/intake.py` danger concern | 30 | 30 ✓ | real defect |
| 5 | `src/systems/world_systems/intake.py` `trauma_dead_ally` | 44 | 44 ✓ | real defect |
| 6 | `src/engine/cognition.py` `SensoryFilter.filter_saliency` | 44 | 44 ✓ | real defect — **folded in** |
| 7 | `src/engine/cognition.py` outnumbered/panic ratio | 117 | 117 ✓ | real defect |
| 8 | `src/domains/cooperation/providers.py` exclude-hostiles | 50 | 50 ✓ | real defect |
| 9 | `src/systems/strategic_systems/intelligence.py` lead/intel | 149, 439 | 149, 439 ✓ | real defect (2 lines) |
| — | `src/engine/legality.py:269` | 269 | named as the *good* example | **not a defect** |
| — | `src/engine/legality.py:524` | 524 | — | **not code** — docstring text |

**`:269` is correct by design** and is the pattern to copy: inside `verify_attack_legality`, an
`if has_clean:` branch calls `is_hostile_compat` and the `else:` falls back to the raw enum **only when
clean identity data is unavailable**. Do not "fix" it.

**`:451` is the contrast** — `has_hostile_at` returns the raw comparison with no catalog path at all:
```python
def has_hostile_at(pos): 
    entity = spatial_index.get(pos)
    if entity:
        return entity.identity.faction != defender.identity.faction
```

**Negative result worth recording:** `intelligence.py:83` imports `ConcernIntakeSystem` from
`src.systems.world_systems.intake` and `:861` from `src.systems.intake`. **Not** a duplicate class —
`src/systems/intake.py` is a 3-line re-export shim. Sites 4 and 5 are one location each. (Checked
because a same-name divergent pair would have doubled the work and is a real pattern elsewhere —
`TCK-20260930-SAME-NAME-DIVERGENT-CLASS-PAIRS`.)

## 3. Ranking — by durability of the wrong answer, not by call volume

The repo's Durable State Rule is the right axis: a wrong transient decision is recoverable next tick, a
wrong durable record is not.

### Group A — writes wrong durable state. Fix first.

**A1. `combat.py:507`, splash friendly-fire.** `if attacker.identity.faction == other_ent.identity.faction: continue`.
Two consequences, both durable: splash **never hits** hostiles that share the attacker's bucket (so no
cross-faction monster splash ever), and **does hit** catalog-allied entities in a different bucket.
Produces wrong HP, wrong deaths and wrong grudges. Live via `action_router.py:111` →
`aoe_actions.py:43`. **Corpus firing frequency is unmeasured** — see §4.

**A2. `intake.py:30` and `:44`, concern generation.** Worse than the triage framed it, because these
write **typed durable records into canonical state**: `strategic.concerns` is serialised in the
canonical form (`src/core/state.py:964`), so wrong concerns are inside the determinism fingerprint.
Runs every tick via `intelligence.py:582` and `:896`.
- `:30` raises a `danger` concern for *any* different-bucket live neighbour within 3 tiles — so a
  catalog-ally in another bucket becomes a standing threat record.
- `:44` raises `trauma_dead_ally` for *any* dead same-bucket neighbour — so an orc grieves a dead goblin
  as an ally. Note the record's **id itself** encodes the false claim:
  `id=f"trauma_dead_ally_{neighbor.id}"`. That is durable meaning carried in an identifier, which the
  Durable State Rule explicitly forbids — so fixing the predicate is necessary but may not be
  sufficient; the plan must decide whether the id/kind needs to change too.

### Group B — alters a durable outcome through a modifier. Fix second.

**B1. `legality.py:451`, flanking bonus.** Feeds a combat modifier, so it changes damage, which changes
HP and deaths. Durable in effect though not itself a record. Lower than Group A only because it is a
modifier rather than the primary decision, and because `:265-269` next door shows exactly the shape to
adopt.

### Group C — wrong transient decision inputs. Fix last, in one pass.

**C1. `cognition.py:44`, `SensoryFilter.filter_saliency`** — the folded-in
`TCK-20260915-SENSORY-FILTER-SALIENCY-USES-LEGACY-FACTION-ENUM`, P2, **measured at 0.5% real impact for
its own specific consumer**. That measurement is now suspect rather than wrong: it was taken for one
consumer, and `CombatEngageScorer` calls this on the line directly above its own hostility test
(`scorers.py:107`), so the saliency filter shapes the candidate set that item 1's fix will start acting
on. **Re-measure in this ticket rather than inheriting 0.5%.**
**C2. `cognition.py:117`**, outnumbered/panic ratio — wrong morale input.
**C3. `cooperation/providers.py:50`**, exclude-hostiles for partner selection — may lead to durable
contracts, so confirm during implementation whether this belongs in Group A.
**C4. `intelligence.py:149` and `:439`**, lead-confirmation/observation intel — confirm whether leads
are durable records; if they are, promote to Group A.

## 4. What is NOT measured, and why that shapes the plan

- **No corpus firing frequency for any Group A or B site.** The 34-97% figure is a *disagreement rate
  over flagged pairs*, **not** a frequency of occurrence. Nothing here establishes how often splash
  actually fires on a mixed-bucket group in corpus play, or how many wrong concerns accumulate per 1000
  ticks. The plan therefore **measures each group before and after** rather than asserting impact.
- **Direction of effect per site is unmeasured.** Over- vs under-detection have opposite gameplay
  consequences (more friendly fire vs no monster-on-monster combat), so a per-site before/after count of
  each direction is the honest instrument.
- **C3 and C4's durability is unconfirmed** — they are ranked on reading, not measurement, and the plan
  says to confirm rather than assume.
- The `0.5%` figure on C1 is inherited from another ticket's measurement of a different consumer and
  should not be cited as this ticket's own.
- Group A1's blast radius interacts with item 1: once `COMBAT_ENGAGE` actually dispatches attacks,
  splash fires more often. **Measure A1 after item 1 has landed**, or the baseline is taken against a
  world where decision-driven combat barely happens.
