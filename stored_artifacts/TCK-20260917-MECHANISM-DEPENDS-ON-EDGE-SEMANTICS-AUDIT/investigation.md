---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260917-MECHANISM-DEPENDS-ON-EDGE-SEMANTICS-AUDIT
artifact_type: investigation
tags: [architecture, schema]
---

# Investigation — TCK-20260917-MECHANISM-DEPENDS-ON-EDGE-SEMANTICS-AUDIT

## Scope of this investigation
Enumerate every declared `depends_on` edge in `registries/mechanisms.yaml` not already checked by
`TCK-20260917-MECHANISM-IDENTITY-RULES-AND-CHANGE-TAXONOMY`, and classify each against the
registry's own stated definition (functional prerequisite — "cannot produce a meaningful result
without the dependency's own output/state already existing" — independent of which mechanism's code
calls the other).

## Real edge count, corrected from the ticket's own estimate
The ticket's Request Summary estimated "~64 others." A direct enumeration of
`registries/mechanisms.yaml` (93 mechanisms, post-split) found **71 total declared `depends_on`
edges**, of which 2 were already resolved by the identity-rules ticket
(`combat_resolution→tactical_decision`, removed; `combat_resolution→movement`, kept), leaving
**70 edges** in this audit's own scope — not 64. The estimate undercounted because it predated the
4-way mechanism split (`TCK-20260917-MECHANISM-IDENTITY-RULES-AND-CHANGE-TAXONOMY`) that grew the
registry from 89 to 93 mechanisms and correspondingly grew the edge count.

## Method
1. Enumerated all 70 remaining edges via a direct read of `registries/mechanisms.yaml`.
2. Grouped by how much `implemented_by` metadata already exists on each side, since that determines
   where a real-code check can start (not whether one is possible — many `state: done` mechanisms
   lack a backfilled `implemented_by` even though real code exists; that is
   `TCK-20260917-MECHANISM-IMPLEMENTED-BY-COVERAGE-EXTENSION`'s own known gap, not evidence of no
   code):
   - **2 edges**: both dependent and dependency have `implemented_by` — richest evidence available.
   - **21 edges**: exactly one side has `implemented_by` — the other side's real code must be located
     by search before a verdict is possible.
   - **47 edges**: neither side has `implemented_by` yet — real code must be located by search on
     both sides; most of these mechanisms are `state: done`, so code is expected to exist even though
     the registry hasn't recorded where.
3. For each edge, applied the registry's own test directly against real code (not against names):
   does the dependent mechanism's own code produce a meaningful result without the dependency's own
   state/output already existing? Call direction does not decide the verdict — only whether the
   dependent's own output would be meaningless/wrong without the dependency having already run.
4. Recorded a verdict per edge: **KEEP** (real prerequisite, confirmed against code), **REMOVE** (a
   caller relationship mislabeled as a dependency, with the same evidence rigor as the
   `combat_resolution`/`tactical_decision` correction), or **UNCLASSIFIABLE** (real code could not be
   located for one or both sides after a genuine search attempt — recorded with what was searched,
   per this ticket's own instruction not to force a verdict).

## Full per-edge findings
See `stored_artifacts/TCK-20260917-MECHANISM-DEPENDS-ON-EDGE-SEMANTICS-AUDIT/edge_audit_results.md`
(migrated from this ticket's own staging artifacts on close) for the complete 70-line verdict table
with evidence citations. Summary counts and any registry corrections are recorded in this ticket's
own Implementation Notes and Completion Summary.
