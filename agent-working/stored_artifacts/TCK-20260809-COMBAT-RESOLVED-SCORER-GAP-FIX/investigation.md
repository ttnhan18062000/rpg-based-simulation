---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260809-COMBAT-RESOLVED-SCORER-GAP-FIX
artifact_type: investigation
tags: [combat, simulation-quality]
---

# Investigation — TCK-20260809-COMBAT-RESOLVED-SCORER-GAP-FIX

## Context search (mandatory step)
`search_docs` for the COMBAT pillar scoring contract surfaced
`docs/simulation_quality/quality_scoring_contract.md` §5 COMBAT (the real, authoritative pillar
definition) directly. Cross-referenced against `docs/simulation_quality/event_type_coverage.md`
(§3 Engine Emission Gaps) and `docs/audits/D20_simq_quality_status_review.md` (line 262, which
already disclosed `combat_resolved`/`attrition_threshold_crossed` as dead code from an earlier
audit pass), and `docs/parity_ledger/combat_movement.yaml`/`infrastructure.yaml` (both already
carry an entry disclosing this same gap from the original push-shaper migration epic).

## Re-confirmed: `combat_resolved` has zero real producers
`CombatScorer.EVENT_TYPES` (`src/simulation_quality/scorers/combat.py:16-24`) includes
`"combat_resolved"`, and `score()` (lines 71-72) has a real, ready handler:
`if et == "combat_resolved": return _rec(self.weights["combat_resolved"], ...)` — **no payload
fields required**, a flat `+3` on event-type match alone. Direct grep of `event_type ==
"combat_resolved"` / `"combat_resolved"` string literals across all of `src/` confirms **zero
real construction of a `SimulationEvent`/`CombatKillEvent`/etc. with this event_type anywhere** —
matching `CombatShaper`'s own class docstring (`event_shapers.py:96`), already self-disclosed as
"dead code, never emitted by any path in this repo; nothing exists to migrate" from the original
push-shaper migration epic (`TCK-20260806-...`). No translation-table entry exists either
(`quality_scoring_contract.md`'s own "Translation table status: Complete" note) — this is a pure
`engine_emission_gap`, the scorer side is fully ready and waiting.

## Real semantic mapping, re-confirmed against the pillar contract's own wording
`quality_scoring_contract.md` line 657: `"Combat resolved (clear winner, loser retreats or
dies)"`. Cross-referenced against `combat_engagement_ended`'s 4 real outcomes
(`TCK-20260809-COMBAT-LIFECYCLE-OBSERVABILITY`, `src/observability/event_shapers.py`):
- **`KILL`** — loser dies. Unambiguous match.
- **`ESCAPED`** — loser (the evading entity) successfully retreats. Unambiguous match — this is
  the literal case the contract's own wording describes ("loser retreats").
- **`CAUGHT_FLEEING`** — a real opportunity attack landed on a fleeing entity, but the entity did
  not necessarily die and the engagement is not necessarily over (the fleeing entity may still be
  alive and moving); no "clear winner" is established by this outcome alone. Already separately
  scored via `combat_damage`'s own `tactical_variety`/base signal. **Not** a semantic match.
- **`PURSUIT_ABANDONED`** — the chaser gave up (`LEASH_RETURN`/`STALEMATE_BREAK`); this is a real,
  inconclusive disengagement, not a "clear winner, loser retreats" scenario — no side "won," the
  engagement simply fizzled without resolution. **Not** a semantic match; arguably closer to the
  pillar's own `combat_unresolved` penalty (`−8`) than to `combat_resolved` — but reusing that
  penalty here is out of this ticket's own proportionate scope (it targets "combat events emitted
  with zero lifecycle resolution," a different real condition) and not pursued.

## `combat_engagement_started` — confirmed NOT a promotion candidate
Fires on the exact same real gate as the already-scored `combat_initiated` (`combat_active`, +2,
`quality_scoring_contract.md` line 656) — both fire together, from the same
`hp_delta < 0 and real_combat is not None and prior_hp == prior_max_hp and new_hp < prior_max_hp`
condition (`event_shapers.py`, confirmed via direct re-read). Promoting it to scored would
double-count the identical real-world event under a second event_type — no new signal, just
inflated pillar volume for the same underlying occurrence. Documented here as a real, deliberate
decision (matching this repo's own `ENABLE_ADVENTURE_ROUTING`/AGENCY DA-ruling precedent), not
left as an unresolved question.

## `attrition_threshold_crossed` — confirmed out of scope, not a trivial shared fix
`CombatScorer`'s own handler (lines 95-100+) reads `payload.get("threshold", 0.0)` and compares
against population-wide attrition-rate gates (`attrition_90pct_by_tick`/`attrition_50pct_by_tick`)
— a fundamentally different computation (aggregate population attrition over the whole run) than
a single combat-engagement outcome. Would require a new, separate population-tracking mechanism,
not an additive emission alongside `combat_engagement_ended`. Confirmed genuinely separate, not
bundled into this ticket per its own Out of Scope.

## Real corpus reachability, honestly checked before implementing
Per this session's own established discipline: `combat_engagement_ended(KILL)` is confirmed to
fire at real, non-zero volume in `dungeon_crawl` (1 real kill observed in the prior tickets' own
2000-tick re-verification). `ESCAPED` fired 5 times in `urban_political` in earlier
re-verification runs (though under corpus-default flags without the identity-resolver/pursuit
fixes active at the time — real re-verification needed at Test phase with all 3 fixes combined).
Both are real, reachable outcomes, not purely-theoretical.

## Docs Requiring Update
- `docs/simulation_quality/event_type_coverage.md` — correct `combat_resolved`'s classification
  from `engine_emission_gap`/unlisted to `scored`, now that a real producer exists.
- `docs/simulation_quality/quality_scoring_contract.md` — no change needed to the pillar
  definition itself (the contract's own wording already matches what gets implemented); a
  footnote citing the real producer may be added for traceability.
