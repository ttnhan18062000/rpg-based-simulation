---
status: active
layer: architecture
authority: P1
audience: agent
tags: [architecture, world, content]
---

# World Rule Family: Supernatural Transformation

**Purpose/scope.** How a supernatural transformation (human → vampire, living → undead,
ordinary object → artifact, ordinary place → magically altered place) relates to identity
continuity, and how death, resurrection, and undeath relate as distinguishable, non-default
processes. Builds directly on Identity (Batch 01), Transformation (Foundational TRANS
family), History/Provenance, and Life/Body. Does not decide magical objects/places
specifically (see `supernatural-entities-places.md`).

**Standing direction (`tmp/world-rule-direction.md`).** Rule statements describe only target
world semantics; repository classification records realization only, never delivery priority.

**Status.** Batch 12 (Magic/Supernatural), drafted per a corrected instruction file
(`tmp/world-rule-batch-12-corrected-ext-ai.md`). This is the direct resolution of "a major
deferred boundary from earlier batches," per that instruction's own explicit framing. Revised
the same day per a targeted semantic-cleanup follow-up
(`tmp/world-rule-batch-12-corrected-followup-ext-ai.md`) — sharpening STR-02's own status to
separate distinctness (required where modeled) from existence (permitted, content-dependent).

---

## Domain Rules

## STR-01 — A supernatural transformation preserves the subject's own identity by default, exactly as any other declared transformation of an existing subject does (reusing `places.md`'s own corrected PLACE-03 default); a subject's species/kind/form classification is a distinct fact from its own identity, and a classification change never implies identity replacement unless a domain explicitly declares replacement/death/rebirth semantics

> A person transformed into a vampire, a creature corrupted into a new form, or an ordinary
> object transformed into a magical artifact is, by default, the *same* subject in a changed
> state — identity continuity is the default outcome of any declared transformation, exactly
> as `places.md`'s own corrected PLACE-03 already establishes for Place transformation
> generally, now extended explicitly to supernatural transformation of any subject. A
> subject's own species, kind, or form classification (human vs. vampire; living vs. undead)
> is a distinct fact from that subject's own identity — reclassifying a subject's own kind
> never, by itself, implies that subject's identity has been replaced by a new one. That
> stronger claim (identity replacement, rather than continuity) requires its own explicit
> declaration — a domain may validly declare that a specific transformation ends the original
> subject and creates a new one (e.g., necromancy over a corpse creating a new undead
> subject, rather than continuing the original person), but this is never assumed by default.
> Summoning an already-existing subject to a new location, creating a genuinely new subject,
> projecting a temporary manifestation, and constructing a temporary construct are four
> distinct operations with different identity implications, never collapsed into one another.

**Disposition: ACCEPT — REQUIRED for the default-continuity and classification-≠-identity
requirements; which specific transformations declare replacement instead is PERMITTED,
domain-declared content.** Passes the admission test: this is the direct, explicit resolution
of the deferred boundary the batch instruction's own item 14 names — extending
`places.md`'s own corrected PLACE-03 default (identity continuity is the default outcome of a
declared transformation, displaced only by an explicit exception) to supernatural
transformation of *any* subject, not merely Places. The genuinely new content beyond that
direct extension is the **species/kind/form ≠ identity** distinction (item 15), which no
earlier Rule states — Batch 01's own ID-03/06 address transformation/identity generally but
do not name "classification" as its own, third fact alongside identity and transformed state.

**Repository evidence: MISSING, for any supernatural transformation mechanism; PARTIAL, by
close non-supernatural analogue.** No human→vampire, living→undead, or comparable
supernatural transformation mechanism exists anywhere in this repository — confirmed via
direct search. Two real, non-supernatural transformation mechanisms already demonstrate
exactly this Rule's own required shape, though neither is itself magical:
`TransformationService` (`src/world/transformation.py`) transforms a Region's own `kind`
(FOREST → BURNT_FOREST → WASTELAND) based on trauma/calamity thresholds while the Region's
own identity never changes; `EvolutionSystem` (`src/engine/evolution.py`) transforms an
entity's own capability/role at growth milestones while the entity's own identity persists
throughout. Both confirm this repository's own architecture already implements
identity-persists/classification-changes as its own real, working pattern for ordinary
causal transformation — direct, if non-supernatural, evidence this Rule's own required shape
is architecturally sound here, not merely aspirational.

**Scenarios:** [MAG-S19](../scenarios/magic-supernatural-batch-12.md#mag-s19) (enchanted
sword), [MAG-S20](../scenarios/magic-supernatural-batch-12.md#mag-s20) (artifact recreated),
[MAG-S21](../scenarios/magic-supernatural-batch-12.md#mag-s21) (human → vampire),
[MAG-S29](../scenarios/magic-supernatural-batch-12.md#mag-s29) (ordinary creature →
supernatural regional threat).

---

## STR-02 — Death, resurrection, and undeath must not be silently collapsed into one default relationship where a domain models resurrection or undeath at all; death remains a real historical fact even where a valid supernatural process later reactivates the subject, resurrection restoring the same identity is a distinct question from a corpse becoming the basis for a genuinely new undead subject, and neither is assumed by default — each requires its own declared supernatural process

> A subject's own death, once it occurs, remains a real historical fact regardless of any
> later supernatural process — resurrection is never permitted to retroactively erase that
> death occurred (`history-provenance`'s own persistence-of-history discipline, applied here).
> Whether a valid resurrection process restores the *same* identity that died is a fact that
> specific process must declare, never assumed by default; whether necromancy over a corpse
> produces a *new* undead subject rather than reviving the original is likewise a distinct,
> separately-declared question — resurrection is never assumed to be the same operation as
> undead creation merely because both begin from a corpse. Whether memory, ownership, or
> social status automatically restore alongside a resurrected identity is a further,
> independently-declared question this Rule does not pre-answer. None of this requires this
> world to model resurrection or undeath at all — the distinctness requirement applies only
> where a domain chooses to model either.

**Disposition: ACCEPT — REQUIRED for the distinctness-where-modeled requirement; whether
resurrection or undeath exist in this world at all is PERMITTED, content-dependent.** Passes
the admission test: no earlier Rule addresses death/resurrection/undeath distinctness at all
— this is squarely new content the batch instruction's own item 16 asks to be "probed
carefully," combining History/Provenance's already-established "historical facts persist"
pattern with Identity's own transformation-requires-declaration pattern for the specific,
high-stakes case where the transformation in question is death itself being causally
reversed. The genuinely new content is the explicit three-way non-collapse this Rule states:
death-persists-as-history ≠ resurrection-restores-same-identity ≠ undeath-creates-new-
identity, none of which any earlier Rule distinguishes. **Revised 2026-09-22 per a targeted
semantic-cleanup follow-up:** the disposition now explicitly separates the two claims this
Rule actually makes — the three-way distinctness is REQUIRED wherever a domain models any of
these processes, but nothing here requires this world to commit to resurrection or undeath
existing at all, matching the same required-distinctness/permitted-existence split
`supernatural-ontology.md`'s SUP-02 and this file's own STR-01 already use.

**Repository evidence: MISSING.** No resurrection, undeath, or comparable supernatural
death-reversal mechanism exists anywhere in this repository — confirmed via direct search.
This repository's own real death/lifecycle machinery (`LifecycleSystem`, reused from prior
batches' own evidence) already treats death as a real, permanent, historical event with no
reversal path at all, which is consistent with — though narrower than — this Rule's own
target semantics (which permit, but do not require, a declared reversal process to exist).

**Scenarios:** [MAG-S22](../scenarios/magic-supernatural-batch-12.md#mag-s22)
(resurrection), [MAG-S23](../scenarios/magic-supernatural-batch-12.md#mag-s23) (undead new
identity, counter).

---

## Inherited / Applied Foundational Rules

### Summoning, creation, manifestation, and temporary construction are governed by STR-01's own identity-continuity-versus-replacement discipline, applied to each specific operation

> Whether summoning relocates an already-existing subject, or creating/projecting/
> constructing produces a genuinely new one, follows the same declared-determination
> discipline STR-01 already states generally — no new claim beyond applying it to these four
> specific operation shapes.

**Disposition: INHERITED — direct reuse of this file's own STR-01. No new claim.**

**Repository evidence: MISSING.**

**Scenarios:** none newly traced; the distinct-operations claim is already stated within
STR-01's own text above.

### Souls, where a domain chooses to model them as an objective concept, require their own declared identity, persistence-after-death, body, and memory relations, exactly as any other durable state requires; no living entity is assumed to have an objective soul merely because fantasy genre convention usually includes one

> If a domain commits to objective souls existing, it must declare how a soul relates to
> identity, to persistence after death, to the body, and to memory — the same Durable State
> Rule discipline this Catalog already requires for any persistent subject. Nothing in this
> family assumes objective souls exist by default.

**Disposition: INHERITED — direct reuse of this Catalog's own general Durable State Rule
(any subject that survives beyond the current tick requires a typed model, a stable
location, a defined lifecycle, and tests) and Identity's own ID-03/06, applied to the
specific, optional case of an objective soul concept. No new claim — and per the batch
instruction's own explicit permission, this remains a possible future supernatural ontology,
not a required Rule family, since no repository or design evidence commits this world to
objective souls.**

**Repository evidence: MISSING.**

**Scenarios:** none newly traced.

---

## Scope / Deferred Boundaries

### Objective souls as a required Rule family

> This family does not commit this world to objective souls existing — per the batch
> instruction's own explicit permission, this remains available as a future supernatural
> ontology if a domain later needs it, never a required concept introduced here.

**Disposition: SCOPE BOUNDARY.**

### Concrete transformation-content catalog (specific creature forms, corruption chains, artifact types)

> This family states the identity-continuity default and the classification-≠-identity
> distinction (STR-01) but does not design a concrete catalog of specific transformation
> chains, forms, or creature kinds — implementation-level, domain-specific content.

**Disposition: SCOPE BOUNDARY.**

---

## Repository Findings (significant, cross-referenced)

**These are repository/implementation facts, not World Rule decisions, and imply no delivery
priority.**

- **Confirmed MISSING — no supernatural transformation, resurrection, undeath, soul, or
  summoning mechanism exists anywhere in this repository.** See STR-01/STR-02 above.
- **A significant, notable finding, not itself a gap.** `TransformationService`
  (`src/world/transformation.py`, region kind-shifting) and `EvolutionSystem`
  (`src/engine/evolution.py`, entity growth-milestone transformation) are both real,
  non-supernatural mechanisms already implementing exactly the identity-persists/
  classification-changes shape STR-01 requires — the closest available evidence that this
  repository's own architecture already supports this Rule's own target shape, even though
  neither is itself magical.

## Cross-domain links recorded here

- STR-01 → Places (`places.md`'s corrected PLACE-03 — the default this Rule directly
  extends), Identity (ID-03/06, Batch 01)
- STR-02 → History/Provenance (Foundational — historical persistence), Identity (ID-03/06,
  Batch 01)
- Inherited souls entry → this Catalog's own Durable State Rule, Identity (ID-03/06)

## Open questions carried forward

1. **When does a magical transformation preserve identity, versus establish a declared
   exception?** STR-01 states the default; which specific transformations a future domain
   declares as exceptions is not decided here.
2. **Does this world require an objective soul concept?** Not decided here — deferred per
   the Scope Boundary above.
3. What distinguishes a magical species/kind classification from a merely temporary magical
   condition (e.g., a permanent vampire classification versus a temporary polymorph)? Not
   decided here — a design-semantic question for a future domain to resolve.
