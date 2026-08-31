---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260824-RELATIONSHIP-ROLE-FIELD
artifact_type: plan
tags: [social]
---

# Implementation Plan — TCK-20260824-RELATIONSHIP-ROLE-FIELD

## Summary

Add a `RelationshipRole(str, Enum)` (`NEUTRAL` default / `FRIEND` / `RIVAL`) as a new additive field
on `SocialBond`, extend the authoritative update path (`SocialBondUpdate.role_set` →
`RelationshipService.process_update()`) to be the only way to set it, wire a single real consumer
(`PartyCompositionScorer.score()`, extended with a new `ROLE_AFFINITY_WEIGHT = 0.10` additive term)
so a `FRIEND`/`RIVAL`-tagged bond produces a measurably different score, and document the new
mechanic as parity ledger entry `SOC-247` plus a new `docs/mechanics/04_strategic_cognition.md` §7.3
subsection. Both design decisions (enum shape/values, consumer choice) were already made in
`investigation.md`'s Recommendation section with documented rationale; this plan additionally commits
to the exact `ROLE_AFFINITY_WEIGHT` magnitude and sign convention that investigation left as a
Plan-phase calibration call. Six narrow, independently verifiable steps: model field → update-delta
field → authoritative apply clause → nemesis-independence guard test → scorer consumer → docs/parity.

## Calibration Decision — `ROLE_AFFINITY_WEIGHT` and Sign Convention

**`ROLE_AFFINITY_WEIGHT = 0.10`** (confirming investigation's suggested value, not adjusting it).
Rationale: one tier below `TRUST_BONUS_WEIGHT = 0.15` (`src/systems/social_systems/party_composition.py:42`,
verified by direct read) because `role` is a coarser 3-valued categorical signal set explicitly by
narrative logic, versus `sentiment`/`trust_history`'s continuous, interaction-accumulated float — a
deliberately smaller nudge than a densely-evidenced continuous signal, consistent with how
`TRUST_BONUS_WEIGHT` itself was a documented deliberate default (not empirically derived) per the
sibling ticket's investigation.

**Sign convention** (`score_role_affinity()`, mean across pool, mirroring `score_trust_bonds()`'s
shape at `party_composition.py:123-135`, verified by direct read):
- `RelationshipRole.FRIEND` → `+1.0` per-candidate contribution
- `RelationshipRole.RIVAL` → `-1.0` per-candidate contribution
- `RelationshipRole.NEUTRAL` (or no bond at all) → `0.0` per-candidate contribution

Final term: `score = clamp(base_score + TRUST_BONUS_WEIGHT(0.15) * trust_term + ROLE_AFFINITY_WEIGHT(0.10) * role_term, 0.0, 1.0)`.
This ordering (trust term, then role term) matches the existing `docs/mechanics/04_strategic_cognition.md`
§7.1→§7.2 narrative progression and keeps `TRUST_BONUS_WEIGHT`/`ROLE_DIVERSITY_WEIGHT`/`OCEAN_COMPAT_WEIGHT`
untouched, satisfying the investigation's Anti-Drift Hazard on those three constants.

## Steps

### Step 1 — Add `RelationshipRole` enum and `SocialBond.role` field

**Files:** `src/core/models/social.py`

**Change:** `src/core/models/social.py:1-11` (read directly) currently has no `Enum` import and
`SocialBond` (frozen, `slots=True` dataclass, lines 5-11) has exactly 4 fields: `target_id: int`,
`familiarity: float = 0.0`, `sentiment: float = 0.0`, `last_interaction_tick: int = 0`. Add
`from enum import Enum` to the imports (line 1-3 area), then add immediately above the `SocialBond`
class:
```python
class RelationshipRole(str, Enum):
    """Categorical relationship tag on a directed SocialBond. Independent of nemesis_ids/grudge_history."""
    NEUTRAL = "neutral"
    FRIEND = "friend"
    RIVAL = "rival"
```
Then add one new field to `SocialBond` as the last field: `role: RelationshipRole = RelationshipRole.NEUTRAL`.
This is purely additive — confirmed via investigation's repo-wide grep that all 28 `SocialBond(...)`
construction call sites (`src/certification/scenarios.py:248`,
`src/systems/social_systems/relationships.py:55`, and 26 more across `tests/unit/social/*.py` and
related test files) use keyword arguments exclusively, so a new trailing default-valued field breaks
nothing at construction. `role` serializes natively as a plain string under `asdict()`/`json.dumps`
because `RelationshipRole` is a `str` subclass — confirmed by direct read of
`src/core/state.py:732` (`"bonds": {str(k): asdict(v) for k, v in sorted(self.social.bonds.items())}`)
and `src/core/state.py:17` (`from src.core.models.social import SocialBond, ...` — confirms
`state.py` does not redefine or wrap `SocialBond`, it re-exports the same class this step edits).

**Do NOT touch:** `PartyRole` (`src/systems/social_systems/party_composition.py:25-30`), `EntityRole`
(`IntEnum`), `IdentityUpdate.role_set: Optional[int]` (`src/core/updates.py:222`), or
`GroupRecord.roles` (tactical-role strings, `src/systems/world_systems/groups.py`). Do not touch
`SocialComponent.nemesis_ids` or `grudge_history` (both on `src/core/models/social.py:29,37`) — no
read/write relationship between `RelationshipRole` and either is introduced anywhere in this plan.

**Verify:** `test_social_bond_role_defaults_to_neutral`,
`test_social_bond_role_canonical_dict_serializes_as_plain_string` (both `tests/unit/social/test_social_bonds.py`).

---

### Step 2 — Add `SocialBondUpdate.role_set` field

**Files:** `src/core/updates.py`

**Change:** `SocialBondUpdate` (frozen, slots dataclass, `src/core/updates.py:268-274`, read directly)
currently has `target_id: int`, `familiarity_delta: float = 0.0`, `sentiment_delta: float = 0.0`,
`last_interaction_tick_set: Optional[int] = None`. Add one new trailing field:
`role_set: Optional[RelationshipRole] = None`, importing `RelationshipRole` from
`src.core.models.social` (or via whatever existing re-export path `updates.py` already uses for
`SocialBond`/`SocialComponent` — confirm the existing import line at the top of `updates.py` and
follow the same pattern). This exactly mirrors the existing `last_interaction_tick_set: Optional[int] = None`
pattern on the same dataclass, and the existing `IdentityUpdate.life_stage_set: Optional[LifeStage] = None`
precedent (`src/core/updates.py:227`, read directly) for an `Optional[<enum>]` set-field on an
`Update` dataclass. **Other writers to `SocialBondUpdate`/`SocialUpdate`:** `SocialUpdate.bond_updates`
(`src/core/updates.py:279`) is a `List[SocialBondUpdate]`; `SocialUpdate.merge()`
(`src/core/updates.py:315-338`, read directly) concatenates `bond_updates` lists
(`bond_updates=self.bond_updates + other.bond_updates`) without inspecting individual field values —
this merge is list-concatenation, not field-level merging, so it needs no change for the new field to
merge correctly (each `SocialBondUpdate` in the list keeps its own `role_set` value; `process_update()`
in Step 3 applies each list entry independently, same as it already does for
`familiarity_delta`/`sentiment_delta`/`last_interaction_tick_set`). No other code constructs
`SocialBondUpdate` outside `SocialUpdate.bond_updates` per investigation's confirmed call-site survey
(`src/engine/combat.py` writes 4 `SocialBondUpdate(...)` instances, none pre-existing supply more than
`sentiment_delta`/`familiarity_delta`, so all remain unaffected with `role_set` defaulting to `None`).

**Do NOT touch:** `IdentityUpdate.role_set` (a different field, on a different dataclass, `int`-typed
— do not rename or alias). Do not add `role_set` handling to `SocialUpdate.merge()`'s dict-summing
logic (lines 320-335) — `bond_updates` is a list, not a dict, and is already merged correctly by
concatenation.

**Verify:** No standalone test for this step alone (a bare dataclass field addition); folded into
Step 3's tests since `role_set` has no observable effect until `process_update()` reads it.

---

### Step 3 — Apply `role_set` in `RelationshipService.process_update()`

**Files:** `src/systems/social_systems/relationships.py`

**Change:** `process_update()` (`src/systems/social_systems/relationships.py:15-99`, read directly,
sole authoritative apply path per SOC-217) has its bond-rebuild loop at lines 51-61:
```python
new_bonds = dict(social.bonds)
for b_upd in update.bond_updates:
    tid = b_upd.target_id
    bond = new_bonds.get(tid, SocialBond(target_id=tid))
    new_bonds[tid] = replace(
        bond,
        familiarity=max(0.0, min(1.0, bond.familiarity + b_upd.familiarity_delta)),
        sentiment=max(-1.0, min(1.0, bond.sentiment + b_upd.sentiment_delta)),
        last_interaction_tick=b_upd.last_interaction_tick_set if b_upd.last_interaction_tick_set is not None else bond.last_interaction_tick
    )
```
Add one new keyword to the `replace(...)` call, directly mirroring the `last_interaction_tick_set`
line immediately above it:
```python
        role=b_upd.role_set if b_upd.role_set is not None else bond.role,
```
This is a set-if-provided (not a delta, not an overwrite-with-default) semantic — a `None` `role_set`
leaves the existing bond's `role` untouched, exactly like `last_interaction_tick_set`.
**Other writers to `SocialComponent.bonds`:** confirmed by direct read that `process_update()`
(this method) is the *only* code path in `relationships.py` that writes `bonds` — the sibling method
`prune_low_salience()` (`src/systems/social_systems/relationships.py:101-118`, read directly) only
rebuilds `trust_history`/`familiarity_history`/`debt_history`/`fear_history`/`grudge_history`/`salience_history`;
its `replace(...)` call at lines 110-117 does not list `bonds` as a keyword, so it implicitly
preserves the caller's existing `bonds` dict unchanged — no collision with this step's edit. No other
module in the codebase calls `dataclasses.replace(bond, ...)` or `dataclasses.replace(social, bonds=...)`
directly (confirmed by investigation's Anti-Drift Hazards and the SOC-217 authoritative-path rule);
the only other `SocialBond(...)` constructions are initial/typed-default constructions at world-gen
time (28 call sites, Step 1), not runtime mutations, so there is no concurrent-writer race to
reconcile for this field.

**Do NOT touch:** Any of the `-1.0..1.0`/`0.0..1.0`/`0.0..5.0` clamping logic for
`trust_history`/`familiarity_history`/`debt_history`/`fear_history`/`grudge_history`/`salience_history`
(lines 30-49) or `nemesis_ids`/`nemesis_promotion` handling (lines 66-67) — role is categorical, not
clamped, and must never read or write `nemesis_ids`/`grudge_history` per the investigation's
Reconciliation section. Do not add a read/lookup method to `RelationshipService` — it stays
authoritative-mutation-only (`process_update()` and `prune_low_salience()` remain its only two
methods).

**Verify:** `test_social_bond_role_set_via_authoritative_update_only`,
`test_process_update_role_set_none_preserves_existing_role` (both `tests/unit/social/test_relationships.py`).

**Depends on:** Step 1 (needs `SocialBond.role`/`RelationshipRole`), Step 2 (needs `SocialBondUpdate.role_set`).

---

### Step 4 — Nemesis-independence guard test

**Files:** `tests/unit/social/test_social_memory.py` (or `tests/unit/social/test_groups.py`, whichever
already contains a `nemesis_ids`/routing-avoidance/cooperation-refusal test — confirm at
implementation time which file has the closest existing nemesis-mechanics test to extend, per
test_plan.md's "wherever `nemesis_ids`/routing-avoidance/cooperation-refusal is already tested")

**Change:** Add a new test (or extend an existing nemesis test) asserting: a bond constructed/updated
with `role=RelationshipRole.RIVAL` (via the Step 3 authoritative path) whose `grudge_history` value
for that counterparty stays below the `3.0` promotion threshold
(`docs/simulation/social_systems_contract.md:84`, "When `grudge_history[entity_id] >= 3.0`, the
entity is promoted to `nemesis_ids`") does **not** appear in `nemesis_ids` and does not trigger any
nemesis-gated behavior (routing avoidance, cooperation refusal, AVENGE directive creation). This is
the concrete proof that `RelationshipRole.RIVAL` and `nemesis_ids` remain independent durable facts,
per investigation's Reconciliation section — no code changed in Steps 1-3 reads `role` when computing
`nemesis_ids`, so this step is purely additive test coverage confirming that absence.

**Do NOT touch:** `SocialMemoryService`'s actual nemesis-promotion logic (`grudge_history >= 3.0`
check) — this step adds a test only, no production code change.

**Verify:** The new/extended nemesis-independence test itself (no separate production-code
verification needed — this step's only deliverable is the test).

**Depends on:** Steps 1-3 (needs `RelationshipRole` and the authoritative `role_set` path to exist).

---

### Step 5 — Wire `PartyCompositionScorer.score()` role-affinity term

**Files:** `src/systems/social_systems/party_composition.py`

**Change:** `party_composition.py` (read directly) already has the established `actor`-gated
additive-term shape: `TRUST_BONUS_WEIGHT: float = 0.15` (line 42), `_candidate_trust_value()`
(lines 108-121, reads `actor.social.bonds.get(candidate.id)`, falls back to `trust_history`),
`score_trust_bonds()` (lines 123-135, mean across pool), folded into `score()` (lines 137-159) as
`base_score + cls.TRUST_BONUS_WEIGHT * trust_term`, clamped `[0.0, 1.0]` (line 159). Add, mirroring
this exact shape:
1. Class constant: `ROLE_AFFINITY_WEIGHT: float = 0.10` (per Calibration Decision above), placed
   directly below `TRUST_BONUS_WEIGHT: float = 0.15` (line 42).
2. `_candidate_role_value(actor, candidate) -> float` static method, mirroring
   `_candidate_trust_value()`'s shape (lines 108-121): reads `actor.social.bonds.get(candidate.id)`;
   if the bond exists, return `+1.0` for `RelationshipRole.FRIEND`, `-1.0` for
   `RelationshipRole.RIVAL`, `0.0` for `RelationshipRole.NEUTRAL`; if no bond exists at all, return
   `0.0` (matches `_candidate_trust_value()`'s "neutral default 0.0 for a candidate with no prior
   relationship record"). Import `RelationshipRole` from `src.core.models.social` (already imported
   transitively via `EntityState`'s `TYPE_CHECKING` block at line 22 — add a runtime import since this
   method needs the enum values at call time, not just for type-checking).
3. `score_role_affinity(actor, entities) -> float` static method, mirroring `score_trust_bonds()`
   (lines 123-135): mean of `_candidate_role_value(actor, e)` across `entities`; empty pool → `0.0`;
   `round(..., 4)` matching the existing rounding convention.
4. In `score()` (lines 137-159), inside the `if actor is None: return base_score` / `else:` branch,
   add a third additive term:
```python
        trust_term = cls.score_trust_bonds(actor, entities)
        role_term = cls.score_role_affinity(actor, entities)
        return round(max(0.0, min(1.0, base_score + cls.TRUST_BONUS_WEIGHT * trust_term + cls.ROLE_AFFINITY_WEIGHT * role_term)), 4)
```
**Other writers/callers of `PartyCompositionScorer.score()`:** confirmed by direct read of
`party_composition.py`'s docstring and investigation's grep — two call sites:
`AdventureRouteGenerator.generate()`'s FORM_PARTY branch (`src/domains/adventure/generator.py:139`,
passes `actor=entity`) and `GroupSystem`'s ally-cohesion group formation
(`src/systems/world_systems/groups.py:310`, calls with **no** `actor` kwarg). Both are read-only
*consumers* of `score()`'s return value, not writers to any shared resource this step mutates (the
method remains pure/stateless — no `dataclasses.replace`/`*Update` construction anywhere in
`party_composition.py`, confirmed). The `generator.py` call site will pick up the new role-affinity
term automatically (it already passes `actor=entity`) — this is in-scope per the ticket's AC ("a real
consumer produces a measurably different score"), not an out-of-scope expansion, since no formula in
`generator.py` itself is edited; `generator.py`'s own `confidence` formula (line 139, using
`score_trust_bonds` directly, not `score()`) is untouched. The `groups.py` call site never supplies
`actor`, so it takes the `if actor is None: return base_score` branch and is structurally unaffected,
per investigation's confirmed analysis — no code change needed there.

**Do NOT touch:** `TRUST_BONUS_WEIGHT`, `ROLE_DIVERSITY_WEIGHT`, `OCEAN_COMPAT_WEIGHT` (lines 40-42) —
values and usage stay bit-identical. Do not touch `score_role_diversity()`, `score_ocean_compatibility()`,
`infer_party_role()`, or `PartyRole` itself (lines 25-105) — these are the pre-existing, unrelated
functional-combat-role concept. Do not touch `src/domains/adventure/generator.py`'s `confidence`
formula (line 139-150) or `src/domains/adventure/scoring.py`/`AdventureRouteScorer`/STRAT-227 — per
investigation's Recommendation, this ticket's AC is satisfied entirely inside `party_composition.py`;
`generator.py`'s FORM_PARTY branch benefits automatically through the unmodified `score()` call it
already makes, with no line of `generator.py` itself edited. Do not deepen
`src/domains/cooperation/evaluators.py`'s `PartnerFitEvaluator.evaluate()` existing direct
`social.bonds` read (explicit ticket Out of Scope) — no role read added there.

**Verify:** `test_party_composition_score_reflects_candidate_role`,
`test_party_composition_score_role_term_is_zero_for_all_neutral_pool`,
`test_party_composition_score_role_term_requires_actor` (all `tests/unit/social/test_party_composition.py`).

**Depends on:** Step 1 (needs `RelationshipRole`). Independent of Steps 2-4 (does not touch the
update/apply path, only reads `bond.role` directly, matching `_candidate_trust_value()`'s existing
raw-attribute-read pattern) — but cannot be meaningfully tested with role values other than the
default `NEUTRAL` until Step 3 exists to set `role` via the authoritative path in test fixtures (tests
may also construct `SocialBond(target_id=..., role=RelationshipRole.FRIEND)` directly for scorer-only
unit tests, since `party_composition.py` only reads bonds, never mutates them — either path works,
but Step 3 must land first since `test_party_composition_score_reflects_candidate_role` is expected
to use realistic bond construction consistent with the rest of the test file's patterns).

---

### Step 6 — Docs and parity ledger updates

**Files:** `docs/mechanics/04_strategic_cognition.md`, `docs/parity_ledger/social_narrative.yaml`,
`docs/simulation/social_systems_contract.md`

**Change:**
1. **`docs/mechanics/04_strategic_cognition.md`** — insert a new `### 7.3 Role-Affinity Adjustment
   (TCK-20260824-RELATIONSHIP-ROLE-FIELD)` subsection directly after the existing `### 7.2 Trust/Bonds-Aware
   Adjustment` subsection (confirmed by direct read: §7.2 currently ends at line 757, with a blank
   line 758-759 before the file's next section; re-read the file immediately before editing to confirm
   the line numbers have not shifted from a concurrent edit). Content: document the `RelationshipRole`
   enum (`NEUTRAL`/`FRIEND`/`RIVAL`), the formula
   `score = clamp(base_score + TRUST_BONUS_WEIGHT(0.15) * trust_term + ROLE_AFFINITY_WEIGHT(0.10) * role_term, 0.0, 1.0)`,
   the `score_role_affinity()` sign convention (`FRIEND -> +1.0`, `RIVAL -> -1.0`, `NEUTRAL -> 0.0`,
   mean across pool), and an explicit sentence confirming §7.1's role-diversity/OCEAN weights and
   §7.2's `TRUST_BONUS_WEIGHT` term stay bit-identical (matching the format/tone of the existing
   §7.1/§7.2 subsections, including a `**Source:**` line).
2. **`docs/parity_ledger/social_narrative.yaml`** — add a new entry after `SOC-246` (confirmed via
   direct read that `SOC-244`/`SOC-245`/`SOC-246` are the three most recent entries; re-run
   `tools/gate_checks/parity_updater_static.py::next_available_id('social_narrative.yaml')` at
   implementation time, not planning time, in case a concurrent ticket has claimed `SOC-247` first
   during the gap between investigation and implementation), matching the exact schema shape of the
   `SOC-244` entry (`id`, `text`, `status: verified`, `priority: P1`, `legacy_evidence: null`,
   `v2_evidence`, `proof_type: parity`, `test_path`, `divergence_note`, `support_boundary: null` —
   confirmed by direct read of `docs/parity_ledger/social_narrative.yaml:3349-3383`). `text` documents
   `SocialBond.role`, `SocialBondUpdate.role_set`, the `process_update()` set-if-provided clause, and
   `PartyCompositionScorer.score()`'s new role-affinity term with its exact weight/sign convention.
   `test_path` points at `tests/unit/social/test_party_composition.py::test_party_composition_score_reflects_candidate_role`
   (the primary AC-proving test). `divergence_note` states this is a new mechanic (no prior version of
   `SocialBond` had a role concept) and explicitly notes `RelationshipRole` is independent of
   `nemesis_ids`/`grudge_history` (cross-referencing Step 4's guard test), analogous to how SOC-244's
   own `divergence_note` disclaims the pre-existing SOC-231/SOC-232 docstring mis-citation. **Use
   `tools/parity_ledger_writer.py` (the schema-validating sanctioned tool) for this edit, not a raw
   Edit/ad-hoc script** — a full-file YAML rewrite via raw editing on this large, actively-shared file
   risks corruption.
3. **`docs/simulation/social_systems_contract.md`** — update the `### Social bonds` subsection (line
   70, currently: "`SocialBond` is a richer directional relationship: `familiarity`, `sentiment`
   (−1.0 to 1.0), `last_interaction_tick`.") to add `role` (`NEUTRAL`/`FRIEND`/`RIVAL`, default
   `NEUTRAL`) to the field list. Add one sentence to the `## Party Composition` subsection (currently
   lines 135-149, confirmed by direct read) documenting the new additive role-affinity term alongside
   the existing SOC-244 trust/bonds description, citing the new `SOC-247` id.

**Other writers to these three docs:** `docs/mechanics/04_strategic_cognition.md` and
`docs/simulation/social_systems_contract.md` are edited only by whichever ticket's session is
currently active per the project's worktree-isolation convention — no automated tool rewrites these
files, so a normal `Edit` is safe, but re-read both files immediately before editing (not just at
Investigate time) since the working directory is documented as sometimes shared across concurrent
sessions. `docs/parity_ledger/social_narrative.yaml` is the higher-risk shared resource: it is
appended to by every ticket touching the `social_narrative` subsystem, and `docs/REGISTRY.yaml` is
regenerated from it (and other docs) unconditionally at ticket close — this step's parity entry must
land before the ticket's own Finalize-phase `docs/REGISTRY.yaml` regeneration, and must use the
sanctioned `tools/parity_ledger_writer.py` (not raw YAML editing) specifically because concurrent
tickets may be appending their own entries to the same file around the same time.

**Do NOT touch:** `docs/architecture/2026-08-11-adventure-as-cognition-strategy-subcomponent-design.md`,
`docs/simulation/domains/adventure_contract.md`, or `docs/parity_ledger/strategic_cognition.yaml`
(STRAT-227) — none of this ticket's recommended scope touches `generator.py`'s FORM_PARTY
candidate-selection/confidence formula or `scoring.py`'s `AdventureRouteScorer.score()`, per
investigation's confirmed "Docs Requiring Update" analysis. Do not modify the existing `SOC-244` entry
in `social_narrative.yaml` — it documents a complete, already-shipped, already-tested mechanic and
stays untouched; the new role-affinity mechanic gets its own `SOC-247` entry.

**Verify:** No new test (docs-only step); `done-checker`'s `frontmatter_valid` condition and the
ticket's own Finalize-phase `docs/REGISTRY.yaml` regeneration are the mechanical checks that confirm
this step landed correctly.

**Depends on:** Step 5 (the exact weight/formula must be finalized in code before being documented).

## Scope Guards

- Do not touch `SocialComponent.nemesis_ids` or `grudge_history`, or any nemesis-promotion logic
  (`grudge_history >= 3.0` threshold, routing avoidance, cooperation refusal, AVENGE directives).
  `RelationshipRole.RIVAL` must never read or write either.
- Do not touch `PartyRole` (`TANK`/`HEALER`/`DPS`/`SUPPORT`), `EntityRole` (`IntEnum`),
  `IdentityUpdate.role_set` (`int`-typed), or `GroupRecord.roles` (tactical-role strings). Four
  pre-existing, unrelated "role" concepts already coexist in this codebase; `RelationshipRole` stays
  scoped to `SocialBond` only.
- Do not add a read/lookup method to `RelationshipService` — it remains authoritative-mutation-only
  (`process_update()` and `prune_low_salience()` are its only two methods).
- Do not bypass `SocialUpdate`/`RelationshipService.process_update()` to set `role` — any direct
  `dataclasses.replace(bond, role=...)` outside `process_update()` violates SOC-217.
- Do not touch `TRUST_BONUS_WEIGHT`, `ROLE_DIVERSITY_WEIGHT`, or `OCEAN_COMPAT_WEIGHT` — the new term
  is strictly additive alongside them.
- Do not extend `src/domains/adventure/generator.py`'s FORM_PARTY `confidence`/`expected_benefit`
  formulas or `src/domains/adventure/scoring.py`/STRAT-227 — this ticket's AC is fully satisfied by
  `PartyCompositionScorer.score()` alone.
- Do not deepen `src/domains/cooperation/evaluators.py`'s `PartnerFitEvaluator.evaluate()` existing
  direct `social.bonds` read — explicit ticket Out of Scope.
- Do not modify `docs/parity_ledger/strategic_cognition.yaml` (STRAT-227) or
  `docs/architecture/2026-08-11-adventure-as-cognition-strategy-subcomponent-design.md` — out of
  scope, no formula in either area changes.
- Do not touch `SocialAppraisalSystem.appraise_contract()` (`src/systems/social_systems/appraisal.py`)
  — not the chosen consumer for this ticket; its existing test suite passing unmodified is itself the
  guard that this ticket did not silently expand into that out-of-scope second consumer.

## Dependency Map

```
Step 1 (SocialBond.role + RelationshipRole enum)
  ├── Step 2 (SocialBondUpdate.role_set)
  │     └── Step 3 (process_update() apply clause)  [depends on 1 + 2]
  │           └── Step 4 (nemesis-independence guard test)  [depends on 1-3]
  └── Step 5 (PartyCompositionScorer role-affinity term)  [depends on 1 only; independent of 2-4]
        └── Step 6 (docs + parity ledger)  [depends on 5 for the finalized formula/weight]
```
Steps 1→2→3→4 form one chain (the authoritative-path plumbing). Step 5 branches off Step 1 directly
and can be implemented in parallel with Steps 2-4 if desired, but Step 6 must wait for Step 5 since it
documents the exact formula Step 5 produces.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| SocialBond gains an additive role field (enum, NEUTRAL/UNSET default); existing construction/serialization continues to work unmodified when omitted | Step 1 | `test_social_bond_role_defaults_to_neutral`, `test_social_bond_role_canonical_dict_serializes_as_plain_string` |
| SocialBondUpdate/RelationshipService.process_update() support setting role only through the authoritative path | Steps 2, 3 | `test_social_bond_role_set_via_authoritative_update_only`, `test_process_update_role_set_none_preserves_existing_role` |
| A real consumer produces a measurably different score for two otherwise-identical bonds differing only in role, asserted by a new test with fixed familiarity/sentiment | Step 5 | `test_party_composition_score_reflects_candidate_role`, `test_party_composition_score_role_term_is_zero_for_all_neutral_pool`, `test_party_composition_score_role_term_requires_actor` |
| docs/mechanics/04_strategic_cognition.md and social_narrative.yaml gain a new SOC-### entry documenting the formula | Step 6 | `done-checker` frontmatter/registry checks (docs-only step, no dedicated pytest) |

## Anti-Drift Notes

- **`RIVAL` ≠ nemesis.** `nemesis_ids` is a one-way ratchet driven purely by `grudge_history >= 3.0`
  (`docs/simulation/social_systems_contract.md:84`). A `RIVAL`-tagged bond with high `sentiment` and
  no accumulated grudge is not a nemesis and must not behave like one anywhere. Step 4 exists
  specifically to prove this with a test, not just an assertion in prose.
- **Five distinct "role" concepts now coexist**: `EntityRole` (`IntEnum`, identity), `PartyRole`
  (`str, Enum`, functional combat role), `GroupRecord.roles` (plain-string tactical role),
  `IdentityUpdate.role_set` (`int`), and now `RelationshipRole` (`str, Enum`, this ticket, scoped to
  `SocialBond` only). Never alias or cross-read between them.
- **`score_role_affinity()` must return exactly `0.0` for an all-`NEUTRAL` pool** — this is the
  regression guard (`test_party_composition_score_role_term_is_zero_for_all_neutral_pool`) that proves
  the new term is additive, not a silent rescale of the pre-existing bit-identical §7.1/§7.2 formulas.
- **`GroupSystem`'s call site never supplies `actor`** (`src/systems/world_systems/groups.py:310`),
  so it takes the `actor is None` branch in `score()` and is structurally unaffected by the new term —
  no code change needed there, and `tests/unit/social/test_groups.py`'s existing assertions must stay
  green untouched as proof.
- **SOC-231/SOC-232 docstring mis-citation in `party_composition.py`'s module header is pre-existing
  and out of scope** — do not propagate it to the new code (do not cite SOC-231/SOC-232 for the
  role-affinity term; use the new `SOC-247`), and do not "fix" the existing mis-citation as a drive-by
  change.
- **`docs/parity_ledger/social_narrative.yaml` is a shared, actively-appended-to file.** Re-verify the
  next available id (`SOC-247`) at implementation time via
  `tools/gate_checks/parity_updater_static.py::next_available_id`, and write the entry only through
  `tools/parity_ledger_writer.py` — never a raw full-file YAML rewrite via ad-hoc script or manual
  Edit, which risks corrupting concurrent tickets' entries in the same file.

## Unresolved Questions

None. Both design decisions this ticket required — (1) the `RelationshipRole` enum name/values and
its explicit independence from `nemesis_ids`, and (2) the consumer choice (`PartyCompositionScorer.score()`
over `SocialAppraisalSystem.appraise_contract()`) — were already firmly resolved in `investigation.md`'s
Recommendation section with documented rationale, not left open. The one remaining open item flagged by
investigation (the exact `ROLE_AFFINITY_WEIGHT` magnitude) was a stated Plan-phase calibration call, not
a question requiring human review, and this plan has committed to a concrete value (`0.10`) and sign
convention (`FRIEND -> +1.0`, `RIVAL -> -1.0`, `NEUTRAL -> 0.0`) with a one-line rationale above. No
open question remains that would change the implementation approach.

## Deviations

Steps 1-5 were implemented exactly as specified, with two narrow deviations, both driven by facts
only visible once implementation started reading files this plan did not fully enumerate:

1. **Step 2's import path**: the plan offered `src.core.models.social` or "whatever existing
   re-export path `updates.py` already uses for `SocialBond`/`SocialComponent`" as an either/or.
   Direct read of `updates.py`'s imports at implementation time confirmed it does not import
   `SocialBond`/`SocialComponent` at all today (no precedent re-export path exists for those
   symbols in this file), so `RelationshipRole` is imported directly from `src.core.models.social`
   (the defining module) — the same module `state.py` itself imports `SocialBond` from. No
   alternative existed to choose between; this resolves the plan's stated either/or in favor of the
   only path that was actually available.
2. **Step 4's target file**: the plan named `tests/unit/social/test_social_memory.py` or
   `tests/unit/social/test_groups.py` as the two candidates to check for an existing
   `nemesis_ids`/routing-avoidance/cooperation-refusal test to extend. A repo-wide grep for
   `nemesis_ids` across `tests/` at implementation time found neither file contains any such test —
   the actual closest-matching file is `tests/unit/social/test_social_memory_service.py` (not named
   by plan.md or investigation.md), which already directly tests
   `SocialMemoryService.check_nemesis_promotion()`'s `grudge_history >= 3.0` threshold with the exact
   fixture pattern (`make_entity(grudge_history=...)`, `with_social(entity, nemesis_ids=...)`) this
   guard test needed. The new test
   `test_check_nemesis_promotion_rival_role_below_grudge_threshold_not_promoted` was added there
   instead, following that file's existing conventions exactly. No production code was touched by
   this step, consistent with the plan.

Both deviations are additive/path-selection only — the intended behavior, formula, weights, and
scope guards of Steps 1-5 were followed exactly as written.
