---
status: authoritative
layer: architecture
authority: P1
audience: agent
tags: [architecture, world, content]
last_verified: "2026-10-09"
---

# World Rule Family: Survival Needs

**Purpose/scope.** Only needs with meaningful causal consequences — food, water, rest, shelter,
temperature/exposure, or other fantasy-specific requirements, where each modeled need follows
the pattern `need pressure accumulates → thresholds/conditions become relevant →
capability/body/decision consequences become possible`. This family does not create a
universal mandatory need system for its own sake.

**Status.** Batch 05 (Life/Body/Survival/Ecology), first draft. Candidates below originated as
external-reviewer hypotheses (`tmp/world-rule-batch-5-ext-ai.md`); each carries this session's
disposition and repository evidence, not the original wording uncritically kept.

**Normalized 2026-09-22** per external-reviewer instruction on Rule admission discipline
(`tmp/world-rule-batch-5-normalization-ext-ai.md`): entries separated into Domain Rules and
Repository Findings. All four original SURV-* entries pass the admission test as genuinely
new domain-refined semantic constraints — none is a bare restatement of an earlier Rule ID —
so **all four (SURV-01–04) remain Domain Rules; nothing was reclassified.** SURV-04 was
specifically flagged for review per the normalization instruction: its target semantic
principle ("unconsumed need-adjacent state is inert") is kept as the Rule; the specific
repository fact (`last_meal_tick`/`last_sleep_tick` are unread) is separated below as a
Repository Finding, not treated as the Rule's own content.

---

## Domain Rules

## SURV-01 — A need is distinct from a resource, a cost, a body condition, and a pressure

> Need, resource, cost, body condition, and pressure are not automatically the same concept. A
> need is an accumulating internal state calling for satisfaction; a resource is a held/
> accessible quantity; a cost is what an action consumes; a body condition is a persistent
> constraint on capability; a pressure is what a need (or an aggregate condition) exerts once
> accumulated.

**Disposition: ACCEPT.** This is the core distinguishing rule the batch instruction asked this
family to establish. Passes the admission test: a genuine taxonomy claim specific to this
family, not a restatement of RES-01/COST-01/BODY-04 (those are cited only as contrast
categories, not as the source of this rule's own claim).

**Repository evidence: SUPPORTED, by contrast.** `BiologicalComponent.hunger`/`sleep_debt`/
`rest_pressure` are needs (accumulating internal state) — distinct from a resource (gold, item
stacks — RES-01's own category), a cost (`StaminaService`'s drain functions — COST-01's own
category), and a body condition (`WoundState`/`ScarState` — BODY-04/06's own category). The
*pressure* a need exerts once thresholds are crossed (SURV-02) is itself a further, derived
fact distinct from the need's own raw accumulated value.

**Scenarios:** none newly traced; confirmed by direct contrast across already-established
categories rather than requiring a fresh scenario.

---

## SURV-02 — Need pressure accumulates, and crossing a threshold produces real consequences

> A modeled need's pressure accumulates over time; crossing a declared threshold produces a
> real capability, body, or decision consequence — never an assumed or silent effect.

**Disposition: ACCEPT.** Passes the admission test: instantiates the general threshold
discipline (LIMIT-04) specifically for needs, with its own richly-confirmed consequence set —
domain-refined, not a bare restatement.

**Repository evidence: SUPPORTED, richly.** `hunger`/`sleep_debt` accumulate passively each
biological tick (`bio.hunger + 0.1 * cadence.biological`). Crossing declared thresholds
produces real, varied consequences: `hunger >= 95.0` → direct HP damage
(`total_passive_dmg += 2`, `src/engine/apply.py`); `sleep_debt > 70` or `hunger > 70` →
capacity degradation (`CapacityService.derive_profile()`'s `fatigue_multiplier`, reused from
Batch 03's LIMIT-02); `hunger > 50/60/80` → real goal-urgency and decision-priority changes
(`src/systems/world_systems/routine.py`, `src/systems/strategic_systems/intelligence.py`,
`work_queue.py`). Need pressure is one of the most thoroughly-consumed state categories this
Catalog has found.

**Amendment, starvation is staged: weak first, death over days (decided by the owner directly,
2026-10-08; row 36 of the memo):**

> Past a need's threshold, the consequence comes in stages. A starving creature, person or
> animal, first weakens: it recovers more slowly and fights worse. Only with continued want does
> it start losing health slowly, and it dies after about two to three days without food. Crossing the line
> is a warning the body gives, not a death sentence within the hour.

- **Today:** `hunger >= 95.0` costs 2 HP per tick (`src/engine/apply.py`). That kills a person
  about 50 ticks (30 minutes, Bible 05 §1: 1 tick is 36 s) after crossing the line, so with
  hunger at 0.05 per tick (decision 33) a person dies within about 20 hours of their last meal.
- **Why staged:** common sense (a person survives days without food), and runs last about 0.4
  to 2 days, so the weakness stays visible within a run instead of every missed meal being
  fatal. Realistic weeks would make starvation never appear in a run.
- **Engineering and content, not this Rule:** the stage thresholds, the weakening effects (they
  may reuse the capacity degradation SURV-02 already cites), the HP-loss rate, and the same
  staging for other needs where it fits. It is a code ticket after Lane B's batch.
- **Every living kind (decided by the owner directly, 2026-10-09; row 42 of the memo):** this
  applies to every living subject that has the need, animals as well as people: a wolf, a deer, a
  goblin and a townsperson alike. The kind's own need profile sizes it (its rate, its stage
  lines, its recovery). "Person" in the text above is an example, not a limit.
  `src/engine/starvation.py` (decision 36's code) is already kind-agnostic: it reads the
  subject's hunger and max HP, never its kind.
- **Evidence: CONFLICTING** until that ticket lands.

**Amendment, sleep debt ends in collapse, not in bleeding (decided by the owner directly,
2026-10-09; row 41 of the memo):**

> A creature, person or animal, that goes far too long without sleep weakens first, then falls
> asleep where it stands and cannot act until enough of the debt is slept off. Lack of sleep does not wound.
> The cost is lost time and being helpless in place, which is dangerous away from settled land.

- **Today:** `sleep_debt >= 98.0` costs 1 HP per tick (`docs/mechanics/01_entity_anatomy.md`,
  the biological pressures table), so a 100 HP body dies about 100 ticks (one hour) after the
  line. That is the same defect decision 36 fixed for hunger, and it is still in place after
  decision 36's code landed (rpg-planner, 2026-10-09).
- **Shape:** a high-debt stage weakens the subject, the same kind of effect as hunger's first
  stage. At 98 or above the subject collapses into sleep and cannot act until its debt falls
  below a wake line. There is no HP loss at any stage.
- **Engineering and content, not this Rule:** the weakening threshold and effects, the wake line,
  how collapse is represented (a typed involuntary sleep, not a frozen action), and how a
  sleeping subject is treated by others (perception, attack).
- **Alternatives not taken:** staged HP loss as for hunger (a sleepless death is less plausible
  than collapse); collapse plus slow HP loss; keep 1 HP per tick for now.
- **Every living kind (decided by the owner directly, 2026-10-09; row 42 of the memo):** this
  applies to every living subject that has the need, animals as well as people: a wolf, a deer, a
  goblin and a townsperson alike. The kind's own need profile sizes it (its rate, its stage
  lines, its recovery). "Person" in the text above is an example, not a limit.
- **Evidence: CONFLICTING** until its code ticket lands.
- **Scenario:** [LB-S19](../scenarios/life-body-batch-05.md#lb-s19) (weakened, collapse where it
  stands, no action while asleep, wakes, no HP loss; a rested control).

**Scenarios:** [LB-S08](../scenarios/life-body-batch-05.md#lb-s08) (survival pressure).  Staged starvation:
[LB-S18](../scenarios/life-body-batch-05.md#lb-s18) (weakened within hours, dies at 2 to 3 days;
a control that eats), a kernel spec owed with Lane A's decision-36 ticket.

---

## SURV-03 — Only needs with real causal consequences are modeled

> A need is not modeled merely because it would be realistic — every modeled need must have a
> real, traceable downstream consequence. This is a scope-discipline rule specific to this
> family's own need catalog, patterned after (but not a restatement of) COST-04's "not every
> action requires a cost."

**Disposition: ACCEPT.** Passes the admission test: COST-04 governs actions/costs; this rule
governs a different category (needs) and states its own standard for this family's own
catalog — a domain-refined instantiation, not a reconfirmation of COST-04 itself.

**Repository evidence: SUPPORTED, by the absence of a wider need catalog than this repository
actually consumes.** Only `hunger`, `sleep_debt`, and `rest_pressure` are modeled as
biological pressures, and (per SURV-02) all three have real, confirmed consequences — the
repository has not added a need field it doesn't also consume, which is exactly this rule's
own standard held up correctly.

**Scenarios:** none newly traced; a negative claim confirmed by the absence of an
over-broad need catalog, not something a scenario trace would add evidence to.

---

## SURV-04 — Tracked need-adjacent state with no consumer is inert bookkeeping

> If a field exists alongside a need but no declared world rule/process consumes or reacts to
> it, that is a real, nameable fact — not a violation of SURV-02/SURV-03, and not something to
> assume is "probably used somewhere." This is the same discipline ENV-05 applies to
> Environment, restated as its own standing standard for Survival Needs specifically (not a
> bare reuse of ENV-05, since it names a distinct set of fields in a distinct family).

**Disposition: ACCEPT — the target semantic principle stands as a Rule; the specific
repository fact confirming it is separated below as a Repository Finding, not folded into the
Rule's own text.** The batch instruction explicitly required identifying causally inert
bookkeeping — the honest answer is that the needs *themselves* are all live (SURV-02/SURV-03),
but two closely-adjacent timestamp fields are not. Passes the admission test as a standing
constraint (a general standard future need-adjacent fields must be checked against); the
"last_meal_tick/last_sleep_tick are unread" fact is repository-specific and does not belong in
the Rule statement itself.

**Repository Finding: MISSING (inert), confirmed directly.** `BiologicalComponent.
last_meal_tick`/`last_sleep_tick` are written whenever an entity eats or sleeps
(`core_actions.py`, `town_service.py`) but checked directly: nothing anywhere reads either
field back to gate or modify any behavior. They exist only as timestamps today, unlike
`well_rested_until` (a similarly-shaped field that *is* read, by `EvolutionSystem`, confirming
the contrast is real and not an artifact of how timestamps are generally treated).

**Scenarios:** [LB-S09](../scenarios/life-body-batch-05.md#lb-s09) (need exists but no
consequence, counter).

---

## SURV-05 — A subject's needs are those of its kind: biology follows the kind's need profile

> What a body requires comes from what kind of body it is. A subject's needs, and how fast each
> one builds, follow its kind's declared need profile. A kind that does not have a need (an
> undead or elemental with no hunger) never builds that need, and kinds whose profiles differ
> build their needs at different rates. A subject with no declared kind is assigned the ordinary
> person's needs only if it is a person (a civil role). Any other subject without a kind is a
> content defect to report, never a guess. Whichever source supplied a subject's need profile, the
> subject's state records it, including when the profile was defaulted.
>
> A kind's profile declares every modeled need, including the ones the kind does not have: "no
> need" is declared (`none`), never inferred from a missing entry. A profile that leaves a
> modeled need out is a content gap to report, not a kind without that need.

**Disposition: ACCEPT — decided by world-rule-catalog-design under owner delegation, 2026-10-07**
(row 22 of `docs/plans/systemic_world/owner_decision_memo.md`). Passes the admission test:
SURV-01 to SURV-04 say what a need is and when it is modeled, not whose needs a subject has.
SURV-02's accumulation is the mechanism this Rule makes kind-specific. Drives, a subject's
standing motivations, are a separate question owned by AGENCY-08: needs belong to the body,
drives to the person.
- **Alternatives not taken:** need by role (a guard's body is not different from a worker's);
  one uniform need set for everyone (today's accident, and it contradicts the catalog, which
  already declares different profiles); a silent default (forbidden by the durable-state rule).
- **Declared absence (decided by world-rule-catalog-design under owner delegation, 2026-10-07, as
  a reading of this Rule; first relayed to the planner by message, recorded here):** a missing
  need key is a content gap, not "no need". This is the same discipline as CONFLICT-03, where
  missing data declares nothing.

**Repository evidence: SUPPORTED for biology since #407 (`0a03c2448`); the provenance clause is
still MISSING.**
- **Biology follows the kind's profile** (divergence 2.80, `src/engine/biological_needs.py`).
  - The profile comes from an explicit `need_profile_id`, else the species' catalog profile,
    else `humanoid_survival` for a civil role.
  - Levels `none`, `low`, `medium` and `high` scale the old constants by 0, 0.5, 1 and 1.5, so
    `medium` keeps the old rate.
  - Undead and spirits no longer hunger.
  - Tests: `tests/unit/engine/test_biological_needs.py`.
- **Declared absence is in the content:**
  - `data/content/living/need_profiles.yaml` declares `sleep` on every profile: `medium` on
    `carnivore_survival` and `goblin_survival` (a content choice, seeded at the humanoid level),
    and `none` on `undead_purpose`, `spirit_anchor` and `elemental_stability`.
  - The content validator reports a profile that leaves out a modeled need as warning
    `CAT-NEED-001` (`src/content/validator.py`). The corpus has 0 such warnings.
  - The code still has an interim fallback that treats a missing key as not built. It records
    every firing (`ABSENT_NEED_KEY_FIRINGS`) and fires 0 times over the 666 corpus subjects.
- **A monster with no species** keeps the old constants and is reported as a content defect. The
  corpus has 0.
- **Measured** (divergence 2.80), on `frontier_living_world`, seed 42, 1,300 ticks. Before is main
  `7a39acc5d`; after is the #407 head `77fc6bc4c`, which has the same `src` as the merge
  `0a03c2448`:
  - alive at t=1100 goes from 3 to 10, and starvation deaths from 33 to 27; both include meals a
    subject could not pay for (SURV-06's conflicting clause), so they are not the effect of the
    need rates alone;
  - `crowded_frontier` is unchanged, because it has no kind without hunger;
  - `urban_political` is unchanged over 5,000 ticks, because it compiles without species and
    every subject takes the person fallback.
- **Still MISSING: compiled subjects carry no profile and no provenance.** Measured by Lane A on
  `f8f1b69fd`: 0 of 666 compiled entities had a `need_profile_id`. The species covers 615 of
  them, and the person fallback covers the other 51, all HERO, SHOPKEEPER or GUARD. Biology now
  resolves the profile on demand, but the state does not yet record which source supplied it.
  Tracked:
  `TCK-20261007-COMPILED-ENTITIES-GET-DEFAULT-NEED-AND-DRIVE-PROFILES-WITH-VISIBLE-PROVENANCE`.
- **Not changed:** need dimensions with no reader stay inert bookkeeping under SURV-04 until a
  consumer exists.

**Scenarios:** none traced yet. Two are owed when implemented: an undead and a human share a
region for a long run, and only the human grows hungry; two species with different hunger
profiles reach the same hunger at different times.

---

## SURV-06 — A modeled need comes with declared ways to meet it, per kind; the world must offer one within reach

> A need's threshold consequence must be avoidable by behaviour. Each kind declares how it meets
> each need it has.
> - **People** meet hunger in two ways: they eat a meal where meals are served (the inn, for a
>   price), or they eat food they carry. They come to carry food by buying it, by harvesting or
>   foraging it, or by receiving it (loot, gift, inheritance).
> - **Meat-eaters** hunt, **plant-eaters** forage, and **people-kinds without a meal place**
>   eat carried, foraged or looted food. (Which kind hunts which follows from properties, not
>   labels: see the decision-46 amendment below.)
> - **A kind with no hunger** has no hunger path and needs none (SURV-05).
> - **Rest:** every kind with a rest need can rest in place, sleeping rough, wherever it is not in
>   danger. A bed (an inn or a home) only makes rest better; rest never requires a building.
>
> A world that places a kind must offer, within reach of where that kind lives, at least one of
> that kind's ways to meet each of its needs. That guarantees a way exists, not that every
> individual can afford it: a penniless subject with nothing to forage may starve, and that is an
> outcome, not a defect.

**Amendment, roles come from properties, never from labels (decided by the owner directly,
2026-10-09; row 46 of the memo):**

> "Predator", "prey", "grazer" and "hunter" are not kinds' labels. They describe what a creature
> ends up doing, given what it is and what is around it. A kind declares its properties: its
> body size, its power, how dangerous it is, its wits, what its diet can eat, and whether its
> body is edible and to which diets. Whether one creature hunts another follows from those
> properties and the moment: the hunter is hungry, its diet can eat the other's body, and it can
> overcome the other. Whether a creature flees another follows from the danger it perceives.
> A small, weak, edible animal is hunted by larger meat-eaters because of what it is, not
> because it is marked as prey.

- **Consequences:**
  - No species carries a "prey" or "predator" flag, and no behaviour reads one.
  - The same creature can be hunter in one meeting and hunted in another: a wolf hunts a hare
    and flees a bear.
  - A hungry wolf may turn on a lone person when nothing easier is near, and keeps away from a
    group it cannot overcome.
  - People hunt (decision 31) by the same reading.
- **Applies everywhere, not only to food:** the same principle holds for every role a kind
  might be given. A role is an outcome of declared properties and the situation, not an authored
  tag, unless a rule says why a tag is the property itself (for example decision 43's "keeps
  coin and trades", which is a cultural fact about the kind, not a role).
- **Engineering, not this Rule:** the property names and scales, how "can overcome" is
  estimated (it may reuse combat_engagement's posture verdict and KNOW-04's common-knowledge
  danger prior), and how edibility maps bodies to diets.
- **Repository finding to check:** LB-S15 cites an individual-level `ecological_predator` role
  classification. If behaviour reads it as a fixed label, it is CONFLICTING with this amendment.

**Disposition: ACCEPT — decided by world-rule-catalog-design under owner delegation, 2026-10-07**
(row 23 of `docs/plans/systemic_world/owner_decision_memo.md`). Passes the admission test: SURV-02
says crossing a threshold has consequences, and SURV-05 says whose needs they are. Neither says a
need must be meetable. Without this Rule a need is a countdown timer that measures the clock, not
the world, which contradicts SURV-03 (a need is modeled for its real, causal consequence).
- **The meal place is the inn.** The decision layer's "tavern" target names a building no world
  declares, so it is a naming defect, not a missing building.
- **World integrity:** the reachability check is reported at assembly for each world and kind.
  It becomes an error only once the corpus passes. Memo row 11 is the precedent: enforcement that
  would fail corpus worlds was declined.
- **Engineering, not this Rule:** prices, recovery rates, what counts as "in danger", and how far
  "within reach" is.
- **Alternatives not taken:**
  - a TAVERN building added to every world (duplicates the inn);
  - rest only in buildings (a timer for anyone far from one);
  - the engine quietly feeding subjects that cannot eat (hides a content defect);
  - a guarantee that every individual can eat (removes poverty as an outcome).
- **Amendment, common-sense ways to eat (decided by the owner directly, 2026-10-08; row 31 of
  the memo):**

  > A kind meets hunger by any way its members could plausibly use, and each way has its own
  > real cost; none is free. For people the ways include gathering wild food, hunting or
  > fishing, eating food raw or cooking it, buying, and receiving. Food enters the world only
  > from a real source and leaves only by being eaten.

  | Way | Where the food comes from | Its cost |
  |---|---|---|
  | Gather | wild plants and fruit (decision 29) | the walk, the finite charges, competition |
  | Hunt or fish | a wild animal killed leaves meat | the fight's risk, finding prey |
  | Eat raw | any edible food as it is | it fills less than the same food cooked |
  | Cook | raw food plus a fire or hearth | time and a place to cook; fills more |
  | Buy | an inn meal or shop food | money, which needs a way to earn it |
  | Receive | gift, loot, inheritance, help from kin | depends on others |

  - **Raw versus cooked:** raw food fills less than the same food cooked. That is the whole
    difference for now. Sickness from raw food needs an illness state that does not exist, and
    waits for a disease Rule.
  - **No single way is required.** Earning then buying is one way among several. The ruling that
    the free-meal fix waits for it is replaced: the fix lands once people who cannot pay have at
    least one other working way, whichever is cheapest to build first. More ways follow.
  - **The rule names the ways; planning orders them.** Which ways are built, and when, is the
    planner's call under memo row 7. Each way's cost and amounts are content and engineering.
  - **Conservation** (Bible 03): meat enters by a kill and gathered food by harvest, and both
    leave by eating. Cooking converts raw food into cooked food and keeps the link to its source
    (RES-06). Nothing is created by the act of eating.
  - **Evidence: MISSING for hunting, eating raw and cooking.** No meat item, no meat from a kill,
    and no cooking exist in code or content (searched `src/` and `data/` on `39e65eb5a`).
    Gathering is decision 29's evidence; buying waits on
    `TCK-20261007-SHOP-AND-BLACKSMITH-TOWN-PATHS-NEVER-RAN-IN-A-COMPILED-WORLD`.
- **Amendment, wild food is part of the land (decided by rpg-designer, direction confirmed by
  the owner directly, 2026-10-08; row 29 of the memo):**

  > Wild food belongs to the land. Each biome declares how much wild food its land holds and
  > how fast it grows back, and a world places wild food by biome, in its wild land outside
  > its settlements. How many subjects that food feeds is an outcome, not a target: a world's
  > wild food is never sized to its hungry.

  - **Sizing input:** biome fertility, not demand. For example, forest, grassland and river land
    hold more, hills less, and desert, mountain and cave little or none. The figures (node
    density per area, charges, regrowth) are content data, set from the land and never fitted to
    a starvation count.
  - **Regrowth:** a flat data value per biome and food-node kind, through RES-05's ecology
    process. No season mechanic exists. A seasonal yield would need its own declared process
    (ENV-01, ENV-05), which is feature work frozen by memo row 7.
  - **The cost is the land's own:** the walk from a settlement to wild land, finite charges, and
    competition for them. There is no minimum-walk number. A town's land holds owned food (the
    inn, the shop), and taking owned food is theft, which decision 27 excludes.
  - **Which worlds have wild land (decided by the owner directly, 2026-10-08; row 35 of the
    memo):** a frontier world's settlements have wild land within reach. A frontier with none is
    a content oversight: `crowded_frontier` gets a wild module (content). A city may have no wild
    land within reach by design: `urban_political` keeps none, and its people eat by earning and
    buying (EXCH-02).
  - **Which wild land crowded_frontier gets (decided by the owner directly, 2026-10-09; row 39
    of the memo):** a new small forest-edge module with forage and no den, no wolves and no
    hostile faction. The ready-made `wolf_den_near_forest` is not used: it would put a den and
    five wolves five tiles from the hometown, against decision 30 (land near a settlement is
    livable; lethal danger sits deeper). The new module's placement must not overlap
    `bandit_road`.
  - **Unchanged guardrails:** wild food enters by harvest and leaves by eating (Bible 03
    conservation); it is its own declared item and node kind, never herb; and the integrity
    check (`need_paths.py`) counts a wild-food node within reach as a hunger way for the kinds
    that forage.
  - **What follows for measurement:** the test of this clause is occurrence and effect.
    Subjects who cannot pay forage, carry what they gather and eat it, and the nodes deplete and
    regrow. Starvation among subjects who cannot pay is an outcome to report, not an acceptance
    target. If it rises, the missing half is earning and then buying
    (`TCK-20261007-SHOP-AND-BLACKSMITH-TOWN-PATHS-NEVER-RAN-IN-A-COMPILED-WORLD`), not more
    wild food.
  - **Alternatives not taken:** size wild food to the demand of subjects who cannot pay (poverty
    never lethal, which contradicts this Rule's "may starve" and makes earning pointless for
    survival); meet a fixed share of that demand (a tuning dial, not a fact about the world);
    gardens and orchards inside settlements (blurs wild food with owned food).
  - **Evidence: SUPPORTED for the mechanism since #454 (`0b4f12af7`, 2026-10-09); DORMANT in the
    three measured worlds.** Implemented by
    `TCK-20261007-A-NEED-WITH-NO-OPEN-WAY-PULLS-TOWARD-THE-STEP-THAT-OPENS-ONE-SURV-07-AMENDMENT`
    (Lane B), divergence 2.91.
    - **Live:** wild food as its own item and node kind, placed by biome. The placement proof
      covers all 24 resolved worlds at seeds 42 and 43: compiled state with the rule on and off
      is identical once the food node is removed. Carried food is eaten
      (`tests/unit/engine/test_eat_carried_before_travel.py`): a subject now eats its own item
      (30 hunger) instead of the free 40.
    - **Pinned by** LB-S17 in its no-inn form (`tests/mechanic_scenarios/test_forage_loop_wild_food.py`)
      and `tests/unit/worldbuilding/test_wild_food_node.py`.
    - **Dormant:** in `crowded_frontier`, `frontier_living_world` and `urban_political`, charges
      harvested and carried EATs are 0 per run, because a subject with an inn in reach goes to
      the free meal. Foraging occurs only where no inn is in reach. This flips once the free
      meal is removed.
    - **Still owed:** `crowded_frontier`'s wild module (decision 39).
  - **Earlier evidence: MISSING, measured by Lane B on main `dcfe5de4d`** (relayed by rpg-planner, 5
    seeds x 3 worlds, after regrowth and the dry-node release landed). Each world has one food
    node of 8 charges. It supplies about 13 charges per run and is dry for 460 to 700 ticks; the
    median walk to it is 80, 72 and 17 ticks. With free meals removed, starvation rises
    (crowded 9.6 to 12.8, frontier_living 11.0 to 17.6, urban 6.8 to 15.4), all of it among
    subjects who cannot pay. Free meals had been feeding 19 to 47 EATs per run. No world places
    wild food by biome yet.

**Repository evidence: PARTLY SUPPORTED since #407 (`0a03c2448`), with one CONFLICTING clause:
a subject who cannot pay is fed for free.** The inn meal and rough rest complete; the price does
not hold. Per divergence 2.80, measured on `frontier_living_world`, seed 42, 1,300 ticks, from
main `7a39acc5d` to the #407 head `77fc6bc4c` (the same `src` as the merge):
- **Eating and resting now complete:** eat events go from 0 to 24 and sleep events from 0 to 17.
  Alive at t=1100 goes from 3 to 10. These figures include the free meals below.
- **Animals first: the removal waits for the animals' own ways (decided by the owner directly,
  2026-10-09; row 44 of the memo).** Under decision 42, the free-meal removal must leave every
  living kind with a working way to eat, not only people. It lands for everyone at once, after
  predators can hunt (a kill leaves meat, and a carnivore eats it raw) and each kind eats only
  what its diet allows. Building hunting moves up the queue. Until then, today's oddities stay,
  recorded as known flaws:
  - **CONFLICTING: animals reach the inn.** `EatScorer`'s inn route has no kind check, so a
    hungry wolf or goblin walks to a town inn for the free meal.
  - **CONFLICTING: carnivores forage berries.** Wolves and spiders (`carnivore_survival`) take
    decision 27's forage step on a berry thicket, because no diet gate exists. That is against
    this Rule's per-kind ways.
  - **MISSING: hunting.** A kill pays gold and XP only. No meat, carcass or hide item exists in
    the catalog, a corpse holds loot and not food, and there is no eat-corpse action.
  - **MISSING: small, edible, plant-eating animals.** The corpus has 13 species and no herbivore
    or small game, so the only creatures a wolf could hunt are people, goblins or other
    meat-eaters. **Decided by the owner directly, 2026-10-09 (rows 45 and 50 of the memo): add a few generic
    animal archetypes,** defined only by coarse properties, for example a small plant-eater and a
    large plant-eater: low wits, low power, a plant-eating diet, edible to meat-eaters. Nothing
    marks them as prey (decision 46). Named species (a deer, a hare) and exact figures are content
    detail, deferred until the foundation is hardened (decision 50). Meat-eaters then mostly eat
    these animals and turn on people mainly when they are scarce, and people gain something to
    hunt (decision 31). Their grazing is foraging by a plant-eating diet, and their numbers follow
    ECOL's population rules, never a target.
    Scenario: [LB-S21](../scenarios/life-body-batch-05.md#lb-s21) (grazes, flees a noticed
    predator, numbers change only by births and deaths).
  - **Scenario:** [LB-S20](../scenarios/life-body-batch-05.md#lb-s20) (a predator eats what it
    kills, raw; it does not forage what its diet excludes; no kill means no meat).
  - **Measured preview** (Lane B, `frontier_living_world`, seed 42; five-seed figures per kind
    group to follow). With free meals removed, wildlife that ever ate goes from 4 to 1, wildlife
    starvation from 2 to 4, and wildlife end hunger from 92 to 100.
  - **Alternatives not taken:** remove the free meal for people now and close the inn to animals
    (wildlife starvation accepted); close the inn to animals now but keep the free meal for
    people (animals lose their only meal).
- **CONFLICTING: the meal is free when the subject cannot pay.** This breaks "for a price" and
  "no engine charity". **Still CONFLICTING after #454 (2026-10-09):** the removal is parked on
  the local branch `d27-free-meal-removal`, and its ticket stays open until earning (EXCH-02,
  decisions 34 and 37) gives a broke worker a way in all three measured worlds (decision 31's
  landing bar). Measured with the removal on (Lane B, parked branch), there is a starvation wave
  from tick 1000 to 2000, and `urban_political` has 0.0 alive at tick 2500.
  - `CoreActions.execute_survival("EAT")` (`src/engine/domain/core_actions.py:41-49`) cuts hunger
    by 40 with no building, no gold and no carried food.
  - The inn's 5-gold charge is a separate resource transfer (`src/engine/town_resolution.py:124-126`),
    and inventory clamps gold at `max(0, …)` (`src/core/inventory.py:156`, `:230`), so a broke
    subject is fed and pays nothing.
  - Lane A's pinned measurement (seed 42): 21 of 21 EATs on `crowded_frontier` and 11 of 11 on
    `urban_political` were by subjects holding under 5 gold, and gold fell in only 1 of them.
  - The same action also consumed no carried food. **Fixed by #454:** a subject carrying food
    now eats its own item first.
  - Tracked: `TCK-20261007-EAT-BESIDE-THE-INN-FEEDS-A-SUBJECT-THAT-CANNOT-PAY-FREE-MEAL` (P1). It
    lands together with decision 27 (a need with no open way pulls toward the step that opens
    one), so fixing the free meal does not leave poor subjects with no behaviour at all.
- **The meal place is the inn.** `EatScorer` targets the nearest `inn`, and the town EAT is
  served at an `inn`.
- **Service reach is adjacency.** The building is the subject's own tile or one of its four
  orthogonal neighbours (MOV-07), filtered by the action's building kinds: REST takes an inn or a
  home, EAT only an inn. A nearer home cannot shadow the inn (`src/engine/service_reach.py`).
- **Rough rest needs no building:** `CoreActions` REST recovers 10 sleep debt anywhere. The inn's
  or home's town REST adds 5 more, so a bed only improves rest.
- **World integrity is advisory:** `src/engine/need_paths.py` and `tools/need_path_report.py`
  list, per world and kind, whether a hungry kind has a meal place. It never blocks. Four of 24
  worlds have no inn: `dungeon_crawl`, `wilderness_survival`,
  `mechanic_scenario_combat_judgement_withdrawal` and `quest_dense_frontier`.
- **Still open:**
  - **Hunger is acted on too late.** Most people still starve at about t=1000, and starvation
    deaths are 27. That is SURV-07's gap, not a missing path.
  - **Not yet measured:** whether buying, harvesting, foraging or receiving actually puts food in
    the subject's hands for later, and the "not in danger" condition on rough rest.
  - **Engineering finding:** shop and blacksmith enforcement has never run in a compiled world.
    Tracked as `TCK-20261007-SHOP-AND-BLACKSMITH-TOWN-PATHS-NEVER-RAN-IN-A-COMPILED-WORLD`.

**Earlier evidence: CONFLICTING. Eating had never worked in the compiled corpus.** Lane A,
read-only, on main `cc3f00a11`, seed 42, `crowded_frontier` and `frontier_living_world`; the
earlier figures are on base `f8f1b69fd`:
- **Outcome:** 0 eat and 0 sleep completions in 2,000 ticks on both worlds; 36 of 51 and 30 of 39
  deaths are starvation; extinction by t≈1100. (A completion means hunger or sleep debt fell
  between consecutive ticks.)
- **No path for the decision layer.** `EatScorer` (`src/ai/goals/scorers.py:60-74`) targets only
  the nearest `tavern`, but 0 of the 24 worlds has one and `BuildingRegistry` has no TAVERN
  template (`src/town/buildings.py:17-24`). Every world has an `inn`. So 100% of hunger goals have
  no target and are skipped.
  - The act itself is there: `CoreActions` EAT needs no building, and the town EAT costs 5 gold on
    a town tile (`town_resolution.py:95-119`).
- **A separate decision defect:** the strategic capacity gate counts terminal projects, which
  blocks new projects; fatigue wins with an inn target are refused. Lane A is fixing this as
  engineering.
- **More breaks remain downstream:** with a tavern added and capacity unblocked in a probe, there
  were only 9 eat events and 0 sleep events, and 27 of 30 still starved. Still being traced.
- **Bisect:** eating never worked in any compiled corpus world probeable since 2026-07-02. It is
  not a regression.
- **Tracked:** the biology child of
  `TCK-20261007-EPIC-DECISION-CORE-LIVE-MOTIVATION-AND-HONEST-FIGHT-OR-FLEE-INPUTS` (Lane B). It
  lands with SURV-05's rates, the inn meal target, the eat-carried-food path, rough sleep and the
  advisory integrity check. It is a row-7 hard bug.

**Scenarios:** none traced yet. Five are owed when implemented:
- a hungry worker with coins walks to the inn and eats;
- a hungry worker far from town eats the bread it carries;
- an exhausted guard on a distant road sleeps rough and recovers, more slowly than in an inn bed.
- a broke worker walks out of town to wild land, gathers wild food, carries it back and eats it
  when hungry; the patch it stripped is dry for a while, then grows back (decision 29). Written as
  a kernel spec with a no-wild-food control arm:
  [LB-S17](../scenarios/life-body-batch-05.md#lb-s17).
- a broke worker hunts a wild animal, eats its meat raw, and is less sated than a worker who
  cooks the same meat at a hearth (decision 31).

---

## SURV-07 — A need's pull grows as its consequence approaches, so a subject acts on it in time; only a present threat outranks a pressing need

> A mild need is one wish among many: a slightly hungry worker keeps working. As a need approaches
> its consequence line (deprivation, starvation, collapse), its pull on the subject's choice grows
> steeply. Well before the line, it outranks ordinary goals (work, trade, social errands, clearing
> a blocker), early enough that a subject with a way to meet it (SURV-06) can reach that way
> before the line. Only a present threat to the subject's life (danger, flight) outranks a
> pressing need. A need never wins merely by being the subject's current task; it wins by
> mattering more as it grows.
>
> The pull is toward meeting the need, not toward one building. When none of the subject's ways
> is open to it now (it cannot pay for the meal, it carries no food), the pull goes to the step
> that opens one: foraging or harvesting where its kind can, earning where it has paid work and
> then buying, or asking where a social path exists. Only ways SURV-06 declares for its kind
> count, and only steps the subject can actually take. A present threat still outranks it.
> Opening a way is attempted, not guaranteed: a subject with no step it can take stays honestly
> hungry, which is SURV-06's poverty outcome.

**Disposition: ACCEPT — decided by world-rule-catalog-design under owner delegation, 2026-10-07**
(row 24 of `docs/plans/systemic_world/owner_decision_memo.md`). This states in catalog terms the
order Bible 04 §1 already declares: Tier 1 Survival (danger, flight), then Tier 2 Biological
(hunger, sleep, exhaustion), then Tier 3 Social, then Tier 4 Economic. It also makes SURV-06's
"avoidable by behaviour" a matter of timing: a need that can only win at its line is not avoidable.
It stays within AGENCY-02, because the escalating pull is still an influence weighed against
others, not a reflex.
- **Engineering, not this Rule:** the shape of the curve, how much travel time "in time" allows
  for, and goal-score magnitudes.
- **A flat priority for routine work is a calibration smell, not a Rule question.** Rescaling it
  is tuning, parked by memo row 7, unless it causes a hard bug like the one below.
- **Alternatives not taken:** one flat scale for needs and goals, where blocker scores are
  rescaled against needs (it treats an order the Bible already declares as a matter of
  magnitude); a need overriding everything near its line (it would outrank fleeing a present
  threat, against Bible 04 §1).
- **Amendment, a need with no open way (decided by world-rule-catalog-design under owner
  delegation, 2026-10-07; row 27 of the memo):** the "toward meeting the need" paragraph.
  - **Why an amendment, not a new Rule:** SURV-06 already makes getting carried food part of the
    way (bought, harvested, foraged, received), so "earn, then buy" is a two-step use of a
    declared way, not a new one. This Rule asks a need to win early enough to reach a way, and
    when every immediate way is closed, the only reachable way is the one the subject opens.
  - **It creates no new ways to get food.** Theft, raiding and coerced begging need their own
    declared Rule. SURV-06's "loot" stays taking from the fallen, not from the living. There is
    no engine charity.
  - **Per subject, not per world:** whether a way is open is judged for the subject (a meal it
    cannot pay for is not open to it; AGENCY-03). SURV-06's world-integrity check stays per kind,
    and poverty stays a valid outcome.
  - **Engineering, not this Rule:** how far ahead "in time" allows for a multi-step way, the
    order among steps, how earning is scored against the escalated need, and when the subject
    gives up.
  - **Alternatives not taken:** the need left honestly unmet with no redirect (every poor
    subject's need becomes a countdown timer again, against SURV-03 and SURV-06's "avoidable by
    behaviour"); a redirect to any means, including crime (it creates ways to get food that no
    Rule declares).

**Repository evidence: PARTLY SUPPORTED for the amendment since #454 (`0b4f12af7`, 2026-10-09);
the escalation and the present-threat gate shipped in #414 (`c2e18b182`).** Lane A's trace, `crowded_frontier`, seed 42, on #403's tree:
- `ResolveBlockerScorer` returns a flat 80.0 whenever an unresolved, unsuppressed blocker exists
  (`src/ai/goals/scorers.py:205-248`), or 95.3 after personality modifiers.
- `SleepScorer`'s utility is the sleep debt itself (+30 at night), about 50 at t≈450.
- So a tired subject walking to the inn is pulled away whenever a blocker's suppression expires.
  A biological need can win only near 80–95, which is close to its consequence line.
- A separate engineering defect is fixed by #406 (`7a39acc5d`): the project switch compared a
  live candidate against the current project's stale, creation-time score.
- **The live gap at `0a03c2448`:** with eating and rough rest completing (SURV-06), most people on
  `frontier_living_world` still starve at about t=1000, because the decision pass picks hunger
  late (divergence 2.80).
- **Implemented by #414 (`c2e18b182`):**
  `TCK-20261007-BIOLOGICAL-NEEDS-ESCALATE-ABOVE-ORDINARY-GOALS-BEFORE-THE-CONSEQUENCE-LINE-SURV-07`
  (Lane A), under
  `TCK-20261007-EPIC-DECISION-CORE-LIVE-MOTIVATION-AND-HONEST-FIGHT-OR-FLEE-INPUTS`. It ships the
  escalation and the present-threat gate. Rest in place uses REST, not SLEEP, because under
  SURV-06 a bed only improves rest.
  - Lane A's pinned measurement, relayed by the planner. Base `0a03c2448` against #414; seeds
    42-46; 1,500 ticks; governor pinned NORMAL; determinism checked; means over the five seeds.
    Starvation deaths go from 25.0 to 13.2 on `crowded_frontier`, from 25.8 to 13.0 on
    `frontier_living_world`, and from 16.0 to 10.8 on `urban_political`. Part of that gain comes
    from the free meals (SURV-06's conflicting clause), so it overstates the escalation's own
    effect.
  - Every remaining starvation death is a subject without gold. The amendment above (decision 27)
    covers them, so that a subject with no open way works toward one rather than being fed for
    free.
- **The amendment landed in #454 (`0b4f12af7`)** as
  `TCK-20261007-A-NEED-WITH-NO-OPEN-WAY-PULLS-TOWARD-THE-STEP-THAT-OPENS-ONE-SURV-07-AMENDMENT`
  (Lane B), divergence 2.91. The paired free-meal removal
  (`TCK-20261007-EAT-BESIDE-THE-INN-FEEDS-A-SUBJECT-THAT-CANNOT-PAY-FREE-MEAL`) did NOT land with
  it, and is parked by the owner's earlier ruling until earning works.
  - **Live:** the forage pull for a subject with no inn within reach (`NO_WAY_WITHIN_REACH`), and
    eating carried food.
  - **Parked:** the "only a subject that can pay is offered the inn" gate (`NO_AFFORDABLE_WAY`,
    defined but not produced), the inn-meal and bed payment, and the no-relief EAT. The earn
    opening step stays a stub until EXCH-02's selling and wages land.
  - **Measured** (Lane B, pinned, 5 seeds, 5000 ticks, re-measured on the merged head after #446
    and #448; base main `ee05ffa98` vs the batch; crowded / living / urban). This includes the
    decision-33 row-1 rate (below) and ENV-08:
    - survivors at tick 5000: 2.2 / 10.0 / 3.0 to 4.2 / 10.4 / 2.8;
    - starvation deaths: 17.2 / 27.4 / 11.0 to 14.2 / 23.6 / 8.2;
    - alive at tick 1000: 5.4 / 15.6 / 14.4 to 17.6 / 21.2 / 22.2.
  - **Decision 33, row 1 (light balance pass):** `humanoid_survival` hunger goes from medium to
    low, 0.1 to 0.05 per tick (divergence 2.93, `tests/unit/engine/test_biological_needs.py`).
    The fiction reason: at the base rate a person reached the starvation line 9.5 hours after a
    full meal and needed about six inn meals a day.
  - **The SUPPORTED flip** waits for the free-meal removal and earning.

**Scenarios:** none traced yet. Four are owed when implemented:
- a tired worker heading to the inn keeps going when a routine blocker reappears;
- the same worker, attacked on the way, flees first and sleeps later;
- a hungry worker with no gold beside the inn is not fed, goes to its paid work, and eats once
  it can pay;
- a hungry subject with no gold, no food and no step it can take stays hungry and is reported as
  having no open way.

---

## Repository Findings (significant, cross-referenced)

- **SURV-04's confirmed inert pair** — `last_meal_tick`/`last_sleep_tick` are written on every
  meal/sleep action and read nowhere, contrasted against the live `well_rested_until`. See
  SURV-04 above for full evidence. This fact is what the Rule's own general standard (inert
  need-adjacent state is a nameable gap, not assumed-used) is checked against here; it is not
  itself the Rule.

## Cross-domain links recorded here

- SURV-01 → Resource (RES-01), Cost (COST-01), Body/Condition (BODY-04/06) — the category
  contrast this rule reuses directly
- SURV-02 → Capacity (LIMIT-02, directly reused), Agency/motivation/decision (the goal-urgency
  content this rule's evidence already touches, owned by that future domain's own content)
- SURV-07 → Agency/Decision (`agency-decision.md`'s AGENCY-02 and AGENCY-07), Bible 04 §1's goal
  tiers
- SURV-06 → Material/Economy (`economy-exchange.md`, buying food; `resources-production.md`,
  harvesting), Settlements (`settlements.md`, the inn as the meal place), Location/Topology
  (`location-topology.md`, "within reach")
- SURV-05 → Agency/Decision (`agency-decision.md`'s AGENCY-08, the drive half of the same
  provenance), Identity/Lifecycle (a subject's kind)
- SURV-04 → all future domains that add need-adjacent tracked fields (a standing standard to
  check new fields against, matching ENV-05's own role for Environment)

## Open questions carried forward

1. Should `last_meal_tick`/`last_sleep_tick` (confirmed inert) be wired to a real consumer
   (e.g., a "time since last meal" decision input distinct from the raw `hunger` value) in a
   future Agency/decision batch, or left as forward-declared bookkeeping? Not decided here.
2. Whether temperature/exposure or shelter should become modeled needs in their own right, or
   remain fully owned by Space/Environment/Movement's own exposure mechanism (ENV-02, BODY-07)
   without a separate Survival-Needs-side pressure, is not decided here — this batch found no
   evidence of a modeled temperature/shelter *need* (as distinct from environmental exposure
   itself), and did not invent one to fill the gap.
