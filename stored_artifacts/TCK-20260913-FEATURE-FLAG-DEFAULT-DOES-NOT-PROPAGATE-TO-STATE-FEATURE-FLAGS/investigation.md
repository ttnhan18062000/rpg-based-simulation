# Investigation — TCK-20260913-FEATURE-FLAG-DEFAULT-DOES-NOT-PROPAGATE-TO-STATE-FEATURE-FLAGS

## Re-confirming the blast radius against current `main` before building

The ticket's own filed measurement (1 of 28 flags disagreeing, 9 flags sharing the direct-dict-gate
shape) was re-run fresh against current `main`, per explicit review instruction, rather than trusted
as a static snapshot:

```
grep -rn 'flags\.get(.*"OFF"\|flags\.get(.*"ON"' src/ --include="*.py"
```

Found the same 9 unique flags at the same 11 call sites (`ENABLE_GUILD_QUEST_GENERATION` appears
twice — `guild_visit.py:40` and `scorers.py:254`):

`ENABLE_GUILD_QUEST_GENERATION`, `ENABLE_ITEM_INSTANCE_HISTORY`, `ENABLE_CAMP_NEST_SPREAD`,
`ENABLE_REPRODUCTION_NATURAL_CREATURE_PATH`, `ENABLE_REPRODUCTION_MAGICAL_DEMONIC_PATH`,
`ENABLE_CREATURE_TERRITORY_LIFECYCLE`, `ENABLE_REPRODUCTION_HUMANOID_PATH`,
`ENABLE_HABIT_BIAS_ACTION_STYLE`, `ENABLE_INFORMATION_HUB_ACCUMULATION`.

Cross-checked each against `FeatureFlagManager().serialize()`: still exactly **1 divergence**
(`ENABLE_GUILD_QUEST_GENERATION`: manager default `ON`, inner fallback `"OFF"`); the other 8 still
agree (`OFF`/`OFF`). The count still holds.

**One drift noted, not load-bearing**: `FeatureFlagManager().serialize()` now returns 26 total flags,
not 28 as the ticket's own filing stated — main moved since filing (two flags removed/consolidated
elsewhere). This doesn't change the 9-flag/1-divergence shape the fix targets; recorded here so the
"28" in the ticket body isn't left silently wrong.

## Why seeding at `Kernel.__init__` and not elsewhere

Every real simulation run constructs exactly one `Kernel` before ticking: `WorldCompiler`-driven
corpus runs, `tools/calibrate_simq.py`'s `_run_engine()`/`_run_campaign_engine()`, `CampaignOrchestrator`,
and every test that exercises real behavior rather than hand-building `AuthoritativeState` directly.
`Kernel.__init__` already had an established pattern immediately adjacent (the `_opt_profile`/
`_force_full_scan` `object.__setattr__` block) for stamping a derived value onto the frozen
`AuthoritativeState` once, at construction — the seeding fix follows the same shape rather than
inventing a new mutation point.

This was deliberately **not** placed inside `FeatureFlagManager` itself, `run_phase()`, or any of
the 9 inner-gate call sites — those were the two options the ticket's own filing explicitly ruled
out as defaults (seeding was "unmeasured risk" at filing time; patching inner fallbacks recreates
the dual-mechanism shape). Peer's re-opening of the seeding option came from the blast-radius
measurement itself: 1 of 26(28) disagreeing, not an unknown number, made the risk boundable.

## Why explicit overrides must win (not be clobbered by manager defaults)

`state.feature_flags` already has real, working callers that set it directly before/around Kernel
construction: `tools/calibrate_simq.py::_run_engine()`'s own profile-YAML + env-var override merge,
and any test that hand-constructs `AuthoritativeState(feature_flags={...})`. If manager defaults were
applied unconditionally (overwriting rather than filling gaps), an explicit `SHADOW` or `ON` override
set by one of those real callers would be silently reset to the manager's own `OFF` default for any
flag not in the manager's dict, or overwritten outright for one that is — turning this fix into a new
instance of the same "looks configured and isn't" problem it closes. The merge order
(`{**manager_defaults, **existing_flags}`) is the only one where the caller's own explicit state
always wins and the manager default only fills in what the caller never set.

## Root-cause confirmation: why this had gone undetected

`FeatureFlagManager` is constructed fresh inside `pipeline.py`'s own `refine()` call, from its own
hardcoded `__init__` defaults plus `state.rollout_profile.enabled_phases` — it is **never**
constructed from `state.feature_flags`, and its own resolved values are **never written back** into
`state.feature_flags` either. The 9 direct-dict-gated consumers (`GuildNeedScorer.score()`,
`GuildVisitPhase.resolve()`, and 7 others) never go through `FeatureFlagManager` or `run_phase()`'s
own OFF/SHADOW/ON/STRICT dispatch at all — they read `state.feature_flags` directly with their own
hardcoded string fallback. Two structurally disconnected sources of truth for the same 9 flags,
confirmed by reading both code paths directly (not inferred from naming or doc claims).

## Acceptance-signal verification (the real evidence, not just unit assertions)

Per explicit review instruction, the acceptance criterion is ticket 2's own signal: a real lead
reaching a real entity in an **unmodified corpus profile**, no env var. Verified twice:

1. **Manual scratch-script verification** (`/tmp/.../guild_flag_trace.py`, pre-existing from a prior
   segment of this same work): monkeypatched `GuildAction.visit`/`GuildNeedScorer.score`, ran
   `tools.calibrate_simq._run_engine("frontier_marches", ...)` with only the profile's own real
   `_load_profile_feature_flags()` overrides (`{'ENABLE_BELIEF_ASSIMILATION': 'ON'}` — no
   `ENABLE_GUILD_QUEST_GENERATION` declared anywhere in that profile's YAML). Before the fix: 0 guild
   visits. After the fix: `GuildNeedScorer` positive-utility calls: 365, `GuildAction.visit()` calls: 1.
2. **Committed pytest test** (`tests/unit/engine/test_kernel_feature_flags_propagation.py::
   test_guild_quest_generation_fires_in_unmodified_corpus_profile_without_env_var`): the same scenario,
   as a permanent regression test — asserts the profile does NOT itself declare the flag (so the
   evidence can't be accidentally satisfied by a profile-YAML override instead of the fix), then
   asserts at least one real `GuildAction.visit()` call occurs within 200 ticks. Passing.

## A side effect surfaced by the fix, not caused by it

Once leads are actually produced (previously impossible — `GuildAction.visit()` never fired against
any real corpus profile before this fix), `LeadState.detail`'s contract mismatch
(`TCK-20260913-LEADSTATE-DETAIL-LOCATION-KIND-CONTRACT-MISMATCH`) now fires on every tick a lead
exists, logged via a bare `except Exception` that was previously almost never exercised. This is
expected — evidence the propagation fix reached real production code, and the reason that ticket is
next in this same batch's strict order rather than a separate, unrelated concern.
