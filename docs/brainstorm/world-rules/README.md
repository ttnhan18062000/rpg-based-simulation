---
status: active
layer: architecture
authority: P1
audience: agent
tags: [architecture, world, content]
---

# World Rule Catalog

**Authority/status.** P1 navigation index for the World Rule Catalog and Scenario Bank. This
index is not itself a design document — it points to the rule-family and scenario files that are.

**Relationship to the P1 direction/preparation documents.** This catalog is the actual Rule
Catalog that `docs/brainstorm/simulation-rule-world-law-design-preparation.md` prepared the
method for, and it inherits its semantics from `docs/brainstorm/core_rpg_design_direction.md`
(target domain map, decisions log) and
`docs/brainstorm/simulation-rule-taxonomy-evaluation-direction.md` (anti-correlation principle,
outcome-neutrality principle, evaluation/governance boundary). It does not restate those
documents; it cites and applies them.

**Roadmap.** [roadmap.md](roadmap.md) is the sequencing plan for the whole Catalog — 12 batches
across 4 milestones, plus a final integration pass. It is not semantic architecture; batch
boundaries may split or merge as scenario evidence warrants.

## Design-area index

Only the areas with actual rule files exist below. Do not scaffold empty files for areas not yet
reached — see `simulation-rule-world-law-design-preparation.md` §3 for the full world-rule design
order.

| Area | Status | File |
|---|---|---|
| Identity | Foundational Batch 01 drafted | [foundations/identity.md](foundations/identity.md) |
| State Ownership | Foundational Batch 01 drafted | [foundations/state-ownership.md](foundations/state-ownership.md) |
| Causality | Foundational Batch 01 drafted | [foundations/causality.md](foundations/causality.md) |
| History / Provenance | Milestone A completion pass drafted 2026-09-21 (HP-01–06) — ready for high-level external review | [foundations/history-provenance.md](foundations/history-provenance.md) |
| Time | Foundational Batch 02 — PASS, frozen | [foundations/time.md](foundations/time.md) |
| Authority | Foundational Batch 02 — PASS, frozen | [foundations/authority.md](foundations/authority.md) |
| Reach | Foundational Batch 02 — PASS, frozen | [foundations/reach.md](foundations/reach.md) |
| Capability | Foundational Batch 03 — PASS, frozen | [foundations/capability.md](foundations/capability.md) |
| Cost | Foundational Batch 03 — PASS, frozen | [foundations/cost.md](foundations/cost.md) |
| Capacity / Limits | Foundational Batch 03 — PASS, frozen | [foundations/capacity.md](foundations/capacity.md) |
| Resource / Conservation Semantics | Foundational Batch 03 — PASS, frozen | [foundations/resource.md](foundations/resource.md) |
| Transformation | Foundational Batch 03 — PASS, frozen | [foundations/transformation.md](foundations/transformation.md) |
| Location / Topology | Batch 04 — PASS, frozen | [space-environment/location-topology.md](space-environment/location-topology.md) |
| Environment | Batch 04 — PASS, frozen | [space-environment/environment.md](space-environment/environment.md) |
| Movement / Navigation | Batch 04 — PASS, frozen | [space-environment/movement-navigation.md](space-environment/movement-navigation.md) |
| Lifecycle | Batch 05 drafted, normalized 2026-09-22 | [life-body/lifecycle.md](life-body/lifecycle.md) |
| Body / Condition | Batch 05 drafted, normalized 2026-09-22 | [life-body/body-condition.md](life-body/body-condition.md) |
| Survival Needs | Batch 05 drafted, normalized 2026-09-22 | [life-body/survival-needs.md](life-body/survival-needs.md) |
| Ecology / Population | Batch 05 drafted, normalized 2026-09-22 | [life-body/ecology-population.md](life-body/ecology-population.md) |
| Perception | Batch 06 drafted | [knowledge-agency/perception.md](knowledge-agency/perception.md) |
| Knowledge / Information / Memory | Batch 06 drafted | [knowledge-agency/knowledge-information.md](knowledge-agency/knowledge-information.md) |
| Agency / Decision | Batch 06 drafted | [knowledge-agency/agency-decision.md](knowledge-agency/agency-decision.md) |

## Rule Catalog progress

- **Foundational Batch 01** (Identity, State Ownership, Causality): drafted, adversarially
  expanded, its open questions dispositioned (deferred / cross-domain-link / implementation-gap /
  resolved-by-naming-a-family — see below), ready for high-level external review. See
  `tmp/world-rule-foundational-batch-01-report.md` (local, not part of this catalog) for the full
  disposition report.
- **History / Provenance** introduced 2026-09-21 as an explicit foundational/cross-cutting Rule
  family, then drafted the same day as the Milestone A completion pass planned in `roadmap.md`
  (HP-01–06 — see [foundations/history-provenance.md](foundations/history-provenance.md)):
  ready for high-level external review. Not a numbered batch; migrates CAUSE-05/CAUSE-06's
  persistence-specific substance and consolidates OWN-04/OWN-06/REACH-04 for future chronicle
  content authors, with only HP-01/HP-02 as genuinely new claims. See
  `review-exports/history-provenance-completion-review.md`.
- **Foundational Batch 02** (Time, Authority, Reach): drafted, revised once per follow-up
  instruction (implementation-detail removed from Time, Authority's actor-only framing broadened,
  a real internal inconsistency in Reach corrected, 4 scenario probes added), **PASS — ready to
  freeze**. See `tmp/world-rule-foundational-batch-02-report.md` (local, not part of this
  catalog) for the full disposition report.
- **Foundational Batch 03** (Capability, Cost, Capacity/Limits, Resource/Conservation Semantics,
  Transformation): drafted, revised once per follow-up instruction (repository-status language
  removed from CAP-05, COST-03's cost-lifecycle distinction sharpened, RES-01 broadened beyond
  personally-held resources, universal atomicity removed from RES-04, LIMIT-03 generalized
  beyond one assumed response), **PASS — ready to freeze**. Threshold semantics were investigated
  and folded into Capacity (LIMIT-04) rather than given their own family; deterministic
  randomness was investigated and moved out of the Catalog entirely, on a rationale sharpened by
  the follow-up (see `review-exports/foundational-batch-03-review.md`'s explicit call-outs). See
  `tmp/world-rule-foundational-batch-03-report.md` (local, not part of this catalog) for the
  full disposition report.
- **Milestone A is fully drafted**: all three foundational batches (01, 02, 03) plus the
  History/Provenance completion pass. Batch 02, Batch 03, and History/Provenance are all ready
  for review (Batch 02/03 **PASS — ready to freeze**; History/Provenance ready for high-level
  external review, not yet marked frozen).
- **Batch 04** (Space/Environment/Movement) — the first domain-facing Milestone B batch —
  drafted 2026-09-21 immediately after Milestone A, revised once per follow-up instruction
  (implementation-specific wording removed from 8 rules, a topology/environment
  ownership-framing correction adding LOC-07 and loosening ENV-03's target-owner claim, 3
  scenario probes added), **PASS — ready to freeze**. 18 rules across Location/Topology,
  Environment, and Movement/Navigation. Two confirmed repository gaps (no route/portal/
  directional-connection mechanism; no non-physical movement mechanism) and one confirmed inert
  environmental field (`service_availability`) — see
  `review-exports/space-environment-batch-04-review.md`'s explicit call-outs. See
  `tmp/space-environment-batch-04-report.md` (local, not part of this catalog) for the full
  disposition report.
- **Batch 05** (Life/Body/Survival/Ecology) — the second domain-facing Milestone B batch, and a
  high-priority one since individual living entities are the primary narrative subjects —
  drafted 2026-09-21 immediately after Batch 04, then normalized 2026-09-22 per a Rule
  admission-discipline review: of its 22 original entries, **14 are genuine Domain Rules, 7 are
  Inherited/Applied Foundational Rules (reused/reconfirmed, no new claim), and 1 is a
  Scope/Deferred Boundary** — no entry removed, no evidence discarded, no ID renumbered. Four
  families: Lifecycle, Body/Condition, Survival Needs, Ecology/Population; ready for
  high-level external review. Two significant confirmed gaps (no HP recovery mechanism at all;
  aggregate population change currently disconnected from real individual births/deaths) and
  one confirmed inert field pair (`last_meal_tick`/`last_sleep_tick`) — see
  `review-exports/life-body-batch-05-review.md`'s explicit call-outs. See
  `tmp/life-body-batch-05-report.md` (local, not part of this catalog) for the full disposition
  report.
- **Rule admission discipline (applied 2026-09-22, standing for every future batch).** There is
  no expected or preferred rule count per family — a statement earns a new local Rule ID only
  if it adds or refines target world semantics beyond Rules already defined elsewhere. A
  direct reuse of an earlier Rule ID is an Inherited/Applied Foundational Rule; "this belongs
  to a later domain" is a Scope/Deferred Boundary; a repository implementation fact or gap is a
  Repository Finding; a reconfirmation of an earlier Rule is evidence, not a new Rule. Only
  genuinely new or domain-refined semantic constraints get a new Rule ID. Each canonical
  domain-family file should separate these categories explicitly (Domain Rules / Inherited /
  Scope-Deferred / Repository Findings / Open Questions) rather than let its own Rule Inventory
  imply every accepted candidate earned a new ID.
- **Batch 06** (Perception/Knowledge/Information/Agency) — the third domain-facing Milestone B
  batch, and a high-priority one, since perception/knowledge/agency govern how an individual
  forms an imperfect view of the world and acts from it — drafted 2026-09-22 directly with the
  five-category admission discipline, then revised the same day per a targeted semantic-cleanup
  follow-up (generalized PERC-01/KNOW-01/INFO-01/AGENCY-02 away from over-specific wording,
  merged KNOW-02/KNOW-03, clarified AGENCY-03's Opportunity/Actionable-Affordance terminology,
  and reclassified the omniscience finding as CONFLICTING rather than MISSING), **PASS — ready
  to freeze**. 11 genuine Domain Rules (26 total catalog entries including 8 inherited/applied
  foundational rules and 7 scope/deferred boundaries) across Perception, Knowledge/Information/
  Memory (Memory folded in rather than given its own file), and Agency/Decision. The single most
  load-bearing finding, now correctly classified **CONFLICTING** (an active violation, not
  merely an absent feature): at least two live decision paths (`ResourceOpportunityProvider.
  get_opportunities()`, `HarvestScorer.score()`) read raw/omniscient world state directly,
  bypassing `PerceptionGate` and `entity.cognition.knowledge_model` entirely — this does not
  invalidate the Rule Catalog; it means the Catalog successfully exposed a real architecture
  mismatch. See `review-exports/knowledge-agency-batch-06-review.md`'s explicit call-outs for
  this and further confirmed gaps, correctly split into CONFLICTING / INERT-OFF / MISSING
  categories (`knowledge_model` has no decision consumer, INERT/OFF; `PerceptionUpdatePhase`
  has zero production call sites, INERT/OFF; `MemoryUpdatePhase` is wired but inactive,
  INERT/OFF; no in-simulation motive-inference mechanism, MISSING; no intermediary-link-failure
  or content-distortion modeling, MISSING, reconfirming REACH-05's own already-flagged gap). See
  `tmp/knowledge-agency-batch-06-report.md` (local, not part of this catalog) for the full
  disposition report.
- Do not begin Batch 07 (Capability / Progression / Conflict) until Batch 06 receives
  high-level review.

## Scenario Bank index

| Batch | File | Scenario IDs |
|---|---|---|
| Foundational Batch 01 | [scenarios/foundational-batch-01.md](scenarios/foundational-batch-01.md) | FND-S01 – FND-S21 |
| Foundational Batch 02 | [scenarios/foundational-batch-02.md](scenarios/foundational-batch-02.md) | TAR-S01 – TAR-S17 |
| Foundational Batch 03 | [scenarios/foundational-batch-03.md](scenarios/foundational-batch-03.md) | CTR-S01 – CTR-S20 |
| History / Provenance completion | [scenarios/history-provenance-completion.md](scenarios/history-provenance-completion.md) | HP-S01 – HP-S02 |
| Batch 04 (Space/Environment/Movement) | [scenarios/space-environment-batch-04.md](scenarios/space-environment-batch-04.md) | SPC-S01 – SPC-S15 |
| Batch 05 (Life/Body/Survival/Ecology) | [scenarios/life-body-batch-05.md](scenarios/life-body-batch-05.md) | LB-S01 – LB-S16 |
| Batch 06 (Perception/Knowledge/Information/Agency) | [scenarios/knowledge-agency-batch-06.md](scenarios/knowledge-agency-batch-06.md) | KA-S01 – KA-S20 |

## Unresolved cross-domain questions

Recorded in full in each rule file's own "Cross-domain links" / "Open questions carried forward"
sections. Not yet promoted to `cross-domain/` — per the adopted structure, that directory is
created only once a link becomes a substantial shared contract, not for every link recorded in a
rule file. Every item below carries an explicit disposition (as of 2026-09-21) rather than sitting
as a bare open question — "unresolved" here means "not yet designed," not "undecided how to treat":

- **DEFER, no universal test invented.** What makes a transformation identity-ending, in general?
  (ID-03) — stays deferred per-domain (Magic, Places); ID-03's default+exception shape is
  unchanged.
- **DEFER to Organizations / Places.** Organization/settlement split, merge, and founding
  semantics (ID-04, ID-06, reconfirmed a third time by FND-S17) — no mechanism exists at all;
  resolved when those domain batches are reached, not before.
- **DEFER to Objects & Material Culture.** A corpse's own identity relative to the deceased
  entity's identity (ID-05).
- **Cross-domain semantic link question, not an ownership problem.** `impaired capability →
  economic loss` (OWN-05) — resolved when Capability/progression and Economy/resources rules
  actually exist to define it; OWN-05 already establishes crossing owners is legitimate, so this
  is a link to design, not a boundary to fix.
- **DEFER across Family/Lineage, Politics, Objects/Economy jointly; ownership stays separate.**
  Succession's property/wealth transfer (OWN-05, FND-S15) — role/authority succession is real and
  correctly owned by Politics; nothing transfers objects or wealth, and whichever domain is
  reached first should cite this rather than deciding it alone.
- **Treated as an implementation/repository gap, not a design-order question.** No general
  capability/precondition detector exists (CAUSE-04) — does not argue for reordering the
  world-rule design order, only for building the detector once, generally, when it's built.
- **RESOLVED — named, then drafted.** History/Provenance's compression-tier constraint (HP-04)
  and significance-fading constraint (HP-05) are now drafted Rules, migrated from CAUSE-05/
  CAUSE-06 — see [foundations/history-provenance.md](foundations/history-provenance.md). The
  *mechanisms* themselves (what fades first, at what rate) remain undesigned, per HP-04/HP-05's
  own stated non-goal — not a gap, a deliberate scope boundary.
- Reputation scalar vs. reputation labels narrative relationship (OWN-03, FND-S05): flagged for
  the Social relations batch — unchanged, not part of this disposition pass.

**From Foundational Batch 02 (drafted 2026-09-21, revised same day per follow-up):**

- **Not conclusively verified — a judgment call, not this session's to make.** Whether a
  currently-incapacitated role-holder's unaffected authority (TAR-S07) is intentional or an
  unexamined gap. Flagged for owner review, not resolved by design.
- **Explicitly deferred per the roadmap's guardrail; sharpened by AUTH-06's revision.** Whether
  political authority (Politics/authority & war) inherits AUTH-01–06 unchanged or refines them —
  and specifically, what makes a political role/mandate "remain valid."
- **Explicitly deferred per the same guardrail.** Whether spatial reach (Space/environment) or
  magical reach (Magic/supernatural) inherit REACH-01–06 unchanged or refine them.
- **Reframed, not merely deferred.** Whether forward-only aging is a Life/Body/Survival law at
  all, and for which subjects, is now that future batch's own question from scratch (TIME-05's
  revision) — no longer an accepted Time constraint with only an open exception question.
- **RESOLVED — upgraded from read-level evidence to a scenario trace.** REACH-03's asymmetry
  finding now has a dedicated scenario (TAR-S17); formal domain-specific stealth/ambush content
  is still Perception/knowledge/information's own job.
- **New, confirmed MISSING.** REACH-05's intermediary-link-failure modeling (a messenger delayed,
  blocked, or lying) — deferred to whichever future batch (most plausibly Perception/knowledge/
  information) first needs it.
- **Sharpened by Batch 04.** Whether spatial reach inherits REACH-01–06 unchanged is now
  answered for the concrete spatial case: MOV-06/LOC-02 confirm spatial reach *instantiates*
  foundational Reach without needing its own refinement — the earlier open question is resolved
  for Space specifically (Magic/supernatural's own spatial-adjacent reach concepts remain
  separately open).

**From Foundational Batch 03 (drafted 2026-09-21, revised same day per follow-up):**

- **Confirmed MISSING, not merely unexplored.** CAP-05's body/form and environment capability
  gates — deferred to Capability & progression and Space/environment respectively.
- **Not decided.** CAP-05's relationships/institutional-support capability gate — deferred to
  Groups/organizations & institutions if that domain ever needs one.
- **Not yet repository-evidenced as their own category.** COST-01's attention and social/
  political-consequence cost categories — deferred to Agency/decision and Politics/authority &
  war respectively.
- **Not independently re-verified this batch.** Whether crafting gates on a learned-recipe
  capability check separate from resource sufficiency — deferred to Objects & material culture
  or Capability & progression, whichever formalizes crafting content first.
- **RESOLVED — investigated and explicitly folded in, not given a separate family.** Threshold
  semantics live in Capacity (LIMIT-04), cross-linked from Cost/Resource/Transformation rather
  than duplicated.
- **RESOLVED — investigated and moved out entirely, rationale sharpened by follow-up.**
  Deterministic randomness is not a Rule Catalog concern; the controlling reason is that valid
  outcome space and causal legitimacy are already governed by Causality (CAUSE-01/CAUSE-03), not
  that the repository happens to use a deterministic seed — reproducibility/replay stays with
  Evaluation/implementation regardless of either.
- **New, confirmed MISSING (added by follow-up).** LIMIT-03's soft-cap alternative (graduated
  degradation past a preferred bound, rather than hard rejection) — the revised rule permits it;
  nothing implements it yet.
- **New, deferred by follow-up.** RES-04's divisible/interruptible transfer semantics — the
  revised rule permits a resource to declare non-atomic transfer semantics; whether any future
  domain actually wants that is not decided.
- **Confirmed CTR-S04's own question, from the movement angle.** MOV-04's cost-per-step finding
  is Batch 03's COST-03 confirmed concretely at the movement level — no new open question, a
  reconfirmation.

**From Batch 04 (Space/Environment/Movement, drafted 2026-09-21, revised same day per
follow-up):**

- **Confirmed MISSING — the most load-bearing gap this batch found; ownership framing corrected
  by follow-up.** LOC-02/LOC-06's route/portal/directional-connection mechanism — treated as a
  Space/Movement capability gap (LOC-07); Magic/supernatural (portals) and Groups/organizations
  & institutions (trade routes) are plausible future *producers/consumers*, not owners.
- **Confirmed MISSING, the movement-side counterpart.** MOV-05's non-physical movement
  mechanism — deferred to Magic/supernatural as a plausible producer, not owner.
- **Confirmed inert, not resolved.** `service_availability` (ENV-01/ENV-05) — whether to wire
  it to a real consumer or leave it forward-declared is not decided.
- **Confirmed live, resolving a flagged uncertainty.** `price_modifiers` is causally live
  (`market.py`); `weather`/`active_modifiers` beyond `"MIASMA"` remain unexhaustively verified —
  flagged for Economy/resources or Ecology/population.
- **RESOLVED by Batch 05, for bodily harm specifically.** ENV-03 deliberately left open which
  domain owns exposure's downstream consequences; Batch 05's BODY-07 answers this for *bodily*
  harm (Life/Body owns it, given subject-specific protection) — other exposure-consequence
  types (non-bodily) remain open.
- **New, added by follow-up.** LOC-07 (producing a topology change ≠ owning topology state) is
  a new rule, not merely a wording fix — added because the original framing risked implying
  whichever domain fills the LOC-02/LOC-06 gap would also own it.

**From Batch 05 (Life/Body/Survival/Ecology, drafted 2026-09-21, normalized 2026-09-22):**

- **Confirmed MISSING — the most load-bearing gap in Body/Condition.** BODY-05's HP recovery
  mechanism does not exist at all, declared or otherwise — entities can perceive a "healing"
  need with no fulfillment path anywhere.
- **Confirmed MISSING — the most load-bearing gap in this whole batch.** ECOL-03's aggregate
  population change is currently statistical, not driven by real individual births/deaths —
  the individual → aggregate half of this family's own causal loop doesn't yet exist.
- **Confirmed inert.** `last_meal_tick`/`last_sleep_tick` (SURV-04) — written on every meal/
  sleep action, read nowhere; contrasted against the live `well_rested_until`.
- **PARTIAL, honestly uncertain rather than resolved either way.** BODY-03's HP-loss/injury
  coupling (confirmed at one production site, independence unverified) and LB-S15's
  predator-prey pressure (individual role classification exists; no aggregate formula
  confirmed).

**From Batch 06 (Perception/Knowledge/Information/Agency, drafted 2026-09-22):**

- **Confirmed CONFLICTING (not merely MISSING) — the most load-bearing gap in this whole
  batch, and one of the most important findings the Rule Catalog has produced to date.**
  Decision-making actively reads raw/omniscient world state directly for at least two live
  paths (`ResourceOpportunityProvider.get_opportunities()`, `HarvestScorer.score()`), bypassing
  `PerceptionGate` and `entity.cognition.knowledge_model` entirely — this is active behavior
  that violates the target semantics, not an absent feature. Does not invalidate the Rule
  Catalog: it means the Catalog successfully exposed a real architecture mismatch. Whether
  these call sites should be re-scoped through perception/knowledge is a real implementation
  question, not decided here.
- **Confirmed INERT/OFF.** `entity.cognition.knowledge_model` (`KnowledgeFact`/`UnknownFact`)
  has zero decision-making consumers outside `src/cognition/` itself — decisions that do depend
  on belief-like state read the separate `strategic.leads`/`BeliefEntry` system instead.
- **Confirmed INERT/OFF (dead in production).** `PerceptionUpdatePhase` (the salience/attention/
  budget layer) has zero call sites in `AuthoritativeApplyPipeline.refine()`; only the upstream
  binary `PerceptionGate` is confirmed live.
- **Confirmed INERT/OFF (wired-but-inactive).** `MemoryUpdatePhase` (causal/spatial/temporal
  memory) is gated behind `ENABLE_MEMORY_UPDATE`, which defaults OFF.
- **Confirmed MISSING.** No in-simulation motive-inference mechanism exists —
  `CognitionPatternMiner` is offline developer/observability tooling, not a world mechanism.
- **Reconfirmed MISSING, from Batch 02's own REACH-05.** No intermediary-link-failure modeling
  (a messenger delayed, blocked, or lying) and no content-level information distortion — only
  certainty/trust vary through transmission, never claim content itself.

## Review index

For external review, send the review export first — it's the compact, generated summary; send
canonical files only when the reviewer flags something needing deeper inspection. A review export
is never itself authoritative: canonical files → review export → external review → feedback →
canonical files updated → review export regenerated. Never patch only the export.

Every export must include a **Rule Inventory** (one row per Rule: ID, short name, one-line
semantic purpose, status — grouped by family; no preconditions, ownership analysis, repository
evidence, or rationale) and a **Scenario Inventory** (one row per scenario, including
counter-scenarios: ID, short name, trajectory, rule families challenged, deferred domain
dependencies, current result), followed by a **Scenario Coverage Summary** (what kinds of world
behavior the scenario set stress-tests, grouped by family — coverage shape, not scenario count)
and a **Deferred Scenario Semantics** section (later-domain questions intentionally left
unresolved, distinguished from actual gaps). These let a reviewer see what semantic territory and
what kinds of world behavior a batch covers without opening the canonical files — full traces and
rationale stay canonical.

| Batch / Area | Canonical source files | Scenario set | Review export | Status |
|---|---|---|---|---|
| Foundational Batch 01 | `foundations/identity.md`, `foundations/state-ownership.md`, `foundations/causality.md` | `scenarios/foundational-batch-01.md` (FND-S01–S21) | [review-exports/foundational-batch-01-review.md](review-exports/foundational-batch-01-review.md) | Ready for high-level external review |
| Foundational Batch 02 | `foundations/time.md`, `foundations/authority.md`, `foundations/reach.md` | `scenarios/foundational-batch-02.md` (TAR-S01–S17) | [review-exports/foundational-batch-02-review.md](review-exports/foundational-batch-02-review.md) | PASS — ready to freeze |
| Foundational Batch 03 | `foundations/capability.md`, `foundations/cost.md`, `foundations/capacity.md`, `foundations/resource.md`, `foundations/transformation.md` | `scenarios/foundational-batch-03.md` (CTR-S01–S20) | [review-exports/foundational-batch-03-review.md](review-exports/foundational-batch-03-review.md) | PASS — ready to freeze |
| History / Provenance completion | `foundations/history-provenance.md` (HP-01–06) | `scenarios/history-provenance-completion.md` (HP-S01–S02) | [review-exports/history-provenance-completion-review.md](review-exports/history-provenance-completion-review.md) | Ready for high-level external review |
| Batch 04 (Space/Environment/Movement) | `space-environment/location-topology.md`, `space-environment/environment.md`, `space-environment/movement-navigation.md` | `scenarios/space-environment-batch-04.md` (SPC-S01–S15) | [review-exports/space-environment-batch-04-review.md](review-exports/space-environment-batch-04-review.md) | PASS — ready to freeze |
| Batch 05 (Life/Body/Survival/Ecology) | `life-body/lifecycle.md`, `life-body/body-condition.md`, `life-body/survival-needs.md`, `life-body/ecology-population.md` | `scenarios/life-body-batch-05.md` (LB-S01–S16) | [review-exports/life-body-batch-05-review.md](review-exports/life-body-batch-05-review.md) | Ready for high-level external review, normalized 2026-09-22 |
| Batch 06 (Perception/Knowledge/Information/Agency) | `knowledge-agency/perception.md`, `knowledge-agency/knowledge-information.md`, `knowledge-agency/agency-decision.md` | `scenarios/knowledge-agency-batch-06.md` (KA-S01–S20) | [review-exports/knowledge-agency-batch-06-review.md](review-exports/knowledge-agency-batch-06-review.md) | PASS — ready to freeze |

## Links to current review batches

- Batch 01 rule files: `foundations/identity.md`, `foundations/state-ownership.md`,
  `foundations/causality.md`
- Batch 01 scenario file: `scenarios/foundational-batch-01.md`
- Batch 01 review export: `review-exports/foundational-batch-01-review.md`
- Batch 01 report (local, gitignored): `tmp/world-rule-foundational-batch-01-report.md`
- Batch 02 rule files: `foundations/time.md`, `foundations/authority.md`, `foundations/reach.md`
- Batch 02 scenario file: `scenarios/foundational-batch-02.md`
- Batch 02 review export: `review-exports/foundational-batch-02-review.md`
- Batch 02 report (local, gitignored): `tmp/world-rule-foundational-batch-02-report.md`
- Batch 03 rule files: `foundations/capability.md`, `foundations/cost.md`,
  `foundations/capacity.md`, `foundations/resource.md`, `foundations/transformation.md`
- Batch 03 scenario file: `scenarios/foundational-batch-03.md`
- Batch 03 review export: `review-exports/foundational-batch-03-review.md`
- Batch 03 report (local, gitignored): `tmp/world-rule-foundational-batch-03-report.md`
- History/Provenance rule file: `foundations/history-provenance.md`
- History/Provenance scenario file: `scenarios/history-provenance-completion.md`
- History/Provenance review export: `review-exports/history-provenance-completion-review.md`
- History/Provenance report (local, gitignored): `tmp/history-provenance-completion-report.md`
- Batch 04 rule files: `space-environment/location-topology.md`,
  `space-environment/environment.md`, `space-environment/movement-navigation.md`
- Batch 04 scenario file: `scenarios/space-environment-batch-04.md`
- Batch 04 review export: `review-exports/space-environment-batch-04-review.md`
- Batch 04 report (local, gitignored): `tmp/space-environment-batch-04-report.md`
- Batch 05 rule files: `life-body/lifecycle.md`, `life-body/body-condition.md`,
  `life-body/survival-needs.md`, `life-body/ecology-population.md`
- Batch 05 scenario file: `scenarios/life-body-batch-05.md`
- Batch 05 review export: `review-exports/life-body-batch-05-review.md`
- Batch 05 report (local, gitignored): `tmp/life-body-batch-05-report.md`
- Batch 06 rule files: `knowledge-agency/perception.md`,
  `knowledge-agency/knowledge-information.md`, `knowledge-agency/agency-decision.md`
- Batch 06 scenario file: `scenarios/knowledge-agency-batch-06.md`
- Batch 06 review export: `review-exports/knowledge-agency-batch-06-review.md`
- Batch 06 report (local, gitignored): `tmp/knowledge-agency-batch-06-report.md`
