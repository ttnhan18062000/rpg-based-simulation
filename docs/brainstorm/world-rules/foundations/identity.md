---
status: active
layer: architecture
authority: P1
audience: agent
tags: [architecture, world, content]
---

# World Rule Family: Identity

**Purpose/scope.** What it means for a first-class simulated subject to remain "the same thing"
across change, transformation, aggregation, and eventual termination. Applies uniformly across
Scale (entity, group, region, faction, world) and across Domain — Identity is not itself a Domain,
it is a foundational law family every Domain's first-class subjects answer to.

**Status.** Foundational Batch 01, first draft. Candidates below originated as external-reviewer
hypotheses (`tmp/world-catalog-batch-1-ext-ai.md`); each carries this session's disposition and
repository evidence, not the original wording uncritically kept.

---

## ID-01 — Persistent identity

> A first-class simulated subject retains its identity across ordinary changes in state: location,
> health, wealth, relationships, role, equipment, reputation, capability.

**Disposition: ACCEPT.** Matches `core_rpg_design_direction.md`'s own Fundamental World Contract
("Identity: first-class entities keep persistent identity; transformation does not erase
historical continuity") almost verbatim — this rule operationalises that contract row rather than
introducing a new idea.

**Repository evidence: SUPPORTED.** `EntityState.id` is stable across every listed change —
confirmed directly: `EvolutionSystem.evaluate()` (`src/engine/evolution.py`) changes `kind`,
attributes, equipment and reward on an entity while writing back to the *same* `entity_id`, never
constructing a new one. `FactionState`/`ClanState` are keyed by a stable id independent of
territory, reputation, or membership changes.

**State ownership:** identity itself is not durable *state* in the OWN-01 sense — it's the
precondition for durable state existing at all (the key everything else attaches to). See
`state-ownership.md` for the distinction between identity and the state a subject owns.

**Scenarios:** [FND-S01](../scenarios/foundational-batch-01.md#fnd-s01), [FND-S11](../scenarios/foundational-batch-01.md#fnd-s11).

---

## ID-02 — Identity is distinct from classification

> Identity is not equivalent to kind, type, role, faction, occupation, ownership, location, or
> current form. A subject may change classification while retaining historical continuity.

**Disposition: ACCEPT.**

**Repository evidence: SUPPORTED.** `EvolutionSystem._get_evolved_kind()` remaps `kind` strings
(`WOLF→DIRE_WOLF`, `HERO→LEGEND_HERO`) on the same `entity_id` — the clearest possible repository
proof that kind and identity are already architecturally separate fields, not the same concept
wearing two names. Confirmed independently earlier this session that nothing currently *reads*
the evolved kind, which is a Reach/Cross-cutting-Layer finding (see `simulation-rule-world-law-
design-preparation.md` §4), not an Identity-family problem — the identity boundary itself holds.

**Scenarios:** [FND-S01](../scenarios/foundational-batch-01.md#fnd-s01).

---

## ID-03 — Transformation preserves continuity by default

> A qualitative transformation does not erase identity unless a specific world rule explicitly
> defines the transformation as identity-ending or identity-creating.

**Disposition: ACCEPT, with the boundary probe left open by design, not resolved prematurely.**
This is the operative default `D2 — Bounded Ontology Change` needs: without a stated default,
every future transformation rule would have to re-derive whether it ends identity from scratch.

**The default and its exception, stated explicitly:**
- Default (continuity): a subject changes *what it is* without ceasing to be *itself* — kind
  transitions (`wolf → adapted predator`), a healed wound becoming a scar, a weapon becoming an
  heirloom. No new id, no lost history.
- Exception (identity-ending or identity-creating): must be an *explicit* rule in the relevant
  domain, never assumed. `human → vampire` is deliberately left as an open boundary case here —
  the Magic/supernatural domain (not yet designed) owns the answer, and forcing one now would
  violate `simulation-rule-world-law-design-preparation.md` §2's own admissibility test question 8
  ("would the world still conceptually work if its implementation changed completely?" — we don't
  yet know enough about what "vampire" means in this world to answer that). `camp → settlement →
  ruin` is a Places-domain case (also not yet designed) and is explicitly not resolved here — see
  `state-ownership.md` OWN-06 for why a *place* changing kind is not automatically the same
  question as a *person* changing kind.

**Repository evidence: SUPPORTED for the default; MISSING for any exception mechanism.**
`EvolutionSystem` never constructs a new entity — every kind change it performs is continuity by
construction, matching the default exactly. No current mechanism implements an identity-ending
transformation for any domain.

**Scenarios:** [FND-S01](../scenarios/foundational-batch-01.md#fnd-s01), [FND-S02](../scenarios/foundational-batch-01.md#fnd-s02) (boundary probe, not resolved), [FND-S05](../scenarios/foundational-batch-01.md#fnd-s05), [FND-S06](../scenarios/foundational-batch-01.md#fnd-s06).

**Open questions:** what makes a transformation identity-ending, in general (not per-domain)? Left
deliberately unanswered — see "Rules added by the local agent" below for the one general-purpose
addition this session judged safe to make now (ID-09).

---

## ID-04 — Creation establishes identity explicitly

> A newly created first-class subject begins a distinct identity and may carry provenance from its
> causes or predecessors without becoming identical to them.

**Disposition: ACCEPT.**

**Repository evidence: SUPPORTED for entities via reproduction; MISSING for organizations and
settlements.** `V2EntityBuilder.birth_record()` constructs a genuinely new `entity_id` and records
`parent_a_entity_id`/`parent_b_entity_id` as provenance, not identity — the child is never
"the same as" either parent. Checked directly this session: no `found`/`create_clan`/`establish`
method exists anywhere in the clan-lifecycle code — a clan can only be *joined*, never *founded by*
a following, and no equivalent exists for settlements (`PlaceState` has no runtime construction
path at all). This confirms, at the Identity-family level, exactly the L7/L17 gap the lived-history
brainstorm work already found from a different angle (missing runtime founding) — the same
repository fact, now stated as a foundational-law gap rather than a scenario-tracing one.

**Scenarios:** [FND-S03](../scenarios/foundational-batch-01.md#fnd-s03), [FND-S06](../scenarios/foundational-batch-01.md#fnd-s06).

---

## ID-05 — Destruction/lifecycle termination does not erase history

> When an entity ceases to exist as an active subject, historical references to that entity remain
> semantically meaningful. Death/destruction may terminate active state without deleting historical
> identity.

**Disposition: ACCEPT.**

**The three-way distinction, checked directly against real code:**
1. **Living subject** — `entity.lifecycle.active = True`, participates in the tick.
2. **Dead subject as historical reference** — `active = False`, `is_permadeath_set = True`, but
   the same `entity_id` remains a valid target for later semantics: `LifecycleSystem._seed_dying_
   wish()` writes a named intention referencing the deceased onto the heir; `_transfer_inherited_
   feud()` transfers hostility that names the same antagonist; `Chronicle`/`LegendFact` reference a
   subject's id whether or not it's still active.
3. **Corpse/remains as a separate material object** — `CorpseState` (`src/core/state.py`) is
   confirmed a genuinely distinct class from `EntityState`, with its own id and decay lifecycle —
   not a flag on the entity, a separate first-class object in the Objects domain's future scope.

**Repository evidence: SUPPORTED**, and this is one of the strongest-evidenced rules in the whole
batch — this session's earlier work already identified death/lineage as the richest live
substrate in the repository, and this rule is the Identity-family statement of exactly why.

**Scenarios:** [FND-S03](../scenarios/foundational-batch-01.md#fnd-s03), [FND-S08](../scenarios/foundational-batch-01.md#fnd-s08), [FND-S12](../scenarios/foundational-batch-01.md#fnd-s12).

---

## ID-06 — Split/merge/succession require explicit identity semantics

> Faction splits, organization merges, settlement absorption, dynastic succession, creature
> reproduction, and place reconstruction must not silently assume identity behaviour. The Rule
> Catalog should eventually state whether each produces continuity, new identity, multiple
> descendants, or successor identity with provenance.

**Disposition: ACCEPT, explicitly left as an unresolved dependency — this rule's entire job is to
say so, not to resolve it.**

**Repository evidence, per case:**
- **Succession (single heir):** SUPPORTED. `LifecycleSystem._select_default_heir()` picks exactly
  one successor by familiarity/sentiment score; the office/role continues under a new id (Politics
  and Family/lineage own the details, not Identity).
- **Reproduction:** SUPPORTED — already covered by ID-04 as an identity-*creating* case, not a
  merge.
- **Faction/clan split, organization merge, settlement absorption, place reconstruction:**
  MISSING. No mechanism found for any of these. Confirmed by direct search this session (no
  split/merge method anywhere in the clan or faction lifecycle code).

**Scenarios:** [FND-S06](../scenarios/foundational-batch-01.md#fnd-s06) (organization split — deliberately exposes this gap without resolving it), [FND-S05](../scenarios/foundational-batch-01.md#fnd-s05) (settlement continuity — same treatment).

**Open questions:** deferred to Organizations/institutions and Places/settlements/territory
(future batches). This rule's own acceptance criterion is that those future batches cannot skip
the question, not that this batch answers it.

---

## ID-07 — Aggregate membership does not erase individual identity

> A first-class individual may participate in an aggregate without becoming semantically identical
> to the aggregate. Aggregate state and individual history must remain conceptually
> distinguishable.

**Disposition: ACCEPT.** Matches `core_rpg_design_direction.md`'s own aggregate/first-class-entity
split exactly (§7: "an aggregate may be promoted to finer detail when causal value requires it" —
which presupposes the two were never the same thing).

**Repository evidence: SUPPORTED.** Demographic cohorts (`PopulationCohort`) are a genuinely
separate representation from named `EntityState` records — confirmed this session multiple times,
including the explicit design intent that a regional population count is "a weather system," never
a stand-in for a named individual's trajectory.

**Scenarios:** [FND-S11](../scenarios/foundational-batch-01.md#fnd-s11).

---

## Rules added by the local agent

Two additions, both judged necessary by scenario tracing and the ownership-clarification work
already established this session — not added to pad the catalog.

### ID-08 — Identity applies uniformly across scale, not only to entities

> The Identity family (ID-01 through ID-07) applies to any first-class simulated subject at any
> scale — a person, a faction, a clan, a place, an artifact, a region — not only to individually
> simulated entities in the narrow sense.

**Why necessary:** the candidate set above mostly used "subject"/"first-class simulated subject"
already, which is correct, but ID-01's own worked list ("location, health, wealth, relationships,
role, equipment, reputation, capability") reads entity-specific enough that a future domain author
could plausibly miss that a `FactionState` or `PlaceState` needs the same treatment. This directly
operationalises the already-adopted clarification that "first-class simulated entity/subject" is
ontological, not an implementation base class (`core_rpg_design_direction.md` §7) — without this
rule, that clarification lives only in the taxonomy vocabulary, not in the Identity law itself
where a domain author would actually look for it.

**Repository evidence: SUPPORTED.** `EntityState`, `FactionState`, `ClanState`, `RegionState`, and
`PlaceState` already don't share a base class, and each already has its own stable id independent
of the others' shape — the repository already behaves this way; this rule states why that's
correct rather than incidental.

### ID-09 — A name or epithet is not identity

> A subject's name, title, or epithet may change without changing its identity, and two subjects
> may share a name without sharing an identity.

**Why necessary:** ID-03 explicitly left "what makes a transformation identity-ending" partly
open, and scenario tracing (`FND-S01`, the wolf earning "the Ash Fang") surfaced a real, narrow gap
the candidate set never mentioned: *naming* a subject is a distinct act from *transforming* it, and
without this rule a future domain could accidentally couple them — e.g. assuming a renamed or
epitheted subject is a new one, which would silently break every lived-history mechanism this
session's earlier work depends on (fame, legend, epithets).

**Repository evidence: SUPPORTED by absence of counter-evidence** — no current mechanism conflates
a name with an id (Chronicle naming, `ChronicleNamer`, targets events and factions by id, never by
name string), but no current mechanism gives an arbitrary entity a persistent player-facing name
either — this rule protects a future capability more than it describes a present one, which is an
acceptable reason to state it now per the admission test (question 5: "does it have at least one
meaningful producer/consumer or causal consequence?" — yes, the notability/epithet work already
scoped in the lived-history brainstorm doc).

**Scenarios:** [FND-S01](../scenarios/foundational-batch-01.md#fnd-s01).

---

## Cross-domain links recorded here (not yet promoted to `cross-domain/`)

- ID-04/ID-05 → Family/lineage (birth, succession, inherited provenance)
- ID-05 → Objects & material culture (corpse as a separate object)
- ID-05 → History/significance (chronicle references a subject regardless of active state)
- ID-06 → Organizations & institutions, Places & settlements (deferred split/merge/founding questions)

None of these is yet substantial enough on its own to warrant a shared `cross-domain/` file per
the structure guidance — each is a single link recorded at its point of origin. Revisit once a
second family (State Ownership, Causality, or a later batch) needs the *same* link independently.

## Open questions carried forward

1. What, in general (not per-domain), makes a transformation identity-ending? (ID-03)
2. How do split/merge/founding resolve for organizations and settlements? (ID-06, deferred to
   Organizations and Places batches)
3. Is a corpse's own identity (as an Objects-domain subject) related to the deceased entity's
   identity, or fully independent? Not resolved in this batch — flagged for the Objects &
   material culture batch.
