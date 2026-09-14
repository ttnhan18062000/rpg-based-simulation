---
status: active
layer: world
authority: P1
audience: agent
tags: [faction, world]
---

# Faction War Drivers — Design Proposal (DRAFT, NOT CERTIFIED)

**This is a proposal, not yet-built mechanics. No code has been written against this document.**
Per explicit instruction: peer review required before any implementation. Once approved and built,
the verified formulas belong in `docs/systems/faction_contract.md` (the living, parity-ledger-backed
contract for this subsystem) — this file is the review artifact, not the destination.

> **User's decision (2026-09-15), stated here first so it can't be missed**: **ship faction
> sentiment now, without importance weighting; the military-strength driver comes next, as its own
> separate piece of work.** Two consequences, both real, both intentional:
> - **Importance weighting is cut from this build**, not deferred quietly. The only real signal
>   found (`public_reputation`) has a structural 2× ceiling that does not widen with more play
>   (measured, §3.2.4) — too weak to express what the design actually wants (a leader's actions
>   reading as categorically different from an ordinary entity's). Rather than ship a near-invisible
>   multiplier, it's cut, and a real importance signal (faction leadership/rank/standing — genuine
>   new design, none exists today) is scoped as its own separate initiative:
>   `TCK-20260915-FACTION-IMPORTANCE-SIGNAL-INITIATIVE` (scoping only, not built).
> - **This design reaches `TENSE`/`HOSTILE` reliably. It does not reach `WAR`.** Loop #1
>   (`military_strength`, frozen at `1.0`) is untouched by sentiment and remains genuinely open —
>   see §3.3/§3.6. Sentiment ships on its own real merits (tension, diplomacy, a trade extension
>   point), not as a complete war-declaration system. Full detail in §4.

> **Post-build finding (2026-09-15), stated as plainly as the gap above**: shipped sentiment
> reliably reaches `TENSE`. **`HOSTILE` has NOT been shown to reach organically post-fix** — a real
> 9000-tick run against unmodified `frontier_living_world` shows `pairwise_tension` for the one
> real interacting pair plateauing at `0.418` against the `0.7` `HOSTILE` threshold, never
> approaching it. An earlier pre-fix run did reach `HOSTILE` for this same pair, but that run's
> mechanism (`tension_level` as an ambient per-faction scalar misread as pairwise tension) was a
> confirmed defect and has been removed — that observation is **no longer representative of
> current behaviour** and should not be cited as evidence `HOSTILE` is reachable. Filed as a
> follow-up: `TCK-20260915-SENTIMENT-HOSTILE-THRESHOLD-REACHABILITY` — same shape as the D-05/
> maturity-gate pattern this week (a mechanism gated behind a value real play doesn't approach).
> Also: `RESOURCE_DEPLETED` (`faction_decision.py`) now feeds only goal-priority scoring, not
> `DiplomaticStateMachine` — it was already dead there (its territory gate never fired), so nothing
> real is lost, but it is no longer a route into diplomatic tension at all; anyone later wanting
> "resource competition raises war risk" needs to route it through `pairwise_tension` with a named
> rival, not the ambient scalar.

Ticket: `TCK-20260914-FACTION-WAR-DECLARATION-DESIGN-QUESTION`. Full investigation evidence:
`stored_artifacts/TCK-20260914-FACTION-WAR-DECLARATION-DESIGN-QUESTION/investigation.md` (once
moved) / `staging_artifacts/.../investigation.md` (current).

## 1. Problem, restated

`DiplomaticStateMachine.compute_transitions()` is a real, wired, correctly-implemented 4-step
diplomatic state machine — but every precondition past the first rung is structurally unreachable:

1. `military_strength` never diverges from its `1.0` default before war (the only producer is a
   WAR-exhaustion drain that requires war to already exist).
2. `territory` can only be gained *by* a war (siege-won transfer requires an existing WAR).
3. `tension_level`'s only real runtime producer is gated on territory, so it's blocked by #2 too.

**The war system can only be entered from a state that only war produces.** User's decision: build
real pre-war drivers — militaries diverging and tension rising from actual world conditions, not
authored starting positions. This document proposes how, reusing existing live systems wherever a
real one exists, and states plainly where none does.

## 2. Reuse-before-invention: what already exists

### 2.1 Does faction→region ownership already exist? — Partially yes, with a real gap

`docs/mechanics/regional_sovereignty.md` (Certified) and `RegionState.owner_faction_id: Optional[int]`
are real and live: death-triggered influence deltas (`FactionInfluenceService.process_influence_shift()`,
`src/world/influence.py`) correctly classify the *specific* dying/killing entity's real faction via
`FactionSemanticsService.is_invader()`/`is_protector()`, which reads each catalog faction's own
`alignment_bucket` (`defender`/`invader`/`neutral`) — a genuine per-faction classification covering
all ~16 real factions, not just two.

**The gap**: the resulting ownership write collapses that specific-faction identity into the legacy
4-value `Faction` enum (`HERO_GUILD`/`MONSTER_HORDE`/`TOWN_COUNCIL`/`NEUTRAL`) —
`owner_faction_id_set = Faction.MONSTER_HORDE`, always, regardless of which real catalog faction
(`orc_clan`, `goblin_warband`, `dragon_cult`, ...) actually caused the conquest. This is a **known,
already-documented limitation** — `docs/systems/faction_contract.md`'s own FAC-010 note: *"The
int/str type mismatch [between `RegionState.owner_faction_id: Optional[int]` and
`FactionState.faction_id: str`] is a known limitation."* Territory transfer (siege-won) already
writes to the correct place (`FactionState.territory`, string-keyed) — only the *influence-driven*
conquest path collapses identity.

**Taxation reuses the same collapsed identity** (`src/engine/town_resolution.py`): vault keys are
`f"faction_{Faction(fid).name.lower()}_gold"` — literally `faction_hero_guild_gold`,
`faction_monster_horde_gold`, etc. Confirmed only 4 buckets, never a real catalog faction id.

**Verified reachability, split by path**:
- **Static (compile-time) ownership is real, reachable, and already produces income.** In a real
  3000-tick run (`urban_political`, seed=42), `hometown`/`trading_hometown` were pre-authored at
  compile time with `owner_faction_id=Faction.HERO_GUILD`, `influence=100.0`. `faction_hero_guild_gold`
  grew from a 1000 baseline to `5708.00` over the run — real, live taxation income.
- **Dynamic (influence-driven) conquest/liberation is CONFIRMED unreachable, not just unverified.**
  §5's follow-up check ran the same probe across four real corpus worlds (`urban_political`,
  `frontier_living_world`, `dungeon_crawl`, `generated_frontier_3_42`), 3000 ticks each — 12,000
  combined real ticks. **`region.owner_faction_id` never changed once, for any region, in any of
  the four worlds.** Every unowned "wild" region (`goblin_camp`, `bandit_road`, `old_mine`, etc. —
  regions independently confirmed elsewhere this batch to have real combat, via `trauma_score`
  movement) showed `influence` staying at exactly `0.0` for the entire run, in all four worlds —
  not slow, not partial, exactly zero movement. The only nonzero influence anywhere was the two
  regions with compile-time-authored ownership, pinned at their starting `100.0` and never moving
  further either.

  Traced the classification path by hand to rule out an obvious cause: `EntityGenerator.spawn_monster()`
  sets `identity.faction=Faction.MONSTER_HORDE` (no `identity.properties["faction_id"]`), so
  `get_faction_id_str()` returns `"monster_horde"`; `FactionSemanticsService.get_alignment_bucket()`
  finds no catalog entry literally named `"monster_horde"`, falls back to
  `get_legacy_faction_bucket()`'s string-matching heuristic, and correctly resolves `"invader"` —
  classification *should* work for the death of an ordinary spawned monster. `recent_deaths`
  collection in `lifecycle.py::resolve_lifecycle()` has no role/kind filter that would exclude
  monsters either. The actual root cause was not chased further here (time-boxed — this is now a
  separate reachability defect from the one this ticket investigates, filed as its own follow-up:
  `TCK-20260914-REGIONAL-INFLUENCE-SHIFT-NEVER-FIRES`). **This changes §3.3's (the military-strength
  driver's) confidence level from "unverified" to "known-broken prerequisite"** — see the updated
  table in §3.5.

### 2.2 What could make military strength diverge? — Vault gold is real; region-count is unverified

Reusing the taxation/vault system (§2.1) once specific-faction identity is fixed gives a real,
already-partially-live economic signal per faction. `FactionState.resources: Dict[str, int]` exists
on the dataclass but has **zero real producers** (confirmed via grep — not wired to anything;
`AuthoritativeState.global_resources` is the real, live vault, not this field). `RegionState.population_cohorts`
exists and is real per-region demographic data, but is not evaluated in this pass — flagged as a
possible future input, not proposed here, to avoid the exact failure mode peer warned about (a
formula built on entity/cohort-level data that turns out uniform across the real corpus, the way
the prior perceived-power draft found every entity at level 1). Region-count-controlled is
plausible in principle (more territory → more military weight) but its own real producer (§2.1's
dynamic conquest path) is now confirmed unreachable, not just unverified — proposing it as an input
would inherit that same confirmed-dead reachability, not a new open question.

### 2.3 Would fixing territory alone unblock tension? — Yes, no new mechanism needed

`FactionAwarenessService.compute_tension_updates()` (`src/engine/faction_decision.py:221-245`) is
already correct and complete: `+0.1` tension per `RESOURCE_DEPLETED` WorldEvent inside
`fs.territory`. It is blocked *only* by `territory` always being empty. **Fixing §2.1's identity
gap so factions actually receive `FactionState.territory` entries makes this producer start working
with zero new code.** This is the cleanest win in this whole proposal — a real, already-correct
mechanism currently starved of its one input.

## 3. Proposed design

### 3.1 Close the identity gap (breaks loop #2 territory, and #3 tension for free)

Add a new field carrying the *specific* catalog faction id alongside the existing legacy int field
— **do not change `RegionState.owner_faction_id`'s type**, given its wide consumer surface
(`town_resolution.py`, `quest_engine.py`, `quest_generator.py`, `metrics.py`,
`state_presenter.py`, `replay/fingerprint.py`, `event_extractor.py`/`event_shapers.py` — all
confirmed via grep). A parallel field keeps every existing consumer's behavior byte-identical and
scopes the new behavior to exactly the code that needs specific-faction identity.

Proposed: `RegionState.owner_faction_id_str: Optional[str] = None`, populated in
`FactionInfluenceService.process_influence_shift()` from the same `get_faction_id_str(entity)` call
already made on each death event (currently used only to classify protector/invader, then
discarded) — no new classification logic, purely recording what's already computed.

A new, small reconciliation step (run once per tick, or on `owner_faction_id_str` change) derives
`FactionState.territory` for the owning faction: add the region to the new owner's `territory`,
remove it from any prior owner's. This is additive to the existing siege-transfer path
(`FactionUpdate.territory_add`/`territory_remove`), not a replacement — both paths write to the
same authoritative field.

**This one change is sufficient to make `shared_territory` (loop #2) reachable, and — because
`compute_tension_updates()` already reads `fs.territory` correctly — simultaneously unblocks organic
tension growth (loop #3) with no separate mechanism.**

### 3.2 Faction sentiment — the tension driver (breaks loop #3 directly, independent of territory)

**User's design, given after reviewing §3.1's own territory fix**: a continuous faction-to-faction
sentiment, scaled hostile ← neutral → friendly, serving *all* faction-level interaction — trade and
diplomacy as much as war — not a war-only mechanism. It builds from real entity interaction
("almost like entity-to-entity"), and it must be the real pre-war producer this whole investigation
has been looking for — one that doesn't itself require war, or even territory, to exist first.

**Scope note (2026-09-15, after the importance-signal finding below)**: the design's original third
requirement — weighting by the acting entity's importance to their faction — is **not built in this
pass**. §3.2.4 found no real signal strong enough to carry it; rather than ship a knob that barely
turns, it's cut and scoped separately (`TCK-20260915-FACTION-IMPORTANCE-SIGNAL-INITIATIVE`). What
follows describes the sentiment mechanism as it will actually ship: real, uniform per-event
magnitude, not yet weighted by who acted.

#### 3.2.1 Reuse check: mirror `SocialBond`, don't invent a new relationship shape

`SocialBond` (`src/core/models/social.py:14`) is the directed, per-target relationship record this
codebase already uses at entity scale: `target_id`, `familiarity: float` (0→1, interaction depth),
`sentiment: float` (−1→+1, liking/hostility), `last_interaction_tick: int`, `role:
RelationshipRole`. `RelationshipService.process_update()` (`src/systems/social_systems/
relationships.py`) is its real, live, tested apply-path — clamps sentiment to [−1, 1], promotes
`role` to `FRIEND`/`RIVAL` at `FRIEND_SENTIMENT_THRESHOLD = 0.8` / `RIVAL_SENTIMENT_THRESHOLD =
-0.8` (itself mirroring `appraisal.py`'s own `TOTAL_DISTRUST` extreme-sentiment precedent), and
never demotes a role on a partial swing.

**Proposed**: `FactionSentiment` — same four data fields as `SocialBond` (`target_faction_id: str`,
`familiarity: float = 0.0`, `sentiment: float = -1.0..1.0 = 0.0`, `last_interaction_tick: int = 0`),
stored as `FactionState.faction_sentiments: Dict[str, FactionSentiment]`, mirroring
`SocialComponent.bonds: Dict[int, SocialBond]` exactly — same shape, same clamping rule, same
apply-path pattern (a new `FactionSentimentService.process_update()`, not a reinvention of
`RelationshipService`, but a direct structural copy of it at faction scope).

**One deliberate deviation from the mirror, flagged for review rather than decided silently**: no
`role` field on `FactionSentiment`. At faction scope, `FactionState.diplomatic_relations[target]`
(the existing `DiplomaticState` enum — `NEUTRAL`/`TENSE`/`HOSTILE`/`WAR`/`ALLIED`/`VASSAL`) already
plays the exact categorical role `SocialBond.role` plays at entity scope. Adding a second,
independent categorical tag on `FactionSentiment` would be a real, avoidable duplication — a third
source of truth for "how do these two factions relate," on top of the continuous `sentiment` score
and the discrete `diplomatic_relations` state. This arc has already deleted seven parallel
implementations of the same idea; a redundant role tag would risk becoming an eighth. If peer/user
wants a lightweight categorical read independent of `DiplomaticState` for some reason not yet
identified, say so — but the default here is to not add it.

#### 3.2.2 Scale and meaning, stated explicitly

- `sentiment`: −1.0 (total hostility) to +1.0 (total friendship), 0.0 = neutral/unknown, matching
  `SocialBond`'s own range exactly — no new scale invented.
- `familiarity`: 0.0 (factions have never meaningfully interacted) to 1.0 (extensive shared
  history), same meaning and range as `SocialBond.familiarity`.
- Real, already-established boundary semantics to reuse rather than invent: `sentiment >= 0.8` reads
  as a friendly-enough relationship for future alliance/trade-preference logic to key off; `sentiment
  <= -0.8` reads as hostile enough that trade should refuse and diplomacy should treat this pair as
  primed for `HOSTILE`. These mirror `RelationshipService`'s own `FRIEND_SENTIMENT_THRESHOLD` /
  `RIVAL_SENTIMENT_THRESHOLD` (0.8 / -0.8) exactly — the same number, not a new one, at the layer
  above.

#### 3.2.3 What moves it, by how much, and in which direction — reusing the real interaction stream, not a new one

`SocialBondUpdate` (`src/core/updates.py`) is the single real choke point every entity-level
interaction system already writes through — confirmed via grep, exactly three real producers exist:
`src/engine/combat.py` (`sentiment_delta=-0.1, familiarity_delta=0.05` on a hit — hostile),
`src/systems/social_systems/contracts.py` (bidirectional `sentiment_delta`/`familiarity_delta` on
contract completion — cooperation/trade), `src/systems/social_systems/appraisal.py` (three further
real sites). All three flow into `RelationshipService.process_update()` per-entity.

**Proposed integration — one new phase, zero changes to the three producer systems**: after
`RelationshipService` resolves the tick's `bond_updates`, a new, small
`FactionSentimentDerivationPhase` scans the same tick's already-produced `SocialBondUpdate` list.
For each `(source_entity_id, bond_update.target_id)` pair where `bond_update.sentiment_delta != 0`,
resolve both entities' real faction via `get_faction_id_str()` (`src/content_semantics/faction.py`
— the same reuse-friendly helper §2.1 already found and traced). If the two factions differ, emit a
scaled `FactionUpdate(faction_sentiment_delta={target_faction: bond_update.sentiment_delta *
FACTION_SCALE_FACTOR, ...})` for both factions (symmetric, like the entity-level bond updates
themselves are effectively symmetric in `contracts.py`). `FACTION_SCALE_FACTOR` is a single fixed
constant (not per-entity — importance weighting is explicitly cut, see the scope note above),
proposed at `< 1.0` purely so one entity-level interaction doesn't swing faction-wide standing as
hard as it swings the two entities' own bond — a real, if provisional, dampening value still needs
picking, not a design decision made here. No existing system needs to know anything about
factions — combat, cooperation, and appraisal stay exactly as they are; the new phase derives
faction consequences from data they already produce.

This directly answers "what moves it": the same real events that already move entity-level
sentiment (a hit, a completed or defaulted contract, an appraisal outcome) — scaled down and
attributed to the acting entities' factions, not invented from scratch.

#### 3.2.4 Importance weighting — investigated, found unsupported, cut from this build

**Rule applied throughout this section, worth stating on its own**: any field proposed as a
discriminator must be measured for real spread before a design leans on it — not assumed reasonable
because it exists and is live. This is the second time this exact class of mistake nearly happened
in this arc (the first: the earlier perceived-power draft assumed entity level would discriminate,
and found every one of 214 corpus entities at level 1). Two instances make it a pattern to check
for by default, not a one-off lesson.

Every real candidate was checked against real data rather than assumed, and none survived:

- **`public_reputation`** (`SocialComponent.public_reputation: float = 1.0`, range 0.0–2.0) — real,
  live, and *not* pinned at the default (confirmed non-degenerate: measured across a real 3000-tick
  run, `urban_political`, seed=42, 49 entities alive at end — min=1.000, max=2.000, mean=1.232, 8
  distinct values). **But the spread itself is narrow, and does not widen with more play.**
  Checked explicitly across a longer 5000-tick run at ten checkpoints (every 500 ticks): `min` and
  `max` are pinned at exactly `1.000`/`2.000` — the field's own hard floor/ceiling — at **every**
  checkpoint from tick 500 through tick 4999, with `spread (max−min)` reading exactly `1.000` the
  entire time. Mean actually drifts *down* over the run (1.335 → 1.145) as new low-reputation
  spawns dilute the average, not because the range narrows or widens. The most important entity in
  the world can count at most 2× a nobody, and that ceiling is structural — it does not loosen
  given more real play. Against real interaction volume, a 2× multiplier would be close to
  invisible.
- **`veterancy_rank`** (`EntityState.identity.veterancy_rank: int = 0`) — real, live producer exists
  (`VeterancyService.process_points()`, driven by `veterancy_points_delta`), **but confirmed
  degenerate in the same real run**: every one of the 49 alive entities was at `veterancy_rank = 0`
  — the exact failure shape from the earlier perceived-power draft (every entity reading as
  identical because all 214 corpus entities were level 1).
- **`EntityRole`** (HERO/SHOPKEEPER/MONSTER/CITIZEN/WORKER/GUARD) and **faction leadership** — no
  real "leader" designation exists for `FactionState` at all. `ClanState.leader_entity_id` exists
  but is schema-only, with zero real producers (a *different*, unrelated concept — Clan, not
  Faction). `EntityRole` has no `LEADER` tier.

**Decision (2026-09-15): cut, not accommodated.** The design wants a leader's action to read as
categorically different from an ordinary entity's — not double it. No signal available today can
express that, and shipping the weak `public_reputation` knob anyway would be exactly the shape this
arc has spent all week deleting: a mechanism that exists and does essentially nothing. Sentiment
ships as a uniform, unweighted signal (§3.2.3's `FACTION_SCALE_FACTOR`, applied the same regardless
of which entity acted) for this pass. A real importance signal — who holds standing in a faction,
who speaks for it, how that's acquired — is genuine new design, not reuse, and is scoped as its own
separate initiative rather than folded in here: `TCK-20260915-FACTION-IMPORTANCE-SIGNAL-INITIATIVE`
(filed, scoping only, not blocking this build). Once it lands, wiring its output into
`FactionSentimentDerivationPhase`'s scale factor is a small, later change — sentiment's own design
doesn't need to be revisited to add it.

#### 3.2.5 Decay — no live precedent found, proposed as new (flagged as such)

Checked for an existing, currently-used decay mechanism for a similarly-shaped directed value to
mirror rather than invent. The one comparable past attempt (`KnowledgeFact.effective_certainty()`,
a decay function for belief certainty) was found abandoned and deleted earlier this arc
(`TCK-20260909-KNOWLEDGE-FACT-EFFECTIVE-CERTAINTY-DEAD-CODE-DISPOSITION`) — a cautionary precedent,
not a reuse target. No other live decay mechanism for a `[-1, 1]` or `[0, 1]` relationship-shaped
value was found in this pass.

**Proposed, explicitly as new work, not reuse**: once per `SEASONAL_PROPAGATION_INTERVAL`-scale
cadence (500 ticks — reusing `CalamityPressurePropagator`'s own real cadence constant rather than
inventing a new tick interval, since it's the closest real precedent for "a periodic, slow-moving
world-level drift"), for every `FactionSentiment` where `current_tick - last_interaction_tick >
SOME_STALENESS_THRESHOLD`, drift `sentiment` a fixed fraction back toward `0.0` (e.g.
`sentiment *= 0.9` per interval past staleness — a placeholder, not a proposed final value).
`familiarity` does not decay in this proposal (interaction depth is memory, not standing — mirrors
`SocialBond.familiarity` itself, which has no real decay producer either). This is the one genuinely
new mechanism in this design; flagged as such rather than presented as reuse it isn't.

#### 3.2.6 What a trade decision and a war decision each read

- **War** (indirect, via the existing wired machinery, untouched): negative `faction_sentiment_delta`
  swings additionally emit a proportional `FactionUpdate(tension_delta=...)` — reusing the
  already-real, already-tested `tension_delta` field `apply.py` clamps into `FactionState.
  tension_level`, which `DiplomaticStateMachine.compute_transitions()` already reads unchanged
  (`pair_tension = max(fa.tension_level, fb.tension_level) > 0.4` / `> 0.7`). **No change to the
  state machine itself** — it stays exactly as verified by `FAC-006`'s parity-ledger entry. Positive
  sentiment swings can symmetrically emit a small negative `tension_delta`, mirroring the existing
  peace-making diplomatic actions' own `-0.1`/`-0.15` pattern (`diplomatic_actions.py`).
- **Trade** (direct, a real but not-yet-built extension point): `FactionDecisionPhase`'s existing
  `TRADE_ROUTE` directive (`military_strength > 0.7 AND tension_level < 0.3`) currently checks a
  faction's own general stability, not its standing with any specific counterpart. Once
  `FactionState.faction_sentiments` exists, a natural, real extension (not proposed as built here)
  is gating trade/alliance proposals toward a *specific* target faction on
  `faction_sentiments.get(target_id).sentiment > THRESHOLD` — the continuous, per-pair signal this
  design adds is exactly what a "do we trust this specific faction enough to trade with them"
  decision needs and currently has no way to express.

### 3.3 Military strength driver (breaks loop #1) — provisional formula, needs review, unaffected by §3.2

**Stated plainly: §3.2's sentiment design does not address loop #1.** Sentiment is a relational
signal (how much do these two factions like each other); `military_strength` is meant to represent
raw military capability, a different and independent axis. Conflating the two — letting warm
relations directly inflate or shrink a faction's own army — was considered and rejected as
thematically incoherent, not proposed here. Loop #1 remains genuinely open and is addressed below,
unchanged from the prior draft of this proposal.

Reusing §2.1's now-fixed per-faction vault gold (`faction_{faction_id}_gold` in
`global_resources`, once §3.1's identity fix also extends to the taxation key — a small, same-shape
change to `town_resolution.py`'s `faction_keys` construction):

```
military_strength = clamp(0.2, 3.0, 1.0 + LOG_SCALE * log10(max(1.0, vault_gold / BASELINE_GOLD)))
```

Sketch only — `LOG_SCALE`/`BASELINE_GOLD` are placeholders, not proposed values; a log scale is
suggested so a faction with 10x the gold isn't 10x the military strength, matching the format of
other real multiplier tables in this codebase (e.g. `DIFFICULTY_TIERS`'s own sub-linear growth).
**This needs real-run calibration once vault gold is confirmed to actually diverge meaningfully
between multiple factions** — with `owner_faction_id_str` wired, at minimum two real factions (not
just the legacy Hero Guild/Monster Horde pair) need to hold territory and generate divergent income
for this formula to produce a real, non-degenerate `military_strength` spread. That is unverified
until §3.1 lands and a real run is measured against it — flagged explicitly rather than assumed.

### 3.5 Which loop each driver breaks

| Driver | Loop broken | Confidence |
|---|---|---|
| §3.2 faction sentiment → `tension_delta` | #3 (`tension_level`) | **High, and direct.** Real entity-interaction producers (combat, cooperation, appraisal) already exist and are live; the new derivation phase is the only new code, and it feeds the already-tested `tension_delta`/`DiplomaticStateMachine` path unchanged. Does not require territory (§3.1) to be fixed first — a genuinely independent pre-war producer. |
| §3.1 identity fix → `FactionState.territory` derivation | #2 (`shared_territory`) | High — reuses a fully-live classification path; only the write-side collapse is new work |
| §3.1 (same fix, free) → tension accrual unblocked (secondary path) | #3 (`tension_level`) | High, but now redundant with §3.2 above for the tension loop specifically — kept as a second real producer, not required for #3 to be broken |
| §3.3 vault-gold-driven `military_strength` | #1 (`military_strength` imbalance) | **Low, pending a separate fix.** §2.1's dynamic-conquest path is now confirmed unreachable (12,000 real ticks across 4 worlds, zero ownership changes) — `TCK-20260914-REGIONAL-INFLUENCE-SHIFT-NEVER-FIRES` must land first, or this driver has no real per-faction signal to read beyond the two legacy Hero Guild/Monster Horde buckets that happen to be statically pre-owned in most worlds. **Not addressed by §3.2's sentiment design at all** (see §3.3's own opening note) — loop #1 is the one genuinely unresolved loop in this entire proposal. |

### 3.6 What stays circular / open, stated plainly

- **Loop #1 (`military_strength`) has no confirmed-working driver in this proposal.** §3.2's
  sentiment design deliberately does not touch it (a relational signal is the wrong shape for raw
  military capability). §3.3's vault-gold sketch remains blocked on a separate, unresolved ticket.
  If the user wants loop #1 addressed in the same pass as sentiment, that's a real open design
  question this proposal does not answer — flagged rather than glossed over.

- **Dynamic (influence-driven) conquest is now confirmed to never fire for any faction in a real
  run** (§2.1, §5) — this is no longer an open question but a second, separate reachability defect
  sitting directly underneath §3.3's proposed `military_strength` driver (not §3.2's sentiment
  driver, which does not depend on it). Filed as its own ticket
  (`TCK-20260914-REGIONAL-INFLUENCE-SHIFT-NEVER-FIRES`) rather than folded into this design, since
  it's a distinct mechanism (`FactionInfluenceService.process_influence_shift()`) with its own root
  cause still to be found. **§3.3 should not be built until that ticket resolves** — building a
  military-strength formula on top of a per-faction signal that structurally cannot diverge (since
  only the two legacy Hero Guild/Monster Horde vaults ever move, via static pre-authored ownership,
  never any of the other ~14 factions) would reproduce this exact ticket's own root problem one
  layer down.
- **Vault-gold divergence between the ~14 non-Hero/Monster factions specifically has never been
  measured, and per the above, currently cannot be** — the one real growth observed in this
  investigation (`faction_hero_guild_gold`: 1000→5708) came entirely from compile-time-authored
  static ownership, not any dynamic path.
- This proposal does not address `EntityGenerator.spawn_stronghold()`'s own maturity-scaled stat
  term (flagged in the sibling maturity-gate ticket, D-05) — out of scope here, unrelated mechanism.

## 4. "War actually works end-to-end" — the acceptance bar, stated before any code lands

Per the lesson carried forward from the maturity-gate ticket: a declared WAR is not the finish
line. Sieges, territory transfer, and `EXPAND_TERRITORY` (`src/engine/military_conflict.py`) are
all downstream, live, wired code that has — per D-06's own original finding — **never actually run
in a real corpus episode**, because no WAR has ever been declared. Once war becomes reachable,
treat that code as unverified, not proven, exactly as the maturity-gate ticket found real defects
(tier-5 stat fallback, unregistered loot) waiting behind a gate nobody had ever opened.

**The real acceptance bar for this design, once built**: one real, unmodified corpus-world run
where all of the following are observed, not just constructed in isolation:
1. At least one real faction pair's `sentiment` moves meaningfully negative from real entity
   interactions (not hand-set), and the pair is observed to reach `TENSE`, then `HOSTILE`, via
   `DiplomaticStateMachine.compute_transitions()` under real, unmodified thresholds.
2. At least one real faction pair's `military_strength` diverges meaningfully from the `1.0`
   default — **this criterion is currently unsatisfiable** until §3.3's own blocker
   (`TCK-20260914-REGIONAL-INFLUENCE-SHIFT-NEVER-FIRES`) resolves, since no confirmed-working
   driver for it exists in this proposal (§3.6). Stated honestly rather than glossed over: **this
   design can be expected to reliably reach `HOSTILE` and then stall there**, never reaching `WAR`,
   until loop #1 gets its own real driver. That is a real, known gap in this proposal, not an
   incidental one.
3. Given #2's gap, at least one real faction pair reaching `WAR` itself should be treated as a
   stretch goal for this specific proposal's own end-to-end proof, not assumed — it depends on
   loop #1 being solved separately.
4. If `WAR` is reached: a siege actually starts, progresses, and completes
   (`MilitaryConflictPhase.execute()`) with a real territory transfer and a real
   `TERRITORY_TRANSFERRED` WorldEvent; `EXPAND_TERRITORY` (if it depends on the transferred
   territory) is checked for whether it actually fires correctly with genuinely-transferred
   territory, not just idle code; and the eventual `WAR → NEUTRAL` exhaustion transition is
   observed to fire correctly too, closing the loop, not just the opening half.

Declaring victory at reaching `HOSTILE` alone, or at "a war was declared" without checking what
happens next, would each separately repeat the exact mistake this arc has spent all week
correcting — this design closes loop #3 cleanly but does not, by itself, close the gap between
`HOSTILE` and a functioning war.

## 5. Verification done before sign-off (was: "immediate next step")

Checked whether `RegionState.owner_faction_id` (dynamic path) ever flips for a non-pre-authored
region, for any faction, in a real corpus world. Ran the same instrumented probe across four real,
unmodified worlds — `urban_political`, `frontier_living_world`, `dungeon_crawl`,
`generated_frontier_3_42` — 3000 ticks each, 12,000 combined real ticks.

**Result: zero ownership changes, in any world, for any region, ever.** Every "wild" region
(confirmed elsewhere this batch to have real combat via `trauma_score` movement — e.g.
`goblin_camp`) showed `influence` frozen at exactly `0.0` the entire run in all four worlds. The
only nonzero influence anywhere came from two regions with compile-time-authored starting
ownership, and even those never moved past their starting `100.0`.

This is not "the design needs different values" — `FactionInfluenceService.process_influence_shift()`
appears, on a code-level trace, like it should fire (see §2.1's classification trace), but
empirically does not, for a reason not yet found. That is now `TCK-20260914-REGIONAL-INFLUENCE-SHIFT-NEVER-FIRES`,
filed separately. **§3.3 (the military-strength driver) is downgraded from "provisional formula" to
"blocked pending that ticket"** — §3.1 (territory) and §3.2 (sentiment/tension, the primary driver
added after this section was first written) are both unaffected, since neither derives from the
dynamic conquest path at all.

## 6. Summary for peer review

1. **Central design, §3.2**: a `SocialBond`-shaped `FactionSentiment` record, built from the same
   real entity-interaction producers (combat, cooperation, appraisal) that already drive
   entity-level bonds, decaying toward neutral on staleness (new mechanism, flagged as such). Feeds
   the existing, untouched `tension_delta` → `DiplomaticStateMachine` path. **Closes loop #3
   directly and independently of territory.**
2. **Importance weighting was investigated, found unsupported by any real signal, and cut from
   this build — not accommodated with a weak proxy.** `veterancy_rank` confirmed degenerate
   (everyone at rank 0). `public_reputation` is real and non-degenerate but its 2× spread is
   structural and **confirmed not to widen with more play** (measured flat across ten checkpoints
   over a real 5000-tick run). Sentiment ships with a single fixed `FACTION_SCALE_FACTOR` instead,
   applied uniformly regardless of which entity acted. A real importance signal (faction
   leadership/rank/standing — genuine new design, none exists today) is scoped separately:
   `TCK-20260915-FACTION-IMPORTANCE-SIGNAL-INITIATIVE` (filed, scoping only, not blocking).
3. **§3.1 (carried from the prior draft)**: a parallel `RegionState.owner_faction_id_str` field
   closes the identity-collapse gap (FAC-010, already documented) and derives `FactionState.
   territory` for real. **Closes loop #2**, and offers a second, now-redundant path to loop #3.
4. **Loop #1 (`military_strength`) remains genuinely open.** §3.3's vault-gold sketch is blocked on
   a separate ticket (`TCK-20260914-REGIONAL-INFLUENCE-SHIFT-NEVER-FIRES`) and is, on its own
   terms, not addressed by the sentiment design at all — a relational signal is the wrong shape for
   raw military capability. This is the one loop this proposal cannot currently claim to close.
5. **User's decision (2026-09-15), stated at the top of this document too**: ship sentiment now on
   its own merits (real tension, real diplomacy, a named trade extension point); the
   military-strength driver is separate, later work. This design should reliably get real faction
   pairs to `TENSE`/`HOSTILE` in a real run. It should **not** be expected to reliably reach `WAR`
   until loop #1 has its own real answer — a known, named gap, not an assumed success.
6. **Acceptance bar for building this** (§4, unchanged in substance): a real, unmodified
   corpus-world run showing two factions' `sentiment` genuinely diverging from ordinary entity
   interaction, and at least one pair reaching `TENSE` or `HOSTILE` as a result — not a constructed
   fixture. Everything unlocked this week passed its unit tests while doing nothing; this proposal
   does not get to skip the same bar.
7. No code has been written against this proposal yet. Peer/user review of this revision requested
   before implementation begins.
