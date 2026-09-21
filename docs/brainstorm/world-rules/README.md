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

## Design-area index

Only the areas with actual rule files exist below. Do not scaffold empty files for areas not yet
reached — see `simulation-rule-world-law-design-preparation.md` §3 for the full world-rule design
order.

| Area | Status | File |
|---|---|---|
| Identity | Foundational Batch 01 drafted | [foundations/identity.md](foundations/identity.md) |
| State Ownership | Foundational Batch 01 drafted | [foundations/state-ownership.md](foundations/state-ownership.md) |
| Causality | Foundational Batch 01 drafted | [foundations/causality.md](foundations/causality.md) |
| History / Provenance | Scope defined 2026-09-21; rules not yet drafted (future batch) | [foundations/history-provenance.md](foundations/history-provenance.md) |

## Rule Catalog progress

- **Foundational Batch 01** (Identity, State Ownership, Causality): drafted, adversarially
  expanded, its open questions dispositioned (deferred / cross-domain-link / implementation-gap /
  resolved-by-naming-a-family — see below), ready for high-level external review. See
  `tmp/world-rule-foundational-batch-01-report.md` (local, not part of this catalog) for the full
  disposition report.
- **History / Provenance** introduced 2026-09-21 as an explicit foundational/cross-cutting Rule
  family (scope only — see [foundations/history-provenance.md](foundations/history-provenance.md)).
  This is not a new batch and implies no change to the world-rule design order; its rules are not
  drafted and drafting them is a future batch's job.
- No other batch has been started, and no rules have been drafted for History / Provenance yet.
  Do not begin the next foundational batch, any per-domain batch (Space & environment, Movement,
  Life/Body, etc.), or draft History / Provenance's own rules, until Batch 01 is explicitly
  reviewed and accepted.

## Scenario Bank index

| Batch | File | Scenario IDs |
|---|---|---|
| Foundational Batch 01 | [scenarios/foundational-batch-01.md](scenarios/foundational-batch-01.md) | FND-S01 – FND-S21 |

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
| History / Provenance | `foundations/history-provenance.md` (scope only) | none yet | none yet | Scope defined 2026-09-21; not a reviewable batch yet |

## Links to current review batch

- Rule files: `foundations/identity.md`, `foundations/state-ownership.md`,
  `foundations/causality.md`
- Scope-only file (not part of Batch 01's own rule set): `foundations/history-provenance.md`
- Scenario file: `scenarios/foundational-batch-01.md`
- Review export: `review-exports/foundational-batch-01-review.md`
- Report (local, gitignored): `tmp/world-rule-foundational-batch-01-report.md`
