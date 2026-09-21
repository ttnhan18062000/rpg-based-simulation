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
| History / Provenance | Scope defined 2026-09-21; rules not yet drafted — per `roadmap.md`, drafting moved into Milestone A as a completion pass after Batch 03, not left for Final Integration | [foundations/history-provenance.md](foundations/history-provenance.md) |
| Time | Foundational Batch 02 — PASS, frozen | [foundations/time.md](foundations/time.md) |
| Authority | Foundational Batch 02 — PASS, frozen | [foundations/authority.md](foundations/authority.md) |
| Reach | Foundational Batch 02 — PASS, frozen | [foundations/reach.md](foundations/reach.md) |
| Capability | Foundational Batch 03 drafted | [foundations/capability.md](foundations/capability.md) |
| Cost | Foundational Batch 03 drafted | [foundations/cost.md](foundations/cost.md) |
| Capacity / Limits | Foundational Batch 03 drafted | [foundations/capacity.md](foundations/capacity.md) |
| Resource / Conservation Semantics | Foundational Batch 03 drafted | [foundations/resource.md](foundations/resource.md) |
| Transformation | Foundational Batch 03 drafted | [foundations/transformation.md](foundations/transformation.md) |

## Rule Catalog progress

- **Foundational Batch 01** (Identity, State Ownership, Causality): drafted, adversarially
  expanded, its open questions dispositioned (deferred / cross-domain-link / implementation-gap /
  resolved-by-naming-a-family — see below), ready for high-level external review. See
  `tmp/world-rule-foundational-batch-01-report.md` (local, not part of this catalog) for the full
  disposition report.
- **History / Provenance** introduced 2026-09-21 as an explicit foundational/cross-cutting Rule
  family (scope only — see [foundations/history-provenance.md](foundations/history-provenance.md)).
  Not a new batch on its own; per `roadmap.md`, its own rules are drafted as a completion pass
  inside Milestone A, after Batch 03 — not yet reached.
- **Foundational Batch 02** (Time, Authority, Reach): drafted, revised once per follow-up
  instruction (implementation-detail removed from Time, Authority's actor-only framing broadened,
  a real internal inconsistency in Reach corrected, 4 scenario probes added), **PASS — ready to
  freeze**. See `tmp/world-rule-foundational-batch-02-report.md` (local, not part of this
  catalog) for the full disposition report.
- **Foundational Batch 03** (Capability, Cost, Capacity/Limits, Resource/Conservation Semantics,
  Transformation): drafted, ready for high-level external review. Threshold semantics were
  investigated and folded into Capacity (LIMIT-04) rather than given their own family;
  deterministic randomness was investigated and moved out of the Catalog entirely (see
  `review-exports/foundational-batch-03-review.md`'s explicit call-outs). See
  `tmp/world-rule-foundational-batch-03-report.md` (local, not part of this catalog) for the
  full disposition report.
- No per-domain batch has been started, and no rules have been drafted for History / Provenance
  yet. Do not begin any per-domain Milestone B batch (Space & environment, Movement, Life/Body,
  etc.) or the History / Provenance completion pass until all three foundational batches are
  explicitly reviewed and accepted — per Batch 03's own instruction, History / Provenance is the
  next planned step once that review happens, not before.

## Scenario Bank index

| Batch | File | Scenario IDs |
|---|---|---|
| Foundational Batch 01 | [scenarios/foundational-batch-01.md](scenarios/foundational-batch-01.md) | FND-S01 – FND-S21 |
| Foundational Batch 02 | [scenarios/foundational-batch-02.md](scenarios/foundational-batch-02.md) | TAR-S01 – TAR-S17 |
| Foundational Batch 03 | [scenarios/foundational-batch-03.md](scenarios/foundational-batch-03.md) | CTR-S01 – CTR-S16 |

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
- **RESOLVED by naming a family.** History/Provenance compression-tier design and
  significance-fading design (CAUSE-05, CAUSE-06, FND-S20/S21) are no longer an unnamed deferred
  item — see [foundations/history-provenance.md](foundations/history-provenance.md) (scope only,
  rules not yet drafted).
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

**From Foundational Batch 03 (2026-09-21):**

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
- **RESOLVED — investigated and moved out entirely.** Deterministic randomness is not a Rule
  Catalog concern; the world-semantic residue is already covered by Causality (CAUSE-01/
  CAUSE-03), and reproducibility/replay stays with Evaluation/implementation.

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
| Foundational Batch 03 | `foundations/capability.md`, `foundations/cost.md`, `foundations/capacity.md`, `foundations/resource.md`, `foundations/transformation.md` | `scenarios/foundational-batch-03.md` (CTR-S01–S16) | [review-exports/foundational-batch-03-review.md](review-exports/foundational-batch-03-review.md) | Ready for high-level external review |
| History / Provenance | `foundations/history-provenance.md` (scope only) | none yet | none yet | Scope defined 2026-09-21; not a reviewable batch yet — next planned step once Batch 03 is reviewed |

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
- Scope-only file (not part of any batch's own rule set): `foundations/history-provenance.md`
