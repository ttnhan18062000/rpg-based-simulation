---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260916-MECHANISM-IMPLEMENTED-BY-BINDING
artifact_type: plan
tags: [architecture, schema, simulation-quality]
---

# Plan — TCK-20260916-MECHANISM-IMPLEMENTED-BY-BINDING

## Steps

1. Add `implemented_by` to the schema documentation (`mechanisms.yaml`'s own header comment).
2. Add invariant 7 to `mechanism_registry.py::validate()`: a list of strings, each an existing
   repo-relative path.
3. Rewrite `mechanism_registry_completeness_check.py` to read `implemented_by` structurally
   instead of regex-searching prose; report bound/excluded/unbound as three distinct, honest,
   non-overlapping buckets.
4. Populate `implemented_by` for the 11 completeness-pass mechanisms (promoting their existing
   inline evidence comments into the structured field).
5. Dispatch a sub-investigation to classify the checker's own first-run "unmapped" targets;
   independently re-verify its most consequential findings before acting on them (never trust a
   subagent's claim without checking).
6. Act on verified findings: fix `causal_spatial_memory`'s state-drift bug, register 2 new orphan
   mechanisms and 1 new partial mechanism, add 5 more `implemented_by` bindings to existing
   mechanisms.
7. Propagate the `causal_spatial_memory` state fix to its two other consumers (atlas badge,
   wiring-map node) — the same discipline used for `motivation_doctrine` earlier in this epic.
8. Regenerate all four derived views (`mechanism_verification_view.md`,
   `mechanism_priority_view.md`, `mechanism_registry_view.md`, `mechanism_registry.html`) for the
   final 89-mechanism state.
9. Fix every test regression the new registrations/state changes surface (atlas mapping count,
   transitive-dependents count, artifact-convergence control assertion, wiring-map drift, HTML row
   count) — never force a gate green by editing its logic, only by fixing the real substance.
10. Run the scoped suite with `graphify-out/` genuinely moved aside and restored.
11. Write staging artifacts, finalize both this ticket and the now-unblocked
    `TCK-20260916-MECHANISM-COMPLETE-REGISTRY-VIEW` together (their work landed in the same pass).
12. Commit, push, report to peer — including filing a follow-up for the ~30-item candidate
    `implemented_by` backfill batch the sub-investigation produced but this ticket deliberately did
    not act on.

## Scope guard

Per peer review: do not populate `implemented_by` for all 89 mechanisms now. Only bindings that
were independently verified in this pass are added. The field grows organically from here.

## Acceptance-criteria map

| AC | Satisfied by |
|---|---|
| 1. `implemented_by` recognized, validated | `mechanism_registry.py::validate()` invariant 7 + its own test coverage |
| 2. 11 completeness-pass mechanisms have `implemented_by` | promoted from existing evidence comments |
| 3. Checker reports two distinct, never-conflated numbers | `build_report()`'s `bound`/`excluded`/`unbound` split, printed separately |
| 4. Full scoped suite passes, including `graphify-out/` absent | re-run and confirmed, 165/165 |
