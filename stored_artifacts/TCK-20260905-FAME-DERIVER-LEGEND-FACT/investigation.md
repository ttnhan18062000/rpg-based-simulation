---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260905-FAME-DERIVER-LEGEND-FACT
artifact_type: investigation
tags: [social, strategy]
---

# Investigation — TCK-20260905-FAME-DERIVER-LEGEND-FACT

## Current Behavior

### The pattern to mirror: `CultureDeriver` (region-scale, live)

- `src/domains/culture/deriver.py:42-115` — `CultureDeriver.derive(hierarchy, entity_names=None)
  -> Dict[str, CultureState]`. Iterates `hierarchy.events` (line 77), keys by
  `entry.payload.get("region_id", "__global__")` (line 78), classifies `entry.event_type` against
  frozensets (`_FATALISM_EVENTS`, `_CONFLICT_EVENTS`, `_SCARCITY_EVENTS`, lines 37-39) plus a
  compound `entity_death` branch (lines 84-90) reading `payload["cause"]`/`payload["entity_role"]`.
  Sums `entry.significance` additively per bucket per key, normalises via
  `min(1.0, raw / NORMALISE_DENOMINATOR)` with `NORMALISE_DENOMINATOR = 3.0` (lines 35, 113-115).
- `src/domains/culture/model.py:24-102` — `CultureState` (frozen, slotted, float axes in
  `[0.0,1.0]`, `to_dict`/`from_dict`) and `CultureCarryForward` (region_id + state +
  `derived_episode: int`, same `to_dict`/`from_dict` shape).
- `src/domains/culture/exporter.py:24-79` — `CultureDriftExporter.export(campaign_state, hierarchy,
  episode_index, entity_names)` (staticmethod), calls `CultureDeriver.derive()` then writes
  `campaign_state.region_cultures[region_id] = CultureCarryForward(...)` in place (lines 55-61) —
  untouched keys keep their prior snapshot (docstring lines 38-40). `CultureDriftImporter.get_culture()`
  (lines 67-79) is a thin `None`-safe lookup.

### The second, freshly-built precedent: `FidelityDeriver` (per-event, no live consumer yet)

Just landed this same day via the sibling ticket `TCK-20260905-CHRONICLE-FIDELITY-DRIFT` (now
`tickets/done/`). Its own investigation independently confirmed the same two findings this
ticket also needs:

- `src/domains/fidelity/deriver.py:35-74` — `FidelityDeriver.derive(hierarchy) ->
  Dict[str, FidelityState]`, keyed per-event by `entry.entry_id` (not per-region), walking
  `hierarchy.eras -> Era.episodes -> Episode.index` rather than doing episode-index arithmetic.
  Demonstrates the 3-layer pattern can vary its *keying* dimension (per-event here vs per-region
  in `CultureDeriver`) while keeping the Deriver/Model/Exporter-Importer shape identical — directly
  relevant since `FameDeriver` is a *third* keying dimension (per-`subject_id`, i.e. per-entity).
- `src/domains/fidelity/model.py:27-77` — `FidelityState`/`FidelityCarryForward`, field-for-field
  mirror of `CultureState`/`CultureCarryForward`.
- `src/domains/fidelity/exporter.py:26-82` — `FidelityExporter.export(campaign_state, hierarchy,
  episode_index)` (no `entity_names` param — narrower signature than `CultureDriftExporter`), same
  direct-dict-mutation write into `campaign_state.historical_drift`. `FidelityImporter.get_fidelity()`
  has **zero call sites anywhere** — explicitly disclosed as "no live consumer yet, idea 63 is the
  intended eventual reader" (mirrors this ticket's own "built, not yet visible in play" framing for
  the perception/motivation half).
- **CampaignState is NOT frozen; there is no `patches.py`-routed write path for it.**
  `CampaignState` (`src/domains/campaigns/state.py:273-282`) is explicitly documented as
  "NOT frozen — mutation by CampaignOrchestrator is intentional." `src/engine/patches.py`'s
  authoritative-apply-path law is scoped to per-tick `EntityState` inside the Kernel loop; it has
  no `CampaignState` write path at all. `CultureDriftExporter`/`FidelityExporter`/
  `GriefUrgencyModifier`/`NemesisRelation` all write via direct dict index-assignment inside
  `CampaignOrchestrator._advance_state()` — this is `CampaignState`'s own established, sanctioned
  write convention, confirmed independently by the sibling ticket's own investigation. `FameExporter`
  must follow the identical convention — not a `patches.py` route.

### Episode-boundary call site (`src/domains/campaigns/orchestrator.py`)

`_advance_state()` (method body starting ~line 210) already chains, in order:

```python
_hierarchy = ChronicleGrouper().group(list(self._state.narrative_ledger))
CultureDriftExporter.export(self._state, _hierarchy, summary.episode_index)
# E62-FIDELITY: derive and persist chronicle-fidelity drift at the same episode boundary.
from src.domains.fidelity.exporter import FidelityExporter
FidelityExporter.export(self._state, _hierarchy, summary.episode_index)
self._state.episode_index += 1
```

`FameExporter.export(self._state, _hierarchy, summary.episode_index[, entity_names])` must be
inserted here, consuming the same `_hierarchy` local — no second `ChronicleGrouper().group()` call.

### `CampaignState` (`src/domains/campaigns/state.py:273-419`)

`region_cultures: Dict[str, CultureCarryForward]` (line 302) and `historical_drift: Dict[str,
FidelityCarryForward]` (line 315) are both plain dataclass fields with matching entries in
`to_dict()` (lines 349-352, 361-364) and `from_dict()` (lines 402-405, 414-417), each using
`sorted(...)` for determinism. A new `entity_fame: Dict[str, FameCarryForward]` field must follow
the identical shape in all three places (field decl + both serialization methods), per the design
doc's own recommendation (line 71-72 of the design doc).

### `NarrativeLedgerEntry` (`src/domains/campaigns/state.py:225-270`)

`event_type` docstring (line 233) claims exactly 4 literal values (`quest_completed | entity_death
| faction_shift | calamity`), but `orchestrator.py`'s `_SIGNIFICANCE_MAP` (lines 63-76) actually
produces additional event_type strings not in that list (`war_declared`, `alliance_formed`,
`peace_treaty`, `territory_transferred`, `war_ended_exhaustion`, `siege_begins`, `betrayal`) — the
docstring is stale/incomplete. This does not change Option B's decision (none of the additional
types are personal-heroism signals — they're all faction/diplomatic), but is worth flagging as a
minor doc-accuracy gap independent of this ticket. `subject_id` (line 244) is the natural per-entity
key `FameDeriver` should use, exactly as the design doc found — for `entity_death`, `subject_id` is
the deceased entity (confirmed via `src/domains/chronicle/naming.py:39`, `"The Death of {subject}"`).

### `PerceptionFilterService.filter()` (`src/domains/perception/filter.py:47-140`)

Signature: `filter(entity: EntityState, candidate_signals: Sequence[WorldSignal], budget:
PerceptionBudget, tick: int = 0) -> PerceptionUpdate`. It has **no awareness of Chronicle, Fame, or
any "fact" type today** — it only classifies `WorldSignal` instances (`src/domains/perception/
salience.py:14-30`, fields `signal_id, kind, position, base_relevance, danger_level, is_novel`) by
`.kind` into typed containers (lines 83-120): `entity`/`HERO`/`MONSTER` → `perceived_entities`;
`healing_resource`/`food_source`/`crafting_material` → `perceived_resources`;
`blacksmith`/`town_inn`/`guild_intel`/`shop_merchant` → `perceived_services`; `threat` →
`perceived_threats`; **any other kind** → `perceived_opportunities` (the catch-all `else` branch,
line 115-119). This means AC4 ("LegendFact is discoverable via a direct unit-level call to
`PerceptionFilterService.filter()`") is achievable **without any change to `filter.py` at all**:
construct a `WorldSignal` wrapping the `LegendFact`'s identity/salience and call `filter()` directly
— it will land in `perceived_opportunities` via the existing catch-all branch unless the Plan phase
deliberately adds a new explicit kind branch (e.g. `"legend_fact"`). Per
`docs/simulation/domains/perception_contract.md`'s own "Extension Rules" ("New signal kind: Add a
classification branch...") this is the documented, sanctioned way to extend `filter()` — so adding
an explicit branch, if Plan chooses to, is not a scope violation of "no change to `PerceptionUpdatePhase`'s
own call-site count" (that AC clause is about the *phase*, not the filter service).

### `MotivationBiasService.compute_bias_multiplier()` (`src/domains/motivation/service.py:14-72`)

Confirmed independently via `grep -rn "compute_bias_multiplier" src/` (excluding its own module):
**zero results**. The ticket's claim of dormancy is correct. Reads `entity.cognition.motivation`
(doctrine tags, value profile) and an optional `culture_values: CultureState` for the
`CulturalBiasApplicator` overlay (lines 65-70) — no `FameState`/`LegendFact` parameter exists or is
in scope to add.

### `PerceptionUpdatePhase` (`src/domains/perception/phase.py`)

Confirmed independently via `grep -rn "PerceptionUpdatePhase(" src/`: **zero results** outside its
own module/tests — no live pipeline call site, matching `docs/simulation/domains/
perception_contract.md` line 15's own disclosure and `TCK-20260831-DEAD-COGNITION-SCHEMA-DECISION`.

### `_CANDIDATE_ROLES` (`src/ai/coming_of_age.py:27`)

Confirmed via direct read: `(EntityRole.SHOPKEEPER, EntityRole.WORKER, EntityRole.GUARD)`. Checked
`src/core/enums.py:7`: `EntityRole.HERO = 0` exists as a role value, but is not in this tuple —
there is no `ADVENTURER` role at all in `EntityRole`. The atlas's "lean toward becoming an
adventurer" framing cannot be mechanically realized without extending this tuple, which is
explicitly out of scope for this ticket (idea 34's own territory).

### `LEGENDARY_ARRIVAL` — the pre-existing, unrelated concept `LegendFact` must not collide with

- `src/systems/social_systems/consequence_events.py:11,30,46-47,131-150` —
  `evaluate_social_consequence()` fires a `LegendaryArrivalEvent` when
  `social_record.faction_reputation.get("default", 0.0) >= LEGENDARY_REP_THRESHOLD` (`0.9`). This
  reads `CampaignState.social_memories[entity_id].faction_reputation` — **not** Chronicle, **not**
  `NarrativeLedgerEntry.significance`, **not** anything `FameDeriver` will touch.
- `src/observability/events.py:399,404-412` — `LEGENDARY_ARRIVAL: str = "LEGENDARY_ARRIVAL"` and
  `class LegendaryArrivalEvent(SimulationEvent)`, tagged `Logic ID: SOC-CROSS-EP-005`.
- `src/domains/chronicle/significance.py:27` — `BASE_SIGNIFICANCE["LEGENDARY_ARRIVAL"] = 0.75`: once
  a `LegendaryArrivalEvent` is itself recorded as a `NarrativeLedgerEntry`, its `event_type` string
  literally is `"LEGENDARY_ARRIVAL"` for Chronicle-worthiness scoring purposes — a second,
  coincidental reuse of the word "legendary" for an entirely different mechanism. `FameDeriver`'s
  own event-type frozensets (`quest_completed`, `entity_death`+`HERO`) do not include
  `"LEGENDARY_ARRIVAL"` and must not be extended to include it without a separate, disclosed
  decision — it is a faction-reputation trigger event, not a fame-accumulation source event under
  Option B.
- A **third**, wholly separate "fame" concept already exists in the parity ledger:
  `docs/parity_ledger/world_dynamics.yaml:424` — `WORLD-035: "Killing world boss grants fame."`
  (P0, `status: verified`, legacy checklist-audit evidence, `test_path: null`). This is a
  loot/title-grant mechanic from the legacy checklist audit, structurally unrelated to
  Chronicle-derived `FameState`/`LegendFact` — do not conflate the two, and do not attempt to
  satisfy WORLD-035's missing `test_path` as part of this ticket (out of scope; a pre-existing gap).

## Mechanics / Engine Constraints

- **`docs/mechanics/05_world_evolution.md` §7 "Cultural Drift (E62)" and §8 "Chronicle Fidelity
  Drift (E62)"** (lines 555-660) are the two live, authoritative precedents for exactly this kind
  of long-horizon, episode-boundary Deriver mechanism. Both document: axis/value definition,
  derivation trigger (with the exact `CampaignOrchestrator._advance_state()` call-site language),
  persistence shape, and an "Acceptance Signal" one-liner. `FameDeriver`'s own Mechanics Bible
  entry (new §9) must follow this identical structure per the Authoritative Mechanics Rule's
  "Reference: cite the specific chapter" requirement, and per §8's own explicit "No Live Consumer
  Yet" subsection precedent for disclosing dormant integration halves honestly.
- **`CultureDeriver._normalise` formula is the mandated normalization law for this ticket** — the
  ticket's own Scope text says "normalised via `min(1.0, raw/NORMALISE_DENOMINATOR)` exactly
  mirroring `CultureDeriver._normalise` — per the already-merged design doc, verbatim." This is not
  a Plan-phase-open formula choice; only the axis-count (single vs. fame+notoriety split) and
  `fame_threshold`'s numeric value remain genuinely open.
- **`docs/simulation/domains/perception_contract.md`'s "Extension Rules"** (line 217-222) is the
  binding contract for how a new `WorldSignal` kind may be added without triggering a full
  `PerceptionUpdatePhase` pipeline change — directly relevant to how `LegendFact` discoverability
  should be implemented (see Current Behavior above).
- **Chronicle's own no-mutation contract**: `docs/simulation/domains/chronicle_contract.md`
  (referenced by the sibling Fidelity ticket) requires derived structures to never mutate
  `NarrativeLedgerEntry`/`ChronicleHierarchy` in place — `FameDeriver`/`FameExporter` must follow
  the same read-only-over-Chronicle constraint `CultureDeriver`/`FidelityDeriver` already honor.
- **Durable State Rule** (project CLAUDE.md): `FameState`, `FameCarryForward`, and `LegendFact` are
  all durable (survive across episodes / are queried later), so each needs a typed model with a
  stable `CampaignState` location, a defined lifecycle (derive → export → carry-forward or
  construct-on-threshold), and tests — satisfied by following the Deriver-pattern shape exactly.

## Docs Requiring Update

- `docs/mechanics/05_world_evolution.md`: new §9 "Living Legend Fame (idea 57)" subsection,
  mirroring §7/§8's exact structure (value/axis definition, derivation trigger citing the
  `_advance_state()` call site, persistence, an honest "No Live Consumer Yet"-style disclosure for
  the perception/motivation dormancy, and an Acceptance Signal one-liner) — required because this
  ticket introduces new simulation-law-shaped behavior (fame accumulation + threshold-gated
  `LegendFact` construction) that has no existing Mechanics Bible coverage.
- `docs/parity_ledger/world_dynamics.yaml`: new `WORLD-FAME-*` entries (mirroring the
  `WORLD-FIDELITY-001`/`-002` and `WORLD-CULT-001..004` precedent exactly — same subsystem file,
  same ticket-landing convention observed on both sibling tickets), documenting `FameDeriver`'s
  derivation rule, determinism, and the `LegendFact` threshold-crossing behavior with real
  `test_path` values.
- `docs/world/fame_legend_contract.md` (new file): a domain contract doc mirroring
  `docs/world/culture_drift_contract.md` and `docs/world/chronicle_fidelity_contract.md`'s own
  section structure — both direct siblings created exactly this kind of contract doc as part of
  their own ticket's Document-Update phase; `FameDeriver`/`LegendFact` warrants the same.
- `docs/plans/rpg_design_roadmap/rpg_m5_memory_reputation_epic.md`: a "Status update, 2026-09-05"
  annotation under idea 57's existing numbered item (mirroring the exact convention both idea 60's
  and idea 62's own tickets followed in this same epic doc) — required to keep the epic's own
  tracking doc from silently drifting stale, matching this batch's own established pattern.
- `docs/simulation/domains/perception_contract.md`: **only if** the implementer adds an explicit
  new `WorldSignal.kind` classification branch (e.g. `"legend_fact"`) inside
  `PerceptionFilterService.filter()` rather than relying on the existing catch-all
  `perceived_opportunities` branch to satisfy AC4 — the doc's own "Extension Rules" section
  requires documenting any new signal-kind branch. This is a genuine Plan-phase implementation
  choice not yet made at investigation time; if the implementer confirms no new branch was added
  (the catch-all path was used instead), whoever resolves this bullet should add "Resolved during
  implementation, condition not met" per this ticket's own conditional-bullet convention.

None of the following need to change: `docs/brainstorm/rpg_expected_schemas.html` — the design doc
(`docs/brainstorm/2026-09-04-idea57-entity-scale-fame-aggregation-design.md`) itself explicitly
calls schema `#schema-57` "read-only, not edited," and this ticket implements that design as-is, so
the frozen schema stays untouched. `docs/parity_ledger/social_narrative.yaml` — its `LEGENDARY_ARRIVAL`/
`SOC-CROSS-EP-005` entries describe a structurally distinct faction-reputation mechanism (see
Current Behavior above) that this ticket does not touch or extend; Fame's own parity entries follow
the `world_dynamics.yaml` precedent set by `WORLD-CULT-*`/`WORLD-FIDELITY-*`, not
`social_narrative.yaml`'s reputation-mechanism entries. `docs/mechanics/04_strategic_cognition.md` —
its §5 "Perception & Salience" documents perception-radius constants used by *live* tactical/
strategic decision logic (`src/engine/domain_logic.py`, `src/systems/strategic_systems/
intelligence.py`), a structurally separate live path from the dormant `PerceptionUpdatePhase`/
`PerceptionFilterService` path this ticket's unit test exercises directly at the service level; this
ticket adds no new live perception-radius rule, so §5 needs no edit. `docs/parity_ledger/
strategic_cognition.yaml` — despite this ticket's `layer: strategy` registration, the sibling
Fidelity ticket (also `layer: strategy`) placed its own parity entries in `world_dynamics.yaml`
matching the Culture Drift subsystem precedent, not `strategic_cognition.yaml`; Fame follows the
identical subsystem-content mapping, not the `layer:` field.

## Parity Ledger Overlap

- `WORLD-CULT-001` through `WORLD-CULT-004` (`docs/parity_ledger/world_dynamics.yaml:1212-1970ish`,
  status `verified`) — the live `CultureDeriver` precedent this ticket's `FameDeriver` structurally
  mirrors. Not modified by this ticket; cited for pattern precedent only.
- `WORLD-FIDELITY-001`, `WORLD-FIDELITY-002` (`docs/parity_ledger/world_dynamics.yaml:1980-2011`,
  status `verified`, P0/P1 — check exact priority at Plan time) — the just-landed sibling precedent.
  Not modified by this ticket; cited for pattern precedent (same file, same convention) and as the
  freshest real example of the exact Docs Requiring Update bullets this ticket must also produce.
- `WORLD-035` (`docs/parity_ledger/world_dynamics.yaml:424`, P0, status `verified`, `test_path:
  null`) — an unrelated, pre-existing "fame" concept (world-boss-kill loot grant) with a real,
  disclosed test-path gap. Flagged here only to prevent confusion with this ticket's own `FameState`
  — not this ticket's gap to fix (P0 status with a missing `test_path` would normally be a red flag
  per the Authoritative Mechanics Rule, but this is legacy-checklist-audit-verified evidence from a
  different, already-shipped mechanic entirely outside this ticket's scope).
- `SOC-CROSS-EP-005` / `LEGENDARY_ARRIVAL` entries in `docs/parity_ledger/social_narrative.yaml`
  (around line 2659-2706) — the pre-existing, structurally distinct faction-reputation consequence
  event this ticket's `LegendFact` must never be confused with (see Current Behavior). Not modified
  by this ticket.
- No existing `WORLD-FAME-*`, `STRAT-FAME-*`, or `SOC-FAME-*` entries exist anywhere in the parity
  ledger today (grepped all four candidate files) — this ticket will create the first ones, per the
  Docs Requiring Update section above. None of the new entries are P0 by default (following
  `WORLD-CULT-*`/`WORLD-FIDELITY-*`'s own precedent of non-P0 priority for these long-horizon,
  no-live-consumer-yet mechanisms), so a passing `test_path` is required by convention/craftsmanship,
  not by the P0 hard rule — but should still be provided, matching precedent.

## Prior Work

- `stored_artifacts/` has **no prior `FAME`/`LEGEND`-named artifacts** (confirmed via
  `find stored_artifacts -iname "*FAME*" -o -iname "*LEGEND*"`, zero results) — this is genuinely
  the first implementation ticket for idea 57.
- `TCK-20260905-CHRONICLE-FIDELITY-DRIFT` (DONE, `tickets/done/`) is the closest possible prior
  work: same epic, same day, same 3-layer Deriver pattern, same episode-boundary call site, same
  "CampaignState is not frozen / no `patches.py` write path" finding, same "ships with no live
  consumer yet" honesty framing. Its `investigation.md`/`plan.md` (now in `stored_artifacts/
  TCK-20260905-CHRONICLE-FIDELITY-DRIFT/`) are directly reusable references for Plan-phase
  decisions this ticket faces (era-distance-walk technique doesn't apply here, since Fame is keyed
  by `subject_id` not per-event, but the write-path/doc/parity-ledger conventions all transfer).
- `TCK-20260904-REPUTATION-LOCALITY-SCOPE` (DONE, idea 60) is the cited "built, not yet visible in
  play" honesty precedent this ticket's own AC explicitly asks to match — its Implementation Notes
  ("Disclosed follow-up gaps (explicitly out of scope, per plan's Scope Guards)") is the template
  for how to phrase LegendFact's own perception/motivation dormancy honestly rather than
  overclaiming a fully-live feature. It also independently demonstrates the "found an
  undisclosed second bypass via the architecture guard test" pattern — worth keeping in mind when
  writing `FameExporter`'s own write-path guard test (a second write path could exist elsewhere
  that hasn't been grepped for yet, e.g. any `entity_fame[` occurrence outside the eventual
  exporter — confirmed zero hits today since the field doesn't exist yet).
- `docs/brainstorm/2026-09-04-idea57-entity-scale-fame-aggregation-design.md` — already-merged,
  authoritative for the aggregation-shape half of this ticket's scope (see Request Summary). Its
  "Recommendation: Option B" section and "What this doc does not resolve" section are the direct
  inputs to this ticket's own Plan-phase open questions.

## Risks and Open Questions

- **fame_threshold's numeric value and FameState's axis count are genuinely unresolved** — no
  existing anchor in the codebase or design doc (the design doc explicitly defers both). Plan phase
  must decide and document rationale; this is not something Investigation can safely guess at.
- **Where does `LegendFact` live as a module, and what triggers its construction?** The design doc
  only specifies "constructed/discoverable only once `FameImporter.get_fame(...)`'s relevant axis
  crosses `fame_threshold`" — it does not specify whether `LegendFact` construction happens inside
  `FameExporter.export()` itself (eagerly, for every entity crossing threshold, stored somewhere new
  in `CampaignState`), or is computed lazily by a separate service call reading `FameState` at query
  time. This materially affects whether a new `CampaignState` field is needed for `LegendFact`
  itself (beyond `entity_fame`), and is a real Plan-phase decision, not resolved here.
- **How `LegendFact` becomes a `WorldSignal` for the AC4 perception test is unspecified by the
  design doc** — `PerceptionFilterService.filter()` has zero awareness of Fame/Chronicle today (see
  Current Behavior). The unit test can pass by manually constructing a `WorldSignal` wrapping the
  `LegendFact`'s data and asserting it's classified/salient — but *how* that wrapping happens (a
  helper function? inline in the test only? a real conversion method on `LegendFact`?) is an open
  design question for Plan, not resolved here. If Plan decides on a real conversion helper, that
  helper's own module location and whether it counts as "Perception-system wiring" (which the
  ticket's Out-of-Scope explicitly limits to `PerceptionUpdatePhase`/pipeline wiring, not a
  standalone signal-construction helper) should be explicitly reasoned about to avoid drifting into
  the excluded live-wiring territory.
- **`entity_names` parameter inconsistency between the two existing siblings** —
  `CultureDeriver.derive()`/`CultureDriftExporter.export()` both accept an optional `entity_names`
  parameter (currently unused, "kept for API forward-compat" per its own docstring);
  `FidelityDeriver.derive()`/`FidelityExporter.export()` do not have this parameter at all. The
  ticket's own Scope text specifies `FameDeriver.derive(hierarchy, entity_names=None)` (matching
  `CultureDeriver`'s signature, not `FidelityDeriver`'s narrower one) — already resolved by the
  ticket text itself, not an open question, but worth flagging since the two precedents disagree
  and an implementer skimming only the Fidelity precedent could copy the wrong signature shape.
- **The stale `NarrativeLedgerEntry.event_type` docstring** (claims exactly 4 values; actual event
  universe is larger, see Current Behavior) does not block this ticket's own Option B decision, but
  if a future reviewer double-checks the design doc's "narrower... than idea 57's own framing
  assumes" claim against the docstring alone (rather than `orchestrator.py`'s actual
  `_SIGNIFICANCE_MAP`), they could incorrectly conclude Option B is even narrower than it really is
  relative to the full event-type universe. Not a blocker; flagged for accuracy only.

## Anti-Drift Hazards

- **Do not let `LegendFact` construction accidentally read or reuse `LEGENDARY_ARRIVAL`/
  `LegendaryArrivalEvent`/`faction_reputation["default"]`** — a natural but wrong shortcut, since
  both concepts use the word "legendary"/"legend" and both are threshold-gated. AC5's own guard
  test exists specifically to catch this; keep `LegendFact`'s only real input as
  `FameImporter.get_fame(...)`'s `FameState`, never `social_memories`/`faction_reputation`.
- **Do not silently widen `FameDeriver`'s event-type frozensets beyond Option B** (`quest_completed`
  + `entity_death` with `entity_role == "HERO"`) — e.g. adding `"LEGENDARY_ARRIVAL"`,
  `"faction_shift"`, or any war/diplomatic event type as a fame source would be new event-scoring,
  explicitly out of scope per both the design doc and this ticket's own Out of Scope section.
- **Do not wire `PerceptionUpdatePhase` into `AuthoritativeApplyPipeline.refine()`, or add a call
  site for `MotivationBiasService.compute_bias_multiplier()`, even opportunistically "since you're
  already touching perception/motivation code"** — both are explicit, hard Out-of-Scope items with
  their own separate tracked tickets (`TCK-20260831-DEAD-COGNITION-SCHEMA-DECISION` and an unnamed
  future follow-up respectively). A single new import or call site here would silently expand scope
  and invalidate the "built, not yet visible in play" framing this ticket must honestly preserve.
- **Do not extend `src/ai/coming_of_age.py`'s `_CANDIDATE_ROLES` tuple** to add an `ADVENTURER`/
  `HERO` option, even though the atlas's illustrative scenario implies it — explicitly out of scope
  (idea 34's own territory), and `EntityRole` has no `ADVENTURER` value to begin with.
- **Do not route `FameExporter`'s write through `src/engine/patches.py`** — confirmed it has no
  `CampaignState` write path at all; the correct pattern is the direct dict-mutation convention
  already established by `CultureDriftExporter`/`FidelityExporter`/`GriefUrgencyModifier`/
  `NemesisRelation`, all inside `CampaignOrchestrator._advance_state()`.
- **Do not add a second `ChronicleGrouper().group()` call** in `_advance_state()` for `FameExporter`
  — reuse the existing `_hierarchy` local that `CultureDriftExporter`/`FidelityExporter` already
  consume, exactly as the sibling ticket's own Implementation Notes emphasize ("no second
  `ChronicleGrouper().group()` call").
- **Do not let a second, undisclosed write path to `entity_fame` slip in** (mirroring the real bug
  the idea-60 ticket caught in `CampaignOrchestrator._build_initial_state()`) — write the
  architecture guard test *before* trusting the investigation's own "only one write site" claim, and
  actually run it, per that ticket's own lesson.
