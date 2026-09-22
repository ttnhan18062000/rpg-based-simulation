---
status: active
layer: architecture
authority: P1
audience: agent
tags: [architecture, world, content]
---

# World Rule Family: Supernatural Ontology

**Purpose/scope.** What it means for something to be objectively supernatural in this world
model, how that truth relates to religious/cultural/individual belief about it, and the
governing principle that magic is never a causality exception — any supernatural world
change still requires the same real, declared causal chain any ordinary change requires; only
the mechanism itself may be fictional. Does not decide magical capability (see
`magic-capability.md`), cross-domain effect ownership (see `magical-effects.md`),
transformation (see `supernatural-transformation.md`), or magical objects/places (see
`supernatural-entities-places.md`).

**Standing direction (`tmp/world-rule-direction.md`).** Rule statements describe only target
world semantics; repository classification records realization only, never delivery priority.

**Status.** Batch 12 (Magic/Supernatural), drafted per a corrected instruction file
(`tmp/world-rule-batch-12-corrected-ext-ai.md`), superseding an earlier draft built from a
since-withdrawn instruction file. Not split into 12A/12B — the batch instruction's own
suggested five-file structure organizes one coherent batch, not a batch-level split.

---

## Domain Rules

## SUP-01 — Objective supernatural truth, observed evidence, an observer's own causal attribution, that observer's own belief, that observer's own knowledge (governed entirely by Batch 06's own KNOW-01, never a parallel supernatural-specific knowledge system), and collective/institutional belief are six independent facts; none is implied by any other, and one objective supernatural event may support several simultaneously-held, observer-relative explanations without changing what actually happened

> Whether a supernatural event, effect, or property objectively exists in world state
> (**truth**) is distinct from whatever evidence an observer happens to receive (**evidence**
> — which need not identify the true cause), which is distinct from whichever cause that
> observer assigns to it (**attribution** — "a ghost did it," "the wind did it," "I don't
> know," any of which may be right, wrong, incomplete, or deceptive), which is distinct from
> that observer's own resulting **belief**, which is further distinct from what that observer
> actually **knows** under the certainty/grounding standard Batch 06's own KNOW-01 already
> defines — belief is not automatically knowledge, and this family never builds a parallel
> supernatural-specific Knowledge system; supernatural knowledge is knowledge, governed
> exactly as any other domain's. A population's own **collective or institutional belief**
> about the same event (Batch 11B's BEL-01/BEL-02) is a sixth, further-independent fact that
> may diverge from the true cause and from any individual's own evidence, attribution,
> belief, or knowledge, simultaneously — a god may objectively exist while society denies it;
> a society may worship a god that does not exist; a ritual may be culturally sacred with no
> supernatural effect; witnesses may misinterpret a real supernatural event. Magic owns
> objective supernatural truth/mechanism; Culture/Belief owns social interpretation;
> Knowledge owns what individuals think is true — none of the three owns, or may silently
> stand in for, either of the other two.

**Disposition: ACCEPT — REQUIRED.** Passes the admission test: Batch 06's KNOW-01/KNOW-02
already establish belief ≠ truth generally, and Batch 11B's BEL-01/BEL-02 already establish
collective/social belief ≠ individual belief ≠ world truth ≠ supernatural mechanism — but
neither names **evidence** and **attribution** as their own intermediate facts distinct from
belief and knowledge. That refinement (evidence received ≠ cause attributed ≠ resulting
belief ≠ resulting knowledge) is genuinely new content this domain specifically requires,
since magic is exactly the domain where "I saw something happen" and "I believe X caused it"
must be kept separable for misattribution and multiple-conflicting-witness scenarios to be
representable at all.

**Repository evidence: PARTIAL, for the perceptual/evidence layer generally (reused, not
new); MISSING, for any supernatural-specific truth/evidence/attribution content.** No field
or mechanism anywhere represents an "objectively supernatural" event, effect, or property —
confirmed via direct, broad search (no dedicated `Magic`/`Supernatural`/`Spell` class or
state anywhere in `src/`; the only "magic"-named repository content is an `ItemDef` category
tag on mage weapons, one skill's "200% magic damage" combat multiplier, and one region's
"magical" flavor tag — none representing objective supernatural truth). The general evidence/
attribution/belief/knowledge machinery this Rule reuses (`PerceptionGate`, `BeliefEntry`,
`KnowledgeFact`) is real and already applies to any observation, magical or not — but nothing
populates it with supernatural content today.

**Scenarios:** [MAG-S01](../scenarios/magic-supernatural-batch-12.md#mag-s01) (real magic, no
witness), [MAG-S03](../scenarios/magic-supernatural-batch-12.md#mag-s03) (misattribution,
both directions — ordinary mistaken for magic, and real magic mistaken for ordinary),
[MAG-S04](../scenarios/magic-supernatural-batch-12.md#mag-s04) (conflicting explanations of
one magical event), [MAG-S27](../scenarios/magic-supernatural-batch-12.md#mag-s27) (false
religious belief, real magic elsewhere).

---

## SUP-02 — Individual or collective belief does not, by default, cause supernatural truth to become real; where a domain permits belief-powered magic at all, that is its own specific, declared supernatural causal conversion edge, never a universal "belief becomes reality" rule

> A population strongly believing a place is cursed, an object is enchanted, or a deity
> exists never, by itself, makes any of those things objectively true. Belief may cause real
> ordinary/social consequences (altered travel, economics, politics, ritual behavior) without
> touching supernatural truth at all. If a domain's own target design wants belief to be
> capable of causing or empowering a real supernatural effect, that must be represented as
> its own specific, named, declared causal conversion edge — "collective belief empowers an
> already-existing supernatural process" is a legitimate declared mechanism; "the belief
> statement itself becomes objectively true by definition" is not, unless the world
> explicitly defines reality that way. Architecture must permit belief-powered magic to be
> declared later; nothing here assumes it exists.

**Disposition: ACCEPT — REQUIRED for the no-default-conversion requirement; whether any
specific belief-powered mechanism exists is PERMITTED, domain-declared content.** Passes the
admission test: this is a genuinely new guard specific to the supernatural domain — no earlier
Rule needed to forbid belief from causing objective truth by default, because no earlier
domain created the specific risk that a belief mechanism might accidentally leak into
truth-making. This is related to, but distinct from, Batch 07's PROG-07 and Batch 08's EXCH-01
(power-conversion edges are specific, never automatic) — those govern one social/practical
fact converting into another (wealth into equipment, reputation into leverage); this Rule
governs the qualitatively different, stronger case of a belief/epistemic fact converting into
objective ontological truth, which no earlier Rule addresses.

**Repository evidence: MISSING, for the entire domain — no current mechanism realizes or
violates this either way.** No mechanism anywhere derives any objective world-state change
from `CultureState`, `BeliefInstitution`, or any individual belief/knowledge record —
confirmed via direct inspection of `CulturalBiasApplicator` (Batch 11B evidence: it only ever
biases a transient route-scoring delta, never writes durable world state) and
`BeliefInstitution` (Batch 11B evidence: currently has no live caller at all). There is no
existing "belief becomes reality" shortcut to correct, and no belief-powered-magic mechanism
of any kind to check the permitted case against either.

**Scenarios:** [MAG-S02](../scenarios/magic-supernatural-batch-12.md#mag-s02) (false magic
belief), [MAG-S26](../scenarios/magic-supernatural-batch-12.md#mag-s26) (belief-powered
effect, permission probe).

---

## SUP-03 — Magic is never a causality exception; any supernatural world change requires the same real, declared causal chain (source/cause, mechanism, applicable conditions, valid target/reach, commit/effect, persistent consequence where applicable) any ordinary change requires, and "magic happened" never terminates causal explanation by itself

> The fictional content of a supernatural mechanism may violate ordinary physical
> expectations; it must not violate this world's own declared causal semantics merely because
> it is supernatural. A valid supernatural outcome always traces to: a real actor or source, a
> declared mechanism that actor has access to, whatever conditions that mechanism requires, a
> valid target/reach relationship, a real commit step producing the effect, and — where the
> mechanism itself declares one — a persistent downstream consequence. "Magic happened" is
> never, by itself, a sufficient causal explanation; it is a placeholder for a real chain that
> must still be traceable in principle, exactly as any other domain's own causal explanation
> must be.

**Disposition: ACCEPT — REQUIRED.** Passes the admission test: this is the direct, necessary
statement of the batch instruction's own governing principle ("treat fictional rules as real
rules") as a target-semantic requirement, not merely a framing note. CAUSE-01 (Foundational)
already requires any change to trace to a real, declared causal event in general; this Rule's
own genuinely new content is the explicit, domain-specific refusal to grant magic an implicit
exemption from that requirement merely by virtue of being supernatural — a refusal no earlier
Rule needed to state, since no earlier domain carried this specific risk of being treated as
an exception to ordinary causal discipline.

**Repository evidence: MISSING, for the entire domain — no in-world supernatural mechanism
exists to check this against, in either direction.** No code path anywhere resolves a
"magic"-labeled outcome by name-based shortcut rather than a real causal chain — but this is
because no supernatural outcome of any kind exists, not because a real chain was checked and
confirmed. `CAUSE-01`'s own general discipline is otherwise well-established for
non-supernatural cases throughout this repository (reused directly from every prior batch's
own evidence).

**Scenarios:** [MAG-S06](../scenarios/magic-supernatural-batch-12.md#mag-s06) (failed spell
after cost), [MAG-S07](../scenarios/magic-supernatural-batch-12.md#mag-s07) (illegal magic
still works — capability and causal chain remain intact regardless of legality).

---

## Inherited / Applied Foundational Rules

### Supernatural laws are declared per mechanism, never assumed from genre convention; a magic rule may declare no cost, unlimited duration, global reach, or an irreversible effect if that is genuinely the declared world law, and any stabilizing counterforce (cost, scarcity, opposition, institutional restriction) is likewise never assumed by default

> Whatever dimensions a specific supernatural mechanism uses — source of capability,
> eligibility, targeting, reach, cost, resource, capacity, resistance, duration, persistence,
> reversibility, interaction with other magic — are whichever the mechanism's own declared
> semantics say they are, never a conventional-balance assumption. A supernatural capability
> may legitimately be rare, expensive, dangerous, unreliable, common, cheap, or overwhelming,
> depending on declared world law; counterforces (resource scarcity, opposing magic, social
> reaction, ecological consequence, institutional restriction, risk) are permitted, never
> mandatory merely to create balance.

**Disposition: INHERITED — direct reuse of this Catalog's own already-established "no default
X, only declared causal/limiting semantics" family (Batch 09's SOC-03, Batch 07's PROG-05,
Batch 10's reclassified open-instability entry), applied to supernatural mechanisms and their
own costs/counterforces specifically. No new claim beyond naming the specific candidate
dimensions this domain's own mechanisms may use, per the batch instruction's own explicit
list.**

**Repository evidence: MISSING, for the same reason as SUP-03 — no supernatural mechanism
exists to declare any of these dimensions one way or the other.**

**Scenarios:** none newly traced; the absence itself, cross-referenced from SUP-03.

---

## Scope / Deferred Boundaries

### Concrete supernatural-law content (spell schools, elemental taxonomies, mana, balancing numbers)

> This family states what makes a supernatural phenomenon causally lawful (SUP-03, and the
> Inherited declared-dimensions entry) but does not design a concrete catalog of spells,
> schools, elements, or balancing numbers — implementation-level, domain-specific content,
> per the batch instruction's own explicit "do not design a spell list."

**Disposition: SCOPE BOUNDARY.**

---

## Repository Findings (significant, cross-referenced)

**These are repository/implementation facts, not World Rule decisions, and imply no delivery
priority.**

- **Confirmed MISSING — no dedicated Magic/Supernatural/Spell state, class, or mechanism
  exists anywhere in this repository.** Every "magic"-named element traced (an `ItemDef`
  category tag, one skill's damage-type multiplier, one region's flavor tag) is unrelated
  flavor/mechanical content, confirmed via direct, targeted inspection rather than inferred
  from names alone — no CONFLICTING finding results, per the standing direction's own
  reminder not to classify CONFLICTING merely because the richer target system does not yet
  exist.
- **Confirmed SUPPORTED, by absence, for SUP-02's own "belief does not create truth by
  default" requirement — the correct outcome, not a gap.** No mechanism anywhere derives
  objective world state from belief or cultural state.

## Cross-domain links recorded here

- SUP-01 → Perception/Knowledge (PERC-01/KNOW-01/02, Batch 06), Collective Belief (BEL-01/02,
  Batch 11B)
- SUP-02 → Capability/Progression (PROG-07, Batch 07), Economy/Exchange (EXCH-01, Batch 08),
  Collective Belief (BEL-01/02, Batch 11B)
- SUP-03 → Causality (CAUSE-01, Foundational)
- Inherited declared-dimensions entry → Social Relations (SOC-03, Batch 09), Capability/
  Progression (PROG-05, Batch 07), Organizations (Batch 10's reclassified open-instability
  entry)

## Open questions carried forward

1. **Does this world have one universal category called "supernatural," or multiple
   unrelated mechanisms grouped only for design convenience?** Not decided here — no
   repository evidence exists either way, and this family deliberately declines to invent a
   universal substrate.
2. **Can collective belief causally affect magic, or is it purely social?** SUP-02 answers
   the default case (no, not by default); whether any specific belief-powered mechanism
   should ever be designed is not decided here.
3. Whether gods/divine entities are objectively supernatural subjects, socially constructed
   beliefs, or both depending on the specific entity is not decided here — SUP-01's own
   distinctions apply regardless of which answer a future domain chooses.
