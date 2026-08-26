---
status: active
layer: engine
authority: P1
audience: agent
tags: [feature-flags, architecture]
---

# Rollout Flag Decisions — RPG Design Roadmap M1

**Source ticket**: `TCK-20260824-ROLLOUT-FLAG-DECISIONS`, the first ticket implemented in the
`m1-quick-wins` batch (`docs/plans/rpg_design_roadmap/rpg_m1_quick_wins_epic.md`, idea 9), run
first per that epic's own explicit acceptance signal: "Idea 9's flag-governance ticket lands
before any other M1 ticket that adds new flag-gated behavior."

This is the durable, discoverable decision artifact `TCK-20260824-ROLLOUT-FLAG-DECISIONS`'s own
Scope calls for — the full evidence trail lives in
`staging_artifacts/TCK-20260824-ROLLOUT-FLAG-DECISIONS/investigation.md`; this document states the
decisions and their rationale for future reference, including for the 38 more M2+ flagged ideas
this precedent governs.

## The 8 Flags Reviewed

| Flag | Verdict | Rationale |
|---|---|---|
| `ENABLE_BELIEF_ASSIMILATION` | **Flipped ON** | Real, live corpus-profile evidence — already `ON` in both `config/simulation_quality/profiles/sandbox_world.yaml` and `urban_political.yaml`. `docs/guidelines/intentional_divergences.md` DEV-003. |
| `ENABLE_SOCIAL_COOPERATION` | **Flipped ON** | Real, live corpus-profile evidence — already `ON` in `urban_political.yaml`. DEV-003. |
| `ENABLE_GUILD_QUEST_GENERATION` | **Kept OFF** | Already had a deliberate, documented DEV-002-policy rationale in `feature_flags.py`'s own comment before this ticket — formalized, not re-litigated. |
| `ENABLE_COMBAT_ENGAGEMENT` | **Kept OFF, deferred** | Real fix history (`TCK-20260809-COMBAT-ENGAGEMENT-FLAG-SUPPRESSES-PUSH-SHAPER-EVENTS`) but no standing production validation. Follow-up: `TCK-20260826-COMBAT-ENGAGEMENT-FLAG-VALIDATION`. |
| `ENABLE_SELF_MODEL_COGNITION` | **Kept OFF, deferred** | No production evidence; the dead `RolloutProfileManager`'s own conflicting default (enabled) was confirmed not usable as evidence. Follow-up: `TCK-20260826-SELF-MODEL-COGNITION-FLAG-VALIDATION`. |
| `ENABLE_WORLD_EMERGENCE` | **Kept OFF, deferred** | No production evidence. Follow-up: `TCK-20260826-WORLD-EMERGENCE-FLAG-VALIDATION`. |
| `ENABLE_PROGRESSION_EVOLUTION` | **Kept OFF, deferred** | No production evidence; thinnest test coverage of the 5 deferred flags (2 files) — the follow-up must assess coverage depth before trusting any trial. Follow-up: `TCK-20260826-PROGRESSION-EVOLUTION-FLAG-VALIDATION`. |
| `ENABLE_INFORMATION_INTENT_EXECUTION` | **Kept OFF, deferred** | No production evidence; distinct system from the now-ON `ENABLE_BELIEF_ASSIMILATION` despite shared domain. Follow-up: `TCK-20260826-INFORMATION-INTENT-EXECUTION-FLAG-VALIDATION`. |

## RolloutProfileManager — Cut

`src/domains/optimization/rollout_profiles.py` defined a full `CLASS_A`/`CLASS_B`/`CLASS_C`
hardware-tier rollout matrix with its own default-ON/SHADOW/OFF assignment per flag —
**conflicting** with `FeatureFlagManager`'s own real defaults (e.g. its `CLASS_A` profile listed
`ENABLE_SELF_MODEL_COGNITION` as enabled; the real default was OFF). Confirmed genuinely
orphaned: the only two references anywhere in the codebase were both test-only
(`tests/perf/test_phase10_integrated_enhanced_stack_budget.py`, which borrowed its
`tick_budget_ms`/`max_trace_events` numbers as convenient test parameters — kept, with those
numbers inlined directly; and `tests/unit/config/test_phase10_rollout_profiles.py`, a dedicated
TDD suite testing nothing but the dead class itself — removed outright). Zero real application
call sites. Both the module and the dedicated test file were removed.

## The Precedent This Sets

Two decision classes exist, both legitimate, neither a default:
1. **Flip ON** requires real, standing evidence the system already runs safely in production —
   here, a live SimQ corpus profile already exercising it. A one-off validated fix (like
   `ENABLE_COMBAT_ENGAGEMENT`'s bug-fix history) is necessary but not sufficient on its own.
2. **Keep OFF, deferred** is not a non-decision — it requires a named follow-up ticket whose job is
   specifically to produce the missing evidence, not an indefinite "someday."

`DEV-002`'s own literal unblock condition (re-running `tools/balance_measure.py`) was found to be
scoped to the specific ticket that wrote it (`TCK-20260627-P0A-ADVENTURE-FLAG`,
`ENABLE_ADVENTURE_ROUTING`'s own economy/hunger metrics) and not a universal fit for every flag's
domain — `DEV-003` documents treating equivalent-strength alternative evidence (standing SimQ
corpus usage in the flag's own domain) as satisfying DEV-002's underlying intent, stated plainly
rather than silently substituted.

## A Real Correction Made During Implementation

The investigation's first pass under-counted `RolloutProfileManager`'s real reference set by one
file (missed `test_phase10_rollout_profiles.py`) and separately, a broad `HardwareClass` grep
initially over-matched dozens of unrelated files (`HardwareClassifier` in
`src/certification/hardware.py`, generic "hardware class" prose) before being narrowed to the
precise `rollout_profiles import` / `RolloutProfileManager\b` pattern. Both corrections are
recorded here and in the staging investigation.md rather than silently fixed without a trace —
worth noting for whoever reviews this precedent: a first grep pass is a starting point, not a
final answer, even on a narrowly-scoped "is this dead" question.

Separately, three independent hardcoded copies of the `_DELIBERATE_ON_DEFAULT_FLAGS` allowlist
were found across the test suite (`tests/unit/config/test_phase10_feature_flags.py`,
`tests/integration/test_scenario_feature_flag_defaults.py`,
`tests/certification/test_phase10_enhanced_determinism_parity.py`) — each explicitly documented as
"kept in sync" with the others, none actually enforced to be in sync by any single source of
truth. All three were updated to add the 2 new flags; this is a real, disclosed architectural
smell (three manually-synchronized copies of the same allowlist) worth a future consolidation
ticket, not fixed here since it is outside this ticket's own scope.

## Related

- `staging_artifacts/TCK-20260824-ROLLOUT-FLAG-DECISIONS/` (investigation.md, plan.md, test_plan.md)
- `docs/guidelines/intentional_divergences.md` (DEV-002, DEV-003)
- `docs/plans/rpg_design_roadmap/rpg_m1_quick_wins_epic.md` (idea 9, the source scope)
- The 5 named follow-up tickets (see table above)
