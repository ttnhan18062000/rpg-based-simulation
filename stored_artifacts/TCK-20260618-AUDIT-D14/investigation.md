---
ticket_id: TCK-20260618-AUDIT-D14-COUPLING
type: investigation
date: 2026-06-18
---

# D14 Investigation — Coupling Depth

## Scanner Results

### Cross-domain imports (prohibited pattern — excluding optimization)
1 violation: src/domains/memory/phase.py:20 → time | `from src.domains.time.service import TemporalPressureService`

### core→engine/domains upward dependencies
2 lazy imports:
- src/core/state.py:1057 → engine.movement_cache | inside __post_init__ method body
- src/core/updates.py:15 → engine.policy | inside TYPE_CHECKING guard

### API layer raw model exposure
Routes: 0 violations — all go through read_cache.get_entity_dto() or StatePresenter.present_full()
engine_manager.py imports: Kernel, MetricsService, CacheRegistry (expected — manager controls engine)

### Engine→domain coupling
All 7 domain imports in pipeline.py only (clean single integration point):
optimization, information, cooperation, adventure, combat_engagement, world_emergence, progression

### Observability→engine
4 files: hard_law_monitor.py (WorldIndexService), sweeper.py (Kernel), controller.py (Kernel), harness.py (Kernel)

### Clean layers
- content: 0 imports from engine or domains
- API routes: 0 imports from domains/engine directly
- Domains (13 of 14): no cross-domain imports
