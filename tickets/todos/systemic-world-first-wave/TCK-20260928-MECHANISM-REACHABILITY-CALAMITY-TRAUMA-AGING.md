---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260928-MECHANISM-REACHABILITY-CALAMITY-TRAUMA-AGING
phase: open
date: 2026-09-28
tags: [simulation-quality, world, root-cause]
---

# TCK-20260928-MECHANISM-REACHABILITY-CALAMITY-TRAUMA-AGING

## Title
Bounded reachability assessment for three mechanisms — `calamity_intensity`, `regional_trauma`, and
`aging_death`/`succession` — answering whether each is a condition, a defect, or a mislabel

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
Three mechanisms carry registry `verified` blocks that corpus runs contradict or cannot confirm.
This ticket answers **why**, on four levels each, and ends each with **one exit claim**. It is a
bounded assessment, not an open-ended sweep and not a fix.

The four levels, per mechanism:
1. trigger reachability;
2. feasible run horizon;
3. actual state effects;
4. observer evidence (recorded, never required).

Implements Card J of `docs/plans/systemic_world/ticket_planner_handoff.md`
(branch `systemic-world-roadmap-proposal` @ `43db4a7fc`, PR #249, unmerged).

## Scope
- **J1 — `calamity_intensity`.** **Adopt** `TCK-20260914-CALAMITY-INTENSITY-PRODUCER-NEVER-FIRES`,
  do not duplicate it. That ticket records `calamity_intensity` never leaving `0.0` in any region
  across a real 5000-tick run, producer and propagator both apparently inert.
- **J2 — `regional_trauma`.** **Adopt** `TCK-20260914-LAIR-REGION-TRAUMA-NEVER-ACCUMULATES`, do not
  duplicate it. It already frames the problem correctly as **a region recording zero combat deaths**,
  not a wrong threshold — a trigger-reachability question that may be legitimately conditional.
- **J3 — `aging_death` / `succession`.** No ticket exists; **assess and classify only**. Fixing the
  known natural-aging defect is out of scope (see Related Tickets). Because that fix may land first,
  **every J3 finding must name the engine commit it was observed on.** The level-2 succession claim
  is limited to default settings and the current corpus.
- For each mechanism, state which of the four levels actually fails, and map the adopted ticket's
  existing scope onto those levels — explicitly naming where it does **not** fit.
- Correct any mechanism label through the registry process, with its evidence recorded in
  `registries/mechanisms.yaml`, not only in planning docs.

## Out of Scope
- **Any fix.** This ticket assesses and classifies. A confirmed defect is routed as separate work.
- A fourth mechanism. Exactly three, per Card J.
- `TCK-20260914-CALAMITY-RANDOM-CHANCE-UNUSED-CONSTANT` and
  `TCK-20260914-REGIONAL-INFLUENCE-SHIFT-NEVER-FIRES`. Both are in the same dormant-mechanism
  family and plausibly share J2's root symptom (regions recording zero combat deaths), but Card J
  fixes the count at three. **If the shared-root-cause hypothesis is confirmed, say so in the exit
  claim and stop** — do not absorb them.
- The `pressure-propagation-economy` epic folder, whose first ticket
  (`TCK-20260822-CALAMITY-AFTERMATH-SIGNAL`) touches the same calamity area. Excluded **whole**, per
  the project's epic all-or-nothing rule; do not cherry-pick from it.
- **Writing J1's `calamity_intensity` label into `registries/mechanisms.yaml`.** That entry's `state`
  reconciliation is already owned by `TCK-20260923-MECHANISM-IMPLEMENTED-BY-RESIDUE-RESOLUTION`
  (open, `tickets/todos/`), whose Request Summary names `calamity_intensity` as its item 1 and whose
  Related Code Areas include the same registry file. J still assesses J1's reachability at all four
  levels and still states its exit claim in the ticket, but **a `registry label corrected` exit
  claim for J1 is recorded as a recommendation to that ticket, not applied to the registry here** —
  two tickets must not write the same mechanism entry. J2 and J3 are unaffected and may write their
  own labels normally. Surfaced by `tools/open_ticket_overlap.py` (top hit, score 40.0,
  `has_code_area_match` on `registries/mechanisms.yaml`).

## Acceptance Criteria
1. Each of the three mechanisms has an answer at all four levels, or a level explicitly recorded as
   `BLOCKED_WITH_REASON`. A harness limitation is never reported as "fine".
2. Each mechanism ends with exactly **one exit claim**, classifying it as a **condition**, a
   **defect**, or a **mislabel**.
3. For J1 and J2, the adopted ticket's existing scope is mapped onto the four levels, including a
   written statement of where it does not fit.
4. Level 2 (feasible horizon) is answered with **minimum evidence, not an open-ended long run** —
   the method is stated and justified. Note the arithmetic: default lifespan is 70 fantasy years,
   roughly 20M ticks (`src/core/state.py:165`), against corpus runs of 1k–5k ticks.
5. Every J3 finding names the engine commit it was observed on.
6. Any label correction is written through the registry process into `registries/mechanisms.yaml`
   with its evidence, not only into planning docs.
7. Findings are routed back to the systemic-world roadmap track (`world-rule-catalog-design`), which
   owns integration.

## Related Tickets
- `TCK-20260914-CALAMITY-INTENSITY-PRODUCER-NEVER-FIRES` — **adopted as J1.**
- `TCK-20260914-LAIR-REGION-TRAUMA-NEVER-ACCUMULATES` — **adopted as J2.**
- `TCK-20260928-NATURAL-AGING-DEATH-DUAL-WRITER-RACE` — the natural-aging fix. **Merged 2026-09-29
  as `5d4e4a237` (PR #254); no longer in flight.** `src/engine/apply.py:109` now reads
  `active=(new_hp > 0 and (life.active or new_age < life.max_age_ticks))`, making
  `LifecycleSystem.resolve_lifecycle` the sole declared authority for old-age deactivation. J3
  assesses against this landed state; it does not fix. This is why AC5 exists.
- `TCK-20260923-MECHANISM-IMPLEMENTED-BY-RESIDUE-RESOLUTION` — open, owns the `calamity_intensity`
  entry's `state` reconciliation in `registries/mechanisms.yaml`. See Out of Scope: J1 recommends,
  that ticket writes.
- `TCK-20260914-CALAMITY-RANDOM-CHANCE-UNUSED-CONSTANT`,
  `TCK-20260914-REGIONAL-INFLUENCE-SHIFT-NEVER-FIRES` — same family, deliberately out of scope.

## Related Docs
- `docs/plans/systemic_world/ticket_planner_handoff.md` — Card J (@ `43db4a7fc`).
- `docs/plans/systemic_world/first_wave_plan.md` §2 Epic J, §3.
- `docs/mechanics/05_world_evolution.md` — regional trauma, ecology, calamities.

## Related Stored Artifacts
- `docs/plans/systemic_world/evidence/2026-09-27-candidate-trajectory-search-findings.md` (on the
  unmerged branch above).

## Related Code Areas
- `src/core/state.py:165` — default lifespan constant behind J3's horizon arithmetic.
- `registries/mechanisms.yaml` — the `verified` blocks for all four mechanism entries; the first two
  were checked 2026-09-27 and are `contradicted` by corpus runs.

## Assumptions / Open Questions
- **Q1.** For J1 and J2, which of the four levels actually fails — and is the answer a condition, a
  defect, or a mislabel?
- **Q2.** How does each adopted ticket's existing scope map onto the four levels, and where does it
  not fit?
- **Q3.** What is the minimum evidence that answers level 2 without an open-ended long run?
- **Q4.** For J3, can levels 2 and 3 be recorded from existing evidence plus the reproduction,
  **without** fixing the defect?
- **Shared-root-cause hypothesis, flagged not assumed.** J2's adopted ticket and the out-of-scope
  `TCK-20260914-REGIONAL-INFLUENCE-SHIFT-NEVER-FIRES` both reduce to regions recording zero combat
  deaths. If the assessment confirms one shared cause, that is a finding worth stating plainly — it
  would mean several backlog tickets are one defect, not several.
- **Contract-level risk.** Re-labelling a mechanism changes what other plans assume is live. Record
  every label change in the registry with evidence.
- None of the three mechanisms is SCP-mapped; **no SCP change is required.**

## Implementation Notes
_To be completed during implementation._

## Test Summary
_To be completed during implementation._

## Files Changed
_To be completed during implementation._

## Completion Summary
_To be completed during implementation._
