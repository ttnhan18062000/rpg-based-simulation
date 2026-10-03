---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260811-MEMORY-INFORMED-ROUTE-SCORING
artifact_type: plan
tags: [cognition, adventure]
---

# Implementation Plan — TCK-20260811-MEMORY-INFORMED-ROUTE-SCORING

## Summary

Add a single new additive/subtractive scoring term, `memory_adjustment`, to
`AdventureRouteScorer.score()` (`src/domains/adventure/scoring.py`) that reads
`entity.cognition.memory.causal.entries` (a `Tuple[CausalMemoryEntry, ...]`, confirmed at
`src/core/cognition.py:245-253`, reachable via `CognitionModel.memory: MemoryModel`
(`cognition.py:341-348`) → `MemoryModel.causal: CausalMemory` (`cognition.py:344`)) and
applies a fixed ±1.0 magnitude to exactly two, deliberately narrow, advice→family mappings:
`"avoid_enemy"` (from a `combat_loss` entry) suppresses `RouteFamily.HUNT_WEAK_ENEMY`, and
`"boost_party_trust"` (from a `party_abandoned` entry) promotes `RouteFamily.FORM_PARTY`. No
other advice string is mapped in this pass (see Design Decisions below). The read is boolean-gated
per matching advice string (not accumulated per entry), so multiple matching `CausalMemoryEntry`
records produce the same single ±1.0 adjustment as one matching record — this keeps the term
bounded regardless of how many of the causal-memory buffer's up-to-30 entries match. No plumbing
changes are needed through `AdventureGoalScorer`/`AdventureDecisionService.decide()` — confirmed by
direct read of `src/ai/goals/adventure_scorer.py` and `src/domains/adventure/service.py:73-78`:
`entity` is already the first positional argument threaded all the way to `AdventureRouteScorer.
score()`, so `entity.cognition.memory.causal.entries` is reachable with zero new call-chain wiring.
`AdventureRouteGenerator.generate()` (`src/domains/adventure/generator.py:24-181`, confirmed
directly) is unchanged — this ticket is scoring-side only, per its own Scope section.

This plan explicitly does **not** wire `MemoryUpdatePhase` (`src/domains/memory/phase.py:24-100`)
into `src/engine/pipeline.py`. A repo-wide grep of `src/` confirms zero call sites of
`MemoryUpdatePhase` outside its own file — it is unreachable from any live tick today, and remains
so after this plan. This means the new scoring term is real, live-reachable code (any future caller
of `MemoryUpdatePhase` benefits immediately, with no further scoring-side work) but is exercised
only by unit tests with manually-constructed `CausalMemoryEntry` fixtures until a separate ticket
wires the phase into the pipeline — see Scope Guards.

## Design Decisions

### 1. Advice → RouteFamily mapping (deliberately narrow, 2 of 10 possible advice strings)

| `event_kind` | `future_advice` value | Mapped `RouteFamily` | Direction | Rationale |
|---|---|---|---|---|
| `combat_loss` (fallback branch — fires only when `hp_pct >= 0.3`, `stamina >= 20`, `weapon_dur >= 0.2`; confirmed `src/domains/memory/attribution.py:37-52`) | `"avoid_enemy"` | `HUNT_WEAK_ENEMY` | **suppress** (−1.0) | Literal semantic match: "avoid X" directly names the family it counsels against. `HUNT_WEAK_ENEMY` is the only combat-seeking family in the 16-value enum (`src/domains/adventure/schema.py:16-33`, confirmed 16 values, not the stale 13 in `adventure_contract.md`). Confirmed **dead code**: `AdventureRouteGenerator.generate()` (`generator.py:24-181`) has zero `RouteFamily.HUNT_WEAK_ENEMY` emission sites (its `kind_map` at generator.py:38-45 and every `opts.append(...)` call site checked directly) — this suppression is unit-testable via `AdventureRouteScorer.score()` called directly with a manually-built `AdventureRouteOption(family=HUNT_WEAK_ENEMY, ...)`, but has **zero observable effect via a live `generate()` → `score()` call chain** today. This must be stated in the new unit test and in the mechanics-doc update, not silently glossed over. |
| `party_abandoned` (unconditional, always paired with `"realign_directive"`; confirmed `attribution.py:65-67`) | `"boost_party_trust"` | `FORM_PARTY` | **promote** (+1.0) | Literal semantic match: "boost X" is an action directive to increase/pursue X, not avoid it — the entity's own advice to itself is to work on party trust, which is achieved by continuing to engage with `FORM_PARTY` (recruit/join), not by suppressing it. `FORM_PARTY` **is** live-generated (`generator.py:125-163`, gated on `sociability >= 0.2` and available allied candidates), so this mapping is both unit- and (once `MemoryUpdatePhase` is eventually wired) live-observable. |

**Deliberately left unmapped in this pass** (all confirmed real, reachable advice strings from
`attribution.py:29-67`, all real per investigation.md's Risk #1):
- `"heal_first"` / `"rest_often"` / `"repair_weapon"` (`combat_loss`, non-fallback branches,
  attribution.py:37-48) — plausible target `RECOVER`, but not named in the ticket's own AC1
  examples, and three advice strings would need a decision about whether they combine or compete
  for one adjustment — deferred, not decided here, to avoid scope creep beyond AC1's stated set.
- `"seek_trusted_guide"` / `"verify_intel"` (`failed_search`, attribution.py:57-59) — ambiguous
  between `ASK_INFORMATION` and `SCOUT_LOCATION` (investigation.md Risk #1); no unambiguous
  single-family read exists without a product decision.
- `"acquire_mats"` / `"train_blacksmith"` (`failed_craft`, attribution.py:61-63) — two advice
  strings from one entry would map to two different families (`GATHER_RESOURCE`/`CRAFT_UPGRADE`
  and `TRAIN_SKILL` respectively) — a two-family fan-out is a materially different design shape
  than the two mappings chosen above and is deferred.
- `"realign_directive"` (`party_abandoned`, attribution.py:67) — maps to no existing `RouteFamily`
  at all; there is no route family for "reconsider my strategic directive."

**Rationale for scoping to exactly 2 of 8**: the ticket's AC1 text itself names exactly these two
advice strings as its own examples (`avoid_enemy` after `combat_loss`, `boost_party_trust` after
`party_abandoned`) and its own Scope section commits only to "a route family" (singular) being
measurably affected. Per CLAUDE.md's Hard Rule ("Do not guess when uncertainty affects behavior or
architecture") and the Planning Rule against planning more work than ticket scope, the six
unmapped advice strings above are left as an explicit gap for a future ticket to design
deliberately (with product/design input on which of several plausible family targets is correct),
not guessed at here.

### 2. Formula placement and magnitude

`AdventureRouteScorer.score()`'s current formula (confirmed `scoring.py:232`):
```
final_score = urgency + benefit + personality_bias + plan_advance_bonus + confidence_bonus - risk_penalty - blocker_penalty
```
This plan adds `memory_adjustment` as a new additive term (positive or negative), inserted
immediately after the existing `plan_advance_bonus` step (`scoring.py:212-221`) as new step 4c,
following the same "flat, capped, entity/route-matched" shape as `plan_advance_bonus` (flat +1.5,
capped at 3.0) rather than a multiplier (unlike the `benefit`/`GATHER_RESOURCE` depletion-fraction
precedent) — a flat term is the right shape here because, like `plan_advance_bonus`, this term
either fires (single fixed magnitude) or does not; there is no continuous quantity to scale by.

**Magnitude: ±1.0**, chosen relative to existing constants confirmed in `scoring.py`: below
`blocker_penalty` (2.0, scoring.py:229) so a blocked route is never rescued by a favorable memory
adjustment; above `confidence_bonus` (max 0.15, scoring.py:224) and `personality_bias` (max 0.50,
scoring.py:200-210) so the effect is unambiguously "measurable" per AC1, comparable in order of
magnitude to `plan_advance_bonus` (flat 1.5, scoring.py:220). This constant is **undertuned** —
no live-run measurement is possible before `MemoryUpdatePhase` is wired into the pipeline (see
Scope Guards) — the same honest disclosure pattern the mechanics doc already uses for
`blocker_penalty` (`docs/mechanics/04_strategic_cognition.md` §6.5: "cannot be empirically refined
until world content provides non-DEFER route candidates"). Symmetric magnitude (not asymmetric
suppress-vs-promote weighting) is chosen because there is no empirical basis yet to justify
asymmetry.

New formula:
```
final_score = urgency + benefit + personality_bias + plan_advance_bonus + memory_adjustment + confidence_bonus - risk_penalty - blocker_penalty
```

### 3. AC3 reinterpretation (explicit, not silent)

AC3 as literally written ("STRAT-227 parity entry gains a test_path (currently null)") is
**unsatisfiable**: `docs/parity_ledger/strategic_cognition.yaml:2529-2531` confirms STRAT-227
already has a non-null `test_path` (`tests/unit/domains/adventure/test_phase3_route_scoring.py;
tests/unit/domains/adventure/test_depletion_scoring.py`), added in the same commit that created
the entry — there is no null state to fill. **Reinterpretation**: this plan satisfies AC3's
evident intent — extending STRAT-227's existing evidence to also describe and test-cover the new
memory-informed term — by appending the new test file to `test_path` and extending `text`/
`v2_evidence` with the new term's constants (Step 5 below). This is a reinterpretation of a stale
AC, not a literal fulfillment, and is called out here so Review does not mistake it for either
"AC ignored" or "AC's literal premise silently patched to look satisfied."

### 4. `self_model` vs `cognition` docstring wording

`scoring.py:6-7`'s module docstring ("Reads only subjective self-model aspects to protect
information opacity") predates the `self_model`/`cognition` field split (`EntityState.self_model:
SelfModelBundle` at `src/core/state.py:689`, `EntityState.cognition: CognitionModel` at
`state.py:690` — two distinct fields). This plan updates the docstring (Step 2) so it does not read
as a literal, narrower promise than what the code will now do (reading `entity.cognition.memory`
is a new fact this ticket introduces) while preserving its actual meaning: "reads only the
entity's own subjective interior state, never omniscient world truth."

## Steps

### Step 1 — Add `memory_adjustment` field to `AdventureRouteOption`
**Files:** `src/domains/adventure/schema.py`

**Change:** Add `memory_adjustment: float = 0.0` to the `AdventureRouteOption` frozen dataclass
(`schema.py:36-72`), placed alongside the existing "Intermediate scoring terms populated by
AdventureRouteScorer (zero before scoring)" block (`schema.py:65-72`, which already lists
`urgency`, `benefit_score`, `personality_bias`, `confidence_bonus`, `risk_penalty`,
`blocker_penalty`, `plan_advance_bonus` — all defaulted to `0.0`, all keyword-only in practice).
Add it as the last field in that block, immediately after `plan_advance_bonus`.

**Other writers to this dataclass** (enumerated, since `AdventureRouteOption` is a shared schema
type): 7 direct construction call sites confirmed via repo-wide grep — 5 in
`src/domains/adventure/generator.py` (lines 80, 101, 115, 150, 168) and 2 in
`src/domains/adventure/service.py` (lines 54, 108) — all use keyword-argument construction and
never pass any of the 7 existing "intermediate scoring term" fields, so all 7 will implicitly
default the new `memory_adjustment` field to `0.0` with zero code change required at those sites.
The single `dataclasses.replace(route, ...)` call in `scoring.py:269-279` is the only site that
sets these intermediate fields today, and Step 2 adds `memory_adjustment=...` to that same call —
no other file constructs or replaces this dataclass with these fields set.

**Do NOT touch:** `RejectedRoute`, `AdventureDecisionResult` (schema.py:75-99) — unrelated
dataclasses in the same file, not part of this ticket's scope.

**Verify:** No dedicated test for the field addition alone; covered implicitly by every test in
Step 3 that inspects `result.memory_adjustment`, plus the full existing regression suite
(`tests/unit/domains/adventure/` — see Regression Surface in test_plan.md) must stay green, proving
the new defaulted field does not break any existing `AdventureRouteOption(...)` construction.

---

### Step 2 — Implement the memory-informed adjustment in `AdventureRouteScorer.score()`
**Files:** `src/domains/adventure/scoring.py`

**Change:**
1. Update the module docstring (`scoring.py:6-7`) from "Reads only subjective self-model aspects
   to protect information opacity" to "Reads only subjective self-model and cognition/memory
   aspects — the entity's own beliefs, never omniscient world truth — to protect information
   opacity." (Design Decision 4.)
2. Insert a new step "4c. Memory-Informed Advice Adjustment" immediately after the existing
   "4b. Plan-Advance Bonus" block (`scoring.py:212-221`), before "5. Confidence Bonus"
   (`scoring.py:223`):
   ```python
   # ── 4c. Memory-Informed Advice Adjustment (TCK-20260811-MEMORY-INFORMED-ROUTE-SCORING) ──
   # Reads only the entity's own subjective causal-memory beliefs (never state/world truth).
   # Fixed ±1.0 magnitude, boolean-gated per advice string (not accumulated per matching
   # entry) so a full 30-entry causal-memory buffer with many matching entries still produces
   # exactly one adjustment per mapped family, never a growing stack.
   memory_adjustment = 0.0
   causal_entries = entity.cognition.memory.causal.entries
   if causal_entries:
       has_avoid_enemy = any(
           "avoid_enemy" in e.future_advice for e in causal_entries
       )
       has_boost_party_trust = any(
           "boost_party_trust" in e.future_advice for e in causal_entries
       )
       if has_avoid_enemy and route.family == RouteFamily.HUNT_WEAK_ENEMY:
           memory_adjustment -= 1.0
       if has_boost_party_trust and route.family == RouteFamily.FORM_PARTY:
           memory_adjustment += 1.0
   ```
   `entity.cognition.memory.causal.entries` is confirmed to exist at this exact path:
   `EntityState.cognition: CognitionModel` (`src/core/state.py:690`) →
   `CognitionModel.memory: MemoryModel` (field confirmed directly at `src/core/cognition.py:549`,
   `class CognitionModel` body) → `MemoryModel.causal: CausalMemory` (`cognition.py:344`) →
   `CausalMemory.entries: Tuple[CausalMemoryEntry, ...]` (`cognition.py:259`). `CausalMemoryEntry.
   future_advice: Tuple[str, ...]` (`cognition.py:251`) — the `in` membership test against a tuple
   correctly handles both 1-element (`combat_loss` fallback) and 2-element
   (`failed_search`/`failed_craft`/`party_abandoned`) tuples with no truncation.
3. Update the final-score formula (`scoring.py:232`) to include the new term:
   ```python
   final_score = urgency + benefit + personality_bias + plan_advance_bonus + memory_adjustment + confidence_bonus - risk_penalty - blocker_penalty
   ```
4. Update the `dataclasses.replace(...)` call (`scoring.py:269-279`) to also set
   `memory_adjustment=round(memory_adjustment, 4)`.
5. Update the module-level docstring's `Formula:` block (`scoring.py:44-46`). **Correction (Review
   round 1)**: this block currently reads `score = urgency + benefit + personality_bias +
   confidence_bonus - risk_penalty - blocker_penalty` — it is already missing `plan_advance_bonus`
   (a pre-existing gap from `TCK-20260619-E61C-PLAN-SCORER`, not introduced by this ticket). There is
   no "existing pattern already used for `plan_advance_bonus`" to match, since it was never added
   here. While editing this exact string for `memory_adjustment`, also add `plan_advance_bonus` in
   the same edit (cheap, closes the pre-existing gap rather than perpetuating it under a
   now-updated-looking docstring): `score = urgency + benefit + personality_bias + plan_advance_bonus
   + memory_adjustment + confidence_bonus - risk_penalty - blocker_penalty`.

**Do NOT touch:** the `get_trait` closure (scoring.py:53-89), needs/urgency block (scoring.py:98-
140), faction-directive block (scoring.py:121-140), benefit/depletion/quest-capability blocks
(scoring.py:142-191), risk_multiplier/risk_penalty (scoring.py:189-191), personality_bias block
(scoring.py:193-210), confidence_bonus (scoring.py:223-224), blocker_penalty (scoring.py:226-229),
class-synergy multipliers (scoring.py:235-254), escort scoring (scoring.py:256-267) — none of
these are affected by or need to reference the new term. Do not add a `state`-derived parameter to
`score()`'s signature — the memory read stays entity-local, consistent with the "reads only
subjective... aspects" boundary (investigation.md Anti-Drift Hazards).

**Other writers / call-chain interaction:** `AdventureRouteScorer.score()` is called from exactly
one live production call site — `AdventureDecisionService.decide()` (`src/domains/adventure/
service.py:73-78`), itself called once per tick per entity from `AdventureGoalScorer.score()`
(`src/ai/goals/adventure_scorer.py:74`). Neither of these callers is modified by this step; both
pass `entity` positionally/by-keyword unchanged, so the new memory read requires no change to
either caller. `entity.cognition.memory` is never mutated by `score()` (confirmed: `score()` reads
`entity.*` attributes only, and its only `dataclasses.replace` call targets the local `route`
argument, never `entity`) — the only writer to `entity.cognition.memory` anywhere in the repo is
`MemoryUpdatePhase.run()` (`src/domains/memory/phase.py:92-96`), which is unreachable from any live
tick (confirmed zero call sites outside its own file) and is not modified by this ticket.

**Verify:** `tests/unit/domains/adventure/test_memory_informed_scoring.py` (Step 3, all 7 tests),
plus full existing `tests/unit/domains/adventure/` regression suite unchanged (specifically
`test_phase3_route_scoring.py`, `test_depletion_scoring.py`, `test_scoring_plan_bonus.py`,
`test_hero_quest_scoring.py` — none of these construct an entity with non-empty `cognition.memory.
causal.entries`, so `memory_adjustment` must be `0.0` for all of them, a strict no-op).

---

### Step 3 — Add new test file
**Files:** `tests/unit/domains/adventure/test_memory_informed_scoring.py` (new file)

**Change:** Implement the 7 tests specified in `test_plan.md`'s "New Tests Required" section,
scoped exactly to the 2-mapping design decided above (no test for the 8 deliberately-unmapped
advice strings):

1. `test_avoid_enemy_advice_suppresses_hunt_weak_enemy_score` — entity with
   `CausalMemoryEntry(event_id="e1", event_kind="combat_loss", interpreted_causes=("strong_enemy",),
   confidence=0.8, future_advice=("avoid_enemy",), tick=1)` in `cognition.memory.causal.entries`
   scores a `HUNT_WEAK_ENEMY` route strictly lower than an otherwise-identical entity with empty
   `cognition.memory.causal.entries`. Include an explicit comment/assertion referencing
   `docs/simulation/domains/adventure_contract.md`'s documented dead-code note for
   `HUNT_WEAK_ENEMY`, so a future reader is not misled into thinking this is observable via a live
   `generate()` → `score()` chain today.
2. `test_boost_party_trust_advice_promotes_form_party_score` — entity with
   `CausalMemoryEntry(event_id="e2", event_kind="party_abandoned",
   interpreted_causes=("grudge_decay", "cohesion_lost"), confidence=0.8,
   future_advice=("boost_party_trust", "realign_directive"), tick=1)` scores `FORM_PARTY` strictly
   *higher* than an entity with no matching entry (promote direction, per Design Decision 1).
3. `test_no_matching_causal_memory_is_a_no_op` — entity with a non-empty `cognition.memory.causal.
   entries` whose `future_advice` values (e.g. `("heal_first",)` from a `combat_loss` non-fallback
   entry) do not match either of the 2 mapped advice strings produces an identical score to an
   entity with fully empty `cognition.memory` for the *same* route family under test.
4. `test_future_advice_tuple_with_multiple_values_handled` — a `CausalMemoryEntry` with a 2-element
   `future_advice` tuple (e.g. `("boost_party_trust", "realign_directive")`) correctly triggers the
   `FORM_PARTY` promotion via membership on the full tuple, not `future_advice[0]` truncation.
5. `test_memory_term_does_not_mutate_entity_cognition` — build entity, capture
   `entity_before = entity.cognition`, call `AdventureRouteScorer.score(entity, route)`, assert
   `entity.cognition is entity_before` (identity check on the frozen dataclass) — proves no
   mutation occurred.
6. `test_memory_term_reads_only_entity_local_state` — call `AdventureRouteScorer.score(entity,
   route)` with no `state`-derived argument involved in the memory term's computation (this is a
   signature/behavior check, not a new kwarg — `score()`'s signature already has no `state`
   parameter; confirm the memory term's logic added in Step 2 references only `entity`, not any of
   `resource_nodes`/`quest_registry`/`group`/`faction_directives`/`factions`/`progression_plan`).
7. `test_capacity_evicted_causal_entries_do_not_affect_scoring` — build a `CausalMemory` with
   `entries` that does **not** contain a matching advice-bearing entry (simulating post-eviction
   state) and assert no adjustment fires — documents that `score()` is stateless per call and only
   ever sees what is passed on `entity.cognition.memory.causal.entries`, with no independent
   history lookup.

Use the `V2EntityBuilder` + `.replace_cognition(CognitionModel(memory=MemoryModel(causal=
CausalMemory(entries=(...,)))))` pattern — confirmed available: `V2EntityBuilder.replace_cognition`
exists at `src/core/builder.py:128`, and the `_build_entity`/`_route` helper pattern already used
in `tests/unit/domains/adventure/test_scoring_plan_bonus.py:20-35` is directly reusable (same
`V2EntityBuilder(1)` → `.replace_combat(...)` → `.replace_biological(...)` → `.identity(...)` →
`.replace_self_model(...)` → `.build()` chain, plus a new `.replace_cognition(...)` call).

**Do NOT touch:** any existing test file. This is a new file only.

**Verify:** `pytest tests/unit/domains/adventure/test_memory_informed_scoring.py -v` — all 7 pass.

---

### Step 4 — Mechanics Bible update
**Files:** `docs/mechanics/04_strategic_cognition.md`

**Change:** Add a new `### 6.11 Memory-Informed Advice Adjustment` subsection (numbering confirmed
by reading the file's existing headers: `6.1`–`6.5`, `6.7`, `6.6`, `6.8`, `6.9`, `6.10` already
exist out of document order but are all present — `6.11` is the next free number), placed after the
existing `### 6.10 Faction Directive Urgency Scoring (E53Ac)` section. Content: state the exact
formula placement (`final_score` now includes `+ memory_adjustment`), the 2-row mapping table from
Design Decision 1 above (advice string → family → direction → magnitude), the ±1.0 magnitude and
its undertuned-constant disclosure (mirroring §6.5's blocker_penalty disclosure pattern), and an
explicit "Not yet live" callout: *"This term is real, reachable code in
`AdventureRouteScorer.score()`, but `CausalMemoryEntry` records are never created in a live
simulation run today — `MemoryUpdatePhase` (`src/domains/memory/phase.py`), the only code that
populates `entity.cognition.memory.causal.entries`, has zero call sites in `src/engine/pipeline.py`
or anywhere else outside its own file and tests. This term is exercised only by unit tests with
manually-constructed `CausalMemoryEntry` fixtures until a separate ticket wires `MemoryUpdatePhase`
into the live pipeline."* Also update §6.2's `Formula Term Constants` table. **Correction (Review
round 1)**: this table currently lists only 6 rows and is already missing `plan_advance_bonus` (same
pre-existing `TCK-20260619-E61C-PLAN-SCORER` gap as Step 2's docstring fix above) — not 6 complete,
current rows to add alongside. While editing this table for `memory_adjustment`, also add the
missing `plan_advance_bonus` row in the same edit, so the table ends up with 8 rows matching the
real current formula, not 7.

**Do NOT touch:** §6.1–§6.10's existing content, the Risk Multiplier calibration history
(§6.3), the Personality Bias table (§6.4), or any of the combat-bravery/ActionStyle historical
notes embedded in §6.3 — all unrelated to this change.

**Verify:** No automated test for doc content; manual proofread that the new section's formula and
constants match `scoring.py` exactly post-Step-2.

---

### Step 5 — Parity ledger update (STRAT-227)
**Files:** `docs/parity_ledger/strategic_cognition.yaml`

**Change:** Extend the existing STRAT-227 entry (`strategic_cognition.yaml:2507-2531`) — do not
create a new sibling entry, since this is the same `AdventureRouteScorer.score()` formula STRAT-227
already documents, just gaining one more term:
- `text`: append a clause describing the new memory_adjustment term and its exact mapping/magnitude
  (mirroring the existing entry's style, e.g. "...; memory_adjustment = ±1.0 when a matching
  CausalMemoryEntry.future_advice is present (avoid_enemy → HUNT_WEAK_ENEMY suppress,
  boost_party_trust → FORM_PARTY promote), all constants documented in
  docs/mechanics/04_strategic_cognition.md §6.11.").
- `v2_evidence`: append a clause citing `TCK-20260811-MEMORY-INFORMED-ROUTE-SCORING` and the new
  test file.
- `test_path`: append `; tests/unit/domains/adventure/test_memory_informed_scoring.py` to the
  existing string (`tests/unit/domains/adventure/test_phase3_route_scoring.py;
  tests/unit/domains/adventure/test_depletion_scoring.py`), per the AC3 reinterpretation (Design
  Decision 3).
- `status`: remains `verified` (both the pre-existing formula terms and the new term are code-
  verified by passing tests).
- Leave `priority: P1`, `legacy_evidence: null`, `proof_type: parity`, `divergence_note: null`
  unchanged.

**Other writers to this file/entry:** confirmed via grep that 3 other parity ledger files
(`social_narrative.yaml:2442,2472`, `progression.yaml:1180`, `infrastructure.yaml:4117`) reference
`src/domains/adventure/scoring.py` but cite *different* sections of that file (§9 escort block,
§4b plan_advance_bonus, and route-scoring test evidence respectively) — none of those entries
describe the formula terms STRAT-227 covers or the new memory term, so they require no change and
are not touched by this step. No other parity ledger entry currently covers memory-informed scoring
(confirmed by investigation.md).

**Do NOT touch:** any other entry in `strategic_cognition.yaml`, or any entry in the 3 other files
listed above.

**Verify:** After Step 3 passes, confirm the appended `test_path` file exists and its tests pass —
this is the P1 parity-ledger requirement (per CLAUDE.md's Authoritative Mechanics Rule, "P0 entries
require a passing test_path" — STRAT-227 is P1, but the same evidentiary standard applies).

---

### Step 6 — `memory_contract.md` staleness correction
**Files:** `docs/simulation/domains/memory_contract.md`

**Change:** Correct the "Domain Interactions" table's "Adventure domain" row (`memory_contract.md`
line ~173, confirmed present-tense claim: "Causal lessons in `CausalMemoryEntry` feed adventure
route scoring — advice from past failures... influences route selection.") to accurately state
**both halves**:
> "As of `TCK-20260811-MEMORY-INFORMED-ROUTE-SCORING`, `AdventureRouteScorer.score()`
> (`src/domains/adventure/scoring.py`) reads `entity.cognition.memory.causal.entries` for exactly 2
> of the 10 possible `future_advice` values (`avoid_enemy` → suppress `HUNT_WEAK_ENEMY`,
> `boost_party_trust` → promote `FORM_PARTY`) — the scoring-side wiring is real code. However, this
> is not yet observable in any live run: `MemoryUpdatePhase`, the only code that ever populates
> `CausalMemoryEntry` records, has zero call sites in `src/engine/pipeline.py` (confirmed
> repo-wide). Spatial danger flags remain unaffected by adventure scoring (unchanged from prior
> text)."

Also correct the pre-existing field-name inaccuracy noticed while reading this doc during
planning: the "What It May Mutate" table (memory_contract.md, "What It May Mutate" section) names
the mutated fields as `entity.cognition.causal_memory` / `entity.cognition.spatial_memory`, but the
real path (confirmed `src/core/cognition.py:341-348`) is `entity.cognition.memory.causal` /
`entity.cognition.memory.spatial` (an intermediate `memory: MemoryModel` field, not a flattened
`causal_memory`/`spatial_memory` name). This is a **pre-existing inaccuracy not caused by this
ticket** — flag and correct it in the same pass since Step 6 is already touching this table, but do
not expand this into a broader doc audit.

**Do NOT touch:** the "Engine Phase", "What It Owns", "What It Must NOT Mutate", "Test Protection"
sections, or any other Domain Interactions row (Motivation, Cognition layer, Cooperation,
Perception) — all accurate and unrelated to this change.

**Verify:** No automated test; manual proofread against `scoring.py` (post-Step-2) and
`phase.py`/`pipeline.py` (confirmed unchanged) for accuracy.

---

### Step 7 — `adventure_contract.md` update
**Files:** `docs/simulation/domains/adventure_contract.md`

**Change:**
1. "What It Reads" table (adventure_contract.md:61-83): add a new row —
   `entity.cognition.memory.causal.entries` | `future_advice` values for 2 mapped advice strings
   (`avoid_enemy`, `boost_party_trust`) suppress/promote `HUNT_WEAK_ENEMY`/`FORM_PARTY` — see
   `docs/mechanics/04_strategic_cognition.md` §6.11.
2. The "Scoring — AdventureRouteScorer / AdventureDecisionService" formula table (confirmed at
   adventure_contract.md, the section beginning "**Formula:**"): add a `memory_adjustment` row to
   the term table, matching how `plan_advance_bonus`-equivalent terms are documented there (note:
   this doc's own formula table is already stale relative to `scoring.py` — e.g. it's missing
   `plan_advance_bonus` and lists personality-bias weights as uniform 0.25 pre-E11C — **do not**
   attempt to fix those pre-existing staleness issues here; add only the new `memory_adjustment`
   row and leave the rest as-is, since a full resync of this table is out of this ticket's scope).

**Do NOT touch:** the "Full `RouteFamily` enum (13 values)" table's pre-existing 13-vs-16 drift
(missing `QUEST_OPPORTUNITY`, `PROTECT_TARGET`, `OWN_SURVIVAL` — confirmed pre-existing, unrelated
to this ticket per investigation.md Risk #5) — do not fix this table's count or missing rows as
part of this ticket.

**Verify:** No automated test; manual proofread.

---

### Step 8 — Architecture design doc update
**Files:** `docs/architecture/2026-08-11-adventure-as-cognition-strategy-subcomponent-design.md`

**Change:** Update the "Memory-informed candidates" bullet (confirmed at lines ~415-418, under
"Deepening adventure's own reasoning") from an open Future Extension Pattern citing the vendor-
cheating example to reflect that a **scoped version** of this pattern is now closed:
> "**Memory-informed candidates** (closed, scoped, `TCK-20260811-MEMORY-INFORMED-ROUTE-SCORING`):
> `AdventureRouteScorer.score()` now reads `entity.cognition.memory.causal.entries` for 2 of the 4
> supported `event_kind`s' advice values (`avoid_enemy` → suppress `HUNT_WEAK_ENEMY`,
> `boost_party_trust` → promote `FORM_PARTY`). The original vendor-cheating example (an entity
> suppressing `BUY_UPGRADE` at a vendor who previously cheated it) remains explicitly unbuildable —
> `CausalAttributionService.attribute()` has no vendor/trade/cheating `event_kind`, and `buy_item`
> opportunities key to a shop/structure id, not an NPC vendor entity id. Also not yet live in any
> running simulation: `MemoryUpdatePhase` is unreachable from the pipeline (see
> `memory_contract.md`)."

**Do NOT touch:** the "Capability-estimate-driven confidence" or "Relationship-aware `FORM_PARTY`"
bullets in the same list (separate, already-ticketed concerns per the ticket's own Related
Tickets/Out-of-Scope), or the "Multi-step planning" bullet, or any other section of this design
doc.

**Verify:** No automated test; manual proofread.

## Scope Guards

- **Do not wire `MemoryUpdatePhase` into `src/engine/pipeline.py`.** Confirmed zero call sites of
  `MemoryUpdatePhase` anywhere in `src/` outside `src/domains/memory/phase.py` itself. Doing so
  would require: (a) registering a new phase in the pipeline (a `run_phase(...)` call alongside
  the ~20 already-registered phases confirmed in `pipeline.py`), (b) deciding tick cadence/ordering
  for that registration (an architecture-review-worthy decision this ticket's Scope section does
  not authorize), and (c) building a real `trigger_event` producer wired to combat/search/craft/
  party-abandonment outcomes (`trigger_event` also has zero live producers today — confirmed only
  constructed inline in `MemoryUpdatePhase`'s own tests). This is a materially larger, structurally
  different change than this ticket's own Scope/Related Code Areas describe. **Recommendation**:
  file a follow-up ticket (e.g. `TCK-YYYYMMDD-MEMORY-UPDATE-PHASE-PIPELINE-WIRING`) scoped to (a)
  pipeline registration + cadence decision and (b) a real `trigger_event` producer, mirroring how
  `TCK-20260811-SOCIAL-CONTRACT-GOAL-SCORER` filed
  `TCK-20260811-SIMQ-COGNITION-BAND-CROSSING-DA-AND-LIFECYCLE-ANCHOR-GAP` for an analogous
  out-of-scope gap it found.
- **Do not touch `AdventureGoalScorer`, `AdventureDecisionService.decide()`, or
  `RouteToProjectMapper`.** `entity` already flows to `AdventureRouteScorer.score()` unchanged;
  no new parameter or plumbing is needed (confirmed by direct reads of `adventure_scorer.py` and
  `service.py:73-78`).
- **Do not attempt the vendor-cheating example.** `CausalAttributionService.attribute()`
  (`attribution.py:15-77`) has no vendor/trade/cheating `event_kind`; `buy_item` opportunities key
  to a shop/structure id, not an NPC entity id — confirmed unchanged. Explicitly out of scope per
  the ticket's own Out of Scope section (AC2).
- **Do not map any of the 8 deliberately-unmapped advice strings** (`heal_first`, `rest_often`,
  `repair_weapon`, `seek_trusted_guide`, `verify_intel`, `acquire_mats`, `train_blacksmith`,
  `realign_directive`) — 10 total minus the 2 mapped = 8 remaining, listed here for completeness. See
  Design Decision 1 for the full rationale per string. A future ticket should decide these with
  product/design input, not this one.
- **Do not fix the pre-existing 13-vs-16 `RouteFamily` doc/code drift** in `adventure_contract.md`
  (missing `QUEST_OPPORTUNITY`, `PROTECT_TARGET`, `OWN_SURVIVAL`) — unrelated pre-existing gap.
- **Do not resync `adventure_contract.md`'s entire formula table** (it is already stale re:
  `plan_advance_bonus` and personality-bias weights pre-E11C) beyond adding the one new
  `memory_adjustment` row — a full resync is out of scope.
- **Do not add time-decay/recency weighting** to the memory read — any matching entry, regardless
  of `tick` age, triggers the adjustment. No recency requirement exists in the ticket's AC or Scope.
- **Do not mutate `entity.cognition.memory` from `AdventureRouteScorer.score()`** — it must remain
  fully read-only, consistent with the existing contract and the only-legitimate-mutator being
  `MemoryUpdatePhase` (which this ticket does not touch).
- **Do not silently "fix" AC3** by editing STRAT-227 to make done-checker pass without disclosing
  the stale-premise finding — Step 5 explicitly reinterprets AC3 per Design Decision 3, disclosed
  here and in the AC map below, not silently substituted.

## Dependency Map

- Step 1 (schema field) must land before Step 2 (scoring logic references the new field in its
  `dataclasses.replace(...)` call) and before Step 3 (tests assert on `result.memory_adjustment`).
- Step 2 must land before Step 3 (tests exercise the new scoring logic) and before Step 5 (parity
  ledger cites the implemented constants).
- Steps 4, 6, 7, 8 (doc updates) are independent of each other and can land in any order, but all
  should land after Step 2 is finalized (they describe the exact implemented formula/constants) and
  ideally in the same session per CLAUDE.md's Parity rule ("If logic changes, update the
  corresponding doc AND the parity ledger entry in the same session").
- Step 5 depends on Step 3 (test file must exist and pass before being cited in `test_path`).
- All steps are otherwise independent — no step requires a different step to be re-done if it
  changes.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC1: "A route family whose `CausalMemoryEntry.future_advice` already exists (e.g. `avoid_enemy` after `combat_loss`, `boost_party_trust` after `party_abandoned`) measurably suppresses/promotes the matching route family's score/benefit vs. an entity with no matching causal memory" | Step 1 (field), Step 2 (scoring logic, Design Decision 1 mapping) | Step 3 tests 1, 2, 3 (`test_avoid_enemy_advice_suppresses_hunt_weak_enemy_score`, `test_boost_party_trust_advice_promotes_form_party_score`, `test_no_matching_causal_memory_is_a_no_op`) |
| AC2: "The vendor-cheating example is explicitly NOT scoped as a buildable AC for this ticket" | Already satisfied by the ticket document's own Out of Scope section (item 1); reinforced by Step 8's design-doc update, which restates the vendor example's unbuildability in the doc that originally proposed it. No code step implements or attempts the vendor example. | N/A (documentation-only AC; no test required) |
| AC3 (reinterpreted, see Design Decision 3): STRAT-227 parity entry extended to cover the new memory-informed scoring term's constants/evidence/tests, since its literal "gains a test_path (currently null)" premise is false (test_path already non-null) | Step 5 | Confirm post-Step-3 that `tests/unit/domains/adventure/test_memory_informed_scoring.py` exists and passes, and that it is listed in STRAT-227's `test_path` string in `strategic_cognition.yaml` |

## Anti-Drift Notes

- **`future_advice` is a tuple, not a string** (`cognition.py:251`) — the implementation in Step 2
  uses `in` membership on the tuple (`"avoid_enemy" in e.future_advice`), never `future_advice[0]`
  or an equality check against the whole tuple. Test 4 in Step 3 exists specifically to catch a
  regression here.
- **`HUNT_WEAK_ENEMY` is dead code in `generator.py`** — confirmed zero emission sites. The Step 3
  test for this mapping must explicitly document (in a comment and/or assertion) that this
  suppression is provably correct at the `AdventureRouteScorer.score()` unit level but has no
  observable effect via a live `generate()` → `score()` chain today. Do not quietly pick a
  different, live family to dodge this caveat — Design Decision 1 already justifies keeping
  `avoid_enemy` → `HUNT_WEAK_ENEMY` despite the dead-code caveat, per the ticket's own AC1 example.
- **`CausalMemoryEntry` records never exist in a live simulation run**, before or after this
  ticket — `MemoryUpdatePhase` has zero call sites in `src/engine/pipeline.py` (confirmed
  repo-wide). This ticket's own Request Summary language ("so entities' own causal memory
  measurably shapes route decisions instead of being ignored entirely") is only half-true after
  this ticket: the *scoring-side* wiring becomes real, but the memory itself is still never
  populated live. This must be stated plainly in Steps 4, 6, and 8's doc updates — not glossed
  over as if the feature is fully live.
- **The memory read must stay boolean-gated per advice string, not per-entry-accumulated** — a
  30-entry causal-memory buffer with many matching entries must still produce exactly one ±1.0
  adjustment per mapped family (Step 2's `any(...)` pattern), not a growing stack that could push
  `memory_adjustment` far outside its intended ±1.0 range.
- **`AdventureRouteOption` has 7 existing call sites** (5 in `generator.py`, 2 in `service.py`) —
  Step 1's new defaulted field must not require changes to any of them; if implementation
  discovers a call site that breaks, that is a signal something in Step 1 was done incorrectly
  (e.g. field placed before a non-defaulted field, or positional construction found somewhere not
  caught by this plan's grep), not a signal to change those call sites' behavior.
- **`CognitionModel.memory` is confirmed the real attribute name** (`src/core/cognition.py:549`,
  verified directly during planning) — the `entity.cognition.memory.causal.entries` expression in
  Step 2 is grounded, not assumed.

## Unresolved Questions

None blocking. All ambiguities flagged in investigation.md (advice→family mapping, AC3's stale
premise, the `MemoryUpdatePhase` scope boundary, the `self_model`/`cognition` docstring wording)
have been explicitly decided above with code-grounded rationale, per this task's direction to
resolve them rather than leave them as open questions for a later phase. If Review disagrees with
any specific mapping choice or magnitude in Design Decisions 1–2, that is a design disagreement to
raise at Review, not a gap in this plan.
