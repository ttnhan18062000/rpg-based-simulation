---
status: active
layer: engine
authority: P3
audience: agent
ticket_id: TCK-20261006-GROUP-GUARD-OBLIGATION-MOVE-OUTLIVES-ITS-LEADER
artifact_type: test_plan
tags: [engine, combat]
---

# Test plan

- Unit, `tests/unit/engine/test_pursuit_completion.py` (29): normal flow (guard ends when the leader dies, goes inactive or is gone; ends when the mover leaves the group or is ungrouped); edge cases (a live same-group leader at any distance does not end it, so adjacency is not an end; a leader that merely stops interacting does not end it); failure modes (missing target); regression-prone paths (a guard with no recognised reason and cover-seeking stay unchanged); both dispatchers (`LocalSequentialExecutor`, concurrent worker).
- Disabling controls: guard kinds untracked fails exactly 5; group condition off fails exactly 1.
- Regression: `tests/unit/engine` and the two mechanism-registry checks, 330 passed, 1 skipped.
- Corpus: legacy vs after arms, 4 worlds x 2 runs.

## Proof Plan

- Level: unit, plus a real-kernel corpus measurement.
- Proof kind: regression with disabling controls; the corpus is a measurement only, because it contains no live-mover instance.
- Oracle source: the Sticky-Task Law in `docs/engine/kernel.md` and divergence 2.70/2.71.
- Expected effect: a guard move ends when its leader is dead, inactive, gone, or no longer in the mover's group; recognised combat moves and cover-seeking are unchanged.
- Selected commands: `pytest tests/unit/engine/test_pursuit_completion.py`; `probes/measure.sh <label> [legacy]`.

## Not run here

`ast-grep`, `mypy`, `prek` and `ruff` are not installed in this venv, so `tests/codebase` ratchet, mypy and hook tests (44 failures, all "tool not found") could not run. `ruff` was run through `uvx` with the project config on the changed file: no findings on any line changed in `candidate_selector.py`.
