---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260824-ROLLOUT-FLAG-DECISIONS
artifact_type: plan
tags: [feature-flags]
---

# Plan — TCK-20260824-ROLLOUT-FLAG-DECISIONS

## Steps

1. **Flip `ENABLE_BELIEF_ASSIMILATION` and `ENABLE_SOCIAL_COOPERATION` to `FeatureMode.ON`** in
   `FeatureFlagManager.__init__` (`src/domains/optimization/feature_flags.py`), each with a real,
   cited inline comment matching the style of the existing 5 `ON`-default flags (not a bare
   change) -- citing this ticket and the two corpus profiles as evidence.
2. **Add both to `tests/unit/config/test_phase10_feature_flags.py::_DELIBERATE_ON_DEFAULT_FLAGS`**
   allowlist, per `TCK-20260807-FEATURE-FLAG-OFF-SHADOW-TEST-STALE`'s own established mechanism --
   confirm the allowlist test still correctly rejects a non-allowlisted `ON` default afterward.
3. **Add `docs/guidelines/intentional_divergences.md` entries** for both flips (real behavior
   change from documented-OFF-by-default expectation).
4. **Formalize `ENABLE_GUILD_QUEST_GENERATION`'s existing keep-OFF rationale** into
   `intentional_divergences.md` too (no code change -- the rationale already exists in
   `feature_flags.py`'s own comment, this step makes it discoverable in the divergences ledger).
5. **Add rationale comments for the 5 deferred flags** (`ENABLE_COMBAT_ENGAGEMENT`,
   `ENABLE_SELF_MODEL_COGNITION`, `ENABLE_WORLD_EMERGENCE`, `ENABLE_PROGRESSION_EVOLUTION`,
   `ENABLE_INFORMATION_INTENT_EXECUTION`) directly in `feature_flags.py`, matching the style/depth
   of the existing ON-default flags' comments, each citing the named follow-up ticket that would
   need to land before a future flip.
6. **File 5 named follow-up tickets** (`tickets/todos/`, not implemented here), one per deferred
   flag, scoped narrowly as "produce real SHADOW/corpus-profile validation evidence for flag X,
   then decide flip" -- not full feature-completion tickets, since the systems themselves already
   exist and are tested; only production-readiness evidence is missing.
7. **Cut `RolloutProfileManager`**: remove `src/domains/optimization/rollout_profiles.py` entirely
   and its one real reference in `tests/perf/test_phase10_integrated_enhanced_stack_budget.py`
   (read that test first -- if it exercises real, still-relevant budget assertions independent of
   `RolloutProfileManager` itself, keep the test and only remove the dead import/usage; if the
   whole test is about the dead class, remove it too).
8. **Write the decision artifact** (this investigation.md + a new
   `docs/architecture/rollout_flag_decisions_m1.md`, ADR-shaped per this project's
   `docs/architecture/` convention) as the durable, discoverable record the ticket's own Scope
   calls for -- not just buried in ticket body text.
9. Run the full `tests/unit/config/`, `tests/perf/test_phase10_integrated_enhanced_stack_budget.py`
   (post-edit), and a scoped real-corpus sanity check before considering this done.

## Scope Guards
- No change to any of the 5 already-`ON`-default push-event-shaper flags.
- No change to the 6 flags NOT in this ticket's 8 (`ENABLE_WORLD_CAPABILITY_LAYER`,
  `ENABLE_ADVENTURE_ROUTING`, `ENABLE_LIFE_ARC_CAMPAIGNS`, `ENABLE_ENHANCED_TRACE_EVENTS`).
- No new gameplay content or scenario wiring for any of the 8 systems.
- Do not attempt real SHADOW-mode validation runs for the 5 deferred flags in this ticket --
  that's explicitly the named follow-up tickets' own job.

## Acceptance-Criteria Map
- AC1 (decision artifact, all 8) -> steps 8 (+ investigation.md's own decision table)
- AC2 (flip-ON needs allowlist entry or deferral) -> steps 1-2 (flips), step 6 (deferrals)
- AC3 (cut needs removal or rationale) -> step 7 (RolloutProfileManager)
- AC4 (reconcile against the 2 profiles) -> investigation.md's own findings, steps 1-3
- AC5 (closed before any other M1 ticket adding new flag-gated behavior) -> satisfied by this
  ticket running first per the reordered `SEQUENCE.md`
