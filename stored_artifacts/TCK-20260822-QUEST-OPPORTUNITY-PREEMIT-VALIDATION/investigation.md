---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260822-QUEST-OPPORTUNITY-PREEMIT-VALIDATION
artifact_type: investigation
tags: [world, content, determinism]
---

# Investigation — TCK-20260822-QUEST-OPPORTUNITY-PREEMIT-VALIDATION

> **Note on Context Scan**: `mcp__knowledge-search__search_docs` returned `{"error": "index not
> found"}` (query: "Pre-Emit Grammar Validation for Procedurally-Generated Quest Opportunities
> QuestOpportunityGenerator faction resource availability"). The documented fallback,
> `python3 tools/knowledge_search.py query "..." --top-k 5`, returned `knowledge index not found —
> run make knowledge-index` — same underlying gap, skipped per instructions. `graphify` CLI failed
> in this worktree (`graph file not found:
> .../hud-design-system-foundation-epic/graphify-out/graph.json` — this worktree has no built
> graph). The main repo checkout (`/home/u24desktop/Working/rpg-based-simulation`) has a live
> `graphify-out/graph.json`, so `graphify query "QuestOpportunityGenerator pre-emit validation
> faction coherence resource availability"` was run from there instead of falling all the way back
> to reading `GRAPH_REPORT.md` — it returned 203 traversed nodes (`QuestOpportunityGenerator`,
> `QuestOpportunity`, `FactionState`(via `Faction`)/community 0 & 12, `WorldEmergencePhase`,
> `AuthoritativeState`, `CatalogRepository`, `FactionSemanticsService`), all of which line up with
> the file set below. No additional prior-art doc surfaced beyond what the ticket's own Related
> Tickets/Docs and `docs/REGISTRY.yaml` already named. This matches the same offline-index
> condition the predecessor ticket's own investigation recorded.

## Resolving the Blocking Open Question (Sequencing Dependency on TCK-20260822-WORLD-GRAMMAR-REACHABILITY-VALIDATOR)

The Scope phase correctly flagged doubt about what the reachability-validator ticket actually
delivered. Direct read of `tickets/done/TCK-20260822-WORLD-GRAMMAR-REACHABILITY-VALIDATOR.md`,
`src/worldbuilding/reachability.py`, and `src/worldbuilding/validator.py` confirms the **narrower**
reading is correct, precisely as the Scope phase suspected:

- **What actually shipped**: `ParticipantReachabilityRule` (`rule_id="WORLD-REACH-001"`), a
  `WorldValidationRule` subclass wired only into `WorldValidator`/`WorldAssemblyValidator` — a
  **build-time, `WorldSpec`-only** check. It operates on `WorldSpec.quest_definitions` /
  `PopulationSpec.archetype_id` / `CatalogRepository`, none of which exist on
  `AuthoritativeState`. There is no "runtime-callable rule API against AuthoritativeState" — that
  phrase in this ticket's own Request Summary describes something that was never built.
- **What is genuinely reusable**: `src/worldbuilding/reachability.py` holds three **pure,
  dependency-light functions** — `is_reachable(required_tags, available_tags)`,
  `resolve_population_tags(population, catalog_repo)`, `build_available_participant_tags(spec,
  catalog_repo)`. Of these, only `is_reachable` (lines 15-24) is truly signature-generic: it takes
  a `list[str]` and an `Optional[set[str]]` and returns a bool, with no `WorldSpec`/`PopulationSpec`
  coupling. `resolve_population_tags` and `build_available_participant_tags` are hard-typed to
  `PopulationSpec`/`WorldSpec`/`CatalogRepository` (worldbuilding/schema.py, content/repository.py)
  and **cannot** be called against `AuthoritativeState`, `FactionState`, or `ResourceNodeState` —
  those types don't exist in that module's signatures at all.
- **What the predecessor ticket's own Implementation Notes say** (point 2, lines 97-101 of the done
  ticket): the module was "deliberately decoupled from `WorldValidationRule` so the downstream
  `TCK-20260822-QUEST-OPPORTUNITY-PREEMIT-VALIDATION` ticket can reuse the **core predicate**
  against `AuthoritativeState`-derived tag sets" — singular "predicate," i.e. `is_reachable`, not a
  turnkey rule engine.

**Conclusion**: this ticket is not blocked by a missing API — the sequencing dependency is
satisfied in the narrow sense that stops this ticket being *premature* (a generic tag-subset
predicate now exists to imitate the pattern from), but this ticket must **write its own**
AuthoritativeState-facing availability-set builders (analogous to `build_available_participant_tags`
but sourced from `state.factions`/`state.resource_nodes` instead of `WorldSpec.entities`), not call
an existing runtime API — none exists. `WorldValidator`/`ParticipantReachabilityRule`/
`ValidationContext` are confirmed out of scope for this ticket (per its own Out of Scope section)
and are not touched. The reusable surface is exactly: the `is_reachable` predicate itself, and the
architectural pattern it and `ParticipantReachabilityRule` establish (pure functions +
`Optional[...]`-as-"cannot verify" signaling, consumed by a thin call site).

## Current Behavior

**`QuestOpportunityGenerator`** (`src/domains/world_emergence/services.py:166-259`) — three static
methods, all read-only, no `quest_registry` writes:
- `from_resource_depleted()` (185-216): builds a `resource_crisis` `QuestOpportunity` from a
  `RESOURCE_DEPLETED` `WorldEvent`. `faction_source=None` is hardcoded (line 213).
  `objective_chain=(f"fetch:{resource}:{quantity}",)` where `resource = event.subject` (214, e.g.
  `"iron_ore"`) — the resource identity is a bare string, not a `ResourceNodeState.id`.
- `from_threat_signal()` (218-249): builds a `threat_response` opportunity from a high-severity
  `ENTITY_DEATH`/`CAMP_RAID` event. `faction_source=None` hardcoded (line 246) here too.
- `from_entity_need()` (251-259): stub, always returns `None` (Phase 5 not built yet) — not
  reachable from `phase.py` today, out of scope.

**`WorldEmergencePhase.execute()`** (`src/domains/world_emergence/phase.py:21-136`) — step 5b
(lines 61-75) is the exact integration point named in scope:
```python
quest_opps = []
for ev in recent_events:
    if ev.category == WorldEventCategory.RESOURCE_DEPLETED:
        opp = QuestOpportunityGenerator.from_resource_depleted(ev, state.tick, state.seed)
        if opp is not None:
            quest_opps.append(opp)
    elif ev.severity >= 0.5 and ev.category in (...ENTITY_DEATH, CAMP_RAID...):
        opp = QuestOpportunityGenerator.from_threat_signal(ev, state.tick, state.seed)
        if opp is not None:
            quest_opps.append(opp)
```
Line 134: `quest_registry_add=list(quest_opps)` — every generated opportunity is unconditionally
forwarded into the `StateUpdate`, with **no filtering step today**. This is the exact line the
implementation must change to apply the new pre-emit check.

**`QuestOpportunity`** (`src/core/models/quests.py:65-83`) — frozen dataclass. Relevant fields for
this ticket: `objective_chain: Tuple[str, ...]` (tokens like `"fetch:iron_ore:3"` /
`"eliminate:threat:1"`), `faction_source: Optional[str]` (currently always `None` from both live
generator paths), `reward_spec: Dict[str, Any]` (includes `"faction_rep"` even when
`faction_source` is `None` — the reward key exists independent of whether a faction is attached).

**Authoritative apply path** (`src/engine/apply.py:327-332`): `StateUpdate.quest_registry_add` is
merged into `state.quest_registry` (dict keyed by `QuestOpportunity.id`) idempotently — duplicate
IDs are skipped, not overwritten. This is the correct, already-existing durable-write channel; the
new check only needs to control **what enters** the list assigned to `quest_registry_add`, not
build a new write path.

**Faction durable state** (`src/core/state.py:608-645`): `FactionState` (E53 family) —
`faction_id: str`, `territory: Tuple[str, ...]` (region_ids controlled). Held in
`AuthoritativeState.factions: Dict[str, FactionState]` (line 1156), applied via
`FactionUpdate.territory_add`/`territory_remove` (`src/core/updates.py:856-865`,
`src/engine/apply.py:338-360`). **This is a distinct representation from
`RegionState.owner_faction_id: Optional[int]`** (`src/core/state.py:249`, legacy `Faction` enum
int) and from the content-catalog `FactionDefinition` (string ID, resolved via
`FactionSemanticsService`, `src/content_semantics/faction.py`). `QuestOpportunity.faction_source` is
typed `Optional[str]`, which only lines up structurally with `FactionState.faction_id` (also `str`)
— not with the legacy int enum. **Design decision for the plan**: faction-coherence must check
`state.factions.get(faction_source)` and its `.territory` tuple, not `RegionState.owner_faction_id`.
A faction absent from `state.factions` entirely (dissolved, or never registered) has zero
territorial presence by definition and must reject the same as a present-but-empty-territory
faction — this needs to be an explicit branch, not an implicit `None`-attribute crash.

**Resource durable state** (`src/core/state.py:907-942`): `ResourceNodeState` — **no `quantity`
field exists**. The field is `remaining_charges: int` (with `max_charges`, `regen_rate_per_tick`).
The ticket's own Scope/AC text ("depleted, quantity==0 resource node") uses a field name that does
not exist on the model; the correct predicate is `remaining_charges == 0`. This is a
naming-precision gap in the ticket text, not a functional blocker — flagged here so the plan uses
the real field name. `AuthoritativeState.resource_nodes: Dict[int, ResourceNodeState]` (line 1096)
is keyed by integer node `id`, **not** by `yields_item` string — matching
`objective_chain`'s `"fetch:iron_ore:3"` token (an item/resource-type string) against nodes
requires scanning `resource_nodes.values()` for `yields_item == resource_type`, there is no direct
key lookup. No existing code in this repo does this specific match today —
`ScarcityModel.evaluate()` (`src/domains/world_emergence/models.py:238-278`) computes scarcity from
`WorldEventAggregate` counts (harvested/depleted event tallies), not from live `resource_nodes`
state, so it is not a reusable precedent for this ticket's resource-availability check.

## Mechanics / Engine Constraints

- `docs/mechanics/06_worldbuilding_foundation.md` §7 ("Integrity Validation Laws & Severity Gates")
  defines the 3-level gate model (Pydantic → Structural/Spatial → Runtime-Gated Compiler) and its
  "Participant Reachability Rule (`WORLD-REACH-001`)" subsection — this is explicitly the
  **build-time** gate model and does not cover runtime/post-authoring checks. This ticket's check
  runs inside `WorldEmergencePhase`, a live per-tick engine phase, not the WorldSpec→Compile
  pipeline §7 describes; it is a **new, distinct gate**, not an extension of §7's gate ladder.
- Durable State Rule (`CLAUDE.md`): the check itself must not create new durable state — it reads
  `state.factions`/`state.resource_nodes` and returns a verdict; the only durable effect is which
  `QuestOpportunity` objects reach `update.quest_registry_add`, which is already the correct typed
  channel.
- Architecture Rule / Core Boundaries: "Decision logic reads state. It does not authoritatively
  mutate durable state." — the check must be a pure function of `(QuestOpportunity,
  AuthoritativeState)`, matching the pattern `is_reachable`/`ParticipantReachabilityRule` already
  establish, and matching this ticket's own AC4 (deterministic, read-only, no mutation).
- `docs/plans/idea_world_grammar_semantic_constraints.md` ("Grammar rule types" table) defines
  **Faction coherence** as "If a quest involves faction tension, both factions must have
  territorial presence" (originally envisioned as a two-faction check) and **Resource coverage**
  as "every resource node type referenced by a quest must exist in ≥1 biome region." Neither
  matches this ticket's runtime shape exactly: `QuestOpportunity` only ever carries a single
  `faction_source` (not two factions in tension), and the runtime resource check is about **current
  depletion state** of an already-existing node, not about the node's *existence* at authoring
  time (that's WORLD-REACH-001's build-time job, already covered). This ticket's two checks are the
  runtime-appropriate reinterpretation of those two idea-doc rule classes, not a literal
  implementation of the doc's original wording — worth stating explicitly in the plan so a reviewer
  doesn't expect two-faction tension logic.
- The idea doc's own **Open Questions** (Python predicates vs. YAML rules; runtime-vs-build-time
  cadence; "runtime grammar must be cheaper than build-time grammar") remain unresolved by the
  predecessor ticket and are inherited here unresolved — see Risks below. Given
  `is_reachable`/`ParticipantReachabilityRule` already established the "Python predicate function"
  pattern, and `WorldEmergencePhase` has no YAML-rule-loading machinery at all, the de facto answer
  is "Python predicates" — this should be recorded as the explicit decision in the plan rather than
  left implicit.

## Docs Requiring Update

- `docs/mechanics/06_worldbuilding_foundation.md`: this ticket adds a new runtime validation gate
  (faction-coherence + resource-availability pre-emit checks) that is a sibling to, but distinct
  from, §7's build-time gate ladder and the WORLD-REACH-001 subsection it documents; §7 (or a new
  adjacent section, e.g. a "Runtime Pre-Emit Validation" subsection) must describe the new gate so
  the Mechanics Bible stays the authoritative description of what blocks a `QuestOpportunity` from
  reaching `quest_registry`, per the Authoritative Mechanics Rule's "new logic/features/settings
  count as behavior needing a doc" instruction.
- `docs/parity_ledger/world_dynamics.yaml`: entry `WORLD-102` currently states "QuestOpportunity
  objects produced by WorldEmergencePhase are added to quest_registry via
  StateUpdate.quest_registry_add through the authoritative apply path... addition is idempotent
  (duplicate IDs are skipped)" citing `phase.py`'s unconditional `quest_registry_add=list(quest_opps)`
  line as `v2_evidence`. Once this ticket makes that line conditional (filtered), the `v2_evidence`
  reference is stale unless updated to describe the new filtering step — this is a genuine parity
  drift this ticket introduces and must record in the same session per the Authoritative Mechanics
  Rule's "Parity" clause.

The `docs/plans/idea_world_grammar_semantic_constraints.md` idea doc (path:
`docs/plans/idea_world_grammar_semantic_constraints.md`) is not required to change for this ticket:
it is explicitly out of scope to promote per the predecessor ticket's own Out of Scope section, and
this ticket only needs to cite it as prior context, not amend its content — the reinterpretation
noted above (single faction_source vs. two-faction tension; depletion-state vs. existence-check)
belongs in the Mechanics Bible entry this ticket adds, not as an edit to the historical idea doc.

## Parity Ledger Overlap

- `WORLD-098` (`docs/parity_ledger/world_dynamics.yaml`) — "QuestOpportunity is generated
  deterministically from RESOURCE_DEPLETED events via `QuestOpportunityGenerator.from_resource_depleted()`."
  status `verified`, priority P1, `test_path:
  tests/unit/quest/test_quest_generation.py::test_resource_crisis_quest_generated_on_depletion`.
  Unaffected by this ticket (generation logic itself does not change) but its cited test is also
  one of the two AC3 "must continue passing unmodified" tests — confirms this entry's evidence
  chain stays valid only if the pre-emit filter sits at the `phase.py` call site, not inside
  `QuestOpportunityGenerator` itself.
- `WORLD-100` / `WORLD-101` (same file) — `quest_registry` persistence and expiry sweep. Not
  touched by this ticket; the pre-emit filter runs strictly before entries reach
  `quest_registry_add`, upstream of both.
- **`WORLD-102`** (same file) — the entry requiring an update per "Docs Requiring Update" above;
  its `v2_evidence` cites the exact `phase.py` line this ticket changes.
- `SUB-387` (`docs/parity_ledger/substrate.yaml`) — the predecessor ticket's own new entry for
  `WORLD-REACH-001`. Overlaps conceptually (both are "grammar"-style checks) but is **not** touched
  by this ticket: it covers build-time `WorldSpec` validation, a fully separate code path
  (confirmed above). No P0 entries were found overlapping this ticket's scope; `WORLD-098`/`-100`/
  `-101`/`-102` and `SUB-387` are all P1/P2, so no `test_path` is contractually required to keep
  passing beyond the AC3 regression requirement already stated in the ticket.

## Prior Work

- `tickets/done/TCK-20260822-WORLD-GRAMMAR-REACHABILITY-VALIDATOR.md` +
  `stored_artifacts/TCK-20260822-WORLD-GRAMMAR-REACHABILITY-VALIDATOR/` (investigation.md, plan.md,
  test_plan.md) — direct predecessor; see "Resolving the Blocking Open Question" above. Its
  `plan.md`/`test_plan.md` establish the pattern this ticket should mirror: pure predicate module +
  thin rule/call-site wrapper + dedicated unit tests + a corpus/registry-style regression test +
  Mechanics Bible subsection + one new parity entry.
- `docs/REGISTRY.yaml` query (filtered on `related_code_areas`/`tags` overlapping
  `world_emergence`/`quest`/`faction`) surfaced no other done ticket that implements an
  AuthoritativeState-facing faction-territory or resource-depletion **gating** check; the closest
  adjacent ticket, `TCK-20260619-E53Ad-TENSION-UPDATE.md` (`src/engine/faction_decision.py`,
  `RESOURCE_DEPLETED` events → faction tension), is about *raising* tension from depletion events,
  not about *rejecting* quest content based on faction/resource state — informative context, not
  reusable code.
- The ticket's own Out of Scope section correctly rules out `TCK-20260807-QUEST-GUILDACTION-DEAD-WIRING`
  and `TCK-20260807-QUEST-HUNT-TARGET-METADATA-GAP` as precedent (both concern `QuestState` via
  `GuildAction.visit()`, a fully separate legacy pipeline from `QuestOpportunity`) — confirmed
  correct on inspection of `graphify query` community membership (`QuestOpportunityGenerator`
  community 12 vs. `QuestGenerator`/`QuestState`-adjacent nodes in a different community, matching
  the ticket's own "364 vs 935" community-distinctness claim).

## Risks and Open Questions

- **Objective-chain resource matching has no existing precedent to match token format against node
  state.** `objective_chain` tokens are free-form strings (`"fetch:iron_ore:3"`) with no schema
  enforcing the `verb:resource:qty` shape beyond convention in the two live generator methods. The
  plan must define an explicit, tolerant parse (e.g. split on `:`, treat unparseable tokens as
  "cannot verify" rather than crashing) — this is a genuine open design decision, not assumable.
- **Zero-matching-node ambiguity.** `state.resource_nodes` may contain no node with
  `yields_item == resource_type` at all (e.g. the existing
  `test_world_emergence_populates_quest_registry` test builds a bare `AuthoritativeState(tick=5,
  seed=1)` with an empty `resource_nodes` dict, yet AC3 requires this exact test keep passing
  unmodified). The check must treat "no matching node found anywhere" as **cannot-verify → pass**
  (mirroring `is_reachable`'s `available_tags is None` semantics), and reserve **rejection** only
  for the case where at least one matching node exists and **all** matching nodes for that resource
  are at `remaining_charges == 0`. Getting this backwards (treating "no node found" as "depleted")
  would break the AC3 regression requirement immediately. This is stated as a design decision here,
  not an assumption the plan should re-derive from scratch.
- **`faction_source=None` behavior is currently unreachable from live code**, since both
  `from_resource_depleted` and `from_threat_signal` hardcode `faction_source=None`. AC5 requires
  "defined, documented behavior" for this case — the natural, `is_reachable`-consistent answer is
  "no faction claim to verify → auto-pass," but since no live path ever produces a non-`None`
  `faction_source` today, the negative-path faction-coherence test (AC2) **cannot be exercised
  through the real generator** — it requires directly constructing a `QuestOpportunity` with a
  non-`None` `faction_source` as a test fixture (confirmed: no such fixture exists in the current
  test harness, matching the ticket's own Assumptions section).
- **Two structurally different "faction ID" spaces coexist** (`FactionState.faction_id: str` in
  `state.factions` vs. `RegionState.owner_faction_id: Optional[int]`, the legacy `Faction` enum).
  The investigation resolves this as: match against `state.factions` (str-keyed, matches
  `faction_source`'s type) — but this is a design decision the plan must state explicitly and a
  reviewer should double check, since it's plausible (though less consistent with the field's type)
  that "territorial presence" was meant in the `RegionState.owner_faction_id` sense used elsewhere
  in the codebase for region ownership/combat.
- **Tick-budget concern is likely a non-issue but unverified**: `WorldEmergencePhase` runs every
  tick and tracks `metric_counters['world_emergence_ms']`. `quest_opps` per tick is typically 0-2
  items (bounded by `recent_events` volume), and `state.factions`/`state.resource_nodes` dict
  lookups are O(1)/O(n) over a small n — the added cost should be negligible, but the ticket's own
  Out-of-Scope section defers "any performance-optimization work" as a follow-up if the naive check
  proves too costly, implying the naive version is expected baseline scope, not a proven-safe
  assumption. No profiling was run as part of this investigation.

## Anti-Drift Hazards

- **Do not touch `src/worldbuilding/validator.py` or `WorldValidator`.** The predecessor ticket's
  `ParticipantReachabilityRule`/`WorldValidationRule`/`ValidationContext` machinery is confirmed
  build-time/`WorldSpec`-only and explicitly out of scope here; a plan that tries to "reuse" it by
  constructing a fake `WorldSpec` from `AuthoritativeState` would be a significant, unwarranted
  scope expansion and an architectural misuse (mixing build-time and runtime state shapes).
- **Do not modify `QuestOpportunityGenerator.from_resource_depleted`/`from_threat_signal`
  themselves.** They are documented read-only/deterministic/no-uuid generators; the filter belongs
  at the `phase.py` step-5b call site (or a small wrapper called from there), consuming their
  output — not inside the generator methods, which would conflate "opportunity synthesis" with
  "opportunity admission" and risk breaking `WORLD-098`/`WORLD-099`'s parity evidence, which cites
  the generator methods directly.
- **Do not silently drop rejected opportunities without an observable signal.** AC2/AC3 require
  "explicit rejection (not a silent None-passthrough)" — a plan that simply omits rejected
  `QuestOpportunity` objects from `quest_registry_add` with no counter/log/return value satisfies
  the narrow letter of "excluded from quest_registry_add" but risks failing the AC's "explicit
  rejection" spirit if there's no way to observe *why* an opportunity was dropped (relevant for
  debugging and for a future regression-baseline test analogous to
  `test_corpus_reachability_baseline.py`). The plan should decide whether rejections get a
  lightweight structured return type (mirroring `ValidationIssue`) or at minimum a metric counter.
- **Do not use `RegionState.owner_faction_id`** for the faction-coherence check without a deliberate
  decision to do so instead of `state.factions`/`FactionState.territory` — see Risks above; picking
  the wrong one silently produces a check that always passes (if `state.factions` is used but never
  populated in the target world) or always fails (type-mismatch comparing a `str` `faction_source`
  against `int` region-owner IDs).
- **Do not treat "iron_ore" (an item/resource-type string) as a `ResourceNodeState.id`** (an int) —
  a naive `state.resource_nodes.get(resource_type)` lookup would always miss (`resource_nodes` is
  keyed by int id, not string), silently degrading to "never found → always cannot-verify → always
  passes," which would make the resource-availability check inert without any visible test failure
  unless a test explicitly constructs a real depleted node and checks for rejection.
