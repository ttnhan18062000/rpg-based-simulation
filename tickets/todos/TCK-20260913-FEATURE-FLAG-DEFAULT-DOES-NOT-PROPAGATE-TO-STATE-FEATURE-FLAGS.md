---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260913-FEATURE-FLAG-DEFAULT-DOES-NOT-PROPAGATE-TO-STATE-FEATURE-FLAGS
phase: open
date: 2026-09-13
tags: [feature-flags, engine]
---

# TCK-20260913-FEATURE-FLAG-DEFAULT-DOES-NOT-PROPAGATE-TO-STATE-FEATURE-FLAGS

## Title
Changing a flag's default in `FeatureFlagManager` is a no-op for real runs — its own default never
reaches `state.feature_flags`, the dict every direct-dict-gated consumer actually reads

## Status
OPEN

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
- For each of the 9 flags in the table, determine whether its own inner literal gate is *sole*
  (no outer `run_phase()` wrapper involved at all — e.g. `GuildNeedScorer`, a goal scorer called
  from tactical decision-making, never from `pipeline.py`'s `refine()`) or *redundant* (an outer
  `run_phase()` gate already exists and is the actual determinant; the inner check is
  belt-and-suspenders, per `GuildVisitPhase`'s own docstring for its half of this shape). This
  changes the fix's own shape per flag.
- Design the real fix for the propagation gap: NOT "seed `state.feature_flags` from
  `FeatureFlagManager`'s defaults" wholesale (the unmeasured-blast-radius risk above) and NOT
  "change each inner gate's hardcoded fallback string to match" (creates two independently-edited
  sources of truth for one concept, coincidentally agreeing today — the exact dual-mechanism shape
  this arc has spent months deleting; the next person who edits one and not the other reproduces
  this same silent divergence). A real design is owed here, not picked by default.
- Once a design exists: decide whether making `SHADOW` meaningful for the *sole*-gate cases
  (scorers with no `run_phase()`-style update-discarding wrapper to reuse) is worth building, or
  whether the ON-based-measurement-with-explicit-override approach this arc just used for
  `ENABLE_GUILD_QUEST_GENERATION` is the accepted alternative going forward.
- Re-examine `TCK-20260824-ROLLOUT-FLAG-DECISIONS`'s 5 named `*-FLAG-VALIDATION` follow-up tickets
  (and any others citing "no SHADOW-validation history exists") for whether each cited flag is
  among the 9 — if so, that ticket's own validation plan needs revising, not just this one.

## Out of Scope
- Implementing any fix in this ticket — investigation, design, and the measurement above only.
- `ENABLE_GUILD_QUEST_GENERATION`'s own resolution — tracked in
  `TCK-20260912-KNOWLEDGE-INVESTIGATION-LAYER-INERT-NO-FACTS-NO-LEADS`, which closes as `BLOCKED`
  rather than `DONE` specifically because this ticket's own propagation gap keeps its default flip
  from reaching real runs. That ticket's own D-10 measurement evidence (the mechanism genuinely
  works once actually reached) stands independent of this ticket's resolution.
- The 5 `ENABLE_PUSH_EVENT_SHAPERS*` flags — different, already-disclosed, intentional bypass, no
  divergence found.
- Re-running the blast-radius measurement as part of this ticket's own filing — it's a live count
  that must be re-verified at whatever point a fix is actually built, not trusted as static.

## Acceptance Criteria
- [x] The propagation-gap headline established with real evidence (not the SHADOW-only framing
      this ticket originally shipped with).
- [x] The blast-radius measurement performed and recorded: 1 flag currently disagrees, 8 more
      share the same shape and currently agree by coincidence, 19 flags are unaffected.
- [ ] Each of the 9 flags classified sole-gate vs. redundant-gate.
- [ ] A real design for the propagation fix, ruling out both the "seed from manager defaults"
      wholesale option (unmeasured blast radius) and the "patch each inner fallback to match"
      option (recreates the dual-mechanism shape) as defaults, brought to peer/user review before
      implementation.
- [ ] `TCK-20260824-ROLLOUT-FLAG-DECISIONS`'s 5 named follow-up `*-FLAG-VALIDATION` tickets checked
      against the 9-flag list; any citing an unobtainable SHADOW window flagged explicitly.
- [ ] No implementation without that review.

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
_(pending — filed, not yet picked up)_

## Test Summary
_(pending)_

## Files Changed
_(pending)_

## Completion Summary
_(pending)_
