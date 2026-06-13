---
status: active
ticket_id: TCK-20260613-DOC-DOMAIN-CONTRACTS
phase: test_plan
date: 2026-06-13
---

# Test Plan: TCK-20260613-DOC-DOMAIN-CONTRACTS

This is a documentation-only ticket. No behavior changes are introduced. The test plan covers verification of the documentation artifacts, not functional tests.

---

## Verification Steps

### 1. Knowledge index update (mandatory)

After all 9 contract docs are written and domain_ownership_map.md is updated:

```bash
make knowledge-index-update
make docs-registry
```

Both must complete without errors.

### 2. Doc guard integrity test

```bash
pytest tests/integrity/test_doc_guards.py -v
```

Ensures doc frontmatter is valid and docs registry is consistent.

### 3. Manifest guard (registry coverage)

```bash
pytest tests/integrity/test_manifest_guards.py -v
```

Ensures newly added docs appear in REGISTRY.yaml after `make docs-registry`.

---

## Manual Spot-Checks

For each of the 9 domain contract docs, verify:

- [ ] Frontmatter present and valid: `status: active`, `layer: simulation`, `authority: P1`, `audience: agent`, `last_verified: 2026-06-13`
- [ ] Phase number cited matches the actual phase.py docstring (or states "no phase.py, invoked inline as Phase N")
- [ ] "May mutate" section cites the actual update type used (EquipmentUpdate, StrategicUpdate, SocialUpdate, etc.)
- [ ] "Must not mutate" section is explicit (not vague)
- [ ] Test paths listed are real files (grep-verified during investigation)
- [ ] Progression contract explains the split between src/domains/progression/ (Phase 6 orchestration) and src/progression/leveling.py (authoritative mechanics)
- [ ] Perception contract cross-links PerceptionGate (src/world/perception/gate.py) and KnowledgeModelService (src/cognition/)
- [ ] Memory contract cross-links KnowledgeModelService and explains that KnowledgeFact assimilation is a separate layer from causal/spatial memory

---

## Domain Phase Number Summary (for doc verification)

| Domain | Phase | Phase class | Entry method |
|---|---|---|---|
| adventure | Phase 3 | AdventureDecisionPhase | apply() |
| motivation | Phase 14 | No phase.py — inline utility | N/A |
| progression (domains/) | Phase 6 | ProgressionConversionPhase | execute() |
| perception | Phase 12 | PerceptionUpdatePhase | run() |
| emotion | Phase 16 | No phase.py — inline utility | N/A |
| commitment | Phase 15 | No phase.py — inline utility | N/A |
| cooperation | Phase 7 | CooperationPhase | execute() |
| world_emergence | Phase 8 | WorldEmergencePhase | execute() |
| memory | Phase 13 | MemoryUpdatePhase | run() |

---

## Existing Test Coverage (for reference in contracts)

All test paths verified to exist as of 2026-06-13. See investigation.md per-domain sections for the full lists.

Key test directories:
- `tests/unit/domains/{domain}/` — unit tests per domain
- `tests/integration/domains/{domain}/` — integration phase tests
- `tests/integration/scenarios/test_phase{N}_*.py` — scenario tests
- `tests/perf/test_phase{N}_*.py` — budget/perf tests
