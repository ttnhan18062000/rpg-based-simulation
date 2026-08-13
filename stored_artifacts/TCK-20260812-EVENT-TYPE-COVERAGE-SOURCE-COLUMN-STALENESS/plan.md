---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260812-EVENT-TYPE-COVERAGE-SOURCE-COLUMN-STALENESS
artifact_type: plan
tags: [observability, documentation, economy]
---

# Implementation Plan — TCK-20260812-EVENT-TYPE-COVERAGE-SOURCE-COLUMN-STALENESS

## Summary

This is a pure documentation-accuracy correction, zero `src/` diff. It corrects the `source`
column of `docs/simulation_quality/event_type_coverage.md` (70 stale rows in §1.1, ~15 duplicate
stale citations in §3.2–§3.9, 1 stale row in §5) from the legacy `event_extractor` label to the
live-default push-shaper terminus (`event_shapers (<ShaperClassName>)`), following the exact
naming convention already established by the `resource_harvested`/`item_crafted` rows
(`docs/simulation_quality/event_type_coverage.md:109-110`, fixed by
`TCK-20260811-HARVEST-CRAFT-EVENT-DERIVATION-REGRESSION`). It also corrects the same stale
`event_extractor.py` citation inside 4 parity-ledger files where sibling entries in the same file
already document the correct shaper terminus, and — per an explicit scope decision below — fixes
`docs/event_ledger/entity.yaml`'s `ENTITY-003`/`ENTITY-007` entries inline rather than deferring a
4th time. All groupings (which shaper owns which `event_type`) were independently re-verified in
Plan phase by grepping every `event_type="..."` literal in `src/observability/event_shapers.py`
(87 literals found) and locating each inside its owning `class`/`def` boundary — full match with
investigation.md's findings, including both flagged tricky cases. Work is organized into batches
by shaper group so each batch is independently gradeable against the test_plan.md spot-check
commands.

## Scope Decisions (resolving the ticket's own Open Questions)

**`docs/event_ledger/entity.yaml` — IN SCOPE, fixed inline (Step 15).** Per CLAUDE.md's
discipline against silently absorbing *or* silently dropping newly-found related work: this is
not new work discovered mid-implementation, it is the exact same staleness class the ticket's own
Scope section already made explicitly conditional ("unless Investigate finds it shares the same
staleness") — Investigate found it does (`entity.yaml:30` `ENTITY-003`, `entity.yaml:58`
`ENTITY-007`, both citing `event_extractor.py` for now-shaper-derived event types). The ticket's
own Request Summary frames this exact staleness class as already flagged-and-deferred twice
before (`TCK-20260807-QUEST-EVENT-PUSH-MIGRATION`, then this ticket's own predecessor). Deferring
a 4th time on the identical fact pattern, for a fix that is mechanically small (2 `evidence`
string edits, different schema but same substance), would repeat the exact failure mode this
ticket exists to close out. Fixing inline is the smaller drift risk.

**§3 Engine Emission Gaps table — corrected, not left frozen (Steps 10-11 fold this into the
per-shaper batches).** §3's own §6 Maintenance Notes call it a "primary expansion surface," not an
archive, and its "resolved by" column makes the identical factual claim as §1.1's `source` column
for the same event types — leaving one corrected and the other stale would be a new
same-doc divergence of the exact kind this ticket exists to eliminate.

## Naming Convention (established precedent, applied verbatim)

- Standard case: `event_shapers (<ShaperClassName>)` — e.g. `event_shapers (CombatShaper)`.
- No owning class (cross-shaper aggregation inside `run_shadow_shapers()`,
  `event_shapers.py:1886-1995`): `event_shapers (run_shadow_shapers)`.
- Every corrected row's `notes` column must retain (or gain, if missing) a short clause stating
  that `event_extractor.py`'s own block is now the flag-gated rollback path, not the live source —
  reuse the exact phrasing already in `resource_harvested`'s row (`event_type_coverage.md:109`):
  *"`event_extractor.py`'s own loop is now the flag-gated (`_push_shapers_active`) rollback path,
  not the live source."* Substitute the correct gate name per registry: `_push_shapers_active`
  (`SHAPER_REGISTRY`, flag `ENABLE_PUSH_EVENT_SHAPERS`) for Combat/Economy/Faction rows;
  `_push_shapers_phase2_active` (`PHASE2_SHAPER_REGISTRY`, flag
  `ENABLE_PUSH_EVENT_SHAPERS_PHASE2`) for Strategy/Progression/WorldDynamics/Social/
  DeferredInstrumentation rows; `_push_shapers_agency_active` (`AGENCY_SHAPER_REGISTRY`, flag
  `ENABLE_PUSH_EVENT_SHAPERS_AGENCY`) for the 2 Agency rows. Do not invent a new phrasing style.
- Cross-domain colocation rows (`cooperation_event`: scored by `SocialScorer` but derived inside
  `StrategyShaper`; `paid_info_changed_goal`: scored by `InformationScorer` but derived inside
  `EconomyShaper`) get one extra parenthetical clause in `notes` flagging the colocation, per
  investigation.md's convention proposal — do not "correct" these to a same-domain shaper name,
  that would introduce a new staleness bug.

## Steps

### Step 1 — §1.1 CombatShaper group (5 rows)
**Files:** `docs/simulation_quality/event_type_coverage.md`
**Change:** Correct the `source` cell for 5 rows to `event_shapers (CombatShaper)`, gate name
`_push_shapers_active` / `ENABLE_PUSH_EVENT_SHAPERS`:
- `hero_death_unrecorded` (line 97 per investigation.md; confirmed class boundary
  `event_shapers.py:108-359` contains `event_type="hero_death_unrecorded"` at line 337)
- `combat_damage` (line 98) — **tricky case:** current value is `CombatDamageEvent`, not literally
  `event_extractor`, but equally stale — that class is only constructed on the flag-gated
  rollback path (`event_extractor.py:451`); the live path builds a plain `SimulationEvent` inside
  `CombatShaper.shape()` (`event_shapers.py:231`, confirmed by direct read). Replace the bare
  `CombatDamageEvent` value with `event_shapers (CombatShaper)`, same as the other 4 rows in this
  batch — do not leave a hybrid value.
- `combat_initiated` (line 99; `event_shapers.py:238`)
- `near_death_survival` (line 100; `event_shapers.py:278`)
- `hazard_drain_applied` (line 143; confirmed `event_shapers.py:347`, inside `CombatShaper`
  108-359, not the adjacent `WorldDynamicsScorer`-scored rows it sits near in the doc — scorer
  column and shaper column are independent, do not conflate)
**Do NOT touch:** `calibration_hits` values (117, 164, 322, 0, 0 respectively), the `scorers`
column, or the extensive `combat_damage` notes about `tactical_modifier`/light-mode suppression —
append only the rollback-path clause, do not rewrite existing prose.
**Verify:** test_plan.md Spot-Check #1 (`hero_death_unrecorded`, `combat_initiated` sampled) and
#2 (`event_type="hero_death_unrecorded"` greps inside `CombatShaper`'s range).

### Step 2 — §1.1 StrategyShaper group (13 rows)
**Files:** `docs/simulation_quality/event_type_coverage.md`
**Change:** Correct `source` to `event_shapers (StrategyShaper)`, gate
`_push_shapers_phase2_active` / `ENABLE_PUSH_EVENT_SHAPERS_PHASE2`, for: `route_selected`(103),
`action_executed`(104), `self_model_updated`(105), `belief_assimilated`(106),
`belief_updated`(107), `cooperation_event`(108), `defer_with_reason`(119),
`route_family_first_use`(120), `lead_certainty_updated`(123), `paid_info_changed_goal`(125),
`belief_stale`(126), `decision_diverged_by_belief`(127), `decision_divergence_detected`(128),
`lead_certainty_changed`(145) — 14 listed here (investigation.md's "13" count undercounts by one;
`lead_certainty_changed` at line 145 is a distinct row from `lead_certainty_updated` at 123 and
was independently confirmed at `event_shapers.py:851`, inside `StrategyShaper`'s 682-950 range —
include it in this batch, do not skip it as a duplicate of `lead_certainty_updated`).
- `cooperation_event`(108): scored by `SocialScorer` but derived inside `StrategyShaper`
  (confirmed `event_shapers.py:824`, inside 682-950) — add the cross-domain colocation
  parenthetical per the Naming Convention section; do not rename to `SocialShaper`.
- `paid_info_changed_goal`(125): scored by `InformationScorer` but derived inside `StrategyShaper`
  (confirmed `event_shapers.py:465`, inside 682-950) — same cross-domain treatment.
- `route_selected`(103)/`action_executed`(104): these two rows already carry an extensive
  dead-writer note (`entity.last_routing_family`'s sole writer deleted by
  `TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE`, re-verified 0 hits by
  `TCK-20260813-SIMQ-ADVENTURE-ROUTING-AGENCY-COGNITION-DRIFT`). The `source` correction is
  orthogonal to the 0-hit fact — apply the same `event_shapers (StrategyShaper)` correction, then
  append a short `"(shaper-side, not extractor-side)"` clarification to the existing note so the
  two facts (stale source path vs. dead upstream writer) don't read as contradictory. Do not
  delete or shorten the existing dead-writer prose.
**Do NOT touch:** `calibration_hits` values (including the historical `20` on
`route_selected`/`action_executed`, explicitly flagged in the doc's own note as stale-but-not-
re-audited — leave that number and its caveat exactly as is), the dead-writer narrative content.
**Verify:** Spot-Check #1 (`route_selected`, `self_model_updated` sampled).

### Step 3 — §1.1 EconomyShaper group (6 rows)
**Files:** `docs/simulation_quality/event_type_coverage.md`
**Change:** Correct `source` to `event_shapers (EconomyShaper)`, gate `_push_shapers_active` /
`ENABLE_PUSH_EVENT_SHAPERS`, for: `shop_transaction`(111), `trade_executed`(112),
`quest_reward_dispensed`(113), `gold_sink_fired`(114), `paid_information_transaction`(115),
`paid_info_transaction`(116). All confirmed present in `EconomyShaper`'s class range
(`event_shapers.py:359-474`; direct literal hits at lines 416, 422, 429, 436, 443, 449). Use
`resource_harvested`/`item_crafted`'s existing row (lines 109-110) as the exact template for
phrasing and rollback-path note.
**Do NOT touch:** `resource_harvested`(109)/`item_crafted`(110) themselves — already correct,
re-verify byte-identical per test_plan.md Spot-Check #4, do not re-edit them. Do not touch the
0-hit calibration counts or the `paid_information_transaction`/`gold_sink_fired` gating notes
(orphaned detector / archetype-blocked) — those are separate, already-tracked gaps.
**Verify:** Spot-Check #1 (`shop_transaction`, `gold_sink_fired` sampled).

### Step 4 — §1.1 FactionShaper group (8 rows)
**Files:** `docs/simulation_quality/event_type_coverage.md`
**Change:** Correct `source` to `event_shapers (FactionShaper)`, gate `_push_shapers_active` /
`ENABLE_PUSH_EVENT_SHAPERS`, for: `alliance_proposed`(136), `resource_seized`(137),
`diplomatic_transition`(164), `alliance_accepted`(165), `territory_ownership_changed`(166),
`faction_tension_delta`(167), `war_declared`(168), `military_conflict_resolved`(169). Confirmed
present in `FactionShaper`'s class range (`event_shapers.py:474-682`; literal hits at 539, 553,
560, 579, 587, 595, 632, 639).
**Do NOT touch:** `faction_trajectory_stagnant`(138) — already correctly reads
`event_shapers (FactionShaper)`, confirm unchanged, do not re-edit. Do not touch
`diplomatic_transition`'s 29-hit calibration note or `faction_tension_delta`'s
"not exercised by the fix" explanation.
**Verify:** Spot-Check #1 (`alliance_proposed`, `diplomatic_transition` sampled).

### Step 5 — §1.1 ProgressionShaper group (7 rows)
**Files:** `docs/simulation_quality/event_type_coverage.md`
**Change:** Correct `source` to `event_shapers (ProgressionShaper)`, gate
`_push_shapers_phase2_active` / `ENABLE_PUSH_EVENT_SHAPERS_PHASE2`, for: `xp_granted`(101),
`level_up`(102), `skill_unlocked`(129), `trait_expressed`(130), `pillar_trait_unlocked`(131),
`progression_conversion_applied`(132), `progression_plateau_detected`(133). Confirmed present in
`ProgressionShaper`'s class range (`event_shapers.py:950-1095`; literal hits at 1015, 1024, 1034,
1041, 1048, 1058, 1078/1086 — two `progression_plateau_detected` emit sites inside the same
class, both still inside the shaper, does not change the `source` value).
**Do NOT touch:** `capability_growth_stalled`(134)/`life_arc_incoherent`(135) — genuinely never
migrated (absent from `event_shapers.py`'s full 87-literal list, confirmed by grep), leave as
`event_extractor`, do not "fix" these.
**Verify:** Spot-Check #1 (`xp_granted`, `progression_plateau_detected` sampled).

### Step 6 — §1.1 WorldDynamicsShaper group (14 rows)
**Files:** `docs/simulation_quality/event_type_coverage.md`
**Change:** Correct `source` to `event_shapers (WorldDynamicsShaper)`, gate
`_push_shapers_phase2_active` / `ENABLE_PUSH_EVENT_SHAPERS_PHASE2`, for:
`demographic_mortality`(95), `demographic_birth`(96), `ecology_cycle_completed`(139),
`spawn_cadence_fired`(140), `threat_evolved`(141), `building_sabotaged`(144),
`region_trauma_delta`(157), `region_ownership_changed`(158), `region_transformed`(159),
`calamity_spawned`(160), `boss_spawned`(161), `narrative_milestone`(162),
`raid_party_spawned`(163), `world_emergence_event`(170). Confirmed present in
`WorldDynamicsShaper`'s class range (`event_shapers.py:1095-1314`; literal hits at 1149, 1158,
1188, 1201, 1211, 1226, 1239, 1246, 1259, 1269, 1282, 1165/1171/1178/1291/1298).
**Do NOT touch:** `node_recharged`(142) and `faction_extinct`(171) — these two are visually
adjacent/interleaved in this table section but belong to a **different** shaper
(`DeferredInstrumentationShaper`) — see Step 7, do not include them in this batch's find/replace.
Do not touch `calamity_spawned`'s or `region_trauma_delta`'s existing hit-count/precondition
narrative.
**Verify:** Spot-Check #1 (`demographic_mortality`, `calamity_spawned` sampled).

### Step 7 — §1.1 DeferredInstrumentationShaper group (3 rows) + §5 (1 row) — tricky case
**Files:** `docs/simulation_quality/event_type_coverage.md`
**Change:** Correct `source` to `event_shapers (DeferredInstrumentationShaper)`, gate
`_push_shapers_phase2_active` / `ENABLE_PUSH_EVENT_SHAPERS_PHASE2`, for:
- `node_recharged`(142, §1.1) — **the ticket's flagged cross-reference hazard.** Confirmed by
  direct read: `event_shapers.py:1375` (`event_type="node_recharged"`) falls inside
  `DeferredInstrumentationShaper`'s class range (`event_shapers.py:1314-1427`), which starts
  *after* `WorldDynamicsShaper` ends at line 1314. Despite sitting in the doc between
  `threat_evolved`(141, WorldDynamicsShaper) and `hazard_drain_applied`(143, CombatShaper — see
  Step 1), this row's correct shaper is neither of its doc-neighbors. Do not group it into Step 6.
- `resource_node_depleted`(156, §1.1) — confirmed `event_shapers.py:1362`, same class range.
- `faction_extinct`(171, §1.1) — confirmed `event_shapers.py:1418`, same class range. (Despite
  the name and `FactionScorer` scoring column, the derivation lives in
  `DeferredInstrumentationShaper`, not `FactionShaper` — do not conflate scorer domain with
  shaper class, same caution as `cooperation_event` in Step 2.)
- `resource_node_regenerated`(§5, line 349) — same shaper class, confirmed `event_shapers.py:1369`.
  §5's table header is also `source`/`reason` (3 columns) — apply the same correction pattern to
  the `source` cell; the `reason` column ("Not a quality signal; node recharge tracked
  separately") is a §5-specific classification field, leave it untouched.
**Do NOT touch:** the `reason` column values anywhere in §5 (only `resource_node_regenerated`'s
`source` cell changes); `faction_extinct`'s "fires only when faction_updates present" note.
**Verify:** Spot-Check #1 (`node_recharged`, `faction_extinct` sampled) and #2's explicit
`node_recharged` grep, which must show it "inside `DeferredInstrumentationShaper`, NOT
`WorldDynamicsShaper`".

### Step 8 — §1.1 SocialShaper group (10 rows)
**Files:** `docs/simulation_quality/event_type_coverage.md`
**Change:** Correct `source` to `event_shapers (SocialShaper)`, gate
`_push_shapers_phase2_active` / `ENABLE_PUSH_EVENT_SHAPERS_PHASE2`, for:
`social_memory_created`(146), `contract_milestone_completed`(147), `group_joined`(148),
`group_expelled`(149), `reputation_delta`(150), `contract_offer_created`(151),
`contract_offer_accepted`(152), `contract_completed`(153), `contract_lapsed`(154),
`contract_expired_offer`(155). Confirmed present in `SocialShaper`'s class range
(`event_shapers.py:1427-1668`; literal hits at 1496, 1503, 1520, 1543, 1575, 1586, 1593, 1601,
1608/1622, 1658).
**Do NOT touch:** `contract_expired_offer`'s 234-hit calibration note.
**Verify:** Spot-Check #1 (`social_memory_created`, `contract_completed` sampled).

### Step 9 — §1.1 AgencyShaper group (2 rows) + run_shadow_shapers row (1 row)
**Files:** `docs/simulation_quality/event_type_coverage.md`
**Change:**
- `commitment_abandoned`(121), `rejection_cascade_tick`(122): correct `source` to
  `event_shapers (AgencyShaper)`, gate `_push_shapers_agency_active` /
  `ENABLE_PUSH_EVENT_SHAPERS_AGENCY`. Confirmed present in `AgencyShaper`'s class range
  (`event_shapers.py:1748-1886`; literal hits at 1823, 1847 — note both carry
  `event_category="strategy"` in source, that is an unrelated field on the emitted event object,
  not evidence against the AgencyShaper class assignment, which is determined by which `class`
  block contains the emit call).
- `conservation_law_verified`(117): correct `source` to `event_shapers (run_shadow_shapers)` —
  not a per-domain shaper class. Confirmed computed directly inside `run_shadow_shapers()`
  (`event_shapers.py:1886-1995`, literal hit at line 1934), as a cross-shaper aggregation over the
  Phase-1 shapers' combined output, gated by `_push_shapers_phase2_active` /
  `ENABLE_PUSH_EVENT_SHAPERS_PHASE2` (the function itself runs inside the Phase-2 gated block).
**Do NOT touch:** any other Agency/Economy row in this pass.
**Verify:** Spot-Check #1 (`commitment_abandoned`, `conservation_law_verified` sampled) and #2's
explicit `conservation_law_verified` grep, which must show it "inside `run_shadow_shapers()`, not
any class".

### Step 10 — §3 duplicate "resolved by" corrections, part 1 (Cognition/Information/Economy/Progression)
**Files:** `docs/simulation_quality/event_type_coverage.md`
**Change:** Apply the same corrected value used in the matching §1.1 row (Steps 2/3/5/9 above) to
each §3 duplicate citation, so the two tables never diverge on the same event_type again:
- §3.2 (line 237): `decision_divergence_detected` → `event_shapers (StrategyShaper)`
- §3.3 (lines 245, 247, 248, 249): `lead_certainty_updated` → `event_shapers (StrategyShaper)`;
  `paid_info_changed_goal` → `event_shapers (EconomyShaper)` (**not** `StrategyShaper` — this row
  is the cross-domain-colocation case from Step 2, keep the parenthetical here too);
  `belief_stale` → `event_shapers (StrategyShaper)`; `decision_diverged_by_belief` →
  `event_shapers (StrategyShaper)`. `lead_contradiction_resolved`(246) stays
  `lead_contradiction.py` — confirmed genuinely not shaper-derived, do not touch.
- §3.4 (lines 257-258): `paid_info_transaction` → `event_shapers (EconomyShaper)`;
  `conservation_law_verified` → `event_shapers (run_shadow_shapers)` — confirmed at line 258 by
  direct read (`| \`conservation_law_verified\` | \`event_extractor.py\` — tick % 50 guard...`).
- §3.6 (lines 274-278): `skill_unlocked`, `trait_expressed`, `pillar_trait_unlocked`,
  `progression_conversion_applied`, `progression_plateau_detected` → all
  `event_shapers (ProgressionShaper)`.
**Do NOT touch:** §3's "All previously listed gaps resolved by ..." framing sentences at the top
of each subsection — only the table cell values change, not the historical attribution prose.
**Verify:** Spot-Check #5 (cross-table pairing check) for `decision_divergence_detected`,
`lead_certainty_updated`, `skill_unlocked`.

### Step 11 — §3 duplicate "resolved by" corrections, part 2 (Faction/Social/World Dynamics)
**Files:** `docs/simulation_quality/event_type_coverage.md`
**Change:**
- §3.7 (lines 286-287): `alliance_proposed`, `resource_seized` → `event_shapers (FactionShaper)`.
- §3.8 (lines 295-296): `social_memory_created`, `contract_milestone_completed` →
  `event_shapers (SocialShaper)`.
- §3.9 (lines 304-307): `ecology_cycle_completed`, `spawn_cadence_fired`, `threat_evolved` →
  `event_shapers (WorldDynamicsShaper)`; `node_recharged` (line 307, confirmed by direct read)
  → `event_shapers (DeferredInstrumentationShaper)` — **same tricky case as Step 7**: this row
  sits in the same §3.9 sub-table as the 3 WorldDynamicsShaper rows immediately above it; do not
  give it the WorldDynamicsShaper value by proximity. `camp_constructed` in the same subsection
  stays `**No engine path.**` — confirmed genuinely unmigrated (no dynamic construction mechanic
  exists), do not touch.
**Do NOT touch:** §3.5's `scenario_objective_progressed` row — confirmed genuinely not
shaper-migrated (absent from the 87-literal `event_shapers.py` grep), stays
`scenario_runtime.py`, no change needed.
**Verify:** Spot-Check #5 (`alliance_proposed`, `social_memory_created`, `ecology_cycle_completed`
sampled — must show the exact same value as their §1.1 counterparts from Steps 4/6/7/8).

### Step 12 — `last_verified` frontmatter bump
**Files:** `docs/simulation_quality/event_type_coverage.md` (frontmatter block, lines 1-7)
**Change:** Update `last_verified: 2026-07-04` (line 6) to this ticket's completion date. Do not
touch `status: authoritative` / `layer: simulation` / `authority: P1` / `audience: developer` —
none of those fields change on a prose-accuracy pass.
**Do NOT touch:** the `**Last updated:**` / `**Previously updated:**` prose lines under the `##
Summary` heading (lines 46+) — those are a separate, hand-maintained changelog convention distinct
from the frontmatter field; add a new one only if the ticket's own convention requires it (it does
not — AC2 only asks for the frontmatter field).
**Verify:** Spot-Check #7 (`head -10 ... | grep last_verified`).

### Step 13 — `docs/parity_ledger/strategic_cognition.yaml` (STRAT-240/241/242)
**Files:** `docs/parity_ledger/strategic_cognition.yaml`
**Change:** Append one clarifying sentence to the `v2_evidence` field of each of the 3 entries
(read in full at plan time — `text`/`status`/`priority`/`test_path` all stay unchanged, only
`v2_evidence` gains a trailing clause):
- `STRAT-240` (`strategic_cognition.yaml:2814-2830`, `v2_evidence` at 2823-2825, covers
  `lead_certainty_updated`)
- `STRAT-241` (`strategic_cognition.yaml:2831-2848`, `v2_evidence` at 2840-2843, covers
  `belief_stale`)
- `STRAT-242` (`strategic_cognition.yaml:2849-2868`, `v2_evidence` at 2860-2862, covers
  `decision_diverged_by_belief`/`decision_divergence_detected`)

Each currently cites only `src/observability/event_extractor.py` with no cross-reference to
`STRAT-247` (same file, `strategic_cognition.yaml:3043-3049`), which already documents that these
exact 4 event types (named verbatim in `STRAT-247`'s text at lines 3046-3048) are available via
the live-default apply-layer `StrategyShaper`. Use the fix pattern already established in this
same file at `STRAT-246`'s `support_boundary` field (lines 3010-3012, 3034-3036): append a clause
naming the live shaper terminus and stating `event_extractor.py`'s block is now the flag-gated
rollback path, e.g.: *"As of the push-shaper migrations (see STRAT-247), this event is also
derived by the live-default apply-layer `StrategyShaper`
(`src/observability/event_shapers.py`); `event_extractor.py`'s block above is now the flag-gated
(`_push_shapers_phase2_active`) rollback path, not the sole terminus."*
**Do NOT touch:** `status: verified`, `priority: P1`, `test_path` (unchanged — the extractor-path
tests remain valid and passing regardless of which path is named in prose), `divergence_note`, or
`STRAT-242`'s existing `support_boundary` (dungeon_crawl archetype-block note) — append only.
**Other writers to this file:** `STRAT-243`-`STRAT-249` and all other entries in this file are
untouched by this ticket; no other in-flight ticket in this session edits
`strategic_cognition.yaml`, confirmed by this session's own ticket queue (`tickets/inprogress/`
contains only this ticket). No ordering/race concern — single sequential edit.
**Verify:** `python3 -c "import yaml; yaml.safe_load(open('docs/parity_ledger/strategic_cognition.yaml'))"`
must not raise. (`validate_frontmatter.py` does NOT apply here — this file has no `---`-delimited
frontmatter block by design, a plain YAML list, and correctly FAILs against it even pre-fix;
confirmed by Review, per CLAUDE.md's rule against treating a gate-tool's spurious FAIL as something
to "fix" by adding an unrequested, wrong-schema frontmatter block. The YAML-parse check above is the
correct and sufficient verification for this file.)

### Step 14 — `docs/parity_ledger/world_dynamics.yaml` (WORLD-108/109) and
`docs/parity_ledger/social_narrative.yaml` (SOC-233 through 238) and
`docs/parity_ledger/progression.yaml` (PROG-114/115/116)
**Files:** `docs/parity_ledger/world_dynamics.yaml`, `docs/parity_ledger/social_narrative.yaml`,
`docs/parity_ledger/progression.yaml`
**Change:** Same append-only `v2_evidence` fix pattern as Step 13, applied per-file:

*`world_dynamics.yaml`:*
- `WORLD-108` (lines 1329-1345, `v2_evidence` at 1338-1340, `ecology_cycle_completed`) → append
  clause naming `event_shapers (WorldDynamicsShaper)` as the live terminus.
- `WORLD-109` (lines 1346-1375, `v2_evidence` at 1360-1364, covers `spawn_cadence_fired`,
  `node_recharged`, `threat_evolved` in one entry) → append a clause that is careful **not** to
  give `node_recharged` the same shaper name as its two siblings in this entry:
  `spawn_cadence_fired`/`threat_evolved` are `WorldDynamicsShaper`-derived, but `node_recharged`
  is `DeferredInstrumentationShaper`-derived (same tricky case as Steps 7/11) — name both classes
  explicitly in the appended clause, do not write one blanket "WorldDynamicsShaper" claim covering
  all three event types in this single-entry fix.

*`social_narrative.yaml`:*
- `SOC-233` (lines 2924-2965, `v2_evidence` at 2945-2958, covers `cooperation_event` +
  `reputation_delta`) → append: `cooperation_event` is now `StrategyShaper`-derived (cross-domain
  colocation, see `SOC-239` at `social_narrative.yaml:3105-3113`); `reputation_delta` is now
  `SocialShaper`-derived (see `SOC-240` at `social_narrative.yaml:3131-3139`). Name both shapers
  explicitly — do not collapse to one class name for both event types.
- `SOC-234` (lines 2967-2989, `v2_evidence` at 2978-2981, `contract_completed`/`contract_lapsed`/
  `contract_expired_offer`) → append clause naming `event_shapers (SocialShaper)` (all 3 named in
  `SOC-240`'s list).
- `SOC-235` (lines 2991-3031, `v2_evidence` at 3008-3015, `diplomatic_transition`/
  `alliance_accepted`/`territory_ownership_changed`/`faction_tension_delta`/`war_declared`/
  `military_conflict_resolved`/`faction_extinct`) → append clause naming
  `event_shapers (FactionShaper)` for all except `faction_extinct`, which is
  `DeferredInstrumentationShaper`-derived (same tricky case as Step 7) — name it separately in the
  appended clause, do not fold it into the FactionShaper claim just because it sits in the same
  ledger entry as the other 6 FactionShaper-derived events.
- `SOC-236` (lines 3032-3063, `v2_evidence` at 3049-3055, `alliance_proposed`/`resource_seized`/
  `paid_info_transaction`/`conservation_law_verified`/`scenario_objective_progressed`) → append
  clause: `alliance_proposed`/`resource_seized` → `FactionShaper`; `paid_info_transaction` →
  `EconomyShaper`; `conservation_law_verified` → `run_shadow_shapers`;
  `scenario_objective_progressed` stays `scenario_runtime.py` (confirmed genuinely unmigrated) —
  do not add a shaper clause for this one event type in the entry.
- `SOC-237` (lines 3086-3103, `v2_evidence` at 3095-3098, `social_memory_created`) → append clause
  naming `event_shapers (SocialShaper)` (see `SOC-240`).
- `SOC-238` (lines 3065-3084, `v2_evidence` at 3075-3079, `contract_milestone_completed`) →
  append clause naming `event_shapers (SocialShaper)` (see `SOC-240`).

*`progression.yaml`:*
- `PROG-114` (lines 1207-1222, `v2_evidence` at 1215-1217, `skill_unlocked`) → append clause
  naming `event_shapers (ProgressionShaper)` (see `PROG-117` at `progression.yaml:1262-1270`).
- `PROG-115` (lines 1223-1240, `v2_evidence` at 1232-1234, `trait_expressed`/
  `pillar_trait_unlocked`) → append clause naming `event_shapers (ProgressionShaper)`.
- `PROG-116` (lines 1241-1261, `v2_evidence` at 1252-1255, `progression_conversion_applied`/
  `progression_plateau_detected`) → append clause naming `event_shapers (ProgressionShaper)`.

**Do NOT touch:** `status`, `priority`, `test_path`, `divergence_note`, `support_boundary` fields
on any of these 10 entries — append-only to `v2_evidence`. Do not touch `SOC-239`/`SOC-240`/
`WORLD-110`+/`PROG-117` themselves (already correct, used only as citation targets).
**Other writers to these files:** no other in-flight ticket touches
`world_dynamics.yaml`/`social_narrative.yaml`/`progression.yaml` this session (confirmed —
`tickets/inprogress/` contains only this ticket). `faction.yaml`, `combat_movement.yaml`,
`town_resource.yaml`, `infrastructure.yaml`, `substrate.yaml` are explicitly out of scope for this
step — investigation.md confirmed those 5 files already correct, do not open them for edits.
**Verify:** `python3 -c "import yaml; [yaml.safe_load(open(f)) for f in ['docs/parity_ledger/world_dynamics.yaml','docs/parity_ledger/social_narrative.yaml','docs/parity_ledger/progression.yaml']]"`
must not raise. (`validate_frontmatter.py` does NOT apply — same reasoning as Step 13: these files
have no frontmatter block by design; the YAML-parse check above is correct and sufficient. Also note
`validate_frontmatter.py` only ever accepts a single positional path — the multi-file invocation
originally drafted here would fail with `unrecognized arguments` before even reaching that question,
confirmed by Review.)

### Step 15 — `docs/event_ledger/entity.yaml` (ENTITY-003, ENTITY-007)
**Files:** `docs/event_ledger/entity.yaml`
**Change:** This file uses an `evidence` field (prose), not a `source` table cell — schema is
different from `event_type_coverage.md` (confirmed by reading the file's own header comment,
`entity.yaml:1-10`, and the two target entries directly).
- `ENTITY-003` (`entity.yaml:27-32`, `evidence` at line 30): currently
  `"src/observability/event_extractor.py (multiple sites); docs/simulation_quality/
  event_type_coverage.md §1.1"` for `event_types: [combat_damage, combat_initiated,
  near_death_survival, combat_kill (-> entity_killed), hazard_drain_applied,
  combat_hard_law_violation]` (line 31). Verified per-event-type against `event_shapers.py`:
  `combat_damage`/`combat_initiated`/`near_death_survival`/`hazard_drain_applied` are
  `CombatShaper`-derived (Step 1); `entity_killed` (the `combat_kill` translation target) is also
  `CombatShaper`-derived (confirmed `event_shapers.py:307`, inside 108-359); `combat_hard_law_violation`
  is **not** among the 87 `event_type="..."` literals found anywhere in `event_shapers.py` —
  confirmed still `event_extractor`-only, do not reclassify it. Append a clause to `evidence`:
  *"6 of these event types (`combat_damage`, `combat_initiated`, `near_death_survival`,
  `hazard_drain_applied`, plus `entity_killed`, the `combat_kill` translation target) are also
  available via the live-default apply-layer `CombatShaper`
  (`src/observability/event_shapers.py`); `combat_hard_law_violation` remains
  `event_extractor.py`-only, not shaper-migrated."*
- `ENTITY-007` (`entity.yaml:55-60`, `evidence` at line 58): currently cites
  `event_extractor.py` for `event_types: [skill_unlocked, trait_expressed, pillar_trait_unlocked,
  level_up, entity_role_changed, entity_faction_changed, recipe_learned,
  skill_cooldown_started]` (line 59). Verified: `skill_unlocked`/`trait_expressed`/
  `pillar_trait_unlocked`/`level_up` are `ProgressionShaper`-derived (Step 5);
  `entity_role_changed`/`entity_faction_changed`/`recipe_learned`/`skill_cooldown_started` are
  confirmed genuinely unmigrated (absent from the 87-literal grep, matches investigation.md's
  "Genuinely NOT migrated" list) — leave those 4 as `event_extractor`-only. Append a clause to
  `evidence` naming the `ProgressionShaper` migration for the first 4 event types only.
**Do NOT touch:** `status`, `mutation_source`, `event_types` list contents, or `notes` on either
entry — `evidence` field only, append-only. Do not touch any other `ENTITY-*` entry in this file
(`ENTITY-001`, `ENTITY-004`-`ENTITY-006`, `ENTITY-008`+ etc.) — confirmed none of those cite
`event_extractor.py` for a shaper-migrated event type per investigation.md's scope.
**Other writers to this file:** no other in-flight ticket touches `entity.yaml` this session.
**Verify:** Spot-Check #6 (`grep -n -A2 "id: ENTITY-003\|id: ENTITY-007" docs/event_ledger/entity.yaml`);
`python3 -c "import yaml; yaml.safe_load(open('docs/event_ledger/entity.yaml'))"` must not raise.
(`validate_frontmatter.py` does NOT apply — same reasoning as Steps 13/14: `entity.yaml` has no
`---`-delimited frontmatter block by design, confirmed by Review to genuinely FAIL against it
pre-fix for that structural reason, unrelated to this ticket's edit. Do not "fix" this by adding a
frontmatter block — that would be an unrequested, wrong-schema change to a file whose format is
correct as-is.)

### Step 16 — Full verification pass
**Files:** none (verification only)
**Change:** Run every command in test_plan.md's "Spot-Check Commands" section (#1-#8) and the
"Anti-Drift Test Guards" section, in order. All 8 spot-checks and both guards (`git diff --stat`
showing 0 `src/` files; 0 `calibration_hits` value changes) must pass before Verify phase. Also
run `python3 tools/validate_frontmatter.py docs/simulation_quality/event_type_coverage.md`
**only** — this is the one touched file with a real `---`-delimited frontmatter block, and it
must pass cleanly. **Corrected during Review**: `validate_frontmatter.py` accepts exactly one
positional path (no `nargs="+"`), so a multi-file invocation fails immediately with
`unrecognized arguments`, and even run singly it correctly FAILs against
`entity.yaml`/any `docs/parity_ledger/*.yaml` file since none of those carry a frontmatter block
by design — that FAIL would be a pre-existing structural fact, not a defect this ticket
introduces, and must never be "fixed" by adding an unrequested frontmatter block. Do not run
`validate_frontmatter.py` against any file besides `event_type_coverage.md`; rely on the
YAML-parse checks in Steps 13-15 for the other 5 files instead. Additionally run `python3
tools/parity_index.py build` (the real schema/structural validation entrypoint for
`docs/parity_ledger/*.yaml`, per test_plan.md's correction) after Steps 13-14 land — a clean build
with no errors on the touched entries confirms schema conformance beyond plain YAML parsing.
**Do NOT touch:** nothing — this is a read-only verification step. If any spot-check fails, return
to the relevant Step above and fix the underlying row, do not adjust the spot-check command to
make it pass (CLAUDE.md hard rule against editing to satisfy a gate).
**Verify:** self — this step's commands are the verification.

## Scope Guards

- Zero changes to `src/observability/event_extractor.py`, `src/observability/event_shapers.py`,
  `src/engine/kernel.py`, or any other `src/` file. This is a documentation-accuracy ticket only.
  `git diff --stat` after Implement must show 0 files under `src/`.
- Zero changes to `calibration_hits` numeric values anywhere in `event_type_coverage.md` (Steps
  1-11 touch only `source`/"resolved by" cells and the specific `notes` clarifications named per
  step).
- Zero changes to `status`, `priority`, or `test_path` on any parity-ledger entry touched in Steps
  13-14 — this is prose-only `v2_evidence` correction, not a status/verification change.
- Zero changes to `docs/parity_ledger/faction.yaml`, `combat_movement.yaml`,
  `town_resource.yaml`, `infrastructure.yaml`, `substrate.yaml` — investigation.md confirmed all 5
  already correct; opening them for edit is out of scope.
- Zero fix to the `0`-hit calibration counts for any ECONOMY (or any other domain) row — separate,
  already-tracked routing/calibration gap (`ENABLE_ADVENTURE_ROUTING` default-off), not a
  doc-staleness issue, explicitly out of scope per the ticket.
- Zero change to `route_selected`/`action_executed`'s dead-writer gap, the `combat_kill`
  translation-table reachability finding (investigation.md's Risk/Open-Question #3), or any other
  adjacent finding investigation.md surfaced but did not scope in — those are future-ticket
  material, not this ticket's work.
- Do not rename `cooperation_event`/`paid_info_changed_goal` to a same-domain-as-scorer shaper
  name (`SocialShaper`/`InformationScorer`-matching) — the actual code deliberately colocates
  these elsewhere; "fixing" this by analogy introduces a new staleness bug.
- Do not give `node_recharged` or `faction_extinct` the `WorldDynamicsShaper`/`FactionShaper`
  value by visual proximity to their doc-neighbors — both are `DeferredInstrumentationShaper`.

## Dependency Map

Steps 1-9 (§1.1 shaper-group batches) are fully independent of each other — each touches a
disjoint set of table rows. Steps 10-11 (§3 duplicates) should run **after** Steps 1-9 complete,
since they copy the corrected value from the matching §1.1 row rather than re-deriving it
independently — this avoids re-doing the shaper-lookup work and guarantees §1.1/§3 agreement by
construction rather than by a separate cross-check. Step 12 (frontmatter bump) is independent, can
run any time, but is logically last for `event_type_coverage.md` since it certifies the whole file
as re-verified. Steps 13-14 (parity ledger) are independent of Steps 1-12 and of each other (4
separate files). Step 15 (entity.yaml) is independent of all others but logically benefits from
Steps 1 and 5 having already confirmed the CombatShaper/ProgressionShaper class ranges. Step 16
(verification) depends on all of Steps 1-15 being complete.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| Every `event_type_coverage.md` row whose live derivation moved to a push-shaper has its `source` column corrected, verified against current `SHAPER_REGISTRY` contents | Steps 1-9 (§1.1, 70 rows), Steps 10-11 (§3, ~15 duplicate rows), Step 7 (§5's `resource_node_regenerated`) | test_plan.md Spot-Check #1, #2, #5 |
| Doc's `last_verified` frontmatter field updated to the date of this ticket's completion | Step 12 | test_plan.md Spot-Check #7 |
| Any `docs/parity_ledger/*.yaml` entry found to share the same stale-terminus claim during cross-check is corrected in the same session | Step 13 (strategic_cognition.yaml), Step 14 (world_dynamics.yaml, social_narrative.yaml, progression.yaml) | Step 13/14's own YAML-parse + `validate_frontmatter.py` verification; no dedicated pytest exists for prose parity |
| No behavior/code change — diff is `docs/` only | All steps (doc-only by construction) | test_plan.md Anti-Drift Test Guards' `git diff --stat` check (Step 16) |

## Anti-Drift Notes

- **Do not conflate "derives" with "delivers".** All 4 gating flags default `ON`, so in the
  default configuration every corrected row is both derived AND delivered by its shaper — but the
  `source` column's job is naming the derivation path, and `event_extractor.py`'s branches are not
  deleted; they remain the real, tested rollback path when a flag is set OFF. Every corrected row
  must retain the rollback-path clause (see Naming Convention), not just swap the bare value.
- **`node_recharged` is `DeferredInstrumentationShaper`, not `WorldDynamicsShaper`** — confirmed
  by direct class-boundary read (`event_shapers.py:1314` starts `DeferredInstrumentationShaper`,
  after `WorldDynamicsShaper` ends at line 1314's boundary), not by doc proximity. This applies in
  4 separate places: §1.1 line 142, §3.9 line 307, and `WORLD-109`'s `v2_evidence` (Step 14).
- **`faction_extinct` is `DeferredInstrumentationShaper`, not `FactionShaper`** — same class of
  mistake, confirmed `event_shapers.py:1418`. Applies in §1.1 line 171 and `SOC-235`'s
  `v2_evidence` (Step 14).
- **`cooperation_event`/`paid_info_changed_goal` cross-domain colocation is intentional** — do not
  "fix" these to a same-domain shaper name; introduces a new bug of the exact class this ticket
  exists to remove.
- **`combat_damage`'s current value (`CombatDamageEvent`) is a stale class name, not the literal
  string `event_extractor`** — a naive string-match find/replace for `event_extractor` would miss
  this row entirely. Step 1 handles it explicitly.
- **No behavior change anywhere.** This is a pure prose/table-value edit across `docs/` only.
  `route_selected`/`action_executed`'s dead-writer gap, the `combat_kill` translation-table
  reachability finding, and any `0`-hit calibration count are explicitly out of scope — do not
  "also fix" them even though they are visible in the same rows being edited.
- **`make knowledge-index-update` must run after all doc edits** per CLAUDE.md's After Work rule
  (docs/ files changed) — easy to forget on a "just a table edit" ticket; this is a Finalize-phase
  action, not part of Steps 1-16, but must not be skipped.
- **`docs/REGISTRY.yaml` and `tickets/working_log.csv`** are regenerated/appended automatically by
  the Finalize phase, not by any step in this plan — do not manually edit either file as part of
  Implement.

## Deviations (recorded during Implement)

- **Step 2's `paid_info_changed_goal` gate name.** Step 2's batch header instructs "Correct
  `source` to `event_shapers (StrategyShaper)` ... for: ... `paid_info_changed_goal`(125) ...",
  implying gate `_push_shapers_phase2_active` (the Strategy-group gate per the Naming Convention
  section). Step 10 already carries the corrected shaper name for this same row
  (`event_shapers (EconomyShaper)`, explicitly flagged "not StrategyShaper") but does not name a
  gate. Direct re-verification against `src/observability/event_shapers.py:441-469` (inside
  `EconomyShaper`, 359-474) and `src/observability/event_extractor.py:684-753` (the
  `_push_shapers_active`-gated `intent_results` loop that contains the extractor-side
  `paid_info_changed_goal` block at line 749) confirmed the correct gate is
  `_push_shapers_active`, matching `EconomyShaper`'s group gate, not `_push_shapers_phase2_active`.
  Implemented using `event_shapers (EconomyShaper)` / `_push_shapers_active` throughout (§1.1 row
  125 and its §3.3 duplicate), consistent with Step 10's explicit shaper-name correction and the
  ground truth in source. No other step's citations required correction — all other shaper-class
  and gate-name mappings verified byte-identical to the plan's stated values via direct
  `event_shapers.py` re-read before writing each batch.
