# Verification Audit: Open Questions

1. **Authoritative Personality Model**: The latest design spec (`2026-04-07-personality-relationships-design.md`) references the **OCEAN** (Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism) system. However, the current implementation in `MindAspect` and `SocialAppraisalService` uses a discrete **RPG Trait** system (`aggression`, `greed`, `caution`, `loyalty`, etc.). 
   - **Question**: Should I pivot the implementation toward OCEAN (breaking existing integrations like `SocialAppraisalService`), or should I align the documentation and broken tests (`test_person_logic.py`) with the current stabilized RPG Trait system?

2. **Missing Goal Scorer Helpers**: The regional awareness tests (`test_region_events.py`) are broken because `_current_region_difficulty` and `_region_danger_penalty` have been removed from `src/ai/goals/scorers.py`.
   - **Question**: Should I restore these helpers to use the Phase 4 `region_consequence_registry`, or has this logic been superseded by a different mechanism?
