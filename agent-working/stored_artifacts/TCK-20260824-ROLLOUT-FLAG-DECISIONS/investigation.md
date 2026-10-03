---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260824-ROLLOUT-FLAG-DECISIONS
artifact_type: investigation
tags: [feature-flags]
---

# Investigation — TCK-20260824-ROLLOUT-FLAG-DECISIONS

## Method
Direct source read of `src/domains/optimization/feature_flags.py`,
`src/domains/optimization/rollout_profiles.py`, `src/engine/pipeline.py`; grep-based call-site and
test-coverage census for each of the 8 named flags; cross-check against
`config/simulation_quality/profiles/{urban_political,sandbox_world}.yaml`; read of the two
Related-Tickets that carry flag history (`TCK-20260703-SIMQ-UPLIFT3-BRANCH-B`,
`TCK-20260807-FEATURE-FLAG-OFF-SHADOW-TEST-STALE`).

## Findings

### All 8 flags confirmed present, currently OFF
`FeatureFlagManager.__init__` (`src/domains/optimization/feature_flags.py:13-79`) confirms all 8
named flags default `FeatureMode.OFF`, with zero inline rationale comments on any of them --
unlike the 5 `ON`-default push-event-shaper flags in the same dict, each of which carries a real,
cited, multi-line justification. This asymmetry itself is evidence the 8 target flags were never
given the same deliberate-decision treatment.

### 2 of 8 already have real production evidence: BELIEF_ASSIMILATION, SOCIAL_COOPERATION
`config/simulation_quality/profiles/sandbox_world.yaml:2` and `urban_political.yaml:9` both set
`ENABLE_BELIEF_ASSIMILATION: "ON"`; `urban_political.yaml:8` also sets
`ENABLE_SOCIAL_COOPERATION: "ON"`. These are real, live SimQ corpus profiles this project already
runs regularly -- the strongest possible evidence short of a dedicated validation ticket. No
counter-evidence found (no test or comment suggesting either is unsafe at the global default
level).

### GUILD_QUEST_GENERATION already has an explicit keep-OFF rationale
`feature_flags.py:46-53`'s own inline comment: "New gameplay behavior
(`TCK-20260807-QUEST-GUILDACTION-DEAD-WIRING`), not a validated replacement of existing behavior --
DEV-002's default-OFF policy applies... Gates both `GuildNeedScorer`... and the `guild_visit`
pipeline phase... belt-and-suspenders." This is already a deliberate decision, just not yet
reflected in a decision artifact or `intentional_divergences.md` entry.

### COMBAT_ENGAGEMENT has a real fix history but no production validation
`src/engine/pipeline.py:245-254`'s comment documents `TCK-20260809-COMBAT-ENGAGEMENT-FLAG-
SUPPRESSES-PUSH-SHAPER-EVENTS` -- a real bug (this phase's own `StateUpdate` silently replaced,
not merged, every earlier phase's output whenever the flag was `ON`, confirmed via live corpus A/B
testing to zero out `combat_engagement_started/ended`, `combat_resolved`, `combat_damage`,
`entity_killed`) that was found and fixed. This confirms someone has already attempted real
flag-ON testing and the current code is post-fix, but no corpus profile turns this flag on by
default today -- the fix's own validation was a one-off A/B test, not a standing production
signal. 7 test files reference the flag.

### SELF_MODEL_COGNITION, WORLD_EMERGENCE, PROGRESSION_EVOLUTION, INFORMATION_INTENT_EXECUTION
Real call sites confirmed in `src/engine/pipeline.py` (`self_model` phase line 143,
`information_intent_execution` around line 161, `world_emergence` line 290,
`progression_conversion` line 322 -- the last confirms the ticket's own open Assumption: "Progression
Conversion" in the M1 epic's own prose naming maps to the actual flag `ENABLE_PROGRESSION_EVOLUTION`,
resolved). 10 / 3 / 2 / 5 test files respectively reference each flag by name. None has a corpus
profile turning it on, and no fix-history comment (of the `TCK-20260809-...` kind found for
COMBAT_ENGAGEMENT) surfaced for any of the four -- no evidence either way beyond "the code exists
and has unit-level test coverage," which is not the same bar as BELIEF_ASSIMILATION/
SOCIAL_COOPERATION's real corpus-profile production evidence.

### RolloutProfileManager is confirmed dead
`src/domains/optimization/rollout_profiles.py` defines a full `CLASS_A`/`CLASS_B`/`CLASS_C`
hardware-tier rollout matrix with its own default-ON/SHADOW/OFF assignment per flag --
**conflicting** with `FeatureFlagManager`'s own all-OFF-except-5 defaults (e.g. its `CLASS_A`
profile lists `ENABLE_SELF_MODEL_COGNITION` as enabled by default, `FeatureFlagManager` says OFF).
Grepped the whole tree for `RolloutProfileManager`/`from ...rollout_profiles import` (a broader,
substring-based `HardwareClass` grep first over-matched dozens of unrelated files --
`HardwareClassifier` in `src/certification/hardware.py` and generic "hardware class" prose, a
false-positive corrected during Implement, not before). The real reference set is exactly two test
files, both test-only: `tests/perf/test_phase10_integrated_enhanced_stack_budget.py` (borrows the
profile's `tick_budget_ms`/`max_trace_events` numbers as convenient test parameters -- kept, with
those numbers inlined directly) and `tests/unit/config/test_phase10_rollout_profiles.py` (a
dedicated TDD suite that tests nothing but `RolloutProfileManager` itself -- removed outright, no
other purpose to preserve). Zero real application call sites in either case (not `src/cli/entry.py`,
not `src/api/server.py`, not `ConfigLoader`). Confirmed genuinely orphaned, not just under-used.

## Decision (per direct user confirmation, given the evidence above)

| Flag | Verdict | Rationale |
|---|---|---|
| `ENABLE_BELIEF_ASSIMILATION` | **Flip ON** | Real, live corpus-profile evidence (2 profiles) |
| `ENABLE_SOCIAL_COOPERATION` | **Flip ON** | Real, live corpus-profile evidence (1 profile) |
| `ENABLE_GUILD_QUEST_GENERATION` | **Keep OFF** | Already-deliberate, already-documented DEV-002 policy decision -- formalized, not re-litigated |
| `ENABLE_COMBAT_ENGAGEMENT` | **Keep OFF, deferred** | Real fix history but no standing production validation; needs a real SHADOW/corpus trial before flipping -- named follow-up ticket |
| `ENABLE_SELF_MODEL_COGNITION` | **Keep OFF, deferred** | No production evidence; named follow-up ticket |
| `ENABLE_WORLD_EMERGENCE` | **Keep OFF, deferred** | No production evidence; named follow-up ticket |
| `ENABLE_PROGRESSION_EVOLUTION` | **Keep OFF, deferred** | No production evidence; named follow-up ticket |
| `ENABLE_INFORMATION_INTENT_EXECUTION` | **Keep OFF, deferred** | No production evidence; named follow-up ticket |
| `RolloutProfileManager` | **Cut** | Confirmed dead: zero real callers, conflicting default matrix |
