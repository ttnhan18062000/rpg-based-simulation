---
status: active
layer: architecture
authority: P1
audience: agent
tags: [architecture, world, content]
---

# World Rule Family: Magical Effects

**Purpose/scope.** How a supernatural cause's own resulting consequence is owned across
domain boundaries, when a magical effect requires its own continuing durable supernatural
state versus a one-time trigger of an ordinary persistent effect, and how resistance and
magical conflict are governed. Does not decide capability (see `magic-capability.md`) or
transformation (see `supernatural-transformation.md`).

**Standing direction (`tmp/world-rule-direction.md`).** Rule statements describe only target
world semantics; repository classification records realization only, never delivery priority.

**Status.** Batch 12 (Magic/Supernatural), drafted per a corrected instruction file
(`tmp/world-rule-batch-12-corrected-ext-ai.md`).

---

## Domain Rules

## EFF-01 — A magical effect's own supernatural cause is distinct from the resulting consequence's own canonical ownership; the domain a magical effect targets (Body, Capability, Knowledge, Object, Place, Relationship, Authority, Resource, Movement) owns the resulting durable consequence, and magic is never the canonical owner of every downstream effect it produces

> Magic generally produces an effect *into* another domain — it does not become the
> canonical owner of all resulting state. A fire spell's own magical cause produces bodily
> harm; Life/Body owns the resulting injury. A memory spell's own supernatural cause changes
> Knowledge/Memory state; the Knowledge domain owns the result. A curse's own magical cause
> changes capability; the Capability domain owns the lasting effect. The producer of a
> consequence is never automatically its canonical owner — this holds for magic exactly as it
> already holds for every other cross-domain causal producer this Catalog has established.

**Disposition: ACCEPT — REQUIRED.** Passes the admission test: this Catalog's own durable-
state architecture already requires that authoritative state be committed only through its
owning domain's own authoritative path (this project's own core architecture rule) — but no
earlier Rule states the specific risk this domain uniquely carries: that a `MagicState`
becomes an informal dumping ground for every magically-caused outcome across every other
domain, simply because magic was the proximate cause. Stating this explicitly, and naming the
specific candidate target domains, is this Rule's own genuinely new content, directly
required by the batch instruction's own explicit warning against exactly this anti-pattern.

**Repository evidence: MISSING.** No magical-effect mechanism exists to check cross-domain
ownership against — but the general pattern this Rule requires is otherwise already
confirmed sound for non-magical cross-domain causal producers throughout this Catalog (Batch
09's own SOC-03 causal-path entries, Batch 10's own ORG-03), which is direct, if
non-supernatural, evidence that this repository's own architecture already supports the
discipline this Rule requires.

**Scenarios:** [MAG-S09](../scenarios/magic-supernatural-batch-12.md#mag-s09) (permanent
spell with no ongoing magic), [MAG-S17](../scenarios/magic-supernatural-batch-12.md#mag-s17)
(memory alteration), [MAG-S28](../scenarios/magic-supernatural-batch-12.md#mag-s28) (magic
creates political consequence).

---

## EFF-02 — A magical effect requires its own continuing durable supernatural state only where the supernatural cause must itself remain active to sustain the consequence; a one-time magical cause that produces an ordinary persistent downstream effect (e.g., a spell causing a wound that then heals or persists normally) requires no continuing magical state at all, and where persistent supernatural state does exist, it requires its own explicit lifecycle semantics (duration, expiration, maintenance, dispel/removal condition), never assumed to be permanent or removable by default; conflicting supernatural effects must not produce undefined authoritative state

> "Magic caused this" is not, by itself, a reason to keep a magical state alive — the test is
> whether the *cause* must keep existing for the *consequence* to continue. A spell causing a
> wound produces an ordinary persistent Body-owned condition once the spell itself is done; no
> continuing magical state is required. A curse that continuously suppresses strength requires
> the curse's own persistent supernatural state to keep existing, because removing the curse
> should remove the suppression. Where persistent supernatural state exists at all (curse,
> blessing, enchantment, pact, ward, magical mark), the specific mechanism must declare its own
> duration, expiration, maintenance requirement, and removal/dispel condition — none of these
> is assumed true or false by default. Where two or more supernatural effects interact or
> conflict, the declared mechanism must resolve them to a definite, coherent authoritative
> state — conflicting supernatural effects are never permitted to leave that state undefined,
> though the specific resolution (priority, suppression, stacking, incompatibility) remains
> domain-specific.

**Disposition: ACCEPT — REQUIRED.** Passes the admission test: no earlier Rule distinguishes
"magic as an ongoing cause" from "magic as a one-time trigger of an ordinary persistent
effect" — this is a genuinely new supernatural-specific refinement, since ordinary causal
producers in this Catalog rarely raise the question of whether the *producer itself* must
keep existing for its own *effect* to persist (an ordinary sword blow does not need to keep
happening for the wound it caused to remain). The lifecycle-declaration requirement, and the
no-undefined-state-on-conflict requirement, are the specific, named content this Rule adds
beyond the general determinism discipline this Catalog's own architecture already requires.

**Repository evidence: MISSING.** No persistent supernatural state (curse, blessing,
enchantment) exists anywhere in this repository to check lifecycle semantics against.

**Scenarios:** [MAG-S10](../scenarios/magic-supernatural-batch-12.md#mag-s10) (persistent
curse), [MAG-S11](../scenarios/magic-supernatural-batch-12.md#mag-s11) (dispel removes
curse).

---

## Inherited / Applied Foundational Rules

### Supernatural resistance, immunity, and conditional vulnerability are permitted, mechanism-specific facts, distinct from capability, authority, or certainty of failure; no universal resistance system is required, and a supernatural mechanism may be fully deterministic under its own declared conditions

> Whether a target resists, is immune to, or is conditionally vulnerable to a given
> supernatural effect is that specific mechanism's own declared property — never a universal
> saving-throw requirement. Resistance is never the same fact as capability, authority, or a
> guarantee of failure.

**Disposition: INHERITED — direct reuse of `supernatural-ontology.md`'s own declared-
dimensions entry (resistance is one of the candidate dimensions a supernatural mechanism may
declare), combined with Batch 02/07's own capability/authority distinctness family. No new
claim beyond confirming resistance is one more mechanism-specific, declared dimension, not a
universal system.**

**Repository evidence: MISSING.**

**Scenarios:** none newly traced; the absence itself.

### Magic and law: where existing law/jurisdiction semantics already provide the necessary scope over supernatural acts, this family reuses them directly rather than building a parallel "magic law," and a law prohibiting a spell never, by itself, prevents that spell from being physically cast

> A law may prohibit a supernatural act. That prohibition does not prevent the act from
> physically occurring — a mage capable of casting a prohibited spell remains capable of
> casting it; whether the violation is detected and enforcement follows is a fully separate
> question, exactly as `law-enforcement.md`'s own LAW-01 already requires for any law.

**Disposition: INHERITED — direct reuse of Batch 10's LAW-01 (law/knowledge/compliance/
detection/adjudication/sanction are distinct facts) and LAW-03 (jurisdiction has a declared
scope), applied to supernatural acts specifically. No new claim.**

**Repository evidence: MISSING, reusing LAW-01's own evidence directly** — no in-world law
subsystem exists at all.

**Scenarios:** [MAG-S07](../scenarios/magic-supernatural-batch-12.md#mag-s07) (illegal magic
still works).

### Magic and institutions/authority/culture: supernatural power may causally influence authority, practical power, or legitimacy, but never automatically substitutes for any of them; institutional or cultural recognition never makes a supernatural claim objectively true, and objective magic never automatically synchronizes social interpretation

> An institution declaring a person divine does not grant that person real supernatural
> capability; real supernatural capability does not automatically grant political, legal, or
> social authority, and an institution may validly refuse to recognize it — a god may
> objectively grant authority a society refuses to recognize, and a society may recognize a
> priest whose claimed divine authority is false; both are representable. Likewise, a culture
> may revere, fear, misunderstand, deny, or normalize magic without that reaction
> automatically tracking objective supernatural truth, and cultural belief never alters
> supernatural truth unless a specific supernatural mechanism explicitly contains a
> belief-powered conversion edge (`supernatural-ontology.md`'s SUP-02).

**Disposition: INHERITED — direct reuse of Batch 10's INST-03/INST-04 (authority/capability/
power/legitimacy correlated, never substitutable; legitimacy's relationship to authority is
institution-declared) and `collective-belief.md`'s BEL-01/BEL-02 (collective belief ≠
individual belief ≠ world truth; social belief ≠ supernatural truth/mechanism), applied to
supernatural power and magical/divine authority specifically. No new claim: supernatural
power is simply one more correlated-but-not-substitutable input alongside wealth or military
capability, which INST-03 already generalizes over, and cultural reaction to magic is simply
BEL-01/02 applied to this specific topic.**

**Repository evidence: MISSING, for any supernatural-power-to-authority or magic-culture
mechanism.** `FactionState.military_strength` (Batch 10 evidence) remains the closest
non-supernatural analogue for a tracked "power" input; nothing supernatural exists to check
the same boundary against yet.

**Scenarios:** [MAG-S07](../scenarios/magic-supernatural-batch-12.md#mag-s07) (magic and
institutions), [MAG-S27](../scenarios/magic-supernatural-batch-12.md#mag-s27) (false
religious belief, real magic elsewhere).

### Environment and Ecology own their own resulting state where magic alters them; magic owns the ongoing supernatural cause only where it persists, exactly as EFF-01/EFF-02 already require generally

> Magic altering weather, terrain, hazard, resource behavior, or a species' own survival
> viability is governed by the same cross-domain ownership (EFF-01) and lifecycle (EFF-02)
> discipline already stated for any magical effect — Environment and Ecology own the resulting
> durable state; magic owns only the ongoing cause, where one continues to exist.

**Disposition: INHERITED — direct reuse of this file's own EFF-01/EFF-02, applied to
Environment/Ecology specifically, per the batch instruction's own explicit request to check
compatibility with those domains. No new claim.**

**Repository evidence: MISSING.**

**Scenarios:** none newly traced.

---

## Scope / Deferred Boundaries

### Concrete magical-conflict resolution algebra

> This family states the minimum requirement (conflicting supernatural effects must not
> produce undefined authoritative state, EFF-02) but does not design a universal resolution
> algebra (priority, suppression, stacking rules) — domain-specific resolution is valid,
> deferred per the batch instruction's own explicit "do not design a universal resolution
> algebra unless evidence requires it."

**Disposition: SCOPE BOUNDARY.**

### Detailed fantasy ecology/species content

> This family confirms magical/ecological compatibility is architecturally possible
> (Inherited above) but does not design detailed supernatural species, biomes, or ecological
> content — implementation-level, domain-specific content.

**Disposition: SCOPE BOUNDARY.**

---

## Repository Findings (significant, cross-referenced)

**These are repository/implementation facts, not World Rule decisions, and imply no delivery
priority.**

- **Confirmed MISSING — no magical-effect, persistent-supernatural-state, or magical-
  conflict mechanism exists anywhere in this repository.** See EFF-01/EFF-02 above.
- **A significant, notable finding, not itself a gap.** This repository's own real,
  non-supernatural cross-domain causal producers (e.g., a combat hit producing a Body-owned
  wound, never a `CombatState`-owned one) already demonstrate the exact ownership discipline
  EFF-01 requires — confirming this Catalog's own architecture is already structurally
  compatible with this requirement, not merely aspirational.

## Cross-domain links recorded here

- EFF-01 → this project's own core durable-state architecture rule (authoritative state
  committed only through its owning domain)
- EFF-02 → History/Provenance (Foundational — the "does the cause need to persist" question
  parallels HP-family reasoning about what survives ordinary change)
- Inherited resistance entry → `supernatural-ontology.md`'s own declared-dimensions entry
- Inherited magic-and-law entry → Law/Enforcement (LAW-01/03, Batch 10)
- Inherited magic-and-institutions/culture entry → Roles/Institutions (INST-03/04, Batch 10),
  Collective Belief (BEL-01/02, Batch 11B)
- Inherited environment/ecology entry → Life/Ecology/Population (Batch 05)

## Open questions carried forward

1. **Which magical effects require persistent source state, versus a one-time trigger of an
   ordinary downstream effect?** EFF-02 states the test (does the cause need to keep
   existing); which specific effects fall on which side of that test is not decided here.
2. **Is supernatural state a cause or a durable consequence, in any specific case a future
   domain designs?** Not decided here — this is the design-semantic question EFF-01/EFF-02
   together exist to let a future author answer correctly.
