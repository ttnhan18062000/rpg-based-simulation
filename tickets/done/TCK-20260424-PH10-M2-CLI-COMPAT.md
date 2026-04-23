# TCK-20260424-PH10-M2-CLI-COMPAT

## Title
Phase 10 Milestone 2: CLI and Entrypoint Compatibility

## Status
DONE

## Request Summary
Recover the legacy CLI contract and unified entrypoint for the V2 engine.

## Scope
- [x] Task 1: Audit legacy CLI and entrypoint rows against current `src_v2` entry behavior.
- [x] Task 2: Recover supported default entry behavior and preserved subcommand semantics.
- [x] Task 3: Recover supported output-path, startup, and shutdown compatibility semantics.
- [x] Task 4: Add direct black-box tests for CLI and entrypoint compatibility.
- [x] Task 5: Publish the CLI and entrypoint compatibility contract.

## Out of Scope
- Full API/WebSocket parity (owned by M5).
- Infrastructure/Env precedence (owned by M3).

## Acceptance Criteria
- `python3 -m src_v2 cli` works with legacy flags.
- Determinism is preserved across CLI calls.
- Black-box tests pass.
- CLI contract is published.

## Related Tickets
- [TCK-20260424-PH10-M1-READINESS](TCK-20260424-PH10-M1-READINESS.md)

## Test Summary
- `tests_v2/cli/test_entry_parity.py` (4 tests passed).

## Files Changed
- `src_v2/__main__.py` [NEW]
- `src_v2/cli/entry.py` [NEW]
- `src_v2/systems/generator.py` [NEW]
- `tests_v2/cli/test_entry_parity.py` [NEW]
- `docs/engine/cli_entrypoint_contract.md` [NEW]
- `docs/engine/legacy_replacement_ledger.md` [MODIFY]
