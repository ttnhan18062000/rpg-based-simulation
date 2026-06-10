# Plan — TCK-20260610-ACTIVE-DATA-CONSUMER-REPAIR

## Ordered Steps

### Step 1 — Rewrite test_active_data_consumer.py

Replace the entire file content. Keep: `catalog`, `module_repo`, `ref_graph` fixtures.
Remove: all STATE-comment scanning functions, constants, fixtures, and tests.
Add: 3 new ContentUsageMatrix-driven tests.

### Step 2 — Run tests to verify all pass with no xfail

### Step 3 — Verify expansion gate gate_04 still passes

## Scope Guards

- Only change `tests/integration/content/test_active_data_consumer.py`
- Do NOT modify `src/content/matrix.py`, `src/content/reference_graph.py`, or any other source
- Do NOT add per-record consumer checks back via any mechanism
- The `_KNOWN_INACTIVE_CONTENT` inline copy in `test_expansion_gate.py` is independent — leave it alone

## Acceptance Criteria Mapped

- AC1 (no STATE comment scanning): Step 1
- AC2 (ContentUsageMatrix validation): Step 1
- AC3 (all replacement tests pass): Step 2
- AC4 (STATE comments non-normative): already satisfied by removing scanning — YAML files unchanged

## Deviations
<!-- Fill if any step changes during implementation -->
