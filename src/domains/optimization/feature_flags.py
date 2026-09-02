from enum import Enum
from typing import Dict, Any, List

class FeatureMode(str, Enum):
    OFF = "OFF"
    SHADOW = "SHADOW"
    ON = "ON"
    STRICT = "STRICT"

class FeatureFlagManager:
    """Manages Phase 10 feature rollout modes."""
    def __init__(self, overrides: Dict[str, FeatureMode] = None) -> None:
        self._flags: Dict[str, FeatureMode] = {
            "ENABLE_WORLD_CAPABILITY_LAYER": FeatureMode.OFF,
            # Keep OFF, deferred (TCK-20260824-ROLLOUT-FLAG-DECISIONS): real call site
            # (self_model_phase.py) and 10 test files, but no corpus profile turns this on and
            # no SHADOW-validation history exists. Follow-up:
            # TCK-20260826-SELF-MODEL-COGNITION-FLAG-VALIDATION.
            "ENABLE_SELF_MODEL_COGNITION": FeatureMode.OFF,
            # New gameplay behavior (TCK-20260824-CAUSAL-MEMORY-ROUTE-SCORING): wires
            # MemoryUpdatePhase into refine() for the first time (previously zero call sites).
            # DEV-002 default-OFF policy applies -- no corpus profile turns this on yet and no
            # SHADOW-validation history exists.
            "ENABLE_MEMORY_UPDATE": FeatureMode.OFF,
            "ENABLE_ADVENTURE_ROUTING": FeatureMode.OFF,
            # Keep OFF, deferred (TCK-20260824-ROLLOUT-FLAG-DECISIONS): a real bug
            # (TCK-20260809-COMBAT-ENGAGEMENT-FLAG-SUPPRESSES-PUSH-SHAPER-EVENTS) was already
            # found and fixed here via live corpus A/B testing, but that was a one-off
            # investigation, not a standing production validation -- no corpus profile defaults
            # this on today. Follow-up: TCK-20260826-COMBAT-ENGAGEMENT-FLAG-VALIDATION.
            "ENABLE_COMBAT_ENGAGEMENT": FeatureMode.OFF,
            # Default ON (TCK-20260824-ROLLOUT-FLAG-DECISIONS): real, live production evidence --
            # already ON in both config/simulation_quality/profiles/sandbox_world.yaml and
            # urban_political.yaml, this project's own real SimQ corpus profiles. Flipped the
            # global default to match already-proven-safe production usage rather than leaving
            # the code default OFF while every real profile that exercises it overrides ON.
            "ENABLE_BELIEF_ASSIMILATION": FeatureMode.ON,
            # Keep OFF, deferred (TCK-20260824-ROLLOUT-FLAG-DECISIONS): real call site
            # (information_intent_execution.py) and 5 test files, but no corpus profile turns
            # this on and no SHADOW-validation history exists. Follow-up:
            # TCK-20260826-INFORMATION-INTENT-EXECUTION-FLAG-VALIDATION.
            "ENABLE_INFORMATION_INTENT_EXECUTION": FeatureMode.OFF,
            # Keep OFF, deferred (TCK-20260824-ROLLOUT-FLAG-DECISIONS): real call site
            # (progression_conversion phase) and 2 test files, but no corpus profile turns this
            # on and no SHADOW-validation history exists. Follow-up:
            # TCK-20260826-PROGRESSION-EVOLUTION-FLAG-VALIDATION.
            "ENABLE_PROGRESSION_EVOLUTION": FeatureMode.OFF,
            # Default ON (TCK-20260824-ROLLOUT-FLAG-DECISIONS): real, live production evidence --
            # already ON in config/simulation_quality/profiles/urban_political.yaml, this
            # project's own real SimQ corpus profile. Flipped the global default to match
            # already-proven-safe production usage.
            "ENABLE_SOCIAL_COOPERATION": FeatureMode.ON,
            # Keep OFF, deferred (TCK-20260824-ROLLOUT-FLAG-DECISIONS): real call site
            # (world_emergence phase) and 3 test files, but no corpus profile turns this on and
            # no SHADOW-validation history exists. Follow-up:
            # TCK-20260826-WORLD-EMERGENCE-FLAG-VALIDATION.
            "ENABLE_WORLD_EMERGENCE": FeatureMode.OFF,
            "ENABLE_LIFE_ARC_CAMPAIGNS": FeatureMode.OFF,
            "ENABLE_ENHANCED_TRACE_EVENTS": FeatureMode.OFF,
            # Default ON (not OFF like the other 11 flags): validated and cut over by
            # TCK-20260806-PUSH-CUTOVER-COMBAT-ECONOMY-FACTION — this is the live default path
            # for COMBAT/ECONOMY/FACTION event emission, not a speculative rollout candidate.
            # event_extractor.py's old diffing branches for these 3 domains remain in the
            # codebase, flag-gated to fire only when this is NOT "ON" — setting it to "OFF"
            # is a real, working rollback to pre-cutover behavior, not just a partial one.
            "ENABLE_PUSH_EVENT_SHAPERS": FeatureMode.ON,
            # Default ON (not OFF like the 11 phase-gating flags): validated (6-world real
            # comparison, TCK-20260806-PUSH-SHADOW-VALIDATION-PERF-PHASE2, GO verdict) and cut
            # over by TCK-20260806-PUSH-CUTOVER-PHASE2 — this is the live default path for
            # AGENCY/COGNITION/INFORMATION/PROGRESSION/WORLD/SOCIAL event emission (Phase 2's ~50
            # events), not a speculative rollout candidate. Same exception class as
            # ENABLE_PUSH_EVENT_SHAPERS above, kept on its OWN separate flag (not merged into that
            # one) specifically because it defaulted OFF during Phase 2's build — event_shapers.py's
            # PHASE2_SHAPER_REGISTRY existed precisely to give Phase 2 a real SHADOW-validation
            # window independent of Phase 1's already-ON flag (a real double-firing bug was found
            # and fixed during TCK-20260806-PUSH-SHAPER-REGISTRY-STRATEGY's own build when this
            # premise was first tested). event_extractor.py's old diffing branches for Phase 2's
            # domains remain in the codebase, flag-gated to fire only when this is NOT "ON" —
            # setting it to "OFF" is a real, working rollback to pre-cutover behavior.
            "ENABLE_PUSH_EVENT_SHAPERS_PHASE2": FeatureMode.ON,
            # New gameplay behavior (TCK-20260807-QUEST-GUILDACTION-DEAD-WIRING), not a validated
            # replacement of existing behavior — DEV-002's default-OFF policy applies (unlike the
            # two ON-default flags above, which cut over already-proven behavior). Gates both
            # GuildNeedScorer (src/ai/goals/scorers.py, checked via state.feature_flags directly)
            # and the guild_visit pipeline phase (src/engine/pipeline.py, checked via
            # FeatureFlagManager/run_phase) — belt-and-suspenders so a stale kind=="guild" project
            # from before a flag flip can't silently complete even if the scorer alone were somehow
            # bypassed. Formalized, not re-litigated, by TCK-20260824-ROLLOUT-FLAG-DECISIONS's own
            # keep-OFF verdict — this is the one flag of the 8 it reviewed that already had a
            # deliberate, documented rationale.
            "ENABLE_GUILD_QUEST_GENERATION": FeatureMode.OFF,
            # Default ON (not OFF): validated via real-kernel checks in both SHADOW
            # (construct-only) and ON (deliver, no double-fire against event_extractor.py's own
            # rollback path) during TCK-20260807-QUEST-EVENT-PUSH-MIGRATION -- migrates
            # quest_event (entity-project quest lifecycle, SOC-241) to the shaper-registry
            # pattern. Same exception class as ENABLE_PUSH_EVENT_SHAPERS/_PHASE2 above, kept on
            # its OWN separate flag rather than folded into ENABLE_PUSH_EVENT_SHAPERS_PHASE2
            # (which already defaults ON) for the identical reason Phase 2 needed its own flag
            # distinct from Phase 1's: reusing an already-ON flag would deliver live immediately
            # with no real SHADOW-validation window. event_extractor.py's old quest_event diffing
            # block remains in the codebase, flag-gated to fire only when this is NOT "ON" -- a
            # real, working rollback to pre-migration behavior.
            "ENABLE_PUSH_EVENT_SHAPERS_QUEST": FeatureMode.ON,
            # Default ON (not OFF): validated via real-kernel checks in both SHADOW
            # (construct-only) and ON (deliver, no double-fire against event_extractor.py's own
            # rollback path) during TCK-20260807-COMMITMENT-ABANDONED-PUSH-MIGRATION-GAP /
            # TCK-20260807-REJECTION-CASCADE-TICK-PUSH-MIGRATION-GAP -- migrates
            # commitment_abandoned + rejection_cascade_tick (both AgencyScorer) to the
            # shaper-registry pattern. Same exception class as the 3 push-event-shaper flags
            # above, kept on its OWN separate flag rather than folded into any already-ON flag
            # for the identical reason ENABLE_PUSH_EVENT_SHAPERS_QUEST needed its own flag apart
            # from ENABLE_PUSH_EVENT_SHAPERS_PHASE2. event_extractor.py's old diffing blocks for
            # both events remain in the codebase, flag-gated to fire only when this is NOT "ON"
            # -- a real, working rollback to pre-migration behavior.
            "ENABLE_PUSH_EVENT_SHAPERS_AGENCY": FeatureMode.ON,
            # New gameplay behavior (TCK-20260831-CREATURE-TERRITORY-LIFECYCLE): wires
            # CreatureTerritoryService into world_dynamics.py's macro-dynamics block for the
            # first time. DEV-002 default-OFF policy applies -- brand-new mechanic, no corpus
            # profile turns this on and no SHADOW-validation history exists.
            "ENABLE_CREATURE_TERRITORY_LIFECYCLE": FeatureMode.OFF,
            # New gameplay behavior (TCK-20260831-HABIT-BIAS-WIRING): wires HabitBiasService's
            # record_outcome/apply_habit_bias into a real per-tick writer (HabitBiasUpdatePhase)
            # and both live ActionStyle read sites (tactical.py kiting distance, movement.py
            # opportunity-attack suppression on EVASIVE retreat) for the first time. DEV-002
            # default-OFF policy applies -- brand-new mechanic, no corpus profile turns this on
            # and no SHADOW-validation history exists.
            "ENABLE_HABIT_BIAS_ACTION_STYLE": FeatureMode.OFF,
            # New gameplay behavior (TCK-20260831-ITEM-INSTANCE-HISTORY): registers the
            # ItemInstance ownership-history scaffolding (ItemInstanceService.maybe_create_instance,
            # src/core/inventory.py). DEV-002 default-OFF policy applies -- brand-new mechanic, no
            # production call site passes significant=True yet (significance_flag trigger criteria is an
            # explicit open design decision, not invented by this ticket -- see ticket AC #5), no corpus
            # profile turns this on and no SHADOW-validation history exists.
            "ENABLE_ITEM_INSTANCE_HISTORY": FeatureMode.OFF,
            # New gameplay behavior (TCK-20260831-ROLE-MODEL-IMITATION): wires
            # RoleModelSelectionPhase into refine() for the first time -- per-entity
            # proximity-based role-model watching/choosing plus intelligence_tier-modulated
            # imitation fidelity. DEV-002 default-OFF policy applies -- brand-new mechanic, no
            # corpus profile turns this on and no SHADOW-validation history exists.
            "ENABLE_ROLE_MODEL_IMITATION": FeatureMode.OFF,
        }
        if overrides:
            for k, v in overrides.items():
                if k in self._flags:
                    self._flags[k] = v

    def get_all_flags(self) -> List[str]:
        return list(self._flags.keys())

    def get_flag_mode(self, flag: str) -> FeatureMode:
        return self._flags.get(flag, FeatureMode.OFF)

    def set_flag_mode(self, flag: str, mode: FeatureMode) -> None:
        if flag in self._flags:
            self._flags[flag] = mode

    def is_enabled(self, flag: str) -> bool:
        return self._flags.get(flag) in (FeatureMode.ON, FeatureMode.STRICT)

    def is_shadow(self, flag: str) -> bool:
        return self._flags.get(flag) == FeatureMode.SHADOW

    def serialize(self) -> Dict[str, str]:
        return {k: v.value for k, v in self._flags.items()}
