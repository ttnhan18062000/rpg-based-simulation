# Investigation: why trust_history never grows in the gate worlds (read-only, rpg-next a1e4b6f3a)

Probe: `trust_probe.py` (outside src, wraps every writer, changes nothing), seed 42 x 5000 ticks x 3 worlds, pinned kernel, observability default. Raw results in `results/`.

## Verdict
Not a dropped-update bug. Every writer that runs reaches `RelationshipService.process_update` and survives apply (`process_update.entries_after` equals `with_trust_delta` in all 3 worlds). The cause is structural: **no wired writer can raise trust**. Every delta that reaches state is negative.

## 1. Writers
| # | Writer | file:line | Trigger | Wired? |
|---|---|---|---|---|
| W1 | `RelationshipService.process_update` (the only in-tick sink for `SocialUpdate.trust_delta`, clamp -1..1) | src/systems/social_systems/relationships.py:39 | any SocialUpdate with trust_delta, via `SocialPatch.apply` | yes (src/engine/patches.py:569) |
| W2 | party cohesion collapse, `CooperationLearningService.learn(outcome_type="abandoned")` -> trust_delta -0.25 toward the leader | src/domains/cooperation/phase.py:232-252 | `PartyCohesionService.evaluate` returns MEMBER_ABANDONING or LEADER_LOST for a live group | yes, fires |
| W3 | `SocialAppraisalSystem.process_betrayal` (-0.3 - 0.4*salience) | src/systems/social_systems/appraisal.py:414; called src/engine/domain/combat_actions.py:94 | attacker and target share `identity.group_id` (same-party hit) | yes, fires rarely |
| W4 | `CooperationLearningService.learn` outcomes "success" (+0.08), "rescue" (+0.22), "betrayal" (-0.75) | src/domains/cooperation/services.py:456-466 | no caller constructs these `CooperationOutcomeEvent` types (only "abandoned", phase.py:232) | NO, dead branches |
| W5 | `SocialAppraisalSystem.recalibrate_trust` (+/-) | src/systems/social_systems/appraisal.py:200 | only via `StrategicIntelligenceSystem.process_outcome` (intelligence.py:1204), which has no caller in src | NO, dead |
| W6 | campaign importer `SocialMemoryImporter` merges `relationship_scores` into trust_history | src/domains/campaigns/social_memory.py:516 | episode start of a multi-episode campaign | only in campaigns, not in a single run |
| W7 | `source_trust_updates` | src/engine/patches.py:498 | a different field (information-source trust), not trust_history | n/a |
`prune_low_salience` (relationships.py:137) would drop entries but has no caller. No world-gen/compiler seeds trust_history.

## 2. Why nothing reaches it (probe, seed 42, 5000t)
| counter | frontier_living_world | urban_political | crowded_frontier |
|---|---|---|---|
| CooperationPhase.execute calls | 5000 | 5000 | 5000 |
| cooperation decisions (postures) | 69488 | 62682 | 23016 |
| PartyCohesionService.evaluate calls | 2824 | 1616 | 2999 |
| cohesion STABLE / NEEDS_REGROUP / MEMBER_ABANDONING | 2637 / 83 / 104 | 1479 / 81 / 56 | 2846 / 77 / 76 |
| learn() calls (all "abandoned") | 104 | 56 | 76 |
| process_betrayal calls | 8 | 0 | 5 |
| recalibrate_trust / process_outcome calls | 0 | 0 | 0 |
| SocialPatch.apply calls / with trust_delta | 10334 / 196 | 8045 / 78 | 7202 / 137 |
| process_update with trust_delta, sign | 196 neg, 0 pos | 78 neg, 0 pos | 137 neg, 0 pos |
| entries present after apply | 196 | 78 | 137 |
| entities holding any trust_history at tick 5000 | 5 of 55 | 2 of 30 | 11 of 38 |
| final values | -0.62, -1.0 | -1.0 | -0.62, -1.0 |
| bonds (SocialBond) in the world at 5000 | 216 | 208 | 202 |
| groups ever formed | 28 | 20 | 19 |

Blocking condition: **a writer that is never wired** (W4 success/rescue, W5), plus gates that open only on failure (W2, W3). `cooperation_event` is emitted from `last_cooperation_decision`, a posture (SOLO / JOIN_PARTY / REQUEST_HELP ...) chosen each tick; it records a decision, not an outcome, and nothing converts a successful party into a trust gain. Groups do form (19-28) and parties do abandon, so the gate for W2 opens; it writes only negatives.
Inference (not separately probed): W2 re-applies -0.25 every tick a group stays in MEMBER_ABANDONING (104 events but only 5 holder entities), so a few pairs saturate at -1.0.
Findings for the designer: (a) positive trust has no writer in a single episode; (b) W4's dead "success"/"rescue" branches look like the intended positive path; (c) bond sentiment, not trust_history, is what live relationships grow (216 bonds vs 5 trust holders), and most readers prefer bond sentiment, so trust_history is a mostly-dormant parallel store; (d) readers disagree on the missing-key default (0.5 vs 0.0, see 3).

## 3. Readers of trust / allies (a reader is dormant for a trust value when trust_history is empty AND no bond exists; defaults shown)
| Reader | file:line | Rule | Missing default |
|---|---|---|---|
| Grief trigger | src/core/grief_triggers.py:34 (threshold ALLY_TRUST_THRESHOLD=0.30, src/core/social_constants.py:17) | grief when trust >= 0.30 | 0.0 -> DORMANT in single runs (nothing writes >0) |
| Campaign grief (episode boundary) | src/domains/campaigns/orchestrator.py:341 (+ grief_urgency.py:24) | relationship_scores >= 0.30 | 0.0; fed by importer W6 only |
| Party member boost | src/systems/social_systems/party.py:60 | bond sentiment else trust | 0.5 |
| Group objective propagation | src/systems/world_systems/groups.py:242 | propagate if trust >= 0.3 | 0.5 |
| Tactical focus-fire bias | src/engine/tactical.py:388 | bias if trust >= 0.2 | 0.5 |
| Contract appraisal prelude (trust<0.2 refuses), recruitment, trade, team-up, teach, marriage, clan | src/systems/social_systems/appraisal.py:53 | refuses below 0.2 | 0.5 |
| Recruitment cost | src/systems/social_systems/appraisal.py:526 | cost multiplier 1.5 - trust | 0.5 |
| Social contract goal scoring | src/ai/goals/social_contract_scorer.py:110 | utility term | 0.5 |
| Party composition fit | src/systems/social_systems/party_composition.py:126 | bond sentiment else trust | 0.0 |
| Cooperation partner shortlist | src/domains/cooperation/providers.py:69,77 | keeps far candidate only if trust > 0.7 | 0.5 |
| Partner fit | src/domains/cooperation/evaluators.py:140 | max(trust, bond sentiment) | 0.5 |
| Party cohesion: drift (<0.35) and abandon (<0.2) | src/domains/cooperation/services.py:342,408 | | 0.5 |
| Social memory export / events | src/domains/campaigns/social_memory.py:453; src/observability/event_extractor.py:952; event_shapers.py:1543 | | n/a |
| API presenter | src/api/presenters/state_presenter.py:130 | read model | n/a |
Downstream effect: with default 0.5, trust-gated rules behave as neutral-trusting (most gates pass) until a negative event drops a pair; with default 0.0 (grief, party composition) they are closed. So grief is the one rule that is fully dormant in single episodes; the rest run on their 0.5 default or on bond sentiment.
