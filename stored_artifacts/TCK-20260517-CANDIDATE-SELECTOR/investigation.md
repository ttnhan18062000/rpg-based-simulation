# Investigation: CandidateSelector & ScanPolicy

## Current Architecture Analysis
In the current implementation of the engine, candidate selection for pipeline phases is partially handled by helper functions such as `get_relevant_entity_ids` in `src/core/dirty.py`. However, as identified in `perf_test_plan.md`, individual pipeline phases and subsystems risk reading `update.dirty_set` directly or inconsistently, leading to "fake full-scan reference risk" where performance benchmarks or correctness verification could diverge.

## Target Design
We will introduce `CandidateSelector`, an authoritative static utility class in `src/core/dirty.py`:
```python
class CandidateSelector:
    @staticmethod
    def entities(state: AuthoritativeState, update: StateUpdate, domains: set[str], *, include_inactive: bool = False) -> tuple[int, ...]:
        ...
```

## Key Findings & Constraints
1. **Full Scan Trigger**: If `update.force_full_scan` is True or `update.dirty_set` is None, the method must return all entity IDs in `state.entities`.
2. **Domain Mapping**: When a dirty set is present, `domains` specifies a set of string identifiers (e.g. `{"movement", "combat"}`). The method must compute the union of the corresponding entity ID sets from `update.dirty_set`.
3. **Inactive Filtering**: If `include_inactive` is False, the resulting candidates (whether from full scan or dirty set) must be filtered to keep only entity IDs where `state.entities[eid].active` is True. Note: `entity.active` is a property returning `self.lifecycle.active`.
4. **Determinism**: The output must be a tuple of sorted integer IDs (`tuple(sorted(candidates))`).
