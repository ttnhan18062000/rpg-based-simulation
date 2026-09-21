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

## Rule Catalog progress

- **Foundational Batch 01** (Identity, State Ownership, Causality): drafted, pending external
  review. See `tmp/world-rule-foundational-batch-01-report.md` (local, not part of this catalog)
  for the full disposition report.
- No other batch has been started. Do not begin the next foundational batch, or any per-domain
  batch (Space & environment, Movement, Life/Body, etc.), until Batch 01 is explicitly reviewed
  and accepted.

## Scenario Bank index

| Batch | File | Scenario IDs |
|---|---|---|
| Foundational Batch 01 | [scenarios/foundational-batch-01.md](scenarios/foundational-batch-01.md) | FND-S01 – FND-S12 |

## Unresolved cross-domain questions

Recorded in full in each rule file's own "Cross-domain links" / "Open questions carried forward"
sections. Not yet promoted to `cross-domain/` — per the adopted structure, that directory is
created only once a link becomes a substantial shared contract, not for every link recorded in a
rule file. Currently tracked, not yet promoted:

- `impaired capability → economic loss` (OWN-05, CAUSE-02): which domain designs this link.
- No capability/precondition detector exists (CAUSE-04): affects every future domain that gates
  an action on a precondition.
- Reputation scalar vs. reputation labels narrative relationship (OWN-03, FND-S05): flagged for
  the Social relations batch.
- Settlement lifecycle (camp → settlement → ruin) is a shared gap surfaced by both Identity
  (ID-03) and Causality (CAUSE-02) independently: flagged for a future Places batch.
- Organization/clan founding and splitting have no mechanism at all (ID-04, ID-06): flagged for a
  future Organizations/Politics batch.
- History/Provenance compression-tier design (CAUSE-06) is deferred to a future foundational
  family not yet added to the design order.

## Review index

For external review, send the review export first — it's the compact, generated summary; send
canonical files only when the reviewer flags something needing deeper inspection. A review export
is never itself authoritative: canonical files → review export → external review → feedback →
canonical files updated → review export regenerated. Never patch only the export.

Every export must include a **Rule Inventory** (one row per Rule: ID, short name, one-line
semantic purpose, status — grouped by family; no preconditions, ownership analysis, repository
evidence, or rationale) and a **Scenario Inventory** (one row per scenario, including
counter-scenarios: ID, short name, what it probes, current result). These let a reviewer see what
semantic territory and what kinds of world behavior a batch covers without opening the canonical
files — full traces and rationale stay canonical.

| Batch / Area | Canonical source files | Scenario set | Review export | Status |
|---|---|---|---|---|
| Foundational Batch 01 | `foundations/identity.md`, `foundations/state-ownership.md`, `foundations/causality.md` | `scenarios/foundational-batch-01.md` (FND-S01–S12) | [review-exports/foundational-batch-01-review.md](review-exports/foundational-batch-01-review.md) | Drafted, pending external review |

## Links to current review batch

- Rule files: `foundations/identity.md`, `foundations/state-ownership.md`,
  `foundations/causality.md`
- Scenario file: `scenarios/foundational-batch-01.md`
- Review export: `review-exports/foundational-batch-01-review.md`
- Report (local, gitignored): `tmp/world-rule-foundational-batch-01-report.md`
