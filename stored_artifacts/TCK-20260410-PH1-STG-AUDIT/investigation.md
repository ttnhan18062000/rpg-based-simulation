# Investigation - Strategic Design Shift Audit

## Sources Scanned
- `src/core/models/strategy.py`: Confirmed core models exist with correct typing.
- `src/core/aspects/mind.py`: Confirmed `strategic` field integration.
- `src/actions/base.py`: Confirmed `StrategicUpdate` intent model.
- `src/systems/gameplay/action_system.py`: Confirmed authoritative dispatch and merge logic.
- `tests/core/test_strategy_models.py`: Confirmed structural foundation tests pass.
- `tests/ai/test_strategic_biasing.py`: Confirmed Phase 2 appraisal tests pass.

## Key Findings
- **Staging Discrepancy**: The history was previously collapsed into a single `STG1` mega-ticket.
- **Naming Convention**: The code uses "Phase 1 Stage 4" comments, implying a granular count was intended.
- **Phase 2 Status**: Phase 2 (Appraisal) was previously ticketed as `PH2-STRATEGIC-APPRAISAL` (now deleted) but fits better as its own Stage-based sequence within the Strategic Shift stream.
- **Snapshot Safety**: Nested models like `DirectiveRecord` and `ProjectRecord` use `SimulationModel` (frozen Pydantic), which is inherently snapshot-safe. However, direct mutation by ID in `ActionSystem` must be careful not to share mutable list references.

## Conflicts/Duplications
- **Conflict**: The `Behavioral Realism` design shift also uses Phase 1 and Phase 2. To avoid confusion, I will reference these as "Strategic Design Shift: Phase X Stage Y" in the logs and tickets.
- **Duplication**: None found.

## Assumptions
- "Continue" implies approval of the reconciliation plan.
- The user wants a clean, granular historical record that matches the code comments.
