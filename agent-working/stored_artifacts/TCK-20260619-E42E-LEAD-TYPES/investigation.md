---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260619-E42E-LEAD-TYPES
artifact_type: investigation
tags: [information-seeking, lead-kind, person-lead, concept-lead, phase-4]
---

# Investigation — TCK-20260619-E42E-LEAD-TYPES

## Topic
Epic 4.2E — PERSON and CONCEPT Lead Types

## Current State

### LeadState.kind (src/core/strategic.py L191)
`kind: str  # 'location', 'object', 'event', 'person'`

Raw string with no formal enum. The comment lists four kinds but omits "concept".
No type safety, no exhaustive dispatch.

### Read Sites (all use raw string comparisons)
- `src/systems/strategic_systems/detour.py` — `lead.kind == "location"` (3 sites)
- `src/systems/strategic_systems/intelligence.py` — `lead.kind == "location"` (2 sites)
- `src/systems/strategic_systems/belief.py` — `lead.kind == "event"` (1 site)
- `src/systems/strategic_systems/redirection.py` — `lead.kind == 'location'` (1 site)
- `src/ai/goals/scorers.py` — `lead.kind == 'location'` (1 site)
- `src/engine/pipeline_phases/lead_contradiction.py` — `lead_kind == "resource"/"location"/"person"/"information"` (4 checks)
- `src/replay/fingerprint.py` — `f"{lead.kind}:"` (used as serialised string)
- Construction sites: `src/strategy/leads.py`, `src/town/guild.py`, `src/engine/pipeline_phases/paid_information.py`, `src/world/providers/information.py`, `src/domains/information/normalizer.py`, `src/systems/strategic_systems/belief.py`, `src/certification/scenarios.py`, `src/perf/scenarios.py`
- Test construction: ~25 files, all use string literals like `kind="location"`

### Migration Strategy
`LeadKind(str, Enum)` inherits from `str`, so `lead.kind == "location"` continues
to evaluate to True when `lead.kind` is `LeadKind.LOCATION`. All existing read
sites require **no changes** — the string value is preserved. Only construction
sites that pass raw strings need updating where enforced, but since `LeadKind`
accepts `LeadKind("location")` at runtime (str subclass), even those are
backward-compatible. We update the canonical construction paths; test files can
remain as-is (str coercion works fine via `LeadKind(kind_str)`).

### PERSON lead routing
`_is_lead_contradicted` in `lead_contradiction.py` already handles `lead_kind == "person"`:
it tries `int(subject)` to find an entity_id. The routing logic (navigate to
last-known position of target) is a **detour/goal-scorer** concern. The
`DetourSuggestionSystem._infer_objective_kind` currently falls through to
`"investigate"` for non-material/non-access/non-inventory/non-danger blockers.
We need to wire PERSON leads to emit `REACH_ENTITY` (a new `ObjectiveKind` or
reuse `INVESTIGATE`) objective kind.

### CONCEPT lead routing
CONCEPT leads ("seeking domain knowledge, e.g. alchemy_recipe") should route
to the nearest `InformationProvider` whose `knowledge_domains` includes the
concept domain. The `InformationProviderState` in `src/domains/information/providers.py`
already has `knowledge_domains: Tuple[str, ...]`. The `PaidInformationTransactionSystem`
already handles INFORMATION_SEEKING projects locating a provider. CONCEPT lead
routing is a new `LeadKind.CONCEPT` path in `DetourSuggestionSystem._infer_objective_kind`
and `_subjects_match` that maps concept subject → `ASK_INFORMATION` objective.

### Routing Implementation Location
`src/engine/domain/lead_routing.py` (new file) — pure static class
`LeadRoutingSystem` following the pattern of `cognition_extras.py` and
`lead_contradiction.py`. Called by detour/cognition layer to produce
`ObjectiveKind` and `target` for PERSON and CONCEPT leads.

### Existing Tests
`tests/unit/cognition/test_information_seeking.py` — 500+ lines, covers
InformationNeedDetector, PaidInformationTransaction, LeadContradiction, etc.
The acceptance criteria names two new tests:
- `test_person_and_concept_lead_types_accepted`
- `test_person_lead_routes_entity_to_provider`

## Findings
1. `LeadKind` as `str, Enum` is a pure additive change — no migration of
   callers needed (str identity preserved).
2. PERSON and CONCEPT routing can be pure decision logic (no authoritative
   mutation) — returns `ObjectiveKind` string + `target` string.
3. `ObjectiveKind.INVESTIGATE` is the correct fallback for PERSON leads
   (navigate to subject entity_id's last-known position).
4. `ObjectiveKind.ASK_INFORMATION` is the correct target for CONCEPT leads
   (matches existing INFORMATION_SEEKING project objective).
5. No new pipeline phase needed — routing is read-only decision logic in a
   new `LeadRoutingSystem` helper + wired into `DetourSuggestionSystem`.
