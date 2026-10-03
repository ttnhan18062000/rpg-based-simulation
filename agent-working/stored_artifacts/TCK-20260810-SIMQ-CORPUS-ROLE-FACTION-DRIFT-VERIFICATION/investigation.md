---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260810-SIMQ-CORPUS-ROLE-FACTION-DRIFT-VERIFICATION
phase: investigate
date: 2026-08-10
tags: [simulation-quality, calibration, corpus]
---

# Investigation — TCK-20260810-SIMQ-CORPUS-ROLE-FACTION-DRIFT-VERIFICATION

## 1. Real cause(s) confirmed

Two distinct, evidence-backed mechanisms explain the SOCIAL/ECONOMY/PROGRESSION/COGNITION/AGENCY/
COMBAT drift left unresolved by the precursor `simq-audit` run (`SIMQ-AUDIT-20260810T032558Z`),
all traced back to `TCK-20260808-MONSTER-ROLE-MISTAGGING-INVESTIGATION` (SUB-384):

**(a) PROGRESSION — direct, traced mechanism.** `src/engine/combat_rewards.py`'s
`CombatRewardClassificationService._CLASSIFICATIONS` is keyed by `EntityRole` (confirmed via
direct source read: `EntityRole.MONSTER -> RewardCategory.MONSTER_KILL, xp_multiplier=10, ...`).
`src/simulation_quality/scorers/progression.py`'s `EVENT_TYPES` includes `"xp_granted"` as a
scored event. Before SUB-384's fix, monsters mistagged as non-MONSTER role received a different
(effectively default/zero) reward classification on defeat; after the fix, they correctly resolve
to `MONSTER_KILL`, changing real `xp_granted` amounts and hence PROGRESSION's score. This closes
the disclosed-but-unverified downstream-consumer item from SUB-384's own completion notes.

**(b) SOCIAL/ECONOMY/COGNITION/AGENCY/COMBAT (remaining) — cascading behavioral change.**
`grep -n "role\|faction\|EntityRole\|Faction\." src/simulation_quality/scorers/{social,economy,progression}.py`
returns zero matches — none of these scorers read role/faction directly. The mechanism is
indirect: SUB-384 changes which entities are correctly detected as hostile and eligible for
combat from tick 1 onward. This changes death/survival timing and population composition
throughout the run's deterministic RNG-consumption stream, cascading into every pillar's own
event production even though the scorers never touch role/faction fields. This is the same
class of effect already established this session for COMB-304 ("plausible deterministic
butterfly-effect consequence in a system where this fix changes many entities' individual
trajectories").

Every world showing unexplained drift (`urban_political`, `frontier_living_world`,
`highland_traverse`, `hero_guild_routing`, `simq_routing_test`, plus two `urban_political_selfmodel_*`
probe variants found while regenerating a guard-test fixture) was confirmed via
`data/worlds/{name}/resolved/compile_context.json` to contain real `legacy_roles`/`legacy_factions`
monster-archetype entries — i.e. every drifted world genuinely has SUB-384-affected content.

## 2. 2026-08-07 watchdog-throttle hypothesis — directly checked, ruled out

Per the Acceptance Criteria's explicit requirement (not just citing the D06 F6 precedent):
ran `tools/evaluate_simq.py --scenario urban_political_seed42_500t` three independent times
today, capturing stdout/stderr. All three runs show the watchdog mechanism firing repeatedly and
early (`Tick 25 exceeded budget: 42.29ms vs limit 27.57ms` — earlier than the documented ~300-320
tick onset — continuing through tick 497, dozens of `WatchdogTrip` CRITICAL alerts per run). Despite
this, all three runs produced a bit-identical SOCIAL score (18.39, 3295 events). Since the watchdog
mechanism is wall-clock/system-load driven (real non-determinism per D06 F6's own description),
identical output across independent runs despite active, repeated trips is decisive evidence this
mechanism does **not** explain today's SOCIAL drift. Directionally, today's finding is also opposite
D06 F6's 2026-08-07 case (COMBAT scores jumping up vs. that session's COMBAT-dropping-to-dormant
finding) — confirmed not the same phenomenon.

## 3. Corpus-wide prevalence

The full unscoped `make simq-full-audit-full` was not re-run to completion a second time (already
confirmed to time out at 590s during the precursor audit — a real instance of the project's chronic
tick-budget-exceeded condition, now tracked separately as task #129 / a follow-up ticket). Instead,
prevalence was established via the authoritative `_within_band`/`_format_score_failures` functions
from `tests/simulation_quality/test_grade_regression.py` run directly against the fresh
`quality_report.json` files the precursor audit's partial run already regenerated (47 reports across
~15 worlds), plus 3 additional scenarios regenerated during this ticket's own work
(`urban_political_selfmodel_execution_probe_seed42_200t`, `urban_political_selfmodel_probe_seed42_200t`
— found while fixing a guard-test fixture gap; `urban_political_seed42_500t` — reproducibility check).
This covers the full `FAST_ANCHOR_KEYS` set; the `SLOW_ANCHOR_KEYS` (1000t/2000t) tier was not
in scope for this ticket (already covered by the separate `TCK-20260710-SIMQ-ANCHOR-RELIABILITY-VERIFY`
reliability pass) and is `-m slow`-marked, excluded per CLAUDE.md's testing rule.

## 4. Recommendation

Recalibrate `grade_anchors.json` for every confirmed-cause key (see Implementation Notes for full
list). Every remaining fast-tier pytest failure after recalibration carries a pre-existing
`[known tick_budget: ...]` annotation in `test_grade_regression.py`'s own annotation dict —
already-documented, accepted noise unrelated to SUB-384 — left untouched, not force-anchored.
