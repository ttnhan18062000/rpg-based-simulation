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
| Time | Foundational Batch 02 drafted | [foundations/time.md](foundations/time.md) |
| Authority | Foundational Batch 02 drafted | [foundations/authority.md](foundations/authority.md) |
| Reach | Foundational Batch 02 drafted | [foundations/reach.md](foundations/reach.md) |

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
- **Foundational Batch 02** (Time, Authority, Reach): drafted, ready for high-level external
  review. See `tmp/world-rule-foundational-batch-02-report.md` (local, not part of this catalog)
  for the full disposition report.
- No other batch has been started, and no rules have been drafted for History / Provenance yet.
  Do not begin Batch 03, any per-domain batch (Space & environment, Movement, Life/Body, etc.),
  the History / Provenance completion pass, or re-open Batch 01/02, until both drafted batches
  are explicitly reviewed and accepted.

## Scenario Bank index

| Batch | File | Scenario IDs |
|---|---|---|
| Foundational Batch 01 | [scenarios/foundational-batch-01.md](scenarios/foundational-batch-01.md) | FND-S01 – FND-S21 |
| Foundational Batch 02 | [scenarios/foundational-batch-02.md](scenarios/foundational-batch-02.md) | TAR-S01 – TAR-S13 |

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

**From Foundational Batch 02 (2026-09-21):**

- **Not conclusively verified — a judgment call, not this session's to make.** Whether a
  currently-incapacitated role-holder's unaffected authority (TAR-S07) is intentional or an
  unexamined gap. Flagged for owner review, not resolved by design.
- **Explicitly deferred per the roadmap's guardrail.** Whether political authority (Politics/
  authority & war) inherits AUTH-01–06 unchanged or refines them.
- **Explicitly deferred per the same guardrail.** Whether spatial reach (Space/environment) or
  magical reach (Magic/supernatural) inherit REACH-01–06 unchanged or refine them.
- **DEFER to Magic/supernatural.** Whether aging needs an explicit reversal-exception mechanism
  (TIME-05).
- **DEFER to Perception/knowledge/information.** REACH-03's asymmetry finding is read-level
  evidence only; needs its own scenario trace before that domain builds on it.

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
| Foundational Batch 02 | `foundations/time.md`, `foundations/authority.md`, `foundations/reach.md` | `scenarios/foundational-batch-02.md` (TAR-S01–S13) | [review-exports/foundational-batch-02-review.md](review-exports/foundational-batch-02-review.md) | Ready for high-level external review |
| History / Provenance | `foundations/history-provenance.md` (scope only) | none yet | none yet | Scope defined 2026-09-21; not a reviewable batch yet |

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
- Scope-only file (not part of any batch's own rule set): `foundations/history-provenance.md`
