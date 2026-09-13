---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260913-FEATURE-FLAG-DEFAULT-DOES-NOT-PROPAGATE-TO-STATE-FEATURE-FLAGS
phase: done
date: 2026-09-13
tags: [feature-flags, engine]
---

# TCK-20260913-FEATURE-FLAG-DEFAULT-DOES-NOT-PROPAGATE-TO-STATE-FEATURE-FLAGS

## Title
Changing a flag's default in `FeatureFlagManager` is a no-op for real runs — its own default never
reaches `state.feature_flags`, the dict every direct-dict-gated consumer actually reads

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P0

## Request Summary
**The headline, stated first because it is larger than any single flag:** `FeatureFlagManager`'s
own hardcoded default dict (`src/domains/optimization/feature_flags.py`) is **not the source of
truth any consumer that reads `state.feature_flags` directly ever sees.** `AuthoritativeState.
feature_flags` (`src/core/state.py:1367`) defaults to an **empty dict** and nothing in real
production code ever seeds it from `FeatureFlagManager`'s own defaults. For any flag whose real
gate is a direct `state.feature_flags.get(FLAG, "OFF")` read (rather than `run_phase()`'s own
`FeatureFlagManager`-backed dispatch), **changing that flag's default in `feature_flags.py` changes
nothing for any real run that doesn't separately, explicitly set the key** — via an env var, a
corpus profile's own YAML `feature_flags:` block, or a test/scenario constructing state directly.
The flag-default dict we reason about when deciding rollout policy is, for that whole class of
flags, **decorative** — it documents an intention that reads correctly and does nothing.

**Found and confirmed empirically, not by static reading, while shipping
`ENABLE_GUILD_QUEST_GENERATION`'s own default flip** for
`TCK-20260912-KNOWLEDGE-INVESTIGATION-LAYER-INERT-NO-FACTS-NO-LEADS`: flipped the flag's own entry
to `FeatureMode.ON`, ran the exact test harness (`tools.calibrate_simq._run_engine`) a real corpus
profile (`frontier_marches`) uses, with the profile's own real `feature_flags:` overrides applied —
**zero** calls to `GuildNeedScorer`/the guild-visit phase, identical to the pre-flip baseline
(confirmed by reverting the change and re-running: bit-identical failure). The flip only "worked"
in an earlier measurement because that measurement set the env var directly, which populates
`state.feature_flags` through a completely different path (`tools/calibrate_simq.py`'s own
override merge) than the dict entry that was changed.

**Root cause**: `GuildNeedScorer.score()` (`src/ai/goals/scorers.py:254`) and the guild-visit
phase's own internal check (`src/engine/pipeline_phases/guild_visit.py:40`) both read
`state.feature_flags.get("ENABLE_GUILD_QUEST_GENERATION", "OFF")` directly — a **second,
independent flag-state surface** from `FeatureFlagManager`, which is constructed fresh per
`refine()` call from its own hardcoded defaults plus `state.rollout_profile.enabled_phases`
(ON-only overrides), **never from `state.feature_flags`, and never written back into it either**.
`run_phase()`'s own outer dispatch (`ff_manager.get_flag_mode()`) genuinely understands
`OFF`/`SHADOW`/`ON`/`STRICT` and reads `FeatureFlagManager`'s real state — but for these consumers,
it's an outer gate wrapping an inner one that reads a *different*, disconnected value, and the
inner one is what actually decides behavior for the scorer (which isn't even wrapped by
`run_phase()` at all).

## The measured blast radius — identify, don't act
**Exactly 1 of the 28 flags currently has its `FeatureFlagManager` default disagreeing with its own
direct-dict-gate's hardcoded fallback**: `ENABLE_GUILD_QUEST_GENERATION` (manager default `ON` as
of this batch; every real consumer's own inner fallback is the string `"OFF"`) — the one this
investigation just created by flipping only one side of the divergence. Measured directly, not
inferred:

- **9 flags total** have at least one real consumer reading `state.feature_flags` with a literal
  `== "ON"` / `!= "ON"` comparison and a hardcoded default (see the table below) — the shape that
  makes this divergence possible at all.
- **8 of those 9** currently *agree* with `FeatureFlagManager`'s own default (both `OFF`) — by
  construction, not by any enforced invariant. Each is one careless default-flip away from
  reproducing the exact silent divergence found here.
- **The other 19 flags** (including the 2 non-push-shaper `ON` flags, `ENABLE_BELIEF_ASSIMILATION`
  and `ENABLE_SOCIAL_COOPERATION`, confirmed via grep to have no direct-dict inner gate anywhere)
  are gated exclusively through `run_phase()`'s own `FeatureFlagManager` dispatch — for these,
  changing the manager default is real and sufficient.

| Flag | Site(s) | Manager default | Inner fallback | Agree? |
|---|---|---|---|---|
| `ENABLE_GUILD_QUEST_GENERATION` | `guild_visit.py:40`, `scorers.py:254` | `ON` | `"OFF"` | **NO** |
| `ENABLE_ITEM_INSTANCE_HISTORY` | `core/inventory.py:256` | `OFF` | `"OFF"` | yes (coincidence) |
| `ENABLE_CAMP_NEST_SPREAD` | `world/camp.py:85` | `OFF` | `"OFF"` | yes (coincidence) |
| `ENABLE_REPRODUCTION_NATURAL_CREATURE_PATH` | `world/camp.py:144` | `OFF` | `"OFF"` | yes (coincidence) |
| `ENABLE_REPRODUCTION_MAGICAL_DEMONIC_PATH` | `world/calamity.py:67` | `OFF` | `"OFF"` | yes (coincidence) |
| `ENABLE_CREATURE_TERRITORY_LIFECYCLE` | `engine/world_dynamics.py:214` | `OFF` | `"OFF"` | yes (coincidence) |
| `ENABLE_REPRODUCTION_HUMANOID_PATH` | `engine/world_dynamics.py:230` | `OFF` | `"OFF"` | yes (coincidence) |
| `ENABLE_HABIT_BIAS_ACTION_STYLE` | `engine/movement.py:193`, `engine/tactical.py:499` | `OFF` | `"OFF"` | yes (coincidence) |
| `ENABLE_INFORMATION_HUB_ACCUMULATION` | `engine/quests.py:241` | `OFF` | `"OFF"` | yes (coincidence) |

The 5 `ENABLE_PUSH_EVENT_SHAPERS*` flags also bypass `FeatureFlagManager` via a direct
`state.feature_flags` read, but their own inner fallback already defaults to `"ON"` matching their
manager default (`event_extractor.py`'s `.get(FLAG, "ON")`), and the bypass is explicitly
documented and intentional (`docs/guides/feature_flags.md`) — no divergence, different case,
excluded from the count.

**This measurement stops here on purpose — it identifies the set, it does not act on it.** Seeding
`state.feature_flags` from `FeatureFlagManager`'s own defaults would activate every flag whose
manager default is `ON` while its own inner-gate fallback is `OFF` — today that's exactly 1 flag,
but a real fix that seeds this generally would need to re-verify that count at fix time, not trust
this snapshot, since the set can grow with every future default flip that doesn't update its own
inner gate. Turning on an unknown number of dormant features in one change is not something to
discover after merging.

## A second, related but distinct question: SHADOW mode is also inert for the same 9 flags
Confirmed via the same instrumented run: setting `state.feature_flags["ENABLE_GUILD_QUEST_
GENERATION"] = FeatureMode.SHADOW` produced **zero** guild-visit calls — identical to `OFF`. Every
one of the 9 flags in the table above states the identical `DEV-002` rationale in its own
`feature_flags.py` comment ("no corpus profile turns this on and no SHADOW-validation history
exists") — that history was never obtainable for these 9 specifically, because their own gates
cannot distinguish `SHADOW` from `OFF` at all. A decision to "wait for SHADOW validation" made on a
precondition that cannot be satisfied is the same shape as this arc's own unreachable-content
findings in `docs/plans/deferred_tuning_decisions_register.md` (D-05's lairs behind a maturity
threshold no run reaches, D-06's sieges behind a war that never gets declared) — except the
unreachable gate here is in the rollout *process* itself, not the simulation. Every one of the 9
also has no non-fabricated SHADOW-validation history behind it for the same structural reason.

## Scope
**Superseded 2026-09-13, after peer review of this ticket's own blast-radius measurement**: the
measured count (1 of 9 direct-dict-gated flags disagreeing, 8 agreeing by coincidence) turned
"seed `state.feature_flags` from `FeatureFlagManager`'s defaults" from an unmeasured risk into a
bounded, reviewable one. Peer reopened it as the leading fix, on condition that (a) the count is
re-confirmed against current `main` before building, (b) real test coverage covers the seeding
*mechanism* itself, not just that one flag's resulting value, and (c) the inner `.get(..., "OFF")`
fallbacks are still not patched — that option remains rejected, unchanged from the original filing.
Acceptance is the real acceptance signal from `TCK-20260912-KNOWLEDGE-INVESTIGATION-LAYER-INERT-NO-FACTS-NO-LEADS`:
a real lead reaching a real entity in an unmodified corpus profile, no env var.

- Re-confirm the 1-of-9 divergence count against current `main` before implementing.
- Seed `state.feature_flags` from `FeatureFlagManager().serialize()` once, at the single real entry
  point every simulation run passes through (`Kernel.__init__`), with explicit overrides already
  present in `state.feature_flags` winning over manager defaults.
- Cover the propagation mechanism itself with committed tests: seeding from empty, override
  preservation, idempotency across repeated construction, and the real corpus-profile end-to-end
  acceptance signal.
- Do NOT patch any of the 9 inner-gate hardcoded fallback strings — unchanged from original filing.

## Out of Scope
- Classifying each of the 9 flags sole-gate vs. redundant-gate — real design question, not required
  to close the propagation gap itself; left open below for whoever picks it up next.
- Re-examining `TCK-20260824-ROLLOUT-FLAG-DECISIONS`'s 5 named `*-FLAG-VALIDATION` follow-ups
  against the 9-flag list — process/tracking work, not part of the propagation fix; left open below.
- `ENABLE_GUILD_QUEST_GENERATION`'s own ticket resolution — tracked in
  `TCK-20260912-KNOWLEDGE-INVESTIGATION-LAYER-INERT-NO-FACTS-NO-LEADS`, which closes independently
  once this fix's real evidence is in hand.
- The 5 `ENABLE_PUSH_EVENT_SHAPERS*` flags — different, already-disclosed, intentional bypass, no
  divergence found; untouched by this fix (they don't read `state.feature_flags.get(FLAG, "OFF")`
  with a hardcoded literal in the same way, and already default `"ON"` to match).

## Acceptance Criteria
- [x] The propagation-gap headline established with real evidence.
- [x] The blast-radius measurement performed, recorded, and **re-confirmed against current `main`**
      before implementation: still 1 of 9 direct-dict-gated flags disagreeing
      (`ENABLE_GUILD_QUEST_GENERATION`), 8 agreeing by coincidence. (Total manager-flag count moved
      28 → 26 since filing; noted, not load-bearing to the 9-flag shape.)
- [x] `state.feature_flags` seeded from `FeatureFlagManager`'s own defaults at `Kernel.__init__`,
      the single real entry point every simulation run passes through.
- [x] Explicit overrides already present in `state.feature_flags` (profile YAML, env var,
      test-constructed state) verified to survive seeding untouched.
- [x] Inner `.get(..., "OFF")` fallbacks left unpatched, per standing rejection of that option.
- [x] Real test coverage for the seeding *mechanism* (not just "the value is now ON"): seed-from-empty,
      override-preservation, and idempotency-across-repeated-construction, all committed.
- [x] The real acceptance signal obtained: `GuildAction.visit()` fires in an unmodified
      `frontier_marches` corpus profile run, no env var, no profile-YAML override for this flag —
      verified both by manual instrumented run and by a committed, passing pytest test.
- [ ] Each of the 9 flags classified sole-gate vs. redundant-gate — deferred, see Out of Scope.
- [ ] `TCK-20260824-ROLLOUT-FLAG-DECISIONS`'s 5 named follow-ups checked against the 9-flag list —
      deferred, see Out of Scope.

## Related Tickets
- `TCK-20260912-KNOWLEDGE-INVESTIGATION-LAYER-INERT-NO-FACTS-NO-LEADS` (blocked — the ticket whose
  own validation work found this; its own default flip for `ENABLE_GUILD_QUEST_GENERATION` is real
  and kept, but documented as not-yet-effective pending this ticket)
- `TCK-20260824-ROLLOUT-FLAG-DECISIONS` (done — the ticket whose 5 named follow-ups may need
  re-examining)

## Related Docs
- `docs/guidelines/intentional_divergences.md` (DEV-002, DEV-003 — the rollout policy this defect
  silently undermines for 9 flags, and whose "changing a default" language this ticket shows is not
  always true)
- `docs/guides/feature_flags.md` (the 16-flag reference table; the 5 push-event-shaper rows are the
  disclosed, different bypass case)
- `docs/plans/deferred_tuning_decisions_register.md` (D-05, D-06 — the same unreachable-gate shape,
  in the simulation rather than the rollout process)

## Related Stored Artifacts
None yet — standard tier, staging artifacts created when picked up.

## Related Code Areas
- `src/core/state.py:1367` (`AuthoritativeState.feature_flags`, defaults to `{}`, never seeded from
  `FeatureFlagManager`)
- `src/engine/pipeline.py:68-92, 102-133` (`FeatureFlagManager` construction, the one-directional
  `state.feature_flags` → `ff_manager` sync that exists, and `run_phase()`'s real dispatch)
- `src/domains/optimization/feature_flags.py` (`FeatureFlagManager.__init__`, the 9 flags' own
  defaults and the 1 current divergence)
- The 9 flags' own inner-gate sites listed in the table above
- `tools/calibrate_simq.py` (`_run_engine()`'s own env-var/profile-YAML override merge — the real
  path that DOES populate `state.feature_flags`, distinct from `FeatureFlagManager`'s defaults)

## Assumptions / Open Questions
- Whether making SHADOW meaningful for the sole-gate cases (no `run_phase()`-style wrapper to
  reuse) is worth the design effort versus standardizing on the ON-based-measurement-with-explicit-
  override approach is the central open question — not resolved here.
- Whether the "redundant" gates (an outer `run_phase()` dispatch already exists) should keep their
  own inner check at all, given it's exactly the dual-mechanism shape this arc avoids elsewhere, or
  whether the real fix removes the redundant check entirely once the sole-gate cases are resolved
  — not decided here.

## Implementation Notes
- Fix lands in `Kernel.__init__` (`src/engine/kernel.py`), immediately after the existing
  `_opt_profile`/`_force_full_scan` `object.__setattr__` block, following that same
  stamp-a-derived-value-onto-frozen-state-at-construction pattern:
  `object.__setattr__(self._state, "feature_flags", {**FeatureFlagManager().serialize(), **dict(getattr(self._state, "feature_flags", None) or {})})`.
  Deliberately not wrapped in a swallowing `try/except`, unlike the adjacent block —
  `feature_flags` is a real, always-present field; a failure here should surface.
- This seeds all 26 manager-default flags into every real run, not only
  `ENABLE_GUILD_QUEST_GENERATION` — confirmed via a repo-wide sweep
  (`-m "corpus_flag_guardrail or scenario_flags or feature_flag_default"`, 118 passed) that this is
  inert for the other 17 non-dual-gated flags, since they're read exclusively through
  `FeatureFlagManager`'s own `run_phase()` dispatch and never consult `state.feature_flags`
  directly.
- Two design questions from the original filing remain genuinely open, not resolved by this fix:
  whether each of the 9 flags' inner gate should be classified sole-gate vs. redundant-gate, and
  whether `TCK-20260824-ROLLOUT-FLAG-DECISIONS`'s 5 named `*-FLAG-VALIDATION` follow-ups need
  revisiting. Left for whoever picks up that design work next — see Related Tickets.
- See `staging_artifacts/.../investigation.md` for the full re-confirmation of the blast-radius
  count against current `main`, and the reasoning for the merge-order choice (explicit overrides
  win, manager defaults only fill gaps).

## Test Summary
- `tests/unit/engine/test_kernel_feature_flags_propagation.py` — 4 new tests, all passing (seed-
  from-empty, override-preservation, idempotency, real corpus-profile end-to-end acceptance signal).
- Guild/flag/feature-flag regression sweep (9 files) — 97 passed.
- Broader `tests/unit/engine/ tests/integration/kernel/ tests/unit/domains/optimization/` sweep
  (`-m "not slow and not extra_slow"`) — 448 passed, 1 unrelated skip, 6 deselected.
- Repo-wide `-m "corpus_flag_guardrail or scenario_flags or feature_flag_default"` — 118 passed.
- No regressions found. Full detail in `staging_artifacts/.../test_plan.md`.

## Files Changed
- `src/engine/kernel.py` — seed `state.feature_flags` from `FeatureFlagManager`'s own defaults in
  `Kernel.__init__`.
- `tests/unit/engine/test_kernel_feature_flags_propagation.py` — new, 4 tests covering the
  propagation mechanism and the real acceptance signal.
- `tickets/inprogress/` → `tickets/done/` (this ticket).
- `staging_artifacts/TCK-20260913-.../` → `stored_artifacts/TCK-20260913-.../`.

## Completion Summary
The propagation gap is fixed: `state.feature_flags` is now seeded from `FeatureFlagManager`'s own
defaults at the single real entry point every simulation run passes through, with explicit
overrides always winning. Verified against the exact acceptance signal specified — a real lead
reaching a real entity in an unmodified `frontier_marches` corpus profile, no env var — both by a
manual instrumented run and by a committed, passing regression test. The inner `.get(..., "OFF")`
fallbacks were left untouched, per the standing rejection of that option. Two narrower design
questions (sole/redundant gate classification per flag; the 5 `ROLLOUT-FLAG-DECISIONS` follow-ups)
remain open and are recorded as such rather than silently dropped. This unblocks
`TCK-20260912-KNOWLEDGE-INVESTIGATION-LAYER-INERT-NO-FACTS-NO-LEADS`, next in this batch's strict
order.
