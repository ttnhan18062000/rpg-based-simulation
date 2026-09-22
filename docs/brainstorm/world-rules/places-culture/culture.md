---
status: active
layer: architecture
authority: P1
audience: agent
tags: [architecture, world, content]
---

# World Rule Family: Culture

**Purpose/scope.** What culture is in this simulation (where modeled), how a collective
cultural pattern relates to any single individual's own belief or practice, and how cultural
participation, transmission, and change require real causal paths. Does not decide collective
belief/religion specifically (see `collective-belief.md`) or draw the Magic/supernatural
boundary (see `collective-belief.md`'s BEL-02, deferred fully to Batch 12).

**Standing direction (`tmp/world-rule-direction.md`).** Rule statements describe only target
world semantics; repository classification records realization only, never delivery priority.

**Status.** Batch 11B (Culture/Collective Belief — split from Batch 11 per that batch's own
explicit size/split permission; Batch 11A, Places/Settlements/Territory, is drafted
separately), first draft, per `tmp/world-rule-batch-11-ext-ai.md`.

---

## Domain Rules

## CULT-01 — Culture, where modeled, is a real collective pattern of language, custom, norm, ritual, symbol, story, aesthetic practice, or shared historical interpretation, distinct from individual belief, law, religion, faction membership, ethnicity, and settlement identity, though it may overlap with any of these without being identical to them

> Culture is never required to be a generic scalar (a `CultureScore`) — it is whichever of
> language, customs, norms, rituals, symbols, stories, aesthetic practices, food, social
> expectations, or shared historical interpretation a domain chooses to model, with no fixed
> catalog required in advance. Culture is distinct from an individual's own belief (a person
> may belong to a culture and privately reject parts of it), from law (a legal rule and a
> cultural norm are different facts even where they agree), from religion (a culture may
> contain religious content without being reducible to it), from faction membership (an
> organization is not the same fact as a shared culture, though members may share one), from
> ethnicity, and from settlement identity — a culture may overlap with any of these without
> collapsing into it.

**Disposition: ACCEPT — REQUIRED for the distinctness; which specific cultural content any
domain models is PERMITTED, open-ended content.** Passes the admission test: no earlier Rule
addresses culture as its own concept — this is genuinely new content, explicitly warned by the
batch instruction against being reduced to one generic score, and against being collapsed into
five adjacent, already-established concepts (individual belief: Batch 06; law: Batch 10;
faction membership: Batch 10's ORG-02; settlement: `settlements.md`'s SETT-01).

**Repository evidence: CONFLICTING, and this family's own single most significant finding.**
`CultureState`/`CultureCarryForward` (`src/domains/culture/model.py`, E62A/E62B) is real, live,
and genuinely consumed (`CulturalBiasApplicator` biases route-scoring tags from it) — but it is
structurally a fixed four-axis derived-tendency score (`fatalism`, `hero_veneration`,
`resource_scarcity_memory`, `faction_conflict_exposure`), each a float in `[0.0, 1.0]` derived
from event history and carried per-region across campaign episodes. This is exactly the
`CultureScore`-shaped pattern the batch instruction's own §15 explicitly warns against, sharing
this repository's own name ("culture") with this Rule's own much richer target concept
(language, custom, ritual, symbol, story) while realizing none of that content — a genuine
naming/scope mismatch between what this repository calls "culture" and what this Rule's own
target semantics mean by it, not merely an incomplete implementation of the same concept.

**Scenarios:** [CB-S01](../scenarios/culture-belief-batch-11b.md#cb-s01) (culture spans
border), [CB-S02](../scenarios/culture-belief-batch-11b.md#cb-s02) (one territory, multiple
cultures).

---

## CULT-02 — Culture may contain durable/shared practices, norms, rituals, institutions, records, symbols, or traditions that persist beyond the current distribution of individual belief or practice; culture is never reducible to the statistical average of individuals' own current states

> A settlement's or population's own cultural pattern is never computed merely as the average
> of its current residents' own private beliefs or practices. Culture *may* contain durable,
> shared practices, norms, rituals, institutions, records, symbols, traditions, or other
> socially persistent structures — but this is a permitted, non-exhaustive description of what
> culture can consist of, not a definition that culture *is* only these artifacts and nothing
> else. Whatever a specific culture's own content turns out to be, it is never reducible to a
> live average of current individual states: a settlement's custom favoring ancestor worship
> does not imply every resident personally believes in it, and does not disappear merely
> because the current population's own average belief has shifted, absent a real, declared
> change process (see CULT-04).

**Disposition: ACCEPT — REQUIRED; reworded 2026-09-22 per external follow-up review to fix an
over-literal equation.** The original wording ("culture consists of durable collective
artifacts") risked being read as a strict, exhaustive definition — that culture *is* durable
artifacts and nothing else. This revision keeps the substantive non-admission claim (culture is
never reducible to a live statistical average of current individual belief) while stating the
durable-artifact content as a permitted, non-exhaustive description rather than a definition,
consistent with CULT-01's own open-ended-content principle. Passes the admission test
unchanged: this goes beyond the already-established individual/aggregate distinctness
(Batch 05's ECOL-01/02, Batch 09's SOC-01) by forbidding the specific "average = culture"
shape the batch instruction's own §35 names as a mistake, which the pure aggregate/individual
boundary alone does not itself forbid (an aggregate *could* legitimately be defined as a live
average of something else; this Rule specifically forbids that shape for culture, without
otherwise constraining what culture's own content may be).

**Repository evidence: PARTIAL.** `CultureCarryForward`'s own per-region, per-episode
snapshot shape is durable and persists independently of any single entity's own belief state —
consistent with the "durable, not a live average" half of this Rule. Whether it is populated
from genuine collective artifacts (declared institutions/rituals/records) or is itself simply
an aggregated statistic derived from individual-level events was not fully resolved — its own
docstring describes deriving axes "from calamity events," "from deaths of HERO entities," and
similar event-aggregation language, which sits closer to a derived statistical tendency than to
a durable institutional artifact, a distinction this Rule's own admission depends on and
which future investigation should sharpen.

**Scenarios:** [CB-S03](../scenarios/culture-belief-batch-11b.md#cb-s03) (individual rejects
local culture).

---

## CULT-03 — Cultural participation, knowledge, practice, rejection, and identification are each distinct facts about an individual's own relationship to a culture; residence or birth within a cultural context never automatically makes an individual culturally identical to it — each requires its own real causal path (family, social interaction, education, institution, ritual, language exposure, migration) to change

> An individual being born in, or residing within, a settlement or region does not by itself
> make that individual culturally identical to whatever pattern that settlement or region
> holds. Participating in, knowing about, practicing, rejecting, or identifying with a culture
> are each their own distinct fact, and any of them changing for a specific individual requires
> a real, declared causal path — family upbringing, social interaction, education, institution,
> ritual participation, language exposure, or migration — never an automatic consequence of
> mere presence.

**Disposition: ACCEPT — REQUIRED.** Passes the admission test: this is CULT-02's own
individual-scale complement, stating the specific causal channels through which an individual's
own cultural relationship may change, which no earlier Rule addresses — an analogous but
distinct claim from Batch 06's general knowledge/belief machinery, since it is about cultural
*identification/participation* specifically, a richer relationship than mere knowledge of a
fact.

**Repository evidence: MISSING.** No mechanism was found that changes any individual entity's
own cultural participation/identification through any of the named causal channels —
`CultureState`'s own consumer (`CulturalBiasApplicator`) reads the *regional* culture value
directly to bias a scoring calculation, with no individual-level cultural-adoption state
mediating it at all; every entity in a region is affected identically regardless of that
entity's own history, family, or education.

**Scenarios:** [CB-S03](../scenarios/culture-belief-batch-11b.md#cb-s03),
[CB-S04](../scenarios/culture-belief-batch-11b.md#cb-s04) (migrant adopts some practices).

---

## CULT-04 — Cultural transmission and change (adoption, blending, fragmentation, drift, revival, suppression, loss) each require a real, declared causal channel; culture existing does not mean a subject knows it, encountering a culture does not mean adopting it, and convergence or decay toward any particular end-state is never assumed by default

> Culture changing — through adoption, blending of contact cultures, fragmentation, gradual
> drift, deliberate revival, suppression, or loss — always requires a real, declared causal
> channel (family, peers, teachers, institutions, records, ritual, migration, trade,
> storytelling, or conquest), never an unstated default direction. A culture existing as a real
> fact does not mean any given subject knows of it; a subject encountering a culture does not
> mean that subject adopts it. Cultures are never assumed to inevitably converge toward
> uniformity or decay toward loss — stabilizing and destabilizing forces may both exist and may
> both fail, exactly as this Catalog's own already-established "no default X" pattern requires
> for any other domain.

**Disposition: ACCEPT — REQUIRED.** Passes the admission test: this names the specific
candidate transmission channels and change modes for culture, genuinely new content beyond the
already-established general "no default X, only declared causal paths" pattern (Batch 09's
SOC-03, Batch 07's PROG-05, Batch 10's reclassified open-instability entry) — this Rule is the
culture-specific instantiation of that pattern, reusing it directly for the "no assumed
convergence/decay" half rather than restating it as new content.

**Repository evidence: MISSING, for individual-level transmission; PARTIAL, for regional-scale
drift.** `CultureCarryForward`'s own per-episode snapshots do change over time (E62A/E62B's own
"regional culture drift" framing), a real, declared, event-driven change process at the
regional scale — but no individual-to-individual or channel-specific (family/peer/ritual/
migration) transmission mechanism was found; the regional value simply is recomputed from
recent event history each episode, not propagated through any of this Rule's own named social
channels.

**Scenarios:** [CB-S05](../scenarios/culture-belief-batch-11b.md#cb-s05) (cultural contact
without adoption), [CB-S06](../scenarios/culture-belief-batch-11b.md#cb-s06) (cultural
blending).

---

## Inherited / Applied Foundational Rules

*(none newly identified for this file; CULT-02/03's own individual/aggregate boundary reuses
Batch 05's ECOL-01/02 and Batch 09's SOC-01 as backing, cited within their own Disposition
text rather than duplicated as a separate entry, since each Domain Rule above also adds
genuinely new structural content beyond a pure restatement.)*

---

## Scope / Deferred Boundaries

### Concrete cultural-content catalog

> This family states that culture is real and structurally rich (CULT-01) but does not fix a
> catalog of specific languages, customs, rituals, symbols, or stories — open-ended,
> domain-declared content, per the batch instruction's own explicit "do not require a fixed
> catalog now."

**Disposition: SCOPE BOUNDARY.**

---

## Repository Findings (significant, cross-referenced)

**These are repository/implementation facts, not World Rule decisions, and imply no delivery
priority.**

- **CONFLICTING — this repository's own "culture" system is a four-axis derived-tendency
  score, not the rich concept this family's own target semantics describe.** See CULT-01
  above. Real, live, and genuinely consumed (`CulturalBiasApplicator`), which makes this a
  more significant naming/scope mismatch than a simple MISSING finding — a reader searching
  this codebase for "culture" will find a real, working system that does not implement what
  this family means by the word.
- **Confirmed MISSING — no individual-level cultural participation/adoption mechanism
  exists.** Every entity in a region is affected identically by `CultureState`, regardless of
  that entity's own history. See CULT-03 above.
- **PARTIAL — regional culture drift is real and event-driven, but not channel-mediated.**
  See CULT-04 above.

## Implementation Candidates — Non-Binding

**This section preserves implementation-relevant discoveries only. Nothing here is approved,
prioritized, or required for implementation during the World Rule Catalog phase.**

- **Target semantic:** cultural knowledge, practice, rejection, and identification are each
  their own distinct individual-level fact, none collapsible into the others, each requiring
  its own causal path to change (CULT-03).
  **Current realization:** `CultureState` is read uniformly by every entity in a region; no
  individual-level field of any kind exists.
  **Gap/mismatch:** the individual/collective boundary this family's own CULT-02/03 requires
  is not represented at all.
  **Possible implementation direction (corrected 2026-09-22 per external follow-up review —
  the prior draft here proposed a single `cultural_affinity` scalar, which would itself
  violate CULT-03's own distinctness requirement and is withdrawn):** whatever shape is
  eventually chosen must keep knowledge, practice, rejection, and identification
  independently representable — for example separate typed fields or relations per
  individual-per-culture (a `knows: bool`, a `practices: Set[custom_id]`, a
  `rejects: Set[custom_id]`, an `identifies_as: bool`, or an equivalent structure), never one
  scalar standing in for all four. No specific schema is committed here.
  **Implementation decision:** DEFERRED — no commitment in Rule Catalog phase.

## Cross-domain links recorded here

- CULT-01 → Perception/Knowledge (Batch 06), Law/Enforcement (LAW-01, Batch 10), Belief
  (`collective-belief.md`'s BEL-02), Organizations (ORG-02, Batch 10), Settlements
  (`settlements.md`'s SETT-01)
- CULT-02, CULT-03 → Ecology/Population (ECOL-01/02, Batch 05), Social Relations (SOC-01,
  Batch 09)
- CULT-04 → Social Relations (SOC-03, Batch 09), Capability/Progression (PROG-05, Batch 07),
  Organizations (Batch 10's reclassified open-instability entry)

## Open questions carried forward

1. **What distinguishes culture from population-wide reputation** (`social-lineage/
   social-relations.md`'s own reputation-representations Inherited entry, Batch 09)**?** Both
   are aggregate, region/population-scoped facts — whether they should ever be unified at the
   data-shape level or remain conceptually and structurally separate is not decided here.
2. Whether `CultureState`'s own four fixed axes should ever be reconciled with, renamed
   relative to, or kept fully separate from this family's own richer target concept is a
   repository-realization question, not decided here.
