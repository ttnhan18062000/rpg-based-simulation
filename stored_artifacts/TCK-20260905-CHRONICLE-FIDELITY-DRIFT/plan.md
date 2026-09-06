---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260905-CHRONICLE-FIDELITY-DRIFT
artifact_type: plan
tags: [social, strategy]
---

# Implementation Plan — TCK-20260905-CHRONICLE-FIDELITY-DRIFT

## Summary

Add a new `FidelityDeriver`/`FidelityState`+`FidelityCarryForward`/`FidelityExporter`-`FidelityImporter`
3-layer Deriver-pattern sibling, in a **new package** `src/domains/fidelity/` (mirroring
`src/domains/culture/{model,deriver,exporter}.py` exactly, one file per layer — the same
"new module, not folded into an existing one" precedent idea 57's own design doc set for
entity-scale `FameState`). `FidelityDeriver.derive(hierarchy)` walks `ChronicleHierarchy.eras` →
`Era.episodes` → `Episode.index` to find each chronicle-worthy event's real era membership (not
`episode // ERA_EPISODE_MIN` arithmetic, which is wrong whenever any episode has zero
chronicle-worthy events), computes a linear fidelity-decay-by-era-distance value keyed by
`NarrativeLedgerEntry.entry_id` (per-event keying, avoiding collision with idea 57's planned
`subject_id`-keyed `entity_fame`), and `FidelityExporter.export()` writes the result into a new
`campaign_state.historical_drift: Dict[str, FidelityCarryForward]` field via the same
direct-dict-mutation-inside-`_advance_state()` pattern `CultureDriftExporter` already uses —
called from the exact same call site, immediately alongside `CultureDriftExporter.export()`, in
`CampaignOrchestrator._advance_state()`. No existing file's read/write behavior changes;
`CultureDeriver`, `BeliefEntry`, `KnowledgeFact`, `grouper.py`, and `significance.py` are all
untouched. Docs (`05_world_evolution.md` new subsection, new `chronicle_fidelity_contract.md`,
new `WORLD-FIDELITY-*` parity entries) are updated last, once the shipped shape is final.

## Concrete Design Decisions (resolving this ticket's own Plan-phase open questions)

**1. Decay formula: linear by era-distance.**
`fidelity = max(0.0, 1.0 - era_distance * FIDELITY_DECAY_PER_ERA)`, with
`FIDELITY_DECAY_PER_ERA: float = 0.2` (module constant in the new `src/domains/fidelity/deriver.py`,
mirroring `NORMALISE_DENOMINATOR = 3.0` in `src/domains/culture/deriver.py:35` — "one constant, one
pure function" is the established stylistic precedent, confirmed by investigation).
Rationale: `CultureDeriver._normalise()`'s own formula (`min(1.0, raw / 3.0)`, `deriver.py:113-115`)
is a saturating accumulation curve for a structurally different purpose (axis strength growing from
repeated events) and is not directly reusable for a distance-decay curve — confirmed by
investigation, which found no code precedent determines this shape either way. Linear is chosen
over stepped or exponential because: (a) AC1 only requires "strictly lower the further ... Era is
from the current Era" — it does not require any specific curve shape; (b) this ticket ships with
no live consumer yet (idea 63 is not built) — inventing an exponential/stepped curve now would be
speculative tuning with nothing to validate it against, and a future consumer ticket can replace
the constant/formula without touching the `FidelityState`/`FidelityCarryForward` shape; (c) linear
is the simplest form that is trivially deterministic and trivially testable byte-for-byte (AC2).
Same-era events (`era_distance == 0`) get `fidelity = 1.0` — unconstrained by AC1 (which only
covers cross-era comparison), and matches "an event you just lived through is fully remembered."

**2. Keying scheme: per-event, via `NarrativeLedgerEntry.entry_id`.**
Confirmed by investigation as the recommended choice; this plan adopts it as-is, no override.
Rationale: `entry_id` is already a deterministic, globally-unique dedup key
(`src/domains/campaigns/state.py:237,246`, format `"{episode}:{tick}:{event_type}:{subject_id}"`),
directly matching the design intent ("a specific recorded event's story degrading," not a
region- or subject-aggregate). It also avoids any key collision with idea 57's planned
`campaign_state.entity_fame: Dict[str, FameCarryForward]` (keyed by `subject_id`), since the two
sibling deriver outputs would otherwise be indistinguishable by key shape alone if both used
`subject_id`. `entry_id` defaults to `""` for legacy pre-dedup-key records
(`state.py:238,246`) — Step 3 below specifies the fallback reconstruction for that case.

**3. New `CampaignState` field name: `historical_drift: Dict[str, FidelityCarryForward]`.**
This is the exact name the ticket's own Scope text proposes ("e.g. `campaign_state.historical_drift`"),
adopted as-is — it already mirrors `region_cultures`'/`entity_fame`'s own field-naming shape
(domain-noun, not layer-noun) and requires no override.

## Steps

### Step 1 — Fidelity model layer: `FidelityState` + `FidelityCarryForward`
**Files:** `src/domains/fidelity/__init__.py` (new, empty), `src/domains/fidelity/model.py` (new)
**Change:** Create a new package `src/domains/fidelity/` and, in `model.py`, define:
```python
from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class FidelityState:
    """Immutable snapshot of one recorded event's remembered-accuracy value.

    fidelity: float in [0.0, 1.0]. 1.0 = fully accurate (just happened / current era).
    Decreases with Era-distance from the current Era (see FidelityDeriver).
    """
    fidelity: float = 1.0

    def to_dict(self) -> dict:
        return {"fidelity": self.fidelity}

    @classmethod
    def from_dict(cls, d: dict) -> "FidelityState":
        return cls(fidelity=d.get("fidelity", 1.0))


@dataclass(frozen=True, slots=True)
class FidelityCarryForward:
    """Durable per-event fidelity snapshot carried across episodes.

    entry_id: the NarrativeLedgerEntry.entry_id this snapshot describes.
    fidelity: the FidelityState as of derived_episode.
    derived_episode: 0-based index of the episode in which this snapshot was derived.
    """
    entry_id: str
    fidelity: FidelityState
    derived_episode: int

    def to_dict(self) -> dict:
        return {
            "entry_id": self.entry_id,
            "fidelity": self.fidelity.to_dict(),
            "derived_episode": self.derived_episode,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "FidelityCarryForward":
        return cls(
            entry_id=d["entry_id"],
            fidelity=FidelityState.from_dict(d.get("fidelity", {})),
            derived_episode=d.get("derived_episode", 0),
        )
```
This is a field-for-field structural mirror of `CultureState`/`CultureCarryForward`
(`src/domains/culture/model.py:23-97`, read in full), substituting the single `fidelity` axis for
`CultureState`'s four axes and `entry_id` for `region_id`. Module-level imports are `from __future__
import annotations` and `from dataclasses import dataclass` only — no `src.engine` or
`src.core.state` import, matching `culture/model.py:19,21`'s own docstring constraint
("MUST NOT import from src.engine or src.core.state at module level," `model.py:6`).
**Do NOT touch:** `src/domains/culture/model.py` itself, `CultureState`, `CultureCarryForward` —
this is a new sibling file, not a shared base class or an edit to the existing model.
**Verify:** No standalone unit test required by test_plan.md for this step in isolation; exercised
indirectly by Step 3's determinism test (`FidelityState` instances compared for byte-identical
output) and Step 4's round-trip test (`FidelityCarryForward.to_dict()`/`from_dict()`).

### Step 2 — Add `campaign_state.historical_drift` field to `CampaignState`
**Files:** `src/domains/campaigns/state.py`
**Change:** Add the import `from src.domains.fidelity.model import FidelityCarryForward` alongside
the existing `from src.domains.culture.model import CultureCarryForward` (`state.py:16`). Add a new
field to the `CampaignState` dataclass immediately after `nemesis_relations`
(`state.py:309`, following the exact same declare-field-plus-comment-block convention used there
and at `region_cultures`, `state.py:301-304`):
```python
historical_drift: Dict[str, FidelityCarryForward] = field(default_factory=dict)
# E62-FIDELITY: per-event chronicle-fidelity snapshots keyed by NarrativeLedgerEntry.entry_id.
# Populated by FidelityExporter at episode end; consumed by FidelityImporter (no live
# consumer yet — idea 63, Belief Grows Around Real History, is the intended eventual reader).
# Derived from ChronicleHierarchy, mirroring region_cultures' own field shape.
```
Then wire it into both serialization methods, following `region_cultures`'s exact
sorted-key pattern (`state.py:343-346` for `to_dict()`, `state.py:392-395` for `from_dict()`):
in `to_dict()` (`state.py:315-356`), add
```python
"historical_drift": {
    k: v.to_dict()
    for k, v in sorted(self.historical_drift.items())
},
```
immediately after the `"nemesis_relations"` entry (`state.py:351-354`); in `from_dict()`
(`state.py:358-404`), add
```python
historical_drift={
    k: FidelityCarryForward.from_dict(v)
    for k, v in d.get("historical_drift", {}).items()
},
```
immediately after the `nemesis_relations=` entry (`state.py:400-403`).
**Enumeration of every other writer to `CampaignState` (shared-resource check):** `CampaignState`
is populated exclusively by `CampaignOrchestrator._advance_state()`
(`src/domains/campaigns/orchestrator.py:210-247`, read in full). Its existing writers, in the order
they run inside that one method, are: `persistent_entities.update()`, `persistent_factions.update()`,
`episode_history.append()`, `narrative_ledger.extend()`, `social_memories.update()`,
`progression_plans.update()`, `_advance_grief_urgencies()` (writes `grief_urgencies`),
`_advance_nemesis_relations()` (writes `nemesis_relations`), a `progression_plans.pop()` cleanup
loop, and finally `CultureDriftExporter.export()` (writes `region_cultures`,
`orchestrator.py:243-246`) immediately before `self._state.episode_index += 1`
(`orchestrator.py:247`). None of these other writers touch `historical_drift` — it is a brand-new
field with no existing writer to collide with. This step only adds the field/serialization
plumbing; Step 5 is what adds the actual writer call, kept as its own step so this step's
correctness (field exists, round-trips) can be verified independently of orchestrator wiring.
**Do NOT touch:** `region_cultures`, `grief_urgencies`, `nemesis_relations`, or any other existing
field's serialization block — add only the new `historical_drift` entries, do not reformat or
reorder the surrounding dict literals.
**Verify:** Exercised by Step 4's round-trip test
(`test_fidelity_carry_forward_round_trips_through_campaign_state_serialization`); no field can be
round-tripped through `to_dict()`/`from_dict()` until this step lands, so that test is the
authoritative check that this step is complete and correct.

### Step 3 — `FidelityDeriver.derive()`
**Files:** `src/domains/fidelity/deriver.py` (new)
**Change:** Pure stateless classmethod, structurally mirroring `CultureDeriver.derive()`
(`src/domains/culture/deriver.py:42-116`, read in full) but computing era-distance decay instead of
additive axis accumulation:
```python
from __future__ import annotations
from typing import TYPE_CHECKING, Dict

from src.domains.fidelity.model import FidelityState

if TYPE_CHECKING:
    from src.domains.chronicle.grouper import ChronicleHierarchy

FIDELITY_DECAY_PER_ERA: float = 0.2


class FidelityDeriver:
    """Derive per-event FidelityState from a ChronicleHierarchy.

    Stateless — all logic in the single classmethod derive().
    """

    @classmethod
    def derive(cls, hierarchy: "ChronicleHierarchy") -> Dict[str, FidelityState]:
        """Derive a fidelity value per chronicle-worthy event, keyed by entry_id.

        Walks hierarchy.eras -> Era.episodes -> Episode.index to find each event's
        real era membership (era ordinals batch the *filtered* episode list, not
        raw episode-index arithmetic -- see ChronicleGrouper._group_eras()).
        Fidelity decreases linearly with era-distance from the current (latest) Era.
        """
        if not hierarchy.eras:
            return {}

        episode_to_era: Dict[int, int] = {}
        for era in hierarchy.eras:
            for ep in era.episodes:
                episode_to_era[ep.index] = era.ordinal
        current_era_ordinal = hierarchy.eras[-1].ordinal

        result: Dict[str, FidelityState] = {}
        for entry in hierarchy.events:
            era_ordinal = episode_to_era.get(entry.episode)
            if era_ordinal is None:
                continue  # defensive: entry's episode absent from the eras it came from
            era_distance = current_era_ordinal - era_ordinal
            fidelity_value = max(0.0, 1.0 - era_distance * FIDELITY_DECAY_PER_ERA)
            key = entry.entry_id or f"{entry.episode}:{entry.tick}:{entry.event_type}:{entry.subject_id}"
            result[key] = FidelityState(fidelity=fidelity_value)
        return result
```
Notes tying this to cited evidence: `Era.ordinal`, `Era.episodes` and `Episode.index` are read from
`src/domains/chronicle/grouper.py:60-71` (`Era`) and `:45-56` (`Episode`) — confirmed both are plain
frozen-dataclass fields, not computed properties, so the walk above is a direct field read, not an
inference. `hierarchy.eras` is a `tuple[Era, ...]` built by `_group_eras()` via
`eras.append(...)` in ascending `ordinal` order starting at 0 (`grouper.py:214-227`, read in full),
so `hierarchy.eras[-1].ordinal` is safely the highest/current ordinal without needing a `max()` scan.
`entry.entry_id`/`entry.episode`/`entry.tick`/`entry.event_type`/`entry.subject_id` are read from
`NarrativeLedgerEntry`'s field list (`src/domains/campaigns/state.py:240-246`) — the `entry_id or
f"..."` fallback reconstructs the exact deterministic format documented at `state.py:237` for
legacy records where `entry_id` defaults to `""` (`state.py:238,246`), avoiding silent key
collisions on an empty string.
**Enumeration of other readers of `ChronicleHierarchy`/`hierarchy.eras`:** `CultureDeriver.derive()`
(`culture/deriver.py:78`) reads `hierarchy.events` only, never `hierarchy.eras` — no overlap risk.
No other code in `src/` currently reads `hierarchy.eras` (confirmed: `ChronicleGrouper` is the sole
producer; `CultureDeriver` and the Chronicle REST/naming/rendering stages consume `hierarchy.events`/
`hierarchy.incidents`/`hierarchy.episodes` per `chronicle_contract.md`'s five-stage pipeline, not
`eras` directly). `FidelityDeriver` is a pure read-only consumer; it does not mutate `hierarchy` or
any of its nested tuples (all frozen dataclasses), so there is no write race to enumerate here.
**Do NOT touch:** `src/domains/chronicle/grouper.py`, `src/domains/chronicle/significance.py` —
this step only *reads* `ChronicleHierarchy`, never modifies era/episode/incident grouping logic.
Do not touch `src/domains/culture/deriver.py`.
**Verify:** `test_fidelity_lowers_with_era_distance` and
`test_fidelity_derive_is_deterministic_byte_identical`
(new file `tests/unit/domains/chronicle/test_fidelity_deriver.py`, per test_plan.md).

### Step 4 — `FidelityExporter` / `FidelityImporter`
**Files:** `src/domains/fidelity/exporter.py` (new)
**Change:** Structural mirror of `CultureDriftExporter`/`CultureDriftImporter`
(`src/domains/culture/exporter.py`, read in full):
```python
from __future__ import annotations
from typing import TYPE_CHECKING, Optional

from src.domains.fidelity.model import FidelityCarryForward

if TYPE_CHECKING:
    from src.domains.campaigns.state import CampaignState
    from src.domains.chronicle.grouper import ChronicleHierarchy
    from src.domains.fidelity.model import FidelityState


class FidelityExporter:
    """Derive fidelity from ChronicleHierarchy and persist into CampaignState.

    Called at episode end from CampaignOrchestrator._advance_state(), immediately
    alongside CultureDriftExporter.export() -- both consume the same _hierarchy local.
    """

    @staticmethod
    def export(
        campaign_state: "CampaignState",
        hierarchy: "ChronicleHierarchy",
        episode_index: int,
    ) -> None:
        from src.domains.fidelity.deriver import FidelityDeriver

        derived = FidelityDeriver.derive(hierarchy)
        for entry_id, fidelity_state in derived.items():
            campaign_state.historical_drift[entry_id] = FidelityCarryForward(
                entry_id=entry_id,
                fidelity=fidelity_state,
                derived_episode=episode_index,
            )


class FidelityImporter:
    """Thin lookup helper for an event's fidelity (no live consumer yet -- idea 63)."""

    @staticmethod
    def get_fidelity(
        campaign_state: "CampaignState",
        entry_id: str,
    ) -> Optional["FidelityState"]:
        cf = campaign_state.historical_drift.get(entry_id)
        if cf is None:
            return None
        return cf.fidelity
```
This is a direct dict-mutation write, matching `CultureDriftExporter.export()`'s own established
pattern exactly (`culture/exporter.py:56-61`) — **not** a `src/engine/patches.py` write, per this
ticket's own corrected Scope text and the investigation's confirmation that `patches.py` has zero
`CampaignState` write path (`src/engine/patches.py:1-806`, read in full).
**Enumeration of every other writer to `campaign_state.historical_drift`:** none exist before this
step (Step 2 only added the field + serialization, no writer). After this step,
`FidelityExporter.export()` is the *only* writer — Step 6's architecture guard test asserts this
stays true. `campaign_state.region_cultures` (the sibling field this pattern mirrors) is written
only by `CultureDriftExporter.export()` (`exporter.py:56-61`) — confirmed no other call site
touches it either, so this step introduces no new collision pattern into `CampaignState`'s existing
one-writer-per-field convention (`grief_urgencies` written only by `_advance_grief_urgencies()`,
`nemesis_relations` only by `_advance_nemesis_relations()`, per Step 2's full writer enumeration).
**Do NOT touch:** `src/domains/culture/exporter.py`. Do not give `FidelityExporter.export()` an
`entity_names` parameter — `CultureDriftExporter`'s own `entity_names` param is documented as
"unused currently, kept for API forward-compat" (`exporter.py:44`); there is no equivalent forward-
compat need here since `FidelityDeriver.derive()` takes no such parameter (Step 3).
**Verify:** `test_fidelity_carry_forward_round_trips_through_campaign_state_serialization`
(new file `tests/unit/domains/chronicle/test_fidelity_exporter.py`, per test_plan.md).

### Step 5 — Wire `FidelityExporter.export()` into `CampaignOrchestrator._advance_state()`
**Files:** `src/domains/campaigns/orchestrator.py`
**Change:** Immediately after the existing `CultureDriftExporter.export(self._state, _hierarchy,
summary.episode_index)` call (`orchestrator.py:246`) and before `self._state.episode_index += 1`
(`orchestrator.py:247`), add:
```python
# E62-FIDELITY: derive and persist chronicle-fidelity drift at the same episode boundary.
from src.domains.fidelity.exporter import FidelityExporter
FidelityExporter.export(self._state, _hierarchy, summary.episode_index)
```
This reuses the exact same `_hierarchy` local `CultureDriftExporter` already consumed two lines
above (`orchestrator.py:245`, `_hierarchy = ChronicleGrouper().group(list(self._state
.narrative_ledger))`) — per the investigation's Anti-Drift Hazard, `FidelityExporter` must never
recompute a separate `ChronicleGrouper().group(...)` call of its own, which could theoretically
diverge if `narrative_ledger` mutated between two separate `.group()` calls (it doesn't today, but
reusing the one local removes the risk entirely rather than merely relying on it not mutating).
**Enumeration of every other writer to `_advance_state()`'s call sequence:** this method is the
single call site for every `CampaignState` mutation in the codebase (see Step 2's full writer
enumeration) and runs exactly once per completed episode, called only from `run_episode()`
(`orchestrator.py:205`, the line directly above `_advance_state()`'s definition). Adding one more
statement at the end of this already-sequential, single-threaded method introduces no ordering
race — every existing write above it (`persistent_entities`, `narrative_ledger`, `region_cultures`,
etc.) has already completed by the time this new line runs, and nothing downstream of it in the
same method reads `historical_drift` back.
**Do NOT touch:** any line before `CultureDriftExporter.export(...)` in `_advance_state()` — do not
reorder `_advance_grief_urgencies()`, `_advance_nemesis_relations()`, or the `dead_ids` cleanup
loop. Do not move `self._state.episode_index += 1` relative to the new call.
**Verify:** `test_fidelity_exporter_runs_alongside_culture_drift_exporter_in_advance_state`
(`tests/unit/domains/campaigns/test_orchestrator_plan_wiring.py`, new test appended, following the
existing `_make_manifest()`/direct-`_advance_state()`-call pattern already in that file, or a new
`tests/unit/domains/campaigns/test_fidelity_wiring.py` — per test_plan.md, either location is
acceptable).

### Step 6 — Architecture guard tests
**Files:** `tests/architecture/test_fidelity_write_paths.py` (new)
**Change:** Three guard tests, using the same `inspect.getsource()` + regex source-text-scan
technique as `tests/architecture/test_clan_reputation_write_paths.py` (read in full) and
`tests/architecture/test_social_write_paths.py`:
1. `test_historical_drift_written_only_through_fidelity_exporter` — scan every other
   `CampaignOrchestrator` method's source (via `inspect.getsource(CampaignOrchestrator)` or a
   targeted per-method scan) for a `historical_drift[` assignment pattern outside
   `FidelityExporter.export`; assert none found. This is the AC4 guard, resolved per the ticket's
   own correction: it asserts the direct-dict-mutation pattern is confined to
   `FidelityExporter.export()`, not that `src/engine/patches.py` is involved (patches.py has no
   `CampaignState` path to assert against).
2. `test_fidelity_module_no_belief_entry_or_knowledge_fact_references` — scan
   `src/domains/fidelity/deriver.py` and `src/domains/fidelity/exporter.py` source text for
   `BeliefEntry(` / `KnowledgeFact(` construction patterns; assert none found. This is the AC5
   scope-creep guard.
3. `test_fidelity_deriver_and_model_no_engine_or_core_state_imports` — scan
   `src/domains/fidelity/model.py` and `src/domains/fidelity/deriver.py` top-level import
   statements (via `ast.parse` on the file source, mirroring the constraint check style already
   documented in `culture/model.py`'s own docstring) for `src.engine` / `src.core.state` imports;
   assert none found.
**Do NOT touch:** `tests/architecture/test_clan_reputation_write_paths.py`,
`tests/architecture/test_social_write_paths.py` — read for pattern only, do not modify.
**Verify:** the three new tests themselves passing is the verification (they are the AC4/AC5/
engine-constraint guards named in test_plan.md); additionally, full regression run of
`tests/unit/domains/culture/`, `tests/unit/domains/chronicle/`, `tests/unit/domains/campaigns/`,
`tests/integration/culture/`, `tests/architecture/test_clan_reputation_write_paths.py`,
`tests/architecture/test_social_write_paths.py` per the Scoped Pytest Command in test_plan.md.

### Step 7 — Docs: Mechanics Bible subsection, new contract doc, parity ledger entries
**Files:** `docs/mechanics/05_world_evolution.md`, `docs/world/chronicle_fidelity_contract.md`
(new), `docs/parity_ledger/world_dynamics.yaml`
**Change:**
- In `docs/mechanics/05_world_evolution.md`, add a new numbered subsection (e.g. "8. Chronicle
  Fidelity Drift (E62)") immediately following §7 "Cultural Drift (E62)" (`lines 555-599` per
  investigation), mirroring that subsection's own structure (axis/value definition, derivation
  trigger, persistence, acceptance signal). Document: the `fidelity` value definition, the linear
  decay-per-era formula and the `FIDELITY_DECAY_PER_ERA = 0.2` constant (Concrete Design Decision
  #1 above), the `entry_id` keying scheme (#2), and that this ships with no live consumer yet
  (idea 63 is the intended future reader) — matching the sibling epic ticket's own disclosure
  convention (`TCK-20260904-LINEAGE-DEATH-DISPATCH`).
- Create `docs/world/chronicle_fidelity_contract.md`, mirroring
  `docs/world/culture_drift_contract.md`'s section structure (Model / Derivation / Persistence /
  Integration Points / Parity Ledger References) exactly, documenting `FidelityState`/
  `FidelityCarryForward`/`FidelityDeriver`/`FidelityExporter`/`FidelityImporter`.
- In `docs/parity_ledger/world_dynamics.yaml`, add new `WORLD-FIDELITY-001`+ entries mirroring the
  `WORLD-CULT-001..003` shape (`status: verified`, `priority: P1`, `v2_evidence` pointing at the new
  test files from Steps 3/4/6, `test_path` set). Use `tools/parity_ledger_writer.py` for this edit
  (per project CLAUDE.md's parity-updater guidance) rather than a raw YAML edit — do not hand-edit
  the full file.
**Do NOT touch:** `docs/simulation/domains/chronicle_contract.md`,
`docs/parity_ledger/social_narrative.yaml`, `docs/brainstorm/rpg_feature_atlas.html`,
`docs/plans/rpg_design_roadmap/rpg_m5_memory_reputation_epic.md`,
`docs/guidelines/intentional_divergences.md` — investigation confirmed none of these require
changes for this ticket (see investigation.md's "Docs Requiring Update" section for the full
per-doc reasoning already established).
**Verify:** No automated test for doc content; verified by the Authoritative Mechanics Rule's own
review step (doc-updater/parity-updater agents) and by `WORLD-FIDELITY-*` entries' `test_path`
fields pointing at real, passing tests from Steps 3, 4, and 6.

## Scope Guards

- Do not touch `src/systems/strategic_systems/belief.py` (`BeliefEntry`) or any `KnowledgeFact`
  definition — confirmed structurally wrong shape by investigation; Out of Scope forbids this by
  name.
- Do not touch `src/domains/culture/deriver.py`, `src/domains/culture/model.py`, or
  `src/domains/culture/exporter.py` — this ticket's new code is a sibling, not an edit to these
  files. `CultureDeriver`'s own test suite (`tests/unit/domains/culture/test_culture_deriver.py`,
  `tests/unit/domains/culture/test_culture_exporter.py`) must pass unmodified (AC5).
- Do not touch `src/domains/chronicle/grouper.py` or `src/domains/chronicle/significance.py` — Out
  of Scope explicitly forbids changing Chronicle's own grouping/significance-scoring logic; this
  ticket only reads `ChronicleHierarchy`.
- Do not route any write through `src/engine/patches.py` — confirmed to have zero `CampaignState`
  write path; the corrected AC4 requires the direct-dict-mutation-inside-`_advance_state()` pattern
  instead (Step 4/5).
- Do not make `FidelityDeriver` a mandatory upstream transform that `CultureDeriver` or idea 57's
  `FameDeriver` must route through — both continue reading `hierarchy.events` directly, unchanged.
- Do not repurpose `src/core/state.py`'s `LifecycleComponent.generation` or `CorpseState.generation`
  fields — confirmed unrelated concepts (hero-rebirth counter, corpse-decay counter).
- Do not build idea 63's belief-institution consumer, or any FidelityImporter *caller* — this
  ticket ships the write path and a thin importer lookup helper only, with no live reader wired in
  (disclosed explicitly in Implementation Notes and the new Mechanics Bible subsection).
- Do not hand-edit `docs/parity_ledger/world_dynamics.yaml`'s full file structure — use
  `tools/parity_ledger_writer.py` for the new entries.

## Dependency Map

- Step 1 (model) — no dependencies; first.
- Step 2 (CampaignState field) — depends on Step 1 (imports `FidelityCarryForward`).
- Step 3 (Deriver) — depends on Step 1 (imports `FidelityState`). Independent of Step 2.
- Step 4 (Exporter/Importer) — depends on Step 1, Step 2, and Step 3.
- Step 5 (orchestrator wiring) — depends on Step 4.
- Step 6 (architecture guards) — depends on Step 1 through Step 5 all existing (scans their source).
- Step 7 (docs) — depends on Step 1 through Step 6 being final/stable (documents the shipped shape,
  including test paths for parity ledger entries).

Steps 2 and 3 can be implemented in either order relative to each other (both only depend on
Step 1); everything else is strictly sequential.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC1 — fidelity strictly lower the further an event's Era is from the current Era | Step 3 | `test_fidelity_lowers_with_era_distance` (`tests/unit/domains/chronicle/test_fidelity_deriver.py`) |
| AC2 — `FidelityDeriver.derive()` called twice with same input is byte-identical | Step 3 | `test_fidelity_derive_is_deterministic_byte_identical` (same file) |
| AC3 — `FidelityExporter.export()` called from same `_advance_state()` call site as `CultureDriftExporter.export()` | Step 5 | `test_fidelity_exporter_runs_alongside_culture_drift_exporter_in_advance_state` (`tests/unit/domains/campaigns/test_orchestrator_plan_wiring.py` or `test_fidelity_wiring.py`) |
| AC4 — `historical_drift` written only from `FidelityExporter.export()`, direct-dict-mutation pattern, no `patches.py` | Step 2, Step 4, Step 5 | `test_historical_drift_written_only_through_fidelity_exporter` (`tests/architecture/test_fidelity_write_paths.py`) |
| AC5 — zero changes to `BeliefEntry`, `KnowledgeFact`, or `CultureDeriver`'s read/write behavior | Step 1, Step 3, Step 4 (by omission — no edits to those files) | `test_fidelity_module_no_belief_entry_or_knowledge_fact_references` (same file) + `tests/unit/domains/culture/test_culture_deriver.py` passing unmodified |

## Anti-Drift Notes

- **Era-membership must be walked, never computed arithmetically.** `episode // ERA_EPISODE_MIN`
  is wrong whenever any episode has zero chronicle-worthy events, because `Era.episodes` batches
  the already-filtered episode list (`grouper.py:199-227`), not raw episode indices. Step 3's
  `episode_to_era` map, built by iterating `hierarchy.eras` → `Era.episodes` → `Episode.index`, is
  the only correct approach — do not "simplify" this to arithmetic during implementation even
  though it looks like it should be equivalent.
- **`entry_id` can be `""` for legacy records** (`state.py:238,246`) — Step 3's fallback
  reconstruction (`entry.entry_id or f"{episode}:{tick}:{event_type}:{subject_id}"`) must not be
  dropped, or multiple legacy entries with empty `entry_id` would silently collide into a single
  dict key and overwrite each other's `FidelityState`.
- **Reuse the orchestrator's existing `_hierarchy` local, do not recompute.** `FidelityExporter`
  must consume the exact same `ChronicleGrouper().group(...)` result `CultureDriftExporter` already
  consumed two lines earlier (`orchestrator.py:245-246`) — a second independent `.group()` call
  is unnecessary and reintroduces a staleness/consistency risk the investigation flagged as a
  hazard to avoid.
- **AC4's `patches.py` wording is already corrected in the ticket text** — do not re-litigate this
  during implementation or "fix" the exporter to route through `patches.py`; that module has zero
  `CampaignState` write path (confirmed by full-file read) and doing so would be unimplementable
  and contradict the ticket's own corrected Scope/AC text.
- **No live consumer is expected or should be built.** Resist the urge to also wire a
  `FidelityImporter.get_fidelity()` call site into anything at episode start — idea 63 (not this
  ticket) is the intended consumer. Adding one now would be scope creep beyond this ticket's stated
  boundary.
- **Do not let `historical_drift` skip serialization wiring.** This is the exact anti-drift hazard
  investigation flagged by name (missed `to_dict()`/`from_dict()` entries breaking checkpoint
  round-tripping silently) — Step 2's two dict-literal additions are mandatory, not optional
  polish, and Step 4's round-trip test is the only thing that would catch a regression here.

## Unresolved Questions

None. The two open Plan-phase questions this ticket's own investigation deferred (decay formula
shape, keying scheme) are resolved above under "Concrete Design Decisions" with rationale; neither
is a genuine architectural blocker. No other open question in investigation.md rises to
blocker status — the AC4/`patches.py` contradiction was the one genuine blocker, and it has already
been resolved by the ticket-text correction this plan was asked to plan against.
