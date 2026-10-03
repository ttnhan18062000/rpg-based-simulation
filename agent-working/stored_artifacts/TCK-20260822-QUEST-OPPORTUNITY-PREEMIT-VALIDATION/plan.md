---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260822-QUEST-OPPORTUNITY-PREEMIT-VALIDATION
artifact_type: plan
tags: [world, content, determinism]
---

# Implementation Plan — TCK-20260822-QUEST-OPPORTUNITY-PREEMIT-VALIDATION

## Summary

Add a new pure-predicate module, `src/domains/world_emergence/quest_grammar.py`, that reuses
`is_reachable` (`src/worldbuilding/reachability.py:15-24`) for the faction-coherence check and
introduces a bespoke, tolerant-parse predicate for the resource-availability check, both operating
directly on `AuthoritativeState` (`state.factions: Dict[str, FactionState]` at
`src/core/state.py:1156`, `state.resource_nodes: Dict[int, ResourceNodeState]` at
`src/core/state.py:1096`). A single combinator, `validate_quest_opportunity()`, is then wired into
`WorldEmergencePhase.execute()` step 5b (`src/domains/world_emergence/phase.py:61-75, 134`) to filter
only the list assigned to `update.quest_registry_add` — the raw `quest_opps` list that feeds
`result.quest_opportunities` (`phase.py:94`) is left untouched, since that field is independently
tested (`tests/unit/quest/test_quest_generation.py::test_world_emergence_phase_emits_quest_opportunities`,
verified by direct grep — not filtered per ticket scope). No existing file is modified beyond
`phase.py` (the call site) and the two doc/parity files the Authoritative Mechanics Rule requires;
`QuestOpportunityGenerator`, `src/worldbuilding/validator.py`, and `WorldValidator` are untouched.

## Steps

### Step 1 — Faction-coherence predicate (reuses `is_reachable`)
**Files:** `src/domains/world_emergence/quest_grammar.py` (new)
**Change:**
- Create `build_faction_territory_pool(state: AuthoritativeState) -> set[str]`: returns
  `{faction_id for faction_id, f in state.factions.items() if f.territory}` — i.e. only factions
  with a non-empty `territory` tuple contribute to the pool. `FactionState.territory: Tuple[str,
  ...] = ()` is confirmed at `src/core/state.py:608-618`; `state.factions: Dict[str, FactionState]`
  is confirmed at `src/core/state.py:1156`. This function always returns a real `set` (possibly
  empty), never `None` — it is not a "no catalog available" signal, it is a real, checkable pool,
  matching the `build_available_participant_tags` docstring's own empty-set-vs-`None` distinction
  (`src/worldbuilding/reachability.py:45-56`).
- Create `check_faction_coherence(faction_source: Optional[str], state: AuthoritativeState) ->
  bool`: `required = [faction_source] if faction_source else []`; `pool =
  build_faction_territory_pool(state)`; `return is_reachable(required, pool)`, importing
  `is_reachable` from `src.worldbuilding.reachability` (signature confirmed generic:
  `is_reachable(required_tags: list[str], available_tags: Optional[set[str]]) -> bool`,
  `reachability.py:15`). Because `pool` is always a real set (never `None`), a `faction_source` not
  present in `pool` — whether because the faction is absent from `state.factions` entirely, or
  present with `territory=()` — falls through `is_reachable`'s `set(required_tags).issubset(pool)`
  branch and returns `False` (reject), satisfying the investigation's "absent-from-factions must
  reject the same as present-with-empty-territory" design decision uniformly, with no special-case
  branch needed. When `faction_source is None`, `required=[]` and `is_reachable([], pool)` returns
  `True` unconditionally via its own `if not required_tags: return True` branch
  (`reachability.py:20-21`) — this is AC5's defined behavior, reusing existing logic rather than
  reimplementing it.
- **Other writers to `state.factions` this check must not race with**: `FactionUpdate.territory_add`
  / `territory_remove` (`src/core/updates.py:856-865`) applied via `src/engine/apply.py:338-360`.
  This check only ever reads the `state` snapshot passed into `WorldEmergencePhase.execute()` — it
  never reads or writes a live/mutable reference — so it cannot race with the authoritative apply
  path, which only runs after all phases (including this one) have returned their `StateUpdate`s for
  the tick.
**Do NOT touch:** `RegionState.owner_faction_id` (legacy int enum, `src/core/state.py:249`) — do
not use it as an alternative or fallback source of "territorial presence."
**Verify:** `test_faction_coherence_rejects_zero_territory_faction`,
`test_faction_coherence_accepts_faction_with_territory`,
`test_faction_coherence_passes_when_faction_source_is_none` (new file
`tests/unit/domains/world_emergence/test_quest_opportunity_preemit_validation.py`).

### Step 2 — Resource-availability predicate (bespoke tolerant parse)
**Files:** `src/domains/world_emergence/quest_grammar.py` (same file as Step 1)
**Change:**
- Create `_parse_fetch_resource_type(token: str) -> Optional[str]`: split `token` on `":"`; if the
  result has at least 2 parts and `parts[0] == "fetch"`, return `parts[1]`; otherwise return `None`.
  **Design decision**: only `"fetch:<resource>:<qty>"` tokens are resource-availability-checkable.
  The only other live token shape is `"eliminate:<subject>:1"` from `from_threat_signal`
  (`src/domains/world_emergence/services.py:235`), where `subject` is a threat identifier, not a
  resource-node `yields_item` value — checking it against `resource_nodes` would be a coincidental,
  meaningless match, not a real grammar constraint. This is a plan-level design call (not
  re-escalated as an open question) because it follows directly from the only two token shapes that
  exist anywhere in the live generators (verified by reading both methods,
  `services.py:184-249`) and matches the ticket's own AC2 wording ("objective_chain references a
  ... resource node").
- Create `check_resource_availability(objective_chain: Tuple[str, ...], state: AuthoritativeState)
  -> bool`: for each token, resolve `resource_type` via `_parse_fetch_resource_type`; if `None`,
  skip (nothing to verify for this token). Otherwise gather `matching = [n for n in
  state.resource_nodes.values() if n.yields_item == resource_type]` (`ResourceNodeState.yields_item:
  str` and `.remaining_charges: int` confirmed at `src/core/state.py:908-919`;
  `state.resource_nodes: Dict[int, ResourceNodeState]` confirmed at `src/core/state.py:1096`, keyed
  by int `id` — never by `yields_item`, so the check must scan `.values()`, not do a dict lookup by
  resource-type string). If `matching` is empty, treat as cannot-verify and continue (no rejection
  contributed by this token) — this is the AC3/anti-regression-critical branch protecting
  `test_world_emergence_populates_quest_registry`'s empty-`resource_nodes` case. If `matching` is
  non-empty and **every** matching node has `remaining_charges == 0`, return `False` (reject) for
  the whole opportunity. If any token triggers a rejection, the function returns `False`; otherwise,
  after scanning all tokens, return `True`.
- **Other writers to `state.resource_nodes` this check must not race with**: resource depletion is
  applied through the same tick's authoritative apply path (harvesting/ecology updates), never
  through a live mutable reference the check could observe mid-computation — the check reads only
  the immutable `state` snapshot passed into `WorldEmergencePhase.execute()`, identical isolation
  argument as Step 1.
**Do NOT touch:** `ScarcityModel.evaluate()` (`src/domains/world_emergence/models.py:238-278`) —
confirmed by investigation to compute scarcity from `WorldEventAggregate` counts, not live
`resource_nodes` state; it is not a reusable precedent and must not be refactored to share logic
with this new predicate.
**Verify:** `test_resource_availability_rejects_when_all_matching_nodes_depleted`,
`test_resource_availability_passes_when_any_matching_node_has_charges`,
`test_resource_availability_passes_when_no_matching_node_exists` (same new test file).

### Step 3 — Combinator + determinism/read-only/no-uuid guard
**Files:** `src/domains/world_emergence/quest_grammar.py` (same file)
**Change:** Add `validate_quest_opportunity(opportunity: QuestOpportunity, state:
AuthoritativeState) -> Optional[str]`: returns `"faction_zero_territory"` if
`check_faction_coherence(opportunity.faction_source, state)` is `False`; else returns
`"resource_depleted"` if `check_resource_availability(opportunity.objective_chain, state)` is
`False`; else returns `None` (admissible). Returning a short string code (rather than a boolean)
gives the phase.py call site (Step 4) a cheap, explicit rejection reason to feed into a metric
counter, satisfying the Anti-Drift Hazard "do not silently drop rejected opportunities without an
observable signal" without building a new `ValidationIssue`-style Pydantic class — that would be
disproportionate scope for a two-branch check. The function is a pure function of its two
arguments — no `uuid()`, no time/clock reads, no RNG — calling it twice with identical inputs is
guaranteed to return identical output by construction (no branch depends on anything but `state`
and `opportunity`'s own fields), and it never calls any method that could mutate `state` or
`opportunity` (both are read via attribute/dict access only, both `state`'s and `opportunity`'s
dataclasses are `frozen=True`, `quests.py:65-83` and confirmed `state.py` dataclasses use
`frozen=True, slots=True` throughout the fields this touches).
**Do NOT touch:** `QuestOpportunityGenerator.from_resource_depleted` /
`from_threat_signal` (`services.py:184-249`) — this combinator consumes their output, it does not
change how they build `QuestOpportunity` objects.
**Verify:** `test_preemit_validation_is_deterministic_and_read_only`,
`test_preemit_check_does_not_call_uuid_or_time_based_seeding` (same new test file).

### Step 4 — Wire the filter into `WorldEmergencePhase.execute()` step 5b
**Files:** `src/domains/world_emergence/phase.py`
**Change:** In step 5b (currently `phase.py:61-75`), after the existing loop builds `quest_opps`
(unchanged — this list still feeds `result.quest_opportunities` at line 94 and must remain
unfiltered), add a second pass that builds the filtered list consumed by `quest_registry_add`:
```python
admitted_quest_opps = []
rejected_count = 0
for opp in quest_opps:
    if quest_grammar.validate_quest_opportunity(opp, state) is None:
        admitted_quest_opps.append(opp)
    else:
        rejected_count += 1
```
Import `quest_grammar` from `src.domains.world_emergence`. Change line 134 from
`quest_registry_add=list(quest_opps)` to `quest_registry_add=list(admitted_quest_opps)`. Add
`metric_counters["quest_opportunities_rejected"] = rejected_count` alongside the existing
`metric_counters["world_emergence_ms"]` / `metric_counters["aggregates_generated"]` assignments
(`phase.py:126-127`) — same dict, same function, no cross-phase collision risk: this key is novel
to this phase, and `StateUpdate.merge()`'s additive-sum behavior for `metric_counters`
(`src/core/updates.py:1050-1052`) only matters across *different* `StateUpdate`s being merged (e.g.
multiple phases in one tick), which is the same pattern the two pre-existing counters already rely
on — introducing a third key changes nothing about that mechanism.
**Do NOT touch:** line 94 (`quest_opportunities=tuple(quest_opps)`) — confirmed by grep that
`result.quest_opportunities` is independently read and asserted by
`tests/unit/quest/test_quest_generation.py::test_world_emergence_phase_emits_quest_opportunities`
(`test_quest_generation.py:174-193`), which is not named in this ticket's scope or test_plan.md as
something to change; filtering line 94 would silently alter that field's contract, which is out of
scope.
**Verify:** `test_passing_opportunity_reaches_quest_registry_add_unfiltered`,
`test_rejected_opportunity_excluded_from_quest_registry_add` (new/extended in
`tests/unit/domains/world_emergence/test_phase8_world_emergence_boundary.py` or the new test file —
implementer's choice per test_plan.md), plus regression run of
`test_world_emergence_populates_quest_registry`,
`test_resource_crisis_quest_generated_on_depletion`,
`test_threat_response_quest_generated_on_high_severity`,
`test_world_emergence_phase_emits_quest_opportunities`, and the full
`tests/unit/domains/world_emergence/test_phase8_world_emergence_boundary.py` /
`tests/integration/domains/world_emergence/test_phase8_world_emergence_phase.py` suites.

### Step 5 — Docs and parity ledger update
**Files:** `docs/mechanics/06_worldbuilding_foundation.md`, `docs/parity_ledger/world_dynamics.yaml`
**Change:**
- In `06_worldbuilding_foundation.md`, add a new top-level section (`## 10. Runtime Pre-Emit
  Validation`, inserted after the existing `## 9. Content Catalog Database Structure` section and
  before `## 📜 Compliance Status`, per the file's confirmed heading structure) describing the
  faction-coherence and resource-availability checks as a distinct, per-tick runtime gate — sibling
  to, not an extension of, `## 7. Integrity Validation Laws & Severity Gates`'s build-time gate
  ladder and its `### Participant Reachability Rule (WORLD-REACH-001)` subsection
  (`06_worldbuilding_foundation.md:113`). State explicitly: (a) this gate runs inside
  `WorldEmergencePhase`, not the WorldSpec→Compile pipeline; (b) `faction_source=None` auto-passes
  faction-coherence (no claim to verify); (c) "no matching resource node found at all" is
  cannot-verify→pass, not depleted→reject; (d) this is a single-`faction_source` reinterpretation of
  the idea doc's original two-faction "tension" wording, and a depletion-state check rather than the
  idea doc's existence-at-authoring-time check — cite
  `docs/plans/idea_world_grammar_semantic_constraints.md` for context without editing it (out of
  scope per the predecessor ticket's own Out of Scope section).
- In `docs/parity_ledger/world_dynamics.yaml`, update entry `WORLD-102` (currently lines
  1094-1103): change `text` to state that `quest_registry_add` now only contains opportunities that
  pass `quest_grammar.validate_quest_opportunity()`, and update `v2_evidence` to cite
  `src/domains/world_emergence/phase.py` (updated step 5b) and
  `src/domains/world_emergence/quest_grammar.py` alongside the existing `apply.py` idempotent-add
  citation. Leave `status: verified`, `priority: P1`, and the existing `test_path` in place, and add
  the two new integration test names from Step 4 to `test_path` (comma-separated, matching this
  file's existing multi-test-path convention seen at, e.g., `WORLD-029`/`WORLD-060`).
**Do NOT touch:** `WORLD-098` (generation determinism), `WORLD-099` (id-formula determinism),
`WORLD-100`/`WORLD-101` (registry persistence/expiry) — confirmed unaffected by this ticket in
investigation.md's Parity Ledger Overlap section; do not edit their `v2_evidence` or `test_path`.
Do not edit `SUB-387` (the predecessor ticket's own new entry) or anything in
`docs/parity_ledger/substrate.yaml`.
**Verify:** No automated test; verified by manual review that the ledger's `v2_evidence` and the
Mechanics Bible section accurately describe the code landed in Steps 1-4 (Authoritative Mechanics
Rule "Parity" clause). Run `make knowledge-index-update` after these doc edits per CLAUDE.md's
"After Work" rule.

## Scope Guards

- Do not modify `src/worldbuilding/validator.py`, `WorldValidator`, `WorldValidationRule`, or
  `ValidationContext` — confirmed build-time/`WorldSpec`-only, explicitly out of scope.
- Do not modify `QuestOpportunityGenerator.from_resource_depleted`, `from_threat_signal`, or
  `from_entity_need` (`src/domains/world_emergence/services.py:166-259`) — the filter is a call-site
  addition in `phase.py`, not a change to generation.
- Do not filter or otherwise change `phase.py:94`'s `quest_opportunities=tuple(quest_opps)` —
  only `quest_registry_add` (line 134) is filtered.
- Do not use `RegionState.owner_faction_id` (`src/core/state.py:249`, legacy int enum) anywhere in
  the faction-coherence check.
- Do not look up `state.resource_nodes` by resource-type string as if it were a dict key — it is
  keyed by int `id`; matching requires scanning `.values()` by `yields_item`.
- Do not promote or edit `docs/plans/idea_world_grammar_semantic_constraints.md`.
- Do not edit `WORLD-098`, `WORLD-099`, `WORLD-100`, `WORLD-101`, or `SUB-387` parity entries.
- Do not run `pytest tests/` (full suite) — use the scoped commands in test_plan.md.
- Do not build a YAML-rule-loading mechanism or a `ValidationIssue`-style Pydantic class for
  rejections — a string-code return plus a `metric_counters` entry is the deliberately minimal,
  in-scope observability signal (see Step 3).

## Dependency Map

- Step 1 and Step 2 both add functions to the same new file
  (`src/domains/world_emergence/quest_grammar.py`) but are logically independent of each other —
  either can be implemented and tested first; the file simply accumulates both.
- Step 3 depends on Step 1 and Step 2 (the combinator calls both predicates).
- Step 4 depends on Step 3 (imports `validate_quest_opportunity`).
- Step 5 depends on Step 4 (the parity/doc text describes the landed call-site behavior and must
  match it exactly) and should be done last.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC1 — blocked/sequenced on reachability-validator ticket | Resolved in investigation.md (no implementation step; `is_reachable` reused in Step 1) | N/A — sequencing fact, not a runtime behavior |
| AC2 — faction-coherence rejection excluded from `quest_registry_add` | Step 1 (predicate), Step 4 (wiring) | `test_faction_coherence_rejects_zero_territory_faction`, `test_rejected_opportunity_excluded_from_quest_registry_add` |
| AC3 — resource-availability rejection excluded; passing opportunity byte-identical | Step 2 (predicate), Step 4 (wiring) | `test_resource_availability_rejects_when_all_matching_nodes_depleted`, `test_passing_opportunity_reaches_quest_registry_add_unfiltered`, `test_world_emergence_populates_quest_registry`, `test_resource_crisis_quest_generated_on_depletion`, `test_threat_response_quest_generated_on_high_severity` |
| AC4 — deterministic, read-only, no mutation | Step 3 | `test_preemit_validation_is_deterministic_and_read_only` |
| AC5 — `faction_source=None` defined behavior | Step 1 | `test_faction_coherence_passes_when_faction_source_is_none` |

## Anti-Drift Notes

- The single most likely silent-failure mode (per investigation.md Risks) is inverting the
  no-matching-node semantics — treating "no resource node found at all" as "depleted" instead of
  "cannot verify." Step 2's `check_resource_availability` must `continue` (not reject) when
  `matching` is empty; the AC3/anti-regression tests exist specifically to catch a regression here.
- `faction_source=None` is currently unreachable from both live generator methods
  (`from_resource_depleted`/`from_threat_signal` both hardcode it) — do not "fix" this as part of
  this ticket; that is out of scope, and `test_faction_coherence_passes_when_faction_source_is_none`
  exists precisely to lock in that both generators keep producing `faction_source=None` unmodified.
- The negative faction-coherence path (AC2) cannot be exercised through the real generator today —
  Step 1's test must construct a `QuestOpportunity` fixture directly with a non-`None`
  `faction_source`, not attempt to coax the live generator into producing one.
- `objective_chain` tokens have no schema — only two verb shapes exist in live code today (`fetch:`
  and `eliminate:`). Step 2's tolerant parse treats anything that isn't `fetch:<x>:<y>` as
  not-a-resource-claim (skip), not as a parse error to raise on.
- Keep the new module's two predicates and the combinator pure — no `state` mutation, no `uuid()`,
  no time/clock access — matching `QuestOpportunityGenerator`'s own documented contract
  (`services.py:170-172`) that this check sits downstream of in the same call chain.

## Deviations

None in implementation substance — Steps 1-5 were implemented exactly as specified (module
location, function names/signatures, combinator return contract, phase.py wiring, doc/parity
targets). Two environment-tooling steps outside the plan's own scope could not be completed and are
recorded here for traceability, not treated as silent skips: `graphify update .` timed out in this
worktree (no pre-built `graphify-out/graph.json` exists here — matching investigation.md's own
Context Scan note that this worktree has no built graph), and `make knowledge-index-update` could
not complete because `sentence-transformers` is not installed in this environment (same offline-index
gap investigation.md's Context Scan note already recorded for `search_docs`/`knowledge_search.py`).
Neither affects the correctness or traceability of the landed code/docs changes themselves.
