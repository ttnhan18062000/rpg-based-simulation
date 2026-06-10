# Investigation — TCK-20260610-EXPANSION-GATE-USAGE-MATRIX

## Problem

`test_expansion_gate.py` gate item 04 scans YAML `# STATE:` comments (lines 61-62) via
`_STATE_RE = re.compile(r"#\s*STATE:\s*(\S+)")` and `_ID_RE = re.compile(...)`.
It also defines `_ACTIVE_STATES = frozenset({"EXISTING-LOGIC", "LEGACY-EXPORT", "REDESIGNED-CORE"})`
and `_KNOWN_INACTIVE_CONTENT` (a 10-item baseline set) at module level.

This violates Option A: "YAML comments are human planning notes only — never parsed by validators or
the engine." The rule is explicitly stated in `ContentFamilyMatrixEntry`'s docstring:
"POLICY NOTE: YAML comments (e.g. # STATE: ...) are planning notes only."

Additionally, a "must stay in sync with test_active_data_consumer.py" comment on line 45 admits
the duplication explicitly.

The module docstring still mentions "Items blocked by the pre-existing CAT-REL-099 defect (moon_cult_ruins
/ apprentice_mage) are marked xfail(strict=False)" — this xfail behaviour was removed but the text
wasn't cleaned up.

## Correct Pattern

`test_active_data_consumer.py` already does this correctly:
- Uses `CONTENT_USAGE_MATRIX.items()` with `entry.implementation_state in _ACTIVE_IMPL_STATES`
- `_ACTIVE_IMPL_STATES = frozenset({"RESOLVED_PARTIALLY", "RUNTIME_AUTHORITATIVE"})`
- `_GRAPH_EXEMPT_SHORTS` covers families whose records are implicit entry points (no inbound edges by design)
- `collect_family_graph_violations` logic: for each active family, get `ref_graph.nodes` filtered by
  `short:` prefix, check `ref_graph.is_record_used(node_id)`

## ContentReferenceGraph API

- `ref_graph.nodes: Dict[str, Any]` — all indexed node IDs (e.g. `"item:wooden_staff"`)
- `ref_graph.is_record_used(node_id: str) -> bool` — True if any inbound edge exists

## test_active_data_consumer.py Status

The three tests in `test_active_data_consumer.py` cover:
1. `test_active_families_have_documented_consumers` — matrix has resolver/consumer fields
2. `test_active_families_have_graph_coverage` — active families have at least one consumed record
3. `test_content_usage_matrix_covers_active_catalog_families` — matrix covers all canonical families

Test 2 contains the logic to extract into the shared helper.
Test 1 uses `_ACTIVE_IMPL_STATES` — the helper should export this constant so test 1 can import it.
Test 2 uses `_ACTIVE_IMPL_STATES` and `_GRAPH_EXEMPT_SHORTS` — both move to the helper.

## Gate 04 Signature Change

Current signature: `test_gate_04_no_new_dead_active_data(catalog, module_repo)` — builds its own
ref_graph internally.
New signature: `test_gate_04_no_new_dead_active_data(ref_graph)` — uses the module-scope fixture.

## Imports After Refactor

- `re` import: remove entirely (no more regex scanning)
- `yaml` import: keep (used in gates 08 and 12 for YAML file parsing)
- `Tuple`, `Dict` from `typing`: remove (no longer needed after removing inline type annotations)

## No Changes to YAML Content Files

YAML `# STATE:` comment markers must remain untouched — they are human-only notes.
