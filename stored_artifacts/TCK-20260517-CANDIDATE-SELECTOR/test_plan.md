# Test Plan: CandidateSelector & ScanPolicy

## Scope
Validate the correctness, determinism, and exact filtering behavior of `CandidateSelector.entities`.

## Test Suite Location
`tests/unit/optimization/test_candidate_selector.py`

## Test Cases (From `perf_test_plan.md`)
1. **Test Force Full Scan**: Verify that when `update.force_full_scan = True`, `CandidateSelector.entities` returns all entities present in `state.entities`, completely ignoring `update.dirty_set`.
2. **Test None Dirty Set**: Verify that when `update.dirty_set` is `None`, the method defaults to a full scan.
3. **Test Single Domain Selection**: Verify that when `update.dirty_set` has specific movement entities, requesting `domains={"movement"}` returns exactly those entities.
4. **Test Multi-Domain Union**: Verify that requesting `domains={"movement", "strategic"}` returns the exact union of both dirty sets.
5. **Test Inactive Exclusion (`include_inactive=False`)**: Verify that inactive entities (`entity.active == False`) are stripped from the return tuple, both during full scan and dirty scan.
6. **Test Inactive Inclusion (`include_inactive=True`)**: Verify that inactive entities are included when `include_inactive=True`.
7. **Test Deterministic Ordering**: Verify that the returned tuple is sorted in ascending integer order regardless of the set insertion order.

## Execution Command
`pytest tests/unit/optimization/test_candidate_selector.py -v`
