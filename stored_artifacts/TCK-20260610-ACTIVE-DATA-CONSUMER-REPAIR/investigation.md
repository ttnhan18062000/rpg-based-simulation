# Investigation — TCK-20260610-ACTIVE-DATA-CONSUMER-REPAIR

## Current Behavior

`tests/integration/content/test_active_data_consumer.py` validates per-record content maturity
by scanning YAML `# STATE:` comments. The key functions:
- `_parse_state_markers_from_file()` reads YAML files line-by-line and extracts `# STATE: X` markers
- `scan_state_marked_records()` aggregates (family, record_id, state) triples from all catalog files
- `test_active_records_have_consumer_paths` uses those state markers to decide which records to validate

This violates Option A: YAML comments are human planning notes only; no test or engine logic should depend on them.

## Option A Decision

Phase 20–28 repair decision (Option A): "YAML comments are human planning notes only. Do not validate per-record maturity from comments."

The review's recommendation: **Option 2** — replace with family-level ContentUsageMatrix validation.

## Authoritative Alternative: ContentUsageMatrix

`src/content/matrix.py` defines `CONTENT_USAGE_MATRIX: Dict[str, ContentFamilyMatrixEntry]`.

Each entry has:
- `implementation_state` — authoritative family-level status: `RESOLVED_PARTIALLY`, `RUNTIME_AUTHORITATIVE`, `DESIGN_ONLY`, `LOADED_ONLY`
- `resolver_component` — which component resolves this family
- `compile_runtime_consumer` — which runtime/compile consumer uses this family
- `content_maturity` — mirrors the YAML STATE at family level (but in code, not YAML)

This is the Option A-compliant source of truth for "which families are active."

## Replacement Design

**Family-level test 1 — matrix consumer documentation:**
For each family in ContentUsageMatrix with `implementation_state` in
{`RESOLVED_PARTIALLY`, `RUNTIME_AUTHORITATIVE`}: assert `resolver_component` or
`compile_runtime_consumer` is non-None. This validates the matrix is properly documented.

**Family-level test 2 — graph coverage:**
For each active family (by ContentUsageMatrix), check that at least one record in that family
has at least one incoming edge in the ContentReferenceGraph (is consumed by something).
Families with implicit consumers (`attribute`, `element`, `perspective`, `projection`) are exempted
from graph coverage checks as before.

**Family-level test 3 — matrix completeness:**
Assert ContentUsageMatrix covers all expected content families loaded by CatalogRepository.

**Remove entirely:**
- `_parse_state_markers_from_file()`
- `scan_state_marked_records()`
- `ACTIVE_STATES` / `INACTIVE_STATES` constants
- `state_marked_records` fixture
- `test_active_records_have_consumer_paths` (per-record STATE-comment-driven test)
- `test_known_gaps_are_genuinely_inactive` (STATE-comment-driven)
- `test_inactive_state_records_not_confused_with_active` (STATE-comment-driven)
- `test_state_marked_records_are_parsed` (scanner sanity)
- `test_implicit_consumer_families_are_scanned` (scanner sanity)

**Keep (rename/adapt):**
- `catalog`, `module_repo`, `ref_graph` fixtures

## Parity Ledger Overlap

No parity entries reference the STATE-comment scanning logic. No ledger update needed.

## Prior Work

- Phase 20–28 repair decision documented the Option A choice
- `src/content/matrix.py` was created in prior phases as the authoritative family registry

## Risks

- The replacement tests are weaker (family-level, not per-record). This is intentional and acceptable per Option 2.
- After the fix, `KNOWN_INACTIVE_CONTENT` per-record tracking is removed — this is acceptable since the baseline set was already tracked in the matrix at family level.
- `FAMILIES_WITH_IMPLICIT_CONSUMERS` list is kept as a code constant (not parsed from YAML) so it remains compliant.

## Anti-Drift Hazards

- Do not add any `re.match` or `# STATE:` parsing back into the replacement
- The ContentUsageMatrix is the authoritative source — do not compare its data against YAML content
