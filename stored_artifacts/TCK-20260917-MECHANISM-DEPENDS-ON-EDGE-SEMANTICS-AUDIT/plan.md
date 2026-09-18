---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260917-MECHANISM-DEPENDS-ON-EDGE-SEMANTICS-AUDIT
artifact_type: plan
tags: [architecture, schema]
---

# Plan — TCK-20260917-MECHANISM-DEPENDS-ON-EDGE-SEMANTICS-AUDIT

## Steps
1. Enumerate all 70 remaining declared `depends_on` edges (done — see investigation.md; corrects the
   ticket's own "~64" estimate to 70).
2. Dispatch a real per-edge code audit against the registry's own stated `depends_on` definition,
   grouped by evidence availability (both-sides-bound → one-side-bound → neither-side-bound), so the
   richest-evidence edges are checked with the most rigor and the weakest-evidence edges get an
   honest UNCLASSIFIABLE verdict rather than a guessed one.
3. For every edge classified REMOVE, apply the same evidence standard as the
   `combat_resolution`/`tactical_decision` correction: cite the real code showing the dependent
   produces a meaningful result without the dependency's state already existing, then remove the edge
   from `registries/mechanisms.yaml`.
4. Re-run `python3 tools/mechanism_registry/generate_mechanism_priority_view.py` (or the registry's
   own validation script) before and after the edit set to measure the actual priority-ranking shift,
   per Acceptance Criteria #3 — report the shift, do not assume it is negligible.
5. Re-validate `registries/mechanisms.yaml` against its own schema/acyclicity check after any edge
   removals.
6. Write the full per-edge verdict table to
   `stored_artifacts/TCK-20260917-MECHANISM-DEPENDS-ON-EDGE-SEMANTICS-AUDIT/edge_audit_results.md` on
   close, and summarize counts (kept/removed/unclassifiable) plus the priority-shift measurement in
   this ticket's own Completion Summary.

## Scope guards
- No new `depends_on` edges are added under this ticket (that is
  `TCK-20260916-MECHANISM-DEPENDENCY-GRAPH-POPULATION`'s completed scope, not reopened here).
- The `combat_resolution` edges are not relitigated — already resolved.
- The `depends_on` definition itself is not changed — only applied.
- An edge is never forced to KEEP or REMOVE when the real code for one side cannot be located after a
  genuine search — UNCLASSIFIABLE is a legitimate, recorded outcome, not a failure to complete the
  audit.

## Acceptance-criteria map
| AC | Satisfied by |
|---|---|
| 1. Every one of the ~64 (actually 70) remaining edges checked, not sampled | Step 2 — full 70-edge enumeration, no sampling |
| 2. Every removed edge recorded with combat_resolution-grade evidence | Step 3 |
| 3. Priority-ranking shift measured and reported, not assumed negligible | Step 4 |
