---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260812-EVENT-TYPE-COVERAGE-SOURCE-COLUMN-STALENESS
phase: done
date: 2026-08-12
tags: [observability, documentation, economy]
---

# TCK-20260812-EVENT-TYPE-COVERAGE-SOURCE-COLUMN-STALENESS

## Title
`docs/simulation_quality/event_type_coverage.md`'s `source` column is stale for every
push-shaper-migrated event row — still lists `event_extractor` where live derivation moved to a
`run_shadow_shapers()`-delivered shaper

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P3

## Request Summary
Filed as the required follow-up ticket for a deferral made in
`TCK-20260811-HARVEST-CRAFT-EVENT-DERIVATION-REGRESSION`'s Verify phase (DoD condition 11 — a
known, deliberately-deferred gap must have an explicit ticket reference, not just be noted in
staging artifacts). That ticket's own Verify phase separately fixed the `resource_harvested`/
`item_crafted` rows directly (the 2 rows its own investigation named) to satisfy a distinct DoD
static check (`docs_to_update_coverage`) — this ticket's scope has been narrowed accordingly to
cover the *remaining* stale rows only.

`docs/simulation_quality/event_type_coverage.md` (status: authoritative, `last_verified:
2026-07-04`) has a `source` column that names which code path derives each scored event type. Since
`TCK-20260806-PUSH-CUTOVER-COMBAT-ECONOMY-FACTION` (commit `11b83f37`) and its sibling migration
tickets, live derivation for many of these event types moved from `EventExtractor.extract()`'s
legacy per-domain loops to `run_shadow_shapers()`-delivered shaper classes in
`src/observability/event_shapers.py` (`EconomyShaper`, and equivalents for COMBAT/FACTION, plus
later QUEST/AGENCY-domain migrations referenced in that ticket's investigation) — with the old
`event_extractor.py` loops now flag-gated dead-by-default rollback paths (`_push_shapers_active` /
`_push_shapers_phase2_active` / `_push_shapers_quest_active` / `_push_shapers_agency_active`, all
defaulting `"ON"` i.e. shaper-path-live).

The doc's `source` column was never updated at any of these migration points. As of this filing,
`resource_harvested`/`item_crafted` (lines 109-110) have already been corrected directly by
`TCK-20260811-HARVEST-CRAFT-EVENT-DERIVATION-REGRESSION`'s own Verify phase (the 2 rows its own
investigation named). It still reads stale `event_extractor` for the remaining ECONOMY-domain rows
(`shop_transaction`, `trade_executed`, `quest_reward_dispensed`, `gold_sink_fired`,
`paid_information_transaction`, `paid_info_transaction`, `conservation_law_verified` — lines
~111-117 as of this filing) — and per
`TCK-20260811-HARVEST-CRAFT-EVENT-DERIVATION-REGRESSION`'s investigation, this same staleness was
already independently flagged-not-fixed once before, by `TCK-20260807-QUEST-EVENT-PUSH-MIGRATION`'s
own investigation, for the COMBAT/FACTION/QUEST/AGENCY rows too. This is the **third** time this
gap has been surfaced without being corrected in full.

## Scope
- Investigate-phase: enumerate every remaining row in `event_type_coverage.md` whose event type is
  now derived (in the default/live configuration) by a `SHAPER_REGISTRY` class in
  `src/observability/event_shapers.py` rather than `event_extractor.py`'s legacy loops —
  `resource_harvested`/`item_crafted` (lines 109-110) are already fixed; do not assume the remaining
  ECONOMY-row list above is complete; re-derive it from current source.
- Correct the `source` column for every such row to name the real live path (e.g. `event_shapers
  (EconomyShaper)` or equivalent naming convention established in this doc's existing table, to be
  decided at Investigate/Plan time) while noting the flag-gated legacy `event_extractor.py` path
  remains the rollback mechanism, not the terminus.
- Cross-check `docs/parity_ledger/*.yaml` entries whose `test_path`/`support_boundary` also cite
  `event_extractor.py` as the terminus for any of these same event types (the exact class of
  staleness `TCK-20260811-HARVEST-CRAFT-EVENT-DERIVATION-REGRESSION`'s Parity phase found and fixed
  twice within a single ledger entry, `STRAT-246`) — this doc and the parity ledger should not
  diverge on the same factual claim.

## Out of Scope
- Any change to the actual event-derivation code (`event_extractor.py`, `event_shapers.py`,
  `kernel.py`) — this is a documentation-accuracy ticket only, no behavior change.
- Fixing the `0`-hit calibration counts themselves for any ECONOMY row — those are a separate,
  already-tracked routing/calibration gap (`ENABLE_ADVENTURE_ROUTING` default-off, per
  `STRAT-246`'s `support_boundary`), not a doc-staleness issue.
- `docs/event_ledger/entity.yaml` — a separate, complementary ledger per this doc's own "See also"
  note; not in scope unless Investigate finds it shares the same staleness.

## Acceptance Criteria
- [x] Every `event_type_coverage.md` row whose live derivation moved to a push-shaper has its
      `source` column corrected, verified against current `SHAPER_REGISTRY` contents, not assumed
      from this ticket's own preliminary ECONOMY-row list
- [x] Doc's `last_verified` frontmatter field updated to the date of this ticket's completion
- [x] Any `docs/parity_ledger/*.yaml` entry found to share the same stale-terminus claim during
      cross-check is corrected in the same session
- [x] No behavior/code change — diff is `docs/` only

## Related Tickets
- TCK-20260811-HARVEST-CRAFT-EVENT-DERIVATION-REGRESSION (the ticket that deferred this gap and
  filed this follow-up per DoD condition 11)
- TCK-20260807-QUEST-EVENT-PUSH-MIGRATION (the first ticket to flag this same staleness, for
  COMBAT/FACTION/QUEST/AGENCY rows, without fixing it)
- TCK-20260806-PUSH-CUTOVER-COMBAT-ECONOMY-FACTION (the migration that introduced the
  ECONOMY/COMBAT/FACTION shaper-delivery path this doc never caught up to)
- TCK-20260813-OBSERVABILITY-IMPORT-BOUNDARY-STALE-OR-VIOLATED (OPEN — filed from this ticket's own
  Document-Update phase; a separate finding while correcting `docs/guides/observability.md`'s
  event_extractor/shaper description, this doc's stated `src/observability/` import-boundary rule
  is contradicted by `event_shapers.py`'s real imports — see that ticket for detail)

## Related Docs
- docs/simulation_quality/event_type_coverage.md
- docs/parity_ledger/strategic_cognition.yaml

## Related Stored Artifacts
- stored_artifacts/TCK-20260811-HARVEST-CRAFT-EVENT-DERIVATION-REGRESSION/ (where this staleness
  was most recently re-confirmed and deferred, with reasoning for the deferral)

## Related Code Areas
- src/observability/event_shapers.py (SHAPER_REGISTRY, per-domain shaper classes)
- src/observability/event_extractor.py (legacy flag-gated rollback loops)
- docs/simulation_quality/event_type_coverage.md

## Assumptions / Open Questions
- The exact naming convention for the corrected `source` column value (e.g. whether to name the
  specific shaper class, or a more general "event_shapers (push path)" label) is not pre-decided —
  Plan phase should pick something consistent with the doc's existing conventions.
- Whether every COMBAT/FACTION/QUEST/AGENCY row flagged by `TCK-20260807-QUEST-EVENT-PUSH-
  MIGRATION`'s own investigation is still stale today (vs. partially fixed since) is not verified
  here — Investigate must re-check current doc state, not assume the prior ticket's finding still
  holds unchanged.

## Implementation Notes
Implemented the approved plan's 16 steps in full, re-verifying every shaper-class row grouping
against current `src/observability/event_shapers.py` (`grep -n "^class \|event_type=\""`) before
writing, rather than trusting the plan's citations blindly:

- **Steps 1-9** (§1.1 `source` column, ~70 rows across CombatShaper, StrategyShaper,
  EconomyShaper, FactionShaper, ProgressionShaper, WorldDynamicsShaper,
  DeferredInstrumentationShaper, SocialShaper, AgencyShaper, and the `run_shadow_shapers()`-derived
  `conservation_law_verified` row) corrected `source` to `event_shapers (<ShaperClassName>)` and
  appended the rollback-path clause to each row's `notes`, using the correct gate name per shaper
  (`_push_shapers_active` for Combat/Economy/Faction, `_push_shapers_phase2_active` for
  Strategy/Progression/WorldDynamics/Social/DeferredInstrumentation, `_push_shapers_agency_active`
  for Agency). Handled both flagged tricky cases: `combat_damage`'s stale `CombatDamageEvent`
  class-name value (not the literal string `event_extractor`), and `node_recharged`/
  `faction_extinct` being `DeferredInstrumentationShaper`-derived despite doc-table proximity to
  `WorldDynamicsShaper`/`FactionShaper` rows. Left `resource_harvested`/`item_crafted`/
  `faction_trajectory_stagnant`/`capability_growth_stalled`/`life_arc_incoherent` untouched
  (already correct or genuinely unmigrated).
- **Deviation from plan (caught during re-verification, not silently worked around):** plan Step 2
  grouped `paid_info_changed_goal` under the StrategyShaper batch header ("Correct `source` to
  `event_shapers (StrategyShaper)` ... for: ... `paid_info_changed_goal`(125) ...") and initially
  paired it with the `_push_shapers_phase2_active` gate. Direct read of `event_shapers.py:441-469`
  confirmed this event is actually emitted inside `EconomyShaper` (359-474), not `StrategyShaper`
  (682-950) — the plan's own Step 10 already carried the correct shaper name
  (`event_shapers (EconomyShaper)`, explicitly flagged "not StrategyShaper") but left the gate name
  unresolved. Used `event_shapers (EconomyShaper)` with gate `_push_shapers_active` (confirmed via
  `event_extractor.py:684`, the same `_push_shapers_active`-gated `intent_results` loop that houses
  `paid_info_changed_goal`'s extractor-side block at line 749) — consistent with Step 10's explicit
  correction and the ground truth in source.
- **Steps 10-11** (§3 "resolved by" duplicates, ~15 rows) copied the Step 1-9-corrected value for
  each matching event_type, guaranteeing §1.1/§3 agreement by construction. Left
  `lead_contradiction_resolved`, `scenario_objective_progressed`, and `camp_constructed` untouched
  (confirmed genuinely not shaper-migrated).
- **Step 12** bumped `last_verified` frontmatter from `2026-07-04` to `2026-08-13`.
- **Step 13** appended a clarifying sentence (mirroring sibling entry STRAT-247's established
  phrasing, and the STRAT-246 `support_boundary` precedent) to `v2_evidence` on STRAT-240/241/242
  in `docs/parity_ledger/strategic_cognition.yaml` — append-only, no other field touched.
- **Step 14** applied the same append-only `v2_evidence` pattern to WORLD-108/109
  (`world_dynamics.yaml`), SOC-233 through 238 (`social_narrative.yaml`), and PROG-114/115/116
  (`progression.yaml`), each mirroring its file's sibling shaper-summary entry (WORLD-110+,
  SOC-239/240, PROG-117 respectively). Correctly kept `node_recharged` (WORLD-109) and
  `faction_extinct` (SOC-235) named as `DeferredInstrumentationShaper`-derived separately from
  their sibling `WorldDynamicsShaper`/`FactionShaper` event types within the same ledger entry, per
  the plan's explicit anti-drift note. `faction.yaml`, `combat_movement.yaml`, `town_resource.yaml`,
  `infrastructure.yaml`, `substrate.yaml` were not opened.
- **Step 15** appended a clause to `evidence` on ENTITY-003/ENTITY-007 in
  `docs/event_ledger/entity.yaml`, naming the CombatShaper/ProgressionShaper migration for the
  now-shaper-derived event types while explicitly leaving `combat_hard_law_violation`,
  `entity_role_changed`, `entity_faction_changed`, `recipe_learned`, and `skill_cooldown_started`
  as `event_extractor.py`-only (confirmed genuinely unmigrated, absent from the source's 87
  `event_type="..."` literals).
- **Step 16** ran all 8 spot-checks and both anti-drift guards from test_plan.md, plus
  `validate_frontmatter.py` (event_type_coverage.md only) and `parity_index.py build`. All passed —
  see Test Summary.

## Test Summary
No `src/` changes, so no pytest suite is at risk — this is a doc-only ticket per its own
Out-of-Scope. Verification ran the full spot-check/guard set from `test_plan.md` instead of
`pytest`, all passing:
- Spot-Check #1 (18 sampled event_types across all shaper groups): every `source` cell reads
  `event_shapers (<ShaperClassName>)` or `event_shapers (run_shadow_shapers)`, no stale
  `event_extractor`/`CombatDamageEvent` values remain.
- Spot-Check #2: `hero_death_unrecorded` confirmed inside `CombatShaper` (108-359);
  `node_recharged` confirmed inside `DeferredInstrumentationShaper` (1314-1427), NOT
  `WorldDynamicsShaper`; `conservation_law_verified` confirmed inside `run_shadow_shapers()`
  (1886+), not any per-domain class.
- Spot-Check #3: all 4 gating flags (`ENABLE_PUSH_EVENT_SHAPERS`,
  `ENABLE_PUSH_EVENT_SHAPERS_PHASE2`, `_QUEST`, `_AGENCY`) confirmed still default `"ON"`.
- Spot-Check #4: `resource_harvested`/`item_crafted` confirmed unchanged
  (`event_shapers (EconomyShaper)`, pre-existing correct value).
- Spot-Check #5: cross-table pairing confirmed for `decision_divergence_detected`,
  `lead_certainty_updated`, `skill_unlocked`, `alliance_proposed`, `social_memory_created`,
  `ecology_cycle_completed` — §1.1 and §3 agree on the same shaper name for each.
- Spot-Check #6: `entity.yaml`'s ENTITY-003/ENTITY-007 entries confirmed present and edited.
- Spot-Check #7: `last_verified: 2026-08-13` confirmed in frontmatter.
- Spot-Check #8 / row-level regression check: a Python diff of every `calibration_hits` value for
  all 81 §1.1/§1.2/§1.3 event_type rows (old vs. new via `git show HEAD:...`) found **0
  mismatches** — every numeric hit count byte-identical to pre-edit.
- Anti-Drift Guard 1: `git diff --stat HEAD | grep -E '^\s*src/'` → no match, confirmed 0 `src/`
  files touched.
- Anti-Drift Guard 2: covered by the Spot-Check #8 row-level diff above (0 calibration_hits
  changes).
- `python3 tools/validate_frontmatter.py docs/simulation_quality/event_type_coverage.md` →
  `OK: 1 file(s) checked — no violations` (run against this one file only, per plan's explicit
  instruction not to run it against `entity.yaml` or any `parity_ledger/*.yaml` file).
- `python3 -c "import yaml; yaml.safe_load(...)"` on all 5 touched non-frontmatter YAML files
  (`strategic_cognition.yaml`, `world_dynamics.yaml`, `social_narrative.yaml`, `progression.yaml`,
  `entity.yaml`) → all parsed cleanly.
- `python3 tools/parity_index.py build` → `"status": "ok"`, `"missing_v2_evidence": 0`, clean
  build across all `docs/parity_ledger/*.yaml` shards (2012 entries, 9 shards).
- `make knowledge-index-update` run after all doc edits (docs/ files changed).

## Files Changed
- docs/simulation_quality/event_type_coverage.md (184 changed lines: §1.1 `source`/`notes`
  corrections for ~70 rows across Steps 1-9; §3 "resolved by" corrections for ~15 duplicate rows,
  Steps 10-11; §5's `resource_node_regenerated` `source` cell, Step 7; `last_verified` frontmatter
  bump, Step 12)
- docs/parity_ledger/strategic_cognition.yaml (append-only `v2_evidence` fix on STRAT-240/241/242,
  Step 13)
- docs/parity_ledger/world_dynamics.yaml (append-only `v2_evidence` fix on WORLD-108/109, Step 14)
- docs/parity_ledger/social_narrative.yaml (append-only `v2_evidence` fix on SOC-233 through 238,
  Step 14)
- docs/parity_ledger/progression.yaml (append-only `v2_evidence` fix on PROG-114/115/116, Step 14)
- docs/event_ledger/entity.yaml (append-only `evidence` fix on ENTITY-003/ENTITY-007, Step 15)
- docs/parity_ledger/infrastructure.yaml (Parity phase: append-only ADDENDUM to INFRA-242's
  `support_boundary` — investigation.md's cross-check of this file only looked for domain-aggregate
  cutover entries and missed this individual citation, which still named `event_extractor.py` as
  the terminus for `resource_harvested`/`item_crafted`/`trade_executed`/`shop_transaction`; corrected
  to name `EconomyShaper` as the live terminus, original root-cause finding preserved unchanged)
- docs/guides/observability.md (Document-Update phase: corrected the "Key source files" table,
  "Adding a new event type" walkthrough, and "Architecture boundary" note's mechanism description
  to reflect the shaper-based live path alongside the legacy extractor path — the same factual axis
  this ticket's other 6 files corrected, found in this forward-looking contributor guide during the
  final doc sweep. Surfaced a separate, real finding while correcting this file: the doc's own
  stated `src/observability/` import-boundary rule appears contradicted by `event_shapers.py`'s
  real imports from `src/domains/`/`src/systems/`, with no existing test enforcing the stated rule
  — not fixed here (adjudicating/fixing an architecture-boundary question is outside a doc
  correction's mandate), filed as `TCK-20260813-OBSERVABILITY-IMPORT-BOUNDARY-STALE-OR-VIOLATED`.)

## Completion Summary
Corrected ~85 stale `source`/citation values across 6 `docs/` files that still named the legacy
`event_extractor.py` per-domain loops as the live derivation path for event types whose actual
live-default derivation moved to `run_shadow_shapers()`-delivered shaper classes in
`src/observability/event_shapers.py` during the 2026-08-06/07/08 push-shaper cutover tickets. This
was the third surfacing of this exact staleness class (after `TCK-20260807-QUEST-EVENT-PUSH-
MIGRATION` and `TCK-20260811-HARVEST-CRAFT-EVENT-DERIVATION-REGRESSION`), both of which flagged but
deferred the fix; this ticket closes it out in full, including the previously-deferred
`docs/event_ledger/entity.yaml` corrections (resolved as in-scope per the plan's explicit Scope
Decision, to avoid a fourth deferral on the identical fact pattern). Zero `src/` changes, zero
`calibration_hits` value changes, zero `status`/`priority`/`test_path` changes on any touched
parity-ledger entry — verified by an 81-row automated diff plus the full spot-check/guard suite
from test_plan.md, all passing.
