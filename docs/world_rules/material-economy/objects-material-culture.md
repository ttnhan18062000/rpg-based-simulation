---
status: authoritative
layer: architecture
authority: P1
audience: agent
tags: [architecture, world, content]
last_verified: "2026-09-23"
---

# World Rule Family: Objects / Material Culture

**Purpose/scope.** What makes an object a persistent world subject or material thing rather
than merely an inventory number. Distinguishes object identity from ownership, holder/
location, value, and resource quantity. Does not require every commodity unit to be a
first-class object. Applies the strict Rule-admission discipline established in Batch 07's own
follow-up review from the first draft — Rule statements below state only target world
semantics; every repository fact lives in Repository evidence/Findings.

**Status.** Batch 08 (Objects/Ownership/Resources/Economy), drafted 2026-09-22, revised the
same day per follow-up review (`tmp/world-rule-batch-8-followup-ext-ai.md`): OBJ-02 reworded
to state the fungible-vs-individuated representational choice as its own semantic distinction
(not a specific promotion-mechanism description) and extended with a provenance-traceability
requirement upon individuation; OBJ-03 reclassified from a Domain Rule to Inherited — History/
Provenance's own HP-02 ("a historically significant fact, record, or *artifact* should be
traceable to what actually produced it") and HP-05 (significance may legitimately fade) already
apply to any first-class simulation subject, records and artifacts included, not entities
alone, so "an object can accumulate history/significance" adds no genuinely new claim beyond
those two Rules. Candidates below originated as external-reviewer hypotheses
(`tmp/world-rule-batch-8-ext-ai.md`); each carries this session's disposition and repository
evidence. Structured per the normalized five-category methodology.

---

## Domain Rules

## OBJ-01 — Object identity is distinct from ownership, holder/location, value, and resource quantity

> An object's own persistent identity does not change merely because who owns it, who holds
> it, where it is, what it is worth, or how much of a fungible substance exists changes. A
> sword changing owner does not change which sword it is.

**Disposition: ACCEPT.** Passes the admission test: no earlier Rule states object identity's
own distinctness from these specific relational facts — Batch 01's ID-* family addresses
entity/subject identity, a different kind of thing, never physical-object identity.

**Repository evidence: SUPPORTED.** `ItemInstance` (`docs/mechanics/03_economic_laws.md` §7,
`TCK-20260831-ITEM-INSTANCE-HISTORY`) is a real, additive layer tracking one specific physical
item's own identity and `owner_history` *on top of* `ItemStack`'s ordinary quantity-by-`item_id`
tracking — the two representations coexist without collapsing: an item's `ItemStack` entry
(quantity, weight, slot) changes constantly as it moves between holders, while its own
`ItemInstance` (when one exists) keeps a single, append-only identity record untouched by any
of that. `HomeStorageService`'s access-controlled private storage (only the owning entity may
deposit/withdraw, `docs/mechanics/03_economic_laws.md` §6) further confirms this repository
already models "owner" and "current holder" as separable facts about the same object — the
same object is the owner's regardless of where it physically sits.

**Scenarios:** [ME-S01](../scenarios/material-economy-batch-08.md#me-s01) (sword changes
hands), [ME-S14](../scenarios/material-economy-batch-08.md#me-s14) (ordinary object becomes
relic).

---

## OBJ-02 — Material things may be represented as fungible quantities or as identity-bearing objects, and meaningful provenance must remain traceable across that boundary

> Material things may be represented as fungible quantities when individual continuity does
> not matter, or as identity-bearing objects when individual history/provenance matters — a
> world is not required to track every unit of a substance individually, nor forbidden from
> doing so once a specific instance's own history becomes relevant. Where a fungible quantity
> becomes individuated (a specific unit is distinguished from the rest of its stack), any
> meaningful provenance the source material already carried must remain traceable through that
> individuation, not silently dropped.

**Disposition: ACCEPT, revised 2026-09-22 per follow-up review — reframed from a
representation-strategy description (a specific "promotion mechanism") to the underlying
semantic distinction and its own provenance requirement.** The original wording risked being
read as prescribing a particular simulation/LOD implementation technique rather than stating a
world law; the fix keeps the semantic core (fungible-vs-individuated representation is a
legitimate world choice) and adds the substantive requirement the original draft only implied
(provenance must survive individuation). Passes the admission test: no earlier Rule states
this representational distinction or the provenance-continuity requirement across it.

**Repository evidence: SUPPORTED for the representational distinction, as this repository's
own real, declared design; MISSING for the provenance-continuity requirement specifically —
checked directly, not assumed satisfied merely because the distinction itself exists.**
`ItemStack` (quantity by `item_id`) is the default representation for every item;
`ItemInstance` is a strictly opt-in, additive layer for items flagged `significant=True` at
creation — a real instance of the fungible/individuated distinction this Rule describes, not a
hypothetical. **Confirmed MISSING/INERT:** zero production call sites currently set
`significant=True` (`docs/mechanics/03_economic_laws.md` §7's own explicit disclosure), and the
feature is additionally gated by `ENABLE_ITEM_INSTANCE_HISTORY` (default OFF). Because
individuation never actually occurs in production, this repository has no occasion to exercise
the provenance-continuity half of this Rule either — checked directly: no code path was found
that would carry a source stack's own history (e.g., which node it was harvested from, which
batch it was crafted in) forward into a newly-individuated `ItemInstance`'s own record; the
`ItemInstance` schema itself only begins `owner_history` from the moment of individuation
onward, with no field for anything the source material carried before that moment.

**Scenarios:** [ME-S05](../scenarios/material-economy-batch-08.md#me-s05) (resource
conversion), [ME-S14](../scenarios/material-economy-batch-08.md#me-s14) (ordinary object
becomes relic), [ME-S17](../scenarios/material-economy-batch-08.md#me-s17) (individuation from
fungible material, added per 2026-09-22 follow-up).

---

## Inherited / Applied Foundational Rules

### An object may accumulate provenance/significance through its own participation in world events (originally drafted as OBJ-03)

> A specific object may become historically significant through what has actually happened to
> or through it. This significance is a durable fact about that particular object, distinct
> from any general fact about its item type or its current holder's own significance.

**Disposition: INHERITED — reclassified 2026-09-22 per follow-up review, from a Domain Rule
(originally drafted as OBJ-03) to this Inherited entry.** Checked directly against the scope of
History/Provenance's own foundations: HP-02 already states that "a historically significant
fact, record, or *artifact* should be traceable to what actually produced it" — explicitly
naming artifacts, not entities alone — and HP-05 already states that "a fact's prominence...
may legitimately diminish over time" using fully generic language, never restricted to
entities. Both Rules already apply to any first-class simulation subject, records and
artifacts included. "An object can accumulate history/significance" is therefore HP-02/HP-05
applied at Objects' own point of use, not a genuinely new claim — this family does not
maintain a parallel object-history ontology alongside History/Provenance's own one. The
flagship trajectory (ordinary object → historically important events → recognized relic)
remains fully supported by this reclassification, not weakened by it: HP-02 supplies the
provenance-traceability requirement, HP-05 supplies the significance-fading permission, and
this repository's own `ItemInstance.owner_history` mechanism (below) is the concrete
object-specific instance of HP-02's own general causal-ancestor requirement.

**Repository evidence: SUPPORTED for the mechanism's own design; MISSING for any live trigger
that actually exercises it.** `ItemInstance.owner_history` is explicitly `append-only`
(`docs/mechanics/03_economic_laws.md` §7's own Ownership Transfer Law) — exactly the durable,
accumulating causal-ancestor record HP-02 requires, committed only through `ApplyPath.
apply_generation()`, no other code path permitted to mutate a live `ItemInstance`. But because
zero production call sites ever set `significant=True` (OBJ-02's own confirmed finding), no
object in this repository has ever actually begun accumulating such a record — the flagship
trajectory HP-02/HP-05 jointly permit is, today, never realized in practice. This repository
has not yet declared *what* participation in a world event should trigger the initial
promotion to `ItemInstance` status, nor any mechanism translating accumulated `owner_history`
into recognition, value, or relic status once promoted.

**Scenarios:** [ME-S14](../scenarios/material-economy-batch-08.md#me-s14) (ordinary object
becomes relic, flagship).

### Object creation and destruction require a real causal path, and a new creation establishes a new object identity

> An object coming into existence or ceasing to exist must trace to a real cause; a genuinely
> new object (as opposed to a modification of an existing one) establishes its own new
> identity, never a continuation of whatever it was made from.

**Disposition: INHERITED — direct reuse of CAUSE-01 (a consequence requires a real causal
path) and ID-04 (creation establishes identity, reused for reproduction in Batch 05). Applying
these to object creation/destruction and material transformation adds no new claim beyond what
those two Rules, combined, already require.**

**Repository evidence: SUPPORTED.** `docs/mechanics/03_economic_laws.md` §5's Crafting law
("source materials are destroyed and the product is created in the same tick") is a real,
CAUSE-01-compliant destruction-and-creation pair, gated on a declared recipe process — never an
arbitrary object appearing or vanishing. The new crafted item receives its own fresh identity
(a new `ItemStack`/potential `ItemInstance`); nothing in the crafting path attempts to carry the
consumed materials' own prior identity forward into the product — production is a legitimate
identity break point, per ID-04's own claim, not an exception to it.

**Scenarios:** [ME-S05](../scenarios/material-economy-batch-08.md#me-s05).

### Equipment durability is a persistent, capability-relevant object condition

> An object's own durability/condition is real, persistent state, and its degradation to zero
> removes that object's own stat contribution — not a cosmetic record.

**Disposition: INHERITED — direct reuse of Batch 07's PROG-01/PROG-03 own evidence
(`recalculate_combat_stats()`'s equipment step, `durability <= 0` zeroing contribution). No new
claim: this family's own investigation of "durability/condition" (§1) lands on exactly the
mechanism Batch 07 already established and cited as evidence for capability-independent-of-
Level.**

**Repository evidence: SUPPORTED**, reused directly from Batch 07's own PROG-01/PROG-03
evidence.

**Scenarios:** none newly traced; reuses Batch 07's own CP-S07 evidence directly.

---

## Scope / Deferred Boundaries

### Universal first-class-object requirement

> This family does not require promoting every commodity/resource unit to first-class object
> status — `ItemStack`'s fungible-quantity representation remains the legitimate default, per
> the batch instruction's own explicit "do not require every commodity unit to be a first-class
> object" instruction.

**Disposition: SCOPE BOUNDARY.**

### What makes an item worth promoting to `ItemInstance` status

> This family confirms the promotion mechanism (`ItemInstance`) is real and correctly designed,
> but does not decide the trigger criteria for *which* objects should actually be promoted
> (participation in what kind of event, at what threshold) — that remains an explicit open
> design decision this repository has not made, not a gap this batch closes.

**Disposition: SCOPE BOUNDARY.**

---

## Repository Findings (significant, cross-referenced)

**These are repository/implementation facts, not World Rule decisions.** The Rules above
state what this family's own target semantics require and permit; the findings below report
where this repository's own current implementation does or does not realize them. Whether and
how to act on any of them is an implementation-planning decision this Rule Catalog identifies
but does not make.

- **The most load-bearing finding in this family, shared with `ownership-possession.md`'s own
  inheritance finding as this batch's two most significant discoveries.** The `ItemInstance`
  provenance/significance mechanism (OBJ-02's own individuation/provenance claim, and the
  Inherited HP-02/HP-05 entry above) is fully designed and wired end-to-end
  (`ItemInstanceUpdate`, `ApplyPath.apply_generation()`, an append-only `owner_history`), but
  **INERT/OFF**: gated behind `ENABLE_ITEM_INSTANCE_HISTORY` (default OFF) and, independently,
  never triggered by any production call site (`significant=True` is set nowhere in
  production code). The "ordinary object becomes relic" flagship trajectory this batch was
  specifically asked to check is therefore causally *permitted* by this repository's own
  design, but never actually realized today — not merely an unbuilt feature (MISSING), but a
  built-and-wired mechanism nothing ever switches on, matching the exact shape of Batch 07's
  own `Breakthrough`-granting and `combat_engagement` findings.
- **Crafting destroys/creates cleanly, with no provenance carry-forward** — confirmed by direct
  inspection of the Crafting law; consistent with the Inherited creation/destruction entry
  above, not a gap.

## Cross-domain links recorded here

- OBJ-01 → State Ownership (Batch 01's own OWN-01/02/06, the general owner/holder-distinctness
  pattern this family instantiates for physical objects specifically)
- OBJ-02 → History/Provenance (HP-02, the provenance-traceability requirement this Rule's own
  individuation clause extends specifically to what a source stack carries)
- Inherited HP-02/HP-05 entry (formerly OBJ-03) → History/Provenance (HP-02, HP-05, direct
  reuse, not a new category)
- Inherited creation/destruction entry → Identity (ID-04), Causality (CAUSE-01)
- Inherited durability entry → Capability/Progression (`capability-progression.md`'s PROG-01/
  PROG-03, Batch 07)

## Open questions carried forward

1. Whether `ENABLE_ITEM_INSTANCE_HISTORY` should be turned on, and what trigger criteria
   should set `significant=True` in production, is a real design/implementation question not
   decided here.
2. Whether accumulated `owner_history`/provenance should ever translate into recognition,
   value, or relic-status content is flagged for a future batch (most plausibly Social
   relations, or a later Economy-focused pass on value/price) — not decided here.
