---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260917-EPIC-MECHANISM-TIER-MODEL
phase: open
date: 2026-09-17
tags: [architecture, documentation, schema]
---

# TCK-20260917-EPIC-MECHANISM-TIER-MODEL

## Title
Build the tiers above `mechanism` — investigate first, then `system`, then `axis`, then the
proposal-decomposition check

## Status
EPIC_SCOPED

## Tier
epic

## Type
feature

## Priority
P2

## Request Summary
`docs/plans/mechanism_tier_model_initiative.md` defines the model: **axis → system → mechanism**,
with systems derived from a declared root and axes declared as overlapping tags. The identity rule
and change taxonomy are done (`TCK-20260917-MECHANISM-IDENTITY-RULES-AND-CHANGE-TAXONOMY`, 4 splits
/ 5 keeps across 9 tested cases).

What remains is building the tiers. **This epic deliberately starts with an investigation rather
than a schema**, because three things the design depends on are currently unknown, and drafting
implementation tickets against unknowns would invent structure rather than discover it.

## Scope

### Child 1 — investigation (drafted, first)
`TCK-20260917-MECHANISM-SYSTEM-TIER-FEASIBILITY-INVESTIGATION`. Derive candidate systems by hand
from the current graph, check whether membership is sensible, and answer the three open questions
with real data.

### Children 2–4 — scoped *from* child 1's findings, not now
Named here so the shape is visible, deliberately not drafted:

- **`system` tier** — schema, root declaration, derived membership, validation. Its shape depends on
  whether one root per system suffices.
- **`axis` tier** — declared overlapping tags, plus the no-mechanical-backing statement. Its shape
  depends on whether axes attach to mechanisms or to systems.
- **Proposal decomposition** — a proposal declares its registry diff; the landed change is checked
  against it. This is the payoff and depends on both tiers existing.

Expanding this epic later is expected. An epic that pretends to know its own children before the
investigation runs is the thing this project keeps finding in other people's documents.

## Out of Scope
- **Drafting children 2–4 now.** See above.
- **A fourth tier.** Three is what the evidence supports.
- **Rolled-up status badges**, at any tier. Counts only — see the plan doc §5.
- **Retrofitting** every mechanism into a system or axis. Unassigned is a visible gap, not an error.

## Acceptance Criteria
1. Child 1 answers all three open questions with measured data, not reasoning.
2. Children 2–4 are drafted from those findings before any schema work begins.
3. No tier introduces a summary status anywhere.
4. The edge-semantics precondition (below) is either satisfied or explicitly accepted as a stated
   limitation before the `system` tier ships.

## Related Tickets
- `TCK-20260917-MECHANISM-IDENTITY-RULES-AND-CHANGE-TAXONOMY` — **done**; supplies the identity rule
- `TCK-20260917-MECHANISM-THREE-TIER-AXIS-SYSTEM-MECHANISM` — the existing design ticket; becomes
  this epic's design reference, and children 2–4 supersede it as implementation units
- **`TCK-20260917-MECHANISM-DEPENDS-ON-EDGE-SEMANTICS-AUDIT` — precondition, see Assumptions #1**
- `TCK-20260917-MECHANISM-IMPLEMENTED-BY-COVERAGE-EXTENSION` — independent; does not block

## Related Docs
- `docs/plans/mechanism_tier_model_initiative.md` — the model and its known limitations
- `docs/plans/mechanism_identity_and_change_taxonomy.md` — the identity rule and the seven change kinds

## Related Stored Artifacts
- `stored_artifacts/TCK-20260917-MECHANISM-IDENTITY-RULES-AND-CHANGE-TAXONOMY/` — the 9-case test

## Related Code Areas
- `registries/mechanisms.yaml`
- `tools/mechanism_registry/generate_mechanism_priority_view.py` — already implements the
  ancestors-of traversal a system needs; reuse it rather than reimplementing

## Assumptions / Open Questions

1. **The edge-semantics audit is a real precondition, currently filed as an unrelated P2.**
   Systems derive membership from `depends_on`. `TCK-20260917-MECHANISM-IDENTITY-RULES-AND-CHANGE-TAXONOMY`
   **removed one edge** — `tactical_decision → combat_resolution` — on the grounds that it was a
   caller, not a functional prerequisite. Roughly 64 others were authored before that rule existed.
   Deriving a system today produces membership from unvalidated edges. Either the audit runs first,
   or child 1 reports how much its results depend on edges it could not trust.

2. **The three unknowns child 1 must answer:**
   - How many systems are there? Nobody has counted; the design assumes a tractable number.
   - Does one root per system suffice? `combat` works from `combat_resolution`. `economy` may need
     several, which changes the schema.
   - Do axes attach to mechanisms or to systems? Attaching to systems is fewer declarations;
     attaching to mechanisms is more precise.

3. **Derived membership reflects declared edges, not real traffic.** Measured 2026-09-17: combat is
   reached overwhelmingly via movement's opportunity-attack path (181–2177 calls/1000 ticks) while
   the declared decision route fires 0–2. A derived `combat` system would describe declared structure
   while the dominant real path runs elsewhere. Known, recorded, not yet resolved.

4. **The base is thin** — 26 of 89 bound to code, 14 with any verdict, 2 runtime-verified.
   Abstraction above a thin layer tends to obscure the thinness rather than expose it, which is why
   counts-never-badges is an acceptance criterion rather than a preference.

## Implementation Notes
Epic tier — scope only. Children carry their own plans.

## Test Summary
Per child.

## Files Changed
None (epic).

## Completion Summary
Open.
