---
ticket_id: TCK-20260612-DOMAINS-ARCH-MAP
phase: investigation
---

# Investigation: Domains Architecture Map

## Domain File Inventory (actual counts)

| Domain | py files | Key files |
|---|---|---|
| adventure | 7 | generator, mapper, phase, resolver, schema, scoring, service |
| campaigns | 10+__init__ | behavior_change, classifier, diversity, forbidden, reports, runner, schema, scorecard, spec, __init__ |
| combat_engagement | 10 | learning, perception, phase, reassessment, resolver, risk_evaluator, schema, selector, self_estimate, service |
| commitment | 5 | abandonment, impact, pressure, reputation + __init__ |
| cooperation | 7 | evaluators, events, phase, postures, providers, services |
| emotion | 5 | emotion_service, habit_service, opportunity_cost, recovery_service |
| information | 10 | assimilation, bridge, contradiction, normalizer, phase, resolver, route_impact, router, schema, trust |
| memory | 3 | attribution, phase, spatial_update |
| motivation | 4 | evaluator, resolver, service, filter |
| optimization | 10 | budget_manager, cache_strategy, degradation, diagnostics, dirty_scheduler, feature_flags, memory_limits, provider_enforcement, rollout_profiles, trace_governor |
| perception | 4 | filter, phase, salience, service |
| progression | 9 | gaps, generator, interpretation, ledger, phase, possession, resolver, schema, selector, service |
| time | 1 | service |
| world_emergence | 5 | aggregators, models, phase, schema, services |

## Phase Associations (from schema docstrings)
- combat_engagement: Phase 4 (pre-combat assessment)
- information: Phase 5 (belief/information schemas)
- campaigns: Phase 9 (campaign lifecycle)
- optimization feature_flags: Phase 10 (feature rollout control)

## Key Technical Findings

### combat_engagement
- CombatPosture enum (10 values): IGNORE, WATCH, AVOID, PROBE, THREATEN, ENGAGE, SKIRMISH, CALL_HELP, RETREAT, PANIC_FLEE
- CombatEngagementDecisionService.evaluate(actor, target, state) — reads EntityState and AuthoritativeState; returns CombatEngagementDecisionResult
- Sub-services: OpponentPerceptionService, SelfCombatEstimateService, EngagementRiskEvaluator, CombatPostureSelector
- Read-only: reads state, does NOT mutate AuthoritativeState

### information
- SourceTrustUpdateService: trust values clamped to [0.0, 1.0]; outcomes: CONFIRMED, PARTIALLY_CONFIRMED, CONTRADICTED, NOT_VERIFIABLE
- InformationSourceKind enum: GUIDE, GUILD, BLACKSMITH, TRAVELER
- Sub-services: assimilation, contradiction, normalizer, router (routes information to appropriate processor), bridge (bridges to core.strategic)
- Reads KnowledgeFact and LeadState from core.strategic

### campaigns
- CampaignRunner orchestrates multi-tick campaigns (runs Kernel ticks internally)
- Sub-analyzers: LifeArcClassifier, BehaviorChangeProofDetector, RouteDiversityAnalyzer, CampaignScorecardEvaluator, ForbiddenBehaviorDetector
- Uses DeterministicRNG for reproducibility
- Output: CampaignResult with EntityArcReport and WorldArcReport

### optimization
- DegradationLevel enum: NORMAL, CONSTRAINED, DEGRADED, CRITICAL
- GracefulDegradationManager: monitors tick_time_ms/limit_ms ratio; thresholds — CRITICAL ≥1.0, DEGRADED ≥0.95, CONSTRAINED ≥0.8
- CacheStrategy: LRU eviction, bounded max_size (default 100), CacheKey (region_id, query_type, extra_param)
- FeatureFlagManager: FeatureMode enum (OFF/SHADOW/ON/STRICT); flags include ENABLE_COMBAT_ENGAGEMENT, ENABLE_BELIEF_ASSIMILATION, ENABLE_PROGRESSION_EVOLUTION, etc.

## Existing Coverage
- docs/architecture/cognition_domain_ownership.md: maps CognitionModel sub-components → domain packages (perception, time, memory, motivation, commitment, cooperation)
- docs/strategy/ bounded_cognition contracts: cover strategy/cognition layer — cross-link, do not duplicate
- No existing docs for: combat_engagement, information, campaigns, optimization, adventure, emotion, progression, world_emergence

## Risks
- optimization domain is cross-cutting (called by many other domains); its contract must clarify it is advisory/utility, not authoritative
- campaigns domain runs the Kernel internally — important boundary: campaigns are analysis/testing, not primary tick execution
