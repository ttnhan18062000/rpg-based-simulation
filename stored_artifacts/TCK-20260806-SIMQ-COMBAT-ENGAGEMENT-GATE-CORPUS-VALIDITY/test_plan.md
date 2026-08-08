---
status: active
layer: simulation
authority: P0
audience: agent
ticket_id: TCK-20260806-SIMQ-COMBAT-ENGAGEMENT-GATE-CORPUS-VALIDITY
artifact_type: test_plan
tags: [simulation-quality, combat, progression, feature-flags, observability]
---

# Test Plan: TCK-20260806-SIMQ-COMBAT-ENGAGEMENT-GATE-CORPUS-VALIDITY

## Scope of change

This ticket is investigation-and-documentation only per its corrected findings — no
`src/` code is touched (the recommendation is two follow-up tickets, not a direct fix; see
investigation.md's Recommendation). No new/changed production logic means no new unit tests are
required for this ticket itself.

## Verification steps

1. **Frontmatter validity** — `python3 tools/validate_frontmatter.py <file> --content-type doc`
   for every doc file touched (`D20_simq_quality_status_review.md` correction) and
   `--content-type ticket` for the two new follow-up ticket files.
2. **No regression risk** — confirm via `git status`/`git diff` that no file under `src/` or
   `tests/` appears in this ticket's changeset; if one does, that is scope creep beyond what this
   ticket's Implement step should do and must be reverted or moved to a follow-up ticket.
3. **Follow-up tickets are correctly filed and gated** — both new tickets exist under
   `tickets/todos/simq-pillar-lifecycle-depth/`, have valid frontmatter, and
   `TCK-20260806-SIMQ-PROGRESSION-CAPABILITY-LIFECYCLE`'s blocking-dependency note is updated to
   reference them instead of this ticket.
4. **SEQUENCE.md accuracy** — re-read after edits to confirm the ordering/dependency notes still
   match reality (this ticket done, two new investigations queued, PROGRESSION still blocked,
   FACTION still independent).

## Out of scope for this ticket's testing

- Actually running the two follow-up investigations (event_extractor misclassification check,
  1000-2000t quest-pacing probe) — that is their own Test phase once implemented.
- Any `pytest` run — no production code changed.
