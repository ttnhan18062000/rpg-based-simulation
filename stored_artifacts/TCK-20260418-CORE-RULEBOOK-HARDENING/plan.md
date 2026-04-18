# Final Verification Audit Plan

This plan outlines the steps for a comprehensive verification of the **Combat and Movement Overhaul** work, ensuring that all tickets, artifacts, logs, and tests are perfectly synced and consistent with the "Definition of Done".

## User Review Required

> [!IMPORTANT]
> This audit will update the `working_log.csv` and move the remaining Milestone 3 sub-ticket to `tickets/done/`. I will also perform a final, consolidated test run.

## Proposed Changes

### Records Synchronization

#### [MODIFY] [working_log.csv](file:///home/vboxuser/Work/rpg-based-simulation/tickets/working_log.csv)
- Append missing entries for the 2026-04-18 session:
  - `TCK-20260418-TEST-STABILITY-HARDENING`
  - `TCK-20260418-CORE-RULEBOOK-HARDENING`
  - `TCK-20260418-MOV-CONGESTION`
  - `TCK-20260418-COMBAT-MOVEMENT-CORRECTION`

#### [MODIFY] [TCK-20260418-MOV-CONGESTION.md](file:///home/vboxuser/Work/rpg-based-simulation/tickets/inprogress/TCK-20260418-MOV-CONGESTION.md)
- Check off the acceptance criteria checkboxes.
- Move to `tickets/done/`.

#### [MODIFY] [task.md](file:///home/vboxuser/.gemini/antigravity/brain/a92667f6-289c-4046-bf7a-597387f0c0e1/task.md)
- Final check-off of all 7 milestones and verification steps.

#### [MODIFY] [walkthrough.md](file:///home/vboxuser/.gemini/antigravity/brain/a92667f6-289c-4046-bf7a-597387f0c0e1/walkthrough.md)
- Ensure the walkthrough summarizes the entire project accurately.

---

## Verification Plan

### Automated Tests
- Run the following test suites to confirm 100% stability across all overhaul components:
  - `pytest tests/arena/` (Harness & Observability)
  - `pytest tests/movement/test_congestion_milestone_3.py` (Movement AI)
  - `pytest tests/engine/test_quiet_tick_integrity.py` (Rulebook & Lifecycle)

### Manual Verification
- Confirm that no files remain in `tickets/inprogress/` related to this task.
- Confirm `working_log.csv` and `working_log.csv` are in parity.
