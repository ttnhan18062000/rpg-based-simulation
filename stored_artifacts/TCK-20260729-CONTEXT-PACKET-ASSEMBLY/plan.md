---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260729-CONTEXT-PACKET-ASSEMBLY
artifact_type: plan
tags: [ai, schema]
---

# Implementation Plan — TCK-20260729-CONTEXT-PACKET-ASSEMBLY

## Summary

Build `tools/context_packet_assembler.py`, a new standalone, read-only module that assembles a
real `ContextPacket` (per `docs/engine/contracts/context_packet_contract.md` §2) from three
candidate-producing sources: `tools/hybrid_retrieval.py`'s `HybridResult` list (docs, tickets,
investigations, working-log rows), `tools/code_test_index.py`'s `build_records()` output (code
symbols — required as a third input source to satisfy AC1's literal `code_symbol` requirement,
since `HybridResult.kind` can never be `code_symbol`), and hand-built `parity_ledger_entry`-shaped
fixture dicts (Decision A's `parity_ledger_entry` branch — fixture-only, no live
`docs/parity_ledger/*.yaml` parsing pipeline is built). The module normalizes all three shapes into
a common internal `Candidate` dataclass that structurally never carries raw excerpt text (only a
pre-computed hash), then builds `included[]`/`excluded_summary[]` entries with exactly the
contract's 10/4 fields, implements Decision A's per-kind authority/freshness rules and Decision B's
include-both-and-rank conflict resolution (with an explicit, caller-supplied `subject_key` grouping
field since no automatic same-subject detection exists anywhere in the repo), and stubs
`expansion_policy` as a plain marker string. The module is never imported by or referenced from any
`.claude/workflows/*.js` file, and does not implement C1's fusion logic, C3's cache logic, or any
new inclusion/exclusion ranking policy (that belongs to the already-done
`TCK-20260728-DEFAULT-PACKET-CRITERIA`) — it only shapes already-decided candidates into the
contract's field format.

## Steps

### Step 1 — Module skeleton, `Candidate`/`ContextPacket` dataclasses, hash convention
**Files:** `tools/context_packet_assembler.py` (new)
**Change:**
- Create the module with the same sibling-import pattern `tools/hybrid_retrieval.py` and
  `tools/retrieval_cache.py` use: insert `_TOOLS_DIR = Path(__file__).resolve().parent` into
  `sys.path`, then `from hybrid_retrieval import UNRATED, HybridResult, load_registry_index` (plain
  sibling import, not `tools.hybrid_retrieval`, matching the existing convention). Do not import
  anything from `tools/retrieval_cache.py` in this step (see Step 7/Anti-Drift Notes — this module
  never wires in live cache consultation).
- Define `Candidate` (frozen dataclass): `source_id: str`, `kind: str`, `path: str`,
  `heading_or_symbol: str`, `hash: str`, `score: float`, `authority: str`, `freshness: str`,
  `last_verified: str | None = None`, `subject_key: str | None = None`. Deliberately **no raw-text
  field of any kind** — every adapter (Steps 3/4/6) must compute `hash` at construction time and
  discard the source text/record immediately; `Candidate` itself cannot leak raw text because it
  has no field capable of holding it. This is a structural guarantee, not a discipline convention.
- Define `ContextPacket` (frozen dataclass): `packet_id: str`, `corpus_generation: str`,
  `retrieval_version: int`, `budget_requested: int`, `budget_returned: int`,
  `included: list[dict]`, `excluded_summary: list[dict]`, `expansion_policy: str`. `included`/
  `excluded_summary` entries are plain `dict`s (not nested dataclasses) so exact-key-set assertions
  in tests are a direct `set(entry.keys()) == {...}` check.
- Add a private `_hash_content(text_or_serializable) -> str` helper: for a `str`, returns
  `hashlib.sha256(text.encode("utf-8")).hexdigest()`; for a `dict`/list-serializable record, returns
  `hashlib.sha256(json.dumps(obj, sort_keys=True).encode("utf-8")).hexdigest()`. This mirrors
  `retrieval_cache.py`'s `_hash_text()`/`_hash_filters()` convention (`hashlib.sha256(...
  ).hexdigest()` over a `json.dumps(..., sort_keys=True)` for structured data) **by matching the
  same algorithm inline**, not by importing `retrieval_cache._hash_text` (a private,
  underscore-prefixed symbol — importing it would create an undesired cross-module coupling to
  another module's private API for a one-line formula).
- Define `EXPANSION_POLICY_STUB: str = "not_yet_resolved: Open Decisions 5/6 (expansion escalation semantics) deferred — see docs/plans/agent_infrastructure/context_efficient_agent_retrieval/ticket_plan_structure_phase3.md"`
  as a **plain string constant**, not a dict/object, so it can never accidentally expose a field
  resembling real escalation semantics (`max_expansions`, `trigger`, `threshold`).
- Define `DEFAULT_EXCERPT_BUDGET: int = 200` as a documented placeholder constant (no AC specifies a
  real numeric budget-allocation algorithm; that belongs to the already-done
  `TCK-20260728-DEFAULT-PACKET-CRITERIA`).
**Do NOT touch:** `tools/hybrid_retrieval.py`, `tools/retrieval_cache.py`, `tools/code_test_index.py`
(read-only consumption only — no edits to any of the three sibling modules).
**Verify:** No standalone test yet (skeleton only) — exercised by every subsequent step's tests.

### Step 2 — Shared test fixtures mixing REGISTRY-backed and non-registry-backed kinds
**Files:** `tests/tools/test_context_packet_assembler.py` (new)
**Change:** Build shared pytest fixtures (module-level fixture functions or constants, following
`tests/tools/test_hybrid_retrieval.py`/`tests/tools/test_retrieval_cache.py`'s hand-built-fixture
convention — no live `docs/REGISTRY.yaml`/`knowledge.db`/`graph.json` reads):
- At least one `HybridResult` instance representing a REGISTRY-backed `doc` or `ticket`
  (`authority="P0"`/`"P1"`, `freshness="active"`, a distinctive fixture path) and a small
  hand-built `registry_index: dict[str, dict]` (matching `load_registry_index()`'s return shape,
  keyed by `path`, values containing `authority`/`status`/`last_verified`) so Step 4's adapter can
  resolve `last_verified` without touching a real file.
- At least one `code_test_index.py`-shaped dict (`id`/`module`/`symbol`/`docstring`/
  `owned_component`/`associated_tests`, using the real `DOCSTRING_GAP`/`ASSOCIATED_TESTS_GAP`
  sentinels imported from `tools.code_test_index` where relevant) — the non-registry-backed kind.
- A distinctive raw-text marker string embedded in the `HybridResult.text` fixture value (for
  Step 8's leakage test).
**Do NOT touch:** No production code in this step — test file only.
**Verify:** `test_fixture_mixes_registry_backed_and_non_registry_backed_kinds`.

### Step 3 — `code_test_index.py` adapter + generic unrated-kind helper (AC1)
**Files:** `tools/context_packet_assembler.py`, `tests/tools/test_context_packet_assembler.py`
**Change:**
- Add `unrated_candidate(*, source_id, kind, path, heading_or_symbol, content_for_hash, score=0.0, subject_key=None) -> Candidate`:
  a single shared builder that sets `authority=UNRATED, freshness=UNRATED` (imported constant, never
  re-literaled) and `hash=_hash_content(content_for_hash)`. This is the one function that implements
  Decision A's "`code_symbol`, `test`, `graphify_node`, in-progress-ticket-body kinds get
  `unrated`" rule for **any** kind value passed to it — it is reachable for `test`/`graphify_node`
  even though no producer for those kinds exists yet (per Resolved Decision 3 below), without
  inventing a fake ingestion pipeline for either.
- Add `candidate_from_code_index_record(record: dict, *, subject_key=None) -> Candidate`: calls
  `unrated_candidate(source_id=record["id"], kind="code_symbol", path=record["module"].replace(".", "/") + ".py", heading_or_symbol=record["symbol"], content_for_hash=record, subject_key=subject_key)`.
  `docstring`/`associated_tests` (including `DOCSTRING_GAP`/`ASSOCIATED_TESTS_GAP` sentinels) are
  part of the hashed record but are never separately surfaced into any `included[]` field —
  `code_test_index.py`'s sentinel strings must be preserved verbatim inside the hashed record, never
  reinterpreted or re-derived, but this ticket's contract fields have no slot for them beyond the
  hash.
- Ticket's in-progress-body kind requires **no new code**: a `tickets/inprogress/` `HybridResult`
  already carries `authority=UNRATED, freshness=UNRATED` from C1's own `resolve_metadata()` (REGISTRY
  only indexes `tickets/done/`) — Step 4's adapter passes `hr.authority`/`hr.freshness` through
  verbatim, so it inherits this automatically. Do not add a redundant REGISTRY-fallback check here.
**Do NOT touch:** `tools/code_test_index.py` itself — read `build_records()`'s dict shape only, do
not call `build_records()`/`load_graph()`/`iter_admitted_edges()` from this module (the assembler
consumes already-built records passed in by its caller/tests, it does not run the graphify indexing
pipeline itself).
**Verify:** `test_code_symbol_candidate_with_no_registry_entry_gets_unrated_sentinel` (AC1).

### Step 4 — `HybridResult` adapter (REGISTRY-backed passthrough + `last_verified` lookup)
**Files:** `tools/context_packet_assembler.py`, `tests/tools/test_context_packet_assembler.py`
**Change:** Add `candidate_from_hybrid_result(hr: HybridResult, registry_index: dict[str, dict], *, subject_key=None) -> Candidate`:
maps `doc_id`→`source_id`, `path`→`path`, `heading`(+`section` if present)→`heading_or_symbol`,
`rrf_score`→`score`, `kind`→`kind`, `authority`/`freshness`→passthrough verbatim (already resolved
by C1's `resolve_metadata()` — this adapter never re-derives or re-checks REGISTRY membership,
avoiding duplicate logic). `hash = _hash_content(hr.text)`, computed once and `hr.text` is never
otherwise referenced — no field of the returned `Candidate` holds it. `last_verified =
registry_index.get(hr.path, {}).get("last_verified")` (`None` if the path has no registry entry or
the entry has no `last_verified` key — expected for every non-REGISTRY-backed `HybridResult`, and
for REGISTRY-backed docs that predate the `last_verified` field requirement).
**Do NOT touch:** Do not modify `HybridResult`, `resolve_metadata()`, or `load_registry_index()` in
`tools/hybrid_retrieval.py` — call `load_registry_index()` read-only from the caller side (tests
build a fixture `registry_index` dict directly, per Step 2, rather than calling
`load_registry_index()` against a real file).
**Verify:** No standalone AC-mapped test at this granularity (this adapter has no behavior directly
tested in isolation — it exists to be exercised in aggregate by Step 5's Decision B tests and Step 8's
leakage tests). Confirm via `python -c` import smoke check only; no dedicated pytest needed here.

### Step 5 — Decision B conflict resolution and tie-break (AC2)
**Files:** `tools/context_packet_assembler.py`, `tests/tools/test_context_packet_assembler.py`
**Change:** Add `_resolve_subject_conflicts(candidates: list[Candidate]) -> dict[str, str]`
returning `{source_id: inclusion_reason}` for every candidate that is part of a same-`subject_key`
conflict group:
- Group candidates by `subject_key` (candidates with `subject_key is None` are never grouped —
  Decision B only applies to explicitly-marked same-subject candidates; see Resolved Decisions for
  why `subject_key` is explicit/caller-supplied rather than auto-derived).
- Within a group, keep only candidates whose `freshness` is `"active"` or `"authoritative"`
  (`tools/validate_frontmatter.py`'s `STATUS_VALUES` — Decision B's literal trigger condition); a
  group with fewer than 2 such candidates has no conflict.
- Rank the qualifying candidates in a group with a **two-pass stable sort**: first
  `sorted(group, key=lambda c: c.last_verified or "", reverse=True)` (most-recent-first; a missing/
  `None` `last_verified` becomes `""`, the lexicographically smallest string, so it always sorts
  last — the explicit missing-`last_verified` fallback resolution), then
  `sorted(that_result, key=lambda c: ("P0", "P1", "P2").index(c.authority))` (stable, so the prior
  recency order is preserved within an authority tie). The first candidate in the final order is the
  winner.
- Every non-winning candidate in the group gets `inclusion_reason = f"superseded-by:{winner.source_id}"`
  (matching the contract's illustrative, non-normative example format). The winner and every
  ungrouped/non-conflicting candidate get `inclusion_reason = "included"`.
- Both winner and loser(s) are returned in the map — **never drop the loser** from the eventual
  `included[]` list; this function only decides `inclusion_reason` text, not membership.
**Do NOT touch:** Do not implement any automatic same-subject detection (e.g. title/path
similarity) — `subject_key` is always caller-supplied.
**Verify:** `test_two_active_docs_same_subject_both_included`,
`test_lower_ranked_entry_inclusion_reason_names_superseding_source_id`,
`test_tiebreak_falls_back_to_last_verified_when_authority_equal` (AC2).

### Step 6 — `parity_ledger_entry` adapter (Scope item 2, Decision A parity branch)
**Files:** `tools/context_packet_assembler.py`, `tests/tools/test_context_packet_assembler.py`
**Change:** Add `candidate_from_parity_ledger_fixture(entry: dict, *, subject_key=None) -> Candidate`:
takes a hand-built dict shaped like a `docs/parity_ledger/schema.json` entry (`id`, `text`,
`status`, `priority`, and optionally `path`). Maps `entry["id"]` → `source_id` and
`heading_or_symbol`, `entry.get("path", "docs/parity_ledger/infrastructure.yaml")` → `path`,
`kind="parity_ledger_entry"`, **`authority = entry["priority"]` and `freshness = entry["status"]`
verbatim** — no lookup against `AUTHORITY_VALUES`/`STATUS_VALUES`, no clamping/mapping table of any
kind between the parity 5-value `status` enum and REGISTRY's 4-value `status` enum. `hash =
_hash_content(entry)`. `score = 0.0` (parity entries carry no retrieval score). This function does
**not** parse any real `docs/parity_ledger/*.yaml` file — it operates purely on an
already-shaped fixture dict passed in by the caller (see Resolved Decisions — this ticket does not
build a live parity-ledger-scanning ingestion path, since no AC requires it and Scope only requires
the classification branch to exist and be correct).
**Do NOT touch:** `docs/parity_ledger/*.yaml` existing entries (read-only reference material per the
investigation — not parsed by this module at all in this step).
**Verify:** `test_parity_ledger_entry_kind_uses_own_priority_and_status_not_registry_enum`,
`test_parity_ledger_entry_authority_not_coerced_into_registry_authority_values` (Scope bullet 2 —
Decision A's parity branch; no dedicated AC covers this, Scope is binding independently per the
ticket's own text).

### Step 7 — `included[]`/`excluded_summary[]` builders and `assemble_context_packet()` (AC3)
**Files:** `tools/context_packet_assembler.py`, `tests/tools/test_context_packet_assembler.py`
**Change:**
- `build_included_entry(candidate: Candidate, *, inclusion_reason: str, excerpt_budget: int = DEFAULT_EXCERPT_BUDGET) -> dict`
  returns a dict with **exactly** the 10 keys `source_id`, `kind`, `path`, `heading_or_symbol`,
  `hash`, `authority`, `freshness`, `score`, `inclusion_reason`, `excerpt_budget` — no more, no
  fewer; values copied straight from `candidate` plus the two builder-supplied arguments.
- `build_excluded_summary(excluded: list[tuple[Candidate, str]]) -> list[dict]` aggregates by
  `(kind, reason)`: each resulting dict has **exactly** the 4 keys `source_id`, `kind`, `reason`,
  `count`, where `source_id` is the first-encountered candidate's `source_id` within that
  `(kind, reason)` group (a representative example, not an exhaustive list — the contract's
  `excluded_summary[]` shape carries one `source_id`, not a list) and `count` is the group's size.
- `assemble_context_packet(*, packet_id: str, corpus_generation: str, retrieval_version: int, budget_requested: int, included_candidates: list[Candidate], excluded: list[tuple[Candidate, str]] = ()) -> ContextPacket`:
  runs `_resolve_subject_conflicts(included_candidates)` (Step 5) to get the
  `{source_id: inclusion_reason}` map, calls `build_included_entry()` for every candidate in
  `included_candidates` (using the resolved reason, `DEFAULT_EXCERPT_BUDGET` for every entry — no
  per-candidate budget differentiation is implemented, since no AC/Scope bullet requires a real
  budget-allocation algorithm), calls `build_excluded_summary(excluded)`, sets
  `budget_returned = len(included_candidates) * DEFAULT_EXCERPT_BUDGET`, and
  `expansion_policy = EXPANSION_POLICY_STUB`. Returns a populated `ContextPacket`.
**Do NOT touch:** Do not invent any field beyond the contract's exact 10/4 lists on either entry
type; do not add real escalation logic to `expansion_policy`.
**Verify:** `test_included_entry_has_exactly_ten_contract_fields`,
`test_excluded_summary_entry_has_exactly_four_contract_fields`,
`test_expansion_policy_is_a_marked_placeholder_not_real_escalation_logic` (AC3, plus Scope's
expansion_policy stub requirement).

### Step 8 — Raw-text leakage and hash-integrity guards (AC4)
**Files:** `tests/tools/test_context_packet_assembler.py` (tests only — no new production code
expected; this step verifies Steps 1–7's structural guarantees)
**Change:** Add:
- A recursive-walk assertion helper that traverses an assembled `ContextPacket` (via
  `dataclasses.asdict()` or manual field walk) and every `included[]`/`excluded_summary[]` dict's
  values, asserting the Step 2 fixture's distinctive raw-text marker string appears in **no** field
  value anywhere.
- A direct check that `included[]`'s `hash` field equals
  `hashlib.sha256(fixture_text.encode()).hexdigest()` for the `HybridResult` fixture's excerpt text,
  and that this hash value is not equal to, and is not a substring of, the raw fixture text.
If either test fails, it means Step 4's adapter (or a future edit) started copying `hr.text` into a
`Candidate` field — since `Candidate` has no raw-text field (Step 1), this should be structurally
impossible, and this step's tests are the mechanical proof of that guarantee.
**Do NOT touch:** No production code changes anticipated; if either test fails, the fix belongs in
Step 1's `Candidate` definition or Step 4's adapter, not a new special-case in this step.
**Verify:** `test_assembled_packet_never_contains_raw_fixture_text_anywhere`,
`test_hash_field_is_sha256_of_excerpt_not_the_excerpt_itself` (AC4).

### Step 9 — Workflow-isolation guards (AC5) and reverse-dependency guard
**Files:** `tests/tools/test_context_packet_assembler.py` (tests only)
**Change:** Add three static/architecture-guard tests, following
`tests/tools/test_retrieval_cache.py`'s existing AST-parse-the-module-source pattern:
- `test_module_not_referenced_by_any_claude_workflows_file`: grep-scan every file under
  `.claude/workflows/*.js` for the literal string `context_packet_assembler` (filename or import
  path); assert zero matches.
- `test_module_does_not_import_any_claude_workflows_file`: AST-parse
  `tools/context_packet_assembler.py`'s own `import`/`from ... import` statements and assert none
  resolve into `.claude/workflows/`.
- `test_assembler_does_not_import_contextpacket_from_retrieval_cache`: AST-parse
  `tools/retrieval_cache.py`'s source and assert it still contains no `ContextPacket` import or
  class definition (guards the reverse direction — this ticket must not retroactively make
  `retrieval_cache.py` import back from the new module).
**Do NOT touch:** Do not add any import of `tools/context_packet_assembler.py` into
`tools/retrieval_cache.py`, `tools/hybrid_retrieval.py`, `tools/code_test_index.py`, or any
`.claude/workflows/*.js` file, at any point in this ticket.
**Verify:** `test_module_not_referenced_by_any_claude_workflows_file`,
`test_module_does_not_import_any_claude_workflows_file`,
`test_assembler_does_not_import_contextpacket_from_retrieval_cache` (AC5, Out-of-Scope guard).

### Step 10 — Parity ledger append (`INFRA-296`)
**Files:** `docs/parity_ledger/infrastructure.yaml`
**Change:** Append a new entry after `INFRA-295`, following the `INFRA-293`/`294`/`295` format
verbatim: `id: INFRA-296`, `text:` describing the new `ContextPacket` assembler module and its three
candidate sources, `status: verified`, `priority: P2`, `legacy_evidence: null`, `v2_evidence:`
citing `tools/context_packet_assembler.py`'s function/line ranges once written,
`test_path: tests/tools/test_context_packet_assembler.py`, `support_boundary:` matching
`INFRA-293`–`295`'s wording verbatim ("Agent-orchestration/retrieval tooling only — no simulation
behavior, Mechanics Bible chapter, or engine contract governs this module's semantics").
**Do NOT touch:** Existing `INFRA-293`/`294`/`295` entries or any other `docs/parity_ledger/*.yaml`
file — append only.
**Verify:** No new pytest — verified by the repo's existing parity-ledger schema validation
tooling/`done-checker`'s frontmatter/schema checks at ticket close.

## Scope Guards

Verbatim from the ticket's Out of Scope:
- Implementing C1's fusion logic or C3's cache logic itself — this ticket consumes their output
  only, does not reimplement them.
- Any new `agent-monitoring/*.jsonl` event type (Phase 4).
- Shadow packets, workflow adoption, or any `.claude/workflows/*.js` wiring (Phase 5-6).
- Any external vector/graph DB (Qdrant/Postgres/Neo4j/hosted RAG).
- Any lightweight re-ranker beyond fusion+metadata filtering.
- Force-resolving Open Decisions 5 or 6 (`expansion_policy` stays a stub).

Additional guards from this plan and the investigation:
- **MUST NOT be imported by or referenced from any `.claude/workflows/*.js` file** — AC5's own
  grep-regression requirement (Step 9).
- Do not modify `tools/hybrid_retrieval.py`, `tools/retrieval_cache.py`, or
  `tools/code_test_index.py` — pure consumer only.
- Do not modify `docs/REGISTRY.yaml` or any existing `docs/parity_ledger/*.yaml` entry — only a new
  `INFRA-296` append is in scope (Step 10).
- Do not add `tools/validate_frontmatter.py`'s `AUTHORITY_VALUES`/`STATUS_VALUES` enum entries for
  `unrated` or for parity's 5-value `status` enum — those enums govern doc/ticket frontmatter, a
  different namespace from a packet's per-source-item field values, and remain untouched.
- Do not build a real `docs/parity_ledger/*.yaml`-scanning ingestion pipeline — the
  `parity_ledger_entry` branch is proven correct against a fixture dict only (Step 6).
- Do not build a real inclusion/exclusion ranking or token-budget-allocation algorithm — that is
  `TCK-20260728-DEFAULT-PACKET-CRITERIA`'s scope, already done; this module only shapes
  already-decided candidates into the contract's field format, with `DEFAULT_EXCERPT_BUDGET` as an
  explicitly-documented placeholder constant.
- Do not wire in a live `retrieval_cache.check_packet_cache()` call — no AC or Scope bullet requires
  a live cache-consultation code path, and inventing one would be unrequested scope.
- Do not re-literal the `"unrated"` string anywhere — always `from hybrid_retrieval import UNRATED`.
- Do not auto-derive Decision B's "same subject" grouping from path/title similarity — `subject_key`
  is always explicit and caller-supplied.

## Dependency Map

- Step 1 (skeleton) — no dependencies; must land first.
- Step 2 (fixtures) — depends on Step 1 only for import paths; independent of Steps 3–7's logic.
- Step 3 (code_index adapter) — depends on Step 1.
- Step 4 (HybridResult adapter) — depends on Step 1; uses Step 2's `registry_index` fixture for its
  test.
- Step 5 (Decision B) — depends on Step 4 (operates on `Candidate`s the HybridResult adapter
  produces).
- Step 6 (parity adapter) — depends on Step 1 only; independent of Steps 3–5.
- Step 7 (builders + orchestration) — depends on Steps 3, 4, 5, 6 (needs all candidate sources and
  the conflict-resolution map).
- Step 8 (leakage guards) — depends on Step 7 (needs a fully assembled packet) and Step 4 (the
  `HybridResult` excerpt is the leakage-risk source).
- Step 9 (workflow-isolation guards) — independent of Steps 2–8; can run any time after Step 1
  creates the module file.
- Step 10 (parity ledger) — depends on all prior steps landing (needs real line ranges for
  `v2_evidence`); last step.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC1: code_symbol candidate with no REGISTRY entry → `authority=="unrated"`, `freshness=="unrated"` | Steps 1, 3 | `test_code_symbol_candidate_with_no_registry_entry_gets_unrated_sentinel` |
| AC2: two active docs (P0, P1) on same subject both in `included[]`; P1's `inclusion_reason` names P0's `source_id` | Steps 1, 4, 5 | `test_two_active_docs_same_subject_both_included`, `test_lower_ranked_entry_inclusion_reason_names_superseding_source_id`, `test_tiebreak_falls_back_to_last_verified_when_authority_equal` |
| AC3: every `included[]` entry has exactly 10 fields; every `excluded_summary[]` entry has exactly 4 fields | Steps 1, 7 | `test_included_entry_has_exactly_ten_contract_fields`, `test_excluded_summary_entry_has_exactly_four_contract_fields` |
| AC4: assembled packet never contains raw prompt/chunk text in any field | Steps 1, 4, 8 | `test_assembled_packet_never_contains_raw_fixture_text_anywhere`, `test_hash_field_is_sha256_of_excerpt_not_the_excerpt_itself` |
| AC5: module not imported by/referenced from any `.claude/workflows/` file; grep-based regression asserts zero references | Step 9 | `test_module_not_referenced_by_any_claude_workflows_file`, `test_module_does_not_import_any_claude_workflows_file` |
| (Scope bullet 2, not AC-mapped) Decision A's `parity_ledger_entry` branch uses its own priority/status, never coerced into REGISTRY enum | Step 6 | `test_parity_ledger_entry_kind_uses_own_priority_and_status_not_registry_enum`, `test_parity_ledger_entry_authority_not_coerced_into_registry_authority_values` |
| (Scope bullet 4, not AC-mapped) fixture corpus mixes REGISTRY-backed and non-registry-backed kinds | Step 2 | `test_fixture_mixes_registry_backed_and_non_registry_backed_kinds` |
| (Scope bullet 5, not AC-mapped) `expansion_policy` is a marked placeholder, not real escalation logic | Step 7 | `test_expansion_policy_is_a_marked_placeholder_not_real_escalation_logic` |
| (Out-of-Scope guard, not AC-mapped) `retrieval_cache.py` still does not import/define `ContextPacket` | Step 9 | `test_assembler_does_not_import_contextpacket_from_retrieval_cache` |

## Resolved Decisions

1. **`code_test_index.py` as a required third candidate source (the AC1 scope gap).** Resolved: yes
   — the assembler directly consumes `code_test_index.py::build_records()`'s dict output as a third
   input alongside `HybridResult` and parity-ledger fixtures (Step 3). Reason: AC1 literally requires
   a `code_symbol` `included[]` item, and `HybridResult.kind` is structurally incapable of ever being
   `code_symbol` (`_SOURCE_TYPE_TO_KIND` only maps `doc_chunk`/`ticket`/`investigation`/
   `working_log`) — no other module in the repo produces code-symbol-shaped records. This is
   consistent with the ticket's own Related Tickets referencing
   `TCK-20260728-CODE-TEST-INDEX-BOUNDARIES` even though `code_test_index.py` is absent from Related
   Code Areas — treated as an omission in the ticket text, not a signal to skip the module.

2. **`parity_ledger_entry` branch (Scope item 2, no dedicated AC).** Resolved: implement the
   classification branch (Step 6) with authority/freshness populated verbatim from the fixture
   entry's own `priority`/`status`, never coerced into `AUTHORITY_VALUES`/`STATUS_VALUES`. No live
   `docs/parity_ledger/*.yaml`-scanning ingestion path is built, since no producer for this kind
   exists anywhere in the repo today (the corpus excludes `docs/parity_ledger/` entirely) and no AC
   requires one — only Scope requires the branch to exist and be correct, which a fixture-only test
   proves without inventing an unrequested scanning pipeline. A new test is added
   (`test_parity_ledger_entry_kind_uses_own_priority_and_status_not_registry_enum` and its sibling)
   citing Scope, not an AC, as the reason, per the instruction that Scope is binding independent of
   AC coverage.

3. **`graphify_node`/`test` kinds — documented-but-unreachable.** Resolved: no real producer exists
   for either kind and none is invented. Instead, Step 3 introduces one shared, kind-parametric
   builder (`unrated_candidate()`) that correctly implements the `unrated`-sentinel rule for *any*
   kind value passed to it, including `test`/`graphify_node` — so the classification logic is
   genuinely implemented and reachable if a future ticket ever wires a producer for those kinds, but
   no fake pipeline is built to manufacture a live `test`/`graphify_node` candidate today. This
   mirrors the same "prove the function is correct even if nothing calls it live yet" pattern already
   established by `retrieval_cache.py`'s `check_packet_cache()`.

4. **Missing/null `last_verified` fallback for Decision B's tie-break.** Resolved: treat missing/null
   `last_verified` as maximally stale (sorts last within an authority tie) — implemented via a
   two-pass stable sort (Step 5: sort by `last_verified or ""` descending first, then by authority
   ascending). Reason: silently crashing on missing data, or defaulting a missing value to "most
   recent" (which would let an unverified doc win a tie-break over a genuinely-verified one), are both
   worse than a documented, deterministic "missing = oldest" rule.

5. **Decision A implementation shape.** Resolved: no central kind-dispatch/rating-resolver function
   exists — each of the three adapters (Steps 3, 4, 6) hard-codes its own kind-appropriate
   authority/freshness rule directly (REGISTRY-backed passthrough for `HybridResult`, `unrated`
   sentinel via the shared builder for code-index records, verbatim `priority`/`status` passthrough
   for parity fixtures). This is a stronger anti-drift design than a shared dispatch table, since
   there is no single function whose kind-to-rule mapping could be edited incorrectly and silently
   affect all three source types at once. The `tickets/inprogress/` case requires zero special-case
   code, since C1's own `resolve_metadata()` already resolves an in-progress ticket to `UNRATED`, and
   Step 4's adapter passes `authority`/`freshness` through verbatim.

6. **Decision B implementation shape and the "same subject" grouping key.** Resolved: `Candidate`
   carries an explicit, optional `subject_key: str | None` field, populated only by the caller
   (production callers or test fixtures) — never auto-derived from path/title similarity. Reason: no
   automatic same-subject detection mechanism exists anywhere in the repo (confirmed by
   investigation), and the contract's own §3 text explicitly frames Decision B as "advisory guidance
   for a future packet-assembly implementation," not a schema change requiring live automatic
   detection. This keeps the conflict-resolution logic itself (ranking + `inclusion_reason` naming)
   fully implemented and directly tested (Step 5), while avoiding inventing an unrequested
   subject-similarity heuristic.

7. **No live `retrieval_cache.check_packet_cache()` wiring.** Resolved: not implemented. Reason:
   `check_packet_cache()` takes `packet_key_hash`/`current_cited_hashes`/`corpus_generation`/
   `policy_version` — inputs that would logically be derived *from* an already-assembled packet's own
   hashes, not inputs *into* assembly — and no AC or Scope bullet requires a cache-consultation code
   path. Building one would be unrequested scope per the "never plan more work than the ticket scope"
   rule; Out of Scope also explicitly forbids reimplementing C3's logic.

8. **`hash` computation convention.** Resolved: `_hash_content()` (Step 1) matches
   `retrieval_cache.py`'s `hashlib.sha256(...).hexdigest()` over `json.dumps(..., sort_keys=True)`
   formula inline, rather than importing `retrieval_cache._hash_text` (a private, underscore-prefixed
   symbol not intended as cross-module public API). This reuses the established algorithm/convention
   without creating an undesired dependency on another module's private internals.

## Anti-Drift Notes

- `Candidate` (Step 1) has no field capable of holding raw excerpt text — this is the load-bearing
  structural guarantee behind AC4, not a discipline-only convention. Any future edit that adds a
  text-shaped field to `Candidate` should be treated as a direct AC4 regression risk.
- `UNRATED` must always be imported from `hybrid_retrieval`, never re-literaled — two independently
  spelled `"unrated"` sentinels could silently diverge if either is ever renamed.
- `docstring`/`associated_tests` sentinel strings (`DOCSTRING_GAP`/`ASSOCIATED_TESTS_GAP`) from
  `code_test_index.py` records must be preserved verbatim inside the hashed record in Step 3's
  adapter — never reinterpreted, defaulted, or silently dropped before hashing.
- Parity's 5-value `status` enum (`verified`/`divergent`/`missing`/`unsupported`/`legacy_verified`)
  and REGISTRY's 4-value `status` enum (`authoritative`/`active`/`historical`/`archive`) must never
  be coerced into each other anywhere in Step 6 — a well-intentioned "just reuse the REGISTRY-join
  logic for everything" refactor would violate this.
- `docs/parity_ledger/schema.json`'s `priority`/`status` enums are read-only reference material for
  Step 6 — not modified by this ticket.
- Every regression command in the test plan (`test_hybrid_retrieval.py`, `test_retrieval_cache.py`,
  `test_code_test_index.py` full suites, plus `test_knowledge_search.py`'s corpus-scope-guard and
  query-mode-routing tests, plus `test_eval_search.py`) must still pass unmodified — a failure there
  means this ticket's assumed input shapes have drifted, or a corpus/routing side-effect leaked in
  from this ticket's work.
- Never run `pytest tests/` for this ticket — use the three scoped commands in
  `staging_artifacts/TCK-20260729-CONTEXT-PACKET-ASSEMBLY/test_plan.md`'s "Scoped Pytest Commands"
  section.

## Deviations

- **Step 9's `test_assembler_does_not_import_contextpacket_from_retrieval_cache` guard is
  AST-based, not a raw substring search.** The plan/test_plan's phrasing ("confirmed to still not
  import/define a `ContextPacket` class") is satisfied, but a literal `"ContextPacket" not in
  source` substring assertion against `tools/retrieval_cache.py`'s full text false-fails: that
  module's own docstring/Anti-Drift Note text (`:341-343`, `:14-19`) legitimately contains the
  string `"ContextPacket"` while documenting that it does *not* import it
  ("`ContextPacket` does not exist as a class yet... never import or assume a `ContextPacket`
  class/serializer"). The implemented test instead AST-parses `retrieval_cache.py` and asserts
  `"ContextPacket"` is neither a defined `ClassDef` name nor an imported name (`ast.Import`/
  `ast.ImportFrom` alias names) — the actual guard intended (no import, no class definition),
  without false-failing on prose that discusses the dependency's absence. No production code
  changed as a result; this is a test-implementation-only deviation, discovered by running the
  test against the real file and observing the false failure.
- All other steps landed exactly as planned; no other deviation.
