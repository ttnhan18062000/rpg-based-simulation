---
status: historical
layer: observability
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261006-PERF-OPERATIONAL-FLAGS-MATRIX-DRIFT
date: 2026-10-08
tags: [performance, observability, documentation]
---

# Plan: TCK-20261006-PERF-OPERATIONAL-FLAGS-MATRIX-DRIFT

1. Matrix section 1: the forbidden-flags row names all three enforced flags and the validator.
2. Matrix section 2: split into the kernel flags that are read (with the file and line), flags that are not implemented (rows kept), forbidden flags, and validated-but-unread flags; note that unknown flags are ignored.
3. Test matrix: replace the `FORCE_REPLAY_OFF` row with the real `no_replay` behaviour and a named test; correct the exception name; list the new tests.
4. Tests in `tests/unit/core/test_operational_flags.py`: `no_replay` sets `replay_allowed=False` and stays off after governor evaluation and the replay sink is not written; `test_safe_operational_flags_accepted` stops being cited as obedience proof; the three forbidden flags are rejected.
5. Parity ledger `infrastructure.yaml`: one entry for operational-flag obedience.
6. Gates: tests/unit/tools and tests/docs in full, code-health and typecheck unaffected (no src/ edit).
