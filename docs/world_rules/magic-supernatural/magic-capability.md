---
status: authoritative
layer: architecture
authority: P1
audience: agent
tags: [architecture, world, content]
last_verified: "2026-09-23"
---

# World Rule Family: Magic Capability

**Purpose/scope.** What makes an entity capable of producing a supernatural effect; how
magical knowledge, capability, resource, reach, and authorization relate as semantically
distinct facts where a mechanism actually uses them; and how supernatural reach may or may not
bypass ordinary spatial topology. Builds on
Batch 02/03/04/07's own capability/cost/reach families. Does not decide cross-domain effect
ownership (see `magical-effects.md`) or transformation (see `supernatural-transformation.md`).

**Standing direction (`tmp/world-rule-direction.md`).** Rule statements describe only target
world semantics; repository classification records realization only, never delivery priority.

**Status.** Batch 12 (Magic/Supernatural), drafted per a corrected instruction file
(`tmp/world-rule-batch-12-corrected-ext-ai.md`), then revised the same day per a targeted
semantic-cleanup follow-up (`tmp/world-rule-batch-12-corrected-followup-ext-ai.md`) —
softening "independent facts" language and clarifying that authorization may be entirely
irrelevant to unregulated/innate/wild magic.

---

## Domain Rules

## MCAP-01 — Magical knowledge, magical capability, resource/cost availability, target reachability, and institutional authorization are semantically distinct facts where a given mechanism actually uses them; none is implied by any other, and a mechanism may leave one or more of them entirely inapplicable

> Knowing that a spell or ritual exists, or conceptually understanding a magical rule, is
> never the same fact as being capable of performing it — a scholar may understand magic
> without capability. Conversely, an entity may possess an innate supernatural capability
> without any conceptual understanding of it — a creature may react through a declared
> supernatural mechanism without knowing it conceptually. Capability itself is further
> distinct from having the resource a mechanism requires, from the target actually being
> reachable, and from being institutionally authorized to use it — capable ≠ has resource,
> capable ≠ target is reachable, capable ≠ authorized, capable ≠ guaranteed success. None of
> these facts (knowledge, capability, resource, reach, authorization) implies any other where
> a mechanism uses them — but not every mechanism uses all five. Authorization in particular
> may be entirely irrelevant to a wild magical creature, a natural supernatural phenomenon, or
> an unregulated innate ability; this Rule never implies that every magical action requires an
> authorization fact to exist at all, only that where one does apply, it remains its own,
> non-substitutable fact.

**Disposition: ACCEPT — REQUIRED for the distinctness-where-applicable requirement; which
facts a given mechanism actually uses is PERMITTED, mechanism-declared content.** Passes the
admission test: Batch 06 already establishes knowledge as its own fact distinct from belief
for *world facts*; Batch 07's own capability family already establishes capability ≠
execution ≠ effect generally. Neither states the specific pairing this Rule requires —
"conceptual understanding of a mechanism" as its own fact distinct from "practical capability
to perform it," a skill-knowledge/capability split this Catalog has not previously drawn,
since ordinary Batch 06 knowledge concerns knowing that some world fact is true, not knowing
how to perform an action. This pairing, plus tying it together with resource/reach/
authorization into one distinctness statement specific to magic, is this Rule's own
genuinely new content. **Revised 2026-09-22 per a targeted semantic-cleanup follow-up:**
"five independent facts" overstated universality — the distinctness holds only among the
facts a given mechanism actually engages, and authorization specifically is never assumed
applicable by default.

**Repository evidence: MISSING.** No supernatural capability, knowledge-of-a-spell, or
magic-specific resource field exists anywhere in this repository — confirmed via direct
search. The general capability-vs-execution machinery this Rule partially reuses (Batch 02's
AUTH-01, Batch 07's own capability family) is otherwise well-established for non-supernatural
cases.

**Scenarios:** [MAG-S05](../scenarios/magic-supernatural-batch-12.md#mag-s05) (knows spell,
cannot cast), [MAG-S06](../scenarios/magic-supernatural-batch-12.md#mag-s06) (innate magic
without knowledge), [MAG-S07](../scenarios/magic-supernatural-batch-12.md#mag-s07) (illegal
magic still works — capability ≠ authority), [MAG-S08](../scenarios/magic-supernatural-batch-12.md#mag-s08)
(spell fails after cost).

---

## MCAP-02 — Supernatural reach that bypasses ordinary spatial/topological reach must do so through declared supernatural reach semantics; "magic ignores Reach" is never a valid default, and a portal or teleportation is one instance of a declared reach semantic, never forced through ordinary pathfinding

> Where an ordinary spatial path is unavailable, a declared supernatural rule may establish a
> valid alternative reach semantic — touch, line of sight, spatial radius, a named target, a
> sympathetic link, a portal connection, a remote ritual, or a cross-plane relation are all
> legitimate declared forms. What is never legitimate is treating "this is magic" as
> sufficient reason to skip Reach's own requirement that a real, declared relation connect
> actor and target. A portal establishing a temporary topology edge, and a teleport
> establishing a direct supernatural transition, are two different declared shapes — neither
> is forced through ordinary pathfinding, but each still tracks its own source, target,
> eligibility, effect, and history where that matters, and a portal's own connection is never
> assumed bidirectional merely because it exists in one direction. A persistent relation
> record (source, target, eligibility) is one possible way to implement this — it is one
> implementation possibility, not the Rule itself; the Rule requires only that the reach
> semantic be declared, not any particular data shape for declaring it.

**Disposition: ACCEPT — REQUIRED for the declared-semantics requirement; the specific reach
shape (touch, portal, sympathetic link, etc.) and its implementation representation are
PERMITTED, domain-declared content.** Passes the admission test: this directly resolves Batch
04's own non-physical-movement boundary, per the batch instruction's own explicit framing —
Reach (Batch 02/04) already requires a real relation connecting actor and target generally,
but does not itself state that supernatural mechanisms may establish *new* reach relations
bypassing ordinary topology, nor that doing so requires its own explicit declaration rather
than an implicit "magic bypasses reach" default. That refinement is this Rule's own genuinely
new content. **Revised 2026-09-22 per a targeted semantic-cleanup follow-up:** reworded away
from "declared supernatural relation" (which risked reading as a mandatory data
representation) to "declared supernatural reach semantics" — a persistent relation record
remains one legitimate implementation shape, never the Rule's own requirement.

**Repository evidence: MISSING.** No portal, teleport, or supernatural-reach mechanism of any
kind exists anywhere in this repository — confirmed via direct search (no "portal"/"teleport"
hits in `src/`). Batch 02/04's own ordinary Reach machinery is otherwise real and
well-established for non-supernatural cases, with nothing currently bypassing it.

**Scenarios:** [MAG-S12](../scenarios/magic-supernatural-batch-12.md#mag-s12) (teleport
across blocked space), [MAG-S13](../scenarios/magic-supernatural-batch-12.md#mag-s13) (portal
is one-way).

---

## Inherited / Applied Foundational Rules

### Magical capability is distinct from the effect actually occurring; the full chain (capability → attempt → resolution → effect → consequence) must never collapse into a label or numeric score, and a valid attempt may still fail, be resisted, redirected, or produce only a partial effect

> Having a supernatural capability, that capability being currently available, attempting to
> use it, the attempt succeeding or failing, and a supernatural effect actually resulting are
> distinct facts. A supernatural outcome must trace to a real, declared causal chain — never
> occurring merely because an entity holds a magic-related label or numeric score (a bare
> `magic_power → effect` shortcut is exactly the pattern this reuse forbids). A successful
> attempt does not guarantee the intended final consequence — a spell may execute but be
> resisted, redirected, partial, or fail downstream, if the declared mechanism permits it.

**Disposition: INHERITED — direct reuse of Batch 06's AGENCY-01 (decision stages causally
distinct), Batch 07's own capability-vs-execution family, `supernatural-ontology.md`'s SUP-03
(magic is not a causality exception), and Batch 10's own authority-can-fail pattern, applied
to supernatural capability specifically. No new refinement beyond what these already state
combined was found necessary.**

**Repository evidence: MISSING, for any supernatural capability/execution mechanism to check
this against.**

**Scenarios:** [MAG-S08](../scenarios/magic-supernatural-batch-12.md#mag-s08).

### Magical resources, costs, and capacity are distinct facts, reused directly from Batch 03; magic is never assumed to require mana, nor is any specific consumable cost assumed universal across supernatural mechanisms

> Whatever resource (mana, stamina, blood, time, material reagent, attention, life force,
> environmental condition, social/institutional permission, sacrifice) a specific supernatural
> mechanism requires is that mechanism's own declared choice — resource, cost, capacity, and
> capability remain four distinct facts, exactly as Batch 03 already establishes generally,
> and no supernatural mechanism is assumed to use any particular one, or any consumable cost
> at all, by default.

**Disposition: INHERITED — direct reuse of Batch 03's own resource/cost/capacity/capability
distinctness family, applied to supernatural mechanisms specifically. No new claim.**

**Repository evidence: MISSING.** No magic-specific resource, mana, or cost field exists
anywhere in this repository.

**Scenarios:** [MAG-S08](../scenarios/magic-supernatural-batch-12.md#mag-s08).

### Magical capability never automatically grants, or requires, institutional authority; capability and authority remain intact as separate facts exactly as Batch 02/10 already establish

> Being capable of casting a spell is never the same fact as being permitted to cast it — an
> institution may prohibit a spell a mage remains fully capable of performing; conversely, an
> institution may authorize a ritual no member is actually capable of performing. Whether an
> institution's own authorization is a prerequisite for a specific supernatural mechanism to
> function at all is that mechanism's own declared choice, never assumed by default.

**Disposition: INHERITED — direct reuse of Batch 02's AUTH-01 (authority ≠ capability) and
Batch 10's INST-02/03 (delegated authority ≠ capability; authority/capability/power/
legitimacy correlated, never substitutable), applied to magical capability specifically. No
new claim.**

**Repository evidence: MISSING.**

**Scenarios:** [MAG-S07](../scenarios/magic-supernatural-batch-12.md#mag-s07) (illegal magic
still works — magic and institutions; corrects a duplicate citation found during the
2026-09-22 follow-up review).

---

## Scope / Deferred Boundaries

### Concrete magical-resource/cost catalog

> This family states that resource/cost/capacity/capability remain distinct facts (Inherited
> above) but does not design a concrete catalog of specific resources, costs, or capacity
> mechanics for any supernatural system — implementation-level, domain-specific content.

**Disposition: SCOPE BOUNDARY.**

---

## Repository Findings (significant, cross-referenced)

**These are repository/implementation facts, not World Rule decisions, and imply no delivery
priority.**

- **Confirmed MISSING — no magical capability, knowledge-of-spell, resource, or reach field
  exists anywhere in this repository.** See MCAP-01/MCAP-02 above.
- **Confirmed MISSING — no portal or teleportation mechanism exists anywhere**, confirmed via
  direct search. See MCAP-02 above.

## Cross-domain links recorded here

- MCAP-01 → Perception/Knowledge (Batch 06), Capability/Progression (Batch 07), Authority
  (AUTH-01, Batch 02)
- MCAP-02 → Reach (Batch 02/04's own family — the deferred non-physical-movement boundary this
  Rule directly resolves)
- Inherited capability/effect entry → Agency/Decision (AGENCY-01, Batch 06), Causality
  (CAUSE-01, Foundational), Organizations (Batch 10's authority-can-fail entry)
- Inherited resource/cost entry → Batch 03's own resource/cost/capacity family
- Inherited authority entry → Authority (AUTH-01, Batch 02), Roles/Institutions (INST-02/03,
  Batch 10)

## Open questions carried forward

1. **What constitutes supernatural reach** for a given mechanism — is there a semantic
   pattern beyond "domain-declared," or is that genuinely the correct target shape for every
   case? Not decided here.
2. Whether a universal `MagicPower` stat is ever genuinely required by target semantics, or
   whether every supernatural capability should remain mechanism-specific, is not decided
   here — no repository evidence motivates deciding it either way.
