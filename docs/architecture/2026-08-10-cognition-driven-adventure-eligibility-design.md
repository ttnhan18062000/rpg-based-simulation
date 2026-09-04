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
extension point already exists for exactly this kind of per-species/faction behavioral variation:
`SpeciesDefinition.cognition_profile` (content: `data/content/living/species.yaml`) references a
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
   not a hardcoded role check — any sufficiently cognitively-capable species/faction (elf, human,
   dwarf, ...) can be adventure-eligible; instinctive/simple species (wolf, slime, ...) never are,
   regardless of role.
2. The interruption-resistance lock-bypass mechanism becomes score/urgency-driven, not a
   hardcoded allowlist of specific `kind` strings — any sufficiently urgent goal, from either
   system, present or future, can interrupt routine activity without new code.
3. Zero behavioral regression for the current corpus (verified: `human`/`practical_humanoid` is
   the only species compatible with the `hero` role today, so marking `practical_humanoid` eligible
   preserves exactly today's real behavior for every existing hero).
4. The historical dormant-wiring pattern (this is the third instance found this session — see
   `HUNT_WEAK_ENEMY` dead route generation, `GoalKind`/`ProjectKind` vocabulary split, and this
   `cognition_profile` gap) gets documented once, durably, so it isn't rediscovered from scratch
   again.

## Non-goals

- Full per-species scoring-coefficient customization (personality-bias weights, risk multipliers) —
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
`False`. **Implement checklist item:** `disciplined_guard`/`trade_pragmatist` are not referenced
by any species in `species.yaml` today (checked directly) — before assigning them a value, search all
of `data/content/` for any other real reference (NPC templates, hero archetypes, etc.) so the
value isn't a guess.

### 2. `AdventureDecisionPhase` eligibility

Resolve the entity's `cognition_profile_id` (already present in `entity.identity.properties`) to
its real `CognitionProfileDefinition` via the catalog, and check `supports_adventure_routing`
**in place of** the current hardcoded `EntityRole.HERO` check, not in addition to it — Goal 1's
own "regardless of role" language is a hard requirement, not an aspiration: a cognitively-capable
non-hero entity (e.g. a non-hero `human`/`practical_humanoid`) must be as eligible as a hero one.
The other 3 existing eligibility criteria in `docs/simulation/domains/adventure_contract.md`'s
own table (alive, active, project-lock-expired) are retained unchanged — only the role/cognition
axis changes.

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
coefficient calibration), not a design-level decision.

> **Open question for Investigate (real, confirmed scale mismatch — not yet resolved):**
> `docs/mechanics/04_strategic_cognition.md` §6.6 documents System A's own real score range as
> **max ≈2.9** (non-blocked). System B's `CombatEngageScorer` utility reaches **100**
> (`40 + bravery×40 + stamina_ratio×20`), and the existing `"danger"` bypass floor is `score > 80`
> — clearly calibrated against System B's own scale, not System A's. Both systems' raw
> `ProjectState.score` values ARE already compared directly today in the normal (unlocked)
> `evaluate_project_switch()` path, but given this scale gap, that comparison is almost certainly
> already lopsided in practice (any System B goal trivially outscores any System A route). Also:
> `AdventureDecisionPhase.apply()` itself never calls `evaluate_project_switch()` at all — on its
> own re-evaluation, once unlocked, it unconditionally overwrites `current_project_id` with no
> score comparison against whatever is currently active, which is the real mechanism behind
> System A "always winning" the moment its own lock expires (not a scoring contest, an
> unconditional overwrite). Both of these need direct, empirical confirmation in Investigate
> before deciding whether the generic bypass rule needs score *normalization* (e.g., percentage-
> of-observed-max per system) rather than a raw cross-system comparison, and whether
> `AdventureDecisionPhase` itself also needs to start respecting `evaluate_project_switch()`'s own
> retention logic (a second, related asymmetry, not just the bypass allowlist) to make the fix
> actually symmetric between the two systems.

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

**Eligibility side**: low for existing corpus behavior. Confirmed only `human`/`practical_humanoid`
is compatible with the `hero` role in current content, so marking it eligible is behavior-
preserving by construction. `GoalRegistry`'s own universal scope is unchanged (still runs for
every entity, always) — this design only adds eligibility-gating to System A's own enrichment
layer, a strict superset expansion for any future species/role combination, never a removal of
existing behavior.

**Bypass side**: a real, deliberate behavior tightening, not risk-free. The generalized rule adds
a condition the current `"danger"` case doesn't have — a `"danger"`-kind candidate scoring >80
today bypasses unconditionally; under the new rule it must *also* clear
`effective_current_score`. This is intentional (a `"danger"` project that scores below the
current project's own retention-adjusted score arguably shouldn't preempt it either), but it
means a corpus scenario that currently relies on unconditional `"danger"` bypass could see
different behavior post-fix. Test must explicitly verify existing `"danger"`-bypass scenarios
(score > 80) still resolve the same way under the dual-condition rule, not just that the new
generalized case works.
