---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260831-HABIT-BIAS-WIRING
artifact_type: investigation
tags: [cognition]
---

# Investigation — TCK-20260831-HABIT-BIAS-WIRING

## Current Behavior

**`HabitMemory`** (`src/core/cognition.py:291-297`): a frozen, slotted dataclass with a single
field, `patterns: Mapping[str, float] = field(default_factory=dict)` — "Phase 16 Shell" per its own
docstring. `to_canonical_dict()` returns `{"patterns": dict(sorted(self.patterns.items()))}`.
Embedded as `MemoryModel.habit` (`src/core/cognition.py:324`), which is itself embedded at
`CognitionModel.memory` and reachable at runtime as `entity.cognition.memory.habit`. Confirmed: the
atlas's "no existing accumulation scaffolding" premise for idea 23 is false — this scaffolding is
real and already shipped, just unpopulated (every entity's `habit.patterns` is permanently `{}`
because nothing ever writes to it).

**`HabitBiasService`** (`src/domains/emotion/habit_service.py`), two static methods:
- `record_outcome(memory: HabitMemory, pattern_id: str, success: bool) -> HabitMemory` (line 15):
  reads `patterns.get(pattern_id, 0.5)`, applies `+0.1` on success / `-0.1` on failure, clamped to
  `[0.0, 1.0]`, returns a new `HabitMemory` via `dataclasses.replace`.
- `apply_habit_bias(memory: HabitMemory, tags: list[str], base_score: float) -> float` (line 27):
  for each `tag` present in `memory.patterns`, adds `(memory.patterns[tag] - 0.5) * 0.4` to
  `base_score`; no clamping (caller's responsibility per `docs/simulation/domains/emotion_contract.md:104`).

**Confirmed zero production call sites for both methods** — verified via
`grep -rn "record_outcome\|apply_habit_bias"` across `src/`: the only matches are the class
definitions themselves and `tests/unit/domains/emotion/test_phase16_habit_bias_service.py`. No
`src/engine/`, `src/domains/`, or `src/ai/` file calls either method. This means the mechanism is
currently a fully dead end in both directions — nothing ever populates `habit.patterns` (no
`record_outcome` caller) and nothing ever reads it for a bias effect (no `apply_habit_bias`
caller), which the ticket's own AC only requires fixing on the read side (see Risks below for why
that alone is insufficient for the feature to do anything observable).

**`get_action_style_for_bravery(bravery: float) -> int`** (`src/content_semantics/personality.py:66-82`):
loads `action_style_thresholds` from `data/content/social/personality_bias.yaml` (cached,
module-level fallback if the file is missing/malformed), returns `ActionStyle.AGGRESSIVE` if
`bravery >= aggressive_at_or_above` (0.65), `ActionStyle.EVASIVE` if `bravery <=
evasive_at_or_below` (0.35), else `ActionStyle.BALANCED`. **Called only at entity-construction
time**, from exactly 3 sites, all passing the entity's freshly-drawn `PersonalityComponent.bravery`:
- `src/worldbuilding/compiler.py:466` (`WorldCompiler.compile()`)
- `src/entities/archetype_factory.py:111` (`ArchetypeEntityFactory.build_entity()`)
- `src/worldassembly/entity_spawner.py:138` (`WorldEntitySpawner._spawn_legacy_guard()`)

The result is written once into `CombatComponent.action_style` (`src/core/state.py:308`,
`int = 0 # ActionStyle.BALANCED`) via the `V2EntityBuilder.combat(action_style=...)` builder
(`src/core/builder.py:250,269`). **There is no per-tick or authoritative-pipeline path that ever
recomputes or mutates `action_style` after construction** — confirmed by grepping `CombatUpdate`
(`src/core/updates.py:97-137`): it has no `action_style`/`action_style_set` field at all, unlike
e.g. `alive_set`, `atk_delta`. This is a load-bearing fact for how this ticket can be implemented
(see Risks).

**Consumption in `src/engine/tactical.py`**: `style = entity.combat.action_style` (line 491) reads
the frozen, construction-time value. It is used once, at line 631:
`kite_dist = 2 if style == ActionStyle.AGGRESSIVE else 6 if style == ActionStyle.EVASIVE else 4`
(SKIRMISHER-role kiting distance) — the real, live consumer this ticket's scope points at. A
second dead sub-branch that used to compute an ActionStyle-biased `attack_range` was already
removed by `TCK-20260809-TACTICAL-DEAD-ACTIONSTYLE-SUBBRANCHES` (lines 672-684, now a removal
comment, not code) — confirmed still removed, not reintroduced. `entity` is fully available at
this decision point (`entity.identity.personality.bravery`, `entity.cognition.memory.habit`, etc.
are all reachable), so a live re-derivation of `style` at this call site (rather than trusting the
frozen field) is structurally possible without new plumbing.

`ActionStyle` (`src/core/enums.py:60-64`): `IntEnum` — `BALANCED = 0`, `AGGRESSIVE = 1`,
`EVASIVE = 2`.

**Established authoritative-write precedent for this exact class of cognition sub-state**
(`src/engine/pipeline_phases/hardening.py:90-106`, `NearDeathHardeningPhase.apply()` — the one
production-wired emotion-domain event): reads `entity_update.cognition_bundle_set` (falling back
to `entity.cognition`), calls the domain service (`EmotionUpdateService.update_on_event`), wraps
the result via `dataclasses.replace()` into a new `cognition`, and sets
`entity_update.cognition_bundle_set`. `src/domains/memory/phase.py` (`MemoryUpdatePhase`,
`ENABLE_MEMORY_UPDATE`-gated) follows the identical shape for `CausalMemory`/`SpatialMemory` inside
the very same `MemoryModel` that owns `habit`, run every tick from
`src/engine/pipeline.py:154-158` via the `run_phase(name, update, lambda, flag_name)` pattern
(`src/engine/pipeline.py:100-133`, `FeatureMode.OFF/SHADOW/ON/STRICT` semantics). This is the
concrete authoritative apply-path precedent this ticket's AC ("applied only through the
authoritative apply path") should follow for writing `HabitMemory` back — `record_outcome`'s output
belongs in `entity_update.cognition_bundle_set`, not a direct `state.entities` mutation.

## Mechanics / Engine Constraints

- **`docs/mechanics/04_strategic_cognition.md` §6.3 (Risk Multiplier) and the `ActionStyle wiring`
  subsection immediately below it (lines 431-442)**: documents `bravery`'s full real derivation
  chain (RNG draw → faction bias → `ActionStyle` threshold) and both live `ActionStyle` consumers
  (`tactical.py` kiting, `movement.py` opportunity-attack suppression on EVASIVE retreat). This is
  the authoritative description of the exact bias point this ticket adds a new input to — the
  chapter must gain a new subsection describing the habit-bias contribution.
- **`docs/simulation/domains/emotion_contract.md`** (Emotion Domain Contract, P1, `last_verified:
  2026-08-28`): line 13 states the domain "Does NOT produce `EntityUpdate` or route through the
  authoritative mutation pipeline" and describes a "synchronous in-event callback pattern" where
  "the caller is responsible for writing these back." This is consistent with wiring
  `HabitBiasService` calls into a pipeline phase's `.apply()` (the caller) rather than the domain
  itself producing `EntityUpdate` — no contradiction with the AC's authoritative-apply-path
  requirement, but the doc's own "Engine Pipeline Phase" table (line 46) currently mis-describes
  `record_outcome` as if it already has a production trigger ("Action outcome (success/failure) →
  `HabitBiasService.record_outcome`", stated flatly, unlike the other 5 event kinds which are each
  correctly annotated "no production call site wired yet"). That line is currently inaccurate and
  must be corrected regardless of what this ticket ships.
- **Determinism**: `04_strategic_cognition.md`'s framing and `emotion_contract.md`'s "Determinism
  invariant" (line 213, "All four services are fully deterministic... Do not introduce randomness")
  both apply — `HabitBiasService`'s existing formula is already deterministic; wiring must not add
  RNG.
- **Frozen `PersonalityComponent`**: `src/core/state.py:417-423` — `bravery` etc. have no
  `_delta`/`_set` update field pattern in any Update dataclass reachable from `src/core/updates.py`
  (confirmed no `PersonalityUpdate` exists). The ticket's AC ("keep `PersonalityComponent`
  frozen/immutable") is already structurally enforced — there is no live mutation path for it to
  violate, so the constraint is really about not inventing one, not about removing an existing one.

## Docs Requiring Update

- `docs/mechanics/04_strategic_cognition.md`: §6.3's "ActionStyle wiring" subsection (lines
  431-442) documents the full real derivation of `ActionStyle` today; must gain the new
  habit-bias contribution to stay authoritative once `get_action_style_for_bravery`'s effective
  bravery input (or the `tactical.py` decision point) is influenced by `HabitBiasService`.
- `docs/simulation/domains/emotion_contract.md`: line 46's "Engine Pipeline Phase" table and line
  189's "Domain Interactions" table must be updated to add the new confirmed production call site
  for `HabitBiasService.apply_habit_bias` (and `record_outcome`, if wired per the recommendation
  below) — the same style already used there for `near_death`'s confirmed call site vs. the other
  five event kinds' "no production call site wired yet" annotations. Line 46's current unqualified
  phrasing for `record_outcome` is a pre-existing inaccuracy independent of this ticket and should
  be corrected either way.
- `docs/parity_ledger/strategic_cognition.yaml`: needs a new entry (next free ID after
  `STRAT-261`) documenting the habit-bias-into-ActionStyle wiring, `status: verified`,
  `priority: P2` (new gameplay behavior, flag-gated OFF by default, not a correctness fix to
  existing shipped behavior), with `test_path` pointing at the new tests this ticket adds.

The `docs/parity_ledger/combat_movement.yaml` entries `COMB-301` (`TCK-20260809-TACTICAL-DEAD-ACTIONSTYLE-SUBBRANCHES`)
and `SUB-381` (`TCK-20260809-COMBAT-ACTIONSTYLE-WIRING`, in `substrate.yaml`) are not required to
change: `COMB-301`'s own `support_boundary` already explicitly scopes itself to the confirmed-dead
range-bonus/reposition-stub sub-branches, not the live kiting-distance consumer this ticket touches
— this ticket does not reopen or contradict that removal. `SUB-381` documents
`get_action_style_for_bravery`'s existing threshold-based behavior at construction time, which this
ticket does not change (it adds a new, separately-gated input path, `ENABLE_...`-flagged OFF by
default; `SUB-381`'s already-verified construction-time behavior is unaffected when the flag is
off, which is the default).

## Parity Ledger Overlap

- `SUB-380` (`substrate.yaml`, `verified`, P1): `get_bravery_bias` / faction-correlated bravery.
  Overlaps as the upstream input this ticket's habit bias would additionally modify — not itself
  touched.
- `SUB-381` (`substrate.yaml`, `verified`, P1): `get_action_style_for_bravery` wiring into
  `tactical.py`/`movement.py`. Directly overlaps — this is the exact function/bias point named in
  the ticket's own Scope. See "Docs Requiring Update" above for why it does not need editing itself.
- `SUB-382` (`substrate.yaml`, `verified`, P2): extraction of the shared personality helpers into
  `src/content_semantics/personality.py`. Confirms current file location; no overlap beyond that.
- `COMB-301` (`combat_movement.yaml`, `verified`, P2): dead `ActionStyle` sub-branch removal in
  `tactical.py`. Directly named in this ticket's Out of Scope — confirmed the removal is real and
  the kiting-distance branch (line ~631, this ticket's real target) is explicitly disclaimed as
  untouched by that removal (`support_boundary`, `combat_movement.yaml:3464-3465`).
- No P0 entries found touching `ActionStyle`, `HabitMemory`, or `HabitBiasService` in
  `strategic_cognition.yaml`, `combat_movement.yaml`, or `substrate.yaml`.

## Prior Work

- **`TCK-20260809-COMBAT-PERSONALITY-RACE-CORRELATION`** (`SUB-380`): established
  `get_bravery_bias(faction_str)`, additive/clamped faction bias on raw RNG bravery.
- **`TCK-20260809-COMBAT-ACTIONSTYLE-WIRING`** (`SUB-381`): established
  `get_action_style_for_bravery`, wired at all 3 construction sites, and traced (but did not fix)
  the two now-removed dead `tactical.py` sub-branches.
- **`TCK-20260809-TACTICAL-DEAD-ACTIONSTYLE-SUBBRANCHES`** (`COMB-301`): removed those two dead
  sub-branches; explicitly confirmed the kiting-distance branch (this ticket's real target) is a
  separate, live, untouched consumer.
- **`TCK-20260824-CAUSAL-MEMORY-ROUTE-SCORING`** (referenced in `feature_flags.py`'s
  `ENABLE_MEMORY_UPDATE` comment): established `MemoryUpdatePhase`/`ENABLE_MEMORY_UPDATE` as the
  first production wiring of any field inside `MemoryModel` (the same dataclass that owns
  `habit`) through the authoritative pipeline — the closest existing precedent for wiring a second
  `MemoryModel` sub-field (`habit`) the same way.
- **Phase 16 Emotion/Recovery/Habit domain** (archived): built `EmotionalModel`, `HabitMemory`,
  `RecoveryState`, and the 4 emotion-domain services as an event-driven (not phase-scheduled)
  synchronous callback layer, documented in `docs/simulation/domains/emotion_contract.md`. Only
  `near_death` (via `NearDeathHardeningPhase`) ever got a real production trigger; the other 5
  event kinds and both `HabitBiasService` methods remained dormant — this ticket closes one of
  those remaining gaps.

## Risks and Open Questions

- **AC only mandates a production consumer for `apply_habit_bias`, not `record_outcome` — wiring
  only the read side leaves the mechanism functionally inert.** `apply_habit_bias` only has an
  effect for `tag in memory.patterns`; since `habit.patterns` starts and stays `{}` for every
  entity until something calls `record_outcome`, wiring `apply_habit_bias` alone (with
  `record_outcome` still uncalled) is a technically-compliant but behaviorally-inert integration —
  it satisfies the letter of the AC ("gains at least one real production consumer... closing the
  current zero-call-site gap") while never producing an observable gameplay effect, because the
  bias table it reads is permanently empty. **Recommendation for the plan phase: wire both methods
  in the same ticket** — `record_outcome` on a real per-entity action outcome (e.g. combat
  win/loss, via the same `combat_loss`/outcome-kind signal `MemoryUpdatePhase` already reads at
  `src/engine/pipeline.py:149-153`) through `entity_update.cognition_bundle_set`, following the
  `NearDeathHardeningPhase`/`MemoryUpdatePhase` precedent exactly. If the plan phase deliberately
  chooses to wire only `apply_habit_bias` per the AC's literal wording, this must be called out
  explicitly as a known limitation in the ticket, not silently left implicit.
- **`get_action_style_for_bravery` is called only at construction time — wiring a habit-bias input
  into it directly is a structural no-op for the ticket's own stated goal.** A freshly-constructed
  entity's `habit.patterns` is always `{}` at the moment `get_action_style_for_bravery` runs (it
  runs during entity construction, before any gameplay has occurred), so feeding habit bias into
  that specific function call would never have any effect, regardless of how well
  `record_outcome`/`apply_habit_bias` are wired elsewhere. For the ActionStyle bias point to
  actually respond to accumulated habit over an entity's lifetime, the live decision must be
  re-derived at a point where `habit.patterns` can have accumulated data — i.e., at
  `src/engine/tactical.py:491` (recomputing `style` from `entity.identity.personality.bravery` +
  `entity.cognition.memory.habit` via `apply_habit_bias`-adjusted bravery fed into
  `get_action_style_for_bravery`, rather than trusting the frozen `entity.combat.action_style`
  field) — not inside `get_action_style_for_bravery` itself at its 3 existing construction-time call
  sites. **This is a real, load-bearing design decision the plan phase must make explicitly** — the
  ticket's Scope text names `get_action_style_for_bravery` as "the ActionStyle bias point," but the
  literal function is the wrong place to add a per-tick-varying input; the right place is the
  runtime read site in `tactical.py` that currently reads the frozen field. Flagging rather than
  assuming — this changes whether `CombatComponent.action_style` stays authoritative-at-construction
  (current behavior, unaffected) or `tactical.py` starts deriving its own live `style` value
  in addition to it.
- **No existing `CombatUpdate`/`EntityUpdate` field carries an `action_style` delta.** If the plan
  phase decides the habit-biased ActionStyle should be persisted back onto the entity (rather than
  computed fresh every tick inside `tactical.py`), a new typed update field would need to be added
  — a larger, more invasive change than a pure read-time re-derivation. Recommend the plan phase
  prefer the pure read-time re-derivation (no new Update field) unless there's a concrete reason
  the value needs to persist/be inspectable outside the tactical decision itself.
- **`data/content/social/personality_bias.yaml` thresholds are designer-tunable content, not
  code** — any habit-bias contribution should compose with (not hardcode around) the existing
  `aggressive_at_or_above`/`evasive_at_or_below` thresholds, consistent with this module's own
  established data-driven-tuning precedent (`personality.py:16-19`).

## Anti-Drift Hazards

- Do not reintroduce the confirmed-dead `attack_range`/EVASIVE-reposition sub-branches
  `TCK-20260809-TACTICAL-DEAD-ACTIONSTYLE-SUBBRANCHES` removed (`tactical.py:672-684`) while
  touching this same function — the ticket's own Out of Scope already flags this; the risk is
  editing adjacent code in the same function and accidentally resurrecting the removed pattern
  under a different name.
- Do not let `record_outcome`'s wiring point (if included) grow into a new, separate
  accumulation/event-classification mechanism beyond a straightforward reuse of an outcome signal
  the pipeline already computes (e.g. combat win/loss) — that would cross into "building new
  accumulation state," which the ticket's own Scope explicitly rules out.
- Do not implement the discrete milestone-event variant ("three near-deaths fighting alone") in
  this ticket — see the ticket's own Out of Scope and the recommendation below; it requires new
  event-counting state that does not exist and is explicitly out of scope.
- Do not silently repoint `SUB-381`/`COMB-301`'s already-verified construction-time behavior —
  those entries describe real, live, currently-correct behavior for the OFF (default) flag state;
  this ticket must not change what happens when the new flag is OFF.
- Keep the new FeatureMode flag's default OFF for the entire ticket, including tests that exercise
  the ON path (explicit flag override in test setup only, per the established
  `overrides` constructor pattern in `FeatureFlagManager.__init__`).
