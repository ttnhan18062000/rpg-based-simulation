---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260729-CONTEXT-PACKET-ASSEMBLY
artifact_type: test_plan
tags: [ai, schema]
---

# Test Plan — TCK-20260729-CONTEXT-PACKET-ASSEMBLY

## Regression Surface

This ticket adds one new standalone module (`tools/context_packet_assembler.py`) that only reads
from `tools/hybrid_retrieval.py`, `tools/retrieval_cache.py`, `tools/code_test_index.py`,
`docs/REGISTRY.yaml`, and (per Decision A's parity_ledger_entry branch)
`docs/parity_ledger/*.yaml`. No `src/` file is touched, so no simulation-domain regression suite
applies. The regression surface is the three already-landed sibling modules this ticket consumes
plus the modules whose scope-guard tests prove no corpus/wiring drift occurred.

**Unit — sibling modules this ticket has a hard, load-bearing dependency on (must still pass
unmodified; a failure here means this ticket's assumed input shapes have drifted):**
- `tests/tools/test_hybrid_retrieval.py` — `HybridResult`'s 13-field shape, `UNRATED` sentinel,
  `resolve_metadata()`'s registry-vs-fallback behavior.
- `tests/tools/test_retrieval_cache.py` — `PacketCacheResult`/`QueryCacheResult`/
  `IndexCacheResult`'s `status`/`reason_code` shape; confirms `check_packet_cache()` still "operates
  on raw fields only," never a `ContextPacket` import.
- `tests/tools/test_code_test_index.py` — `build_records()`'s 6-field record shape
  (`id`/`module`/`symbol`/`docstring`/`owned_component`/`associated_tests`), `DOCSTRING_GAP`/
  `ASSOCIATED_TESTS_GAP` sentinel behavior.

**Unit — corpus/scope-guard regressions (proves this ticket did not fold a new corpus source into
`knowledge_search.py`, and did not change `hybrid`/`vector`/`keyword` mode routing):**
- `tests/tools/test_knowledge_search.py::TestCorpusScopeGuard` (both tests).
- `tests/tools/test_knowledge_search.py::TestQueryModeRouting`.
- `tests/tools/test_eval_search.py` (full file — guards `_reciprocal_rank()`'s MRR@10 semantics
  stay untouched; this ticket's assembler must not import or alias it).

**Integration/architecture — none required beyond the module's own new tests**, since nothing in
`.claude/workflows/*.js`, `src/`, or the API layer is modified by this ticket.

## New Tests Required

All new tests live in `tests/tools/test_context_packet_assembler.py` (new file), following the
batch's established conventions (`tests/tools/test_hybrid_retrieval.py`/
`tests/tools/test_retrieval_cache.py`): no live ML dependency required, `tmp_path`/`monkeypatch`
isolation for any file-path state, small hand-built fixtures only (never asserting against a live
`docs/REGISTRY.yaml`/`knowledge.db`/`graph.json`).

| Test name | Category | What it verifies | AC |
|---|---|---|---|
| `test_code_symbol_candidate_with_no_registry_entry_gets_unrated_sentinel` | unit | A `code_test_index.py`-shaped candidate (no REGISTRY path match) produces an `included[]` item with `authority == "unrated"` and `freshness == "unrated"`, using the imported `hybrid_retrieval.UNRATED` constant, not a re-literal string | AC1 |
| `test_two_active_docs_same_subject_both_included` | unit | Two candidate docs, both `status: active`, one `authority: P0` one `authority: P1`, on the same subject: both appear in `included[]`, none silently dropped | AC2 |
| `test_lower_ranked_entry_inclusion_reason_names_superseding_source_id` | unit | The `P1` entry's `inclusion_reason` contains/names the `P0` entry's `source_id` as superseding (e.g. `"superseded-by:<source_id>"`) | AC2 |
| `test_tiebreak_falls_back_to_last_verified_when_authority_equal` | unit | Two `active` docs with equal `authority` but different `last_verified` rank the more recent one higher | AC2 (Decision B) |
| `test_included_entry_has_exactly_ten_contract_fields` | unit | Every `included[]` item's key set equals exactly `{source_id, kind, path, heading_or_symbol, hash, authority, freshness, score, inclusion_reason, excerpt_budget}` — no more, no fewer | AC3 |
| `test_excluded_summary_entry_has_exactly_four_contract_fields` | unit | Every `excluded_summary[]` item's key set equals exactly `{source_id, kind, reason, count}` | AC3 |
| `test_assembled_packet_never_contains_raw_fixture_text_anywhere` | unit | Given a fixture with a distinctive raw-text marker string in `HybridResult.text`, assert that marker string appears in **no** field value anywhere in the assembled packet (recursive walk of the packet dict/dataclass) — only its hash digest may appear | AC4 |
| `test_hash_field_is_sha256_of_excerpt_not_the_excerpt_itself` | unit | `included[]`'s `hash` field equals `hashlib.sha256(text.encode()).hexdigest()` of the source excerpt, confirming the reused `retrieval_cache._hash_text()` convention, and is not equal to or a substring of the raw text | AC4 |
| `test_module_not_referenced_by_any_claude_workflows_file` | architecture guard | Static/grep-based scan of every file under `.claude/workflows/*.js` finds zero references to `context_packet_assembler` (filename or import path) | AC5 |
| `test_module_does_not_import_any_claude_workflows_file` | architecture guard | AST-parses `tools/context_packet_assembler.py`'s own imports and asserts none resolve into `.claude/workflows/` | AC5 |
| `test_parity_ledger_entry_kind_uses_own_priority_and_status_not_registry_enum` | unit | A hand-built `parity_ledger_entry`-kind candidate (fixture dict with `priority`/`status` per `docs/parity_ledger/schema.json`) produces an `included[]` item whose `authority`/`freshness` equal the entry's own `priority`/`status` values verbatim, and those values are asserted to not be members of `tools.validate_frontmatter.STATUS_VALUES` when the parity `status` value used is one exclusive to the 5-value parity enum (e.g. `"legacy_verified"`) | Scope item 2 (Decision A, parity branch — not directly an AC, see investigation Risks) |
| `test_parity_ledger_entry_authority_not_coerced_into_registry_authority_values` | unit | Same fixture: confirms no silent mapping/clamping of parity `priority` into a REGISTRY-flavored value occurs (identity passthrough only) | Scope item 2 |
| `test_fixture_mixes_registry_backed_and_non_registry_backed_kinds` | unit (fixture validity) | The shared test fixture used across this file contains at least one REGISTRY-backed doc candidate and at least one non-REGISTRY-backed candidate (code_symbol), proving the "no such fixture currently exists" gap from the ticket's Assumptions is actually closed | Scope bullet 4 |
| `test_expansion_policy_is_a_marked_placeholder_not_real_escalation_logic` | unit | `expansion_policy`'s value is a clearly-labeled stub (e.g. contains an explicit "not yet resolved"/"Open Decision 5/6" marker) and is not a dict/object exposing any field resembling real escalation semantics (`max_expansions`, `trigger`, `threshold`, etc.) | Scope ("Stub expansion_policy...not invented escalation semantics") |
| `test_assembler_does_not_import_contextpacket_from_retrieval_cache` | architecture guard | `tools/retrieval_cache.py` is confirmed to still not import/define a `ContextPacket` class after this ticket lands (static check, mirrors `retrieval_cache.py`'s own Anti-Drift Note) | Out of Scope guard |

## Scoped Pytest Commands

```
pytest tests/tools/test_context_packet_assembler.py -v
pytest tests/tools/test_hybrid_retrieval.py tests/tools/test_retrieval_cache.py tests/tools/test_code_test_index.py -v
pytest tests/tools/test_knowledge_search.py tests/tools/test_eval_search.py -m "not slow" -q
```

Never `pytest tests/`. The three commands above are scoped strictly to `tools/`-tier
agent-orchestration/retrieval tooling — this ticket touches no `src/` or `tests/unit/` simulation
code, so no `tests/unit/` suite is in scope.

## Anti-Drift Test Guards

- **`test_module_not_referenced_by_any_claude_workflows_file` / `test_module_does_not_import_any_claude_workflows_file`**
  — directly guard AC5's "never wired into a workflow" requirement; a passing test here is the
  only mechanical proof this module stays advisory/standalone as the epic's Maturity banner
  requires.
- **`test_assembled_packet_never_contains_raw_fixture_text_anywhere`** — the single highest-value
  guard in this plan: any future edit that starts passing `HybridResult.text` (or a code symbol's
  docstring body, or an excerpt string) straight through into `inclusion_reason`, `path`, or any
  other free-text-shaped field breaks this test immediately, catching the exact class of drift the
  investigation's Risks section flags as most likely.
- **`test_hash_field_is_sha256_of_excerpt_not_the_excerpt_itself`** — guards against a hash field
  that is accidentally populated with the raw text (defeating the "hash, not content" MAY-list
  discipline `retrieval_cache.py` already established) or with a fabricated/random value instead of
  a real content digest.
- **`test_two_active_docs_same_subject_both_included` / `test_lower_ranked_entry_inclusion_reason_names_superseding_source_id`**
  — guard against the tempting-but-wrong shortcut of silently dropping the lower-authority
  duplicate, which Decision B explicitly forbids ("never silently dropped").
- **`test_parity_ledger_entry_kind_uses_own_priority_and_status_not_registry_enum` /
  `test_parity_ledger_entry_authority_not_coerced_into_registry_authority_values`** — guard against
  a plausible-looking but wrong "just reuse `resolve_metadata()`'s REGISTRY-join logic for
  everything" implementation shortcut, since `docs/parity_ledger/` entries are never in
  `docs/REGISTRY.yaml` and must never be silently mapped through that path.
- **`test_expansion_policy_is_a_marked_placeholder_not_real_escalation_logic`** — guards against
  scope creep into Open Decisions 5/6, which `ticket_plan_structure_phase3.md` explicitly forbids
  force-resolving in this batch.
- **`test_included_entry_has_exactly_ten_contract_fields` /
  `test_excluded_summary_entry_has_exactly_four_contract_fields`** — guard against both silent
  field omission (breaks downstream consumers) and silent field addition (contract drift/scope
  creep) in the same assertion, using an exact set-equality check rather than a subset check.
- **`test_assembler_does_not_import_contextpacket_from_retrieval_cache`** — guards the reverse
  direction of the dependency this ticket creates: this ticket may import from
  `tools/retrieval_cache.py`, but `tools/retrieval_cache.py` must never be made to import back from
  this ticket's new module — a cycle here would also violate `retrieval_cache.py`'s own
  already-tested "does not import/assume `ContextPacket`" Anti-Drift Note.
- Regression commands above (`test_hybrid_retrieval.py`, `test_retrieval_cache.py`,
  `test_code_test_index.py` full suites) guard against this ticket accidentally modifying any of
  the three consumed modules' behavior instead of purely reading their output shapes, which Out of
  Scope explicitly forbids.
