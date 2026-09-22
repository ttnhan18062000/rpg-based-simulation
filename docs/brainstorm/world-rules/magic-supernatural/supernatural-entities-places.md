---
status: active
layer: architecture
authority: P1
audience: agent
tags: [architecture, world, content]
---

# World Rule Family: Supernatural Entities / Places

**Purpose/scope.** The mandatory reconciliation between culturally sacred and objectively
magical Places (required because of Batch 11A/11B); magical objects; illusion, divination,
and mind/memory magic as applications of already-established Perception/Knowledge and belief
Rules; and observer legibility. Does not decide capability (see `magic-capability.md`) or
cross-domain effect ownership generally (see `magical-effects.md`).

**Standing direction (`tmp/world-rule-direction.md`).** Rule statements describe only target
world semantics; repository classification records realization only, never delivery priority.

**Status.** Batch 12 (Magic/Supernatural), drafted per a corrected instruction file
(`tmp/world-rule-batch-12-corrected-ext-ai.md`).

---

## Domain Rules

## PLC-01 — A Place's own objective supernatural property, a culture's attributed sacredness, an institution's declared sacredness, an individual's own knowledge of that declaration, an individual's own personal belief, the Place's own historical significance, and a past supernatural event occurring there are seven independent facts; none automatically implies any other, and no single global "sacred" or "magic" boolean may represent all seven

> Extending `places.md`'s own PLACE-02 (significance is always attributed, never intrinsic)
> and `collective-belief.md`'s own sacredness content (Inherited, originally BEL-03 —
> sacredness may arise through cultural interpretation alone, without requiring supernatural
> transformation) to the supernatural case specifically: a Place may have a real, objective
> supernatural property (`supernatural-ontology.md`'s SUP-01, applied to a location) that is
> entirely independent of whether any culture attributes sacredness to it, whether any
> institution formally declares it sacred, whether any specific individual knows of that
> declaration, whether that individual personally believes it, whether the Place has ordinary
> historical significance, or whether a supernatural event occurred there in the past. All
> seven facts may combine in any combination — a Place may be objectively magical with zero
> cultural recognition; culturally sacred with zero objective supernatural property; both;
> or neither. This is a critical distinction: culturally sacred ≠ objectively magical, in
> either direction.

**Disposition: ACCEPT — REQUIRED.** Passes the admission test: the batch instruction's own
item 24 explicitly frames "culturally sacred ≠ objectively magical" as "critical," and this
directly connects to Batch 11A/11B's own explicit mandate that this reconciliation happen
here. `places.md`'s PLACE-02 and `collective-belief.md`'s own sacredness content already
establish significance/sacredness as attribution-relative — but neither introduces
**objective supernatural property** as an eighth kind of fact alongside the attribution/
recognition/belief/history facts they already separate. Adding that missing fact, and
stating that all seven remain independently combinable, is this Rule's own genuinely new
content — this Catalog's identical genuinely-new content requirement already satisfied once
before, in the now-superseded draft of this same batch, and preserved here unchanged since
the underlying reconciliation requirement is unchanged by the corrected instruction.

**Repository evidence: MISSING.** No field represents an objective supernatural property on
`PlaceState`, consistent with PLACE-02/the reclassified sacredness entry's own prior findings
that no significance/sacred field of any kind exists there either — confirmed by the same
direct search. This Rule's own seven-way combination remains untested against any real
content, but is stated regardless, consistent with the standing direction's own guidance.

**Scenarios:** [MAG-S24](../scenarios/magic-supernatural-batch-12.md#mag-s24) (sacred but not
magical place), [MAG-S25](../scenarios/magic-supernatural-batch-12.md#mag-s25) (magical but
unknown place).

---

## Inherited / Applied Foundational Rules

### Magical objects: a magical property attaches to an object's own identity, distinct from its ownership or possession, exactly as `supernatural-transformation.md`'s own STR-01 and Batch 08's own OBJ-01 already require generally

> An enchanted sword remains the same object with a new capability, unless a transformation
> explicitly replaces its identity (an ordinary sword destroyed in a ritual to create a
> genuinely new artifact is a declared identity-replacement case, not an enchantment case).
> The magical property itself is never the same fact as who currently owns or possesses the
> object.

**Disposition: INHERITED — direct reuse of `supernatural-transformation.md`'s own STR-01
(transformation preserves identity by default; classification ≠ identity) and Batch 08's own
OBJ-01 (object identity ≠ owner/holder/value/quantity), applied to magical objects
specifically. No genuinely new supernatural-specific semantic was found beyond applying these
two already-established Rules — the same admission-test conclusion this Catalog's own prior
follow-up review reached for an equivalent claim in this batch's own earlier, superseded
draft.**

**Repository evidence: MISSING.** No magical-property field exists on any object anywhere in
this repository.

**Scenarios:** [MAG-S19](../scenarios/magic-supernatural-batch-12.md#mag-s19), [MAG-S20](../scenarios/magic-supernatural-batch-12.md#mag-s20).

### Illusion is Perception/Knowledge's own evidence/attribution/belief boundary (`supernatural-ontology.md`'s SUP-01), instantiated for the specific case where a real supernatural process manufactures the evidence itself; illusion never directly rewrites objective truth unless the specific supernatural rule truly does so

> A supernatural process changing what an observer perceives, while the world's own physical
> state remains unchanged, is exactly SUP-01's own evidence ≠ truth distinction — the
> observer's own resulting belief may drive real action, without the underlying objective
> truth having changed at all. This is different in kind from a supernatural process that
> genuinely transforms the world; illusion is never assumed to do the latter unless its own
> declared mechanism says so.

**Disposition: INHERITED — direct reuse of `supernatural-ontology.md`'s own SUP-01 and Batch
06's Perception/Knowledge family, applied to the specific case of manufactured evidence. No
new claim: illusion does not require its own Rule, since SUP-01 already states the general
evidence/truth boundary this is simply one instance of.**

**Repository evidence: MISSING.**

**Scenarios:** [MAG-S14](../scenarios/magic-supernatural-batch-12.md#mag-s14) (illusion
causes real action).

### Divination is a supernatural information channel (already Inherited generally in `magic-capability.md`'s own reuse of Batch 06's PERC-01/KNOW-01), which may be declared exact, partial, or ambiguous by its own specific mechanism, including — where explicitly declared — a mechanism that is perfectly reliable; no divination is assumed omniscient by default, and no general Rule prohibits a domain from declaring one exactly reliable

> What truth a specific divination mechanism can access, what reach it establishes, and
> whether it can be wrong are that mechanism's own declared properties. A domain may validly
> declare a specific divination mechanism to be perfectly reliable for its own declared
> scope — this is not forbidden by the general "no silent omniscience" requirement, which
> concerns *unstated* reliability, not an *explicitly declared* one.

**Disposition: INHERITED — direct reuse of Batch 06's PERC-01/KNOW-01, applied to
supernatural information channels specifically, with the explicit clarification that a
declared-perfect channel does not violate that reuse (an already-implicit corollary of "no
*silent* omniscience," made explicit here per the batch instruction's own item 20). No new
claim.**

**Repository evidence: MISSING.**

**Scenarios:** [MAG-S15](../scenarios/magic-supernatural-batch-12.md#mag-s15) (divination
without omniscience), [MAG-S16](../scenarios/magic-supernatural-batch-12.md#mag-s16)
(perfect divination where declared, counter-probe).

### Mind and memory magic: changed belief, changed memory, changed motivation, compelled action, and changed relationship are five independent facts, none automatically implying the others; compulsion exercises the explicit reflex/compulsion/mind-control carve-out Batch 06's own AGENCY-02 already reserved, and a compulsion rule may constrain or override ordinary choice only where declared, preserving its own source/target/scope/duration/conditions/result

> A magical false memory changes belief; whether that later changes a relationship requires
> its own further, real causal step (social consequence) — magic never skips causal layers
> merely because the initiating cause was supernatural. Ordinary motivation is never the same
> fact as supernatural compulsion (Batch 06's own AGENCY-02 already reserves this exact
> distinction, and its own explicit carve-out for future reflex/compulsion/mind-control
> overrides is precisely what this domain exercises) — a declared compulsion rule may
> constrain or override ordinary choice, but "mind control" is never used as a bare causality
> bypass; the compulsion's own source, target, scope, duration, and conditions remain
> declared and checkable.

**Disposition: INHERITED — direct reuse of `supernatural-ontology.md`'s own SUP-01 (belief/
knowledge/memory distinctness) and Batch 06's AGENCY-01/AGENCY-02 (decision stages causally
distinct; motivation influences, never determines, with an explicit reserved carve-out for
compulsion), applied to mind/memory magic specifically. No new claim: this is the direct
exercise of a carve-out Batch 06 already anticipated by name, not new content.**

**Repository evidence: MISSING.**

**Scenarios:** [MAG-S17](../scenarios/magic-supernatural-batch-12.md#mag-s17) (memory
alteration), [MAG-S18](../scenarios/magic-supernatural-batch-12.md#mag-s18) (compelled
action).

### Observer legibility: the causal law behind a supernatural mechanism remains coherent even when individual agents misunderstand it, exactly as `supernatural-ontology.md`'s own SUP-01/SUP-03 already require

> Magic may be mysterious to individual observers without being arbitrary at the world-model
> level — an observer's own incomplete evidence, later refined through repeated pattern,
> record, or investigation, is exactly SUP-01's own evidence/belief/knowledge chain; the
> underlying causal law SUP-03 requires never depends on any observer's own correct
> understanding of it.

**Disposition: INHERITED — direct reuse of `supernatural-ontology.md`'s own SUP-01 and SUP-03
combined. No new claim beyond synthesizing two already-drafted Rules.**

**Repository evidence: MISSING, reusing SUP-01/SUP-03's own evidence directly.**

**Scenarios:** none newly traced; a synthesis, not an independently-tested claim.

---

## Scope / Deferred Boundaries

### Concrete magical-object, magical-place, and divination-mechanism content

> This family states the identity/ownership, sacredness/magic, and information-channel
> distinctions Rules above require, but does not design a concrete catalog of specific
> enchanted items, magical locations, or divination spells — implementation-level,
> domain-specific content.

**Disposition: SCOPE BOUNDARY.**

---

## Repository Findings (significant, cross-referenced)

**These are repository/implementation facts, not World Rule decisions, and imply no delivery
priority.**

- **Confirmed MISSING — no objective supernatural Place property, magical object, illusion,
  divination, or mind/memory magic mechanism exists anywhere in this repository.** See
  PLC-01 and the Inherited entries above.
- **Cross-referenced from `magic-capability.md`.** `PerceptionGate`'s own `magic_sense`/
  `magic_signal` channel (`src/world/perception/gate.py`) remains this batch's own single
  genuinely positive structural match — real, live, structurally ready to gate a supernatural
  information channel exactly as the divination Inherited entry requires, currently INERT/OFF
  since no content emits a non-default value. Not duplicated here in full; see that file's own
  Repository Findings for the complete evidence trace.

## Cross-domain links recorded here

- PLC-01 → Places (`places.md`'s PLACE-02), Collective Belief (`collective-belief.md`'s
  reclassified sacredness entry), Territory (TERR-01, Batch 11A — the same non-collapsing
  multi-fact discipline)
- Inherited magical-objects entry → Objects/Ownership (OBJ-01, Batch 08), Supernatural
  Transformation (STR-01)
- Inherited illusion entry → Perception/Knowledge (Batch 06), Supernatural Ontology (SUP-01)
- Inherited divination entry → Perception/Knowledge (PERC-01/KNOW-01, Batch 06)
- Inherited mind/memory-magic entry → Agency/Decision (AGENCY-01/02, Batch 06)
- Inherited observer-legibility entry → Supernatural Ontology (SUP-01/SUP-03)

## Open questions carried forward

1. **What semantic conditions turn a Place's own objective supernatural property into
   socially meaningful recognition** — is attribution alone sufficient, or does it require a
   further threshold, exactly as `collective-belief.md`'s own significance-grammar note
   already leaves open for the non-supernatural case? Not decided here.
2. Whether this world ever needs a declared-perfect divination mechanism, or whether every
   supernatural information channel should remain bounded/fallible, is not decided here — no
   repository or design evidence motivates deciding it either way.
