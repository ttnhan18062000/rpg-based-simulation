---
status: active
layer: architecture
authority: P1
audience: agent
tags: [architecture, world, content]
---

# World Rule Family: State Ownership

**Purpose/scope.** How authoritative truth is distributed across domains without duplication or
silent conflict, and how a proposed change relates to a committed one. This family operationalises
`core_rpg_design_direction.md` §7's canonical-state-ownership rule and `simulation-rule-world-law-
design-preparation.md` §2's three-way distinction (Semantic Home ≠ State Ownership ≠ Participating
Domains) as actual Rules a future domain author can cite directly, rather than only as design-doc
prose.

**Status.** Foundational Batch 01, first draft.

---

## OWN-01 — One authoritative source of durable truth

> Every durable authoritative state concept has an unambiguous canonical owner. Multiple systems
> may consume, interpret, react to, or derive from the state. They must not independently
> establish conflicting authoritative truth for the same concept.

**Disposition: ACCEPT.** This is the Rule-Catalog restatement of an already-adopted P1 principle
— nothing new is being decided here, only made citable at Rule granularity.

**Repository evidence: SUPPORTED architecturally.** The authoritative apply pipeline (typed
`*Update` objects → `*Patch.apply()` → `AuthoritativeState`) is the concrete mechanism that makes
this rule true by construction rather than by convention alone — a durable field can only be
written through the one apply path its own Patch class owns.

**Scenarios:** [FND-S07](../scenarios/foundational-batch-01.md#fnd-s07), [FND-S08](../scenarios/foundational-batch-01.md#fnd-s08).

---

## OWN-02 — Participation does not imply ownership

> Reading, consuming, reacting to, or causing a change in state does not make a domain the
> canonical owner of that state. The producer of a consequence and the owner of the resulting
> durable state may differ.

**Disposition: ACCEPT unchanged.** The worked example given (`combat causes injury → Life/Body
owns injury`; `death may trigger succession → Lineage owns succession state`) is exactly right and
is kept as written — it's the same example this session's own preparation-artifact ownership
clarification already used.

**Repository evidence: SUPPORTED.** `WoundState`/`ScarState` (the durable injury record) live on
the entity's own state, read and written through the Life/Body-owned patch path; `Combat` produces
the triggering event but is never the thing that commits the wound record. Succession similarly:
`LifecycleSystem` (Life-domain code) detects death, but the actual heir/inheritance write happens
through `LifecycleUpdate`/`LifecyclePatch`, and the *lineage* meaning of that data (feud transfer,
dying wish) is a separate, Family/lineage-owned interpretation layered on top — not a second
authoritative copy.

**Scenarios:** [FND-S07](../scenarios/foundational-batch-01.md#fnd-s07), [FND-S08](../scenarios/foundational-batch-01.md#fnd-s08).

---

## OWN-03 — Derived views are not duplicate truth

> Multiple domains may derive views, classifications, scores, or signals from authoritative state
> without becoming additional owners of that state.

**Disposition: ACCEPT, with one factual correction to the example list — precisely the challenge
this rule's own review checklist asked for.**

**Checked directly, per example:**
- **Scarcity ratio** — confirmed DERIVED. Never stored; computed at read time as
  `remaining_charges / max_charges` from the owned `ResourceNodeState`.
- **Threat classification** — confirmed DERIVED. `RegionThreatClassifier` is explicitly read-only
  and perspective-based; it never writes state.
- **Reputation interpretation** — confirmed **not a clean example either way**. There are two
  separately *owned* authoritative fields already (`SocialComponent.public_reputation`, a clamped
  scalar; `PublicReputationProfile.labels`, an independent qualitative map) — neither is derived
  from the other, both are real owned state in their own right (this session's own social-systems
  evidence found this exact naming collision earlier). A genuinely *derived* view built on top of
  either — e.g. a shop discount computed from `public_reputation` — is derived; the reputation
  fields themselves are not.
- **Combat readiness — corrected, this is not a derived-state example at all.** Checked directly:
  `entity.combat.readiness` is a real, directly owned, authoritative field (`src/core/state.py`),
  written through the normal Combat-domain patch path — not computed at read time from anything
  else. The original candidate list was wrong to cite it here.
- **Economic opportunity** — confirmed DERIVED. `QuestOpportunity`/`WorldSignal` are explicitly
  documented as read-only, non-persisted projections over pressure signals.

**Repository evidence: SUPPORTED**, once the readiness example is removed — the corrected list
(scarcity ratio, threat classification, a reputation-derived discount, economic opportunity) is a
clean, real set of derived-state examples; the rule itself needed no change, only its illustration.

**Scenarios:** none yet directly probe this rule; flagged for the Perception/knowledge and
Economy/resources batches, where derived-state examples are dense.

---

## OWN-04 — Proposed change is distinct from committed state

> An intent, request, opportunity, decision, or proposed transition does not become authoritative
> world state merely because it exists. There must be a valid semantic path from proposal/cause →
> accepted transition → authoritative resulting state.

**Disposition: ACCEPT unchanged, kept deliberately semantic per the instruction's own guard
against turning it into an implementation API rule.**

**Repository evidence: SUPPORTED**, and this is close to the most concretely-proven rule in the
whole batch: it is already an explicit Hard Rule of this project ("do not mutate durable state
outside authoritative flows"), and the entire typed-`Update`-then-`Patch` architecture exists
specifically to make a proposed change and a committed one two different kinds of object at the
code level, not merely at the documentation level.

**Scenarios:** [FND-S09](../scenarios/foundational-batch-01.md#fnd-s09) (a false belief is a real
proposed-cause, never itself committed world truth).

---

## OWN-05 — Cross-domain transitions preserve ownership boundaries

> A causal chain may cross multiple owners without collapsing them into one domain. Each durable
> fact should remain authoritative in its appropriate semantic home/state owner.

**Disposition: ACCEPT, with the worked example's real repository support recorded per-link rather
than as one blanket claim — the chain given (`combat event → injury → impaired capability →
economic loss → relationship reaction`) is a good probe precisely because its links have
different support levels.**

**Repository evidence, per link:**
- `combat event → injury`: SUPPORTED (`WoundState`/`ScarState` carry real `atk_penalty`/
  `def_penalty`/`speed_penalty`/`max_hp_penalty` fields, applied through the Combat/Life boundary
  this rule describes).
- `injury → impaired capability`: SUPPORTED — the wound/scar penalties are read directly into
  combat-stat recalculation; capability is genuinely reduced, not merely flavour text.
- `impaired capability → economic loss`: MISSING. No mechanism translates a reduced combat stat
  into an economic consequence (lost wages, reduced harvesting rate, etc.).
- `economic loss → relationship reaction`: MISSING, for the same underlying reason — there's
  nothing upstream of it yet to react to.

**Scenarios:** [FND-S07](../scenarios/foundational-batch-01.md#fnd-s07) (traces exactly this
chain and stops where repository support stops — the scenario is *partially covered* by design,
not a failure of the scenario).

---

## OWN-06 — Historical reference does not imply present ownership

> History, provenance, chronicles, memories, and knowledge claims may reference durable or former
> state without becoming authoritative owners of the world fact they describe. A belief being held
> does not make it true.

**Disposition: ACCEPT unchanged.** This is the State-Ownership-family restatement of the
Fundamental World Contract's own "Information ≠ truth" row, made concrete for history/provenance
specifically.

**Repository evidence: SUPPORTED.** `BeliefEntry`/lead records are explicitly modelled as
possibly-wrong; nothing in the belief or chronicle machinery ever writes back into the
authoritative fact it describes (a chronicle entry recording "A owned the sword" cannot itself
change who owns the sword — ownership stays Objects-domain-owned regardless of what history says
about it).

**Scenarios:** [FND-S04](../scenarios/foundational-batch-01.md#fnd-s04), [FND-S09](../scenarios/foundational-batch-01.md#fnd-s09).

---

## Candidates considered and not added

One candidate rule was drafted during this batch and deliberately **not added**: a rule about
same-tick read/write ordering between domains ("a rule may read another domain's state but must
not assume it won't change underneath it without a defined ordering"). Rejected — this is
execution-order, an implementation concern the mechanism registry already tracks as a distinct
axis from functional dependency, not a semantic world truth. It fails `simulation-rule-world-law-
design-preparation.md` §2's own test 8 directly: the world would conceptually work identically
under a different tick-ordering implementation. Recorded here so a future author doesn't
re-propose it without knowing it was already considered.

## Cross-domain links recorded here

- OWN-02 → Combat, Life/Body, Family/lineage (the injury/succession worked examples)
- OWN-05 → Economy, Social relations (the two currently-missing links in the worked chain)
- OWN-06 → Perception/knowledge/information, History/significance (belief and chronicle,
  respectively)

## Open questions carried forward

1. Where does "impaired capability → economic loss" get designed — Economy/resources or
   Capability/progression? Deferred; either future batch should cite this open question rather than
   silently deciding it.
2. OWN-03's reputation example exposed a real *existing* naming collision between two owned
   fields, not a new design gap — flagged for the Social relations batch to formally document
   (not this batch's job to resolve, since neither field is being redesigned here).
