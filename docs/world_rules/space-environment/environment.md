---
status: authoritative
layer: architecture
authority: P1
audience: agent
tags: [architecture, world, content]
last_verified: "2026-09-23"
---

# World Rule Family: Environment

**Purpose/scope.** How a location or environment can create conditions that affect subjects and
processes within its declared reach — terrain, hazard, climate/weather, shelter, visibility,
environmental exposure, local resource conditions, environmental modifiers/constraints.
Environment should create **causal conditions**, not passive descriptive metadata — this
family's own investigation explicitly challenged whether environmental state currently has
actual consumers, per the batch instruction's own requirement.

**Status.** Batch 04 (Space/Environment/Movement), first draft. Candidates below originated as
external-reviewer hypotheses (`tmp/world-rule-batch-4-ext-ai.md`); each carries this session's
disposition and repository evidence, not the original wording uncritically kept.

**Explicit non-goal, per the batch instruction.** Do not build detailed weather/ecology
mechanics here, and do not design the Life/Magic consequences of exposure — this family
establishes that exposure is real and causal; downstream domains own the resulting body/
capability state where appropriate.

---

## ENV-01 — Environmental state has causal significance only where a declared world rule/process can consume or react to it

> A region or location's environmental state (hazard, weather, terrain) has causal significance
> only where a declared world rule or process can consume or react to it. Environmental state
> existing as a field is not, by itself, proof that it is causally significant — this rule
> states what environment *should* be (a source of real conditions with a declared consumer),
> and this family's own evidence review found that claim is not automatically true of every
> environmental field in this repository.

**Disposition: ACCEPT, refined 2026-09-21 — "a mechanism reads it" replaced with world-semantic
language.** The original wording described the requirement in terms of a mechanism reading a
field — an implementation-level description of what causal significance looks like in code,
not a statement of the semantic requirement itself. The rule now states the semantic
requirement directly: causal significance requires a *declared world rule/process* able to
consume or react to the state, of which "a mechanism reads it" is simply this repository's own
way of realizing that requirement. The batch instruction explicitly asked this family to
challenge whether environmental state has actual consumers — the honest answer is: most of it
does, one clear field doesn't.

**Repository evidence: SUPPORTED for most environmental state; MISSING (inert) for at least one
field, confirmed directly.** *Causally live:* `EnvironmentService.calculate_hazard_drain()`
reads `region.hazard_level`, `region.calamity_intensity`, and `"MIASMA" in region.
active_modifiers` to compute a real HP-drain amount; `EnvironmentService.get_weather_
multipliers()` feeds directly into `MovementSystem.resolve_move()`'s own speed calculation.
*Causally inert, confirmed by absence of any read site:* `RegionState.service_availability` is
written (degraded by siege, recovered by successful defense — `military_conflict.py`) but
checked directly: nothing anywhere reads it back to gate or modify any behavior. It exists only
as bookkeeping today.

**Scenarios:** [SPC-S10](../scenarios/space-environment-batch-04.md#spc-s10) (the required
counter: environment is descriptive but causally inert).

---

## ENV-02 — Presence or traversal creates an exposure opportunity; actual exposure depends on whether declared conditions are satisfied

> The causal pattern is: presence/traversal → exposure opportunity/context → declared exposure
> conditions checked → exposure occurs only if those conditions are satisfied → downstream
> consequence becomes possible. Occupying or traversing a hazardous location does not, by
> itself, guarantee actual exposure — shelter, immunity, equipment, or form may prevent it.
> Environment establishes the relevant *condition*; later rules (potentially including
> Environment's own mechanism, or another domain's) determine whether that condition actually
> affects the subject.

**Disposition: ACCEPT, refined 2026-09-21 — removed the implication that occupying/traversing
automatically produces exposure.** The original wording collapsed "the environment has a
relevant condition" and "the subject is exposed" into one automatic step. That was too strong,
and this repository's own evidence already contradicted it before this refinement made the rule
match: a subject with a declared immunity to a region's hazard kind experiences the condition
(the hazard is real) without experiencing actual exposure (zero drain). The revised rule states
the full chain explicitly, with the immunity/shelter/equipment/form check as a legitimate,
expected step between condition and exposure, not an exception the original wording had no room
for.

**Repository evidence: SUPPORTED, and this refinement is confirmed by evidence already
gathered, not new evidence.** `EnvironmentService.calculate_hazard_drain()` checks
`get_faction_semantics_service().get_hazard_immunities(faction_id)` *before* computing any
drain — a faction with a declared immunity to the region's `hazard_kind` returns `0` regardless
of `hazard_level`. `WorldDynamicsSystem.resolve_dynamics()` still checks, for every active/alive
entity, which region contains its position and calls this function — presence/traversal
reliably creates the *opportunity* for exposure; whether exposure actually results is a further,
already-real conditional step this repository already implements correctly.

**Scenarios:** [SPC-S04](../scenarios/space-environment-batch-04.md#spc-s04) (enter hazardous
environment), [SPC-S05](../scenarios/space-environment-batch-04.md#spc-s05) (leave hazardous
environment), [SPC-S13](../scenarios/space-environment-batch-04.md#spc-s13) (added 2026-09-21 —
hazardous region entered, but immunity prevents actual exposure).

---

## ENV-03 — Environment establishes exposure; it does not own the downstream consequence

> Environment produces the *fact and magnitude* of exposure. It does not commit the resulting
> body/capability/resource state change itself — that commitment happens through whichever
> domain's own authoritative update path owns the affected state (Life/Body, or another
> appropriate later domain, depending on what the exposure affects). This is OWN-02
> (participation ≠ ownership) restated for Environment specifically. **This rule does not
> decide which domain that is** — only that Environment itself is never that domain.

**Disposition: ACCEPT strongly, refined 2026-09-21 — the specific target-owner claim
loosened.** The original wording named Life/Body (via the repository's own `CombatUpdate` path)
as though that settled which domain *should* own environmental bodily harm going forward. It
doesn't: this repository's current implementation happens to route hazard damage through Combat/
Life's own update path, but that is repository evidence about *today's* wiring, not a target-
architecture claim that Combat specifically must always own this consequence. A later domain
(Life/Body more generally, a distinct Survival domain, or something else this Catalog hasn't
named yet) may end up being the more precise owner once that domain is actually designed — this
rule's own job is only to keep Environment itself out of that role, not to decide who fills it.

**Repository evidence: SUPPORTED for "Environment never owns it"; read as today's wiring, not
target ownership, for "who does."** `EnvironmentService.calculate_hazard_drain()` returns a
plain `int` — it does not construct, touch, or return any `EntityUpdate`/`CombatUpdate` object,
which is the part of this rule that is genuinely settled. The actual commitment happens two
call-frames away, in `WorldDynamicsSystem.resolve_dynamics()`, which builds a
`CombatUpdate(hp_delta=..., alive_set=...)` — real evidence of *a* domain other than Environment
owning the result, cited here as evidence of the boundary holding, not as a claim that Combat is
where this consequence should live once Life/Body/Survival is actually designed.

**Scenarios:** [SPC-S04](../scenarios/space-environment-batch-04.md#spc-s04),
[SPC-S05](../scenarios/space-environment-batch-04.md#spc-s05) (same scenarios as ENV-02 — one
mechanism answering both "does exposure happen" and "who owns the result").

---

## ENV-04 — Environmental modifiers may affect other domains' calculations without owning their commit path

> A weather or terrain modifier may change how another mechanism's own calculation resolves
> (movement speed, combat modifiers) without Environment itself owning or committing that
> mechanism's result. This is ENV-03's same ownership discipline, restated for the
> modifier-rather-than-exposure case.

**Disposition: ACCEPT.**

**Repository evidence: SUPPORTED.** `EnvironmentService.get_weather_multipliers(region)` returns
a plain multiplier dict, consumed inside `MovementSystem.resolve_move()`'s own speed
calculation — Movement's own mechanism reads and applies the multiplier; Environment never
touches Movement's `EntityUpdate` directly.

**Scenarios:** none newly traced; reuses the same evidence as ENV-03, read for a second,
adjacent purpose (a modifier feeding a calculation, rather than exposure feeding a consequence).

---

## ENV-05 — Inert environmental state should be recognized as such, not assumed causal by its mere existence

> If an environmental field exists but no declared world rule/process currently consumes or
> reacts to it, that is a real, nameable fact about the repository's current state — not a
> violation of ENV-01, and not something to silently assume is "probably used somewhere."
> Recognizing inert state explicitly is what keeps ENV-01's "causal significance requires a
> declared consumer" standard honest rather than aspirational.

**Disposition: ACCEPT.** This is the rule ENV-01's own counter-finding motivated — stated
separately so a future domain author has an explicit standard to check newly-added
environmental fields against, rather than relying on this batch's one-time investigation
remaining accurate forever.

**Repository evidence:** same as ENV-01 — `service_availability` is the confirmed instance;
recorded once, not duplicated.

**Scenarios:** [SPC-S10](../scenarios/space-environment-batch-04.md#spc-s10) (same scenario as
ENV-01).

---

## ENV-06 — A region's calamity is the escalation of prolonged instability, not a count of events

> A region's calamity intensity measures how long the region has remained unstable, not how
> many things have happened in it. It rises only while the region stays above the declared
> instability threshold for a sustained period. It falls back slowly once the region stays
> below that threshold. No single event raises it directly: not a death, not a hero's death, not
> one battle. Single events are already counted by regional trauma; calamity measures their
> persistence, not their occurrence. Calamity may spread to adjacent regions through a declared
> propagation process, and anything that consumes it (hazard amplification, displacement,
> regional transformation) reacts to this escalation, never to raw event counts.

**Disposition: ACCEPT — ratified by the owner, 2026-10-05** (owner decision 10,
`docs/plans/systemic_world/owner_decision_memo.md`). Passes the admission test: no earlier Rule
says what raises `calamity_intensity`. Bible 05 L457 and ENV-01's own evidence only *read* it,
so before this Rule, wiring any producer would have invented the law by implication
(`TCK-20260914-CALAMITY-INTENSITY-PRODUCER-NEVER-FIRES`, 2026-10-05 re-check). The meaning
chosen is the one the existing prose already implied: Bible 05 §6 triggers macro events when
regional trauma is "sufficiently high", and `docs/world/ecology_and_calamity_contract.md`
describes calamity as escalation "when trauma reaches critical levels".

**How it divides the work with regional trauma (no collision).** Trauma is the acute, per-event
measure: every violently caused death in a region adds to it (ENV-07), and it recovers (Bible 05 §2). Calamity is the
chronic measure derived from trauma's *persistence* above the instability threshold. They are
two distinct facts about one region, not two counters of the same deaths. A "deaths raise
calamity" rule would have double-counted the cause trauma already owns, and is not adopted.

**Parameters are engineering, not law.** The instability threshold reuses Bible 05 §2's
existing `trauma_score > 50.0`. The persistence window, rise rate, decay rate and cap are
planner and implementer choices, recorded in the mechanics Bible and the parity ledger when
implemented. This Rule fixes only their direction and what drives them.

**Repository evidence: MISSING (producer), SUPPORTED (consumers), at `405cbd77b`.**
- *Producer missing:* the only writer, `CalamityService.apply_calamity_consequences()`
  (`src/world/calamity.py:80`), has zero callers, and its trigger (a `kind == "hero"` death in a
  region with `hazard_level > 0.5`) is the single-event, classification-keyed shape this Rule
  excludes, so it is not the producer to wire. Nothing decays the field either, despite the
  calamity contract's "decays naturally" line.
- *Consumers live, all reading a value that is always 0.0:* the hazard-drain multiplier
  (`environment.py:36`), refugee displacement (`displacement.py:38`), regional transformation
  requirements (`transformation.py:57-59`), and seasonal propagation to neighbours
  (`CalamityPressurePropagator`, `calamity.py:103-162`). Propagation is the declared spread
  process this Rule permits and is kept.
- *World-boss emergence is DEFERRED and INERT* (owner, 2026-10-05). The owner first
  deferred it ("world boss is a very abstract and later feature"), then, the same day, made
  the deferred branches inert. There are three, all behind a flag that defaults OFF, with the
  code kept:
  1. the calamity-gated boss (`calamity.py:42-53`, `calamity_intensity > 0.3`);
  2. `BossService`'s region boss (`boss.py:~100`);
  3. its lair occupant (`boss.py:226`).
  The ratification named (2) and (3). (1) belongs to the same deferred feature (row 10's
  original text names it) and was included to match the owner's intent. **The owner
  confirmed (1), 2026-10-05.** (1) does not fire today because calamity is always 0.0, but it would fire as
  soon as this Rule's escalation is implemented. The precedent is the magical/demonic spawn on the same
  trigger (`ENABLE_REPRODUCTION_MAGICAL_DEMONIC_PATH`, default OFF).
  - *Why inert, not just uncited:* while live, the region boss produced 68% of the deaths on
    `frontier_living_world` (158 of 233). It spawned at a region's centre with no hazard
    endurance and died of drain within ticks, every ~100 ticks (base `54c31ee73`). With bosses
    removed, the instability threshold of 50 is never crossed in any of the 24 worlds. So the deferred feature was the
    evidence every trauma figure rested on. The lair occupant (3) never fired in 48 runs: it is
    dormant, not looping.
  - *What it reverses:* the lair boss had been "live and untouched".
  - *Still holds:* implementing this Rule must not use a boss spawn as evidence. What a world
    boss is, what calls one forth, where it may spawn, and what it endures is later feature
    design, parked by memo row 7.
- *Upstream dependency:* this Rule is observable only once trauma actually accumulates, which
  it does not today (`TCK-20260914-LAIR-REGION-TRAUMA-NEVER-ACCUMULATES`). That ordering is
  deliberate: the meaning was chosen for correctness, not for how soon it becomes visible.
  Under ENV-07 this Rule is **correct but latent** on the current corpus: the only regions above
  the threshold got there through the boss loop and ambient drain, which ENV-07 excludes. Per
  ENV-05, that is an unexercised rule, not a wrong one. This is measured, not only argued: with
  bosses removed, the threshold is never crossed in any world, and under ENV-07 the series is
  0 in every world (see ENV-07's measurement).
- *Not part of this Rule:* `CALAMITY_RANDOM_CHANCE` (declared, unwired; the calamity contract
  L81/L176). A purely random onset would have no causal path (CAUSE-01). Any later probabilistic
  branch must be conditioned on this escalation, not replace it.

**Scenarios:** none traced yet. A scenario is owed when the producer is implemented: a region
held above the threshold escalates, a single death spike does not, and a region that calms
decays.

---

## ENV-07 — Regional trauma counts violently caused deaths; ambient attrition is exposure, not unrest

> A region's trauma is the acute measure of unrest within it. A death adds to it only when the
> death has a violent cause: combat, an attack, an execution, or another act of violence by an
> agent. Deaths from ambient attrition do not add to it: environmental drain from the region's
> own hazard, starvation and other passive biological drain, natural death. Ambient attrition is
> exposure (ENV-02), and its consequences belong to the bodies that suffer it, not to the
> region's record of unrest. A death caused by violence still counts when an ambient process
> delivers the final blow, for example an entity wounded in a fight and then finished by drain.
> Admitting any other kind of death (a declared catastrophe such as a plague) is its own
> decision, not a reading of this Rule.

**Disposition: ACCEPT — ratified by the owner, 2026-10-05.** Passes the admission test: no
earlier Rule said which deaths trauma counts.
- Bible 05 §2 described regions reacting to "the violence and activity within their borders",
  yet added +1.0 for "every entity death".
- ENV-06 calls the result "unrest".
- The two readings came apart once measured: on `frontier_living_world` (10,000 ticks, seed 42,
  audit_mode, base `54c31ee73`), 232 of 233 deaths were hazard drain with no killer, and 1 was a
  defeat.

**Why this meaning (fiction).** Trauma at the instability threshold transforms a region (a
FOREST burns) and feeds calamity (ENV-06). A forest burning because creatures died of the
forest's own drain contradicts ENV-06's "prolonged unrest". Unrest is violence; attrition is the
environment doing what ENV-02 already says it does.

**Why this meaning (dynamics).** Hazard drain grows with trauma above the threshold, and owner
decision 12 removed its cap. Under the old meaning, that was an unbounded positive feedback
loop: drain kills, the deaths raise trauma, trauma raises hazard, and hazard drains harder.
Excluding attrition breaks the loop structurally.

**Alternatives not taken.**
- *Every death counts:* the status quo, the forest incoherence above, and the loop above.
- *Hazard deaths at a reduced weight:* keeps the loop, only slower, and keeps attrition as unrest.
- *Give the dying population hazard endurance instead:* the boss that died most has no catalog
  faction, only the `MONSTER_HORDE` legacy bucket. Endurance is declared per faction, for that
  faction's own in-fiction reason, never derived from location or hostility (owner, 2026-07,
  `TCK-20260701-HAZARD-NATIVE-IMMUNITY`), so granting it to a bucket is not available.

**Consequence, stated plainly (measured).** Trauma falls to roughly zero on the current
corpus, and ENV-06's threshold is unreachable without the boss loop. Three readings were
tested (Lane B, all 24 worlds, 10,000 ticks, seed 42, audit_mode, deaths only, on two bases: `54c31ee73` (includes #347) and `06a0ce1cb` (that base plus the fix for TCK-20261005-SILENT-NO-OP-RETURNS-IN-ACTIONROUTER-HOLD-THE-TASK-AND-ANNOTATE-FALSE-SUCCESS)):
- *"The world fights but misattributes"* (wounded, then drain finishes): **not supported.** 0
  of 2,112 hazard deaths took attacker damage at any earlier time, checked with windows of 50
  and 200 ticks and with no window, on both bases. Control: all 17 defeat deaths checked carry
  a last-hit record.
- *"The world was prevented from fighting"* (combat suppressed by defects): **not supported.**
  Defeats were 31 on the first base and 30 on the second, although the fix cut withheld attacks
  on `frontier_living_world` from 844 to 2.
- *"The world barely fights"*: **supported.**
This Rule does not change with lethality. If the world needs more trauma, the answer is more
violent deaths in the world, not counting more kinds of death.

**Repository evidence: CONFLICTING, at `544b1d341`.** `WorldDynamicsSystem` adds 1.0 to the
containing region for every entity whose `alive_set` becomes false, whatever its cause
(`world_dynamics.py:59-75`, "Each death adds 1.0 trauma"). Hazard deaths carry
`outcome_kind == HAZARD` on the same update, so the cause is available at the writer.
Separately, `apply_plan.py:235` adds 2.0 when a building is destroyed. That is in scope only
when the destruction is violent, and its cause is to be verified when this Rule is implemented.

**How this Rule is refuted.** Cause misattribution: deaths recorded as ambient attrition
whose real cause was violence. Tested at ratification and not found (0 of 2,112, above). It
stays the acceptance test when the producer is implemented
(`TCK-20261005-REGIONAL-TRAUMA-IS-PRODUCED-BY-A-BOSS-RESPAWN-AND-HAZARD-DEATH-LOOP-NOT-BY-FIGHTING`).
If a material share of hazard deaths ever shows prior attacker damage, the implementation must
count a violent cause within a window, not only a recorded killer.

**Scenarios:** none traced yet. One is owed when implemented: a battle in a region raises its
trauma, the same number of drain deaths does not, and a wounded-then-drained death counts.

---

## Cross-domain links recorded here

- ENV-06 → World dynamics / regional trauma (Bible 05 §2: trauma is the acute input calamity
  escalates from), Ecology & population (displacement), Places (regional transformation)
- ENV-07 → World dynamics / regional trauma (what the counter admits), Conflict & combat (the
  violent causes), Life/body/survival (attrition's consequences stay with the body), ENV-06
  (its only input)
- ENV-01, ENV-05 → all future domains that add environmental state (a standing standard to check
  new fields against)
- ENV-02, ENV-03 → Life/body/survival, Capability & progression (plausible future owners of
  exposure's downstream consequences — **not settled here**; ENV-03 keeps Environment itself out
  of that role without deciding which of these, or another domain not yet named, fills it)
- ENV-04 → Movement/Navigation (`movement-navigation.md`), Conflict & combat (future terrain-
  affects-combat content)
- ENV-03 → State Ownership (OWN-02, directly reused)

## Open questions carried forward

1. Should `service_availability` (confirmed inert) be wired to an actual consumer (e.g., shop
   pricing, trade availability) in a future Economy/resources or Places batch, or was it added
   ahead of its own consumer intentionally (a forward-declared field awaiting siege-mechanics
   content not yet built)? Not decided here — this batch only confirms the fact, not the
   remedy.
2. **Checked directly:** `price_modifiers` is causally live, not inert — `src/systems/
   economy_systems/market.py` reads it directly into buy/sell price calculation. `weather` and
   `active_modifiers` beyond `"MIASMA"` were not exhaustively re-verified for every possible
   modifier string this batch; flagged for whichever future Economy/resources or Ecology/
   population batch next touches regional modifiers, rather than assumed either way.
3. **Added 2026-09-21.** ENV-03 deliberately leaves open which domain owns exposure's downstream
   consequences (Life/Body, a future Survival domain, or another not yet named) — not decided
   here, and not to be read as already-settled by the `CombatUpdate` path this repository
   currently happens to use.
