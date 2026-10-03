---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260917-MECHANISM-SYSTEM-TIER-FEASIBILITY-INVESTIGATION
artifact_type: plan
tags: [architecture, documentation, investigation]
---

# Plan — TCK-20260917-MECHANISM-SYSTEM-TIER-FEASIBILITY-INVESTIGATION

Investigation only, per this ticket's own explicit scope. No schema, field, or generator built.

## Steps

1. Reuse `tools.mechanism_registry.registry.transitive_dependencies_of()` (the existing
   ancestors-of traversal) rather than reimplementing it, per this ticket's own instruction.
2. Derive 4 candidate systems (`combat`, `progression`, `economy/trade`, `social`) against the real
   93-mechanism graph, trying more than one root per domain where a single obvious root isn't
   apparent.
3. Judge each derived set against the stated test: would someone who knows this simulation call
   that set the named system, without heavy explanation?
4. Answer the three blocking questions (system count, single-root sufficiency, axis attachment
   point) with the derived data, not reasoning alone — test the axis question against a real axis
   proposal document.
5. Count internal edges per derived set and how many are audited under the identity-rules ticket's
   own `depends_on` definition versus unaudited (predate that rule).
6. State a real recommendation (proceed / proceed-with-changes / do not build), not softened
   regardless of which way the evidence points.
7. Report findings to peer for review against the live design conversation before closing the
   ticket, per explicit request — do not move the ticket to done in this same pass.

## Non-goals

- No system schema, `depends_on`-derivation generator, or registry field — this is a feasibility
  check, not implementation.
- No running of `TCK-20260917-MECHANISM-DEPENDS-ON-EDGE-SEMANTICS-AUDIT` — only reporting how much
  each derived set's own trustworthiness depends on it.
- No committing candidate systems to the registry — candidates are for judgment only.
- No axis testing beyond the single test case (temporal) needed to answer the attachment question.
