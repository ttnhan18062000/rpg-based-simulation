---
status: authoritative
layer: architecture
authority: P1
audience: agent
tags: [architecture, world, content]
last_verified: "2026-09-23"
---

# World Rule Family: Politics / Authority

**Purpose/scope.** Political succession as the resolution of who validly holds an office, and
the absence of a required equilibrium in political/institutional stability. Politics is
treated broadly as the processes by which actors acquire, preserve, exercise, contest, or
redirect collective authority and resources — not designed as any single universal
resolution mechanism. Does not decide organization/role semantics (see `organizations.md`,
`roles-institutions.md`) or law/enforcement (see `law-enforcement.md`).

**Standing direction (2026-09-22, `tmp/world-rule-direction.md`).** Applied from this batch
onward: Rule statements below describe only target world semantics, independent of current
repository realization.

**Status.** Batch 10 (Organizations/Institutions/Politics/Law), first draft, per
`tmp/world-rule-batch-10-ext-ai.md`.

---

## Domain Rules

## POL-01 — Political succession — who validly becomes an office-holder — is distinct from kinship eligibility and from property inheritance; a descendant is not automatically a legitimate successor absent a declared political rule connecting them

> Whether a candidate validly succeeds to a political office is a fact a domain's own
> institutional succession rule determines — never automatically granted by kinship (being a
> close relative of the prior holder) or by property inheritance (having inherited the prior
> holder's estate). Family/Lineage (Batch 09) may supply descent, kinship, and candidate
> eligibility as real inputs; Politics/Institutions decides who is a valid successor under
> which institutional rule. Inheriting property is never the same fact as inheriting office.

**Disposition: ACCEPT — REQUIRED for the distinctness; which inputs any specific succession
rule actually weighs is PERMITTED, domain-specific content.** Passes the admission test: this
directly resolves the boundary Batch 09's own `lineage-descent.md` explicitly deferred
("political succession... remains Politics/Institutions' own future domain") and the open
question Batch 02's AUTH-06 carried forward about whether *political* authority earns its own
succession-eligibility refinement. The genuinely new content is the three-way split itself
(kinship eligibility ≠ property inheritance ≠ political-successor validity) — no earlier Rule
states all three are independent.

**Repository evidence: MISSING, for the political-office half; SUPPORTED, for the
kinship-does-not-determine-succession half, via a structurally close analogue.** No office/
ruler/king/mayor/council concept exists anywhere in this repository for a "political
succession" rule to apply to (`roles-institutions.md`'s own INST-01 finding). The closest real
analogue, `ClanLifecycleService.process_succession()`, already demonstrates the *shape* this
Rule requires at the leadership-role scale: successors are chosen by social-bond/sociability
score, never by reading `parent_a_entity_id`/`parent_b_entity_id` (Batch 09's own
`lineage-descent.md` evidence) and never by any property/asset fact. Whether this same,
already-real mechanism should be understood as a genuine instance of "political succession," or
whether political succession is a distinct, currently entirely-unrealized concept one level
above ordinary group leadership, is carried forward as an owner-attention question below.

**Scenarios:** [IP-S06](../scenarios/institutions-politics-batch-10.md#ip-s06),
[IP-S08](../scenarios/institutions-politics-batch-10.md#ip-s08) (kinship does not automatically
grant office).

---

## Inherited / Applied Foundational Rules

### Political stability, instability, collapse, consolidation, and fragmentation require causal mechanisms; stability is not assumed as the default outcome

> A political or institutional system does not tend toward equilibrium by default. Authority
> collapse, institutional decay, civil conflict, corruption, fragmentation, failed enforcement,
> power concentration, and rebellion are all legitimate outcomes wherever real causal
> conditions produce them — none is precluded by an assumed background stability. Where a
> counterforce (a stabilizing mechanism) exists, it must itself be a real, declared mechanism
> that can also fail, never an assumed default that instability must overcome.

**Disposition: INHERITED (reclassified from a Domain Rule, originally drafted as POL-02,
during the 2026-09-22 follow-up review).** The follow-up correctly re-tested this against the
admission discipline: on stricter re-examination, it adds no Politics-specific content beyond
applying two already-locked patterns to this batch's own subject matter — Batch 09's revised
SOC-03 (persistence/decay/rupture/expiration occur only per declared semantics, never an
unstated default) and Batch 07's PROG-05 (limiting semantics must be declared, not assumed).
The batch instruction's own "Open Instability" guidance (item 29) is itself an instance of the
already-locked "no default X" principle, not a new one Politics itself contributes. Per the
follow-up's own explicit instruction not to preserve a Rule merely to keep two Politics Rules,
this is moved rather than kept as a Domain Rule.

**Repository evidence: PARTIAL.** `FactionState.tension_level`/`pairwise_tension`
(`src/core/state.py`) and `DiplomaticStateMachine` (`src/domains/faction/
diplomatic_state_machine.py`) are real, causally-driven state that can move a faction pair from
peaceful toward hostile — a real instability channel, not an assumed-stable default. No
countervailing stabilizing mechanism (something that actively repairs tension/decay) was found
in the same investigation, which is itself consistent with this Rule (a stabilizing mechanism is
permitted, not required) rather than a violation.

**Scenarios:** none directly traced; reuses the diplomatic-tension evidence above as a
standing instance of the permitted-instability case.

### Authority never guarantees compliance; practical power can produce behavior without formal authority

> A valid order issued under real authority does not guarantee a subordinate executes it — the
> subordinate's own decision-making layer may still refuse. Conversely, an actor with
> sufficient practical power (coercive capacity, resources) but no formal authority may still
> produce compliance through other means.

**Disposition: INHERITED — direct reuse of Batch 06's AGENCY-01/AGENCY-02 (motivation
influences a decision, never determines it) combined with this batch's own INST-03
(authority/capability/power/legitimacy are independent). No new claim: an authority-backed
order is simply one motivational input among others to the subordinate's own decision process,
which AGENCY-02 already establishes never determines the outcome by itself.**

**Repository evidence: PARTIAL.** No scenario in this repository was found where an entity's
own decision process explicitly reads "was this order authorized" as an input and then refuses
despite that authority — the general AGENCY-01/02 machinery (decision stages causally distinct,
motivation influences never determines) is real and reused directly, but a
political-authority-specific instance of "the order was valid and was still refused" was not
independently confirmed to exist in current code.

**Scenarios:** [IP-S03](../scenarios/institutions-politics-batch-10.md#ip-s03),
[IP-S05](../scenarios/institutions-politics-batch-10.md#ip-s05).

### Power-conversion edges (wealth → coercive capacity, reputation → leverage, office → resource access) are specific and declared, never a universal political-power score

> Where one kind of advantage (wealth, reputation, office, information, military capability)
> converts into political leverage or coercive capacity, that conversion is a specific,
> declared edge — never computed from one universal "Political Power" score.

**Disposition: INHERITED — direct reuse of Batch 07's PROG-07 (power-conversion edges are
specific, never automatic) and Batch 08's EXCH-01 (value/price/cost/wealth are distinct;
non-universal price influences), applied to political conversion specifically. No new claim
beyond instantiating an already-settled pattern for this batch's own subject matter.**

**Repository evidence: MISSING, for every named political conversion edge checked.** Batch 08's
own EXCH-01 evidence already confirmed wealth→political-influence as MISSING. This batch's own
investigation found no reputation→political-leverage, no office→resource-access mechanism
beyond ordinary organizational resource access (`organizations.md`'s own Inherited entry), and
no information→bargaining-advantage mechanism specific to political contexts. `FactionState.
military_strength` is the one real, already-existing coercive-capacity proxy, but nothing
converts it *from* another advantage (e.g., wealth) through a declared edge — it is seeded and
adjusted directly, not derived.

**Scenarios:** none newly traced; reuses Batch 07/08's own evidence directly.

---

## Scope / Deferred Boundaries

### Concrete political-resolution-mechanism catalog

> This family states politics broadly (negotiation, coalition, appointment, election,
> succession, coup, rebellion, patronage, coercion, institutional maneuver) as the general
> category of processes by which collective authority/resources are contested, but does not
> design any one of these as a concrete, buildable mechanism, nor privilege any single one —
> deferred, per this family's own scope, and per the batch instruction's own explicit
> "do not create a universal political-resolution mechanism."

**Disposition: SCOPE BOUNDARY.**

### Territorial sovereignty depth

> `FactionState.territory` and `region.owner_faction_id` supply a real, existing hook for
> territorial jurisdiction, but this family does not design full territorial sovereignty
> semantics — deferred to Batch 11 (Places/Settlements/Territory/Culture/Belief), per the batch
> instruction's own explicit deferral.

**Disposition: SCOPE BOUNDARY.**

---

## Repository Findings (significant, cross-referenced)

**These are repository/implementation facts, not World Rule decisions, and imply no delivery
priority.**

- **Confirmed MISSING — no political office concept exists for POL-01's own succession rule to
  apply to.** See POL-01 above; cross-referenced from `roles-institutions.md`'s INST-01.
- **Confirmed MISSING — every named political power-conversion edge checked (reputation →
  leverage, office → resource access beyond ordinary organizational access, information →
  bargaining advantage) is unrealized.** See the power-conversion Inherited entry above.
- **PARTIAL — a real, live instability channel exists** (`FactionState.tension_level`/
  `pairwise_tension`, `DiplomaticStateMachine`) **with no confirmed stabilizing counterforce** —
  consistent with, not a violation of, the Open-Instability Inherited entry's own permission.
- **A real territorial-jurisdiction-style pattern already exists elsewhere in the engine, even
  though no law/rule subsystem yet consumes it.** `region.suppression_active` combined with
  `entity.identity.faction != region.owner_faction_id` applies real combat penalties to
  entities in enemy-controlled, suppressed territory (`src/engine/town_resolution.py`) — a
  live example of location-plus-affiliation-scoped effect, the same general shape
  `law-enforcement.md`'s own LAW-03 (jurisdiction has a declared scope) requires, just not yet
  applied to law specifically.

## Implementation Candidates — Non-Binding

**This section preserves implementation-relevant discoveries only. Nothing here is approved,
prioritized, or required for implementation during the World Rule Catalog phase.**

- **Target semantic:** political succession requires its own declared eligibility/validity
  rule, distinct from kinship and property (POL-01).
  **Current realization:** only `ClanLifecycleService.process_succession()` exists (a
  group-leadership-scale mechanism); no office/ruler/council concept exists at any larger
  political scale.
  **Gap/mismatch:** whether ordinary group leadership succession already *is* an instance of
  "political succession," or a genuinely larger political-office concept remains entirely
  unbuilt, is unresolved.
  **Possible implementation direction:** an `OfficeState`-shaped record with its own
  succession-rule declaration, independent of `ClanState.leader_entity_id`, if investigation
  later confirms group-leadership succession is not itself sufficient.
  **Implementation decision:** DEFERRED — no commitment in Rule Catalog phase.

## Cross-domain links recorded here

- POL-01 → Lineage/Descent (`social-lineage/lineage-descent.md`'s LIN-01, Batch 09 — the
  deferred boundary this Rule directly resolves), Authority (AUTH-06, Batch 02 — its own
  carried-forward open question)
- Inherited open-instability entry → Social Relations (SOC-03, Batch 09 — the same
  declared-semantics pattern), Capability/Progression (PROG-05, Batch 07 — the same
  declared-limiting-semantics pattern)
- Inherited authority-can-fail entry → Agency/Decision (AGENCY-01/02, Batch 06)
- Inherited power-conversion entry → Capability/Progression (PROG-07, Batch 07), Economy/
  Exchange (EXCH-01, Batch 08)
- Territorial jurisdiction finding → Places/Settlements/Territory (Batch 11, deferred)

## Open questions carried forward

1. Whether `ClanLifecycleService.process_succession()`'s own leadership-succession mechanism
   should be understood as a genuine instance of "political succession," or whether political
   succession names a distinct, currently entirely-unrealized concept one scale above ordinary
   group leadership, is an open design-semantic question, not decided here.
2. Whether "Power" (INST-03) ever needs a political-scale representation distinct from
   `FactionState.military_strength` is carried forward from `roles-institutions.md`.
