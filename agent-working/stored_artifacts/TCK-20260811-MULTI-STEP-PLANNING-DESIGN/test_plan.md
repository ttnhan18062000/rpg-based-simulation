---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260811-MULTI-STEP-PLANNING-DESIGN
artifact_type: test_plan
tags: [cognition, strategy, progression]
---

# Test Plan — TCK-20260811-MULTI-STEP-PLANNING-DESIGN

This ticket's deliverable is a design document plus a go/no-go decision, not executable code (Scope
/ Out of Scope are explicit: "No production code merged under this ticket"). There is nothing for
`pytest` to run against. "Testing" this deliverable means verifying the design doc's own factual
and architectural claims against the real, current source and doc state — the same standard this
investigation.md applied to itself — plus confirming the ticket's four ACs are each literally
satisfied by the doc's content.

## Regression Surface

Not applicable in the traditional sense (no code changes). The tests below are cited as the
**factual ground-truth surface** the design doc's claims must not contradict — Verify should confirm
these still pass unmodified (proving this ticket touched no code), and Plan/Implement should confirm
the design doc's description of current behavior matches what these tests actually assert:

- `tests/unit/strategic/test_interruption_resistance.py` — current single-slot retention/switching
  behavior (STRAT-185/186/187 basis).
- `tests/unit/strategic/test_score_normalization.py` — the normalized lock-bypass dual-condition
  gate, including
  `test_locked_system_a_current_interrupted_by_high_urgency_system_b_candidate` and
  `test_locked_system_a_current_still_blocks_low_urgency_system_b_candidate` (the two parity-ledger
  `test_path` entries for STRAT-186/187).
- `tests/unit/strategic/test_evaluate_project_switch_state_threading_guard.py` — STRAT-236
  threat-resolved early-release wiring.
- `tests/unit/campaigns/test_progression_plan.py`,
  `tests/unit/campaigns/test_progression_plan_exporter.py`,
  `tests/unit/campaigns/test_progression_plan_importer.py`,
  `tests/unit/campaigns/test_plan_revision.py`,
  `tests/integration/campaigns/test_progression_planner_three_episode.py` — current
  `ProgressionPlan`/`goal_queue`/`PlanRevisionService` behavior (episode-cadence, head-goal-only
  consultation).
- `tests/unit/ai/goals/test_adventure_goal_scorer.py`,
  `tests/unit/ai/goals/test_social_contract_goal_scorer.py`,
  `tests/unit/ai/goals/test_region_stabilization_goal_scorer.py` — current tier-5 `GoalRegistry`
  competition shape (13 `GoalKind`s, all going through the same arbiter).

## New Tests Required

None — there is no new code and this ticket's ACs do not ask for any. If the design doc includes
illustrative pseudocode/dataclass sketches, they remain prose/illustration and do not require test
coverage under this ticket; a follow-up implementation ticket (if the go/no-go decision is "accept")
would own its own test plan for the real model.

## Documentation Validation Checks (in place of pytest)

Each check below maps to what would normally be a "new test" but validates the *design doc's own
claims*, not runtime behavior. All must be performed before the design doc ships (Verify phase for
this ticket):

1. **AC1 — durable typed model, reviewed against Strategic/Tactical Rule.**
   - Verify the design doc proposes a concrete typed structure (fields/types named, not just prose)
     for "a short sequence of future intentions."
   - Verify the doc explicitly quotes or paraphrases CLAUDE.md's Strategic/Tactical Rule and states,
     with reasoning, why its proposed model sits on the strategy side of that boundary rather than
     being "more tactical goal scoring" (per this investigation's Mechanics/Engine Constraints
     section — the rule's plain reading classifies tier-5 `GoalRegistry` scoring as tactical).
   - Fail condition: a proposal that adds a new `GoalKind`/`GoalScorer` as its primary mechanism
     without addressing why that isn't "stacking more tactical goal scoring."

2. **AC2 — interaction with `current_project_id`/`current_objective_id` and the lock-bypass
   arbiter.**
   - Every claim the design doc makes about `evaluate_strategic_intent()` or
     `evaluate_project_switch()`'s current behavior must be checked line-for-line against
     `src/systems/strategic_systems/intelligence.py` as it exists at design-doc-write time (post
     both `ADVENTURE-GOAL-SCORER` and `THREAT-RESOLVED-ARBITER-RELOCATION` — already true as of this
     investigation, but Verify should re-diff in case intervening tickets touched the file).
   - Specifically confirm the doc does not describe the pre-epic "kind==danger and score>80 /
     kind==detour" allowlist as current behavior (superseded twice this session — see this
     investigation's Anti-Drift Hazards).
   - Confirm the doc explicitly states whether a "next queued intention" would go through
     `evaluate_project_switch()` unmodified, bypass it, or extend it — silence on this point is a
     failure of AC2, not an acceptable ambiguity.

3. **AC3 — relationship to `ProgressionPlan.goal_queue` / "multi-goal lookahead deferred."**
   - Confirm the design doc quotes or accurately paraphrases
     `docs/simulation/domains/progression_planner_contract.md:123`'s exact boundary language
     ("Only `goal_queue[0]`... Multi-goal lookahead is deferred (post-E61)").
   - Confirm the doc states one of supersede / extend / coexist explicitly, with rationale — not
     merely "this is related to `ProgressionPlan`."
   - If "coexist" is chosen, confirm the doc directly engages the ticket's own flagged
     third-overlapping-concept risk (Assumptions line 2) rather than ignoring it.

4. **AC4 — closure record.**
   - Confirm the design doc (or the ticket's own Completion Summary, whichever the doc's structure
     places it in) ends with either (a) an accepted follow-up implementation ticket ID, or (b) an
     explicit reject/defer statement with rationale. A design doc that trails off without a stated
     decision fails this AC regardless of how thorough the analysis is.

5. **Citation accuracy pass.** Every `file:line` reference, parity-ledger ID, and doc-path citation
   the design doc makes must independently resolve — i.e., re-open each cited file/line and confirm
   the content matches what's claimed. This mirrors the standard this investigation.md itself was
   held to. Any drifted citation (file moved, line renumbered by an intervening ticket) must be
   corrected before the doc ships, not left stale.

6. **Template conformance.** Confirm the new doc follows the structural pattern established by
   `docs/architecture/2026-08-11-adventure-as-cognition-strategy-subcomponent-design.md` (frontmatter
   → `## Context` → Non-Goals-style scoping statement → `## Design` → `## Future Extension
   Patterns` (if applicable) → diagrams), since that is the only existing precedent in
   `docs/architecture/` for this exact kind of proposal-plus-decision doc.

## Scoped Pytest Commands

No pytest run is required to validate the design doc's content (it is not code). The one pytest
obligation for this ticket is a **negative check** — proving no source files were touched — run
during Verify:

```
git diff --stat tickets/inprogress/TCK-20260811-MULTI-STEP-PLANNING-DESIGN.md HEAD -- src/
# must be empty
```

If Plan/Implement's investigation-validation pass (checks 1-6 above) requires re-confirming any
cited test's current behavior, the narrowest correct scope is:

```
pytest tests/unit/strategic/ tests/unit/campaigns/ tests/unit/ai/goals/ -m "not slow"
```

Never `pytest tests/` — this ticket touches no runtime code, so a full-suite run would be pure
overhead with no signal this ticket could plausibly have broken.

## Anti-Drift Test Guards

- **Guard against silent code changes riding along with this ticket.** `git diff --stat -- src/`
  must be empty at Verify time — this is a design-scoping ticket; any `src/` diff at all is
  automatically out of scope and must be rejected regardless of how small or "obviously correct" it
  looks.
- **Guard against the design doc quietly deciding the ProgressionPlan question by default** (e.g.
  by only ever describing the new model and never mentioning `goal_queue` again after the intro) —
  covered by check 3 above.
- **Guard against re-litigating already-closed sibling tickets.** The design doc may reference
  `TCK-20260811-ADVENTURE-GOAL-SCORER` / `TCK-20260811-THREAT-RESOLVED-ARBITER-RELOCATION` /
  `TCK-20260811-SOCIAL-CONTRACT-GOAL-SCORER` / `TCK-20260811-REGION-STABILIZATION-GOAL-SCORER` as
  established, stable context, but must not propose reopening or re-designing them — they are DONE,
  committed, and out of this ticket's scope. Any Implement-phase edit to those tickets' own files
  (beyond `docs/architecture/2026-08-11-...design.md`'s Future Extension Patterns post-landing note,
  which is explicitly anticipated by that doc's own precedent) is a drift signal.
