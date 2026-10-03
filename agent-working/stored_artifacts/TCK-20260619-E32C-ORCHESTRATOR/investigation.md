---
ticket_id: TCK-20260619-E32C-ORCHESTRATOR
date: 2026-06-21
phase: investigation
status: complete
---

# Investigation — TCK-20260619-E32C-ORCHESTRATOR

## Current Behavior

### ScenarioRuntimeService (E31A/E31B — DONE)

**File:** `src/engine/scenario_runtime.py`

- `ScenarioRuntimeService.__init__(spec: SimulationScenarioDefinition)` — builds kernel lazily on first `start()` or `step()` call (L128).
- `start(tick_limit=500)` / `pause()` / `resume(tick_limit)` / `step()` / `abort()` — full lifecycle API (L139–205).
- `_build_kernel()` (L293): constructs `Kernel(profile, AuthoritativeState(tick=0, seed=0), DeterministicRNG(base_seed=0), flags={"no_replay": True})`. Hardcoded seed=0 — **no per-episode seed parameterization exists yet**.
- `kernel` property: **not exposed publicly**. Stored as `self._kernel` (private). The ticket pseudocode calls `svc.kernel.state` — this will require either a public `kernel` property to be added to `ScenarioRuntimeService`, or an alternative state-extraction path (e.g., a dedicated `final_state` property).
- `objective_state: ScenarioObjectiveState` — `RUNNING / OBJECTIVE_MET / OBJECTIVE_FAILED / STALLED / ABORTED` (L36–42).
- `alive_entity_count` property (L228): reads `len(self._kernel.state.entities)` — this is the only public state accessor. It does **not** expose `self._kernel.state` directly.
- `ScenarioObjectiveState` values that count as terminal (episode ended): `OBJECTIVE_MET`, `OBJECTIVE_FAILED`, `STALLED`, `ABORTED`.

### CampaignState (E32B — DONE)

**File:** `src/domains/campaigns/state.py`

- `CampaignState` (mutable): `campaign_id: str`, `episode_index: int`, `episode_history: List[EpisodeSummary]`, `persistent_entities: Dict[int, EntityCarryForward]`, `persistent_factions: Dict[str, FactionCarryForward]`, `world_timeline: List[WorldTimelineEntry]`, `narrative_ledger: List[NarrativeLedgerEntry]` (L172–188).
- `EntityCarryForward` (frozen): `entity_id, level, xp, equipment: dict, reputation: float, alive: bool` (L16–54). Field mapping notes are baked into docstring: `level <- entity.identity.evolution_level`, `xp <- entity.identity.evolution_points`, `reputation <- entity.social.public_reputation`, `alive <- entity.lifecycle.active`.
- `FactionCarryForward` (frozen): `faction_id: str, alive: bool, tension: float` (L57–86). Docstring: E32C owns the `int -> str` faction mapping. `alive` = at least one entity with this faction int is active.
- `EpisodeSummary` (frozen): `episode_index: int, completed_tick: int` (L89–110). Described as "minimal stub — E32C adds richer fields."
- `episode_history` already exists on `CampaignState` and `EpisodeSummary` is the type (L184). No `_advance_state` method exists on `CampaignState` — the orchestrator builds it externally.
- No engine imports in `state.py` (enforced by test Guard-4 at `test_campaign_state_module_has_no_engine_imports`).

### EntityState field extraction path (AuthoritativeState)

**File:** `src/core/state.py`

The E32C extraction must read from `AuthoritativeState.entities: Dict[int, EntityState]`. Per-entity fields:

| Target (EntityCarryForward) | Source in EntityState | Notes |
|---|---|---|
| `level` | `entity.identity.evolution_level` (L436) | `IdentityComponent` field |
| `xp` | `entity.identity.evolution_points` (L437) | `IdentityComponent` field |
| `alive` | `entity.lifecycle.active` (L154) | `LifecycleComponent.active: bool = True` |
| `reputation` | `entity.social.public_reputation` (L639) | `SocialComponent` — single float |
| `equipment` | `entity.equipment.slots` + `entity.equipment.durability` | `EquipmentComponent`: `slots: Dict[EquipSlot, str|None]`, `durability: Dict[EquipSlot, float]` (L553–557). Keys are `EquipSlot` enum. Must be serialized as `{str(slot): item_id}` to match `EntityCarryForward.equipment` format `{"slots": {...}, "durability": {...}}`. |
| faction (for FactionCarryForward) | `entity.identity.faction: int` (L433) | E32C owns int→str mapping — no registry call is specified. Simplest: `str(faction_int)` or `f"faction_{faction_int}"`. Decision required (see OQ-3 below). |

`CombatComponent.alive` (L270) also exists — note distinction: `entity.lifecycle.active` (lifecycle death / permadeath) vs `entity.combat.alive` (combat alive status). Per E32B docstring, `EntityCarryForward.alive <- entity.lifecycle.active`. The `ObjectiveEvaluator` uses `e.combat.alive` for entity_count condition. The orchestrator must use `lifecycle.active` for carry-forward.

### CampaignSpec (legacy / analysis-domain)

**File:** `src/domains/campaigns/schema.py`

The existing `CampaignSpec` (L28–39) is the **analysis-domain** campaign spec — it has no `episodes` list, no `carry_forward_rules`, and no `id` field matching the orchestrator's needs. It is owned by `SimulationAnalysisRunner` and is **unrelated** to E32C.

**File:** `src/domains/campaigns/spec.py`

`CampaignSpecLoader` loads the analysis-domain `CampaignSpec` only — also unrelated.

The ticket's `CampaignSpec` (for orchestration) — with `id`, `episodes: List[SimulationScenarioDefinition]`, and `carry_forward_rules` — **does not yet exist**. This is a new type to be created as part of E32C.

### SimulationScenarioDefinition (E31A/E31B)

**File:** `src/scenarios/schema.py` (L45–90)

Fields: `id, display_name, world_composition, perspective, focus_modules, initial_conditions, setup_tags, template_id, victory_conditions`. `extra="forbid"` — adding `episodes` or `carry_forward_rules` here is **not appropriate**; these belong on the new orchestrator-level `CampaignSpec`.

### No CampaignOrchestrator exists

`src/domains/campaigns/orchestrator.py` does not exist. It must be created from scratch.

### Existing integration test directory

`tests/integration/scenarios/` exists with `test_scenario_runtime_service.py` (includes E31C checkpoint tests). No `test_campaign_runtime.py` exists. The ticket's two ACs point to:
- `tests/integration/scenarios/test_campaign_runtime.py::test_entity_state_persists_across_episodes`
- `tests/integration/scenarios/test_campaign_runtime.py::test_dead_faction_absent_in_episode_2`

Both need to be created.

### Campaigns domain contract note

`docs/simulation/domains/campaigns_contract.md` describes campaigns as "analysis domain — NOT simulation state." That contract describes the **existing** `SimulationAnalysisRunner` path. The E32C orchestrator is a **new** entity at a different layer — it wraps `ScenarioRuntimeService` (not `SimulationAnalysisRunner`) and produces durable `CampaignState`. The contract will need a new section or a sibling document to cover the orchestration domain.

---

## Mechanics / Engine Constraints

1. **Immutability law** (`docs/core/state.md`): `EntityState` is frozen; extraction reads are safe and non-mutating. `CampaignState` is intentionally mutable (not frozen) — mutation is the orchestrator's job.

2. **AuthoritativeState isolation** (campaigns_contract.md §Boundary): Each episode must use its own isolated `AuthoritativeState`. The orchestrator passes `CampaignState` (extracted carry-forward snapshots) between episodes — it must **not** share or transfer `AuthoritativeState` objects across episodes. The new episode's `AuthoritativeState` is built from scratch by `ScenarioRuntimeService._build_kernel()`, then seeded with carry-forward data before ticking. How carry-forward is applied to the new kernel's initial state is the key open question (OQ-1).

3. **Determinism** (INFRA-101/102): `ScenarioRuntimeService._build_kernel()` currently hardcodes `seed=0`. For a 3-episode campaign with determinism, each episode's seed must either (a) be fixed from the campaign spec, or (b) be derived deterministically from the previous episode outcome. Nondeterministic seeding across episodes is an anti-drift risk.

4. **No engine imports in state.py** (Guard-4): `CampaignOrchestrator` may import from `src.engine`, `src.core.state`, and `src.domains.campaigns.state` — but must not route engine types through `state.py`.

5. **`svc.kernel` is private**: `ScenarioRuntimeService.__slots__` lists `_kernel`. Adding a `kernel` property or a `final_state` property to `ScenarioRuntimeService` is the minimal change needed for state extraction. The ticket pseudocode uses `svc.kernel.state` — implementation must decide whether to expose `kernel` directly or add a `final_state: AuthoritativeState` property (preferred for encapsulation; keeps E32C from coupling to kernel internals).

6. **`EpisodeSummary` is a stub** (state.py L89): docstring says "E32C adds richer fields." The ticket's acceptance criteria require `episode_history` to have 2 entries after 2 episodes — the stub is sufficient for the AC. Richer fields (outcome, entity counts, faction outcomes) can be added as needed.

---

## Parity Ledger Overlap

The relevant ledger is `docs/parity_ledger/infrastructure.yaml`.

| ID | Text (summary) | Status | Action required |
|---|---|---|---|
| INFRA-214 | ScenarioRuntimeService kernel lifecycle (E31A+E31B) | `verified` | E32C adds a consumer of `ScenarioRuntimeService` — no status change needed. If a `kernel` or `final_state` property is added to `ScenarioRuntimeService`, add a new INFRA entry for it. |
| INFRA-215 | ScenarioCheckpointer (E31C) | `verified` | No change needed — checkpoint is orthogonal to orchestration. |
| INFRA-217 | CampaignState data model (E32B) | `verified` | No status change needed. E32C populates it — no model change unless EpisodeSummary is extended with richer fields (then update v2_evidence). |

**New entry required:** A new parity entry (suggest **INFRA-218**) must be added for `CampaignOrchestrator` on completion, covering:
- Multi-episode sequence execution via `ScenarioRuntimeService`
- EntityCarryForward extraction path (level, xp, equipment, reputation, alive)
- FactionCarryForward synthesis (faction alive = ≥1 active entity with that faction int)
- Dead entity / destroyed faction filtering on episode spawn
- `episode_history` accumulation after each episode

---

## Prior Work

| Ticket | Status | What it delivered |
|---|---|---|
| TCK-20260619-E32A-RENAME-RUNNER | DONE | Renamed legacy runner; cleared the `runner.py` path for orchestration-layer code |
| TCK-20260619-E32B-CAMPAIGN-STATE | DONE | `src/domains/campaigns/state.py` — all 6 data types with to_dict/from_dict, 17 tests |
| TCK-20260619-E31A-SCENARIO-SERVICE | DONE | `ScenarioRuntimeService` + `ScenarioObjectiveState` + `VictoryCondition` schema |
| TCK-20260619-E31B-OBJECTIVE-FSM | DONE | `ObjectiveEvaluator` wired into `_evaluate_after_tick()` in `scenario_runtime.py` |
| TCK-20260619-E31C-CHECKPOINT | DONE | `ScenarioCheckpointer` — binary checkpoint/restore; re-exported from `scenario_runtime.py` |
| TCK-20260619-E31D-REST-API | DONE | Scenario REST API + `scenario_registry.py` |

**Stored artifacts to check:** `stored_artifacts/` has no E32A or E32B folders confirmed. The E32B ticket lists only `src/domains/campaigns/state.py` and the test file as files changed — no stored artifacts directory was generated (E32B implementation notes confirm this is a pure data model ticket).

---

## Risks and Open Questions

### OQ-1 (DECISION REQUIRED) — How does carry-forward state seed the next episode's AuthoritativeState?

`ScenarioRuntimeService._build_kernel()` calls `AuthoritativeState(tick=0, seed=0)` with no entities pre-loaded. The campaign orchestrator must inject the carry-forward entity states into the next episode's kernel before tick 1 runs. **No mechanism for this exists yet.**

Options:
- (A) Add a `initial_state: Optional[AuthoritativeState]` parameter to `ScenarioRuntimeService.__init__` so the caller can provide a pre-built state. The orchestrator builds a new `AuthoritativeState` from carry-forward data and passes it in.
- (B) Add a `seed_from_carry_forward(entities: Dict[int, EntityCarryForward], ...)` method to the orchestrator that mutates the post-init kernel state before `start()` is called.
- (C) Extend `_build_kernel()` to accept a carry-forward dict and apply it during state construction.

Option A is the cleanest boundary — it doesn't change `ScenarioRuntimeService`'s internal build logic. However it requires that `CampaignOrchestrator` knows how to construct `AuthoritativeState` with pre-seeded entity data (V2EntityBuilder pattern from runner.py).

**This is the primary architectural decision that must be made before implementation begins.**

### OQ-2 (DECISION REQUIRED) — `svc.kernel` or `final_state` property?

The ticket pseudocode uses `svc.kernel.state`. Adding a `kernel` property exposes full kernel internals to the orchestrator. A narrower `final_state: Optional[AuthoritativeState]` property on `ScenarioRuntimeService` is preferable and avoids coupling. Either way, a small change to `scenario_runtime.py` is required.

### OQ-3 (DECISION REQUIRED) — Faction int → str mapping

`entity.identity.faction` is an `int`. `FactionCarryForward.faction_id` is a `str`. E32B docstring says "E32C owns the int→str mapping." The simplest approach is `str(faction_int)` (e.g., `"0"`, `"1"`). A more readable alternative is `f"faction_{faction_int}"`. No faction registry lookup is available in this domain. Decision affects test fixture values and the faction-absent AC.

### OQ-4 — Episode seed per-episode vs fixed

`_build_kernel()` uses `seed=0` always. For a 3-episode campaign to be deterministic, episode seeds must be derived from the campaign spec (e.g., `campaign_seed + episode_index`). This should be part of the new `CampaignSpec` for orchestration.

### OQ-5 — Where does the new orchestrator-level `CampaignSpec` live?

The ticket says `src/domains/campaigns/spec.py` already hosts `CampaignSpecLoader` for the analysis-domain spec. The new orchestrator `CampaignSpec` (with `id`, `episodes: List[SimulationScenarioDefinition]`, `carry_forward_rules`) must be a **different type**. Options: add it to `schema.py` (alongside existing types), create `orchestrator_spec.py`, or put it inline in `orchestrator.py`. Given the project pattern of separating schema from logic, `schema.py` or a new `orchestrator_schema.py` is preferred.

### OQ-6 — carry_forward_rules format

The ticket refers to `CampaignSpec.carry_forward_rules` but does not define its schema. The carry-forward behavior described (entity XP/equipment/rep/injury/alive; faction alive) appears to be a fixed set of rules rather than user-configurable. If `carry_forward_rules` is a simple dataclass/dict of boolean toggles, this is straightforward. If it's a pluggable rule system, scope creep risk is high. Recommend: start with fixed rules; `carry_forward_rules` is a stub `dict` defaulting to all-enabled.

---

## Anti-Drift Hazards

1. **`entity.lifecycle.active` vs `entity.combat.alive`** — `EntityCarryForward.alive` maps to `lifecycle.active` (not `combat.alive`). Using the wrong field produces a wrong alive status for entities in combat-dead but lifecycle-alive state. Test must assert on the correct source field.

2. **`EntityCarryForward.equipment` format** — `EquipmentComponent.slots` uses `EquipSlot` enum keys, not strings. Extraction must convert: `{str(slot): item_id}`. The `durability` dict also uses `EquipSlot` keys. Test must verify string keys in extracted equipment dict.

3. **`public_reputation` is a float on `SocialComponent`** — not a dict. E32B resolved this (OQ-1 in E32B: `reputation: float`). Test must not assume `reputation` is faction-keyed.

4. **`episode_history` accumulation** — must append after each episode completes, not at orchestrator initialization. Test must assert len(episode_history) == N after N episodes.

5. **State isolation** — each `ScenarioRuntimeService` instance must run on its own `AuthoritativeState`. The orchestrator must not reuse the previous episode's service or kernel. Test must confirm episode-2 entity state is derived from carry-forward, not from episode-1's live kernel.

6. **No engine imports in `state.py`** — the import guard test (`test_campaign_state_module_has_no_engine_imports`) must still pass after E32C. E32C imports engine types in `orchestrator.py`, not in `state.py`.

7. **`CampaignSpec` naming collision** — the existing `src/domains/campaigns/schema.py` already has a `CampaignSpec` (analysis-domain). The new orchestrator spec type must use a distinct name (e.g., `CampaignManifest`, `EpisodeCampaignSpec`, or similar) to avoid shadowing.
