---
status: authoritative
layer: architecture
authority: P1
audience: agent
tags: [architecture, world, content]
last_verified: "2026-09-23"
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

> Culture is whichever of language, customs, norms, rituals, symbols, stories, aesthetic
> practices, food, social expectations, or shared historical interpretation a domain chooses
> to model, with no fixed catalog required in advance. Culture is distinct from an
> individual's own belief (a person may belong to a culture and privately reject parts of
> it), from law (a legal rule and a cultural norm are different facts even where they agree),
> from religion (a culture may contain religious content without being reducible to it), from
> faction membership (an organization is not the same fact as a shared culture, though members
> may share one), from ethnicity, and from settlement identity — a culture may overlap with
> any of these without collapsing into it. Culture cannot be reduced to any single one of
> these adjacent concepts, nor to one assumed-universal scalar.

**Disposition: ACCEPT — REQUIRED for the distinctness; which specific cultural content any
domain models is PERMITTED, open-ended content; wording corrected 2026-09-22 per a second
external follow-up review to remove implementation-oriented language from the Rule statement
itself.** The original wording ("Culture is never required to be a generic scalar (a
`CultureScore`)") stated an implementation-shaped prohibition directly inside the Rule's own
normative text. The follow-up correctly identified that the underlying semantic principle —
culture cannot be reduced to a single adjacent concept or to one assumed-universal scalar — is
what belongs in the Rule itself; whether any specific domain later derives a score or
projection *from* a richer culture model is an implementation matter, addressed in Repository
Findings/Implementation Candidates, not a constraint the Rule's own text needs to name by a
specific data-shape term. Passes the admission test unchanged: no earlier Rule addresses
culture as its own concept — this is genuinely new content, against being collapsed into five
adjacent, already-established concepts (individual belief: Batch 06; law: Batch 10; faction
membership: Batch 10's ORG-02; settlement: `settlements.md`'s SETT-01).

**Repository evidence: PARTIAL — a narrower, valid representation, not CONFLICTING (reassessed
2026-09-22 per a second external follow-up review, examining what `CultureState` actually
claims to represent and how its consumers use it, rather than treating the shared name
"culture" or its narrower scope as sufficient grounds for CONFLICTING on their own).**
`CultureState`/`CultureCarryForward` (`src/domains/culture/model.py`, E62A/E62B) is real, live,
and genuinely consumed (`CulturalBiasApplicator` biases route-scoring tags from it) — it is
structurally a fixed four-axis derived-tendency score (`fatalism`, `hero_veneration`,
`resource_scarcity_memory`, `faction_conflict_exposure`), each a float in `[0.0, 1.0]` derived
from event history and carried per-region across campaign episodes. Checked directly: no code
anywhere treats these four axes as the complete, authoritative, or exhaustive definition of
culture in a way that would foreclose a richer culture model coexisting alongside it —
`CulturalBiasApplicator`'s own consumption is a transient, per-scoring-call bias delta, never
written to durable state, and nothing in the model or its consumers asserts or enforces that
these four axes are all "culture" could ever be. This is correctly classified as a
**derived regional cultural tendency/projection** — a real, narrower, and semantically valid
representation of one slice of what culture can mean, not an active collapse of this Rule's
own richer target concept. Naming the same word ("culture") for a narrower thing is, by
itself, not sufficient grounds for CONFLICTING, per the follow-up's own explicit correction.

**Scenarios:** [CB-S01](../scenarios/culture-belief-batch-11b.md#cb-s01) (culture spans
border), [CB-S02](../scenarios/culture-belief-batch-11b.md#cb-s02) (one territory, multiple
cultures).

---

## CULT-02 — Culture is a persistent collective social pattern that may be carried through practices, norms, rituals, institutions, stories, symbols, records, language, and repeated social behavior — through durable artifacts/institutions or through oral tradition and repeated practice with no durable artifact at all; culture is never reducible to the statistical average of individuals' own current states

> A settlement's or population's own cultural pattern is never computed merely as the average
> of its current residents' own private beliefs or practices, and it is never identical to
> every individual's own behavior. Culture may be carried through durable artifacts and
> institutions (records, symbols, declared rules), but that is only one legitimate carrier
> among several — an oral tradition, a repeated social practice, or a shared convention may
> just as legitimately carry a real, persistent cultural pattern through nothing but ongoing
> social transmission, with no institution, record, or physical object storing it at all.
> Whatever a specific culture's own content and carrier turn out to be, it is never reducible
> to a live average of current individual states: a settlement's custom favoring ancestor
> worship does not imply every resident personally believes in it, and does not disappear
> merely because the current population's own average belief has shifted, absent a real,
> declared change process (see CULT-04).

**Disposition: ACCEPT — REQUIRED; reworded twice, 2026-09-22, per two successive external
follow-up reviews.** The original wording ("culture consists of durable collective
artifacts") risked being read as a strict, exhaustive definition. A first follow-up loosened
this to "may contain durable/shared... structures," but a second follow-up correctly
identified that even that revision still implicitly centered culture on durability/artifacts
as the primary carrier — this further revision makes explicit that a purely non-durable
carrier (oral tradition, repeated practice, shared convention, with no institution, record, or
object storing it) is an equally legitimate way for culture to persist, not a lesser or
implied case. This keeps the substantive non-admission claim (culture is never reducible to a
live statistical average of current individual belief) fully intact while removing any
remaining artifact-centric bias from the Rule's own wording. Passes the admission test
unchanged: this goes beyond the already-established individual/aggregate distinctness
(Batch 05's ECOL-01/02, Batch 09's SOC-01) by forbidding the specific "average = culture"
shape the batch instruction's own §35 names as a mistake, which the pure aggregate/individual
boundary alone does not itself forbid.

**Repository evidence: PARTIAL.** `CultureCarryForward`'s own per-region, per-episode
snapshot shape is durable and persists independently of any single entity's own belief state
— consistent with the "persistent, not a live average" half of this Rule, realized here via
the durable-artifact/institutional-projection carrier (CULT-01's own PARTIAL finding), not the
oral-tradition/repeated-practice carrier this revision also explicitly permits. No mechanism
was found that carries any cultural content purely through repeated social behavior with no
durable backing at all — confirmed MISSING for that specific carrier, though this Rule does
not require it to exist, only permits it.

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

- **PARTIAL, not CONFLICTING (reassessed 2026-09-22 per a second external follow-up
  review) — this repository's own "culture" system is a four-axis derived-tendency score, a
  narrower, valid projection, not an active collapse of this family's own richer target
  semantics.** See CULT-01 above. Real, live, and genuinely consumed
  (`CulturalBiasApplicator`), and worth a reader's attention precisely because it shares the
  word "culture" with this family's own much richer concept — but nothing in the code treats
  those four axes as complete or exhaustive, so this is correctly a narrower-scope PARTIAL
  finding, not a naming collision serious enough to call CONFLICTING on its own.
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
- **Target semantic:** culture is a real, richer collective pattern than a fixed set of
  derived-tendency axes, though a narrower projection is a legitimate partial realization
  (CULT-01, CULT-02).
  **Current realization:** `CultureState`'s own four fixed axes are a real, valid, but
  narrower regional-tendency projection (PARTIAL, per the second follow-up's own
  reassessment) — not a violation, but also not the full concept.
  **Possible implementation direction (moved here 2026-09-22 from Owner-Attention, per the
  second follow-up's own explicit instruction):** should `CultureState` ever be renamed,
  reconciled with, or kept fully separate from a future richer culture model, as an
  implementation/data-shape decision — no schema or renaming is committed here.
  **Implementation decision:** DEFERRED.

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
2. **Added 2026-09-22 per a second external follow-up review — what makes cultural state
   persistent beyond current individuals?** Not decided here in the abstract — CULT-02's own
   revision names durable artifacts/institutions and oral tradition/repeated practice as two
   legitimate carriers, but which carrier(s) any specific domain actually uses, and how a
   domain would recognize "the culture is still the same culture" through either carrier's
   own drift, remains open.

*(The prior version of this list's own item 2 — "whether `CultureState`'s own four fixed
axes should ever be reconciled..." — was moved to Implementation Candidates below, per the
second follow-up's own explicit instruction to keep storage/data-shape questions there
rather than in Owner-Attention/Open Questions.)*
