# Plan — TCK-20260613-DOC-DOMAIN-CONTRACTS

## Approach

Create 9 domain contract docs in `docs/simulation/domains/` and update the ownership map.

Docs follow the established `campaigns_contract.md` format.

## Documents to create

| Doc | Engine Phase | Phase file? |
|-----|-------------|-------------|
| adventure_contract.md | Phase 3 | ✓ phase.py |
| motivation_contract.md | Phase 14 (inline) | ✗ |
| progression_contract.md | Phase 6 | ✓ phase.py |
| perception_contract.md | Phase 12 | ✓ phase.py |
| emotion_contract.md | Phase 16 (event-driven) | ✗ |
| commitment_contract.md | Phase 15 (inline) | ✗ |
| cooperation_contract.md | Phase 7 | ✓ phase.py |
| world_emergence_contract.md | Phase 8 | ✓ phase.py |
| memory_contract.md | Phase 13 | ✓ phase.py |

## Key findings from investigation

- adventure: phase 3, generates up to 25 route candidates, scores via personality biases, maps to StrategicUpdate
- motivation: no phase.py, used as scoring utility for other domains; backed by world/motivation/pressure_resolver.py  
- progression/domains: phase 6, 6-step pipeline, manages XP ledger and reward conversion; does NOT do level-up (that's src/progression/)
- perception: phase 12, salience formula: base_relevance + attention_bonus + danger×(1+fear) + novelty×0.2×(1+curiosity) − distance×0.01; backed by world/perception/gate.py
- emotion: event-driven, 7 emotion dimensions, deterministic deltas per event_kind
- commitment: no phase.py, scoring utility for pressure/abandonment/reputation; no EntityUpdate produced
- cooperation: phase 7, 4 help-need triggers, 12 posture options, timeline.append() is known pattern
- world_emergence: phase 8, 100-tick recent_events window, MD5 quest seeding, produces StateUpdate + WorldEmergenceResult
- memory: phase 13, causal attribution + spatial memory + temporal urgency; backed by cognition/knowledge_model.py

## Execution

Write all 9 docs plus ownership map update in a single pass (parallel agents per doc).
