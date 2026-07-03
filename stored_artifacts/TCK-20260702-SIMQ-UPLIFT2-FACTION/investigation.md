# Investigation — TCK-20260702-SIMQ-UPLIFT2-FACTION

## Current Behavior (file:line refs)

### The compile path never constructs any `FactionState` at all

`WorldCompiler.compile()` (`src/worldbuilding/compiler.py:106-444`) builds the initial
`AuthoritativeState` at lines 405-417:

```python
state = AuthoritativeState(
    tick=0, seed=seed, entities=entities, resource_nodes=resource_nodes,
    buildings=buildings, regions=regions, terrain=terrain,
    global_resources=global_resources, blocked_tiles=blocked_tiles,
    town_tiles=town_tiles, town_entity_ids=town_entity_ids
)
```

There is **no `factions=` kwarg**. `AuthoritativeState.factions` defaults to
`field(default_factory=dict)` (`src/core/state.py:1152`), so a freshly compiled world's
`state.factions` is an **empty dict**, not a dict of `FactionState(tension_level=0.0)`
entries as the ticket's Request Summary assumes. Step 3 of `compile()` (lines 175-192)
only initializes faction *gold vaults* in `global_resources` (e.g.
`global_resources["faction_town_council_gold"] = 1000.0`) — it never touches
`AuthoritativeState.factions`.

Grep across `src/` confirms the *only* place `FactionState(...)` is ever constructed is
`src/engine/apply.py:335`, inside the per-tick apply-path's faction-update merge loop:

```python
existing = new_factions.get(fu.faction_id)
if existing is None:
    existing = FactionState(faction_id=fu.faction_id)   # tension_level=0.0 default
```

This only runs when a `FactionUpdate` for that `faction_id` already exists in
`StateUpdate.faction_updates` for the tick. But the only producer of `FactionUpdate`
objects, `FactionAwarenessService.compute_tension_updates()`
(`src/engine/faction_decision.py:174-198`), itself iterates `state.factions.items()`
(line 195) — which is empty. **This is a closed loop with no bootstrap**: nothing ever
seeds the first `FactionState`, so `state.factions` stays `{}` for the entire run of any
compiled world, in perpetuity. `FactionDecisionPhase` (directives) and
`DiplomaticStateMachine.compute_transitions()` (`src/domains/faction/diplomatic_state_machine.py:38`,
called from `src/engine/pipeline.py:190`) also iterate `factions.keys()` / `.items()` and
are consequently permanent no-ops for every calibration world today. This is a more severe
finding than the ticket's framing ("all faction pairs start at tension_level=0.0") — there
are currently **zero** `FactionState` records in any compiled world, ever.

### `WorldSpec.factions` already exists and is already populated for `urban_political` (resolves UQ-1)

`WorldSpec.factions: list[FactionSpec]` (`src/worldbuilding/schema.py:134`) is a real,
already-wired schema field. `FactionSpec` (schema.py:47-51) currently has exactly two
fields:

```python
class FactionSpec(BaseModel):
    model_config = ConfigDict(frozen=True)
    id: str = Field(..., min_length=1, ...)
    type: str = Field(..., min_length=1, ...)
```

No tension field of any kind. `data/worlds/urban_political/resolved/world.resolved.yaml`
(lines 47-56) already has a `factions:` block with 7 entries including
`bandit_company` and `town_council`, sourced from two different world modules:
`town_council` from `data/content/world_modules/frontier_village_core.yaml`,
`bandit_company` from `data/content/world_modules/bandit_road_trade_pressure.yaml`. These
per-module `factions:` blocks are merged into the composed `WorldSpec.factions` list via
`src/worldmodules/normalizer.py:155` (`factions=list(spec.factions)`) and
`src/worldassembly/resolver.py` (lines 104/661/704/717/890 all thread a `factions` dict
through resolution/validation). So there is no "faction pair" declaration anywhere in the
schema — factions are individual entries, keyed by `id`.

### `tension_level` is a per-faction scalar, not a per-pair value (resolves UQ-1, corrects ticket's framing)

`FactionState.tension_level` (`src/core/state.py:615`) is one float **per faction**, not
per relationship. `compute_transitions()` derives a pair proxy from it:

```python
# src/domains/faction/diplomatic_state_machine.py:51
pair_tension = max(fa.tension_level, fb.tension_level)
```

So the ticket's plan to declare `bandit_company ↔ town_council tension_level=0.5` as a
*pair* entry does not match the schema's shape. The correct extension is a **per-faction**
field, e.g. `FactionSpec.initial_tension_level: float = 0.0`, added to each faction that
should start tense. Setting it on just one of the two factions (e.g.
`bandit_company.initial_tension_level = 0.5`) is sufficient to make
`pair_tension = max(0.5, town_council.tension_level) = 0.5 > 0.4` and fire
`NEUTRAL → TENSE`. Setting it on both is also valid and arguably more narratively honest
(bandit pressure on the town, and the town's guard posture rising in response) — this is
an implementation choice, not a schema constraint.

### `WorldCompiler` vs `WorldAssemblyResolver` (resolves UQ-2)

These are two distinct classes with a producer → consumer relationship, not aliases:

- `WorldAssemblyResolver` (`src/worldassembly/resolver.py:209`, entry point used by
  `src/worldbuilding/cli.py` and `src/lab/orchestrator.py`) resolves a
  `WorldCompositionSpec` (module refs + parameters) into a fully-merged `WorldSpec`
  object (`ResolvedWorldBundle.world_spec`) — this is where the `frontier_village_core` +
  `trading_company_hub` + `bandit_road_trade_pressure` + `hero_adventurers` modules get
  merged into the single `urban_political` `WorldSpec`, including the `factions:` list
  merge.
- `WorldCompiler.compile(spec: WorldSpec, seed: int, ...)` (`src/worldbuilding/compiler.py:112`)
  takes that *already-resolved* `WorldSpec` and turns it into the runtime
  `AuthoritativeState` (regions, entities, resource nodes, buildings — and, after this
  ticket, faction state). It is called from `src/cli/entry.py:216`,
  `src/worldbuilding/cli.py:282`, `src/lab/orchestrator.py:198`,
  `tools/calibrate_simq.py:128`, `tools/balance_measure.py:95`,
  `tools/personality_audit.py:47`. **This confirms the ticket's "compiler code path" language is
  correctly targeted at `WorldCompiler.compile()` step 3** (lines 175-192, immediately
  after faction gold-vault seeding is the natural insertion point for
  `FactionState` construction).

### `compute_transitions()` reads live state each tick, no caching (resolves UQ-3)

`compute_transitions(factions: Dict[str, FactionState])`
(`src/domains/faction/diplomatic_state_machine.py:25`) is a pure function. It is called
every tick at `src/engine/pipeline.py:190` as `compute_transitions(state.factions)`,
where `state` is the current tick's frozen `AuthoritativeState` — i.e. it reads
`AuthoritativeState.factions` **directly, live, with zero caching or snapshotting**.
`FactionAwarenessService.compute_tension_updates()` (`faction_decision.py:195`) and
`FactionDecisionPhase` (`faction_decision.py:126`) do the same. Because `FactionState`
is durable state that persists tick-to-tick via the typed `FactionUpdate` apply-path
(`apply.py:328-354`, confirmed by `test_faction_state_factions_persist_across_ticks` in
`tests/unit/faction/test_faction_state.py:170`), **seeding `tension_level` once at
compile time (tick 0) is sufficient** — the value will be present on `state.factions` from
tick 0 onward and read live by every phase every tick. No additional "activation" step is
needed beyond the compiler fix.

## Mechanics/Engine Constraints

- Chosen threshold `tension_level > 0.4` (NEUTRAL→TENSE) matches
  `docs/systems/faction_contract.md` "Tension Mechanics" and
  `diplomatic_state_machine.py:9` docstring priority table — `0.5` clears this
  threshold with margin.
- `DEFEND_BORDER` directive additionally fires at `tension_level > 0.5` AND non-empty
  `territory` (`docs/systems/faction_contract.md` Directive Kinds table,
  `src/engine/faction_constants.py`). At `tension_level=0.5` exactly, this is a `>` not
  `>=` comparison — verify the exact operator in `faction_decision.py` if the directive
  firing (not just the diplomatic transition) is desired as a side effect; the ticket's
  ACs only require the diplomatic_transition/faction_tension_delta event, so this is not
  blocking, just worth a code-level double-check during implementation.
- `TENSE → HOSTILE` additionally requires `pair_tension > 0.7` or shared territory
  (diplomatic_state_machine.py:69). At `0.5`, the pair stays at `TENSE` and does not
  cascade into `HOSTILE`/`WAR` on its own — consistent with the ticket's Out of Scope
  ("Diplomatic event gameplay beyond tension seeding").
- `AuthoritativeState.to_readonly()` (`src/core/state.py:1229`) already wraps `factions`
  with `ReadOnlyDict` — no change needed there for read-only exposure once populated.

## Parity Ledger Overlap (IDs + status)

`docs/parity_ledger/faction.yaml`:
- **FAC-001** (`verified`) — "AuthoritativeState.factions persists FactionState records
  across ticks via typed FactionUpdate apply-path." Accurate but incomplete after this
  ticket: it documents the *persist* half, not the *initial construction* half. No status
  change needed (still true), but the `v2_evidence` should be extended to mention the new
  compile-time seeding path, or a new entry added (see below).
- **FAC-006** (`verified`) — `compute_transitions()` wiring — accurate, unaffected.
- **FACTION-TENSION-001** (`verified`) — resource-depletion tension delta — accurate,
  unaffected (this ticket does not touch that path).

`docs/parity_ledger/social_narrative.yaml`:
- **SOC-FAC-001..010** — chronicle/significance/naming entries, all downstream of events
  actually firing. Unaffected by this ticket directly, but SOC-FAC-001
  (war_declared significance) becomes reachable in practice for the first time once
  tension seeding exists (still requires HOSTILE→WAR cascade, out of scope here).

**New entry needed**: no existing FAC-* entry documents "FactionState is constructed with
non-zero `tension_level` at world-compile time from `WorldSpec`/`FactionSpec`." Recommend
adding **FAC-012** (or `FACTION-SEED-001`) to `docs/parity_ledger/faction.yaml` once
implemented, with `v2_evidence` pointing at `src/worldbuilding/compiler.py` step 3 and
`src/worldbuilding/schema.py::FactionSpec.initial_tension_level`, `priority: P1`,
`test_path` pointing at the new compiler unit test.

## Prior Work

- **TCK-20260619-E53Aa-FACTION-STATE** (done) — Added `FactionState`/`FactionUpdate`
  and the apply-path merge. Its Implementation Notes explicitly scoped compiler
  integration **out**: `apply.py` was updated to accept `factions=new_factions`, but
  `WorldCompiler.compile()` was never touched. This is the origin of the gap this ticket
  closes — not a bug introduced later, but a scope boundary drawn at E53Aa that nobody
  closed.
- **TCK-20260619-E53Dc-COMPILER-INTEGRATION** (done) — Despite the name, this ticket is
  about `ChronicleCompiler` (narrative rendering), not `WorldCompiler`. Not relevant to
  this ticket's compiler path; noted to avoid confusion from the similar name.
- **TCK-20260627-P2D-FACTION-RELS** (done) — Added 34 entries to
  `data/content/social/faction_relationships.yaml` (a separate *content catalog*
  describing hostile/rival/trade/alliance stances between the 16-faction catalog). That
  ticket's own scope note says the engine system that reads these entries does not exist
  yet. It is unrelated to `FactionState.tension_level` / `WorldSpec.factions` — a
  different faction subsystem (qualitative relationship labels) with no runtime consumer.
  Do not conflate the two; this ticket's `initial_tension_level` is a new, narrower field
  on `FactionSpec`, not a use of `faction_relationships.yaml`.
- **stored_artifacts/TCK-20260702-SIMQ-UPLIFT-SOCIAL-ZERO/investigation.md** (FACTION
  Deferral section, lines 12-53, 98-99, 111-117, 141-148) — root-caused this exact gap as
  hypothesis (c1) and explicitly deferred the fix to a follow-up ticket, which is this
  ticket. Its framing ("all factions start with tension_level=0.0, territory=()")
  undersells the actual severity (factions dict is empty, not populated-with-zeros) but
  the fix direction it recommends ("Set tension_level=0.5 on at least two factions... OR
  assign territory") matches what this investigation confirms.

## Risks and Open Questions

- **Module-level merge collision**: `bandit_company` and `town_council` are declared in
  *different* world modules (`bandit_road_trade_pressure.yaml`,
  `frontier_village_core.yaml`). Adding `initial_tension_level` requires editing the
  *module* YAML (not `data/worlds/urban_political/world.yaml`, which only references
  modules by `module_id`). Confirm `WorldAssemblyResolver`'s faction-merge step
  (dedupe-by-`id` behavior across modules) tolerates the new optional field with a
  default — since `FactionSpec` gets a `default=0.0`, existing worlds/modules with no
  `initial_tension_level` key will validate unchanged (Pydantic default field semantics),
  so this should be low-risk, but must be exercised by the "existing worlds still compile
  cleanly" regression AC.
- **Determinism / state hash**: `StateFingerprinter.get_fingerprint()`
  (`src/replay/fingerprint.py:33-80`) does **not** currently include `state.factions` in
  its hashed fields (entities, global_resources, resource_nodes, regions, local_scars,
  groups, macro world state — no `factions` line). This means seeding `tension_level`
  will **not** change `state_hash` in `world_compile_report.json` or
  `tests/certification/test_world_compile_determinism.py`, so no regression risk there —
  but it also means faction state is currently invisible to the replay/certification
  fingerprint, a pre-existing gap worth flagging (not fixing) since it means
  faction-driven divergence between two "identical" replays would not be caught by this
  test today. Out of scope for this ticket; noted as an anti-drift hazard.
- **Directive side effect at exactly 0.5**: confirm the `>` vs `>=` operator on
  `DEFEND_BORDER`'s `tension_level > 0.5` gate (`faction_constants.py` /
  `faction_decision.py`) before assuming `tension_level=0.5` alone triggers or does not
  trigger that directive — immaterial to this ticket's ACs but could surprise calibration
  numbers if `DEFEND_BORDER`-driven urgency deltas shift entity behavior unexpectedly.
- **Two-faction vs one-faction seeding choice**: seeding only `bandit_company` (or only
  `town_council`) is schema-sufficient per the `max()` proxy, but the ticket's Scope item
  4 explicitly frames it as a pair (`bandit_company ↔ town_council: tension_level=0.5`).
  Implementer should decide and document whether both factions get
  `initial_tension_level=0.5` (symmetric, matches ticket prose) or just one (schema-
  minimal). This does not need a human decision — either satisfies the ACs — but should
  be stated explicitly in the ticket's Implementation Notes once decided, since it affects
  calibration output (e.g. `DEFEND_BORDER` directive would fire for whichever faction(s)
  carry `tension_level > 0.5`, which it won't at exactly `0.5`, but would if a future
  ticket nudges the value).

## Anti-Drift Hazards

- Do not model `initial_tension_level` as a new pair/relationship object — it must be a
  scalar field on the existing `FactionSpec` (per-faction), matching the runtime
  `FactionState.tension_level` shape exactly. Introducing a pair-keyed structure would
  require also changing `FactionState`/`compute_transitions()`, which is out of scope and
  would be a much larger, unrequested refactor.
  scoring weights (this ticket is explicitly "Out of Scope: Changing FACTION scoring
  weights").
- Do not touch `data/content/social/faction_relationships.yaml` or its resolver
  (`RelationshipResolver`, `resolve_faction_relationship` in `src/content/resolver.py`) —
  that is a separate, currently-unconsumed content catalog for qualitative relationship
  labels, unrelated to `FactionState.tension_level`. Conflating the two would silently
  create durable content with no runtime reader (violates the Durable State Rule).
- `AuthoritativeState.factions` construction must go through `WorldCompiler.compile()`'s
  single `AuthoritativeState(...)` constructor call (compiler.py:405) — do not add a
  second, separate faction-seeding pass elsewhere (e.g. in `WorldAssemblyResolver` or a
  post-compile patch step) — that would create two divergent seeding code paths and break
  the "Authoritative application is the only place durable state should be committed"
  rule in spirit (compile-time construction is the one authoritative init point for a
  fresh `AuthoritativeState`).
- Existing worlds without `initial_tension_level` in any module must compile to
  `FactionState(tension_level=0.0, ...)` for every declared faction (default fully
  transparent) — the regression AC "existing worlds with no initial_tension_level
  declared still compile to tension_level=0.0" implies `WorldCompiler.compile()` should
  now construct a `FactionState` entry for **every** `FactionSpec` in `spec.factions`
  (not just ones with non-zero tension), so `state.factions` stops being permanently
  empty for all worlds, not just `urban_political`. This is a bigger behavior change than
  a literal reading of the ticket title ("seed tension") suggests — confirm this is
  intended (it must be, since `compute_transitions()`, `FactionDecisionPhase`, and
  `FactionAwarenessService` all require faction entries to exist at all, non-zero-tension
  or not, to do anything) and treat "compile the full faction roster into
  AuthoritativeState.factions" as the real scope, with tension-seeding as the specific
  urban_political content change.
