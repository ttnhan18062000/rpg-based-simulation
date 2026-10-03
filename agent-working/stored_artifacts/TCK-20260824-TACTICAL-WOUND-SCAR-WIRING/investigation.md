---
status: historical
layer: combat
authority: P2
audience: agent
ticket_id: TCK-20260824-TACTICAL-WOUND-SCAR-WIRING
artifact_type: investigation
tags: [combat]
---

# Investigation — TCK-20260824-TACTICAL-WOUND-SCAR-WIRING

## Current Behavior

**Note on search-before-grep step**: `mcp__knowledge-search__search_docs` returned `{"error": "index
not found", "action": "run make knowledge-index"}` for the topic query, and the documented fallback
`python3 tools/knowledge_search.py query ... --top-k 5` returned the same "knowledge index not
found" condition — both are the known, pre-existing environment gap noted in the task instructions,
not skipped by choice. `graphify query "TacticalDecisionSystem wound scar tactical decision"` was
run and returned 393 BFS-depth-2 nodes rooted at `TacticalDecisionSystem`, confirming
`WoundState` (`src/core/state.py:90`), `ScarState` (`src/core/state.py:105`), and
`TacticalDecisionSystem` (`src/engine/tactical.py:23`) as the primary graph-linked nodes — consistent
with the code-level findings below, gathered as required follow-up.

**`TacticalDecisionSystem.evaluate_entity_intent`** (`src/engine/tactical.py:38-700`) is the sole
entry point for bounded local tactical decisions. Relevant existing branches:

- **HP-ratio cover-seeking/retreat** (`tactical.py:442-469`): gated on
  `role == "SKIRMISHER" or hp_percent < 0.4` where `hp_percent = entity.combat.hp /
  max(1, entity.combat.max_hp)` (line 442). If ranged threats exist, moves to cover
  (`SEEK_COVER`, line 447-456). If `hp_percent < 0.15` and still in this branch, retreats to origin
  (`PANIC_RETREAT`, line 459-469). **Zero wound/scar awareness** — only reads raw `hp`/`max_hp`.
- **PROTECTOR guard-wounded-ally** (`tactical.py:492-519`): only runs when `group and role ==
  "PROTECTOR"` and hostiles are present (this is section "5.3", reached only after the
  no-hostiles early-return at line 348 does not fire). Priority 1: guards the group leader if
  `leader.interaction.target_node_id is not None or hp_ratio < 0.8` (line 502, `hp_ratio =
  leader.combat.hp / max(1, leader.combat.max_hp)`). Priority 2: guards any other ally with
  `a.combat.hp / max(1, a.combat.max_hp) < 0.7` (line 507). **Zero wound/scar awareness** — pure
  HP-ratio thresholds.
- A separate, unrelated PROTECTOR/VANGUARD branch at `tactical.py:312-331` ("Role-Based
  Obligation") also triggers guard-leader movement, but only when **no hostiles are present** and
  the leader is `INTERACT`-ing — this is the branch `tests/unit/social/test_domain_7_social.py::
  test_protector_guarding` (lines 134-156) already exercises. It is a different code path from the
  492-519 "5.3 Guarding Logic" branch this ticket must modify (that one requires hostiles present,
  since it falls after the `if not hostiles: ... return` block at line 348). Do not conflate the
  two when writing new tests for AC #2 — a new PROTECTOR guard test needs `hostiles` populated to
  reach line 492-519.

**Reusable aggregators** (`src/engine/rpg_depth.py`), confirmed present and unmodified since prior
tickets:
- `WoundService.get_wound_stat_penalties(wounds: list) -> Dict[str, float]` (lines 138-157): sums
  `atk_penalty`/`def_penalty`/`speed_penalty`/`max_hp_penalty` across all wounds where `not
  w.healed`.
- `WoundService.get_scar_stat_penalties(scars: list) -> Dict[str, float]` (lines 159-173): sums
  `atk_penalty`/`def_penalty`/`speed_penalty` across all scars (no `healed` filter — scars have no
  such field; see `ScarState` below).

**Data model** (`src/core/state.py`):
- `WoundState` (frozen dataclass, lines 89-101): `id`, `kind`, `severity` (0.0-1.0),
  `tick_inflicted`, `atk_penalty`, `def_penalty`, `speed_penalty`, `max_hp_penalty` (all
  `float = 0.0`), `healed: bool = False`, `scar_created: bool = False`.
- `ScarState` (frozen dataclass, lines 104-112): `id`, `wound_kind`, `tick_created`, `atk_penalty`,
  `def_penalty`, `speed_penalty` (all `float = 0.0`). **No `max_hp_penalty` field on `ScarState`**
  (confirmed — only wounds carry an HP penalty).
- `CombatComponent.wounds: List[WoundState]` / `.scars: List[ScarState]` (lines 312-313), both
  `field(default_factory=list)`. The authoritative apply path (`WoundPatch.apply()`,
  `src/engine/patches.py:639`, confirmed by `TCK-20260824-WOUND-HEALING-DECISION`'s Implementation
  Notes) always commits these as **tuples**, not lists, once a real `WoundUpdate` has gone through
  `ApplyPath`. `WoundService.get_wound_stat_penalties`/`get_scar_stat_penalties` iterate with a bare
  `for w in wounds`, so they are tuple/list-agnostic and unaffected by that shape detail —
  confirmed safe to call with either.

**Production data reality** (confirmed by `TCK-20260824-WOUND-HEALING-DECISION`, re-verified via
this session's own read of `docs/mechanics/02_combat_laws.md:85-92` and `src/engine/combat.py:605-
618`): `_get_wound_infliction()` is the only production constructor of `WoundUpdate` in `src/`, and
it only ever populates `wounds_add`. `wounds_heal` and `scars_add` have **zero production
producers** — wounds never heal, and scars are never created by the live pipeline. This is a
settled, documented decision (Mechanics Bible Section 5 "Wound Permanence"), not a gap this ticket
should try to close. Consequence for this ticket: any test exercising the scar-behavior-difference
acceptance criterion (AC #3) must hand-construct `ScarState` entries directly via
`V2EntityBuilder(...).combat(scars=[...])` (confirmed supported —
`src/core/builder.py:238-274` accepts a `scars: Optional[List[ScarState]]` kwarg), matching the
pattern the ticket's own briefing already anticipated.

**`speed_penalty` non-wiring** (confirmed, `src/engine/rpg_depth.py:341-389`
`SkillScalingService.get_effective_stats()`): only `atk_penalty`, `def_penalty`, and (for wounds
only) `max_hp_penalty` are consumed (lines 374-384); `speed_penalty` is computed and stored on both
`WoundState` and `ScarState` but never read anywhere in `get_effective_stats()`. This is an
explicit, already-documented out-of-scope gap (`TCK-20260824-WOUND-PENALTY-FORMULA-WIRING`'s Out of
Scope and Completion Summary) that this ticket must not silently close — this ticket is
decision-making only (should a wounded/scarred entity behave differently), not a stat-computation
fix.

**Test infrastructure already exists** for the exact shape of test this ticket needs:
`tests/unit/combat/test_engagement_behavior.py` uses `V2EntityBuilder(...).combat(hp=..., ...)`
and bare `AuthoritativeState(entities={...})` to drive `TacticalDecisionSystem.evaluate_entity_intent`
directly (`test_retreat_behavior`, lines 46-56, is the existing hp_percent<0.15 PANIC_RETREAT test
this ticket's new wound-triggered-retreat test must stay independent of/parallel to).
`tests/unit/social/test_domain_7_social.py::test_protector_guarding` (lines 134-156) shows the
`GroupRecord(id=..., leader_id=..., member_ids={...}, anchor=..., roles={eid: "PROTECTOR"})`
construction pattern needed for AC #2's guard-wounded-ally test, though that specific existing test
exercises the *different* no-hostiles guard branch (line 312-331) — a new test for AC #2 needs
`hostiles` present in `state.entities` to reach the 492-519 branch.

## Mechanics / Engine Constraints

- **`docs/mechanics/02_combat_laws.md` Section 5 "Wound Infliction"** (lines 70-92): documents the
  wound infliction threshold (`damage > max_hp * 0.25`), severity formula, the severity-scaled
  penalty formula (`atk_penalty=int(severity*3)`, etc.), and explicit Wound Permanence (no healing,
  no scar production). It does **not** currently describe any tactical-decision consequence of a
  wound/scar (retreat, cover-seeking, guard-priority) — that omission is exactly what this ticket
  is scoped to close, both in code and in this doc.
- **Strategic/Tactical Rule** (project CLAUDE.md): "Strategy owns enduring direction. Tactics own
  immediate execution. Do not solve strategic problems by stacking more tactical goal scoring." The
  new wound/scar-aware branches must stay tactical (immediate positioning/target reactions within
  `TacticalDecisionSystem`), not leak into `StrategicIntelligenceSystem`/goal scoring — consistent
  with the ticket's own scope (all three ACs are phrased as `TacticalDecisionSystem` branch
  changes).
- **Core Boundaries / Durable State Rule**: "Decision logic reads state. It does not authoritatively
  mutate durable state." `TacticalDecisionSystem.evaluate_entity_intent` already strictly returns
  `EntityUpdate`/`NavigationUpdate`/`TaskUpdate` objects for the authoritative apply path to commit
  — new wound/scar reads must stay read-only against `entity.combat.wounds`/`.scars` (and
  `ally.combat.wounds`/`.scars` for the PROTECTOR branch), never construct or mutate
  `WoundState`/`ScarState`/`WoundUpdate` from inside `tactical.py`. `WoundUpdate` construction stays
  exclusively `combat.py`'s `_get_wound_infliction()`'s job (out of scope, explicitly listed as
  such in the ticket).
- **Reuse mandate (AC #4)**: new reads must call `WoundService.get_wound_stat_penalties(entity.
  combat.wounds)` / `WoundService.get_scar_stat_penalties(entity.combat.scars)` rather than
  re-deriving severity/penalty sums inline in `tactical.py` — both aggregators already exist and are
  unit-tested (`tests/unit/core/test_rpg_depth.py::TestWoundInfliction`,
  `TestScarPermanence`), and `tactical.py` has no existing import of `WoundService` today (only
  `LeashService` is imported from `src.engine.rpg_depth`, line 106) — a new local import will be
  required.

## Docs Requiring Update

- `docs/mechanics/02_combat_laws.md`: Section 5 ("Wound Infliction") documents the wound/scar
  penalty formula and permanence but has zero mention of any tactical-decision consequence
  (retreat/cover-seeking/guard-priority); once this ticket wires wound/scar severity into
  `TacticalDecisionSystem`, that is new documented behavior requiring a new bullet or short
  subsection there, per this ticket's own `Related Docs` listing and the "new feature still needs a
  doc" rule.
- `docs/parity_ledger/combat_movement.yaml`: AC #5 explicitly requires "a new parity_ledger entry or
  explicit extension note for the new wound/scar tactical branch, distinct from COMB-268's existing
  hp-ratio-only verified entry" — COMB-268 (`text: "Low HP affects tactical choice."`, `test_path:
  null`) only covers the pre-existing hp_percent branch and must not be silently reused/overwritten
  to also claim wound/scar coverage it doesn't test.

`docs/mechanics/01_entity_anatomy.md` (path: `docs/mechanics/01_entity_anatomy.md`, under
`docs/mechanics/`) was considered and excluded: its Section 6 "Permanent Scars" subsection
(rewritten by `TCK-20260824-WOUND-HEALING-DECISION`) documents the wound/scar *data model and
permanence decision*, which this ticket does not touch (Out of Scope: "Any change to the underlying
WoundState/ScarState data model"). This ticket only adds a new *consumer* of the existing
aggregators inside `TacticalDecisionSystem`, so `01_entity_anatomy.md` stays accurate as-is.

## Parity Ledger Overlap

- **COMB-268** (`status: verified`, `priority: P0`, `test_path: null`, `v2_evidence: "Implementation
  proven via exhaustive checklist audit Phase 1-11"`) — "Low HP affects tactical choice." Covers
  only the existing `hp_percent`-based branch (`tactical.py:442-469`). This ticket must not modify
  or reuse this entry for the new wound/scar branch (AC #5 explicitly says "distinct from
  COMB-268"); a genuinely new entry should be added instead, referencing real new test evidence
  (unlike COMB-268 itself, which has `test_path: null` — do not perpetuate that gap in the new
  entry).
- **COMB-269** (`text: "Threat level affects tactical choice."`) — adjacent, same
  cover-seeking/retreat branch (`ranged_threats` check at line 445), not itself in scope but
  physically inside the same `if` block the wound-triggered branch must coexist with.
- **COMB-072/073/COMB-102/103/104** — all `verified`, all already updated by
  `TCK-20260824-WOUND-PENALTY-FORMULA-WIRING` to cite the real severity-scaled formula and real
  `test_path`s (`tests/unit/core/test_rpg_depth.py::TestWoundInfliction::*`,
  `tests/unit/combat/test_direct_combat_outcomes.py::test_wound_penalties_scale_with_severity_
  through_live_combat_path`). These cover the *penalty-formula* pipeline this ticket must reuse
  (via `WoundService.get_wound_stat_penalties`/`get_scar_stat_penalties`), not the tactical-decision
  consumption of it — no changes needed to these entries themselves.
- **COMB-290** (`status: verified`, `priority: P1`) — the 25%-damage wound infliction threshold.
  Unrelated to this ticket's decision-making scope; not touched.
- **COMB-314** (`status: verified`, `priority: P1`) — documents the live-path wiring of the
  severity-scaled formula end-to-end into `get_effective_stats()`, including the explicit note that
  `speed_penalty` is "not yet wired into get_effective_stats()". Confirms (independently of the
  task-supplied context) that `speed_penalty` non-wiring is a settled, already-flagged gap — not
  something to fix inside this ticket.
- **COMB-296** (`docs/parity_ledger/combat_movement.yaml`, corrected by `TCK-20260824-WOUND-
  HEALING-DECISION`) — documents `wound_healed`/`scar_gained` zero-producer status at the
  observability/event layer. Not directly in this ticket's scope (`TacticalDecisionSystem` reads
  `entity.combat.wounds`/`.scars` directly from state, not via emitted events), but relevant context
  — see Risks below re: the separate event-extractor bug.

## Prior Work

- **`TCK-20260824-WOUND-PENALTY-FORMULA-WIRING`** (done, hotfix): wired
  `WoundService.create_wound()`'s severity-scaled formula into the live `combat.py` infliction path,
  and confirmed `get_effective_stats()` already correctly consumes `atk_penalty`/`def_penalty`/
  `max_hp_penalty` (not `speed_penalty`). This is the direct precondition this ticket depends on —
  confirmed landed and functioning by this session's own read of `combat.py:605-618` and
  `rpg_depth.py:341-389`.
- **`TCK-20260824-WOUND-THRESHOLD-DECISION`** (done, standard): deleted the dead 40%-threshold
  `should_inflict_wound()`/`WOUND_THRESHOLD_RATIO` branch; confirmed no longer present anywhere in
  `rpg_depth.py` (only `create_wound`, `get_wound_stat_penalties`, `get_scar_stat_penalties` remain
  in the `WoundService` class per this session's own read of the file, lines 111-173).
- **`TCK-20260824-WOUND-HEALING-DECISION`** (done, standard, `stored_artifacts/TCK-20260824-WOUND-
  HEALING-DECISION/`): settled wound-permanence decision (no healing, no scar production in
  production), documented in `docs/mechanics/02_combat_laws.md` Section 5 and
  `docs/guidelines/intentional_divergences.md` DEV-005. Its own Completion Summary explicitly names
  this ticket (`TCK-20260824-TACTICAL-WOUND-SCAR-WIRING`) as the best-positioned place to decide
  whether `speed_penalty` wiring belongs here — this investigation's judgment (consistent with the
  task's supplied context) is **no**: that is a stat-computation change (`get_effective_stats()`),
  not a decision-making change, and stays a separate, still-open follow-up.
- No `stored_artifacts/TCK-20260824-WOUND-PENALTY-FORMULA-WIRING/` directory exists (that ticket was
  `hotfix`-tier, which per project convention requires no staging artifacts) — only the ticket file
  itself was available as prior-work evidence for that one.
- `tests/unit/combat/test_engagement_behavior.py` and `tests/unit/social/test_domain_7_social.py`
  establish the exact `V2EntityBuilder` + bare `AuthoritativeState` + `GroupRecord` test pattern this
  ticket's new tests should follow (see Current Behavior above).

## Risks and Open Questions

- **Severity threshold for "sufficient severity" (AC #1) is undefined by the ticket.** The ticket
  says "an active WoundState of sufficient severity" without specifying a numeric cutoff. No
  existing constant in `rpg_depth.py` or `tactical.py` defines a wound-severity-based behavior
  threshold (only the 25% *infliction* threshold in `combat.py`, and the 0.4/0.15 *hp_percent*
  thresholds in `tactical.py` — neither is a wound-severity threshold). The planner must choose a
  concrete value (e.g. `severity >= 0.6`, matching the existing SLASH/CRUSH kind-selection
  threshold in `WoundService.create_wound()`) and state the rationale explicitly; this
  investigation does not resolve it, since inventing a number here would be exactly the kind of
  premature-coordinate collapse the Uncertainty Rule warns against. Flag for the planner, not
  silently assumed.
- **Ally wound/scar severity signal for AC #2 is also unspecified in exact form.** The ticket says
  "considers ally wound/scar severity as an additional signal, not just hp_ratio" — this could mean
  (a) lowering the hp_ratio threshold when a wound/scar is present, (b) adding a wound/scar
  severity check as an independent OR condition alongside the existing `hp_ratio < 0.8`/`< 0.7`
  checks, or (c) a combined weighted score. Existing code has no precedent for combining
  raw-penalty-dict output (`Dict[str, float]` from the aggregators) into a single "severity" scalar
  for this purpose — the planner must decide the exact combination logic.
- **`TCK-20260829-HOTFIX-WOUND-SCAR-EVENT-EXTRACTOR-TUPLE-BLIND`** (found in `tickets/todos/`,
  filed by `TCK-20260824-WOUND-HEALING-DECISION`'s follow-up session, not yet implemented as of this
  investigation): a real bug where `event_extractor.py`'s `isinstance(x, list)` checks (lines
  280-281, 302-303) silently miss wound/scar diffs once state carries tuples (the real apply-path
  shape). This does **not** block this ticket — `TacticalDecisionSystem` reads
  `entity.combat.wounds`/`.scars` directly from `AuthoritativeState`, never through
  `EventExtractor`-emitted events — but is worth naming so nobody mistakenly assumes observability
  events are a viable/necessary path for this ticket's new logic.
- **`ScarState` has no `max_hp_penalty` field**, unlike `WoundState`. Any new tactical logic that
  treats "wound or scar severity" as a single interchangeable concept must account for this
  asymmetry — `get_scar_stat_penalties()` deliberately returns only
  `atk_penalty`/`def_penalty`/`speed_penalty`, no `max_hp_penalty` key at all (confirmed,
  `rpg_depth.py:159-173`). Code that blindly does `penalties["max_hp_penalty"]` on a scar-derived
  dict will `KeyError`.
- **`ScarState` has no `severity` field either** (unlike `WoundState.severity`). "Scar severity" as
  phrased in the ticket (AC #1's "WoundState of sufficient severity" is unambiguous — only wounds
  have `severity`; scars only have penalty magnitudes) must be operationalized via summed
  `atk_penalty + def_penalty + speed_penalty` (or similar), not a nonexistent `.severity` attribute
  — the planner should pick a concrete proxy, e.g. thresholding on
  `get_scar_stat_penalties(scars)`'s summed values, and state it explicitly.

## Anti-Drift Hazards

- **Do not re-derive wound/scar penalty math inline in `tactical.py`.** AC #4 is explicit and
  machine-checkable in spirit: always call `WoundService.get_wound_stat_penalties`/
  `get_scar_stat_penalties`, never hand-sum `w.atk_penalty for w in entity.combat.wounds` or
  similar inline in the new branches.
- **Do not touch `combat.py::_get_wound_infliction()` or `rpg_depth.py::WoundService.create_wound()`
  /`get_wound_stat_penalties`/`get_scar_stat_penalties`.** This ticket is a pure new *consumer*
  inside `tactical.py`; the producer/aggregator pipeline is explicitly out of scope and was already
  hardened by the three prerequisite tickets.
- **Do not wire `speed_penalty` into `get_effective_stats()`** as a "while I'm here" fix — this is
  an explicitly separate, already-flagged follow-up (see Risks/Prior Work), not silently bundled
  into this ticket's decision-making scope.
- **Do not overwrite or reinterpret COMB-268 to also cover the new wound/scar branch.** AC #5
  requires a distinct new entry (or explicit extension note) — collapsing the two would hide the
  fact that COMB-268 (`test_path: null`) still has no real regression test of its own.
- **Do not conflate the two different PROTECTOR guard branches** (`tactical.py:312-331`
  no-hostiles/leader-interacting branch vs. `tactical.py:492-519` hostiles-present
  guard-wounded-ally branch). AC #2 is scoped to the second one; a new test that never populates
  `hostiles` would silently exercise the wrong (already-covered, untouched-by-this-ticket) branch
  and give false confidence.
- **Do not mutate `entity.combat.wounds`/`.scars` or ally state from within `evaluate_entity_intent`
  or any helper it calls.** All reads must stay strictly read-only against the passed-in
  `AuthoritativeState`/`EntityState` objects, consistent with the Core Boundaries rule and the
  existing pattern of every other branch in this function (all of which only ever construct and
  return `EntityUpdate`).
- **Do not let the new wound/scar checks silently change the existing hp_percent<0.4/<0.15
  thresholds' behavior for entities with zero wounds/scars.** AC #1's "earlier/independently of the
  existing hp_percent checks" means the new branch must be additive (an OR condition or an earlier
  early-return), not a replacement of the existing gate — a regression test asserting the old
  `test_retreat_behavior`/hp_percent-only paths still work unchanged is required (see test_plan.md).
