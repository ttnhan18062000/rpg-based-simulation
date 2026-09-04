---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260904-CAMP-NEST-CLASSIFICATION
artifact_type: investigation
tags: [content, feature-flags]
---

# Investigation — TCK-20260904-CAMP-NEST-CLASSIFICATION

## Current Behavior

### `CampService.process_camps` (`src/world/camp.py:12-117`)

Verified directly against source (all four claims in the ticket brief hold):

- `MATURITY_PER_TICK = 0.05` (line 17), `RAID_MATURITY_THRESHOLD = 80.0` (line 18),
  `CAMP_SPAWN_INTERVAL = 30` (line 19) — all confirmed as class constants, exactly as claimed.
- Spawn cap is `max(2, int(camp.maturity / 10.0))` (line 55) — confirmed, matches
  `docs/world/raid_boss_camp_contract.md`'s documented formula.
- Four sequential blocks inside the per-camp loop (`for c_id, camp in state.camps.items()`,
  line 32): (1) maturity evolution with trauma multiplier (lines 36-44), (2) garrison spawn on
  `CAMP_SPAWN_INTERVAL` cadence (lines 46-63, hardcoded `"goblin_warrior" if camp.kind == "goblin"
  else "orc_warrior"` binary — **this is the only place `camp.kind` is read today**, and it treats
  every non-`"goblin"` camp as `"orc"`), (3) raid trigger when `camp.maturity >=
  RAID_MATURITY_THRESHOLD` and `state.tick - camp.last_raid_tick >= 500` (lines 66-84, cost
  `maturity_delta=-20.0`), (4) the existing flag-gated Natural-Creature Reproduction branch behind
  `ENABLE_REPRODUCTION_NATURAL_CREATURE_PATH` (lines 87-116).
- `flags = getattr(state, "feature_flags", None) or {}` (line 29) — flags are read as a plain
  `Dict[str, str]` off `state.feature_flags` directly (`flags.get(KEY, "OFF") == "ON"`), **not**
  via `FeatureFlagManager.is_enabled()`. `AuthoritativeState.feature_flags` (`src/core/state.py:1336`)
  is typed `Dict[str, Any]`. This is the exact pattern block 4 already uses and the new Nest branch
  must follow the same convention for consistency with the one existing precedent in this file.

### `CampState` / `CampUpdate` (`src/core/state.py:1233-1261`, `src/core/updates.py:891-905`)

Confirmed: `CampState` has exactly `id: str`, `kind: str`, `position: tuple[float, float]`,
`maturity: float = 0.0`, `active: bool = True`, `faction: str = "hostile"`, `last_raid_tick: int =
0` (plus cache-only `_canonical_cache`/`_readonly_cache`) — no totem/stockpile/palisade fields.
`to_canonical_dict()` (lines 1248-1261) serializes exactly these 7 real fields; any new field must
be added here too or it silently drops from canonical hashing/replay.

`CampUpdate` has `id: str`, `maturity_delta: float = 0.0`, `active_set: Optional[bool] = None`,
`last_raid_tick_set: Optional[int] = None`, and a `merge()` (lines 898-905) that sums
`maturity_delta` and prefers non-`None` `_set` fields from the incoming update — the additive
delta / non-None-wins convention any new field must follow.

**Confirmed application path** (`src/engine/apply_plan.py:275-286`): the only place `CampUpdate`
fields are consumed to produce the next `CampState`. It reads `maturity_delta`, `active_set`,
`last_raid_tick_set` explicitly and calls `replace(camp, maturity=new_mat, active=new_act,
last_raid_tick=new_raid)` (line 285) — **this is the exact insertion point** for applying new
totem/stockpile/palisade fields; omitting it here means the new `CampUpdate` fields are accepted
but never actually committed to state. `src/engine/apply.py:222,415` just wires
`plan.world_collection_changes["camps"]` through unchanged — no camp-specific logic there.

### `natural_traits` (`data/content/living/races.yaml`) — all 13 races verified directly

| Race | `natural_traits` | `drive_profile` | `cognition_profile` |
|---|---|---|---|
| human | humanoid, tool_user, social_humanoid | cautious_commoner | practical_humanoid |
| wolf | quadruped, pack_hunter, territorial, carnivore | territorial_predator | instinctive_animal |
| goblin | humanoid, tool_user, opportunistic, social_humanoid, small_body | opportunistic_raider | opportunistic_humanoid |
| spider | venomous, territorial | territorial_predator | instinctive_animal |
| orc | humanoid, tool_user, large_body | opportunistic_raider | opportunistic_humanoid |
| elf | humanoid, tool_user, magic_sensitive, social_humanoid | disciplined_protector | arcane_scholar |
| dwarf | humanoid, tool_user, craftsman, disciplined | disciplined_protector | practical_humanoid |
| undead | undead | undead_purpose_bound | undead_fixated |
| troll | large_body, regenerating | territorial_predator | instinctive_animal |
| lizardfolk | humanoid, tool_user, amphibious | disciplined_protector | practical_humanoid |
| dragonkin | flying, large_body, fire_aligned, magic_sensitive | disciplined_protector | arcane_scholar |
| slime | regenerating | territorial_predator | instinctive_animal |
| spirit | spiritual, magic_sensitive | ritual_fixated | arcane_scholar |

**Key finding not in the ticket brief's summary**: `orc`'s `natural_traits` do **not** include
`"opportunistic"` (only goblin's do) — the shared axis between goblin and orc is `drive_profile ==
"opportunistic_raider"`, not the `natural_traits` list itself. This matters directly for resolving
the goblin/`social_humanoid` contradiction below.

## Classification Rule (City / Camp / Nest / Excluded)

The naive heuristic named in the ticket brief ("camp races lack `social_humanoid`") is confirmed
false against real data: goblin (Camp-target) *has* `social_humanoid`, and orc (Camp-target,
already the code's implicit second camp race via the `else "orc_warrior"` fallback in block 2)
*lacks* it entirely, same as dwarf and lizardfolk (both City-target). `social_humanoid` is
necessary-but-not-discriminating and must **not** be used as the deciding trait.

**The real, evidence-backed discriminator is `drive_profile`, cross-checked against
`natural_traits`/`cognition_profile`:**

1. **City**: `natural_traits` contains both `humanoid` AND `tool_user`, AND `drive_profile !=
   "opportunistic_raider"`. → **human, elf, dwarf, lizardfolk.**
2. **Camp**: `natural_traits` contains both `humanoid` AND `tool_user`, AND `drive_profile ==
   "opportunistic_raider"`. → **goblin, orc.**
3. **Nest**: `tool_user` absent from `natural_traits` (non-sapient/instinctive) AND
   `cognition_profile == "instinctive_animal"` AND `drive_profile == "territorial_predator"`. →
   **wolf, spider, troll, slime.**
4. **Excluded** (fall through both rules above — resolved individually, not silently dropped):
   **undead, dragonkin, spirit** — see below.

### Goblin resolution (ticket-mandated)

Goblin carries `social_humanoid` (shared with City-eligible human/elf) *and* `opportunistic`
(unique to goblin among all 13 races) plus `drive_profile: opportunistic_raider` (shared only with
orc). **The trait that actually decides Camp-over-City for goblin is `drive_profile ==
"opportunistic_raider"`, not `social_humanoid`.** `social_humanoid` is present on both City races
(human, elf) and one Camp race (goblin) — it tracks "capable of complex social organization,"
which both City and Camp populations have, not "settles into permanent cities." The raiding-economy
axis (`opportunistic_raider`) is what the code already independently confirms: `camp.py`'s garrison
-spawn block (line 60) has always defaulted every non-goblin camp to `"orc_warrior"`, i.e. orc was
already the code's *de facto* second Camp race before this ticket, and orc shares goblin's
`opportunistic_raider` `drive_profile` while having neither `opportunistic` nor `social_humanoid`
in its own `natural_traits`. This is strong independent (pre-ticket, production) evidence that
`drive_profile == "opportunistic_raider"` — not any `natural_traits` entry — is the load-bearing
signal, and it reproduces cleanly against both goblin and orc with no exceptions.

### The 5 previously-unclassified races (ticket-mandated, each resolved explicitly)

- **wolf** (`quadruped, pack_hunter, territorial, carnivore`; `territorial_predator` /
  `instinctive_animal`) → **Nest.** Matches rule 3 exactly: non-tool_user, instinctive-animal
  cognition, territorial-predator drive — the textbook "pack den" archetype Nest's spread/
  population-growth outcome is designed for.
- **undead** (`undead` only; `undead_purpose_bound` / `undead_fixated`) → **Excluded (neither),
  out-of-scope-for-now.** Fits neither rule: no `tool_user`/`humanoid` pair for City/Camp, and no
  `territorial_predator` drive or `instinctive_animal` cognition for Nest. Substantively, undead
  population growth is conceptually reanimation/raising, not biological reproduction — the Nest
  branch's spread outcome is built on the same parentless-birth-record shape as the existing
  Natural-Creature Reproduction path (`EntityGenerator.spawn_natural_creature_offspring`,
  `V2EntityBuilder.birth_record()`), which has no natural semantic fit for an undead "birth." No
  ticket currently owns a reanimation-based population mechanic; this is a real, named gap, not a
  silent omission.
- **troll** (`large_body, regenerating`; `territorial_predator` / `instinctive_animal`) → **Nest.**
  `large_body`/`regenerating` are physical-body traits, not settlement-type traits — they do not
  override the behavioral signature. `drive_profile`/`cognition_profile` are byte-identical to
  spider's and slime's already-Nest-eligible pair, and match wolf's `drive_profile`. Troll's
  `body_model` (`large_humanoid`) is visually humanoid but its `natural_traits` deliberately omit
  both `humanoid` and `tool_user` (unlike orc, which is also `large_body` but does carry both) —
  read as an authored signal that troll is a brute/monster archetype, not a tool-using
  civilization-builder.
- **dragonkin** (`flying, large_body, fire_aligned, magic_sensitive`; `disciplined_protector` /
  `arcane_scholar`, `intelligence_tier: high`) → **Excluded from Camp/Nest, explicitly Lair-
  adjacent.** Confirmed: `natural_traits` omit both `humanoid` and `tool_user` (fails rules 1/2),
  and `cognition_profile` is `arcane_scholar` not `instinctive_animal` (fails rule 3). Its
  high-intelligence, solitary/elite, `disciplined_protector` profile (shared axis with elf/dwarf/
  lizardfolk, all City-eligible) plus `flying`/`fire_aligned` do not fit Camp's raiding-horde shape
  or Nest's breeding-swarm shape — they fit idea 47's Lair concept (a single powerful, place-
  anchored occupant, `PlaceKind.LAIR`/`PlaceState.occupant_entity_id`, generalizing
  `BossService`'s `boss_region_id` idempotency pattern) far better. This ticket's own Out of Scope
  explicitly excludes anything beyond Camp/Nest, and `TCK-20260904-LAIR-ENTITY-ANCHOR` (open,
  `tickets/todos/m4-place-material-expansion/`) is the ticket that already owns exactly this
  concept — dragonkin is excluded here so it does not get double-scoped between the two tickets.
- **spirit** (`spiritual, magic_sensitive`; `ritual_fixated` / `arcane_scholar`) → **Excluded
  (neither), out-of-scope-for-now.** Fits neither rule for the same structural reasons as undead:
  no `tool_user`/`humanoid`, no `territorial_predator`/`instinctive_animal`. `spirit`'s
  `body_model` (`spirit_body`, shared only with `undead`) and its `attribute_tendencies` (no
  `strength`/`agility`/`endurance` at all — only `intelligence`/`perception`/`willpower`/
  `magic_affinity`) mark it as incorporeal; `compatible_roles` (`guardian, healer, leader`) read as
  an anchored-guardian archetype, not a raiding or breeding population. Same reasoning class as
  undead: population growth is not a coherent concept for this race under the existing spawn/birth-
  record vocabulary, and no ticket currently owns whatever the correct mechanic would be.

### spider and slime (not named in the ticket's "5 unclassified" list, but genuinely require the
same explicit call to produce a complete 13-race table)

- **spider** (`venomous, territorial`; `territorial_predator` / `instinctive_animal`) → **Nest.**
  Matches rule 3 exactly.
- **slime** (`regenerating`; `territorial_predator` / `instinctive_animal`) → **Nest.** Matches
  rule 3 exactly, despite having the sparsest `natural_traits` list of any race (a single entry) —
  `drive_profile`/`cognition_profile` alone are sufficient and unambiguous here.

### Final table (all 13 races)

| Race | Classification | Deciding rule |
|---|---|---|
| human | City | Rule 1 (humanoid+tool_user, not opportunistic_raider) |
| elf | City | Rule 1 |
| dwarf | City | Rule 1 |
| lizardfolk | City | Rule 1 |
| goblin | Camp | Rule 2 (humanoid+tool_user, opportunistic_raider) |
| orc | Camp | Rule 2 |
| wolf | Nest | Rule 3 (instinctive_animal + territorial_predator) |
| spider | Nest | Rule 3 |
| troll | Nest | Rule 3 |
| slime | Nest | Rule 3 |
| undead | Excluded (neither) | No reproduction-concept fit; unowned gap, named not silent |
| spirit | Excluded (neither) | No reproduction-concept fit; unowned gap, named not silent |
| dragonkin | Excluded (Lair-adjacent) | Owned by TCK-20260904-LAIR-ENTITY-ANCHOR |

## Insertion Points

### 1. Nest branch in `CampService.process_camps` (`src/world/camp.py:66-84`)

The existing "3. Raid Trigger" block is the exact insertion point. Today it's unconditional once
`camp.maturity >= RAID_MATURITY_THRESHOLD` and the 500-tick cooldown passes. The Nest branch must
become a fork *inside* this same gate (same threshold, same 500-tick `last_raid_tick` cooldown per
the ticket's explicit "reuses timing" requirement), not a fifth independent block, so that a camp
cannot both raid and spread on the same qualifying tick:

```python
if camp.maturity >= CampService.RAID_MATURITY_THRESHOLD:
    if state.tick - camp.last_raid_tick >= 500:
        is_nest = (
            flags.get("ENABLE_CAMP_NEST_SPREAD", "OFF") == "ON"
            and camp.kind in CampService.NEST_RACE_KINDS
        )
        if is_nest:
            # new spread/population-growth outcome
            ...
        else:
            # existing, byte-for-byte unchanged raid outcome
            ...
```

A new module-level constant on `CampService` (or a frozenset alongside the class) —
`NEST_RACE_KINDS = frozenset({"wolf", "spider", "troll", "slime"})`, mirroring the classification
table above — is the cleanest way to key off `camp.kind`, since `CampState.kind` already holds a
free-form race-flavor string (currently only ever `"goblin"` in tests; no production code
constructs `CampState` at all, confirmed by `TCK-20260904-CAMPSTATE-PLACE-BRIDGE`'s own
investigation note "no production code currently constructs `CampState()`"). This keeps the new
mechanism additive and reuses the existing `kind` field rather than adding a new one — but it is a
real design choice, not the only option (an explicit new `settlement_tier`-style field on
`CampState` is the alternative), and should be confirmed at Plan.

**Anti-drift note**: the garrison-spawn block (block 2, lines 46-63) still hardcodes
`"goblin_warrior" if camp.kind == "goblin" else "orc_warrior"` and is explicitly **not** part of
this ticket's scope to extend to wolf/spider/troll/slime kinds — the ticket's AC is specifically
about the maturity-threshold trigger (raid vs. spread), not the periodic garrison spawn. Widening
block 2 to spawn wolf/spider/troll/slime-kind mobs for Nest camps would be scope creep unless the
implementer finds it strictly required to make the spread outcome observable, in which case it must
be called out explicitly, not silently added.

**Spread outcome semantics — open question, not resolved here**: the ticket names it a "spread/
population-growth outcome" but does not specify the exact mechanism. Given this ticket's Out of
Scope explicitly forbids any `WorldModuleSpec`/`WorldCompiler`/world-generation touch and no AC may
assume a live seeded Camp exists at compile time, and given `docs/parity_ledger/world_dynamics.yaml`
WORLD-109's still-true divergence note ("camps are pre-placed at world generation... no dynamic
[CampState] construction"), the spread outcome **cannot** construct a new `CampState`. The only
existing precedent for a parentless population-growth spawn inside `CampService.process_camps()` is
block 4's Natural-Creature Reproduction path (`generator.spawn_natural_creature_offspring`). The
most conservative, precedent-consistent implementation is: on the Nest fork, spawn one or more
parentless same-kind offspring near the camp (reusing `spawn_natural_creature_offspring`, keyed off
`camp.kind`) instead of the raid's `RaidService.check_for_raid()` call, and apply the same
`maturity_delta=-20.0` partial-reset cost. This is a genuine implementation decision Plan must make
explicitly — flagged in Risks below, not assumed.

### 2. New typed fields on `CampState` / `CampUpdate`

`CampState` (`src/core/state.py:1233-1261`) — add alongside `last_raid_tick`, and add to
`to_canonical_dict()`'s `res` dict or the fields silently drop from canonical hashing:

```python
totem_tier: int = 0            # 0 = no totem; provisional numeric strength scale, unanchored
stockpile: float = 0.0         # accumulated resource stockpile; provisional magnitude, unanchored
palisade_integrity: float = 0.0  # 0 = no palisade; provisional defensive scale, unanchored
```

`CampUpdate` (`src/core/updates.py:891-905`) — matching delta/set fields, following the file's
existing `_delta`/`_set` naming convention exactly:

```python
totem_tier_set: Optional[int] = None
stockpile_delta: float = 0.0
palisade_integrity_set: Optional[float] = None
```

`merge()` (lines 898-905) must be extended: `stockpile_delta` summed (matching `maturity_delta`'s
own additive pattern), `totem_tier_set`/`palisade_integrity_set` non-None-wins (matching
`active_set`/`last_raid_tick_set`'s own pattern).

`apply_plan.py`'s camp-application block (`src/engine/apply_plan.py:275-286`) must be extended to
read and apply all three new fields via the same `replace(camp, ...)` call (line 285) — this is the
single authoritative commit point; missing it here is the single most likely silent-gap failure
mode for this ticket (new `CampUpdate` fields accepted but never actually applied to state).

Per the ticket's own note and the epic doc's Content & Balance Requirements section ("no numeric
anchor for actual magnitudes — how much does a totem buff nearby monsters"), these three
magnitudes have **zero existing numeric anchor anywhere in the codebase** — confirmed via this
investigation (no `totem`/`stockpile`/`palisade` string appears in `src/world/`,
`src/core/state.py`, or `src/core/updates.py` prior to this ticket). Any concrete tuning value
Plan/Implement choose must be explicitly flagged as provisional in both the ticket's Implementation
Notes and the mechanics doc update below — not presented as a balanced, tested constant.

### 3. New feature flag registration (`src/domains/optimization/feature_flags.py`)

Confirmed: `FeatureFlagManager.__init__`'s `_flags` dict (lines 13-177) is the canonical flag
registry, and every recent entry (`ENABLE_CREATURE_TERRITORY_LIFECYCLE`,
`ENABLE_REPRODUCTION_NATURAL_CREATURE_PATH`, etc.) follows the same comment convention: cites its
own ticket ID, states DEV-002's default-OFF policy applies, and names "no corpus profile turns this
on and no SHADOW-validation history exists." The new flag (proposed name:
`ENABLE_CAMP_NEST_SPREAD`, following the `ENABLE_<SUBJECT>_<VERB/NOUN>` shape of its siblings)
should be added at the end of the dict with the same comment shape, default `FeatureMode.OFF`.

**Important convention gap to resolve at Plan**: `camp.py` reads flags via the raw
`state.feature_flags` dict (`flags.get(KEY, "OFF") == "ON"`, string comparison), matching block 4's
existing precedent — it does **not** go through `FeatureFlagManager.is_enabled()`
(`FeatureMode`-typed). Registering the flag in `FeatureFlagManager._flags` is still required per
the ticket's explicit AC ("registered in `feature_flags.py`'s flag map"), for discoverability/
`serialize()`/`get_all_flags()` purposes, but the actual gate inside `process_camps()` must read
`state.feature_flags` directly (string `"ON"`), exactly mirroring block 4 — using
`FeatureFlagManager.is_enabled()` instead would be an inconsistent, untested pattern for this file.

## Mechanics / Engine Constraints

- `docs/mechanics/05_world_evolution.md` §6 "Calamities & World Threats" is the authoritative
  chapter for `CampService` behavior — verified via `docs/brainstorm/rpg_feature_atlas.html`'s own
  Documentation Cross-Reference table (ideas 45/46 → "Ch5 §2... world_dynamics.yaml... Topical,
  high confidence"). This section already documents three prior flag-gated `CampService`
  extensions (Creature Territory Lifecycle, Natural-Creature Reproduction, Magical/Demonic
  Reproduction) each as its own `###`-level subsection citing its own ticket ID — the new Nest
  branch must follow this exact established documentation shape (see Docs Requiring Update).
- `docs/world/raid_boss_camp_contract.md` — the `camp.py`-specific engine contract, verified
  directly. Documents growth (`maturity += 0.05/tick`, `x1.5` at `trauma_score > 50`), monster
  spawning (`max(2, int(maturity/10))`), raid trigger (`maturity >= 80`, partial reset to 50 — note:
  the doc says "resets to 50" but the actual code applies `maturity_delta=-20.0`, a relative delta,
  not an absolute set-to-50; from `maturity=80` these coincide, but from any higher pre-raid
  maturity they diverge — **pre-existing doc/code drift, not introduced by this ticket**, but worth
  flagging since the Nest branch's own doc description must be precise about using the identical
  relative `-20.0` delta, not "resets to 50," to avoid repeating the same imprecision). Also has its
  own "Extension rules" section (line 139-144) explicitly inviting "a new camp variant and growth
  rate" — the Nest branch is exactly the kind of extension this section anticipates, and per rule 1
  it states "Monster cap formula should remain `max(2, maturity/10)` unless the variant has a
  documented reason to differ" — this ticket's Nest branch does not touch the monster-cap formula
  (that's block 2, out of this ticket's scope per the Insertion Points anti-drift note above), so no
  documented deviation is needed there.
- **Authoritative Mechanics Rule / durable-state law** (project CLAUDE.md): new totem/stockpile/
  palisade values are durable per-camp state and must be typed fields on `CampState`/`CampUpdate`,
  never free-form `metadata`/dict storage — the ticket's own AC already mandates this; confirmed
  consistent with the Durable State Rule.
- **`CreatureTerritoryService` separation** (`src/world/creature_territory.py:13-20`): its own
  docstring explicitly states it is "a parallel service, not a shared refactor" to `CampService`,
  citing this exact ticket's Out of Scope. Confirmed: it operates on per-entity
  `IdentityComponent.territory_maturity`, entirely independent of `CampState.maturity` — no overlap
  risk with the Nest branch's camp-level maturity mechanism, but both mechanisms independently key
  off proximity to the same `state.camps` — a Nest-classified camp with
  `ENABLE_CREATURE_TERRITORY_LIFECYCLE` also ON would run both mechanisms simultaneously
  (uncoordinated, but each individually flag-gated and functionally independent — not a conflict,
  just worth naming as a real combinatorial case that exists once both flags are ever ON together).

## Docs Requiring Update

- `docs/mechanics/05_world_evolution.md`: add a new `###`-level subsection under §6 "Calamities &
  World Threats," immediately after "### Natural-Creature Reproduction," documenting the new Nest
  branch — trigger condition, flag name, spread-outcome mechanism, and the classification rule
  table (or a pointer to where the rule lives) — following the exact prose/structure shape of the
  three existing sibling subsections in that chapter (Creature Territory Lifecycle, Natural-
  Creature Reproduction, Magical/Demonic Reproduction).
- `docs/world/raid_boss_camp_contract.md`: the "Camp — `camp.py`" section's "Raid trigger"
  subsection must be updated to describe the new fork (Camp → raid outcome unchanged, Nest-
  classified + flag ON → spread outcome), and a new "Camp/Nest classification" note should be added
  (or a pointer to the classification rule) since this doc is the canonical `camp.py`-specific
  engine contract and currently describes only the single unconditional raid path. The "Extension
  rules" section (currently rule 1 only) should gain the Nest branch as a second documented
  precedent for future camp-variant extensions.
- `docs/parity_ledger/world_dynamics.yaml`: add a new entry (new `WORLD-1xx` id, following the
  existing `WORLD-118`/`WORLD-119` numbering for the most recent `CampService`/
  `CreatureTerritoryService` extensions) describing the Nest spread-outcome behavior, its flag gate,
  and `v2_evidence`/`test_path` pointing at the new test coverage — mirroring `WORLD-119`'s own
  shape exactly (`ENABLE_REPRODUCTION_NATURAL_CREATURE_PATH` entry, lines 1650-1728).

The `docs/parity_ledger/world_dynamics.yaml` WORLD-109 entry (path:
`docs/parity_ledger/world_dynamics.yaml`, under `docs/parity_ledger/`) is not required to change for
this ticket: its `camp_constructed` divergence note ("camps are pre-placed at world generation...
no dynamic construction") remains true after this ticket, since the Nest branch's spread outcome —
per the Insertion Points analysis above — spawns entities near an already-existing camp, it does not
construct a new `CampState`. This ticket does not change the fact WORLD-109 describes.

The `docs/mechanics/content_usage_matrix.md` `living/races` row (path:
`docs/mechanics/content_usage_matrix.md`, under `docs/mechanics/`) is not required to change: this
ticket reads existing `races.yaml` data to build a classification rule, it does not add a new
content family, change `races.yaml`'s schema, or alter `LivingDefaultsResolver`'s consumption of it
— the row's existing `RESOLVED_PARTIALLY` status and resolver/consumer wiring are untouched.

The `docs/plans/rpg_design_roadmap/rpg_m4_beyond_city_epic.md` epic doc (path:
`docs/plans/rpg_design_roadmap/rpg_m4_beyond_city_epic.md`, under `docs/plans/`) is not required to
change for this ticket: it is a scope-tracking plan doc, not a mechanics/parity source of truth: it
already correctly names the goblin-contradiction and 5-race gaps as open items for this ticket to
resolve, and resolving them does not itself require editing the epic doc's own prose (the epic doc
gets updated when child tickets are formally cut from it, which is a separate create-tickets-phase
concern, not this investigation's).

## Parity Ledger Overlap

- **WORLD-109** (`world_dynamics.yaml:1384-1420`, status `verified`, priority `P1`): `camp_constructed`
  blocked, "camps pre-placed at world generation." Confirmed still true and unaffected — see Docs
  Requiring Update above. No status change.
- **WORLD-118/119** (`world_dynamics.yaml:1629-1728`): Creature Territory Lifecycle and Natural-
  Creature Reproduction entries — both are the direct structural precedent for the new Nest entry
  this ticket must add (same file, same section, same "behind `ENABLE_X` (default OFF)..." shape).
  Neither entry's own status changes; the new Nest branch is additive.
- **WORLD-030/031** (`world_dynamics.yaml:373-384`, "Camp reinforcements occur on schedule" /
  "Camp reinforcement level increases when camp is full"): these describe the existing garrison-
  spawn block (block 2), which this ticket does not touch (see anti-drift note above) — no status
  change expected, but worth flagging since they're the closest pre-existing entries to the area
  being extended, so a Verify-phase reviewer should confirm they still pass unmodified.
- No `P0`-priority entries were found touching `CampService`/`CampState`/races.yaml classification
  in a search of `world_dynamics.yaml` — no `test_path`-required P0 gate applies to this ticket's
  scope specifically (WORLD-109 is P1).

## Prior Work

- `stored_artifacts/TCK-20260902-REPRODUCTION-NATURAL-CREATURE-PATH/` (done) — the direct structural
  precedent for adding a fourth/fifth additive branch to `process_camps()`: flag-gated via the raw
  `state.feature_flags` dict, parentless offspring via `EntityGenerator.spawn_*` methods, additive
  `WorldUpdate` merge pattern for population signals, and an explicit "does not reference Genetics"
  behavioral-form guard test. This ticket's Nest branch should mirror this precedent's test-writing
  shape closely (see test_plan.md).
- `stored_artifacts/TCK-20260831-CREATURE-TERRITORY-LIFECYCLE/` (done) — establishes the
  `docs/mechanics/05_world_evolution.md` §6 subsection documentation pattern this ticket must
  follow, and is the source of the explicit "parallel service, not a shared refactor" framing this
  ticket's investigation reconfirmed for `CreatureTerritoryService`.
- `stored_artifacts/TCK-20260831-RACE-RELATIONS-MATRIX/` (done) — the closest prior race-
  classification-adjacent ticket (`data/content/living/races.yaml`-driven logic). Its
  investigation.md's Docs Requiring Update section format (Format 1 bullets vs. Format 2 prose-only
  exclusions, both used correctly) was used as the direct template for this investigation's own
  Docs Requiring Update section.
- `tickets/todos/m4-place-material-expansion/TCK-20260904-LAIR-ENTITY-ANCHOR.md` (open, sibling
  ticket in the same M4 batch) — confirmed its own Scope explicitly excludes "Any change to
  CampService/Camp-Nest classification (C1)," and this investigation confirms the converse: dragonkin
  is excluded from this ticket's classification precisely because it belongs there instead.
- `tickets/todos/m4-place-material-expansion/TCK-20260904-CAMPSTATE-PLACE-BRIDGE.md` (open, sibling
  ticket) — confirmed its own Out of Scope excludes "The City/Camp/Nest race classification decision
  itself... this ticket consumes that decision's output" and "Any change to the Nest spread-outcome
  mechanism or new typed Camp/Nest feature fields (totem/stockpile/palisade) — those are
  `TCK-20260904-CAMP-NEST-CLASSIFICATION`'s scope" — confirms this ticket's scope boundary from the
  other side, and its own investigation note ("No production code currently constructs `CampState()`
  at all") was directly reused above to justify not creating new `CampState` instances in the Nest
  spread outcome.

## Risks and Open Questions

- **Blocking-if-wrong**: the exact spread-outcome mechanism (spawn N parentless offspring? increase
  a new "population" concept? something else?) is not specified by the ticket text beyond "spread/
  population-growth outcome" — this investigation recommends reusing
  `spawn_natural_creature_offspring` as the lowest-risk, precedent-consistent choice, but Plan must
  make this an explicit, stated decision, not an assumed default.
- **Design choice, not blocking**: whether Nest-vs-Camp is keyed off the existing `CampState.kind`
  string (recommended above, reuses existing field) or a new explicit typed field — both are
  architecturally valid; Plan should pick one and state why, since it affects both the `CampUpdate`
  shape and how `TCK-20260904-CAMPSTATE-PLACE-BRIDGE` will eventually bridge `CampState`↔`PlaceState
  (kind=CAMP/NEST)`.
- Totem/stockpile/palisade magnitudes are genuinely unanchored (confirmed via full-codebase check);
  any numeric default chosen (e.g. `stockpile` accrual rate, `palisade_integrity` effect on raid/
  spread mechanics) must be flagged provisional in both code comments and the mechanics doc — do not
  present as tuned/balanced.
- The `docs/world/raid_boss_camp_contract.md` "resets to 50" vs. actual `maturity_delta=-20.0`
  drift (noted above) is pre-existing, not introduced by this ticket, but the new Nest documentation
  added to that same file must not repeat the imprecision — describe the delta correctly.

## Anti-Drift Hazards

- Do not extend the garrison-spawn block (block 2, `camp.py:46-63`)'s goblin/orc binary to the new
  Nest race kinds unless strictly required for the spread outcome to be observable — that block is
  explicitly out of this ticket's AC (which is scoped to the maturity-threshold trigger fork).
- Do not let the Nest branch bypass the existing 500-tick `last_raid_tick` cooldown check — the
  ticket explicitly requires reusing the same timing constants; a Nest branch with its own
  independent cadence would silently diverge from "reuses `MATURITY_PER_TICK`/
  `RAID_MATURITY_THRESHOLD` for timing."
- Do not construct a new `CampState` instance anywhere in the Nest branch — this ticket's Out of
  Scope explicitly forbids assuming a live seeded Camp exists at compile time, and WORLD-109's
  divergence note (no dynamic camp construction) must remain true after this ticket.
- Do not route the new flag check through `FeatureFlagManager.is_enabled()` — the one existing
  precedent in this exact file (block 4) reads `state.feature_flags` directly as a string dict; a
  mixed convention within the same function would be an inconsistency worth avoiding.
- Do not silently skip updating `CampState.to_canonical_dict()` when adding the three new fields —
  this is the canonical-hash/replay serialization path; a field present on the dataclass but missing
  from this dict is a real, easy-to-miss silent bug (already exists as a real risk pattern in this
  exact file's history — the dict is manually maintained, not auto-derived from `dataclasses.fields`).
- Do not conflate this ticket's classification rule with `CreatureTerritoryService`'s per-entity
  `territory_maturity` mechanic — confirmed structurally independent; extending or referencing that
  service is explicitly out of scope per the ticket's own Out of Scope section.
