---
status: historical
layer: observability
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261006-PERF-OPERATIONAL-FLAGS-MATRIX-DRIFT
date: 2026-10-08
tags: [performance, observability, documentation]
---

# Investigation: TCK-20261006-PERF-OPERATIONAL-FLAGS-MATRIX-DRIFT

Tree: `origin/main` `28d0af111`. Docs and tests only.

## What the code reads
- `Kernel.__init__` (`src/engine/kernel.py`): `audit_mode` (:84), `audit_dirty_set` (:85), `perf_tracker` (:86, stored, **read nowhere**), `force_full_scan` (:87), `no_frame_pacing` (:217, used :467),
  `no_replay` (:198 sets `GovernorPolicy.replay_allowed=False`; :218 stores `_no_replay`, re-applied after each governor evaluation at :566).
- `ProfileValidator.validate_flags` (`src/config/validator.py:66-84`): rejects `FORCE_NORMAL`, `BYPASS_GOVERNOR`, `DISABLE_RESOURCE_CEILINGS`; checks `SURVIVAL_ONLY` + `REPLAY_ENABLED` and
  `REPLAY_ENABLED` with a 0 KB replay buffer, but no code in `src/` reads either flag.
- Read nowhere in `src/`: `FORCE_REPLAY_OFF`, `SELECT_PROFILE`, `FORCE_DEGRADED`. Unknown flags are ignored (`test_flags_cannot_alter_authoritative_semantics` relies on it).

## The drift
Matrix section 2 lists `FORCE_REPLAY_OFF` and `SELECT_PROFILE` as "Safe" with no implementation, omits the flags the kernel really reads, and section 1 lists one forbidden flag where three are enforced.
The test matrix claims "`FORCE_REPLAY_OFF` flag active -> sink never called" as covered; `test_safe_operational_flags_accepted` only checks the kernel does not raise.
The test matrix also says an illegal flag gives `SecurityError`; the code raises `ConfigValidationError`.
