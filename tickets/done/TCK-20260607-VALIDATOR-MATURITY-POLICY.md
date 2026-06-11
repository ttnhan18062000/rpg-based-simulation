---
status: historical
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20260607-VALIDATOR-MATURITY-POLICY
phase: done
date: 2026-06-07
tags: [validator, maturity, policy]
---

# TCK-20260607-VALIDATOR-MATURITY-POLICY

## Title
Fix content_maturity policy violation in validator and matrix tests

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
`src/content/validator.py:636` uses the `content_maturity` field inside dead-record validation logic, violating the Phase 20 rule that YAML-comment-derived values must not drive engine validators. The test `test_content_usage_matrix.py:150` has the same violation. Both must use `implementation_state` instead.

## Scope

### Bug 1 — `validator.py:636` uses `content_maturity` in exemption logic

Current code:
```python
if entry.implementation_state in ("ADDITIONAL", "FUTURE-EXTENSION") or \
   entry.content_maturity in ("ADDITIONAL", "FUTURE-EXTENSION", "DESIGN_ONLY"):
    continue
```

Problems:
- `entry.content_maturity` is a YAML-comment-sourced field. Using it in a validator violates the Phase 20 contract.
- `"ADDITIONAL"` and `"FUTURE-EXTENSION"` are not valid `implementation_state` values — dead code that references non-existent states.
- The `DESIGN_ONLY` exemption is already covered by `implementation_state == "DESIGN_ONLY"` but is incorrectly expressed via `content_maturity`.

Fix:
```python
if entry.implementation_state in ("DESIGN_ONLY", "LOADED_ONLY"):
    continue
```

(Only `DESIGN_ONLY` families should be exempt from dead-record warnings. `LOADED_ONLY` families have no consumer by definition and should also be exempt. Remove the `content_maturity` check entirely.)

### Bug 2 — `test_content_usage_matrix.py:150` uses `content_maturity` in assertion

Current code:
```python
if entry.content_maturity == "COMPATIBILITY":
    assert entry.implementation_state != "RUNTIME_AUTHORITATIVE"
```

Fix: identify compatibility families via `implementation_state`:
```python
if entry.implementation_state in ("PROJECTED_TO_LEGACY",):
    assert entry.implementation_state != "RUNTIME_AUTHORITATIVE"
```

(Since `PROJECTED_TO_LEGACY` is already not `RUNTIME_AUTHORITATIVE`, the assertion becomes a no-op and should be rephrased to be meaningful — or replaced with: assert that any family with a compatibility-only resolver_component cannot be RUNTIME_AUTHORITATIVE.)

A cleaner assertion:
```python
for key, entry in CONTENT_USAGE_MATRIX.items():
    if entry.implementation_state == "PROJECTED_TO_LEGACY":
        assert entry.implementation_state != "RUNTIME_AUTHORITATIVE", (
            f"PROJECTED_TO_LEGACY family '{key}' cannot be RUNTIME_AUTHORITATIVE"
        )
```

## Out of Scope
- Do not change the `content_maturity` field definition itself (it serves as a human documentation column in the matrix report).
- Do not change valid `implementation_state` values.
- Do not touch other validators or resolvers.

## Acceptance Criteria
- [x] `validator.py` does not reference `content_maturity` for any conditional logic
- [x] Dead-record exemption uses only `implementation_state` 
- [x] Non-existent states `"ADDITIONAL"` / `"FUTURE-EXTENSION"` removed from all logic
- [x] `test_compatibility_family_not_runtime_authoritative` uses `implementation_state` only
- [x] `test_yaml_state_comments_are_ignored` still passes
- [x] All 159 unit tests pass (content + worldassembly scope)

## Related Tickets
- TCK-20260606-GRAPH-MODELFIX (same audit session)
- TCK-20260607-FAMILY-KEY-MISMATCH (companion hotfix)

## Related Docs
- world_phase_20_28_repair.md §5 — Decision: YAML comments are human-only

## Related Stored Artifacts
None

## Related Code Areas
- `src/content/validator.py:636`
- `tests/unit/content/test_content_usage_matrix.py:147-153`

## Assumptions / Open Questions
- Should `LOADED_ONLY` families also be exempt from dead-record warnings? Likely yes — they have no consumer by definition so a dead-record warning would be misleading. Confirm and add to fix.

## Implementation Notes
Single-file changes. No architecture changes required.

## Test Summary
Run `pytest tests/unit/content/ tests/unit/worldassembly/ -q` — expect 173 pass.

## Files Changed
- `src/content/validator.py`
- `tests/unit/content/test_content_usage_matrix.py`

## Completion Summary
Removed the dead-code compound condition at `validator.py:636` that referenced `content_maturity` and non-existent states (`ADDITIONAL`, `FUTURE-EXTENSION`). Replaced with `if entry.implementation_state in ("DESIGN_ONLY", "LOADED_ONLY"): continue`. Rephrased `test_compatibility_family_not_runtime_authoritative` to use `resolver_component`/`compile_runtime_consumer` fields instead of `content_maturity`, making the assertion non-tautological. 159 unit tests pass.
