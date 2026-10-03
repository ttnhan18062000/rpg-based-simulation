---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260903-INFORMATION-HUB-ACCUMULATION
artifact_type: plan
tags: [information, feature-flags, faction]
---

# Implementation Plan — TCK-20260903-INFORMATION-HUB-ACCUMULATION

## Summary

This plan adopts investigation's option **(b)**: build the accumulation mechanism and the
City-to-City/City-to-Country propagation mechanism as real, typed-update-path code, proven via
direct unit-level construction (`AuthoritativeState`/`StateUpdate`/`ApplyPath.apply_generation`),
without requiring either to be reachable from a real corpus-world run today. It does **not** seed
`InformationProviderState`, does **not** build a building→provider lookup, and does **not** build
any Guide-to-Guide/hub-to-hub exchange mechanism — all three stay explicitly out of scope and are
disclosed, not silently assumed away, matching this session's established
Coming-of-Age/Clan-Lifecycle/Economic-Vacancy-Signal precedent for a documented inertness gap.

**A new, more severe blocking finding beyond the investigation's own text**: direct read of
`src/engine/apply.py:396-452` (`ApplyPath.apply_generation`'s `new_state = AuthoritativeState(...)`
constructor call) shows `information_providers` is never passed as a keyword argument there — unlike
`factions=new_factions` and `clans=new_clans`, which sit two lines above it (apply.py:446-447) and
both correctly carry-forward-and-merge their durable dicts first. Because
`AuthoritativeState.information_providers` has `field(default_factory=dict)`
(`src/core/state.py:1237`), omitting it from the constructor call means it silently resets to `{}`
on **every single tick apply** — discarding both `prior_state.information_providers` and
`update.information_providers_update`, regardless of what wrote to either. This means even the
existing, `status: verified` `STRAT-230` decrement path
(`src/engine/pipeline_phases/lead_contradiction.py`) has never actually survived a tick boundary in
any real run; it has only ever been observed by tests that call `LeadContradictionSystem.enforce()`
directly and assert on the returned `StateUpdate`, not through the full apply path. This is not
"building a seeding pipeline" (out of scope) — it is completing the wiring for an already-declared
typed update field, the same class of fix the `factions`/`clans` lines immediately above it already
represent. Fixing it is Step 1 and is a hard prerequisite for AC #1's own literal wording ("applies
correctly through the authoritative apply path"), which is impossible to satisfy without it.

The plan otherwise: (1) adds one new field to `InformationProviderState` for the accumulation
counter; (2) hooks the existing `QuestResolutionSystem.enforce()` `is_newly_completed` branch
(`src/engine/quests.py:197`) — the same branch that already does the analogous ESCORT→reputation
side-effect — using the existing but currently-dead `QuestState.source_entity_id` field, so no new
attribution field or building→provider lookup is invented; (3) adds a new
`InformationPropagationService` beside `FactionAwarenessService` in `src/engine/faction_decision.py`
that walks `state.recent_world_events`/`FactionState.territory`/`diplomatic_relations` exactly like
`compute_tension_updates()` does, emitting new `WorldEvent`s (not `FactionState` mutations — no new
topology field, satisfying the architecture guard) at destination regions; (4) anchors "critical" to
`WorldEvent.severity >= 0.8` (a new named constant), explicitly not `SimulationEvent.severity`
(a disjoint observability vocabulary no decision phase reads); (5) registers one new flag,
`ENABLE_INFORMATION_HUB_ACCUMULATION`, DEV-002-compliant (default OFF), gating both the accumulation
branch and the propagation phase; (6) adds the two required parity ledger entries and one Mechanics
Bible section; (7) documents Guide-to-Guide/hub-to-hub exchange as scoped out entirely (not stubbed),
satisfying AC #5 without building unneeded scaffolding.

## Steps

### Step 1 — Fix `apply.py`: wire `information_providers` into the tick-boundary apply path
**Files:** `src/engine/apply.py`

**Change:** In `ApplyPath.apply_generation`, add a carry-forward-and-merge block for
`information_providers`, placed next to the existing `factions`/`clans` blocks
(`src/engine/apply.py:351-394`, confirmed by direct read) and mirroring their exact shape:

```python
# Wire information_providers into the tick-boundary apply path (previously omitted --
# every StateUpdate.information_providers_update write, including LeadContradictionSystem's
# existing decrement, was silently discarded at tick end; see TCK-20260903-INFORMATION-HUB-
# ACCUMULATION investigation.md).
new_information_providers = dict(getattr(prior_state, "information_providers", {}))
new_information_providers.update(update.information_providers_update)
```

Then add `information_providers=new_information_providers,` to the `AuthoritativeState(...)`
constructor call at `src/engine/apply.py:396-452`, placed next to `factions=new_factions,`/
`clans=new_clans,` (currently lines 446-447, confirmed by direct read — no `information_providers=`
keyword is present in that call today).

**Other writers to this resource, and how this interacts with them:** `update.information_providers_update`
is a `Dict[int, InformationProviderState]` (`src/core/updates.py:1015`). Its only current production
writer is `LeadContradictionSystem.enforce()` (`src/engine/pipeline_phases/lead_contradiction.py:154,
228-242`), which reads `providers_update.get(provider_id, state.information_providers.get(provider_id))`
before calling `replace(provider, reliability_score=...)` — i.e. it always reads the *current,
already-threaded* dict as its base, not a stale snapshot. `StateUpdate.merge()`
(`src/core/updates.py:1102,1172`) does a plain `dict.update()` when combining two `StateUpdate`s
(whole-key replacement, not field-level), but because both `LeadContradictionSystem` and this
ticket's new accumulation write (Step 4) each build their replacement object via `replace()` off the
already-current per-key object rather than constructing a bare new one, and because the pipeline
runs phases sequentially (`update = phaseA(...); update = phaseB(state, <result of phaseA>)`, not in
parallel), two same-tick writes to different fields on the *same* provider correctly stack rather
than clobbering each other, as long as each new writer follows this same read-current-then-`replace()`
convention (Step 4 must follow it). This fix does not change `LeadContradictionSystem`'s own logic,
`_RELIABILITY_PENALTY`, or `_RELIABILITY_FLOOR` (0.1) — it only makes its existing output durable
across a tick boundary, which it never was before.

**Do NOT touch:** Any other field's carry-forward logic in `apply.py` (`factions`, `clans`,
`quest_registry`, `recent_world_events`, etc.) — add only the new `information_providers` block, do
not restructure the surrounding function.

**Verify:** New test proving a `StateUpdate.information_providers_update` entry passed through
`ApplyPath.apply_generation` produces a matching `AuthoritativeState.information_providers[id]`
in the returned state (test 1, extended to explicitly also prove `LeadContradictionSystem`'s
existing decrement now survives an `apply_generation` call — a regression proof, not just a new
feature proof). Location: `tests/unit/domains/information/test_information_provider_accumulation.py`
(new file).

---

### Step 2 — Add the accumulation field to `InformationProviderState`
**Files:** `src/domains/information/providers.py`

**Change:** `InformationProviderState` (`src/domains/information/providers.py:36-58`, confirmed by
direct read: frozen, `slots=True` dataclass with `entity_id`, `archetype`, `reliability_score`,
`knowledge_domains`, `knowledge_age` — no accumulation field exists today) gains one new field:

```python
knowledge_accumulated: int = 0
```

Placed after `knowledge_age`. Docstring addition: "knowledge_accumulated: Cumulative count of
distinct knowledge-report events this provider has received (e.g. a quest they assigned being
reported back). Monotonically non-decreasing. Distinct from reliability_score (trustworthiness) and
knowledge_age (freshness) — see Anti-Drift Notes." Update `to_canonical_dict()`
(`src/domains/information/providers.py:60-74`) to include `"knowledge_accumulated": self.knowledge_accumulated,`
in the returned dict, in field-declaration order, matching the existing convention.

**Do NOT touch:** `reliability_score`'s semantics, default, or decrement logic — this is a
new, independent field, not a repurposing of `reliability_score` (explicit Anti-Drift Hazard in
investigation.md). Do not rename or change the type/default of `knowledge_age`.

**Verify:** `test_information_provider_accumulation_field_default` — constructs
`InformationProviderState()` and asserts `knowledge_accumulated == 0` by default, and that
`to_canonical_dict()` includes the new key. Same file as Step 1's test.

---

### Step 3 — Register the new feature flag
**Files:** `src/domains/optimization/feature_flags.py`

**Change:** Add one new entry to `FeatureFlagManager.__init__`'s `self._flags` dict
(`src/domains/optimization/feature_flags.py:13-165`, confirmed by direct read of the full dict and
its DEV-002 inline-comment convention — every flag added since `TCK-20260824-ROLLOUT-FLAG-DECISIONS`
follows the same "New gameplay behavior... DEV-002 default-OFF policy applies... no corpus profile
turns this on and no SHADOW-validation history exists" shape, e.g. `ENABLE_GUILD_QUEST_GENERATION`
at lines 81-91):

```python
# New gameplay behavior (TCK-20260903-INFORMATION-HUB-ACCUMULATION): gates both the
# InformationProviderState accumulation branch inside QuestResolutionSystem.enforce()
# (checked via state.feature_flags directly, matching ENABLE_GUILD_QUEST_GENERATION's own
# guild_visit.py convention) and the new information_propagation pipeline phase (checked via
# FeatureFlagManager/run_phase). DEV-002 default-OFF policy applies -- brand-new mechanic
# (idea 41), no corpus profile turns this on and no SHADOW-validation history exists. Note:
# the accumulation branch is structurally inert in any real corpus run today even when ON --
# GuildAction.visit() never populates QuestState.source_entity_id (src/town/guild.py:38,
# `source_entity_id=None  # GUILD`), so this flag currently only gates directly-constructed
# unit-test scenarios and the propagation phase. See investigation.md Risk #1/#2.
"ENABLE_INFORMATION_HUB_ACCUMULATION": FeatureMode.OFF,
```

Insert after `ENABLE_REPRODUCTION_HUMANOID_PATH` (the last entry before the closing `}` at line 164),
matching the file's append-at-end convention for new flags.

**Do NOT touch:** Any existing flag's value or comment — this is a single new dict entry.

**Verify:** `tests/unit/config/test_phase10_feature_flags.py` — confirm the new flag is present,
defaults to `FeatureMode.OFF`, and (per the file's own established pattern for
`ENABLE_GUILD_QUEST_GENERATION`) does not need allowlisting since it's OFF by default.

---

### Step 4 — Accumulation trigger: hook `QuestResolutionSystem.enforce()`'s `is_newly_completed` branch
**Files:** `src/domains/information/accumulation.py` (new), `src/engine/quests.py`

**Change:** Create `src/domains/information/accumulation.py` (new file, sibling to
`providers.py`/`assimilation.py` in the same directory — no existing file of this name, confirmed
by directory listing) with:

```python
class InformationAccumulationService:
    """Applies a knowledge_accumulated increment + knowledge_age freshness reset to an
    InformationProviderState in response to a quest report-back. Decision-only: returns a
    replacement InformationProviderState, does not mutate state."""

    @staticmethod
    def record_quest_reported_back(provider: InformationProviderState) -> InformationProviderState:
        return replace(
            provider,
            knowledge_accumulated=provider.knowledge_accumulated + 1,
            knowledge_age=0,
        )
```

In `src/engine/quests.py`'s `QuestResolutionSystem.enforce()`, inside the existing
`if is_newly_completed or is_retry_pending:` block (`src/engine/quests.py:200`), add a new branch
directly beside the existing `if is_newly_completed and project.quest_kind == QuestKind.ESCORT:`
branch (lines 221-235, confirmed by direct read — this is the one existing precedent for a
`quest_kind`-independent-shaped, `is_newly_completed`-gated side effect via a service class import,
matching `ReputationUpdateService` imported at line 164):

```python
if is_newly_completed:
    flags = getattr(state, "feature_flags", None) or {}
    if flags.get("ENABLE_INFORMATION_HUB_ACCUMULATION", "OFF") == "ON" and project.source_entity_id is not None:
        provider = providers_update.get(
            project.source_entity_id,
            state.information_providers.get(project.source_entity_id),
        )
        if provider is not None:
            providers_update[project.source_entity_id] = InformationAccumulationService.record_quest_reported_back(provider)
```

where `providers_update = dict(update.information_providers_update)` is initialized once at the top
of `enforce()` (mirroring `refined_entity_updates = dict(update.entity_updates)` at line 166) and the
returned `StateUpdate` at the end of `enforce()` includes `information_providers_update=providers_update`.
This is gated **only** on `is_newly_completed` (not `is_retry_pending`) — matching the ESCORT
branch's own guard — so a reward-delivery retry across ticks cannot double-increment the counter.
The flag check uses the direct `state.feature_flags.get(...)` pattern from `GuildVisitPhase.resolve()`
(`src/engine/pipeline_phases/guild_visit.py:39-41`, confirmed by direct read), not
`FeatureFlagManager`/`run_phase`, because `QuestResolutionSystem.enforce()` is called directly from
`QuestRewardPhase.resolve()` (`src/engine/pipeline_phases/quests.py:26`), which itself is invoked via
`AuthoritativeApplyPipeline._resolve_quest_rewards` at `src/engine/pipeline.py:496-501`, wrapped in
`run_phase("quest_rewards", ...)` at `src/engine/pipeline.py:347` — `run_phase` only gates the whole
`quest_rewards` phase call, not this specific new branch inside it, and quest rewards must keep
firing unconditionally regardless of this new flag.

**Other writers to this resource, and how this interacts with them (ordering-verified):**
`pipeline.py:347` (`quest_rewards`, containing this new branch) runs **before**
`pipeline.py:384` (`lead_contradiction`, `LeadContradictionSystem.enforce()`) in
`AuthoritativeApplyPipeline.refine()`'s sequence — confirmed by direct read of both line numbers.
Because `LeadContradictionSystem.enforce()` reads `providers_update.get(provider_id,
state.information_providers.get(provider_id))` (Step 1's citation) as its base before calling
`replace()`, if the *same* `provider_id` is targeted by both this new accumulation branch (in the
same tick, running first) and a lead contradiction (running second), the lead-contradiction's
`replace(provider, reliability_score=...)` call operates on the object that already has this step's
`knowledge_accumulated`/`knowledge_age` change applied — both edits stack correctly, no lost update.
This ordering guarantee depends on Step 1's fix; without it, `information_providers_update` would
still merge correctly *within* a tick, but the merged result would be discarded at tick-apply time
regardless.

**Do NOT touch:** The `is_newly_completed and project.quest_kind == QuestKind.ESCORT` reputation
branch's own logic or condition. Do not populate `QuestState.source_entity_id` anywhere else (e.g. in
`src/quests/generator.py` or `src/town/guild.py`) — that would be building the live-seeding/
attribution pipeline, explicitly out of scope per decision (b). Do not add a `quest_kind` restriction
to the new branch (accumulation is attribution-based via `source_entity_id`, not kind-based, unlike
the ESCORT reputation branch).

**Verify:** `test_quest_completion_increments_provider_accumulation` — constructs an
`AuthoritativeState` with a real `InformationProviderState` and an entity holding a `QuestState`
project with `source_entity_id` set to that provider's `entity_id`, drives
`QuestResolutionSystem.enforce()` directly (per investigation Risk #3 — do not depend on the
corpus-broken HUNT/GATHER/BOUNTY/LIBERATE evaluator gap; either a directly-constructed `QuestState`
already at `COMPLETED`/`ACTIVE` transition or the EXPLORE kind), with the flag overridden ON, and
asserts `knowledge_accumulated` increased by exactly 1 and `knowledge_age` reset to 0 via a
before/after `AuthoritativeState.information_providers[id]` comparison (through `ApplyPath.apply_generation`,
using Step 1's fix — not just inspecting the returned `StateUpdate`). Location:
`tests/unit/quest/test_quest_system.py` (existing file that already imports/exercises
`QuestResolutionSystem`, confirmed by grep) or `tests/unit/domains/information/test_information_provider_accumulation.py`
if kept alongside Steps 1-2's tests — implementer's choice, but must not duplicate coverage across
both.

---

### Step 5 — New `WorldEventCategory` member for propagated critical information
**Files:** `src/domains/world_emergence/schema.py`

**Change:** Add one new member to `WorldEventCategory`
(`src/domains/world_emergence/schema.py:15-54`, confirmed by direct read of the full enum — no
exhaustiveness/count-assertion test was found guarding this enum's member list, see grep result in
investigation follow-up):

```python
# TCK-20260903-INFORMATION-HUB-ACCUMULATION: critical WorldEvent propagated to a sibling
# City (same faction territory) or an ALLIED Country's territory.
CRITICAL_INFORMATION_PROPAGATED = "CRITICAL_INFORMATION_PROPAGATED"
```

A new member is used rather than repurposing the existing dead `RUMOR_CONFIRMED`/`RUMOR_CONTRADICTED`
members (`src/domains/world_emergence/schema.py:29-30`) because "rumor confirmed/contradicted"
describes confirming or refuting a specific existing rumor, not propagating a critical-severity
event to new territory — reusing them would be a semantic mismatch, not a genuine reuse. This
follows the same pattern as recent additions to this enum (e.g. `PRODUCTION_ROLE_VACATED`,
`SOVEREIGNTY_SHIFT`, both confirmed present at lines 49-54) — additive enum growth, not new
topology, so it does not conflict with the Scope's "no new topology type" guard (that guard targets
`FactionState`, not `WorldEventCategory`).

**Do NOT touch:** `RUMOR_CONFIRMED`/`RUMOR_CONTRADICTED` or any other existing member.

**Verify:** Covered implicitly by Step 6's tests (the new category is only meaningful in
combination with the propagation phase that emits it).

---

### Step 6 — City-to-City / City-to-Country propagation phase
**Files:** `src/engine/faction_decision.py`, `src/engine/pipeline.py`

**Change:** In `src/engine/faction_decision.py`, add `InformationPropagationService` directly below
`FactionAwarenessService` (`src/engine/faction_decision.py:174-208`, confirmed by direct read — this
is the exact sibling pattern this ticket is asked to reuse):

```python
_CRITICAL_SEVERITY_THRESHOLD: float = 0.8  # WorldEvent.severity anchor for "critical" (Plan decision
# — see Anti-Drift Notes for why WorldEvent.severity was chosen over SimulationEvent.severity).

class InformationPropagationService:
    """Propagates critical WorldEvents to sibling City territory (same faction) and ALLIED
    Country territory (cross-faction), by emitting new WorldEvents at destination regions.
    Does not mutate FactionState -- no new topology field, no FactionUpdate emitted.

    Uses state.recent_world_events, the same bounded, one-tick-lagged window
    FactionAwarenessService.compute_tension_updates() reads."""

    @staticmethod
    def compute_propagation_events(
        state: AuthoritativeState,
        recent_events: Sequence[WorldEvent],
    ) -> list[WorldEvent]:
        new_events: list[WorldEvent] = []
        for event in recent_events:
            if event.severity < _CRITICAL_SEVERITY_THRESHOLD:
                continue
            if event.region_id is None:
                continue
            for faction_id, fs in state.factions.items():
                if event.region_id not in fs.territory:
                    continue
                # City-to-City: sibling regions in the same faction's territory.
                for sibling_region in fs.territory:
                    if sibling_region == event.region_id:
                        continue
                    new_events.append(WorldEvent(
                        category=WorldEventCategory.CRITICAL_INFORMATION_PROPAGATED,
                        tick=state.tick, region_id=sibling_region,
                        subject=event.subject, severity=event.severity,
                    ))
                # City-to-Country: ALLIED factions' territory only (see Anti-Drift Notes for
                # why ALLIED-only, not ALLIED/NEUTRAL).
                for other_id, other_fs in state.factions.items():
                    if other_id == faction_id:
                        continue
                    if fs.diplomatic_relations.get(other_id, DiplomaticState.NEUTRAL) != DiplomaticState.ALLIED:
                        continue
                    for dest_region in other_fs.territory:
                        new_events.append(WorldEvent(
                            category=WorldEventCategory.CRITICAL_INFORMATION_PROPAGATED,
                            tick=state.tick, region_id=dest_region,
                            subject=event.subject, severity=event.severity,
                        ))
        return new_events
```

Wire it into `src/engine/pipeline.py`'s `refine()`, immediately after the existing
`faction_awareness` block (`src/engine/pipeline.py:233-242`, confirmed by direct read — same
`_recent_events`/`state.factions` inputs, natural adjacent placement), using the `run_phase(...,
feature_flag=...)` form already used by e.g. `world_emergence` at line 339 (confirmed signature:
`run_phase(phase_name: str, upd: StateUpdate, phase_fn, feature_flag: Optional[str] = None)`,
`src/engine/pipeline.py:102-127`):

```python
# --- TCK-20260903-INFORMATION-HUB-ACCUMULATION: Information Propagation ---
t_start = time.perf_counter_ns()
from src.engine.faction_decision import InformationPropagationService
from src.core.updates import StateUpdate as _SU_ip
update = run_phase(
    "information_propagation", update,
    lambda u: u.merge(_SU_ip(world_events_add=InformationPropagationService.compute_propagation_events(state, _recent_events))),
    "ENABLE_INFORMATION_HUB_ACCUMULATION",
)
costs["information_propagation"] = (time.perf_counter_ns() - t_start) / 1e6
```

`_recent_events` is already computed one block above (line 237) — reused, not recomputed.

**Other writers to this resource, and how this interacts with them:** `update.world_events_add`
(`src/core/updates.py:1009`) already has multiple writers this tick — `diplomatic_transitions`
(pipeline.py:264-271, `_diplo_world_events`), `world_dynamics.py:115` (sovereignty events),
`military_conflict.py:354`, `economy.py:290` — all append-only via `StateUpdate.merge()`'s list
concatenation (`src/core/updates.py:1097,1167`, confirmed by direct read: `new_world_events_add =
list(self.world_events_add); ...; new_world_events_add.extend(other.world_events_add)` — additive,
no key collision possible for a list field, unlike the dict-keyed `information_providers_update`).
`AuthoritativeState.recent_world_events` is written once, at tick-apply time, by
`src/engine/apply.py:335-338` (confirmed: `merged_events = prior_events + update.world_events_add;
new_recent_world_events = merged_events[-500:]`) — a single writer, already correctly wired (unlike
`information_providers`, which needed Step 1's fix). This phase's new events simply add to that same
list; no change to `apply.py`'s existing `WORLD_EVENT_WINDOW = 500` trimming logic is needed or made.

**Do NOT touch:** `FactionState` (no new field, no `FactionUpdate` emitted by this service — verified
by Step 7's architecture guard), `diplomatic_relations` itself (read-only: `.get(...)`, never
`replace()`'d or written via `FactionUpdate(diplomatic_relations_set=...)` — that is
`src/domains/faction/diplomatic_state_machine.py`'s territory, explicitly out of scope), and
`FactionAwarenessService.compute_tension_updates()`'s own logic/output (unchanged — this is a
parallel, independent consumer of the same `_recent_events` input, confirmed to be
read-only-with-respect-to-that-input so no interference).

**Verify:** Test 4 (`test_critical_information_propagates_within_faction_territory`) and test 5
(`test_critical_information_reaches_allied_country_not_unrelated_country`), plus a non-regression
assertion that `FactionAwarenessService.compute_tension_updates()`'s own
`RESOURCE_DEPLETED`→`tension_delta=+0.1` output is byte-identical with this new phase also reading
`recent_world_events` in the same tick. Location:
`tests/unit/domains/faction/test_critical_information_propagation.py` (new).

---

### Step 7 — Architecture guards
**Files:** `tests/architecture/` (new test file(s))

**Change:** Add two architecture-guard tests:
1. `test_no_new_faction_topology_field_added` — introspects `FactionState`'s `__dataclass_fields__`
   and asserts the set is exactly `{faction_id, territory, resources, diplomatic_relations,
   active_doctrines, military_strength, tension_level}` (confirmed as the complete current field set
   by direct read of `src/core/state.py:639-648`) plus the private `_canonical_cache` bookkeeping
   field — directly enforcing Scope's "no new topology type" and AC #4's "no new topology type"
   wording.
2. `test_no_conversation_class_introduced` — greps `src/` for a `class Conversation` (or similarly
   named dialogue-system class) definition and asserts zero matches, extending the zero-grep-hits
   fact already confirmed in investigation.md; documents that this ticket's Guide-to-Guide/hub-to-hub
   exchange requirement (AC #5) was resolved by scoping the exchange mechanism out entirely (see
   Step 10), not by building a state-level stand-in.

**Do NOT touch:** Any other architecture guard file's existing assertions.

**Verify:** Both tests pass; `pytest tests/architecture/ -k "information_hub or no_new_faction_topology or no_conversation" -v` per test_plan.md's scoped command.

---

### Step 8 — Flag-OFF no-op test
**Files:** `tests/unit/domains/optimization/test_information_hub_flag_off.py` (new) or folded into
Step 4/6's test files

**Change:** Add `test_information_hub_accumulation_flag_off_no_state_change`: with
`ENABLE_INFORMATION_HUB_ACCUMULATION` left at its default `OFF`, drive both (a) a quest report-back
scenario that would otherwise trigger Step 4's accumulation and (b) a critical-severity `WorldEvent`
scenario that would otherwise trigger Step 6's propagation, through `ApplyPath.apply_generation`, and
assert `AuthoritativeState.information_providers` and `AuthoritativeState.recent_world_events` are
byte-identical before and after (via `to_canonical_dict()` comparison or direct equality).

**AC-wording note (see Acceptance Criteria Map, AC #3):** the ticket's own wording says
"information_providers/FactionState unchanged" — this plan's propagation mechanism (Step 6) never
writes to `FactionState` at all (by design, per Step 7's architecture guard), so a literal
"FactionState unchanged" assertion would pass trivially regardless of flag state and would not
actually test anything. The test target is corrected here to the two fields this ticket's flag
genuinely gates: `information_providers` (Step 4's output) and `recent_world_events` (Step 6's
output).

**Do NOT touch:** `ENABLE_GUILD_QUEST_GENERATION`'s own flag-off test or default value — this new
flag must remain independently toggleable from it (anti-drift guard from test_plan.md).

**Verify:** Test passes with the flag at its default; a second assertion (or a paired test) confirms
the same scenario, run again with the flag explicitly overridden ON, DOES change the state — proving
the OFF-path test isn't vacuously true because the scenario itself is a no-op.

---

### Step 9 — Docs: Mechanics Bible, parity ledger, feature flags guide
**Files:** `docs/mechanics/04_strategic_cognition.md`, `docs/parity_ledger/strategic_cognition.yaml`,
`docs/parity_ledger/faction.yaml`, `docs/guides/feature_flags.md`

**Change:**
- `docs/mechanics/04_strategic_cognition.md`: add a new `## 11. Information Hub Knowledge
  Accumulation & Propagation Law (idea 41, M4)` section, immediately after the existing `## 10. Clan
  Lifecycle Law (idea 40/M4, SOC-263)` section (confirmed as the current last section by direct
  read — `grep "^## "` shows section 10 at line 1118 is the final heading), documenting: the
  `knowledge_accumulated` field and its increment law (Step 2/4), the apply-path fix (Step 1) and
  why it matters for `STRAT-230`'s pre-existing decrement path too, the `WorldEvent.severity >= 0.8`
  critical-severity anchor (Step 6) and the explicit choice over `SimulationEvent.severity`, the
  City-to-City/ALLIED-only City-to-Country propagation rule, and an explicit note that Guide-to-Guide/
  hub-to-hub exchange is scoped out of this ticket (not built, not stubbed) and that the accumulation
  trigger is structurally inert in live corpus runs today (cite `src/town/guild.py:38`).
- `docs/parity_ledger/strategic_cognition.yaml`: add one new entry (next available `STRAT-###` ID,
  determined at implementation time to avoid collision with entries added by concurrent tickets)
  documenting the `knowledge_accumulated` increment mechanism, `priority: P1` (matching `STRAT-230`'s
  own priority, not P0), `v2_evidence` citing `src/domains/information/accumulation.py`,
  `src/engine/quests.py` (the hook site), and `src/engine/apply.py` (the fix), `test_path` citing
  Step 4's test.
- `docs/parity_ledger/faction.yaml`: add one new entry (next available ID) documenting
  `InformationPropagationService.compute_propagation_events()`, modeled directly on
  `FACTION-TENSION-001`'s own entry shape (`docs/parity_ledger/faction.yaml:50-64`, confirmed by
  direct read), `priority: P1`, `v2_evidence` citing `src/engine/faction_decision.py` and
  `src/engine/pipeline.py`'s `information_propagation` block, `test_path` citing Step 6's test.
- `docs/guides/feature_flags.md`: add one new row for `ENABLE_INFORMATION_HUB_ACCUMULATION`,
  matching the row shape used for `ENABLE_GUILD_QUEST_GENERATION` (per its own ticket's Files
  Changed list).

Use `tools/parity_ledger_writer.py` (the sanctioned, schema-validating tool) to add both parity
entries — not a raw YAML edit — per this session's own established
parity-updater-full-file-rewrite-risk guidance.

**Do NOT touch:** `docs/brainstorm/rpg_feature_atlas.html`, `docs/audits/D19_domain_phase_inventory.md`,
`docs/brainstorm/rpg_expected_schemas.html` — investigation confirmed none of these are required
update targets for this ticket (see investigation.md "Docs Requiring Update"). Do not edit
`STRAT-230`'s own entry's `text`/`status` fields beyond what's needed to note the apply-path fix in
`v2_evidence` if the parity-updater agent judges that necessary — its core claim (the decrement
law itself) is unchanged by this ticket.

**Verify:** `make knowledge-index-update` after doc changes (per CLAUDE.md's After Work rule); no
dedicated test, doc-updater/parity-updater agent review at the appropriate pipeline phase.

---

### Step 10 — Ticket-level disclosure: Guide-to-Guide/hub-to-hub exchange scoped out
**Files:** None (documentation-only, folded into Step 9's Mechanics Bible section and the ticket's
own Completion Summary at Finalize)

**Change:** No exchange mechanism is built. AC #5 is satisfied by: (a) Step 7's architecture guard
proving no `Conversation` class was introduced, and (b) Step 9's Mechanics Bible section explicitly
stating the exchange mechanism is out of this ticket's scope entirely — not reframed at the state
level, not stubbed — because decision (b) (see Summary) already narrows this ticket to the
accumulation and propagation mechanisms only; building even a minimal state-level exchange primitive
would be scope creep beyond AC #5's literal requirement (that it be documented as NOT
Conversation-based).

**Do NOT touch:** Do not create any new `StateUpdate` field, service class, or state-level primitive
for Guide-to-Guide exchange "just in case" — that is explicitly not required by AC #5 as literally
worded and would be unrequested scope expansion.

**Verify:** Step 7's `test_no_conversation_class_introduced`.

## Scope Guards

- Do not populate `AuthoritativeState.information_providers` anywhere in `V2EntityBuilder`, content
  loaders, or `src/worldbuilding/` — no live seeding pipeline is built by this ticket (decision (b)).
- Do not populate `QuestState.source_entity_id` in `src/quests/generator.py` or `src/town/guild.py`
  — the accumulation trigger (Step 4) reads this field but does not populate it; it remains dead in
  the live `GuildAction.visit()` path exactly as investigation found.
- Do not build a building→provider lookup (investigation Risk #2 option (b)) — Step 4 uses only the
  existing `source_entity_id` field, never `source_building_id`.
- Do not add a `Conversation`/entity-dialogue class anywhere in `src/` (Step 7/10).
- Do not add any new field to `FactionState` (Step 6/7) — propagation output is new `WorldEvent`s
  only, never a `FactionUpdate`.
- Do not change `LeadContradictionSystem`'s decrement logic, `_RELIABILITY_PENALTY`, or
  `_RELIABILITY_FLOOR` (Step 1/4).
- Do not flip `ENABLE_GUILD_QUEST_GENERATION` or otherwise touch its default/tests as a side effect.
- Do not silently "fix" `QuestGenerator`'s HUNT/GATHER/BOUNTY/LIBERATE metadata gap
  (`TCK-20260807-QUEST-EVALUATOR-GATHER-BOUNTY-LIBERATE-GAP` territory) as a side effect of Step 4's
  test design.
- Do not edit `docs/brainstorm/rpg_feature_atlas.html`, `docs/audits/D19_domain_phase_inventory.md`,
  or `docs/brainstorm/rpg_expected_schemas.html`.
- Do not restructure any part of `apply.py` beyond the single new `information_providers`
  carry-forward-and-merge block (Step 1).

## Dependency Map

- Step 1 (apply.py fix) is a hard prerequisite for Step 4's and Step 8's "applies through the
  authoritative apply path" verification — must land first.
- Step 2 (new field) is a prerequisite for Step 4 (the field being incremented) and Step 9 (doc
  content referencing it).
- Step 3 (flag registration) is a prerequisite for Step 4's and Step 6's flag checks, and for Step 8.
- Step 5 (new `WorldEventCategory` member) is a prerequisite for Step 6 (the category it emits).
- Step 6 depends on Step 3 (flag) and Step 5 (category); independent of Steps 1/2/4 (propagation
  never touches `information_providers`).
- Step 7 depends on Steps 2, 6, 10 existing (or explicitly not existing, for the Conversation guard)
  to have something to assert against.
- Step 8 depends on Steps 1-6 all being in place (it exercises both the accumulation and propagation
  paths under the flag).
- Step 9 depends on Steps 1-8 being functionally complete (doc content describes real, tested
  behavior, not a plan).
- Step 10 has no code dependency; it is satisfied by Step 7's test plus Step 9's doc note.
- Steps 4 and 6 are otherwise mutually independent and could be implemented in either order once
  Steps 1-3/5 land.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC #1: InformationProviderState gains a real accumulation mechanism, before/after state assertion, "a quest a Guide assigned is reported back" | Steps 1, 2, 4 | Step 1/4 tests in `tests/unit/domains/information/test_information_provider_accumulation.py` and/or `tests/unit/quest/test_quest_system.py`. **AC revision**: "a quest a Guide assigned is reported back" cannot be exercised end-to-end via a real corpus-world run today — `GuildAction.visit()` never populates `QuestState.source_entity_id` (`src/town/guild.py:38`), so the live Guild hub has no attribution path to any `InformationProviderState`. This AC is satisfied via direct unit-level construction of a `QuestState`+`InformationProviderState` pair proving the mechanism (typed update path + apply-path wiring, both real and tested) is correct — not via corpus reachability. This is a disclosed gap (decision (b)), not a silent narrowing. |
| AC #2: ticket/docs state current flag reality (BELIEF_ASSIMILATION ON, INFORMATION_INTENT_EXECUTION OFF) | Already stated in the ticket's own Request Summary; reaffirmed in Step 9 | No dedicated test — doc consistency, reviewed at done-checker. |
| AC #3: new flag defaults OFF (DEV-002), flag-OFF test leaves state unchanged | Steps 3, 8 | Step 8's flag-off test. **AC revision**: ticket wording says "information_providers/FactionState unchanged" — corrected to "information_providers/recent_world_events unchanged" because this plan's propagation mechanism never writes to `FactionState` at all (by design — see Step 6/7), so "FactionState unchanged" would be true regardless of flag state and would not test anything real. See Step 8's explicit note. |
| AC #4: City-to-City/City-to-Country propagation via `territory`/`diplomatic_relations`, no new topology type, reaches sibling Cities under Country A but not unrelated Country B | Steps 5, 6, 7 | Step 6's tests 4/5, Step 7's `test_no_new_faction_topology_field_added`. **AC revision**: cross-faction (City-to-Country) gating is restricted to `diplomatic_relations == ALLIED` only — not the investigation's tentative "ALLIED/NEUTRAL" example. Reasoning: the `fs.diplomatic_relations.get(other_fid, DiplomaticState.NEUTRAL)` idiom defaults an *absent* relation entry to `NEUTRAL`; the AC's own "unrelated Country B" test case has no explicit relation to Country A and must therefore resolve to that same default. If `NEUTRAL` were also a propagate-gate, "unrelated" Country B would incorrectly receive the propagation, directly contradicting the AC's literal wording. ALLIED-only is the one gating rule consistent with the AC as written. |
| AC #5: Guide-to-Guide/hub-to-hub exchange explicitly documented as NOT reusing Conversation | Step 10 (scoped out entirely, not stubbed), verified by Step 7 | Step 7's `test_no_conversation_class_introduced`; Step 9's Mechanics Bible note. |

## Anti-Drift Notes

- **Apply-path fix is not seeding.** Step 1 fixes a pipeline-wiring omission that already existed
  before this ticket (it silently broke `STRAT-230`'s decrement path too) — it is not "building a
  full seeding pipeline" and does not conflict with the Out-of-Scope guard against one. Do not use
  this fix as a foothold to also add a seeding call site "since we're already in `apply.py`."
- **`knowledge_accumulated` is a distinct concept from `reliability_score`.** Do not let the two
  fields' `replace()` calls get merged into a single code path or a single semantic meaning —
  investigation explicitly flags this as a real collision risk given both live on the same record
  and are now written by two different phases in the same tick (see Step 1's ordering analysis).
- **`_CRITICAL_SEVERITY_THRESHOLD = 0.8` is this plan's own reasoned choice**, not a pre-existing
  convention — investigation left "critical" fully undefined. `WorldEvent.severity` was chosen over
  `SimulationEvent.severity` because propagation reads `state.recent_world_events` (a list of
  `WorldEvent`, not `SimulationEvent`) — anchoring to the type actually being walked, not the
  disjoint observability-layer vocabulary no decision phase currently reads.
- **ALLIED-only City-to-Country gating is a deliberate divergence from investigation's own tentative
  example** ("ALLIED/NEUTRAL") — see the AC #4 revision note above for why NEUTRAL had to be
  excluded to satisfy the ticket's own AC wording.
- **Ordering dependency, not a race**: Steps 1 and 4's "other writers" analysis shows `quest_rewards`
  (pipeline.py:347) runs before `lead_contradiction` (pipeline.py:384) in the same tick. This ordering
  is load-bearing for same-provider same-tick correctness (see Step 4). If a future ticket reorders
  these phases, re-verify this interaction.
- **Live-seeding remains a real, disclosed gap.** This plan does not resolve
  `InformationProviderState`'s zero-live-instances problem (investigation Risk #1) or the Guild's
  lack of entity identity (Risk #2). A follow-up ticket for live seeding is recommended but not filed
  by this plan — that is the main session's decision, not the planner's or implementer's.

## Deviations (implementation-time, recorded per CLAUDE.md's "never silently deviate" rule)

1. **Step 1 test event-count assertion.** The Step 1 verify text implied a single-event proof for
   `LeadContradictionSystem.enforce()`'s regression test. The real method emits two
   `SimulationEvent`s per contradicted lead (`belief_contradiction` + `lead_contradiction_resolved`),
   not one. The implemented test asserts `len(events) >= 1` rather than an exact count of 1 — this
   is a test-authoring correction discovered during Test, not a change to
   `LeadContradictionSystem`'s own logic (untouched, per the plan's own Scope Guards).
2. **Step 3 flag-comment wording.** The Step 3 flag-registration comment as drafted in this plan
   used the literal string "GuildAction.visit()". That collided with a pre-existing architecture
   guard (`tests/architecture/test_guild_action_dormancy.py`, a `\bGuildAction\b` regex checking
   `GuildAction` is referenced from exactly one deliberate dispatch site). The implemented comment
   describes the same fact ("the Guild hub's own visit-completion path never populates
   QuestState.source_entity_id") without the literal class-name token. No behavior change,
   comment-only.

Both deviations are also recorded in `tickets/inprogress/TCK-20260903-INFORMATION-HUB-ACCUMULATION.md`'s
Implementation Notes.
