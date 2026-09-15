# Investigation — TCK-20260914-FACTION-WAR-DECLARATION-DESIGN-QUESTION

**Investigation only, per this ticket's own explicit instruction: no implementation until peer/user
has reviewed the finding.**

## Central question, answered: a real design exists

`DiplomaticStateMachine.compute_transitions()` (`src/domains/faction/diplomatic_state_machine.py`)
is a real, deliberate, deterministic 4-step state machine, not a decorative or abandoned mechanism:

```
NEUTRAL → TENSE     pair_tension > 0.4
TENSE   → HOSTILE    pair_tension > 0.7  OR  shared_territory
HOSTILE → WAR        military_strength imbalance > 20%
WAR     → NEUTRAL    both military_strength < 0.3 (exhaustion)
```

Its own module docstring explicitly documents the transition priority and design intent — this
reads as authored game design, not incidental code. **It is genuinely wired into the real tick
pipeline**: `src/engine/pipeline.py:260` calls `compute_transitions(state.factions)` every tick
(confirmed via direct grep of all call sites, and independently confirmed via an earlier
investigation's own phase-cost telemetry from this batch showing a live `diplomatic_transitions`
phase cost on every real tick). This is not the "no real design exists" outcome the ticket's own
scope named as the other possibility — a real design exists.

## But it is unreachable in practice — three independent, structurally-blocking causes

Ran a real, instrumented 3000-tick `Kernel.tick_once()` simulation against `urban_political`
(seed=42, 16 real factions) tracking every faction's `tension_level`, `military_strength`,
`territory`, and `diplomatic_relations` on every tick.

### 1. `military_strength` is mathematically frozen at `1.0` for every faction, always

`FactionState.military_strength: float = 1.0` is the dataclass default (`src/core/state.py:727`).
Confirmed via exhaustive grep: the **only** real producer that ever changes it is
`military_conflict.py`'s WAR-exhaustion drain (`-0.001/tick per WAR faction`) — which only applies
to a faction **already at war**. No compile-time content (checked `WorldCompiler` directly — zero
references to `military_strength` anywhere in it) and no other runtime mechanism differentiates one
faction's military strength from another's before war exists.

**Empirically confirmed**: across the full 3000-tick run, every one of the 16 factions' own
`military_strength` stayed at exactly `1.0..1.0` (min==max==1.0) for the entire run. The
`HOSTILE → WAR` condition (`ms_a > ms_b * 1.2`) needs `1.0 > 1.2`, which is never true. **This
transition is not rare — it is structurally impossible from the real starting state**, independent
of any other precondition.

### 2. `shared_territory` is circularly blocked — territory can only be gained *by* a war

`FactionState.territory: Tuple[str, ...] = ()` — confirmed via direct grep of `WorldCompiler`
(`src/worldbuilding/compiler.py`) that **zero lines anywhere in it reference `territory`** — no
world spec, of any tested world, ever seeds a faction's starting territory at compile time. (A
grep hit for the string "territory" in some `data/worlds/*/resolved/*.yaml` files turned out to be
resource-node/content-module naming, e.g. `orc_clan_territory__iron_vein_0` — not
`FactionState.territory` data; the actual faction roster entries in every checked world spec have
no `territory` key at all.)

The **only** real runtime producer of new territory is `military_conflict.py:283`
(`territory_add=(contested_region_id,)`) — territory transfer following a completed siege, which
per D-06's own text requires an existing `DiplomaticState.WAR` to fire in the first place.

**This is circular**: `shared_territory` is one of two ways to reach `HOSTILE` (a precondition for
`WAR`), but the only way to ever have territory to share is a siege that itself requires `WAR` to
already exist. A faction pair can never accumulate territory before their first war, so this half
of the `TENSE → HOSTILE` condition can never be the thing that triggers a *first* war.

**Empirically confirmed**: every one of the 16 factions had `territory=()` at compile time and
`territory=()` for the entire 3000-tick run — confirmed via the same probe run.

### 3. `tension_level`'s only real runtime producer is *also* gated on territory

`FactionAwarenessService.compute_tension_updates()` (`src/engine/faction_decision.py:221-245`) is
the sole real runtime producer of `tension_delta` from ongoing play: `+0.1` per `RESOURCE_DEPLETED`
WorldEvent, but **only** `if event.region_id in fs.territory`. Since territory is always empty
(cause 2 above), this producer can structurally never fire for any faction, in any real run.

The only other real producers are hand-placed compile-time seeds
(`initial_tension_level`, `src/worldbuilding/schema.py`) and small negative deltas from diplomatic
actions (`src/domains/faction/diplomatic_actions.py`, peace-making, `-0.1`/`-0.15`) — no organic,
in-run tension *increase* mechanism exists that isn't itself blocked by the same territory gap.

**Empirically confirmed**: of `urban_political`'s 16 factions, 14 stayed at exactly `tension_level
= 0.0` for the entire 3000-tick run (never moved once — matches the analysis: their runtime
producer can never fire). The other 2 (`town_council`, `bandit_company`) started at `tension_level
= 0.5` **already at compile time** (`initial_tension_level` authored directly in the faction
catalog) and never moved from that value for the rest of the run either — confirming the runtime
producer really is inert, not just slow. `0.5` clears the `NEUTRAL → TENSE` threshold (`> 0.4`) —
every pair involving either of those two factions flipped to `TENSE` at tick 1 (`pair_tension =
max(a, b)`, so any pairing with a 0.5-tension faction crosses 0.4 immediately) — but `0.5` falls
well short of the `TENSE → HOSTILE` threshold (`> 0.7`), and `shared_territory` (the only other way
past `TENSE`) is itself blocked by cause 2. **Every one of these pairs got stuck at `TENSE` for the
entire run and never progressed further.**

## Summary: not "no design," and not "just slow" — three separately-necessary preconditions are each structurally unreachable

This is a real, intentional, correctly-implemented, wired design (`DiplomaticStateMachine`) sitting
behind THREE independent reachability defects, not one large number:
1. `military_strength` never diverges from its `1.0` default before war — the `WAR` transition's
   own precondition cannot be satisfied by any real pre-war state.
2. `territory` can only be gained by a war — the `shared_territory` half of the `HOSTILE`
   transition is circularly blocked.
3. `tension_level`'s only real runtime growth mechanism is gated on territory too — so even the
   `HOSTILE` transition's other half (`tension > 0.7`) has no organic path to grow past whatever a
   faction was authored to start with.

Empirically, in a real 3000-tick run of a 16-faction world, the state machine's own transition
ladder gets exactly one rung of real movement (2 factions reach `TENSE`, from compile-time seeding,
not runtime accrual) and then permanently stalls — matching this week's own repeated pattern of a
real mechanism whose own inputs never move enough to let it do its job.

## What this is NOT (per the ticket's own explicit scope)

This is **not** the "no real design exists, inventing a trigger is the user's call" outcome. A real
design exists. This **is** the "real design, unreachable in practice, here's which preconditions
are the actual blocker" outcome the ticket's scope names as the alternative path — bringing this
back for review, not building a fix, per explicit instruction ("Out of Scope: actually building or
changing any war-declaration trigger — investigation only, regardless of which of the two outcomes
above the investigation finds").

A genuine design decision is still needed before any fix, though, because unlike D-05 (where the
existing formula just needed reachable *numbers*), fixing this cleanly likely needs at least one
new *mechanism* to break the circularity — some real pre-war producer for `military_strength`
divergence, and/or some real pre-war producer for territory or tension that doesn't itself require
war to already exist. That is real game design (what should cause two factions' militaries to
diverge, or what should seed territory before any conquest happens), not a one-value tuning pass —
flagging this distinction explicitly rather than assuming it's the same shape as D-05.
