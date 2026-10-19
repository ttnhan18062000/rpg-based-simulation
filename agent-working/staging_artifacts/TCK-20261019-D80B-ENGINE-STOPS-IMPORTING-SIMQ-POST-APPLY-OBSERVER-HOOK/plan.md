---
status: active
layer: architecture
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261019-D80B-ENGINE-STOPS-IMPORTING-SIMQ-POST-APPLY-OBSERVER-HOOK
date: 2026-10-19
---

# Plan: D80 B, a run-observer hook replaces the kernel's SimQ wiring

Not implemented. For rpg-planner's review.

## Shape

New module `src/engine/run_observers.py` (no SimQ import; stdlib and typing only):

```python
@dataclass(frozen=True)
class RunContext:
    run_id: str
    run_dir: str              # where the run's artifacts go (same string the kernel passes EventRecorder today)
    observability_on: bool

class RunObserver(Protocol):
    def on_envelope(self, env: ObservabilityEventEnvelope) -> None: ...   # called on the recorder's drain thread, as quality_fn is today
    def start(self) -> None: ...        # after the EventRecorder exists (today: feed.start(hub))
    def stop_intake(self) -> None: ...   # before recorder shutdown (today: feed.stop())
    def finish(self) -> None: ...        # after recorder shutdown (today: report write + persistence.shutdown())

RunObserverFactory = Callable[[RunContext], Optional[RunObserver]]
```

`Kernel.__init__(..., observers: Sequence[RunObserverFactory] = ())`. The kernel builds each factory when observability is not OFF (a factory exception is logged and that observer is skipped, as the SimQ build failure is today), passes one fan-out callable to `EventRecorder(quality_fn=...)` (a small `_FanOut` that calls each `on_envelope` in registration order and isolates exceptions, matching the recorder's per-call try/except), then calls `start()`; at shutdown it calls `stop_intake()` before `event_recorder.shutdown()` and `finish()` after it, preserving the drain-ordering fix. The kernel keeps `observers` (a tuple of the built instances, read-only property) and drops `_quality_hub`, `_quality_feed`, `quality_hub`.

SimQ side: new `src/simulation_quality/observer.py` with `QualityRunObserver` (wraps today's feed + hub + persistence build, moved verbatim from kernel.py:233-260 and the shutdown report block) and `quality_observer_factory(context)`; `default_observer_factories() -> (quality_observer_factory,)`. The observer exposes `.hub` and `.persistence` so the API can read them.

Composition roots pass the factory explicitly (no global registry, no import-time registration):
- `src/api/engine_manager.py:139` passes `default_observer_factories()`; `server.py:63-65` finds the observer in `kernel.observers` by type (`QualityRunObserver`) instead of `kernel.quality_hub`.
- `src/cli/entry.py`, `tools/{calibrate_simq,evaluate_simq,simq_long_run_observation,entity_lifecycle_score}.py` and the SimQ tests pass it.
- Perf, certification, scenario, lab/sweeper and gate/paired runs pass nothing (open decision 1 in the investigation, planner to confirm).

Order of work (one batch, one measured step):
1. Add `run_observers.py`, `observer.py`, and the fan-out; kernel uses them; unit tests for the fan-out, lifecycle order, failure isolation.
2. Move composition roots; migrate the three test files off `_quality_hub`/`_quality_feed`.
3. Add the import-linter contract; remove nothing else.
4. Measure.

## Import-linter contract

Add to `codebase/structure/importlinter.toml` next to `c06_hot_path_not_heavy`, id `c16_engine_core_no_simq` (c15 is the last one in use):

```toml
[[tool.importlinter.contracts]]
id = "..."
name = "src.engine and src.core do not import the SimQ package (decision 80 B)"
type = "forbidden"
source_modules = ["src.engine", "src.core"]
forbidden_modules = ["src.simulation_quality"]
allow_indirect_imports = true   # observability -> simq paths, if any, are not this contract's concern
unmatched_ignore_imports_alerting = "warn"
```

No `ignore_imports`: the contract must be green because the import is gone, not excused. The function-local import in `kernel.py` is visible to import-linter (it scans the AST), so the contract fails on the current tree and passes after the move; I will confirm that red-first before the change. A source-text test in `tests/architecture/` is not needed.

## Acceptance mapping

| criterion | how |
|---|---|
| Final hash identical to the v1 record, 3 gate worlds x seed 42, observability ON and OFF | paired tool `--neutral`-style byte compare at 5000 ticks, base 864f7b281 vs branch, run with observability ON and with it OFF (one run each, cache keyed by commit) |
| New contract passes | `lint-imports`, first shown failing on the base |
| SimQ report unchanged on one calibration run | `tools/calibrate_simq.py` on base and branch, same seed and ticks, diff `quality_report.json` and `quality_scores.jsonl` |
| Paired numbers as their own step (memo row 82) | `paired --report-only`, step name "D80 B", behaviour columns expected identical |

Out of scope held: no change to scorers, grades, or how SimQ reads events (C).

## Not doing

Moving RunLedger/DeathLedger (they are event producers, see investigation section 3). Touching `_event_listeners`.
