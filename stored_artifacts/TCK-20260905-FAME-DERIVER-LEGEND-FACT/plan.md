---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260905-FAME-DERIVER-LEGEND-FACT
artifact_type: plan
tags: [social, strategy]
---

# Implementation Plan — TCK-20260905-FAME-DERIVER-LEGEND-FACT

## Summary

Implement `FameDeriver`/`FameState`/`FameCarryForward`/`FameExporter`/`FameImporter` as a new
`src/domains/fame/` package, structurally mirroring `FidelityDeriver`/`FidelityState`/
`FidelityCarryForward`/`FidelityExporter`/`FidelityImporter` (`src/domains/fidelity/`, landed same
day via `TCK-20260905-CHRONICLE-FIDELITY-DRIFT`) field-for-field, but keyed by
`NarrativeLedgerEntry.subject_id` and using Option B's event-type rule (`quest_completed` +
`entity_death` where `payload["entity_role"]=="HERO"`), per the already-merged design doc. Add a
new `LegendFact` (+ `LegendFactService`) in the same package as a **lazily-computed, non-durable
read-model** over `FameCarryForward` — not a new `CampaignState` field — gated by a
`FAME_THRESHOLD` module constant. Wire `FameExporter.export()` into
`CampaignOrchestrator._advance_state()` immediately after the existing `FidelityExporter.export()`
call, consuming the same `_hierarchy` local. Unit-test `LegendFact` discoverability by converting
it to a `WorldSignal` (`kind="legend_fact"`) and calling the real `PerceptionFilterService.filter()`
directly — no pipeline/phase wiring, relying on `filter.py`'s existing catch-all
`perceived_opportunities` branch (confirmed by direct read: no new `kind` branch is needed, so
`docs/simulation/domains/perception_contract.md` is not touched). Two Plan-phase decisions the
investigation flagged as genuinely open are resolved below with cited rationale: (1) `FameState` is
a **single fame axis** (not fame+notoriety), `fame_threshold = 0.5`; (2) `LegendFact` lives in
`src/domains/fame/legend.py`, is constructed lazily by `LegendFactService.for_entity()` at
query/test time (never persisted), and is converted to a `WorldSignal` by
`LegendFactService.to_world_signal()` in the same module.

## Plan-Phase Decisions (resolving the investigation's two open questions)

### Decision 1 — FameState axis count and fame_threshold value

**Axis count: single `fame: float` axis, not a fame+notoriety split.**

Rationale:
- The direct structural precedent for this ticket is `FidelityState`
  (`src/domains/fidelity/model.py:27-35`), which is a **single-axis** frozen dataclass
  (`fidelity: float = 1.0`) — not `CultureState`'s 4-axis shape
  (`src/domains/culture/model.py:24-49`). Fidelity is the more relevant precedent: it is the other
  idea-57-epic sibling deriver that landed the same day, also has "no live consumer yet," and the
  design doc's own aggregation-shape recommendation for Fame does not specify multiple axes.
- Confirmed via direct read (`src/core/updates.py:300-301`, `src/systems/social_systems/
  relationships.py:99-102`) that a real heroism/notoriety split **already exists** as a live
  mechanism: `SocialUpdate.heroism_delta`/`notoriety_delta` feed `SocialRecord.heroism_score`/
  `notoriety_score`/`public_reputation` at the per-encounter social-consequence layer. This is a
  structurally separate, already-shipped mechanism. Mirroring that same split inside the new
  Chronicle-derived `FameState` would duplicate its job, not add coverage.
- Option B's own event set (`quest_completed` + HERO `entity_death`) contains **zero
  fame-reducing event types** — there is no dishonor/defeat/betrayal-attributed-to-subject event in
  scope (adding one is explicitly Out of Scope: "Adding a new combat_victory/monster_slain
  Narrative Ledger event type... new event-scoring, not aggregation"). A `notoriety` axis with no
  accumulation input would sit permanently at `0.0` — durable-shaped state with no real writer and
  no defined lifecycle, which the Durable State Rule and "Do not create hidden or implicit durable
  behavior" hard rule both caution against. A future ticket that adds a fame-reducing event type is
  the place to revisit this, not this one.

**`fame_threshold = 0.5`**, reusing `CHRONICLE_THRESHOLD` (`src/domains/chronicle/
significance.py:41`, `CHRONICLE_THRESHOLD: float = 0.5`) as the anchor.

Rationale: no anchor exists in the design doc or codebase for a *new* number, but
`CHRONICLE_THRESHOLD` is an existing, already-authoritative constant operating on the identical
`[0.0, 1.0]` normalized scale (`FameDeriver` normalizes via the mandated
`min(1.0, raw / NORMALISE_DENOMINATOR)` formula, same as `CultureDeriver`/would-be `FidelityDeriver`
range) and expresses the same underlying concept this ticket needs: "has this crossed the bar to be
considered narratively significant enough to be noticed." Reusing it avoids inventing an arbitrary
number and ties `LegendFact` construction to a concept the codebase already treats as the
significance cutoff. Concretely (verified via `src/domains/campaigns/orchestrator.py:63-68`
`_SIGNIFICANCE_MAP`, the source of `NarrativeLedgerEntry.significance`): a single `quest_completed`
entry contributes raw `0.7`, a single HERO `entity_death` contributes raw `0.5` (no hero-bonus is
applied to this field — that bonus is `EventSignificanceScorer.score()`'s own separate concept, at
`src/domains/chronicle/significance.py:69-71`, used only for chronicle-worthiness filtering, not for
`entry.significance`). Normalized by `/3.0`, one event alone (`0.7/3.0≈0.233` or `0.5/3.0≈0.167`)
never crosses `0.5`; two `quest_completed` entries (`1.4/3.0≈0.467`) still falls just short; three
events or a `quest_completed`+HERO-death combination (`≥1.5` raw) clears it — i.e. becoming a
"living legend" requires roughly 2-3 significant hero-events, consistent with
`NORMALISE_DENOMINATOR=3.0`'s own documented intent ("three high-significance events saturate an
axis," `src/domains/culture/deriver.py:18`).

**Confirmed hazard to document, not fix:** `orchestrator.py:68` maps `QUEST_FAILED` to
`event_type="quest_completed"` with `significance=0.3` (same string as a real success, which is
`0.7`). `ChronicleGrouper.group()` filters purely on `EventSignificanceScorer.score()`
(`src/domains/chronicle/significance.py:69`, `BASE_SIGNIFICANCE.get(entry.event_type, 0.1)` — keyed
by `event_type` string alone, not by `entry.significance` or success/failure), and
`BASE_SIGNIFICANCE["quest_completed"]=0.7` regardless of outcome, so a `QUEST_FAILED`-derived entry
passes the chronicle-worthiness gate (`score=0.7 ≥ CHRONICLE_THRESHOLD=0.5`) exactly like a real
success and lands in `hierarchy.events`. `FameDeriver`, mirroring `CultureDeriver`'s own pattern of
matching purely on `entry.event_type` (never on payload success/failure), will therefore sum a
failed quest's raw `0.3` into fame alongside successes' `0.7` — a real, confirmed characteristic of
the existing `NarrativeLedgerEntry`/`_SIGNIFICANCE_MAP` taxonomy, not something `FameDeriver` should
special-case (Option B's design doc says "quest_completed entries," matching the literal
`event_type` field; inventing a payload-based success/failure filter would be scope creep beyond the
merged design doc). Document this in the Mechanics Bible entry (Step 8) as a disclosed
characteristic, at lower magnitude (0.3 vs 0.7) but not zero.

### Decision 2 — Where LegendFact lives, construction trigger, and its WorldSignal shape

**Module:** `src/domains/fame/legend.py` (same package as `FameState`/`FameDeriver`/`FameExporter`
— not a new top-level domain, not inside `src/domains/perception/`). `LegendFact`'s only real input
is `FameState`, which already lives in this package; keeping it here means the "no live
consumer yet" boundary stays contained in one package, exactly as `FidelityImporter` stays idle
inside `src/domains/fidelity/` without spilling into any consumer package.

**Construction trigger: lazy, query-time — NOT eager inside `FameExporter.export()`, and NO new
`CampaignState` field for `LegendFact` itself.**

`LegendFactService.for_entity(campaign_state, subject_id, entity_name=None) -> Optional[LegendFact]`
calls `FameImporter.get_fame(campaign_state, subject_id)`; returns `None` if no `FameState` exists
or its `.fame < FAME_THRESHOLD`; otherwise constructs and returns a `LegendFact`.

Rationale: `LegendFact` does not need to "survive beyond the current tick or current function call"
independently — it is fully and deterministically reconstructible from `FameCarryForward`
(`CampaignState.entity_fame`), which is *itself* the actual durable, typed record with a defined
lifecycle (derive → export → carry-forward). Per the Durable State Rule, only things that must
survive need their own typed model + stable `CampaignState` location; `LegendFact` is a derived
read-model, analogous to how `CultureDriftImporter.get_culture()` returns a plain `CultureState`
snapshot without a second persisted record. An eager-construction alternative would require a new
`CampaignState.legend_facts` field (its own write path, its own architecture guard test, its own
parity-ledger entries, its own serialization round-trip) for a value that is a pure function of data
already persisted — unnecessary surface area for a feature this ticket already discloses as "built,
not yet visible in play." No `CampaignState` change is made for `LegendFact`; only `entity_fame` (an
actual carry-forward record) is added (Step 3).

**WorldSignal wrapping:** `LegendFactService.to_world_signal(fact: LegendFact, position:
Tuple[float, float] = (0.0, 0.0)) -> WorldSignal`, also in `legend.py`, importing only
`WorldSignal` (a plain data type, `src/domains/perception/salience.py:14-30`) — never
`PerceptionUpdatePhase` or `PerceptionFilterService`. Constructs
`WorldSignal(signal_id=f"legend:{fact.subject_id}", kind="legend_fact", position=position,
base_relevance=fact.fame, danger_level=0.0, is_novel=False)`. `position` must be an explicit
parameter (default `(0.0, 0.0)`) because `LegendFact`/`FameState` have no location concept of their
own (a hero's fame isn't location-bound) — confirmed by reading `FameState`'s only source field is
`fame: float`; there is no coordinate anywhere in the Fame data model to derive one from.

**`kind="legend_fact"` uses the existing catch-all branch — no `filter.py` change.** Confirmed by
direct read of `src/domains/perception/filter.py:83-119`: the classification `if/elif` chain checks
`entity`/`HERO`/`MONSTER`, then `healing_resource`/`food_source`/`crafting_material`, then
`blacksmith`/`town_inn`/`guild_intel`/`shop_merchant`, then `threat`; anything else (line 115-119,
the bare `else`) lands in `perceived_opportunities`. `"legend_fact"` matches none of the explicit
sets, so it is classified into `perceived_opportunities` today with zero code changes to `filter.py`.
This is the minimal-footprint choice: it satisfies AC4 without touching a file every other signal
kind also shares, and without needing a new typed `PerceivedX` container. Per
`docs/simulation/domains/perception_contract.md`'s own Extension Rules, adding an explicit branch is
*sanctioned* but not *required* — since this plan does not add one,
`docs/simulation/domains/perception_contract.md` is **not** modified (resolves the investigation's
conditional docs bullet as "not met"). A future ticket wiring a real live consumer can add a
dedicated typed container then, if warranted.

## Steps

### Step 1 — `FameState` / `FameCarryForward` data model
**Files:** `src/domains/fame/__init__.py` (new, empty package marker — mirror
`src/domains/fidelity/__init__.py`), `src/domains/fame/model.py` (new)

**Change:** Create `FameState` as a frozen, slotted dataclass with one field, `fame: float = 0.0`,
plus `to_dict()`/`from_dict()`, mirroring `FidelityState` verbatim
(`src/domains/fidelity/model.py:27-42`, single-axis shape, per Decision 1 above). Create
`FameCarryForward` (`subject_id: str`, `fame: FameState`, `derived_episode: int`) with matching
`to_dict()`/`from_dict()`, mirroring `FidelityCarryForward` verbatim
(`src/domains/fidelity/model.py:45-76`), renaming `entry_id`→`subject_id` and `fidelity`→`fame` per
the ticket's own field names. Module docstring must state the same constraints
`FidelityState`'s docstring states (no `src.engine`/`src.core.state` import, frozen, JSON-safe
round-trip) — verified by Step 2's guard test.

**Do NOT touch:** `src/domains/culture/model.py`, `src/domains/fidelity/model.py` (read-only
precedents, not to be imported from or modified).

**Verify:** No test yet (pure data model) — exercised indirectly by Step 2's deriver tests.

---

### Step 2 — `FameDeriver.derive()`
**Files:** `src/domains/fame/deriver.py` (new), `tests/unit/domains/fame/__init__.py` (new),
`tests/unit/domains/fame/test_fame_deriver.py` (new)

**Change:** `FameDeriver.derive(hierarchy, entity_names=None) -> Dict[str, FameState]`, mirroring
`CultureDeriver.derive()` verbatim (`src/domains/culture/deriver.py:48-115`) but:
- Keyed by `entry.subject_id` (not `entry.payload.get("region_id")`) — no `"__global__"` fallback
  string is needed since `subject_id` defaults to `""` per `NarrativeLedgerEntry`
  (`src/domains/campaigns/state.py:244`), and an empty-string subject should simply not accumulate
  fame (skip entries with falsy `subject_id`, since Fame is per-entity and an unattributed event
  has no entity to credit).
- Event rule (Option B, module-local frozensets, not imported from `culture/deriver.py`):
  `etype == "quest_completed"` → add `entry.significance` (see Decision 1's disclosed
  quest-failure caveat); `etype == "entity_death" and entry.payload.get("entity_role") == "HERO"`
  → add `entry.significance`. No other event types contribute (explicitly do not add
  `"LEGENDARY_ARRIVAL"`, `"faction_shift"`, `"calamity"`, or any war/diplomatic type).
- Module-local `NORMALISE_DENOMINATOR: float = 3.0` and `_normalise(raw) -> min(1.0, raw /
  NORMALISE_DENOMINATOR)`, verbatim copy of `CultureDeriver._normalise`
  (`src/domains/culture/deriver.py:113-115`) — a fresh module constant, not an import from
  `culture/deriver.py`, matching how `fidelity/deriver.py` keeps its own constants independent.

**Other writers to this shared resource:** `hierarchy.events` (a `tuple`, read-only,
`src/domains/chronicle/grouper.py`) is produced once per `_advance_state()` call and consumed by
three derivers in the same call (`CultureDeriver`, `FidelityDeriver`, now `FameDeriver`) — all are
read-only over it (confirmed: `CultureDeriver.derive()` never mutates `hierarchy` or its entries).
`FameDeriver.derive()` must be equally read-only; adding it introduces no new writer, only a third
reader.

**Do NOT touch:** `src/domains/culture/deriver.py`'s `_FATALISM_EVENTS`/`_CONFLICT_EVENTS`/
`_SCARCITY_EVENTS` frozensets or its `NORMALISE_DENOMINATOR` (do not import or alias it — Fame's
own copy must be independent so a future change to Culture's denominator cannot silently affect
Fame).

**Verify:** `test_fame_deriver_attributes_two_subjects_distinctly`,
`test_fame_deriver_only_option_b_events_contribute`,
`test_fame_deriver_empty_hierarchy_returns_empty_dict`,
`test_fame_deriver_normalises_like_culture_deriver`,
`test_fame_deriver_is_deterministic_byte_identical` (all in `tests/unit/domains/fame/
test_fame_deriver.py`, per test_plan.md items 1-3 and the determinism guard).

---

### Step 3 — `CampaignState.entity_fame` field
**Files:** `src/domains/campaigns/state.py`

**Change:** Add `from src.domains.fame.model import FameCarryForward` to the module-level import
block (`state.py:14-17`, alongside the existing `CultureCarryForward`/`FidelityCarryForward`
imports — confirmed these are plain module-level imports, not `TYPE_CHECKING`-guarded, so
`state.py`'s own "must NOT import `src.engine`/`src.core.state`" docstring constraint,
`state.py:6-7`, does not forbid this). Add exactly three things, in the same shape
`historical_drift` already uses (`state.py:315-319` field, `361-364` in `to_dict()`, `414-417` in
`from_dict()`):
1. Field: `entity_fame: Dict[str, FameCarryForward] = field(default_factory=dict)` with a comment
   block matching the `# E62-FIDELITY:` style already used for `historical_drift`.
2. `to_dict()`: `"entity_fame": {k: v.to_dict() for k, v in sorted(self.entity_fame.items())}`,
   inserted after the `"historical_drift"` entry (line 364).
3. `from_dict()`: `entity_fame={k: FameCarryForward.from_dict(v) for k, v in
   d.get("entity_fame", {}).items()}`, inserted after the `historical_drift=` block (line 417).

Key type is `str` (matching `subject_id`'s type and `historical_drift`'s own `Dict[str, ...]`
shape) — **not** `int` like `persistent_entities`/`social_memories`, so no `str(k)`/`int(k)` casting
is needed in either serialization method (confirmed by reading `state.py:349-352` vs `361-364`: the
`int`-keyed dicts use `str(k)` in `to_dict()`; the `str`-keyed `region_cultures`/`historical_drift`
do not).

**Other writers to this shared resource:** `CampaignState` (`state.py:273-282`) is written by
`CampaignOrchestrator._advance_state()` and its helper methods for many other fields
(`persistent_entities`, `narrative_ledger`, `social_memories`, `grief_urgencies`,
`nemesis_relations`, `progression_plans`, `region_cultures`, `historical_drift`) — none of those
existing writers touch `entity_fame`; this step only adds the field declaration and
serialization wiring, no writer yet (the writer is Step 4).

**Do NOT touch:** any other field declaration, `to_dict()`, or `from_dict()` entry in this class.

**Verify:** exercised by Step 4's `test_fame_exporter_round_trips_through_campaign_state_
serialization`-style test (mirroring `test_culture_exporter.py:77-85`).

---

### Step 4 — `FameExporter` / `FameImporter`
**Files:** `src/domains/fame/exporter.py` (new), `tests/unit/domains/fame/test_fame_exporter.py`
(new)

**Change:** `FameExporter.export(campaign_state, hierarchy, episode_index, entity_names=None) ->
None` (staticmethod), mirroring `CultureDriftExporter.export()` verbatim
(`src/domains/culture/exporter.py:30-61`): calls `FameDeriver.derive(hierarchy,
entity_names=entity_names)`, then for each `(subject_id, fame_state)` writes
`campaign_state.entity_fame[subject_id] = FameCarryForward(subject_id=subject_id, fame=fame_state,
derived_episode=episode_index)` — direct dict index-assignment, confirmed as the correct convention
(`CampaignState` is **not frozen**, `state.py:280`; there is no `src/engine/patches.py` write path
for `CampaignState` at all — `patches.py`'s authoritative-apply-path law is scoped to per-tick
`EntityState`, confirmed by the sibling Fidelity ticket's own investigation and re-confirmed here by
reading `state.py:273-282`'s explicit "NOT frozen" docstring). Entries for subjects absent from this
episode's `hierarchy` are left untouched (same "persists until overwritten" guarantee
`CultureDriftExporter`/`FidelityExporter` both give). `FameImporter.get_fame(campaign_state,
entity_id) -> Optional[FameState]`, a thin `None`-safe lookup mirroring
`CultureDriftImporter.get_culture()` verbatim (`src/domains/culture/exporter.py:67-79`).

**Other writers to `campaign_state.entity_fame`:** none besides this exporter — this is the sole
authoritative writer, enforced by Step 7's architecture guard. No other existing code path (grep
confirmed zero occurrences of `entity_fame[` anywhere in `src/` today, since the field doesn't exist
until Step 3) writes it, and this step must not introduce a second one (e.g. do not also assign it
inside `CampaignOrchestrator._build_initial_state()` or any other method — the exact class of
undisclosed second-write-path bug the idea-60 ticket caught).

**Do NOT touch:** `CultureDriftExporter`/`CultureDriftImporter`, `FidelityExporter`/
`FidelityImporter` (read-only precedents).

**Verify:** `test_fame_exporter_populates_entity_fame`,
`test_fame_exporter_preserves_untouched_entity_across_zero_event_episode` (both in
`tests/unit/domains/fame/test_fame_exporter.py`, per test_plan.md item 4).

---

### Step 5 — Wire `FameExporter.export()` into `CampaignOrchestrator._advance_state()`
**Files:** `src/domains/campaigns/orchestrator.py`, `tests/unit/domains/campaigns/
test_fame_wiring.py` (new)

**Change:** Insert, immediately after the existing `FidelityExporter.export()` call
(`orchestrator.py:247-249`) and before `self._state.episode_index += 1` (`orchestrator.py:250`):
```python
# E-FAME: derive and persist fame drift at the same episode boundary.
from src.domains.fame.exporter import FameExporter
FameExporter.export(self._state, _hierarchy, summary.episode_index)
```
Consumes the same `_hierarchy` local already produced at `orchestrator.py:245`
(`ChronicleGrouper().group(list(self._state.narrative_ledger))`) — **do not** call
`ChronicleGrouper().group()` a second time.

**Other writers to `_advance_state()`'s call sequence:** this method already chains, in fixed
order: entity/faction carry-forward extraction, narrative-ledger extension, chronicle-event
emission, social-memory update, progression-plan export/prune, grief-urgency advance, nemesis-
relation advance, `CultureDriftExporter.export()`, `FidelityExporter.export()`, then
`episode_index` increment (`orchestrator.py:216-250`). This step's insertion point (right after
`FidelityExporter.export()`, before the increment) does not reorder any of these — it only adds one
more call between the last existing exporter call and the increment, so no other writer's ordering
guarantee changes.

**Do NOT touch:** the ordering or logic of any other call in `_advance_state()` (grief urgencies,
nemesis relations, progression-plan pruning, `CultureDriftExporter`/`FidelityExporter` themselves).
Watch `tests/architecture/test_phase18_import_boundaries.py` for a pinned-import-line-number
assertion that may shift because of the new `import` line — re-pin deliberately if it fails, per
the sibling Fidelity ticket's own noted lesson; do not silently ignore a failure here.

**Verify:** `test_fame_wiring_advance_state_calls_fame_exporter_alongside_culture_and_fidelity`
(mirrors `tests/unit/domains/campaigns/test_fidelity_wiring.py`'s exact pattern, extended to assert
`region_cultures`, `historical_drift`, and `entity_fame` are all populated from one
`_advance_state()` call).

**Depends on:** Steps 3 and 4 (needs `entity_fame` field + `FameExporter` to exist).

---

### Step 6 — `LegendFact` + `LegendFactService`
**Files:** `src/domains/fame/legend.py` (new), `tests/unit/domains/fame/test_legend_fact.py` (new)

**Change:** Per Decision 2 above:
- `FAME_THRESHOLD: float = 0.5` module constant, with a comment citing
  `src/domains/chronicle/significance.py:41`'s `CHRONICLE_THRESHOLD` as the reused anchor.
- `LegendFact`: frozen dataclass, fields `subject_id: str`, `fame: float` (the axis value that
  crossed threshold — a plain float snapshot, not a live reference to `FameState`, so the fact
  can't silently change after construction), optional `entity_name: Optional[str] = None`. Add
  `to_dict()` for debug-inspection consistency with every other typed record in this ticket (not
  required by the Durable State Rule since `LegendFact` is not itself durable, but cheap and
  consistent).
- `LegendFactService.for_entity(campaign_state, subject_id, entity_name=None) ->
  Optional[LegendFact]`: calls `FameImporter.get_fame(campaign_state, subject_id)`; returns `None`
  if the result is `None` or `.fame < FAME_THRESHOLD`; else returns
  `LegendFact(subject_id=subject_id, fame=result.fame, entity_name=entity_name)`.
- `LegendFactService.to_world_signal(fact, position=(0.0, 0.0)) -> WorldSignal`: imports
  `WorldSignal` from `src.domains.perception.salience` (type-only import — no
  `PerceptionUpdatePhase`, no `PerceptionFilterService`, no pipeline import) and returns
  `WorldSignal(signal_id=f"legend:{fact.subject_id}", kind="legend_fact", position=position,
  base_relevance=fact.fame, danger_level=0.0, is_novel=False)`.

**Do NOT touch:** `src/domains/perception/salience.py`, `src/domains/perception/filter.py`,
`src/domains/perception/phase.py` — this step only *imports* `WorldSignal`'s constructor, it does
not modify the perception package.

**Verify:** `test_legend_fact_constructed_only_above_threshold`,
`test_legend_fact_not_constructed_below_threshold` (both in
`tests/unit/domains/fame/test_legend_fact.py`, per test_plan.md item 6).

**Depends on:** Step 4 (`FameImporter.get_fame`).

---

### Step 7 — Architecture guards
**Files:** `tests/architecture/test_fame_legend_fact_distinctness.py` (new, combines what
test_plan.md splits across items 8 and the anti-drift guards — kept as one file scoped to the new
`src/domains/fame/` package, mirroring `tests/architecture/test_fidelity_write_paths.py`'s exact
`inspect`/regex/AST technique read at `tests/architecture/test_fidelity_write_paths.py:1-119`)

**Change:** Four guard tests, each a direct structural mirror of
`test_fidelity_write_paths.py`'s four tests, retargeted at `src/domains/fame/`:
1. `test_entity_fame_written_only_through_fame_exporter` — regex scan `\bentity_fame\s*\[` across
   all `src/**/*.py`, allowlisting only `src/domains/fame/exporter.py`
   (mirrors `test_historical_drift_written_only_through_fidelity_exporter`,
   `test_fidelity_write_paths.py:56-72`).
2. `test_fame_module_no_belief_entry_knowledge_fact_or_legendary_arrival_references` — regex scan
   for `\b(BeliefEntry|KnowledgeFact|LegendaryArrivalEvent|LEGENDARY_ARRIVAL)\s*[\(=]` (extends the
   `_BELIEF_OR_KNOWLEDGE_PATTERN` technique, `test_fidelity_write_paths.py:42`, with the
   `LegendaryArrivalEvent`/`LEGENDARY_ARRIVAL` exclusion this ticket specifically needs) across
   `src/domains/fame/model.py`, `deriver.py`, `exporter.py`, `legend.py`.
3. `test_fame_deriver_and_model_no_engine_or_core_state_imports` — AST import scan for
   `src.engine`/`src.core.state` prefixes (mirrors `test_fidelity_write_paths.py:96-118`), scoped
   to `src/domains/fame/model.py` and `src/domains/fame/deriver.py` only (matching the sibling's
   own scoping — `exporter.py`/`legend.py` are allowed to import `CampaignState`/`WorldSignal`
   types under `TYPE_CHECKING`/direct import respectively, same as `FidelityExporter` does).
4. `test_fame_module_no_perception_update_phase_call_site_increase` — source-text scan of
   `src/domains/perception/phase.py` and the `AuthoritativeApplyPipeline.refine()` method's own
   source confirming `PerceptionUpdatePhase(` still has zero live pipeline call sites (per
   AC4's explicit wording), plus a companion assertion that `compute_bias_multiplier(` still has
   zero call sites outside `src/domains/motivation/service.py` itself.

**Do NOT touch:** `tests/architecture/test_fidelity_write_paths.py`,
`tests/architecture/test_social_write_paths.py`,
`tests/architecture/test_clan_reputation_write_paths.py` (existing sibling guards, read-only
precedents — do not edit their allowlists to include Fame).

**Verify:** all four tests above must pass; run alongside Step 2/4's own suites.

**Depends on:** Steps 1, 2, 4, 6 (scans their output files).

---

### Step 8 — `LegendFact` discoverability via `PerceptionFilterService.filter()`
**Files:** `tests/unit/domains/perception/test_legend_fact_discoverability.py` (new)

**Change:** One new test file (kept separate from `test_phase12_perception_filter_service.py` per
test_plan.md item 7, so Step 7's guard #4 stays a clean scan). Construct an `EntityState(id=1,
kind="HERO")` (minimal fixture, confirmed sufficient by the existing pattern at
`tests/unit/domains/perception/test_phase12_perception_filter_service.py:7`, which relies on
`EntityState`'s own defaults for `navigation.position`/`cognition.subjective.emotion` — no new
fixture helper needed). Build a `LegendFact` via `LegendFactService.for_entity()` against a
`CampaignState` seeded through `FameExporter.export()` with fame above threshold, convert it via
`LegendFactService.to_world_signal()`, and call `PerceptionFilterService.filter(entity,
[signal], PerceptionBudget())` directly (no `PerceptionUpdatePhase` involved anywhere in the test).
Assert the returned `PerceptionUpdate.perceived_opportunities` contains the signal's
`signal_id` with `salience > 0.0` (per Decision 2, `"legend_fact"` lands in the existing catch-all
branch, `src/domains/perception/filter.py:115-119` — no new typed container).

**Do NOT touch:** `src/domains/perception/filter.py`, `src/domains/perception/salience.py`,
`src/domains/perception/phase.py`, `tests/unit/domains/perception/
test_phase12_perception_filter_service.py`, `tests/unit/domains/perception/
test_phase12_signal_salience_evaluator.py`, `tests/unit/domains/perception/
test_phase12_attention_focus_service.py` (all read-only regression surface per test_plan.md).

**Verify:** `test_legend_fact_discoverable_via_perception_filter_service` (test_plan.md item 7).

**Depends on:** Steps 4 and 6.

---

### Step 9 — Docs and parity ledger
**Files:** `docs/mechanics/05_world_evolution.md`, `docs/parity_ledger/world_dynamics.yaml`,
`docs/world/fame_legend_contract.md` (new), `docs/plans/rpg_design_roadmap/
rpg_m5_memory_reputation_epic.md`

**Change:**
- `docs/mechanics/05_world_evolution.md`: new §9 "Living Legend Fame (idea 57)," mirroring §7
  "Cultural Drift (E62)" / §8 "Chronicle Fidelity Drift (E62)"'s exact structure (axis definition —
  single `fame` axis per Decision 1, source events, `NORMALISE_DENOMINATOR=3.0`, derivation trigger
  citing `orchestrator.py:247-249`'s exact call-site language, `FAME_THRESHOLD=0.5` and its
  `CHRONICLE_THRESHOLD` anchor, the disclosed quest-failure-contributes-fame characteristic from
  Decision 1, persistence in `CampaignState.entity_fame`, an honest "No Live Consumer Yet"-style
  disclosure matching §8's own precedent for the perception/motivation dormancy, and an Acceptance
  Signal one-liner).
- `docs/parity_ledger/world_dynamics.yaml`: new entries `WORLD-FAME-001` (derivation +
  persistence rule, `status: verified`, `priority: P1` or `P2`, `test_path:
  tests/unit/domains/fame/test_fame_deriver.py`) and `WORLD-FAME-002` (determinism +
  round-trip-serialization + `LegendFact` threshold-gating, `test_path:
  tests/unit/domains/fame/test_legend_fact.py`), directly mirroring the `WORLD-FIDELITY-001`/`-002`
  entry shape read at `docs/parity_ledger/world_dynamics.yaml:1980-2004`.
- `docs/world/fame_legend_contract.md` (new): mirrors `docs/world/chronicle_fidelity_contract.md`'s
  own section structure.
- `docs/plans/rpg_design_roadmap/rpg_m5_memory_reputation_epic.md`: a "Status update, 2026-09-05"
  annotation under idea 57's existing numbered item, matching idea 60's/idea 62's own convention in
  this doc.

**Do NOT touch:** `docs/parity_ledger/social_narrative.yaml` (the `LEGENDARY_ARRIVAL`/
`SOC-CROSS-EP-005` entries describe the unrelated faction-reputation mechanism — not touched),
`docs/parity_ledger/strategic_cognition.yaml`, `docs/mechanics/04_strategic_cognition.md` §5,
`docs/simulation/domains/perception_contract.md` (per Decision 2, no new `kind` branch was added,
so this doc's Extension Rules obligation is not triggered — do not edit it),
`docs/brainstorm/2026-09-04-idea57-entity-scale-fame-aggregation-design.md` (frozen, read-only per
its own text), `docs/brainstorm/rpg_expected_schemas.html` (schema `#schema-57` explicitly
"read-only, not edited").

**Verify:** no automated test; verified by `done-checker`'s frontmatter/parity checks and manual
review that `WORLD-FAME-*` entries have real, passing `test_path` values.

**Depends on:** Steps 1-8 (documents the shipped shape, not written first).

## Scope Guards

- Do not wire `PerceptionUpdatePhase` into `AuthoritativeApplyPipeline.refine()` or any other live
  pipeline phase.
- Do not add or wire any call site for `MotivationBiasService.compute_bias_multiplier()`.
- Do not extend `src/ai/coming_of_age.py`'s `_CANDIDATE_ROLES` tuple.
- Do not add a `combat_victory`/`monster_slain` (or any other new) Narrative Ledger event type, and
  do not widen `FameDeriver`'s event-type match beyond exactly `quest_completed` and
  `entity_death`+`HERO`.
- Do not route `FameExporter`'s write through `src/engine/patches.py`.
- Do not add a second `ChronicleGrouper().group()` call in `_advance_state()`.
- Do not let `LegendFact` read `social_memories`/`faction_reputation` or reference
  `LegendaryArrivalEvent`/`LEGENDARY_ARRIVAL` in any form.
- Do not add a `CampaignState.legend_facts` (or similarly named) durable field — `LegendFact` is
  intentionally non-durable/lazily computed per Decision 2.
- Do not modify `src/domains/culture/*` or `src/domains/fidelity/*` (read-only precedents).
- Do not modify `src/domains/perception/filter.py`, `salience.py`, or `phase.py`.
- Do not modify `docs/parity_ledger/social_narrative.yaml`,
  `docs/simulation/domains/perception_contract.md`, or the frozen idea-57 design doc / schema.
- Do not touch idea 62's (`Fidelity`) or idea 63's (belief-institution) own scope — sibling/
  downstream tickets.

## Dependency Map

- Step 1 → Step 2 (deriver needs `FameState`)
- Step 1 → Step 3 (`CampaignState` needs `FameCarryForward`)
- Step 3, Step 2 → Step 4 (exporter needs the field and the deriver)
- Step 4 → Step 5 (wiring needs `FameExporter`)
- Step 4 → Step 6 (`LegendFactService` needs `FameImporter`)
- Step 6 → Step 8 (discoverability test needs `LegendFactService`)
- Steps 1, 2, 4, 6 → Step 7 (guards scan all four modules' finished source)
- Steps 1-8 → Step 9 (docs describe the shipped shape)
- Steps 3, 6 are otherwise independent of each other and of Step 5/8 until their respective
  dependency arrives — most steps can be implemented and unit-verified in isolation before the
  next step begins.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC1: `FameDeriver.derive()` on a hierarchy with a `quest_completed` entry and a HERO `entity_death` entry for two different subject_ids produces two distinct non-zero `FameState` entries | Step 2 | `test_fame_deriver_attributes_two_subjects_distinctly` |
| AC2: `FameExporter.export()` called from the same episode-boundary call site as `CultureDriftExporter.export()`; untouched entity's `FameCarryForward` preserved across a zero-event episode | Steps 3, 4, 5 | `test_fame_exporter_preserves_untouched_entity_across_zero_event_episode`, `test_fame_wiring_advance_state_calls_fame_exporter_alongside_culture_and_fidelity` |
| AC3: `LegendFact` constructed only when fame crosses `fame_threshold` | Step 6 | `test_legend_fact_constructed_only_above_threshold`, `test_legend_fact_not_constructed_below_threshold` |
| AC4: `LegendFact` discoverable via direct `PerceptionFilterService.filter()` call, with zero `PerceptionUpdatePhase` call-site increase and unchanged `_CANDIDATE_ROLES` | Steps 6, 8; Step 7 guards #3/#4 | `test_legend_fact_discoverable_via_perception_filter_service`, `test_fame_module_no_perception_update_phase_call_site_increase`, `test_coming_of_age_candidate_roles_unchanged` |
| AC5: `LegendFact` never confused with/merged into `LEGENDARY_ARRIVAL` | Step 6 (no such reference introduced); Step 7 guard #2 | `test_fame_module_no_belief_entry_knowledge_fact_or_legendary_arrival_references` |

## Anti-Drift Notes

- **Quest-failure fame contamination (newly confirmed, not in investigation.md):**
  `orchestrator.py:68` maps `QUEST_FAILED` to `event_type="quest_completed"` at `significance=0.3`.
  Because `ChronicleGrouper`'s chronicle-worthiness gate scores by `event_type` alone
  (`BASE_SIGNIFICANCE["quest_completed"]=0.7` regardless of outcome,
  `significance.py:22-38,69-71`), both real quest successes and failures reach `hierarchy.events`
  and both literally match `FameDeriver`'s `event_type == "quest_completed"` check. This is a
  disclosed, accepted characteristic (lower-magnitude but non-zero fame from failed quests) — not a
  bug to special-case in this ticket. Document it plainly in the Mechanics Bible entry (Step 9) so
  it is not later mistaken for an implementation defect.
- Keep `FameDeriver`'s `NORMALISE_DENOMINATOR` and event-type frozensets **module-local** to
  `src/domains/fame/deriver.py` — do not import them from `culture/deriver.py`, even though the
  numeric value is identical today.
- `LegendFact` is deliberately **not** durable/persisted — resist the urge to add a `CampaignState`
  field for it "for consistency with the other typed records"; Decision 2 above explains why it
  must stay a lazy read-model.
- The `entity_fame` key type is `str` (matching `subject_id`), not `int` — do not copy the
  `persistent_entities`/`social_memories` int-keyed `str(k)`/`int(k)` casting pattern into
  `CampaignState.to_dict()`/`from_dict()` for this field.
- `FameImporter.get_fame(campaign_state, entity_id)`'s second parameter is named `entity_id` per
  the ticket's own Scope text, but its runtime type/value domain is `subject_id` (str) — do not
  rename it to imply an `int` entity id lookup.
- Re-pin `tests/architecture/test_phase18_import_boundaries.py` deliberately if Step 5's new
  `import` line shifts a pinned line number there — this exact class of collateral failure hit the
  sibling Fidelity ticket.

## Unresolved Questions

None. Both Plan-phase decisions the investigation flagged (`fame_threshold`/axis-count, and
`LegendFact`'s home/trigger/WorldSignal shape) are resolved above with cited rationale. No other
open question surfaced during this planning pass that would change the implementation approach.

## Deviations

- **Step 7 guard count**: Step 7 enumerates exactly four guard tests, but this plan's own
  Acceptance Criteria Map (AC4 row) cites a fifth test name,
  `test_coming_of_age_candidate_roles_unchanged`, as verifying AC4's "unchanged `_CANDIDATE_ROLES`"
  clause — a test no other step actually specifies creating. Implementation added this fifth guard
  test to `tests/architecture/test_fame_legend_fact_distinctness.py` (asserting
  `src/ai/coming_of_age.py::_CANDIDATE_ROLES == (EntityRole.SHOPKEEPER, EntityRole.WORKER,
  EntityRole.GUARD)`) rather than leave the AC map's own citation pointing at a nonexistent test.
  This is an addition, not a change to any of the four originally-specified guards' behavior.
- No other deviations. All 9 steps were implemented exactly as specified, including the exact
  field names, module paths, event-type rule, `NORMALISE_DENOMINATOR`/`FAME_THRESHOLD` constants,
  and the re-pin of `tests/architecture/test_phase18_import_boundaries.py`'s pinned import line
  (437→440) the Anti-Drift Notes section anticipated.
