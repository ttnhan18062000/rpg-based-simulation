---
status: active
layer: architecture
authority: P1
audience: agent
tags: [cognition, strategy, documentation]
---

# D22 — Dormant Content Wiring

**Ticket:** TCK-20260810-D22-DORMANT-WIRING-AUDIT
**Date:** 2026-08-10

## Purpose

`TCK-20260810-COMBAT-BRAVERY-QUARTILE-ENGAGEMENT-INVERSION`'s investigation
(`staging_artifacts/TCK-20260810-COMBAT-BRAVERY-QUARTILE-ENGAGEMENT-INVERSION/investigation.md` —
that ticket is still open/in `tickets/inprogress/` as of this writing, so the source material has
**not** yet moved to `stored_artifacts/`; cite the `staging_artifacts/` path above until it does)
surfaced a recurring pattern while tracing a failing quartile-engagement test: real, authored,
tested wiring that sits dormant because nothing downstream ever reads it, alongside real,
authored, tested vocabulary that never got exercised because the code path that would exercise it
was never called. Three distinct instances of this pattern were found in that single
investigation. This document records all three durably, following the D21 narrative convention,
so a future investigation does not have to re-derive them from scratch via bisection and source
archaeology.

Three follow-on tickets were spawned from the same investigation to close (or, in one case,
deliberately not close) each finding:

- `TCK-20260810-COGNITION-PROFILE-ADVENTURE-ELIGIBILITY` (**C1**) — DONE
- `TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION` (**C2**) — landed (see status caveat below)
- `TCK-20260810-COGNITION-ELIGIBILITY-BYPASS-DOCS` (**C3**) — DONE

This document is authored last in that batch (`TCK-20260810-D22-DORMANT-WIRING-AUDIT`, **C4**) so
that each finding's status reflects the real, landed state of C1/C2/C3 — not a forecast made when
the parent investigation was still in progress.

**Status caveat on C2**: `tickets/done/TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION.md`'s own
body `## Status` field still reads `INPROGRESS` even though the file lives under `tickets/done/`
with all 5 Acceptance Criteria checked `[x]` and a filled-in Completion Summary. This document
treats C2's code as landed (verified directly against the real source below), consistent with the
file's location and completed checklist, and flags the stale `## Status` field as a hygiene gap
for that ticket rather than silently treating C2 as unfinished.

## Summary table

| Finding | Location | Status |
|---|---|---|
| `HUNT_WEAK_ENEMY` dead route generation | `src/domains/adventure/mapper.py:37`, `src/domains/adventure/generator.py` | **Open, documented not fixed** (explicit non-goal) |
| `GoalKind`/`ProjectKind` vocabulary split | `src/core/strategic.py:121-148`, `src/systems/strategic_systems/intelligence.py`'s `evaluate_project_switch()` | **Fixed differently** — worked around, not unified |
| `cognition_profile` inert-until-fixed gap | `src/strategy/cognition_capacity.py`'s `CapacityService.derive_profile()`, `src/content/schema.py` | **Fixed** — via a different function than originally scoped |

---

## `HUNT_WEAK_ENEMY` dead route generation

**Status: open, documented not fixed.**

`RouteFamily.HUNT_WEAK_ENEMY` (`src/domains/adventure/schema.py:23`) is a fully real, wired-up
route family everywhere *except* the one place that would actually produce it:

- `src/domains/adventure/mapper.py:37` — `RouteToProjectMapper._MAP` maps
  `RouteFamily.HUNT_WEAK_ENEMY → (ProjectKind.COMBAT, ObjectiveKind.DEFEAT_ENEMY)`, a real,
  correct entry.
- `src/domains/adventure/scoring.py:49,125-126,241,243` — `AdventureRouteScorer` has real scoring
  logic that boosts `HUNT_WEAK_ENEMY` routes for `GUARD`-role entities and for
  `WARRIOR`+`MAGE` party compositions.
- `src/domains/adventure/generator.py` — **zero references to `HUNT_WEAK_ENEMY` anywhere in the
  file.** `AdventureRouteGenerator.generate()` only ever constructs `RouteFamily.RECOVER`,
  `ASK_INFORMATION`, `FORM_PARTY`, and `DEFER_WITH_REASON` options directly, plus a
  `_OPPORTUNITY_FAMILY_MAP` covering `gather_resource`/`buy_item`/`craft_item`/`repair_gear`/
  `ask_information`/`rest_inn` — no combat-hunting family is ever emitted.

**Re-verified this session** (2026-08-10, after C1 and C2 both landed and touched
`mapper.py`/`generator.py`-adjacent files): the `grep` for `HUNT_WEAK_ENEMY` across `src/` still
returns only `mapper.py:37` (the mapping entry), `scoring.py` (scoring logic), and `schema.py:23`
(the enum member) — `generator.py` is still confirmed to have **zero** references. Neither C1 nor
C2 touched this dead path; both worked entirely within `AdventureDecisionPhase`'s eligibility
gate and `StrategicIntelligenceSystem.evaluate_project_switch()`'s bypass logic respectively,
neither of which is upstream or downstream of route *generation* itself.

**Why this stays open, deliberately**: the design doc that spawned C1/C2/C3
(`docs/architecture/2026-08-10-cognition-driven-adventure-eligibility-design.md`) explicitly lists
this as a **non-goal**:

> Reviving `RouteFamily.HUNT_WEAK_ENEMY`'s dead generator logic — would create a second, redundant
> combat-decision path duplicating what `GoalRegistry` already correctly owns (see investigation's
> own historical-confirmation section).

`GoalKind.COMBAT_ENGAGE` (`src/ai/goals/`, System B) is the real, live combat-decision path
corpus-wide; wiring `HUNT_WEAK_ENEMY` into the generator would build a second, competing combat
decision inside System A (`AdventureDecisionPhase`) that duplicates System B's job. This is a
considered design decision, not an oversight — it is recorded here so a future investigator who
finds the same dead code doesn't re-open it as a "bug" without first reading this rationale.

## `GoalKind`/`ProjectKind` vocabulary split

**Status: fixed differently than a naive fix would.**

`src/core/strategic.py` defines two separate `str, Enum` classes with **overlapping string
values**:

```python
class GoalKind(str, Enum):        # lines 121-133
    HARVESTING = "harvesting"
    ...
    SOCIAL = "social"
    ...

class ProjectKind(str, Enum):     # lines 135-148
    HARVESTING = "harvesting"
    ...
    SOCIAL = "social"
    ...
```

`ProjectKind.HARVESTING`/`ProjectKind.SOCIAL` and `GoalKind.HARVESTING`/`GoalKind.SOCIAL` share
identical string values but are distinct Python enum classes, produced by two independent
systems: System A (`AdventureDecisionPhase` → `RouteToProjectMapper`, always emits real
`ProjectKind` members) and System B (`GoalRegistry`-sourced candidates in
`StrategicIntelligenceSystem`, always emits real `GoalKind` members). This split meant
`StrategicIntelligenceSystem.evaluate_project_switch()`'s lock-bypass gate (originally
`intelligence.py:881-935`, a hardcoded `kind=='danger' and score>80` / `kind=='detour'`
allowlist) had no principled way to compare or normalize a candidate's `kind` across the two
systems.

**What C2 actually landed** (verified directly against `src/systems/strategic_systems/
intelligence.py`, current source, not the ticket's paraphrase): a module-level
`_score_scale_max(kind)` helper (`intelligence.py:89-107`) that classifies which system produced
a `kind` via `isinstance(kind, ProjectKind)` — **actual Python enum class identity, not string
value** — because a value-based check would silently misclassify the two overlapping members
(`HARVESTING`/`SOCIAL`). `evaluate_project_switch()`'s bypass gate now: keeps `kind=="detour"` as
the sole unconditional structural bypass, and for any other candidate requires its score
(normalized as a percentage of its own system's declared max — `_ADVENTURE_ROUTE_SCORE_MAX=2.9`
for `ProjectKind`, `_GOAL_UTILITY_SCORE_MAX=100.0` for anything else) to both exceed the current
project's own normalized effective score and clear an `_INTERRUPTION_URGENCY_FLOOR_PCT=0.8`
floor, regardless of `kind`.

**This works around the split, not through it.** The helper's own docstring says so directly:

> Does not unify or alter the ProjectKind/GoalKind vocabulary split (out of scope, tracked under
> D22/C4) — it only reads the enum identity already present at each `ProjectState` construction
> site.

C2's own `plan.md` (`stored_artifacts/TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION/plan.md`)
has an explicit `## Scope Guards` section: "Do not touch `GoalKind`/`ProjectKind` vocabulary
unification. ... Do not ... introduce a `ProjectKind`/`GoalKind` common base or rename either
enum's members." C2's own ticket Out of Scope section
(`tickets/done/TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION.md`) does not list unification
explicitly, but its Related Code Areas and plan-level Scope Guards make clear the two enums were
deliberately left untouched — `strategic.py:121-148` is byte-identical to before C2 landed.

**Conclusion**: the vocabulary split itself is still real and still open. C2 closed the
*consequence* that mattered for the failing test (the bypass gate's inability to fairly compare
cross-system candidates) by classifying on enum identity instead of unifying the enums — a
narrower, lower-risk fix that avoids a much larger refactor (renaming/merging two enums with
overlapping values used throughout `src/core/strategic.py`, `src/domains/adventure/`, and
`src/ai/goals/`). "Fixed" in C2's own Acceptance Criteria means "the bypass gate now works
correctly across both systems," not "the two enums were unified" — those are different claims,
and only the first one is true today.

## `cognition_profile` inert-until-fixed gap

**Status: fixed** — via a different code path than the ticket's own Scope description names.

Before C1, `RaceDefinition.cognition_profile` (content: `data/content/living/races.yaml`)
resolved to a `CognitionProfileDefinition` (content: `data/content/living/cognition_profiles.yaml`)
and was threaded through entity construction as
`entity.identity.properties["cognition_profile_id"]` — but nothing downstream ever read it back.
`CapacityService.derive_profile()` (`src/strategy/cognition_capacity.py:15-30`) computed the live
`CognitionProfile` governing interruption-resistance math purely from raw numeric
`entity.attributes`/`entity.identity.personality`/`entity.biological` fields — no reference to
`cognition_profile_id` anywhere in the function or the file.

**Re-verified directly this session, post-C1**: `src/strategy/cognition_capacity.py` is
**unchanged by C1** — `CapacityService.derive_profile()` still only reads `attrs`, `personality`,
and `bio`; it still does not read `entity.identity.properties["cognition_profile_id"]` anywhere.
C1's own Scope/Related Code Areas list this file, which could read as "the fix touched
`derive_profile()`" — it did not. **C1 wired the field through a different path entirely**:

- `src/content/schema.py:101` — `CognitionProfileDefinition` gained
  `supports_adventure_routing: bool = Field(False)`.
- `src/engine/behavior_consumers.py` — gained `get_cognition_profile_definition()`/
  `get_role_definition()` catalog accessors (following the existing `get_perception_gate()`
  singleton pattern).
- `src/domains/adventure/phase.py:52-96` (module-level, not inside `CapacityService`) — new
  `_resolve_cognition_profile_id()` (3-tier fallback: explicit `cognition_profile_id` → `role_id`
  → `RoleDefinition.default_cognition_profile` → legacy `EntityRole.HERO` → `"hero"` role's own
  default) and `_supports_adventure_routing()` (a cache-backed eligibility predicate, keyed by
  profile id so the catalog is hit at most once per distinct profile per tick, not once per
  entity).
- `AdventureDecisionPhase.apply()`'s own hero-eligibility filter (`phase.py:129`) now calls
  `_supports_adventure_routing(e, _profile_eligibility_cache)` in place of the previous hardcoded
  `entity.identity.role == EntityRole.HERO` check.

In other words: the dormant `cognition_profile_id` field is now read and acted on — but by
`AdventureDecisionPhase`'s own routing-eligibility gate, not by `CapacityService.derive_profile()`
(which still governs a different, unrelated concern: interruption-resistance/project-capacity
limits, still purely attribute-driven). The gap this finding names — "a real, authored,
threaded-through field that nothing ever reads" — is genuinely closed for the *adventure-routing
eligibility* consumer. `CapacityService.derive_profile()` itself remains exactly as
attribute-driven as before; if a future ticket wants cognition-profile-aware interruption
resistance specifically, that is a distinct, still-open piece of work, not something C1 already
did.

---

## Related Docs

- `docs/audits/D19_domain_phase_inventory.md`
- `docs/audits/D20_simq_integration.md`
- `docs/audits/D21_entity_lifecycle_foundation_layers.md` (structural template for this document)
- `docs/architecture/2026-08-10-cognition-driven-adventure-eligibility-design.md` (the design doc
  that names all 3 findings and spawned C1/C2/C3/C4)
- `docs/mechanics/04_strategic_cognition.md` (goal hierarchy, interruption resistance — the
  authoritative mechanics both C1 and C2 extend)
- `docs/simulation/domains/adventure_contract.md` (System A eligibility table, updated by C3)
- `docs/guidelines/intentional_divergences.md` §2.40 (C2's Interruption-Bypass Generalization
  entry)
- `docs/parity_ledger/strategic_cognition.yaml` (STRAT-185/186/187, STRAT-243 — C1/C2's parity
  entries)
- `staging_artifacts/TCK-20260810-COMBAT-BRAVERY-QUARTILE-ENGAGEMENT-INVERSION/investigation.md`
  (origin of all 3 findings; still in `staging_artifacts/` since the parent ticket has not closed)
- `stored_artifacts/TCK-20260810-COGNITION-PROFILE-ADVENTURE-ELIGIBILITY/` (C1's plan/investigation/test_plan)
- `stored_artifacts/TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION/` (C2's plan/investigation/test_plan)
- `tickets/done/TCK-20260810-COGNITION-PROFILE-ADVENTURE-ELIGIBILITY.md`
- `tickets/done/TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION.md`
- `tickets/done/TCK-20260810-COGNITION-ELIGIBILITY-BYPASS-DOCS.md`
