# Investigation: TCK-20260619-E-PHASE-PERMISSIONS

## Current Behavior

### Engine phases — `src/engine/phases.py:L6`
Seven `TickPhase` members: INIT, SCHEDULING, COLLECTION, RESOLUTION, CLEANUP, ADVANCEMENT (authoritative), PERSISTENCE (non-authoritative hook).
`get_authoritative_phases()` returns the first 6.

### Per-phase state access (from `src/engine/kernel.py`)
| Phase | Reads | Writes |
|---|---|---|
| INIT (L395) | profile, prior signals, worker/replay stats, platform signals | OccupancySnapshot, current_policy, executor concurrency |
| SCHEDULING (L455) | state (entity), current_policy | current_work_items |
| COLLECTION (L459) | state.readonly_view(), current_work_items, rng | final_results (proposals) |
| RESOLUTION (L471) | final_results, current_signals, current_policy, state | entity state via AuthoritativeApplyPipeline, metrics, replay trace |
| CLEANUP (L577) | platform signals, cache_registry, state.tick | metrics, cache prune, platform_signals update |
| ADVANCEMENT (L609) | current_update | tick+1, world_time via ApplyPath.apply_generation |
| PERSISTENCE (L804) | state, events | replay/log disk writes |

### No existing domain declarations
No `PHASE_READ_DOMAINS` / `PHASE_WRITE_DOMAINS` / `PHASE_EMIT_DOMAINS` constants exist anywhere in `src/engine/`.

### Parity tracking — two separate systems (ID collision)
- `docs/parity_ledger/infrastructure.yaml` INFRA-155/156 = replay manifest atomicity (already verified — **different items**)
- `docs/logic_checklist_exhaustive.md` § Z12 (L3001-3003) = per-phase domain declarations — **unchecked** `[ ]`
  - RPG-INFRA-155: Each engine phase declares allowed read domains
  - RPG-INFRA-156: Each engine phase declares allowed write/update domains
  - RPG-INFRA-157: Each engine phase declares allowed emit/event domains

### Existing architecture guard test patterns
`tests/architecture/` contains: hot-path import checks, observability boundary checks, enum migration checks.
All use static file analysis or lightweight import inspection — no runtime instrumentation.

### Last parity ledger ID
INFRA-205 (`src/observability/live/entity_inspector.py` personality snapshot). New entries use INFRA-206+.

## Mechanics / Engine Constraints

Per `docs/engine/kernel.md`:
- RESOLUTION is the singular authoritative write point — verified by `_guard_stability`
- COLLECTION uses `state.readonly_view()` — read-only snapshot, enforced by existing guard
- PERSISTENCE is non-authoritative — must not mutate entity/world state

## Parity Ledger Overlap

- `docs/logic_checklist_exhaustive.md` Z12 items RPG-INFRA-155/156/157 are unchecked — will be checked on completion
- New parity ledger entries INFRA-206/207/208 will cover the declarations

## Prior Work

- `TCK-20260619-P0-CI-AUTOMATION` (done): architecture guard CI — tests will run in CI automatically
- `tests/architecture/test_phase19_hot_path_safety_contract.py`: pattern reference for static architecture tests

## Risks and Open Questions

- **None critical.** The declarations are documentation-level constants; they don't add runtime enforcement (that's RPG-INFRA-158–163, out of scope).
- The `RPG-INFRA-155/156` acceptance criterion in the ticket says "status=verified in infrastructure.yaml" — but those IDs there are replay manifest. Resolution: check the logic checklist + add new parity entries INFRA-206/207/208.

## Anti-Drift Hazards

- If a phase is added to `TickPhase` in future, the domain maps must be extended — covered by tests asserting all authoritative phases are present.
- RESOLUTION must remain the only entity/world write phase — asserted in architecture guard.
