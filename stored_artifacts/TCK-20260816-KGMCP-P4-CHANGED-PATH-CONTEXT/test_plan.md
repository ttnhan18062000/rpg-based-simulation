---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260816-KGMCP-P4-CHANGED-PATH-CONTEXT
artifact_type: test_plan
tags: [ai, mcp]
---

# Test Plan — TCK-20260816-KGMCP-P4-CHANGED-PATH-CONTEXT

## Context

Per investigation.md, AC1-AC3's real behavior is already implemented and already covered by
existing, passing tests (verified live this session — see "Already-Passing Coverage" below). This
plan therefore treats those tests as **regression surface to preserve**, not as tests to newly
write, and focuses "New Tests Required" on the two things that are genuinely not yet covered: the
AC4 parity-ledger entry's schema validity, and (conditionally) the open routing-integration
question from investigation.md.

## Already-Passing Coverage (spot-verified this session)

Ran live: `.venv/bin/python3 -m pytest tests/tools/test_knowledge_gateway_mcp.py -k "changed_paths" -q`
→ `1 passed, 38 deselected` (`test_level2_hit_rejected_on_changed_paths_intersection_triggers_real_refresh`).

## Regression Surface

Unit:
- `tests/tools/test_knowledge_gateway_cache.py` — all `changed_paths`/`working_tree_overlap`-related
  tests: `test_compute_lookup_identity_filters_excludes_budget_tokens_and_changed_paths` (:109),
  `test_working_tree_fingerprint_uses_changed_paths_intersection_not_full_tree_hash` (:212),
  `test_revalidate_context_packet_row_rejects_on_changed_paths_intersection` (:515), the
  spy-based pass-through test at (:697-718).
- `tests/tools/test_retrieval_cache.py` — `changed_paths`-adjacent dependency-storage assertions
  around (:1085-1089).
- `tests/tools/test_knowledge_gateway_contract_schemas.py` — request-schema `changed_paths` property
  assertions (:179-180).
- `tests/tools/test_evidence_cache_identity_contract.py` —
  `test_changed_paths_intersected_with_cached_evidence_paths_approach_is_documented` (:306-317).

Integration (real MCP round-trip via `_run_knowledge_context()`):
- `tests/tools/test_knowledge_gateway_mcp.py` —
  `test_level2_hit_rejected_on_changed_paths_intersection_triggers_real_refresh` (:820-834), plus the
  full Level 1/Level 2 hit/miss/fallthrough suite in the same file (broad blast radius — any
  `_run_knowledge_context()` signature change risks all of it).
- `tests/tools/test_kgmcp_phase3_pilot_acceptance_measurement.py` — uses `changed_paths=[...]` as a
  real input at (:551, :591, :601); part of the frozen Phase 3 pilot-measurement fixture set.

Architecture guard (must keep passing if the routing-integration open question is resolved as
"do not build (b) now"):
- `tests/tools/test_knowledge_gateway_router.py::test_changed_path_impact_call_is_not_wired_by_this_ticket`
  (:486-489) — AST-inspects `_run_parity_provider()`'s real body; asserts `impact`/`changed_path`
  are not called/passed. **If Plan/Implement decides to build option (b), this exact test must be
  explicitly and deliberately rewritten as part of that change** — it must never be silently left
  failing, silently deleted, or silently monkeypatched around.

## New Tests Required

Mapped to the ticket's 4 ACs:

**AC1 — `changed_paths` is a real, optional field on the schema and `_run_knowledge_context()`'s
signature.**
- Already satisfied by existing code + `test_knowledge_gateway_contract_schemas.py:179-180` and the
  live signature at `tools/knowledge_gateway_mcp.py:153`. No new test required unless Implement
  finds a genuine gap during re-verification (none found this session).

**AC2 — the integration-point decision is documented explicitly, with real reasoning.**
- Test name: `test_infrastructure_ledger_documents_changed_paths_integration_decision`
- Category: unit (doc/ledger content assertion, mirrors the pattern of
  `test_changed_paths_intersected_with_cached_evidence_paths_approach_is_documented`)
- Verifies: the new `INFRA-352` (or whatever id is actually next at Implement time — re-derive, do
  not hardcode) entry's `text`/`support_boundary` fields mention both "changed_paths" and the
  chosen integration point(s) by name, and that the entry parses under
  `docs/parity_ledger/schema.json`.
- Location: `tests/docs/test_parity_ledger_schema.py` if a generic schema-validity test already
  exists there (check first — likely already covers "every entry validates against schema.json"
  generically, in which case this AC is satisfied by that existing generic test plus a human/
  reviewer read of the entry's prose, and no new Python test is needed — only add a new test if no
  such generic validator already exists).

**AC3 — a real test proves `changed_paths` genuinely changes observed behavior for a real input.**
- Already satisfied by `test_level2_hit_rejected_on_changed_paths_intersection_triggers_real_refresh`
  (Level 2 path) and `tests/tools/test_knowledge_gateway_cache.py`'s Level 1
  `revalidate_cache_row()` tests. If Implement wants an explicit Level 1 (not just Level 2)
  end-to-end `_run_knowledge_context()` test for extra clarity, add:
  - Test name: `test_level1_hit_rejected_on_changed_paths_intersection_triggers_real_refresh`
  - Category: integration
  - Verifies: same shape as the existing Level 2 test but with Level 2 lookup forced to miss
    (monkeypatch `perform_context_packet_cache_lookup` to return `None`, mirroring the pattern at
    `test_knowledge_gateway_mcp.py:793-814`) so the Level 1 path is genuinely exercised.
  - Location: `tests/tools/test_knowledge_gateway_mcp.py`
  - Optional — only add if Implement/Plan judges the existing Level 2 coverage insufficient to
    satisfy AC3's literal text; do not add purely for count.

**AC4 — a real, schema-valid `docs/parity_ledger/infrastructure.yaml` entry is added.**
- Covered by the AC2 test above (same entry, same assertions) plus whatever
  `docs/parity_ledger/schema.json` validator already runs generically over the file (locate and
  reuse — do not hand-roll a duplicate).

## Conditional: If the Routing-Integration Open Question Is Resolved as "Build (b)"

Only relevant if Plan/human decides to build parity-routing preference. Not scoped by default per
investigation.md's open question.
- Test name: `test_parity_provider_prefers_impact_when_changed_paths_present`
- Category: integration
- Verifies: a parity-shaped query with a real `changed_paths` value routes through
  `impact(changed_path=...)` instead of `entry()`, and the existing
  `test_changed_path_impact_call_is_not_wired_by_this_ticket` guard is explicitly rewritten (not
  deleted) in the same change to assert the new, intentional behavior.
- Location: `tests/tools/test_knowledge_gateway_router.py`

## Scoped Pytest Commands

```
.venv/bin/python3 -m pytest tests/tools/test_knowledge_gateway_mcp.py tests/tools/test_knowledge_gateway_cache.py tests/tools/test_knowledge_gateway_contract_schemas.py tests/tools/test_evidence_cache_identity_contract.py tests/tools/test_retrieval_cache.py -q
```

Narrower, changed_paths-specific slice for fast iteration:
```
.venv/bin/python3 -m pytest tests/tools/ -k "changed_paths or working_tree_overlap" -q
```

If the routing-integration open question is resolved as "build (b)", additionally:
```
.venv/bin/python3 -m pytest tests/tools/test_knowledge_gateway_router.py tests/tools/test_knowledge_gateway_packet_assembly.py -q
```

Never `pytest tests/` — scope stays within `tests/tools/` (Knowledge Gateway MCP domain).

## Anti-Drift Test Guards

- `tests/tools/test_knowledge_gateway_router.py::test_changed_path_impact_call_is_not_wired_by_this_ticket`
  — the single most important guard for this ticket: catches any accidental/silent wiring of
  `impact()`/`changed_path` into `_run_parity_provider()` before that decision is deliberately made.
- `tests/tools/test_knowledge_gateway_cache.py` module-docstring-referenced guards (e.g.
  `test_module_does_not_import_knowledge_gateway_router_or_packet_assembly`, if present under that
  or a similar name) — catch accidental new coupling between the cache module and routing/packet
  modules while touching `changed_paths` plumbing.
- `tests/tools/test_knowledge_gateway_contract_schemas.py`'s `additionalProperties: false` schema
  assertions — catch any accidental widening of the request schema beyond `changed_paths` itself
  (this ticket's Out-of-Scope explicitly prohibits exposing any other internal mechanic as a new
  caller option).
- Full existing `test_knowledge_gateway_mcp.py` Level 1/Level 2 hit/miss/fallthrough suite — catches
  any regression to cache semantics introduced while touching the shared `request` dict plumbing.
