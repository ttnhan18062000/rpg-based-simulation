---
status: authoritative
layer: architecture
authority: P1
audience: agent
tags: [architecture, world, content]
last_verified: "2026-09-23"
---

# World Rule Catalog — Roadmap

**Purpose.** A lightweight, high-level roadmap for completing the World Rule Catalog. This
roadmap is for **sequencing and review only** — batch boundaries are not semantic architecture,
and batches may split or merge when scenario evidence shows another grouping is better. Roughly
10–12 domain-facing batches, grouped into four milestones, plus one final integration pass that
sits outside that count by design (see "Batch count" below) — this is a **current forecast**,
not a target this roadmap should resist justified splits to preserve.

**Status (2026-09-21).** Drafted from an external-reviewer proposal, cross-checked against
`core_rpg_design_direction.md`'s target domain map and cross-cutting-layer table and
`simulation-rule-world-law-design-preparation.md`'s world-rule design order and foundational-law
list. Three gaps found in the original draft are resolved explicitly below (see "Cross-cutting
layer disposition") rather than left as silent omissions. Batch 01 is complete; Batch 02 (Time /
Authority / Reach) and Batch 03 (Capability / Cost / Capacity / Resource / Transformation) are
both drafted, each revised once per its own follow-up review, and both **PASS — frozen**; the
Milestone A History/Provenance completion pass is drafted and ready for high-level external
review. **Milestone A is fully drafted.** Batch 04 (Space/Environment/Movement) — the first
domain-facing Milestone B batch — is drafted, revised once per its own follow-up review, and
**PASS — frozen**. Batch 05 (Life/Body/Survival/Ecology) is drafted, normalized 2026-09-22 per
a Rule admission-discipline review (14 genuine Domain Rules of 22 original entries — see that
batch's own status below), and ready for high-level external review. Batch 06
(Perception/Knowledge/Information/Agency) is drafted 2026-09-22, revised the same day per a
targeted semantic-cleanup follow-up (11 genuine Domain Rules of 26 total catalog entries after
a KNOW-02/KNOW-03 merge, plus a corrected CONFLICTING/INERT-OFF/MISSING repository-finding
classification), and **PASS — ready to freeze**. Batch 07 (Capability/Progression/Conflict) is
drafted 2026-09-22, revised the same day per a targeted Rule-admission and semantic cleanup
follow-up (8 genuine Domain Rules of 26 total catalog entries after PROG-04/CONFLICT-02 were
reclassified to Inherited and LEARN-02 retired to Repository Findings), and **PASS — ready to
freeze**. Batch 08 (Objects/Ownership/Resources/Economy) is drafted 2026-09-22, revised the
same day per a targeted semantic-cleanup follow-up (6 genuine Domain Rules of 23 total catalog
entries after OBJ-03/PROP-02 were reclassified to Inherited), and **PASS — ready to freeze**.
Batch 09 (Social Relations/Family/Lineage) is drafted 2026-09-22, revised the same day per a
targeted semantic-cleanup follow-up (6 genuine Domain Rules of 19 total catalog entries after
SOC-04 was reclassified to Inherited and a reputation-reach re-investigation added a new
Inherited entry), and **PASS — ready to freeze**. Batch 10 (Organizations/Institutions/
Politics/Law) is drafted 2026-09-22, revised the same day per a targeted semantic-cleanup
follow-up (12 genuine Domain Rules of 31 total catalog entries after POL-02 was reclassified
to Inherited), and **PASS — ready to freeze**. This is the first batch drafted under the
standing direction (`tmp/world-rule-direction.md`, 2026-09-22): Rule statements describe only
target world semantics, repository classification implies no delivery priority, and the
review export carries a non-binding Implementation Candidates section. Batch 11 (Places/
Settlements/Territory/Culture/Belief) is drafted 2026-09-22, split into **Batch 11A** (Places/
Settlements/Territory, 10 genuine Domain Rules of 18 total catalog entries) and **Batch 11B**
(Culture/Collective Belief, 6 genuine Domain Rules of 12 total catalog entries, after BEL-03
was reclassified to Inherited on a second follow-up review) per that batch's own explicit
split permission, then both revised twice the same day per two successive follow-up reviews
(the second correcting parts of the first — see each sub-batch's own review export), and
both **PASS — ready to freeze**. Batch 12 (Magic/Supernatural) was first drafted 2026-09-21 as
a single file (5 genuine Domain Rules) per `tmp/world-rule-batch-12-ext-ai.md`, then fully
redrafted 2026-09-22 as five files (10 genuine Domain Rules of 31 total catalog entries) per a
corrected, richer instruction file, before any follow-up review of the original draft was
applied — the original single-file draft is superseded and removed. Batch 12 was then revised
the same day per a second, targeted semantic-cleanup follow-up (wording precision only —
"independent facts" softened to "semantically distinct facts," EFF-02 broadened to recognize
a durable-property/consequence shape of persistent supernatural state alongside the
ongoing-cause shape, SUP-03/MCAP-01/MCAP-02/STR-02 generalized away from over-strong framings;
the 10-Domain-Rule count is unchanged). Batch 12 is **PASS — ready to freeze**. **Final
Integration (Cross-Domain History / Significance / Propagation) is now complete: PASS — World
Rule Catalog ready to freeze** (see its own section below) — zero new Rules were required; the
next planned step is Simulation Rule → Implementation Mapping, once its own instruction file
is provided.

---

## Milestone A — Foundational World Semantics

**Goal:** establish the semantic laws every later domain depends on.

### Batch 01 — Identity / State Ownership / Causality

**Status: complete.** Drafted, adversarially scenario-expanded (FND-S01–S21, 8 counters), all
open semantic questions and owner-attention decisions dispositioned, and — as a direct product of
that work — a fourth foundational family was added at scope level only:

**Includes the History / Provenance dependency, discovered through scenarios, not planned in
advance.** `foundations/history-provenance.md` names (but does not yet draft) the family that
will eventually own CAUSE-05/CAUSE-06's persistence, provenance, compression, and
significance-fading substance. See that file and `causality.md`'s forward-reference notes for the
exact boundary between what stays in Causality and what migrates once it's drafted.

### Batch 02 — Time / Authority / Reach

**Status: PASS — frozen.** Drafted, then revised once per follow-up review (implementation
detail removed from Time, Authority's legitimacy framing broadened beyond actor identity, a real
internal inconsistency in Reach corrected, 4 scenario probes added). See
`review-exports/foundational-batch-02-review.md`.

Focus on:

```text
time and ordering
temporal persistence
authority to cause/change state
reach / locality / interaction possibility
```

These should answer: **when can something affect something else, and who is semantically
allowed to do so?**

**Clarified 2026-09-21 — world-semantic time is in scope; execution-mechanical time is not:**

```text
execution scheduling / same-tick domain ordering / engine cadence
→ out of scope

world-semantic time
→ in scope
```

*World-semantic time* — squarely this batch's job — may include ordering, duration, delay,
recurrence, expiration, aging, simultaneity, and temporal persistence where relevant: whether one
event happened before another in the world's own causal sense, how long an effect lasts, whether
something recurs or expires, whether two things can be simultaneous, and how age/duration accrue.
None of that is the same question as *which system's code runs first within a tick* —
`core_rpg_design_direction.md`'s Substrate domain scope includes "state transition, scheduling and
cadence, event flow" alongside identity/time/persistence, and that execution-mechanical side stays
out of this batch. This is an implementation/execution-order concern, not a world-semantic law —
already decided once, not merely assumed: Batch 01 drafted and deliberately rejected a same-tick
read/write-ordering candidate rule on exactly this basis (see `foundations/state-ownership.md`'s
"Candidates considered and not added"). Batch 02 should carry that same disposition forward
rather than re-deciding it, and should not attempt to write a semantic rule for
scheduling/cadence/event-flow.

### Batch 03 — Capability / Cost / Capacity / Resource / Transformation

**Status: PASS — frozen.** Drafted, then revised once per follow-up review (repository-status
language removed from CAP-05, cost-lifecycle distinction sharpened in COST-03, RES-01 broadened
beyond personally-held resources, universal atomicity removed from RES-04, LIMIT-03 generalized
beyond one assumed response). All five families kept separate (no merge found necessary);
threshold semantics folded into Capacity rather than given their own family; deterministic
randomness investigated and moved out of the Catalog entirely, on a rationale sharpened by the
follow-up. See `review-exports/foundational-batch-03-review.md`.

Focus on foundational constraints such as:

```text
capability requirements
cost
capacity / limits
resource / conservation semantics
thresholds
transformation permission
deterministic randomness / reproducibility where semantically relevant
```

Do not build generic implementation frameworks.

### Foundational completion pass — History / Provenance

**Status: drafted 2026-09-21, ready for high-level external review.** See
`review-exports/history-provenance-completion-review.md`. Six rules (HP-01–06): two restate/
newly-claim within this family's own home (HP-01, HP-02), three are direct migrations of
CAUSE-05/CAUSE-06's persistence-specific substance (HP-03/HP-04/HP-05), one consolidates three
already-accepted rules for future chronicle-content authors (HP-06). Establishes semantics for:

```text
historical continuity
provenance
persistence
causal-history retention
compression boundaries
legitimate fading
```

This is where the persistence-specific substance already flagged for migration out of CAUSE-05
and CAUSE-06 (declared-reach mechanism, compression-tier design, significance-fading mechanism)
actually gets drafted as History/Provenance's own rules, per those rules' own forward-reference
notes and `history-provenance.md`'s "Relationship to Causality" section. **The Final Integration
Batch later deepens and integrates these already-drafted semantics with significance, world
reaction, propagation, and long causal chains — it does not define History/Provenance for the
first time.** (See that batch's own updated wording below.)

**Milestone A exit:** later domains can define their own rules without redefining basic
identity, causality, authority, reach, time, capability, persistence, and now
historical-continuity/provenance semantics.

> **Guardrail, added 2026-09-21.** Foundational concepts such as Authority, Reach, Resource,
> Capacity, and State Ownership must not be automatically unified with similarly named
> later-domain concepts such as political authority, spatial reach, economic resources, or
> property ownership. A shared word is not a shared Rule — each later domain earns its own
> semantics through its own investigation (per `simulation-rule-world-law-design-preparation.md`
> §3.3's A–L order), even where a foundational family already used the same word at a more
> abstract level.

---

## Milestone B — Individual Entity World Model

This milestone should receive especially strong depth because the primary narrative subject is
the trajectory of individual entities.

### Batch 04 — Space / Environment / Movement

**Status: PASS — frozen.** Drafted 2026-09-21, then revised once per follow-up review
(implementation-specific wording removed from 8 rules, an ownership-framing correction adding
LOC-07 and loosening ENV-03's target-owner claim, 3 scenario probes added). 18 rules across
`space-environment/location-topology.md`, `environment.md`, `movement-navigation.md`. Two
confirmed repository gaps (no route/portal/directional-connection mechanism; no non-physical
movement mechanism) and one confirmed causally-inert environmental field
(`service_availability`). See `review-exports/space-environment-batch-04-review.md`.

```text
location
topology
movement
accessibility
environmental exposure
spatial reach
```

### Batch 05 — Life / Body / Survival / Ecology

**Status: drafted 2026-09-21, normalized 2026-09-22 per Rule admission-discipline review,
ready for high-level external review.** 22 catalog entries across `life-body/lifecycle.md`,
`body-condition.md`, `survival-needs.md`, `ecology-population.md` — of these, **14 are genuine
Domain Rules, 7 are Inherited/Applied Foundational Rules, 1 is a Scope/Deferred Boundary**
(no entry removed, no ID renumbered; see each file's own "Normalized 2026-09-22" note). Two
significant confirmed gaps (no HP recovery mechanism at all; aggregate population change
currently disconnected from real individual births/deaths) and one confirmed inert field pair
(`last_meal_tick`/`last_sleep_tick`). See `review-exports/life-body-batch-05-review.md`.

```text
life and death
body state
injury
needs
survival
creatures
population / ecological pressures
```

Keep individual entity semantics distinct from aggregate ecology.

### Batch 06 — Perception / Knowledge / Information / Agency

**Status: drafted 2026-09-22, revised the same day per a targeted semantic-cleanup follow-up
review, PASS — ready to freeze.** 11 genuine Domain Rules (26 total catalog entries — 11 Domain
Rules after a KNOW-02/KNOW-03 merge, 8 Inherited/Applied Foundational Rules, 7 Scope/Deferred
Boundaries) across `knowledge-agency/perception.md`, `knowledge-information.md`,
`agency-decision.md` (Memory folded into the Knowledge/Information file rather than given its
own). PERC-01/KNOW-01/INFO-01/AGENCY-02 were generalized away from over-specific wording,
AGENCY-03 given an explicit Opportunity/Actionable-Affordance terminology, and three
adversarial probes added (KA-S18–S20). The single most load-bearing finding, now correctly
classified **CONFLICTING** rather than MISSING: at least two live decision paths actively read
raw/omniscient world state directly, bypassing perception and the knowledge model entirely —
this does not invalidate the Rule Catalog; it means the Catalog successfully exposed a real
architecture mismatch. See `review-exports/knowledge-agency-batch-06-review.md`.

```text
observation
belief
truth vs knowledge
memory
information propagation
decision
motivation
opportunity / affordance
```

This batch strongly revisited scenarios such as:

```text
false belief → real action → real consequence
```

Batch 01's FND-S18/S19 already probed this at the foundational level via Causality/State
Ownership; this batch's own AGENCY reuses that evidence directly (Inherited, not restated as
new) and writes the actual Perception/Agency domain semantics on top of it.

### Batch 07 — Capability / Progression / Conflict

**Status: drafted 2026-09-22, revised the same day per a targeted Rule-admission and semantic
cleanup follow-up, PASS — ready to freeze.** 8 genuine Domain Rules (26 total catalog entries —
8 Domain Rules, 13 Inherited/Applied Foundational Rules, 5 Scope/Deferred Boundaries) across
`capability-progression/capability-progression.md`, `learning-adaptation.md`,
`conflict-combat.md`. PROG-01/02/05/06 were rewritten to remove repository-evaluation language
from their own Rule statements; PROG-04 and CONFLICT-02 were reclassified to Inherited;
Learning/Adaptation's LEARN-02 was retired to Repository Findings and LEARN-01 rewritten into
genuinely normative, open form; two adversarial probes were added (Non-Combat Lived Experience,
and CP-S15 deepened to distinguish generic kind/threat reaction from reaction to a specific
historied individual). Most load-bearing finding, unchanged: no counterforce against
repeated-trivial-kill XP farming, and a documentation claim (`max_xp_per_tick`) does not match
the actual implementation. See `review-exports/capability-progression-batch-07-review.md`.

```text
learning
adaptation
XP / level where applicable
qualitative transformation
power development
combat / conflict
injury → capability consequences
```

This is where lived-history progression should begin becoming concrete.

**Milestone B exit:** an individual can meaningfully live, perceive, decide, act, change, fight,
learn, survive, die, and accumulate history.

---

## Milestone C — Material and Social World

### Batch 08 — Objects / Ownership / Resources / Economy

**Status: drafted 2026-09-22, revised the same day per a targeted semantic-cleanup follow-up,
PASS — ready to freeze.** 6 genuine Domain Rules (23 total catalog entries — 6 Domain Rules, 9
Inherited/Applied Foundational Rules, 8 Scope/Deferred Boundaries) across `material-economy/
objects-material-culture.md`, `ownership-possession.md` (its own `PROP-*` prefix, deliberately
distinct from Batch 01's `OWN-*`), `resources-production.md`, `economy-exchange.md`. OBJ-03 and
PROP-02 were reclassified to Inherited (fully covered by History/Provenance's HP-02/HP-05 and
State Ownership's OWN-01/OWN-02); OBJ-02 and PROD-01 were generalized. Most significant
finding, unchanged: the heirloom-transfer/inheritance mechanism is **CONFLICTING** — it
constructs a real `ResourceTransferIntent(source_kind="CHEST")` on death that `src/core/
conservation.py`'s own resolver rejects with `UNKNOWN_SOURCE_KIND`, so the resolved heir never
actually receives the property. See `review-exports/material-economy-batch-08-review.md`.

```text
objects
material transformation
possession / ownership
production
scarcity
wealth
trade
economic consequences
```

**Resolved 2026-09-22.** Batch 01's own FND-S15/OWN-05 open question (role/authority
succession is real but object/wealth transfer to an heir has no mechanism at all) is now
resolved for the object/property side: `ownership-possession.md`'s PROP-02 states that the
producer of an ownership-changing event is not automatically the owner of the resulting
relation, and this batch's own repository investigation confirmed the specific implementation
defect (the `"CHEST"` resolver gap) that makes property transfer to an heir actually fail in
practice today, despite the code's own appearance of completeness.

### Batch 09 — Social Relations / Family / Lineage

**Status: PASS — frozen 2026-09-22.** Drafted 2026-09-22, then revised the same day per a
targeted semantic-cleanup follow-up. 6 genuine Domain Rules (19 total catalog entries — 6
Domain Rules, 9 Inherited/Applied Foundational Rules, 4 Scope/Deferred Boundaries) across
`social-lineage/social-relations.md`, `family-kinship.md`, `lineage-descent.md`. The follow-up
reworked SOC-01 (removed a five-fact decomposition requirement in favor of a two-category
structural-relation/subjective-attitude split), generalized SOC-03 to a positive
declared-semantics framing, reclassified SOC-04 to Inherited (fully covered by SOC-03 +
CAUSE-01 + KNOW-02), and narrowed LIN-01. Two clean resolutions of long-carried-forward open
questions (Batch 01's OWN-03 reputation-naming-collision, Batch 05's LIFE-05 family-meaning
deferral); one significant, notable finding, preserved: this repository's own default
heir-eligibility mechanism is social-bond-based, not kinship-based. A direct re-investigation
of reputation/recognition reach (left unchecked in the first draft) found it **CONFLICTING**
with Batch 06's own Perception/Knowledge semantics — every reputation consumer checked reads
another subject's `public_reputation` as globally available truth, never through a
perception/knowledge-mediated channel, collapsing the two causal steps between "an ancestor's
significance seeds a descendant's own starting standing" and "another subject learns of that
ancestry and reacts accordingly" into one ungated read. See
`review-exports/social-lineage-batch-09-review.md`.

```text
relationships
reputation
identity in society
family
inheritance
succession
feuds
obligations
```

**RESOLVED 2026-09-22.** The reputation-scalar-vs-reputation-labels naming collision Batch
01's OWN-03/FND-S05 surfaced is now formally documented: `SocialComponent.public_reputation`
(numeric scalar) and `PublicReputationProfile.labels` (qualitative label map, populated via
`ReputationUpdateService.process_witnessed_event()`, called from `src/engine/quests.py`) are
confirmed two legitimately separate, real, independently-owned fields — neither a duplicate of
the other. See `social-lineage/social-relations.md`'s own Inherited entry for the reputation
boundary.

### Batch 10 — Organizations / Institutions / Politics / Law

**Status: PASS — frozen 2026-09-22.** Drafted 2026-09-22, then revised the same day per a
targeted semantic-cleanup follow-up. 12 genuine Domain Rules (31 total catalog entries — 12
Domain Rules, 11 Inherited/Applied Foundational Rules, 8 Scope/Deferred Boundaries) across
`institutions-politics/organizations.md`, `roles-institutions.md`, `politics-authority.md`,
`law-enforcement.md`. The first batch drafted under the standing direction
(`tmp/world-rule-direction.md`, 2026-09-22) — target semantics lead, repository
classification implies no delivery priority, and the review export carries a non-binding
Implementation Candidates section. The follow-up generalized ORG-03 (standing policy
permitted without a fresh decision), refined INST-01 (organization/institution/role stay
conceptually distinct without requiring separate materialization), refined INST-03/INST-04
(authority/capability/power/legitimacy are correlated and causally related, not independent;
legitimacy's relationship to authority is institution-declared, not fixed), reclassified
POL-02 to Inherited (fully covered by SOC-03 + PROG-05), generalized LAW-01 (nine distinct
facts, no mandatory pipeline), and refined LAW-03 (an explicitly-global declared scope is
permitted; only *accidental* universality is prohibited). Two carried-forward open questions
resolved: Batch 02's AUTH-06 (political authority inherits the role-persists-occupant-change
rule unchanged) and Batch 09's `lineage-descent.md` deferral of political succession (POL-01:
succession ≠ kinship ≠ property inheritance). The single largest finding, unchanged by the
follow-up: no in-world law/crime/violation/enforcement subsystem exists at all. See
`review-exports/institutions-politics-batch-10-review.md`.

```text
groups
organizations
institutional roles
authority
political power
law
crime / enforcement where applicable
war
split / merge / succession of organizations
```

**Resolved 2026-09-22.** Batch 01's ID-06 found no organization/clan split, merge, or founding
mechanism exists at all (confirmed twice, independently, by FND-S06 and FND-S17). This batch's
own ORG-04 states the target requirement (a declared process must determine identity
continuity, transfer, and history wherever a domain models split/merge); the repository
realization is confirmed MISSING — the Rule is accepted regardless, per the standing direction
that a missing implementation does not invalidate a target semantic requirement.

### Batch 11 — Places / Settlements / Territory / Culture / Belief

**Status: PASS — both 11A and 11B frozen 2026-09-22, after two successive follow-up
reviews.** Per this batch's own instruction file's explicit size/split permission, split into
two coherent semantic clusters without changing this milestone's own overall ordering, then
revised twice the same day (`tmp/world-rule-batch-11-followup-ext-ai.md`, then
`tmp/world-rule-batch-11-followup-2-ext-ai.md` — the second correcting parts of the first; no
rule added merely to increase count):

- **Batch 11A — Places / Settlements / Territory.** 10 genuine Domain Rules (18 total catalog
  entries — 10 Domain Rules, 4 Inherited/Applied Foundational Rules, 4 Scope/Deferred
  Boundaries) across `places-culture/{places,settlements,territory-control}.md`. Directly
  resolves Batch 10's own deferred territorial-jurisdiction integration (territory is one
  declared jurisdiction basis among several, reusing Batch 10's own revised LAW-03 unchanged).
  PLACE-03 was corrected to match the foundational default (identity continuity is the default
  outcome of a Place transformation, not a case-by-case decision with no default); SETT-01
  was corrected to define settlement by its own declared function/state, stating the default
  relationship that settlement status may end/dormant while Place identity persists.
  `owner_faction_id`'s contested-territory finding was re-verified twice: the first pass
  narrowed CONFLICTING to control-vs-sovereignty and downgraded the contested-claim half to
  MISSING; the second pass corrected that downgrade, **restoring CONFLICTING** for the
  contested-claim half too — the field's own active, sole-authoritative role structurally
  forecloses representing a diverging claim, an active incompatibility, not a bare absence.
  See `review-exports/places-territory-batch-11a-review.md`.
- **Batch 11B — Culture / Collective Belief.** 6 genuine Domain Rules (12 total catalog
  entries — 6 Domain Rules, 3 Inherited/Applied Foundational Rules, 3 Scope/Deferred
  Boundaries) across `places-culture/{culture,collective-belief}.md`. This repository's own
  real, live, consumed "culture" system (`CultureState`, a four-axis derived-tendency score)
  was reassessed against actual consumers rather than its shared name: correctly **PARTIAL**,
  not CONFLICTING — nothing treats its four axes as culture's complete definition. BEL-03
  (sacredness achievable through cultural interpretation alone) was first reframed from
  REQUIRED to PERMITTED, then reclassified to Inherited once that reframing showed it added
  no content beyond BEL-02 + PLACE-02 combined — 11B's own genuine Domain Rule count drops
  from 7 to 6. `BeliefInstitution`'s own role remains narrowed to the institution-backed
  subset of collective belief only, and is now explicitly not presumed to be the semantic or
  implementation home for the recurring cross-domain significance gap — that conclusion is
  stated purely at the semantic level (a valid path from provenance to recognition to
  reaction is required; which mechanism supplies it is undecided). See
  `review-exports/culture-belief-batch-11b-review.md`.

Both sub-batches are drafted under the standing direction (`tmp/world-rule-direction.md`):
target semantics lead, repository classification implies no delivery priority, and both
review exports carry a non-binding Implementation Candidates section. See
`tmp/places-culture-batch-11-report.md` (local, not part of this catalog) for the full,
shared disposition report, including both follow-ups' own addenda.

```text
persistent places
settlement lifecycle
territory
place ownership / occupation
culture
religion
belief institutions
```

**Resolved 2026-09-22.** Settlement lifecycle (camp → settlement → ruin) — the gap Batch 01
found independently from two angles (ID-03, CAUSE-02) — is now addressed: `places.md`'s
PLACE-03 and `settlements.md`'s SETT-03 state that transformation continuity is never assumed
by default and must be declared per case; the repository's own real CITY→RUIN transformation
trail (`PlaceState.prior_kind`/`transformed_tick`) is confirmed as the one already-realized
instance, with the reverse (long-abandoned → resettled) and scale-up (village→town) cases
confirmed MISSING.

**Milestone C exit:** individuals can participate in durable material, economic, social,
institutional, territorial, and cultural structures that themselves evolve historically.

---

## Milestone D — Fantasy Integration and Whole-World Validation

### Batch 12 — Magic / Supernatural

**Status: PASS — ready to freeze (redrafted 2026-09-22).** First drafted 2026-09-21 as a
single file (5 genuine Domain Rules) per `tmp/world-rule-batch-12-ext-ai.md`, then fully
redrafted the next day per a corrected, richer instruction file
(`tmp/world-rule-batch-12-corrected-ext-ai.md`) before any follow-up review of the original
draft was applied — the original single-file draft is superseded and removed (`git rm`).
**10 genuine Domain Rules (31 total catalog entries — 10 Domain Rules, 16 Inherited/Applied
Foundational Rules, 5 Scope/Deferred Boundaries)** across five files:
`magic-supernatural/{supernatural-ontology,magic-capability,magical-effects,
supernatural-transformation,supernatural-entities-places}.md`. Directly reconciles Batch 11A's
PLACE-02 and Batch 11B's reclassified sacredness entry (both already attribution-relative) by
adding objective supernatural property as an eighth semantically distinct fact for Places
(PLC-01) — the mandatory boundary those two batches deliberately left open. Also directly
resolves two named deferred boundaries from earlier batches: Batch 04's non-physical-movement
boundary (MCAP-02) and Batch 06's own AGENCY-02 reflex/compulsion/mind-control carve-out
(exercised directly by the mind/memory-magic Inherited entry). The single largest finding: no
dedicated magic/supernatural mechanism of any kind exists anywhere in this repository,
comparable in scope to Batch 10's own Law/Enforcement gap — with one genuinely positive
structural exception: `PerceptionGate`'s own `magic_sense`/`magic_signal` channel is real,
live, structurally-ready information-channel infrastructure, currently INERT/OFF (existing
perception infrastructure capable of hosting a supernatural channel, not itself evidence the
channel's target semantics are implemented). Two more real, non-supernatural mechanisms
(`TransformationService`, `EvolutionSystem`) independently confirm this repository's own
architecture already supports STR-01's identity-persists/classification-changes shape.
**Revised the same day per a second, targeted semantic-cleanup follow-up** — wording
precision only, 10-Rule count unchanged: "independent facts" softened to "semantically
distinct facts" throughout; SUP-03 generalized away from a caster-centric causal-chain
framing; EFF-02 corrected to recognize a durable-property/consequence shape of persistent
supernatural state (e.g., a permanent enchantment outliving its caster) alongside the
ongoing-cause shape; STR-02 sharpened to separate required distinctness from permitted
existence. See `review-exports/magic-supernatural-batch-12-review.md`.

Do not make magic an isolated spell subsystem. Define its world rules and connect it outward
into:

```text
body
capability
environment
objects
knowledge
belief
places
institutions
conflict
```

**Note (2026-09-22, superseded by the redraft below).** The `human → vampire-like
transformation` probe this section originally flagged is now directly resolved, not merely
governed indirectly: `supernatural-transformation.md`'s own STR-01 states that a supernatural
transformation preserves the subject's own identity by default (reusing `places.md`'s
corrected PLACE-03), with species/kind/form classification stated as its own fact distinct
from identity — and MAG-S21 ("Human → Vampire") is now a dedicated scenario tracing exactly
this case directly against STR-01.

### Final Integration Batch — Cross-Domain History / Significance / Propagation

**Status: PASS — World Rule Catalog ready to freeze (completed 2026-09-22).** Not another
ordinary domain — per `tmp/world-rule-integration-ext-ai.md`, this phase tested whether the
frozen/freeze-ready Rules from Foundations and Batches 04–12 actually compose into the
intended persistent, systemic world, introducing no new major domain and no new Rule unless
strictly required. 12 flagship/counter scenario groups (18 scenarios: FI-PER, FI-CRE, FI-OBJ,
FI-PLC, FI-LIN, FI-ORG, FI-SET, FI-X) in
`scenarios/final-integration-history-significance.md`, each tracing every important stage
against current authoritative state, producer, canonical owner, information path, downstream
consumer, and persistent consequence. **Zero new Rules were added** — every flagship
trajectory (ordinary person → historically significant with no HERO role; ordinary creature →
named regional threat; ordinary object → relic via provenance alone; ordinary Place →
historic/sacred with multiple simultaneous attributed meanings; family → lineage → descendant
consequence without automatic inheritance; group → organization → institution surviving member
turnover; a full settlement growth/disaster/decline/resettlement lifecycle) proved fully
derivable end-to-end from Rules that already existed before this phase began, including the
candidate "shared historical grammar" wording itself, which was explicitly tested and rejected
as a standalone Rule (§36) because it is already fully composed from HP-01/02/05, PROG-06,
INFO-01/02, KNOW-01/02, BEL-01, and PLACE-02/ORG-01 acting together. **The one real finding
carried forward, precisely stated after a same-day targeted follow-up correction:** no tested
subject scale currently realizes a complete generic lived-history → named/contextual
recognition → persistent downstream reaction trajectory end-to-end — a recurring, shared
*late-stage* gap at six of seven subject scales (person, creature, object, place, organization,
lineage), which coexists with real, partial upstream realization that differs by domain (most
notably, object provenance is **PARTIAL/INERT-OFF**, not MISSING — `ItemInstance`'s own real,
feature-gated, untriggered-in-production history/provenance machinery, per Batch 08's own
already-established evidence). Documented explicitly as a repository fact, not resolved into
one proposed `UniversalSignificanceSystem`, per the instruction's own repeated warning against
exactly that move. **Previously established repository CONFLICTING findings (most notably
Batch 11A's own TERR-01/TERR-03 territorial-representation finding) are explicitly preserved,
not superseded, by this pass** — its own lightweight repository check simply did not
re-exercise those specific mechanisms. The follow-up also fixed a pre-existing `CAP-01`/
`CAP-02` ID collision between `foundations/capability.md` and `magic-supernatural/magic-
capability.md` before freeze, renaming the magic-capability Rules to `MCAP-01`/`MCAP-02`
throughout the Catalog rather than merely disambiguating by file scope. See
`review-exports/final-integration-history-significance-review.md` for the full Canonical State
Ownership matrix, Information/Reach/Aggregate↔Individual audits, and the 13 Required Final
Answers.

History / Provenance itself was not redefined here — it remains first drafted in Milestone A's
foundational completion pass (see above); this phase deepened and integrated those semantics
(historical continuity, provenance, persistence, compression boundaries, legitimate fading)
with significance, world reaction, propagation, and cross-domain power conversion, per that
Milestone's own original framing.

---

## Cross-cutting layer disposition

**Added 2026-09-21.** `core_rpg_design_direction.md` §7 names five cross-cutting layers, not
domains. This roadmap's batches account for three of them; the other two need an explicit call
rather than silent omission:

- **History, significance & world reaction** — covered by Batch 01's History/Provenance naming,
  Milestone A's foundational completion pass (actual drafting), and the Final Integration
  Batch's later deepening/integration with significance and world reaction specifically.
- **Systemic pressure & propagation** — covered by the Final Integration Batch ("power
  conversion, cross-domain propagation, counterforces").
- **Evaluation** — **correctly out of scope for this Catalog**, not a gap. Rule/Law design
  defines world semantics; evaluation semantics (what must hold, what constitutes violation, what
  should be observable) is `simulation-rule-taxonomy-evaluation-direction.md`'s own document, per
  the evaluation/governance boundary already established in
  `simulation-rule-world-law-design-preparation.md` §3.8. No batch should attempt to redefine or
  absorb it.
- **Observation & legibility** (read models, presenters, chronicles, telemetry, inspection
  surfaces) — **out of scope for this Catalog.** This is how the world's state is *presented*,
  not a rule about what is *true* of the world — the same distinction the project's Architecture
  Rule already draws ("API/routes present shaped read models through presenters/schemas, not raw
  domain objects"). No batch should write a semantic Rule family for it; it stays governed by the
  existing Architecture Rule and `/api-design-principles`, outside this Catalog's remit.
- **Content authoring & world assembly** (catalogs, world modules, compilation, content
  resolution, registries) — **mostly out of scope, with one real semantic sub-question flagged,
  not resolved, for whichever batch first needs it.** The compilation/tooling mechanics
  themselves are implementation, not world semantics. But "where authored identity enters the
  world" touches a genuine open question already latent under Batch 01's ID-04 (creation
  establishes identity explicitly): does an authored catalog template carry its own identity
  distinct from the instances it produces, or is it purely a stamp with no identity of its own?
  Not decided here — flagged so whichever future batch first needs the answer (most likely
  Objects/Batch 08 or Organizations/Batch 10, wherever templated instantiation first becomes
  concrete) cites this rather than silently deciding it.

## Batch count

The 12 numbered batches above, plus the unnumbered Milestone A History/Provenance completion
pass, plus the Final Integration Batch, total 14 labeled units. **This entire section is a
current forecast, not a target** — "10–12" was never meant to resist a justified split (or, as
happened here, a justified insertion); the count is expected to keep moving as scenario evidence
warrants, per "Roadmap governance" below. The Final Integration Batch specifically is not an
ordinary domain batch (see its own heading above) and was never counted toward the forecast range
either way.

---

## Expected Depth Reassessment

After Milestones B and C, and again after final integration, reassess the existing Expected
Depth Priority Map (`simulation-rule-world-law-design-preparation.md` §4). Compare expected depth
against the actual causal load revealed by Rules and Scenarios so far. Revise ratings only when
evidence warrants it.

---

## Batch workflow

Every batch should follow approximately:

```text
seed scenarios
        ↕
draft / refine rules
        ↕
counter-scenarios
        ↓
cross-domain dependency findings
        ↓
canonical files updated
        ↓
review export generated
```

Do not require external high-level review for every trivial internal edit. Generate an external
review packet at: major batch completion, milestone completion, major semantic contradiction, or
unexpected architectural discovery.

---

## Roadmap governance

Keep this roadmap high-level. Do not create implementation milestones yet. Do not estimate code
effort. Do not freeze the exact number of batches — the "10–12" figure anywhere in this document
is a current forecast, never a target to protect by declining a justified split or insertion.

- If a batch becomes too broad: split it.
- If two adjacent batches are inseparable after investigation: merge them.
- If scenario evidence reveals a missing foundational family: add it explicitly, but require a
  semantic reason rather than taxonomy completeness (this is exactly how History/Provenance was
  added in Batch 01, and how its own completion pass was then moved into Milestone A — scenario
  evidence and semantic dependency, not a desire for a complete-looking list or a fixed count).
- **Rule admission discipline (standing, applied 2026-09-22 to Batch 05, required from the
  first draft for every batch from Batch 06 onward).** There is no expected or preferred rule
  count per family — "roughly 5–6 rules per family" is never an implicit template; let
  scenarios and semantics determine the shape. Before assigning a new Rule ID, ask: does this
  statement add or refine target world semantics beyond Rules already defined elsewhere? A
  direct reuse/reconfirmation of an earlier Rule ID → Inherited/Applied Foundational Rule, no
  new ID. "This belongs to a later domain" → Scope/Deferred Boundary, no new ID. A repository
  implementation fact or gap → Repository Finding, evidence within a Rule, not the Rule itself.
  Only a genuinely new or domain-refined semantic constraint earns a new local Rule ID. Each
  canonical domain-family file should separate Domain Rules / Inherited / Scope-Deferred /
  Repository Findings / Open Questions explicitly.
- **Standing direction — Rules lead, repository is evidence (2026-09-22, `tmp/world-rule-
  direction.md`, required from Batch 10 onward).** The current phase answers "what must the
  simulated world mean, and what causal relationships must be valid" — not "which features
  should we build next." Repository inspection remains valuable but is evidence *against* the
  target model, never itself the source of a Rule (unless the repository reveals a semantic
  question already independently accepted as part of the target design). SUPPORTED/PARTIAL/
  CONFLICTING/MISSING/INERT-OFF classify realization only, never delivery priority — MISSING
  is not a feature requirement, and a Rule may be fully valid while its implementation
  remains deferred indefinitely. State explicitly whether a Rule is REQUIRED (the world would
  become semantically invalid without it) or PERMITTED (the architecture must allow it when a
  domain chooses to model it) wherever that distinction matters. Every review export from
  Batch 10 onward carries a non-binding **Implementation Candidates** section, and
  Owner-attention decisions focus on design semantics (does this belong here, are these
  actually separate concepts, which domain owns this state) rather than implementation
  choices (should we build/enable/fix X now) — those questions belong to a later
  Simulation-Rule-to-Implementation-Mapping phase, not this one.

The governing principle remains: **Scenario Bank and World Rule Catalog co-evolve; the roadmap
organizes the investigation rather than predetermining its conclusions.**
