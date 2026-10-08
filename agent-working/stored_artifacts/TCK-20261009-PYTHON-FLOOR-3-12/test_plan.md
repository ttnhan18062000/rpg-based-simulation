---
status: historical
layer: architecture
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261009-PYTHON-FLOOR-3-12
phase: done
date: 2026-10-09
tags: [architecture, delivery]
---

# test_plan — TCK-20261009-PYTHON-FLOOR-3-12

Normal flow: uv lock succeeds without --upgrade; `uv lock --check` passes; mypy gate and code-health ratchet report 0 new.
Edge: the 3.13 and 3.12 exports differ only by the marker-excluded async-timeout line; numpy 2.5.0 and scipy 1.18.0 unchanged.
Failure mode: any other export diff, or a changed package version for 3.13, would fail the proof.
Regression: tests/static and tests/codebase pass (two known local 60 s tests deselected).

## Proof Plan
- level: tooling gates plus static tests
- proof kind: commands recorded in the ticket
- oracle source: `uv export` before and after, `mypy_baseline filter`, the code-health ratchet, pytest
- expected effect: no package version change for 3.13, 0 new type errors, 0 new/worse code-health findings
- selected commands: `uv export --frozen --no-hashes --python 3.13` (before/after diff), `uv lock --check`, `make typecheck-py`, `make code-health`, `pytest tests/static tests/codebase` (544 passed)
