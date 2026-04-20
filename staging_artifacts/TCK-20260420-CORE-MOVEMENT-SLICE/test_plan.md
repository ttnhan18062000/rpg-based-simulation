# Test Plan: Deterministic Grid Movement

## Unit Tests
- `tests_v2/engine/test_movement_logic.py`:
  - Test blocked terrain rejections.
  - Test occupancy rejections.
  - Test simultaneous movement claim rejections (determinism check).
  - Test successful movement update generation.

## Parity Tests
- `tests_v2/parity/test_movement_parity.py`:
  - Compare `src_v2` movement results against `src` results for a set of movement scenarios.

## Certification Tests
- Integrate movement scenarios into `tests_v2/certification/test_final_gate.py`.

## Verification Commands
- `pytest tests_v2/engine/test_movement_logic.py`
- `pytest tests_v2/parity/test_movement_parity.py`
- `pytest tests_v2/certification/test_final_gate.py`
