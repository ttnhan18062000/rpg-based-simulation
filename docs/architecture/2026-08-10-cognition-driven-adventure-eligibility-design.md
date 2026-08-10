---
status: active
layer: architecture
authority: P1
audience: developer
last_verified: 2026-08-10
---

# Cognition-Driven Adventure Eligibility & Generic Interruption Bypass — Design

## Context

`TCK-20260810-COMBAT-BRAVERY-QUARTILE-ENGAGEMENT-INVERSION`'s investigation (see
`stored_artifacts/TCK-20260810-COMBAT-BRAVERY-QUARTILE-ENGAGEMENT-INVERSION/investigation.md`)
traced a failing test through three compounding, confirmed root causes, all rooted in the same
underlying gap: two independent strategic-decision systems compete for the same
`entity.strategic.current_project_id` field using hardcoded, non-generalizable rules.

**System A — `AdventureDecisionPhase`** (`src/domains/adventure/`): hero-only route selection
(recover, craft, train, quest, scout, trade, socialize). Gated today on a hardcoded
`entity.identity.role == EntityRole.HERO` check, nothing else.

**System B — `StrategicIntelligenceSystem`/`GoalRegistry`** (`src/systems/strategic_systems/
intelligence.py`, `src/ai/goals/`): the universal baseline — survival, combat, social, recovery
goals for every entity, always.

Confirmed via direct source + content read that a real, already-authored, but completely inert
extension point already exists for exactly this kind of per-race/faction behavioral variation:
`RaceDefinition.cognition_profile` (content: `data/content/living/races.yaml`) references a
`CognitionProfileDefinition` (content: `data/content/living/cognition_profiles.yaml`) — e.g.
`elf → arcane_scholar`, `human → practical_humanoid`, `wolf → instinctive_animal`. This reference
is threaded through entity construction as `entity.identity.properties["cognition_profile_id"]`
but is **never read again** — `CapacityService.derive_profile()` (the function that computes the
live `CognitionProfile` governing interruption-resistance math) only reads raw numeric
`intelligence`/`wisdom` attributes, ignoring the qualitative profile entirely.

This design wires that dormant mechanism up properly, replacing two hardcoded rules (`HERO` role
gate; `"danger"`/`"detour"` kind-string bypass allowlist) with generalized, cognition-profile- and
score-driven ones.

## Goals

1. Adventure-routing eligibility becomes a property of how an entity thinks (`cognition_profile`),
   not a hardcoded role check — any sufficiently cognitively-capable race/faction (elf, human,
   dwarf, ...) can be adventure-eligible; instinctive/simple races (wolf, slime, ...) never are,
   regardless of role.
2. The interruption-resistance lock-bypass mechanism becomes score/urgency-driven, not a
   hardcoded allowlist of specific `kind` strings — any sufficiently urgent goal, from either
   system, present or future, can interrupt routine activity without new code.
3. Zero behavioral regression for the current corpus (verified: `human`/`practical_humanoid` is
   the only race compatible with the `hero` role today, so marking `practical_humanoid` eligible
   preserves exactly today's real behavior for every existing hero).
4. The historical dormant-wiring pattern (this is the third instance found this session — see
   `HUNT_WEAK_ENEMY` dead route generation, `GoalKind`/`ProjectKind` vocabulary split, and this
   `cognition_profile` gap) gets documented once, durably, so it isn't rediscovered from scratch
   again.

## Non-goals

- Full per-race scoring-coefficient customization (personality-bias weights, risk multipliers) —
  scoped out; this design only touches eligibility and interruption bypass, not the scoring
  formulas themselves.
- Migrating `AdventureDecisionPhase`'s own 14 non-combat route families into `GoalRegistry`
  scorers — a much larger, separate effort (see investigation.md's own effort estimate: 1,089
  lines, a live REST API surface, 27 test files, 2 additional dependent domains).
- Reviving `RouteFamily.HUNT_WEAK_ENEMY`'s dead generator logic — would create a second, redundant
  combat-decision path duplicating what `GoalRegistry` already correctly owns (see investigation's
  own historical-confirmation section).

## Design

### 1. Schema — `CognitionProfileDefinition` gains one new field

`supports_adventure_routing: bool = False` (`src/content/schema.py`). Explicit, directly authored
per profile — not derived from existing qualitative fields (`planning_depth`, `abstraction`,
etc.), which remain descriptive-only. Content authoring for the 7 existing profiles:
`practical_humanoid`, `arcane_scholar` → `True` (matches current hero-eligible behavior and the
elf/human parity example); `instinctive_animal`, `opportunistic_humanoid`, `undead_fixated` →
`False`; `disciplined_guard`/`trade_pragmatist` → resolved during Implement based on real usage
(not yet referenced by any race in `races.yaml`, need to check other content sources before
assigning).

### 2. `AdventureDecisionPhase` eligibility

Resolve the entity's `cognition_profile_id` (already present in `entity.identity.properties`) to
its real `CognitionProfileDefinition` via the catalog, and check `supports_adventure_routing`
instead of (or in addition to — a real Implement-phase decision once the resolution code is
written and its interaction with the existing `EntityRole.HERO` filter is visible) the current
hardcoded role check.

### 3. Generic interruption bypass

`StrategicIntelligenceSystem.evaluate_project_switch()` (`intelligence.py:881-932`) currently:

```python
if current.lock_until_tick > current_tick:
    if (candidate_project.kind == "danger" and candidate_project.score > 80) or candidate_project.kind == "detour":
        pass
    else:
        return None
```

Generalizes to: keep `"detour"` as the one true **unconditional structural bypass** (a genuinely
different semantic category — an immediate situational override, not a competing prioritized
goal). Replace the `"danger" and score > 80` special case with a **generic rule**: any candidate
project, from either system, whose `score` clears both the current project's existing
`effective_current_score` (`current.score + retention_margin`, unchanged) *and* a real urgency
floor, may bypass an active lock — regardless of its `kind`. This is a direct generalization of
the code's own existing pattern (a numeric floor already gates the `"danger"` case specifically)
to the case-general form, not a new invented concept. The exact floor value is a calibration
detail for Implement (same spirit as `TCK-20260619-E11D-SCORING-CAL`'s own empirical bravery-
coefficient calibration), not a design-level decision — both systems' `ProjectState.score` fields
are already directly comparable today (used in the existing non-locked switch path), so no new
score-normalization is needed.

### 4. Documentation (durable, not per-ticket)

- Extend `docs/mechanics/04_strategic_cognition.md` with the real eligibility + generalized-bypass
  mechanism as authoritative goal-hierarchy content.
- Update `docs/simulation/domains/adventure_contract.md`'s eligibility table (today: role/alive/
  active/lock only).
- New parity ledger entries in `docs/parity_ledger/strategic_cognition.yaml`.
- New `docs/audits/D22_dormant_content_wiring.md` — a durable record of this session's 3 confirmed
  dormant-wiring findings (`HUNT_WEAK_ENEMY` dead route generation, `GoalKind`/`ProjectKind`
  vocabulary split between the two systems, `cognition_profile` inert-until-now), so a future
  investigation can find this in one place instead of re-deriving it via bisection and source
  archaeology, matching the existing D-numbered audit convention (`D06`, `D19`, `D20`, `D21`).

## Testing

- New unit tests: `cognition_profile_id` → `CognitionProfileDefinition` resolution →
  `supports_adventure_routing` eligibility check (positive: elf/human; negative: wolf).
- New unit tests for the generalized bypass: a high-score candidate of a novel/synthetic `kind`
  (not `"danger"`, not `"detour"`, not `"combat_engage"`) correctly bypasses a lock when it clears
  the urgency floor — proves the generalization actually works for kinds the allowlist never knew
  about, not just for `combat_engage` specifically.
- Regression: `tests/integration/scenarios/test_entity_differentiation.py::
  test_bravery_quartile_combat_rate_2x` — the original failing test. Also address the small-N
  quartile-collapse finding (investigation finding 1) as part of Test, since the fix alone doesn't
  guarantee the test's own `q_size=1`-after-deaths fragility won't still produce noise.
- Scoped suite: `tests/unit/strategic/`, `tests/unit/domains/adventure/`,
  `tests/integration/scenarios/`, `tests/unit/content/` (schema change).

## Rollout risk

Low for existing corpus behavior: confirmed only `human`/`practical_humanoid` is compatible with
the `hero` role in current content, so marking it eligible is behavior-preserving by construction.
`GoalRegistry`'s own universal scope is unchanged (still runs for every entity, always) — this
design only adds eligibility-gating to System A's own enrichment layer, a strict superset
expansion for any future race/role combination, never a removal of existing behavior.
