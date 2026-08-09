---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260809-COMBAT-TACTICAL-VARIETY-SCORER-GAP-FIX
phase: open
date: 2026-08-09
tags: [combat, simulation-quality]
---

# TCK-20260809-COMBAT-TACTICAL-VARIETY-SCORER-GAP-FIX

## Title
Surface `CombatUpdate.trace`'s real per-attack tactical-modifier data into `combat_damage`'s
`tactical_modifier` payload field, activating the currently-dead `tactical_variety` COMBAT-pillar
signal — the real, precise form of the user's own thread #1 ("per-attack tactical trace")

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Direct continuation of the user's own thread #1 request ("we need combat initial reason... in-
combat mechanism later"), explicitly deferred by `TCK-20260809-COMBAT-LIFECYCLE-OBSERVABILITY`
and flagged as low-value "until real attacks actually execute at volume" — now true, after this
session's own identity-resolver and pursuit-tracking fixes produced real, if still low-volume,
combat.

Investigating this surfaced the same class of finding as the immediately-prior
`TCK-20260809-COMBAT-RESOLVED-SCORER-GAP-FIX`: `CombatScorer.score()`'s own `combat_damage`
handler (`src/simulation_quality/scorers/combat.py:77-82`) already reads
`payload.get("tactical_modifier")` and scores `tactical_variety` (+1) the first time each unique
modifier name is ever seen in a run — a real, ready, already-designed signal. But **zero
producers anywhere in `src/` ever populate `tactical_modifier`** (confirmed via direct grep) —
this scoring branch has been permanently dead since it was written, undisclosed until now.

Separately, `CombatResolutionSystem.calculate_tactical_multipliers()`
(`src/engine/combat.py:52-107`) already computes a real, rich per-attack trace dict every single
attack: `HIGH_GROUND`, `FLANKING`, `SURROUNDED`, `COVER_REDUCTION`, `SHATTER`, `EXHAUSTION`,
`STAMINA_EXHAUSTION`, `BOND_SYNERGY` (matching `docs/mechanics/02_combat_laws.md` §2's own
documented modifier table, plus `STAMINA_EXHAUSTION` which isn't in that table — worth checking
during Investigate whether that's a doc gap). This trace is stored on `CombatUpdate.trace` but
never read by `src/observability/` anywhere (confirmed via grep) — the exact "computed but
discarded" finding this whole thread traces back to.

## Scope
1. **Investigate**: re-confirm the `tactical_modifier` emission gap and the real trace field
   list against current source; check whether `STAMINA_EXHAUSTION` missing from
   `02_combat_laws.md`'s own documented table is a real doc gap worth a one-line fix alongside
   this ticket (small, same-subsystem, discovered during the same investigation — matching this
   session's own established precedent for bundling adjacent, small, disclosed findings).
2. **Plan**: design how `combat_damage`'s existing payload gets a real `tactical_modifier` value
   when `CombatUpdate.trace` has one or more real modifier keys active — a single attack can have
   multiple simultaneously active modifiers, but the scorer's own contract expects one string per
   event; decide a real, deterministic selection rule (not arbitrary).
3. **Implement**: the minimal wiring in `event_shapers.py`'s `combat_damage` construction.

## Out of Scope
- Building a brand-new, separate "per-attack trace" event type from scratch — rejected in favor
  of reusing the already-designed, already-scored `combat_damage`/`tactical_variety` contract,
  matching the `combat_resolved` sibling ticket's own precedent (reuse over invention).
- `REWARD_SOURCE`/`REWARD_CATEGORY`/`WOUND_INFLICTED`/`FINAL_ATK_MULT`/`FINAL_DEF_MULT` — real
  trace keys but not "tactical modifiers" in the mechanics-bible sense (reward classification,
  wound tracking, and aggregate multipliers respectively, not a discrete tactical condition) —
  excluded from the `tactical_modifier` selection.
- Any change to `calculate_tactical_multipliers()`'s own real combat-modifier logic — purely
  additive observability on top of already-computed data.

## Acceptance Criteria
- [x] investigation.md re-confirms the `tactical_modifier` emission gap and the real trace field
      list against current source
- [x] A concrete, deterministic selection rule for which modifier populates `tactical_modifier`
      when multiple are simultaneously active is designed and justified (mechanics-bible table
      order)
- [x] `combat_damage` carries a real `tactical_modifier` value when the underlying attack had one
- [x] `docs/simulation_quality/event_type_coverage.md`/`quality_scoring_contract.md` corrected
- [x] Real corpus re-verification: **confirmed working** — `combat_damage`/`tactical_modifier`
      are sparse/run-to-run timing-variable at this corpus scale (matching `combat_damage`'s own
      already-known sparsity), but 2 of 3 clean re-runs showed a real, correct
      `tactical_modifier="STAMINA_EXHAUSTION"` — not just unit-tested, genuinely observed live.
- [x] Scoped pytest passes — 1021 passed, 6 skipped, zero regressions

## Related Tickets
- TCK-20260809-COMBAT-RESOLVED-SCORER-GAP-FIX (DONE, same session — the sibling fix this ticket
  directly mirrors: a real, ready scorer signal with zero producers, fixed by wiring already-
  computed data into an already-existing event's payload)
- TCK-20260809-COMBAT-LIFECYCLE-OBSERVABILITY (DONE, same session — deferred this exact thread)
- TCK-20260809-COMBAT-HOSTILE-PAIRS-NEVER-ENGAGE, TCK-20260809-COMBAT-PURSUIT-PER-TICK-TRACE
  (DONE, same session — the 2 fixes that made real combat volume exist to evaluate this against)

## Related Docs
- `docs/mechanics/02_combat_laws.md` §2 (Tactical Modifiers — the authoritative mechanics table)
- `docs/simulation_quality/quality_scoring_contract.md` §5 COMBAT (`tactical_variety` row)

## Related Stored Artifacts
None yet — will be created at
`staging_artifacts/TCK-20260809-COMBAT-TACTICAL-VARIETY-SCORER-GAP-FIX/` during implementation.

## Related Code Areas
- `src/engine/combat.py` (`CombatResolutionSystem.calculate_tactical_multipliers`, the real trace
  computation — reference only, not touched)
- `src/observability/event_shapers.py` (`CombatShaper.shape()`, where `combat_damage` is
  constructed — where the wiring lands)
- `src/simulation_quality/scorers/combat.py` (`CombatScorer`, the already-real, already-ready
  `tactical_variety` handler — not modified)

## Assumptions / Open Questions
- The real, deterministic tie-break rule for multiple simultaneously-active modifiers is left to
  Plan phase judgment, informed by whichever ordering (mechanics-bible table order, trace dict
  insertion order, or a magnitude-based rule) is most defensible and simplest to justify.

## Implementation Notes
- `src/observability/event_shapers.py` — added `_TACTICAL_MODIFIER_ORDER` (the mechanics-bible
  §2 modifier order) and `_select_tactical_modifier(trace)`, a small, pure helper that returns
  the first real modifier key present in a `CombatUpdate.trace` dict, checked in that order.
  Wired into the existing `combat_damage` construction site: `tactical_modifier` is included in
  the payload only when a real modifier is present (omitted entirely otherwise — matches
  `CombatScorer`'s own `if modifier and ...` handling of absence).
- Deliberately excludes `FINAL_ATK_MULT`/`FINAL_DEF_MULT` (aggregate multipliers, not a discrete
  condition), `REWARD_SOURCE`/`REWARD_CATEGORY` (reward classification), `WOUND_INFLICTED`
  (wound tracking) — all real `CombatUpdate.trace` keys, none a tactical modifier per the
  mechanics bible's own definition.
- `STAMINA_EXHAUSTION` missing from `docs/mechanics/02_combat_laws.md` §2's own summary table
  investigated and confirmed NOT a real documentation gap — it's fully documented in the more
  detailed, authoritative `docs/mechanics/damage_formula_contract.md`; `02_combat_laws.md` is
  just a summary table, not the sole source of truth. Not touched.
- Chose mechanics-bible table order (not trace-dict insertion order, which happens to match
  today but isn't guaranteed to stay that way) as the deterministic tie-break for attacks with
  multiple simultaneously-active modifiers — traceable directly to the authoritative doc, not an
  implicit code-ordering dependency.

## Test Summary
- 4 new unit tests in `tests/unit/observability/test_event_shapers.py`
  (`test_combat_damage_carries_tactical_modifier_when_active`,
  `test_combat_damage_tactical_modifier_absent_when_no_trace`,
  `test_combat_damage_tactical_modifier_picks_mechanics_bible_order_when_multiple_active`,
  `test_combat_damage_tactical_modifier_excludes_non_modifier_trace_keys`) — all pass (42/42 in
  that file).
- Full scoped re-run: `tests/unit/observability/ tests/simulation_quality/test_combat_scorer.py`
  — 1021 passed, 6 skipped, zero regressions.
- Real corpus re-verification (2000-tick live `Kernel.tick_once()` loop, corpus-default flags,
  `dungeon_crawl_seed42`, 3 clean re-runs to characterize real, honest variance): `combat_damage`
  itself is sparse and run-to-run timing-variable at this corpus scale (0, 1, 1 occurrences
  across the 3 runs — a pre-existing condition of `combat_damage`'s own already-known sparsity,
  not something this ticket needs to or can fix), but **2 of 3 runs showed a real, correct
  `tactical_modifier="STAMINA_EXHAUSTION"`** on the fired `combat_damage` event — the fix is
  confirmed genuinely working live, not just unit-tested.

## Files Changed
- `src/observability/event_shapers.py` — `_select_tactical_modifier()` helper,
  `tactical_modifier` wiring in `combat_damage`.
- `tests/unit/observability/test_event_shapers.py` — 4 new tests; extended `_real_combat_upd()`
  builder with a `trace` parameter.
- `docs/simulation_quality/event_type_coverage.md` — `combat_damage`'s own §1.1 row updated.
- `docs/simulation_quality/quality_scoring_contract.md` — added a real producer citation to the
  COMBAT pillar's own `tactical_variety` row.
- `docs/parity_ledger/combat_movement.yaml` — COMB-306.

## Completion Summary
Closed the user's own thread #1 ("per-attack tactical trace") with the same precise,
reuse-over-invention pattern established by the immediately-prior `combat_resolved` fix:
`tactical_variety`, the COMBAT pillar's own already-designed "tactical discovery" signal, had a
real, ready scorer handler but zero producers, while `CombatResolutionSystem` was already
computing a rich per-attack modifier trace on every attack and discarding it. Wired the two
together via `combat_damage`'s own existing payload, with a deterministic,
mechanics-bible-traceable tie-break rule for attacks with multiple active modifiers. Confirmed
genuinely working in a real, live corpus run (not just synthetic tests) — `STAMINA_EXHAUSTION`
observed correctly on 2 of 3 clean re-runs. This closes out both of the user's own originally-
requested threads (#1 per-attack trace, #3 pillar-scoring) from earlier in this session, on top
of the deeper combat-volume investigation chain (#2) already completed.
