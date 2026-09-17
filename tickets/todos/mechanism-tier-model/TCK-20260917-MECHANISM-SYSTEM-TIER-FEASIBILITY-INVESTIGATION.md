---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260917-MECHANISM-SYSTEM-TIER-FEASIBILITY-INVESTIGATION
phase: open
date: 2026-09-17
tags: [architecture, documentation, investigation]
---

# TCK-20260917-MECHANISM-SYSTEM-TIER-FEASIBILITY-INVESTIGATION

## Title
Derive candidate systems by hand against the real graph and report whether the tier design survives
contact — investigate, build nothing

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
The tier model proposes that a **system** declares a root and derives its membership from that
root's transitive ancestors in `depends_on`. That design has never been run against the real graph.

Before writing any schema, find out whether it produces sensible sets — and answer the three
questions the implementation tickets cannot be drafted without.

**Build nothing.** No schema, no field, no generator. Derive by hand or with a throwaway script and
report.

## Scope

### 1. Derive 4 candidate systems against the current 89-node graph

Suggested, adjust if the graph says otherwise: **combat**, **progression**, **economy/trade**,
**social**. For each, pick a plausible root, compute its transitive ancestors, and record the
resulting membership set.

### 2. Judge each set against one question

**Would a person who knows this simulation call that set "the combat system"?**

Report what is missing that should be there, and what is included that should not be. That judgement
is the finding — a set that needs heavy explanation is evidence the derivation does not work, not
evidence the reader is wrong.

### 3. Answer the three blocking questions

- **How many systems are there?** Nobody has counted. The design assumes a tractable number; if the
  89 nodes decompose into 30 systems the tier adds noise rather than structure.
- **Does one root per system suffice?** `combat` plausibly works from `combat_resolution`.
  `economy` may need several. If multiple roots are needed, the schema changes.
- **Do axes attach to mechanisms or to systems?** Fewer declarations versus more precision. Decide
  against a real case — take one axis from the existing proposals (knowledge-belief,
  social-relationship, legacy-memory, temporal) and try both.

### 4. Report how much the result depends on untrusted edges

`TCK-20260917-MECHANISM-IDENTITY-RULES-AND-CHANGE-TAXONOMY` removed `tactical_decision →
combat_resolution` as a caller rather than a prerequisite. ~64 edges predate that rule.

For each derived set, state how many of its edges have been validated against the stated definition
and how many have not. **If membership rests mostly on unaudited edges, that is the headline finding**
and `TCK-20260917-MECHANISM-DEPENDS-ON-EDGE-SEMANTICS-AUDIT` becomes a hard precondition rather than
a related ticket.

## Out of Scope
- **Any schema, field, or generator.** Investigation only.
- **Running the edge audit.** Report dependence on it; don't do it here.
- **Declaring real systems in the registry.** Candidates are for judgement, not for committing.
- **Axes beyond the single test case** in §3.

## Acceptance Criteria
1. Four candidate systems derived, with membership sets recorded in full.
2. Each set judged explicitly — what is missing, what is wrongly included — not merely listed.
3. All three blocking questions answered with data.
4. Edge-trust reported per set as a count, not an impression.
5. A stated recommendation: **proceed, proceed-with-changes, or do not build this tier.** "Do not
   build" is a legitimate and useful outcome — the epic exists to find that out cheaply if true.

## Related Tickets
- `TCK-20260917-EPIC-MECHANISM-TIER-MODEL` — parent
- `TCK-20260917-MECHANISM-DEPENDS-ON-EDGE-SEMANTICS-AUDIT` — the precondition this measures
- `TCK-20260917-MECHANISM-THREE-TIER-AXIS-SYSTEM-MECHANISM` — the design being tested

## Related Docs
- `docs/plans/mechanism_tier_model_initiative.md` §3, §7
- `docs/brainstorm/2026-09-02-core-rpg-knowledge-belief-axis-proposal.md` and siblings — real axes
  for the §3 test

## Related Stored Artifacts
None yet.

## Related Code Areas
- `registries/mechanisms.yaml`
- `tools/mechanism_registry/generate_mechanism_priority_view.py` — the ancestors-of traversal exists
  here already; call it rather than reimplementing

## Assumptions / Open Questions
1. Derived membership reflects **declared** edges, not real traffic. Combat is reached mostly via
   movement's opportunity-attack path while the declared decision route fires 0–2 times per 1000
   ticks. The `combat` candidate is the sharpest test of whether that gap makes derivation useless
   or merely imperfect.
2. Roots may not be unique — two plausible roots could derive overlapping-but-different sets for the
   same intuitive system. If so, say which and how much they differ.
3. This investigation can conclude the tier is not worth building. That outcome saves the three
   implementation tickets and is a success, not a failure.

## Implementation Notes
The pattern that has worked repeatedly in this arc: measure the cheapest discriminating thing before
committing to a design. This is that step for the tier model.

## Test Summary
To be completed during implementation.

## Files Changed
To be completed during implementation.

## Completion Summary
Open.
