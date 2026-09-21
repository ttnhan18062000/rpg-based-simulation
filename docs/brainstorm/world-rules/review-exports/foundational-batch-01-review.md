---
status: active
layer: architecture
authority: P2
audience: agent
tags: [architecture, world, content]
---

# Review Export: Foundational Batch 01 (Identity, State Ownership, Causality)

**This file is a generated, non-authoritative review view.** It exists so an external reviewer
can assess the batch without opening every canonical file. It is never edited directly as the
fix for a review finding — feedback goes back into the canonical files below, and this export is
regenerated from them. See `world-rules/README.md`'s review index for the current status of
every batch.

## Batch scope

Three foundational law families — Identity, State Ownership, Causality — the load-bearing layer
every later per-domain batch (Space, Life/Body, Economy, etc.) will build on. Not a per-domain
batch; deliberately domain-agnostic.

## Canonical files included

- `foundations/identity.md` (ID-01–09)
- `foundations/state-ownership.md` (OWN-01–06)
- `foundations/causality.md` (CAUSE-01–07)
- `scenarios/foundational-batch-01.md` (FND-S01–S12)

## Design intent

Establish, before any per-domain rule is written, what "the same thing across change" means
(Identity), who is allowed to hold durable truth about a concept and how that truth relates to
proposals, derived views, and history (State Ownership), and what makes one event a real cause of
another rather than a coincidence or fabricated narrative link (Causality). These three answer
questions every later domain would otherwise have to re-derive independently and inconsistently.

## Rules/law families introduced or materially changed

All three families are newly introduced (first draft, no prior version exists). 20 external
starter candidates were reviewed; 2 rules were added locally (ID-08, ID-09 — see summary below).
No rule from a prior batch was changed, since this is the first batch.

## Major scenario findings

Of 12 scenarios (including all 5 required counter-scenarios): 5 covered outright, 4 partially
covered (real design gaps, not contradictions), 1 blocked (no mechanism exists at all —
FND-S03, settlement lifecycle), 2 revealed an undocumented seam rather than a contradiction
(FND-S05, FND-S06's organization/clan-founding sub-probe). **Zero scenarios revealed a genuine
semantic contradiction between two accepted rules.**

The single most load-bearing gap found: **no general-purpose capability/precondition detector
exists anywhere in the repository** (CAUSE-04) — every future domain that gates an action on a
precondition inherits this gap until it's addressed.

## Important cross-domain links

- `impaired capability → economic loss → relationship reaction` (OWN-05, FND-S07): two links in
  a plausible cross-domain chain are unbuilt; unclear which future domain should own the first one.
- Settlement lifecycle (camp → settlement → ruin): surfaced independently by Identity (ID-03) and
  Causality (CAUSE-02) — the same gap seen from two angles, flagged once for a future Places batch.
- Organization/clan founding and splitting: no mechanism exists at all (ID-04, ID-06) — flagged
  for a future Organizations/Politics batch.
- Reputation scalar vs. reputation labels: two legitimately separate owned fields with an
  undocumented narrative relationship (OWN-03, FND-S05) — flagged for a future Social relations
  batch.
- Capability/precondition detector (CAUSE-04): flagged for Agency/decision.
- Compression-tier design for history/chronicle (CAUSE-06): deferred to a future History/
  Provenance family not yet in the design order at all.

## Open semantic questions

1. What, in general (not per-domain), makes a transformation identity-ending? (ID-03) — `human →
   vampire` and `camp → settlement → ruin` both deliberately left open, deferred to Magic and
   Places respectively.
2. How do split/merge/founding resolve for organizations and settlements? (ID-06)
3. Is a corpse's own identity (as a future Objects-domain subject) related to the deceased
   entity's identity, or fully independent? (ID-05, deferred to Objects & material culture)
4. Where does "impaired capability → economic loss" get designed? (OWN-05)
5. CAUSE-06's compression-tier constraint is stated; its actual mechanism design is deferred to a
   family not yet named in the design order.

## Known tensions / contradictions

None found. This batch's own headline result is that the existing architecture (typed
Update→Patch pipeline, single-owner durable state) already satisfies nearly every proposed
semantic rule by construction — the gaps found are unbuilt downstream consequences, not
architectural contradictions with the proposed rules.

## Expected-depth implications

None. This batch operates below the per-domain depth-priority map
(`simulation-rule-world-law-design-preparation.md` §4) — it doesn't rate any of the 19 domains,
and nothing found here argues for revising an existing depth/priority rating.

## Repository evidence that materially changed the design

One external candidate's own worked example was factually wrong and was corrected rather than
kept: OWN-03 cited `entity.combat.readiness` as a derived-state example; direct inspection showed
it is a directly owned, authoritative field, written through the normal Combat-domain patch path.
The example list was replaced (scarcity ratio, threat classification, a reputation-derived
discount, economic opportunity) — the rule itself needed no change, only its illustration.

## Decisions that need owner/external-reviewer attention

- Whether the two open transformation cases (`human → vampire`, `camp → settlement → ruin`)
  should stay deferred to their future domains, or whether ID-03 should state a general-purpose
  identity-ending test now instead of per-domain.
- Whether CAUSE-04's precondition-detector gap should be prioritized ahead of its "natural" place
  in the world-rule design order, given how many future domains depend on it.
- Whether a History/Provenance foundational family should be added to the design order now
  (to give CAUSE-05/CAUSE-06 a home) or left implicit until a domain batch needs it.

## Starter-candidate disposition summary

20 of 20 external candidates accepted (0 rejected, 0 split, 0 merged, 0 moved out of family). 3
refined beyond a plain accept: ID-03 (explicit default/exception split added), OWN-03 (factual
correction to its example list), CAUSE-06 (constraint kept here, detailed mechanism design
partial-moved to a future family). 2 rules added locally: ID-08 (identity applies uniformly
across scale), ID-09 (a name/epithet is not identity). One additional candidate (a same-tick
domain read/write ordering rule) was drafted and deliberately rejected as an implementation
concern, not a world-semantic one — recorded in `state-ownership.md` so it isn't re-proposed
without context.

Full per-rule disposition, evidence, and rationale: see the canonical files above, or
`tmp/world-rule-foundational-batch-01-report.md` (local review report, not part of this catalog).
