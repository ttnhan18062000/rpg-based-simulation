---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260920-MECHANISM-ENTITY-LAYER-UNBOUND-CLAIMS-RESOLUTION
phase: done
date: 2026-09-20
tags: [architecture, schema, simulation-quality]
---

# Plan — TCK-20260920-MECHANISM-ENTITY-LAYER-UNBOUND-CLAIMS-RESOLUTION

## Approach

1. Enumerate the 24 entity-layer mechanisms with `state in (done, partial, gated)` and
   `implemented_by` absent, directly from `registries/mechanisms.yaml` (confirmed peer's own
   count exactly: 24).
2. For each, check the mechanism's own existing `verified` note first (citation-trail check,
   per the `trauma` misattribution lesson) before any fresh code search.
3. Where a real, direct caller-confirmed implementation exists: bind it, using method-level syntax
   when the file/class also implements another mechanism via different methods.
4. Where no real implementation exists: correct `state` with a new `verified` block explaining the
   evidence.
5. Where genuinely ambiguous: leave unbound, document the search and why it didn't resolve.
6. Delegate the ~15 mechanisms with no pre-existing citation to two read-only investigation forks
   (progression/social cluster, cognition cluster), each instructed explicitly on the
   misattribution risk and told to report structured findings, not to edit the registry directly.
   Apply all resulting bindings myself after independent verification.
7. Resolve the 2 remaining `unaudited_depends_on_edges` (`motivation_doctrine` pair) against the
   registry's own already-stated `depends_on` semantics (functional dependency, not execution
   order) — code is deleted, so resolve via the deletion's own documented behavior instead of a
   fresh code trace.
8. Investigate the `commitment_betrayal` merge candidate rather than executing it — check whether
   the original "no distinct implementation" premise still holds under a broader search.
9. Decide the method-level binding question: extend `registry.py`'s validator to support
   `path::Class::method`, since the pattern recurred across 2 more mechanisms this batch (crossing
   the "not worth building for 2" bar the prior ticket declined at).
10. Regenerate every consumer artifact (atlas, capabilities, wiring map, HTML page, markdown views)
    and re-run the full validation/check suite after every substantive edit.

## Scope guards
- No registry schema changes, no system-membership reassignment, no re-verification of
  already-verified entries, no code fixes — report findings that look like code defects rather
  than fixing them.
- Trust but verify: every fork-produced finding independently re-checked against source before
  being kept, regardless of how confident the fork's own report reads.
