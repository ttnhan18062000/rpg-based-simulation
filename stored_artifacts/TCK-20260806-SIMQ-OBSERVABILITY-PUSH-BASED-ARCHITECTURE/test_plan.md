---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260806-SIMQ-OBSERVABILITY-PUSH-BASED-ARCHITECTURE
artifact_type: test_plan
tags: [observability, engine, simulation-quality, performance]
---

# test_plan.md — TCK-20260806-SIMQ-OBSERVABILITY-PUSH-BASED-ARCHITECTURE

## Scope of change

This ticket is investigation-and-recommendation only, per its own explicit Out of Scope — no
`src/` code is touched. The recommendation is a phased migration; Phase 1's implementation is a
separate follow-up ticket with its own test plan (shadow-mode comparison against the existing
diff-based extractor, plus reuse of `test_simq_isolation_overhead.py`'s harness for performance
validation).

## Verification steps for this ticket

1. `python3 tools/validate_frontmatter.py <file> --content-type doc|ticket` for every doc/ticket
   file touched.
2. Confirm via `git status`/`git diff` that no `src/`/`tests/` file appears in this ticket's
   changeset.
3. Confirm the Phase 1 follow-up ticket exists, is correctly scoped to the 3 already-push-ready
   domains (COMBAT/ECONOMY/FACTION), and explicitly excludes PROGRESSION's quest detection
   (Phase 2, separate ticket, not yet filed — needs new instrumentation work scoped first).

## Out of scope for this ticket's testing

- Any `pytest` run — no production code changed.
- Actually running a shadow-mode comparison — that's Phase 1's own Test phase.
