# SimQ Event Gap — Ticket Sequence

## Epic Context
Calibration (TCK-20260628-SIMQ-E7-CALIBRATE) found 0 events scored: engine emits
~10 event types; SimQ scoring contract §5 requires ~83. Gap has two layers:
1. Translation gap (~10 events already emitted but wrong names)
2. Emission gap (~73 events never emitted from engine phases)

Parity entry: SIMQ-CALIBRATED-001 (status: missing) in docs/parity_ledger/infrastructure.yaml.

## Execution Order

Must be done **in this order**:

1. `TCK-20260629-SIMQ-EVENT-TRANSLATE` — **P0/hotfix** — Translation table in QualityHub.
   Unblocks calibration immediately. No engine changes. ~83 events → ~10 actually scored
   after this, covering NARRATIVE (quest events), COGNITION (strategic project events),
   and COMBAT (kill events).

2. `TCK-20260629-SIMQ-EMIT-STATE-DIFF` — **P1/standard** — Extend EventExtractor for
   COMBAT (combat_initiated, near_death_survival), PROGRESSION (xp_granted, level_up),
   ECONOMY (resource_node events), WORLD (demographic events). State diff — no phase hooks.

3. `TCK-20260629-SIMQ-EMIT-AGENCY` — **P1/standard** — Hook PP-12/13/14/15 for AGENCY
   events (action_executed, defer_with_reason, route_selected, etc.).

4. `TCK-20260629-SIMQ-EMIT-COGNITION` — **P1/standard** — Hook PP-03/04/26/30 for
   COGNITION and INFORMATION events (belief_updated, lead_certainty_changed, etc.).

5. `TCK-20260629-SIMQ-EMIT-WORLD` — **P2/standard** — Hook WD-01 through WD-15 for all
   WORLD dynamics events (calamity, boss, ecology, spawn, demographics, etc.).

6. `TCK-20260629-SIMQ-EMIT-ECONOMY` — **P2/standard** — Hook PP-07/21/24/25/27 for ECONOMY
   events (resource_harvested, item_crafted, trade_executed, quest_reward_dispensed, etc.).

7. `TCK-20260629-SIMQ-EMIT-SOCIAL-FACTION` — **P2/standard** — Hook PP-05/08/09/10/11/18/
   23/34/35/36 for SOCIAL and FACTION events.

8. `TCK-20260629-SIMQ-EMIT-NARRATIVE` — **P2/standard** — Wire NarrativeLedger to EventRecorder;
   hook PP-23/PP-33/ScenarioRuntimeService for NARRATIVE events.

## After all tickets done
- Re-run `tools/calibrate_simq.py` for all 8 canonical scenarios
- Populate `tests/simulation_quality/fixtures/grade_anchors.json`
- Tune `config/simulation_quality/grade_thresholds.yaml` if needed
- Update SIMQ-CALIBRATED-001 parity entry to `status: verified`
