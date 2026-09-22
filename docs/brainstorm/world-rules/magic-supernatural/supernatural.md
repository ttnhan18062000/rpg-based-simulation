---
status: active
layer: architecture
authority: P1
audience: agent
tags: [architecture, world, content]
---

# World Rule Family: Magic / Supernatural

**Purpose/scope.** What it means, in this world model, for something to be objectively
supernatural, merely believed supernatural, apparently supernatural through ignorance, a
supernatural capability, a supernatural effect, or a supernatural property of an object,
place, or entity — and how these relate to ordinary causal, perceptual, social, cultural,
institutional, and legal semantics already established. Does not design a magic gameplay
system, spell/ritual/deity catalog, or elemental/mana taxonomy — those remain later,
domain-specific content decisions.

**Standing direction (`tmp/world-rule-direction.md`).** Rule statements describe only target
world semantics; repository classification records realization only, never delivery priority.

**Status.** Batch 12 (Magic/Supernatural), first draft, per
`tmp/world-rule-batch-12-ext-ai.md`. Not split — one coherent batch remains reviewable, per
that instruction's own explicit "do not split pre-emptively" guidance. Structured per the
normalized five-category methodology, plus the standing direction's own Implementation
Candidates — Non-Binding section.

---

## Domain Rules

## MAG-01 — Objective supernatural truth, observed evidence, an observer's own causal attribution, and that observer's own resulting belief/knowledge are four independent facts; a fifth, collective belief, may diverge from all of them at once

> Whether a supernatural event or effect objectively occurred in world state (**truth**) is
> distinct from whatever evidence an observer happens to receive (**evidence** — which need
> not identify the true cause), which is distinct from whichever cause that observer assigns
> to it (**attribution** — "a ghost did it," "the wind did it," "I don't know," any of which
> may be right, wrong, incomplete, or deceptive), which is distinct from that observer's own
> resulting belief or knowledge (governed by the existing Perception/Knowledge rules, Batch
> 06 — this family never bypasses that machinery). A population's own **collective belief**
> about the same event (Batch 11B's BEL-01) is a fifth, further-independent fact that may
> diverge from the true cause, from any individual's own evidence, and from any individual's
> own attribution, simultaneously. One objective event may support several different,
> simultaneously-held, observer-relative explanations without any of them changing what
> actually happened.

**Disposition: ACCEPT — REQUIRED.** Passes the admission test per this batch's own explicit
discipline (§23): Batch 06's KNOW-01/KNOW-02 already establish belief ≠ truth generally, and
Batch 11B's BEL-01 already establishes collective belief ≠ individual belief ≠ world truth —
but neither names **evidence** and **attribution** as their own intermediate facts distinct
from belief itself. That three-way refinement (evidence received ≠ cause attributed ≠
resulting belief) is genuinely new content this domain specifically requires, since magic is
exactly the domain where "I saw something happen" and "I believe X caused it" must be kept
separable for scenarios like misattribution and multiple conflicting witnesses to be
representable at all.

**Repository evidence: PARTIAL, for the perceptual/evidence layer generally (reused, not
new); MISSING, for any supernatural-specific truth/evidence/attribution content.** No field
or mechanism anywhere represents an "objectively supernatural" event, effect, or property —
confirmed via direct, broad search (no dedicated `Magic`/`Supernatural`/`Spell` class or
state anywhere in `src/`). The general evidence/attribution/belief machinery this Rule reuses
(`PerceptionGate`, `BeliefEntry`, `KnowledgeFact`) is real and already applies to any
observation, magical or not — but nothing populates it with supernatural content today, so
this Rule's own specific claim (that these four-plus-one facts may diverge for a *supernatural*
event) remains untested against real content, only against the general machinery it reuses.

**Scenarios:** [MAG-S01](../scenarios/magic-supernatural-batch-12.md#mag-s01) (real magic, no
witness), [MAG-S03](../scenarios/magic-supernatural-batch-12.md#mag-s03) (ordinary event
mistaken for magic), [MAG-S04](../scenarios/magic-supernatural-batch-12.md#mag-s04) (real
magic mistaken for ordinary cause), [MAG-S05](../scenarios/magic-supernatural-batch-12.md#mag-s05)
(conflicting explanations of one magical event).

---

## MAG-02 — Individual or collective belief does not, by default, cause supernatural truth to become real; where a domain permits belief-powered magic at all, that is its own specific, declared supernatural causal mechanism, never a universal rule

> A population strongly believing a place is cursed, an object is enchanted, or a person is
> divine never, by itself, makes any of those things objectively true. Belief may cause real
> ordinary/social consequences (altered travel, economics, politics, ritual behavior) without
> touching supernatural truth at all. If a domain's own target design wants belief to be
> capable of causing a real supernatural effect, that must be represented as its own specific,
> named, declared supernatural mechanism (belief-powered magic as one particular kind of
> magic) — never as an implicit, universal "sufficiently strong belief becomes reality" rule
> applying to every belief by default.

**Disposition: ACCEPT — REQUIRED.** Passes the admission test: this is a genuinely new guard
specific to the supernatural domain — no earlier Rule needed to forbid belief from causing
objective truth by default, because no earlier domain created the specific risk that a belief
mechanism might accidentally leak into truth-making. This is related to, but distinct from,
this Catalog's own already-established "no default X, only declared causal mechanisms" family
(Batch 09's SOC-03, Batch 07's PROG-05, Batch 10's reclassified open-instability entry) — those
are about persistence/stability defaults, not about one *fact category* (belief) defaulting
into causing a *different* fact category (objective truth) becoming real.

**Repository evidence: SUPPORTED, by absence — the correct outcome, not a gap.** No mechanism
anywhere derives any objective world-state change from `CultureState`, `BeliefInstitution`, or
any individual belief/knowledge record — confirmed via direct inspection of `CulturalBias
Applicator` (Batch 11B evidence: it only ever biases a transient route-scoring delta, never
writes durable world state) and `BeliefInstitution` (Batch 11B evidence: currently has no live
caller at all, so it certainly does not write supernatural truth). There is no existing
"belief becomes reality" shortcut to correct.

**Scenarios:** [MAG-S02](../scenarios/magic-supernatural-batch-12.md#mag-s02) (false magic
belief).

---

## MAG-03 — A supernatural property or condition attached to an object, place, or individual is its own fact, distinct from that subject's own identity, ownership, or possession; whether it persists through ownership change, movement, transformation, or identity replacement is a further, independently declared question the supernatural mechanism itself must answer

> A curse, blessing, enchantment, or comparable supernatural condition is never automatically
> tied to whoever currently owns or possesses its subject — a cursed object may remain cursed
> when stolen, sold, or gifted, exactly because the condition attaches to the object (or
> place, or individual) itself, not to the ownership relation. Whether a specific supernatural
> condition persists through a change of owner, physical movement, transformation (see
> `places.md`'s PLACE-03/`settlements.md`'s SETT-03 for the general pattern this reuses), or
> identity replacement (Batch 01's ID-06) is a further fact that specific mechanism must
> declare — never assumed to follow ownership or identity by default, and never assumed to
> automatically terminate on any of them either. The condition remains distinct from
> knowledge of it, belief about it, its subject's own value, and its subject's own reputation
> — a legal owner may not know their own property is cursed while someone else does.

**Disposition: ACCEPT — REQUIRED for the distinctness and the "not decided by default"
requirement; which specific conditions persist through which changes is PERMITTED,
mechanism-specific content.** Passes the admission test: Batch 01's OWN-01/02 and Batch 08's
`PROP-01` already establish that ownership/possession are their own facts distinct from an
object's own identity, and Batch 01's ID-03/06 already require transformation/identity
questions to be explicitly declared — but neither anticipated a property that specifically
does **not** follow ownership the way ordinary object properties usually do (a sword's own
sharpness moves with whoever holds it; this Rule's own point is that a curse need not). That
inversion — supernatural properties attach to the subject regardless of who controls it,
unless declared otherwise — is the genuinely new content, required by this batch's own §11/
§13 investigation.

**Repository evidence: MISSING.** No supernatural-property field or mechanism exists on any
object, place, or entity anywhere in this repository — confirmed via direct search (no
"curse"/"blessing"/"enchant" class or field found). The ordinary ownership/identity machinery
this Rule reuses (`ResourceTransferIntent`, `PlaceState.prior_kind`) is real and already
correctly separates ownership from identity for non-supernatural cases (Batch 08/11A
evidence) — nothing currently attaches a supernatural condition to any subject for this
machinery to be tested against.

**Scenarios:** [MAG-S08](../scenarios/magic-supernatural-batch-12.md#mag-s08) (persistent
cursed object changes owner).

---

## MAG-04 — A Place's own objective supernatural property, a culture's attributed sacredness, an institution's declared sacredness, an individual's own knowledge of that declaration, an individual's own personal belief, the Place's own historical significance, and a past supernatural event occurring there are seven independent facts; none automatically implies any other, and no single global "sacred" or "magic" boolean may represent all seven

> Extending `places.md`'s own PLACE-02 (significance is always attributed, never intrinsic)
> and `collective-belief.md`'s own BEL-03 (sacredness is always attributed, never universal)
> to the supernatural case specifically: a Place may have a real, objective supernatural
> property (MAG-01's own "truth" layer, applied to a location) that is entirely independent of
> whether any culture attributes sacredness to it, whether any institution formally declares
> it sacred, whether any specific individual knows of that declaration, whether that
> individual personally believes it, whether the Place has ordinary historical significance
> (PLACE-02, no supernatural component required), or whether a supernatural event occurred
> there in the past. All seven facts may combine in any combination — a Place may be
> objectively magical with zero cultural recognition; culturally sacred with zero objective
> supernatural property; historically significant through an entirely ordinary event; or the
> object of a culture's own false belief that a miracle occurred there when historical/
> supernatural truth says otherwise. No single field can correctly represent all seven at
> once, the same discipline `territory-control.md`'s own TERR-01 already requires for
> territorial facts.

**Disposition: ACCEPT — REQUIRED.** Passes the admission test: the batch instruction's own
§12 explicitly states this boundary is "mandatory because of Batch 11A/11B" — PLACE-02 and
BEL-03 already established that significance/sacredness are attribution-relative, but neither
one, on its own, introduces **objective supernatural property** as an eighth kind of fact
alongside the attribution/recognition/belief/history facts they already separate. Adding that
missing fact, and stating that all seven (not merely the attribution-relative subset PLACE-02/
BEL-03 already cover) remain independently combinable, is this Rule's own genuinely new
content — the direct, required reconciliation point between this batch and Batch 11A/11B.

**Repository evidence: MISSING.** No field represents an objective supernatural property on
`PlaceState`, consistent with PLACE-02/BEL-03's own prior findings that no significance/
sacred field of any kind exists there either — confirmed by the same direct search. This
Rule's own seven-way combination remains untested against any real content, but is stated
regardless, consistent with the standing direction's own guidance that a Rule may be valid
before any repository realization exists to check it against.

**Scenarios:** [MAG-S09](../scenarios/magic-supernatural-batch-12.md#mag-s09) (sacred place
without magic), [MAG-S10](../scenarios/magic-supernatural-batch-12.md#mag-s10) (magical place
without recognition), [MAG-S11](../scenarios/magic-supernatural-batch-12.md#mag-s11) (same
place, different sacred interpretations), [MAG-S12](../scenarios/magic-supernatural-batch-12.md#mag-s12)
(institution declares false miracle), [MAG-S13](../scenarios/magic-supernatural-batch-12.md#mag-s13)
(unrecognized real miracle).

---

## MAG-05 — A ritual or comparable intentional practice, a participant's own belief, and whether a declared supernatural mechanism actually activates are three independent facts; a culturally meaningful ritual may produce no supernatural effect at all, and whether a real supernatural mechanism requires participant belief as one of its own prerequisites is mechanism-specific, never assumed universally true or false

> A ritual's own social/cultural meaning (Culture, `culture.md`'s CULT-01/02) is one fact.
> Whether a specific participant privately believes the ritual "works" is a second, distinct
> fact (an individual's own belief, per Batch 06). Whether a declared supernatural mechanism
> actually activates as a causal consequence of the ritual is a third, further-independent
> fact. A ritual practiced purely for its cultural/social meaning, with no supernatural
> mechanism attached to it at all, is fully legitimate and common — the majority of any
> culture's own ritual content need never touch this family at all. Where a real supernatural
> mechanism *is* attached to a ritual, whether participant belief is one of that mechanism's
> own declared prerequisites is a property of that specific mechanism, never assumed
> universally required or universally irrelevant across every supernatural mechanism a domain
> might ever declare.

**Disposition: ACCEPT — REQUIRED.** Passes the admission test: this batch's own §19 names
this as "an important integration point with CULT-03/CULT-04 and BEL-01/BEL-02," but the
three-way split itself (cultural practice ≠ participant belief ≠ mechanism activation) states
content none of those Rules individually provide — CULT-03/04 govern cultural practice and
its transmission generally, not specifically whether a practice has an attached supernatural
consequence; BEL-01/02 govern collective belief and the belief/supernatural-truth boundary
generally, not specifically whether one mechanism's own activation is belief-gated. Combining
them for this specific three-way case is genuinely new content, not a restatement.

**Repository evidence: MISSING.** No ritual-with-supernatural-mechanism concept exists
anywhere — confirmed via direct search (no "ritual" hits beyond unrelated identifiers, per
this batch's own §22 investigation). This Rule's own target semantics remain independently
coherent and testable via scenario even though nothing currently realizes them.

**Scenarios:** [MAG-S07](../scenarios/magic-supernatural-batch-12.md#mag-s07) (failed spell/
ritual), [MAG-S15](../scenarios/magic-supernatural-batch-12.md#mag-s15) (ritual practice
without supernatural effect), [MAG-S16](../scenarios/magic-supernatural-batch-12.md#mag-s16)
(supernatural effect without cultural ritual).

---

## Inherited / Applied Foundational Rules

### Supernatural capability is distinct from a supernatural effect actually occurring; the full chain (capability → attempt → resolution → effect → consequence) must never collapse into a label or numeric score

> Having a supernatural capability, that capability being currently available, attempting to
> use it, the attempt succeeding or failing, and a supernatural effect actually resulting are
> five distinct facts. A mage capable of teleportation is not currently teleporting; knowing a
> ritual does not mean an entity can perform it right now. A supernatural outcome must trace
> to a real, declared causal chain — it must never occur merely because an entity holds a
> magic-related label or numeric score (a bare `magic_power → effect` shortcut is exactly the
> pattern this reuse forbids).

**Disposition: INHERITED — direct reuse of Batch 06's AGENCY-01 (decision stages causally
distinct), Batch 07's own capability-vs-execution family, and the foundational CAUSE-01 (any
change requires a real, declared causal event), applied to supernatural capability
specifically, per this batch's own explicit instruction (§8/§9: "reuse Batch 07... add a new
Rule only for genuinely supernatural refinement" — no such refinement was found necessary
here beyond what these three already state combined).**

**Repository evidence: MISSING, for any supernatural capability/execution mechanism to check
this against.** No supernatural capability field exists anywhere. The general
capability-vs-execution discipline this entry reuses is otherwise well-established in this
repository for non-supernatural cases (Batch 02/07/10 evidence, reused directly).

**Scenarios:** [MAG-S06](../scenarios/magic-supernatural-batch-12.md#mag-s06) (capability
without use).

### Magic may fail; a successful attempt is distinct from its intended final consequence, and interruption, insufficient resources, invalid or resistant targets, and partial/redirected effects are all legitimate outcomes where a declared mechanism permits them

> A supernatural attempt succeeding does not guarantee the intended final consequence
> results — a spell may execute but be resisted, redirected, partial, or fail downstream, if
> the declared mechanism permits it. No universal resistance system is required merely to
> make this possible.

**Disposition: INHERITED — direct reuse of Batch 10's own "authority never guarantees
compliance" pattern, Batch 07's capability ≠ guaranteed success, and Batch 10's LAW-01
("sanction decided ≠ sanction executed"), applied to supernatural attempts specifically. No
new claim beyond confirming these already-settled patterns extend unchanged.**

**Repository evidence: MISSING, for the same reason as above.**

**Scenarios:** [MAG-S07](../scenarios/magic-supernatural-batch-12.md#mag-s07).

### Supernatural power may causally influence authority, practical power, or legitimacy, but never automatically substitutes for any of them; institutional declaration never makes a supernatural claim objectively true

> An institution declaring a person divine does not grant that person real supernatural
> capability; conversely, real supernatural capability does not automatically grant political,
> legal, or social authority, and an institution may validly refuse to recognize it. Institutional
> declaration never makes any supernatural claim objectively true, exactly as `collective-
> belief.md`'s BEL-01 already requires for collective belief generally.

**Disposition: INHERITED — direct reuse of Batch 10's INST-03 (authority/capability/power/
legitimacy are correlated, never substitutable) and INST-04 (legitimacy's relationship to
authority is institution-declared, not fixed) and `collective-belief.md`'s BEL-01, applied to
supernatural power specifically. No new claim: supernatural power is simply one more
correlated-but-not-substitutable input alongside wealth or military capability, which INST-03
already generalizes over.**

**Repository evidence: MISSING, for any supernatural-power-to-authority mechanism.**
`FactionState.military_strength`'s own real, tracked practical-capacity fact (Batch 10
evidence) remains the closest analogue for a non-supernatural "power" input; nothing
supernatural exists to check the same boundary against yet.

**Scenarios:** [MAG-S12](../scenarios/magic-supernatural-batch-12.md#mag-s12),
[MAG-S13](../scenarios/magic-supernatural-batch-12.md#mag-s13).

### Where existing law/jurisdiction semantics already provide the necessary scope over supernatural acts, this family reuses them directly rather than building a parallel "magic law"

> A supernatural act may be prohibited by a declared law, may occur outside an enforcing
> institution's own reach, may be misclassified by an authority, or may cause an ordinary act
> to be falsely prosecuted as magic — all of this is already expressible through
> `law-enforcement.md`'s own LAW-01 (law/knowledge/compliance/detection/adjudication/sanction
> are distinct, no mandatory pipeline) and LAW-03 (jurisdiction has a declared scope), with no
> supernatural-specific refinement required.

**Disposition: INHERITED — direct reuse of Batch 10's LAW-01/LAW-03, per this batch's own
explicit instruction (§15: "do not create magic law as a parallel legal model if LAW rules
already express the necessary semantics"). No new claim.**

**Repository evidence: MISSING, reusing LAW-01's own evidence directly** — no in-world law
subsystem exists at all (Batch 10's own finding), so no supernatural-specific instance of it
exists either.

**Scenarios:** none newly traced; reuses Batch 10's own evidence directly.

### A supernatural information channel (telepathy, clairvoyance, prophecy, divine revelation) establishes a new, bounded information path — it must never silently create omniscience, and knowledge still requires that path exactly as any other fact does

> No observer automatically knows that magic happened, who or what caused it, whether a
> target is cursed, or whether a prophecy is true. Where a supernatural information channel
> exists, it is treated as one more declared information path — governed by the same
> Perception/Knowledge discipline as sight, hearing, or rumor — never as an exemption from it.

**Disposition: INHERITED — direct reuse of Batch 06's PERC-01 (perception bounded by
declared constraints, default of partiality) and KNOW-01, applied to supernatural information
channels specifically, per this batch's own explicit instruction (§16). No new claim beyond
confirming this already-settled boundary extends to a new *kind* of channel.**

**Repository evidence: INERT/OFF — a genuinely positive, real structural match.**
`PerceptionGate`'s own `_SENSE_TO_SIGNAL` mapping (`src/world/perception/gate.py`) already
treats `magic_sense`/`magic_signal` as a first-class sense channel, gated by the exact same
threshold/confidence discipline as vision, hearing, or smell — checked directly, this is real,
live perception-gating infrastructure already capable of realizing this Rule's own
requirement (a supernatural channel gated like any other), not merely a hypothetical shape.
The gap: no content anywhere (checked across the catalog) ever sets a non-default
`magic_signal` value — `get_entity_signals()`'s own fallback (`"magic_signal":
props.get("magic_signal", "none")`) is exercised by every entity checked, confirming the
channel is real and structurally ready but currently INERT/OFF, the same "built, not yet
visible in play" shape this Catalog has now found repeatedly (`BeliefInstitution`, Batch 08's
`ItemInstance`).

**Scenarios:** [MAG-S14](../scenarios/magic-supernatural-batch-12.md#mag-s14) (supernatural
information channel).

### Collective belief about supernatural phenomena is governed by `collective-belief.md`'s own BEL-01/BEL-02 without modification

> A group may collectively believe something supernatural occurred even when it did not, when
> the actual cause was different, or when no supernatural phenomenon occurred at all —
> exactly as BEL-01 already permits for collective belief generally, and BEL-02's own
> social-belief/supernatural-truth boundary already requires.

**Disposition: INHERITED — direct reuse of Batch 11B's BEL-01/BEL-02, per this batch's own
explicit instruction (§3.E: "Preserve Batch 11B BEL-01/BEL-02"). No new claim.**

**Repository evidence: reuses BEL-01/BEL-02's own evidence directly** — PARTIAL for the
institution-backed case (`BeliefInstitution`), MISSING for the institution-free case, per
Batch 11B's own already-established, follow-up-narrowed findings.

**Scenarios:** none newly traced; reuses Batch 11B's own evidence directly.

---

## Scope / Deferred Boundaries

### Concrete spell/ritual/deity/prophecy content catalog

> This family states the target semantics governing supernatural truth, belief, capability,
> and persistence, but does not design a concrete catalog of specific spells, rituals,
> deities, curses, or blessings — implementation-level, domain-specific content, per the batch
> instruction's own explicit "do not invent detailed catalogs."

**Disposition: SCOPE BOUNDARY.**

### Prophecy/divination truth-guarantee semantics

> Whether a specific prophecy or divination mechanism guarantees truth, and whether knowing a
> future proposition could ever force that future to occur, is not designed here — the batch
> instruction's own §17 explicitly permits marking this Deferred rather than inventing
> semantics, since no prophecy/divination concept exists anywhere in this repository to
> investigate against (confirmed via direct search).

**Disposition: SCOPE BOUNDARY.**

### One universal magic substrate

> No universal supernatural resource (mana, a single `magic_power` scalar, one global
> resistance system) is established as target semantics — different supernatural mechanisms
> may use different causal structures, per the batch instruction's own explicit §20/§21
> anti-collapse discipline. Should repository or design evidence ever establish such a
> substrate as genuine target semantics, that would be evaluated on its own merits at that
> time, not pre-decided here.

**Disposition: SCOPE BOUNDARY.**

---

## Repository Findings (significant, cross-referenced)

**These are repository/implementation facts, not World Rule decisions, and imply no delivery
priority.** Per this batch's own explicit instruction (§22): classification below is based on
traced writers/consumers/liveness, never inferred from names alone.

- **Confirmed MISSING — no dedicated Magic/Supernatural/Spell/Ritual/Curse/Blessing/
  Enchantment/Miracle/Divine/Prophecy state, class, or mechanism exists anywhere in this
  repository.** Every "magic"-adjacent hit traced resolves to one of three unrelated, purely
  flavor/mechanical uses: an `ItemDef` category tag (`"magic"`, affecting weapon range for
  `mage`-tagged items), a damage-type multiplier on one combat skill ("Fireball," "200% magic
  damage" — an ordinary combat mechanic, not a supernatural-truth mechanism), and a content
  tag (`"magical"`) on one region (`moon_cave`) with no behavioral consequence traced. None of
  these represents, or collapses, any of this family's own target distinctions — confirmed
  MISSING, not CONFLICTING, per this batch's own explicit classification discipline (§22: "do
  not classify something as CONFLICTING merely because the richer target system does not yet
  exist").
- **A genuinely positive, real structural match, currently INERT/OFF.** `PerceptionGate`'s own
  `magic_sense`/`magic_signal` channel (`src/world/perception/gate.py`) is real, live
  perception-gating infrastructure, structurally ready to realize this family's own
  supernatural-information-channel requirement — but no content anywhere currently emits a
  non-default `magic_signal` value. See the Inherited information-channel entry above.
- **Confirmed SUPPORTED, by absence, for MAG-02's own "belief does not create truth by
  default" requirement.** No mechanism anywhere derives objective world state from belief or
  cultural state — the correct outcome, not a gap.

## Implementation Candidates — Non-Binding

**This section preserves implementation-relevant discoveries only. Nothing here is approved,
prioritized, or required for implementation during the World Rule Catalog phase.**

- **Target semantic:** a supernatural information channel establishes a new, bounded
  information path, gated the same way as any other sense (the Inherited information-channel
  entry).
  **Current realization:** `PerceptionGate`'s own `magic_sense`/`magic_signal` channel is
  real and structurally ready, but no content emits a non-default value.
  **Gap/mismatch:** the gating mechanism exists; nothing feeds it.
  **Possible implementation direction:** a declared supernatural event/effect writing a
  non-default `magic_signal` onto the emitting entity/place's own properties, read through
  the existing, unmodified `PerceptionGate` path — no new perception mechanism required.
  **Implementation decision:** DEFERRED — no commitment in Rule Catalog phase.
- **Target semantic:** a supernatural property or condition attaches to its subject (object/
  place/individual) independently of ownership, with its own persistence rules (MAG-03).
  **Current realization:** no supernatural-property field exists anywhere.
  **Possible implementation direction:** a typed supernatural-condition relation (subject,
  source, kind, activation/removal condition), read independently of ownership/possession
  fields, only as an illustrative shape — never a universal `MagicState` or one global effect
  hierarchy, per the batch instruction's own explicit §27 prohibition.
  **Implementation decision:** DEFERRED. No concrete schema is committed here.
- **Target semantic:** a Place's own objective supernatural property is independent of
  attributed sacredness, institutional declaration, and historical significance (MAG-04).
  **Current realization:** no bridge exists between `PlaceState` and any supernatural
  concept.
  **Possible implementation direction:** consistent with `collective-belief.md`'s own
  already-recorded candidate, a relational (`sacred-to`, `attributed-by`) model rather than a
  boolean, now additionally requiring an independent objective-supernatural-property fact
  alongside it.
  **Implementation decision:** DEFERRED.

## Cross-domain links recorded here

- MAG-01 → Perception/Knowledge (PERC-01/KNOW-01/02, Batch 06), Social Relations (Batch 09's
  reputation-reach entry), Collective Belief (BEL-01, Batch 11B)
- MAG-02 → Social Relations (SOC-03, Batch 09), Capability/Progression (PROG-05, Batch 07),
  Organizations (Batch 10's reclassified open-instability entry), Collective Belief (BEL-01/
  BEL-02, Batch 11B)
- MAG-03 → State Ownership (OWN-01/02, Batch 01), Objects/Ownership (`PROP-01`, Batch 08),
  Identity (ID-03/06, Batch 01), Places (PLACE-03, Batch 11A)
- MAG-04 → Places (PLACE-02, Batch 11A), Collective Belief (BEL-03, Batch 11B), Territory
  (TERR-01, Batch 11A — the same non-collapsing multi-fact discipline)
- MAG-05 → Culture (CULT-01/02/03/04, Batch 11B), Collective Belief (BEL-01/02, Batch 11B)
- Inherited capability entry → Agency/Decision (AGENCY-01, Batch 06), Capability/Progression
  (Batch 07), Organizations (ORG-03, Batch 10), Causality (CAUSE-01, Foundational)
- Inherited failure entry → Organizations (Batch 10's authority-can-fail entry),
  Law/Enforcement (LAW-01, Batch 10)
- Inherited authority entry → Roles/Institutions (INST-03/04, Batch 10)
- Inherited law entry → Law/Enforcement (LAW-01/03, Batch 10)
- Inherited information-channel entry → Perception/Knowledge (PERC-01/KNOW-01, Batch 06)
- Inherited collective-belief entry → Collective Belief (BEL-01/02, Batch 11B)

## Open questions carried forward

1. **Does this world have one universal category called "supernatural," or multiple
   unrelated mechanisms grouped only for design convenience?** Not decided here — no
   repository evidence exists either way, and this batch deliberately declines to invent a
   universal substrate (see Scope Boundaries).
2. **Can belief ever causally affect supernatural truth, and if so, is that universal or
   mechanism-specific?** MAG-02 answers the default case (no); whether any specific
   belief-powered mechanism should ever be designed is not decided here.
3. Can supernatural effects exist permanently without an active source, and are supernatural
   properties attached to subject identity, material composition, location, relation, or
   mechanism-specific state? Not decided here — MAG-03 requires each mechanism to declare its
   own persistence, but does not itself choose among these attachment models.
4. Can supernatural effects transfer between subjects? Not decided here.
5. Can supernatural effects contradict ordinary physical/causal rules, or must they remain
   part of the same broader causal world model this Catalog already requires (CAUSE-01)? Not
   decided here — the Inherited capability entry requires a real causal chain regardless, but
   does not resolve whether that chain may violate ordinary physics.
6. Are gods/divine entities objectively supernatural subjects, socially constructed beliefs,
   or both depending on the specific entity? Not decided here — MAG-01/MAG-04's own
   distinctions apply regardless of which answer a future domain chooses.
7. Is there any semantic reason to unify spells, miracles, curses, enchantments, and psychic
   effects beyond repository naming, or should they remain genuinely separate mechanisms? Not
   decided here, per this batch's own explicit anti-collapse discipline.
