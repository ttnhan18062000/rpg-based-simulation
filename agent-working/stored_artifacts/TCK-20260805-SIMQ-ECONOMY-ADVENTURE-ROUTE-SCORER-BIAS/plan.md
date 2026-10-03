---
status: active
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260805-SIMQ-ECONOMY-ADVENTURE-ROUTE-SCORER-BIAS
artifact_type: plan
tags: [simulation-quality, economy, adventure]
---

# plan.md — TCK-20260805-SIMQ-ECONOMY-ADVENTURE-ROUTE-SCORER-BIAS

## Ordered Steps

1. **No scoring/generation code change.** Investigation concluded craft/buy's 0-selection pattern
   is `AdventureRouteScorer`/`AdventureRouteGenerator` working correctly — entities genuinely lack
   the gold/materials craft/buy opportunities require (a downstream consequence of the same
   zero-harvest root cause `TCK-20260713-SIMQ-ECONOMY-INTENT-GENERATION-GAP`'s Factors 1/3 already
   track), not a scorer bug. Per the ticket's own AC3, this is a valid closing outcome — files
   changed below are documentation only.
   - Files: none in `src/`.

2. **Update `docs/simulation_quality/current_state.md`'s Finding 2** — replace the "Factor 2:
   ... AdventureRouteScorer never selects craft_upgrade/buy_upgrade" framing with the precise root
   cause: blocker_penalty=2.0 correctly fires because entities lack gold/materials, itself a
   consequence of the zero-harvest gap. Mark Factor 2 as **investigated, confirmed correct
   behavior, not a scoring bug** rather than "remaining open work."
   - Files: `docs/simulation_quality/current_state.md`.

3. **Update `docs/audits/D20_simq_quality_status_review.md`'s Item B2** — same correction, in the
   Candidate Work Items table and Finding 2 text.
   - Files: `docs/audits/D20_simq_quality_status_review.md`.

4. **Fill this ticket's Completion Summary** with the finding and close.

## Scope Guards

- Do NOT modify `src/domains/adventure/scoring.py` or `generator.py` — the investigation
  concluded no fix is warranted there.
- Do NOT touch Factor 1 (`ENABLE_ADVENTURE_ROUTING` default) — separate policy decision, not this
  ticket's scope.
- Do NOT re-open the zero-harvest root cause itself (already tracked by Factors 1/3 in the prior
  ticket chain) — this ticket only explains *why* craft/buy specifically inherit that gap.

## Dependency Map

Steps 2 and 3 are independent of each other (different files); both depend on step 1's conclusion
(no code change). Step 4 depends on 2 and 3 being written first (Completion Summary references
them).

## Acceptance Criteria Map

- AC1 (concrete evidence for miscalibration-vs-correct verdict) → investigation.md's "Current
  Behavior" + "Risks and Open Questions" sections (done).
- AC2 (fix justified by named scenario, if any) → N/A, no fix implemented (verdict: correct
  behavior).
- AC3 (finding documented in current_state.md + D20 doc, Factor 2 status corrected) → Steps 2-3.
- AC4 (regression tests pass, no scoring change) → Test phase, `test_grade_regression.py`.
- AC5 (spot-check example if a scoring change lands) → N/A, no scoring change.

No unresolved questions requiring human review — the investigation reached a clear, evidenced
conclusion. (The tangential open question about `blocker_penalty`'s flat, non-gradient shape,
noted in investigation.md, is explicitly scoped out, not unresolved *for this ticket*.)
