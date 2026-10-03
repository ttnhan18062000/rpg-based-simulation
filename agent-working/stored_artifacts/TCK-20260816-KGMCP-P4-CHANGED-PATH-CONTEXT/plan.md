---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260816-KGMCP-P4-CHANGED-PATH-CONTEXT
artifact_type: plan
tags: [ai, mcp]
---

# Implementation Plan — TCK-20260816-KGMCP-P4-CHANGED-PATH-CONTEXT

## Summary

Investigate found AC1–AC3 already substantively satisfied by prior sibling tickets' incidental
work: `changed_paths` is a real, live, tested, caller-facing optional field on
`_run_knowledge_context()` (`tools/knowledge_gateway_mcp.py:153`), already wired into integration
point (a) — cache-validity revalidation via `working_tree_overlap_forces_revalidation()` — at both
Level 1 (`tools/knowledge_gateway_cache.py:290-313` → `:214-229` → `:206-211`) and Level 2
(`:496-529` → `:249-283` → `:267-268`), with a real passing end-to-end behavior-change test
(`tests/tools/test_knowledge_gateway_mcp.py:820-834`). This plan does **not** write new
`tools/`/`src/` code to re-prove those criteria — doing so would be manufactured, redundant work per
CLAUDE.md's gate-gaming rule and investigation.md's Risk 2.

The one genuinely open item — routing integration point (b), preferring the Parity adapter's
`impact(changed_path=...)` over `entry()` when `changed_paths` is present on a parity-shaped query —
is decided in this plan, not deferred: **do not build it.** Reasoning (see "Decision Record"
below). This plan is therefore scoped to: (1) confirming the already-live behavior with a
regression run (no code change), (2) adding the AC4 `INFRA-352` parity ledger entry that documents
both the live (a) wiring and the declined (b) decision, (3) a small content-assertion test locking
that documented decision in place so it cannot silently erode, and (4) marking
`docs/plans/knowledge-gateway-mcp-proposal.md` §20 Phase 4's "Add changed-path-aware task context."
bullet **Done**, following the file's own established bullet-annotation pattern (see e.g. line 1368
for `INFRA-351`'s bullet).

## Decision Record — Option (b) Is Not Built

Reasoning, made explicit for the record (this is a planner-level decision per the launching
session's explicit direction to decide rather than defer; it remains open to override before
Implement runs):

1. **Textual scope conflict is not resolved by "additive-only" framing.** The ticket's Out of Scope
   says: "Any change to the Parity adapter itself... this ticket may call into it once it exists,
   but does not build it." `_run_parity_provider()`'s current body
   (`tools/knowledge_gateway_router.py:292-312`) calls only `entry()` — see its own docstring at
   `:292-306`: "In-process call to tools/parity_index.py::entry() only -- never impact()/health()".
   Making it conditionally call `impact()` instead is a change to *which function the adapter calls
   and when* — i.e. the adapter's own routing behavior — not a caller-side use of an already-fixed
   interface. "Calling into it" (in scope) means invoking the adapter's existing, stable contract;
   changing that contract's internal decision of which underlying provider function it invokes is
   adapter-building work, regardless of whether the new parameter is additive.
2. **Shape mismatch reinforces that this is real adapter design work, not a thin passthrough.**
   `tools/parity_index.py:599` — `impact(changed_path=None, test_path=None, symbol=None,
   db_path=None)` — takes a single `changed_path` (singular), while the gateway's field is
   `changed_paths` (plural, a list). Wiring one into the other requires a real design decision
   (loop over paths? first match? union/dedup of per-path results? what if the query is
   `changed_paths`-shaped but not parity-shaped?) that belongs to the Parity adapter ticket's scope,
   not this one's.
3. **A sibling ticket committed a deliberate, named guard against exactly this.**
   `tests/tools/test_knowledge_gateway_router.py:486-489`
   (`test_changed_path_impact_call_is_not_wired_by_this_ticket`) AST-inspects
   `_run_parity_provider()`'s real body and asserts `"impact" not in called_attrs` and
   `"changed_path" not in kwarg_names`. The test's own name states "is not wired by this ticket" —
   i.e. by `TCK-20260816-KGMCP-P4-CHANGED-PATH-CONTEXT`, this ticket. That is as explicit an
   in-repo signal as exists that wiring (b) here should be a deliberate, separately-justified
   amendment, not a default outcome of this ticket's normal scope.
4. **No concrete demand exists.** No failing test, no measured routing-quality gap, and no
   ticket/user complaint currently shows `entry()` (exact-id/status lookup) underperforming
   `impact()` (reverse dependency/blast-radius lookup) for the `requirement_completeness_verification`
   routing row. `impact()` answers a structurally different question than `entry()`; assuming it
   would produce "better" results for a changed-paths-aware query is speculative without a real use
   case exercising it.
5. **Precedent.** This session's own DEDUP-BUDGET-ENFORCEMENT ticket narrowed scope honestly when
   Investigate found the premise already met, rather than manufacturing new work. The same
   discipline applies here: AC1–AC3 are real and already met; inventing routing work to make the
   ticket "feel bigger" would be the failure mode CLAUDE.md's gate-gaming rule exists to prevent.

Because (b) is declined, `test_changed_path_impact_call_is_not_wired_by_this_ticket` and its
sibling `test_symbol_filter_on_impact_remains_unused_for_parity_provider`
(`tests/tools/test_knowledge_gateway_router.py:492-495`) require **no changes** — they continue to
assert the true, intended state.

## Steps

### Step 1 — Confirm the already-live behavior with a regression run (no code change)
**Files:** none changed. Verification only.
**Change:** Run the scoped regression slice from `test_plan.md` to reconfirm, in this session, that
AC1 (real field on schema/signature — `tools/knowledge_gateway_mcp.py:153`, request-schema property
already declared per `docs/engine/contracts/knowledge_gateway_mcp/knowledge_context_request.schema.json`)
and AC3 (real behavior-change test) are genuinely green before any doc/ledger work references them
as fact:
```
.venv/bin/python3 -m pytest tests/tools/test_knowledge_gateway_mcp.py tests/tools/test_knowledge_gateway_cache.py tests/tools/test_knowledge_gateway_contract_schemas.py tests/tools/test_evidence_cache_identity_contract.py tests/tools/test_retrieval_cache.py -q
```
Also run the anti-drift guard explicitly, to confirm the declined-(b) state is currently intact
before Step 4/5 documents it:
```
.venv/bin/python3 -m pytest tests/tools/test_knowledge_gateway_router.py -k "changed_path or impact" -q
```
**Do NOT touch:** Any file under `tools/` or `src/`. This step is read-only verification.
**Verify:** All listed tests pass (per test_plan.md's "Already-Passing Coverage", the first command
was already spot-verified passing this session for the `changed_paths` slice; full command re-runs
the complete regression surface named in test_plan.md).

### Step 2 — Add the `INFRA-352` parity ledger entry (AC2 + AC4)
**Files:** `docs/parity_ledger/infrastructure.yaml`
**Change:** Add a new entry via `tools/parity_ledger_writer.py::write_entry()` (not a hand-rolled
YAML dump — `tests/tools/test_parity_ledger_writer.py:168-187`
(`test_writer_never_bypasses_validation_via_direct_yaml_dump`) is a regression guard that requires
all new entries to route through `validate_entry()`; `write_entry()` is the only sanctioned
insertion path and enforces schema validity — see `tools/parity_ledger_writer.py`'s `validate_entry`
import chain at `tests/tools/test_parity_ledger_writer.py:16`). The next free id is `INFRA-352` —
re-derive at implementation time by scanning `docs/parity_ledger/infrastructure.yaml` for the
highest existing `INFRA-NNN` id (confirmed this session: last entry is `INFRA-351` at
`docs/parity_ledger/infrastructure.yaml:10053`); do not hardcode if the file has moved on.

Entry fields:
- `id`: `INFRA-352`
- `text`: State plainly that `changed_paths` is a real, optional field on `knowledge_context`'s
  request schema and `_run_knowledge_context()`'s signature (`tools/knowledge_gateway_mcp.py:153`),
  already wired into integration point (a) — cache-validity revalidation via
  `working_tree_overlap_forces_revalidation()` (`tools/knowledge_gateway_cache.py:206-211`) — at
  both Level 1 (`:290-313`/`:214-229`) and Level 2 (`:496-529`/`:249-283`), built incidentally by
  `TCK-20260815-KGMCP-P2-CACHE-READ-WRITE-WIRING` and the Phase 3 packet-cache tickets before this
  ticket formally introduced it as a caller option. State that integration point (b) — routing
  `changed_paths` into the Parity adapter's `impact(changed_path=...)` call — was evaluated and
  **declined**, citing the reasoning in this plan's Decision Record (textual Out-of-Scope conflict,
  singular/plural shape mismatch between `impact(changed_path=...)` and the gateway's
  `changed_paths` list, the deliberately named guard test, and absence of concrete demand).
- `status`: `verified` (the documented behavior — integration point (a) — is real, live, and
  covered by passing tests; this is not a divergence from any Mechanics Bible chapter since this is
  pure infrastructure/tooling, not simulation mechanics).
- `priority`: `P1` (matches sibling entries `INFRA-341`/`343`/`348`/`349`/`351`, all P1, all in the
  same `changed_paths`/Knowledge Gateway MCP lineage).
- `v2_evidence`: Cite the concrete wiring points and the passing end-to-end test:
  `tools/knowledge_gateway_mcp.py:153` (signature), `:167-168` (request-dict threading),
  `tools/knowledge_gateway_cache.py:206-211` (`working_tree_overlap_forces_revalidation()`),
  `:214-229`/`:267-268` (Level 1/Level 2 revalidation call sites),
  `tests/tools/test_knowledge_gateway_mcp.py:820-834`
  (`test_level2_hit_rejected_on_changed_paths_intersection_triggers_real_refresh`, reconfirmed
  passing this session).
- `proof_type`: `regression`
- `test_path`:
  `tests/tools/test_knowledge_gateway_mcp.py::test_level2_hit_rejected_on_changed_paths_intersection_triggers_real_refresh`
- `divergence_note`: `null`
- `support_boundary`: State explicitly that this entry documents (a) as already-live/tested, and
  explicitly declines (b), naming the guard test that remains intact:
  `tests/tools/test_knowledge_gateway_router.py::test_changed_path_impact_call_is_not_wired_by_this_ticket`
  (`:486-489`) — "not wired by this ticket, and this ticket's own Plan phase confirms that decision
  stands; `_run_parity_provider()` (`tools/knowledge_gateway_router.py:292-312`) is unchanged by this
  ticket." Cross-reference `INFRA-351`'s own `support_boundary` deferral text so a future reader can
  trace both sides of the sibling-ticket disagreement documented in investigation.md.
**Do NOT touch:** Any other existing entry in `docs/parity_ledger/infrastructure.yaml` (including
`INFRA-341`, `INFRA-343`, `INFRA-348`, `INFRA-349`, `INFRA-351`) — append only, via `write_entry()`,
which is additive by construction.
**Verify:** `write_entry()`'s own `validate_entry()` call succeeds (raises `EntryValidationError` on
any schema violation — confirmed by reading `tests/tools/test_parity_ledger_writer.py:56-134`'s
rejection-path tests); Step 3's content-assertion test below passes.

### Step 3 — Lock the documented decision with a content-assertion test (AC2)
**Files:** `tests/tools/test_parity_ledger_writer.py` (append a new top-level test function; this
file already imports `yaml` at line 8 and already resolves
`docs/parity_ledger/` paths relative to `Path(__file__).resolve().parent.parent.parent`, per
`:10` `_TOOLS_DIR` — reuse the same relative-path pattern for the ledger YAML file, e.g.
`_TOOLS_DIR.parent / "docs" / "parity_ledger" / "infrastructure.yaml"`).
**Change:** Add `test_infra_352_documents_changed_paths_integration_decision()`:
- Load `docs/parity_ledger/infrastructure.yaml` with `yaml.safe_load()`.
- Find the entry with `id == "INFRA-352"`.
- Assert its `text` field mentions `"changed_paths"` and `"working_tree_overlap_forces_revalidation"`.
- Assert its `support_boundary` field mentions `"impact"` and
  `"test_changed_path_impact_call_is_not_wired_by_this_ticket"` (proving the decline decision and
  its guard-test reference are actually recorded, not just asserted in this plan).
- Assert `status == "verified"` and `test_path` is non-empty (mirrors the schema's own
  `verified` → `v2_evidence`+`test_path` required-pair rule from `docs/parity_ledger/schema.json`
  lines 44-56, read this session).
This mirrors the existing doc-content-assertion pattern already used in this codebase for the same
class of claim, e.g.
`tests/tools/test_evidence_cache_identity_contract.py:306-317`
(`test_changed_paths_intersected_with_cached_evidence_paths_approach_is_documented`), which asserts
specific substrings are present in a frozen contract doc rather than re-testing the underlying code.
**Do NOT touch:** The existing test classes/functions already in
`tests/tools/test_parity_ledger_writer.py` (`:1-234`) — add only a new, additive function; do not
rename or restructure existing fixtures (`_entry()` at `:24`) even if convenient, since other tests
in the file depend on their current signatures.
**Verify:** New test passes against the entry written in Step 2. Full file still passes:
`.venv/bin/python3 -m pytest tests/tools/test_parity_ledger_writer.py -q`.

### Step 4 — Mark the proposal doc bullet Done (doc parity)
**Files:** `docs/plans/knowledge-gateway-mcp-proposal.md`
**Change:** The Phase 4 bullet at line 1403, `"- Add changed-path-aware task context."`, currently
carries no `**Done**` annotation, unlike every other completed bullet in this document (e.g. line
1368's `"- Add Parity Ledger routing. **Done** (`TCK-20260816-KGMCP-P4-PARITY-ADAPTER`) — ..."`, and
the Phase 0–3 bullets at lines 1061, 1066, 1070, 1078, 1084, 1090, 1098, 1103, 1108, 1111, 1118,
1123, 1133, 1144, 1151, 1158, 1162, 1167, 1176, 1212, 1224, 1242, 1262, 1302, 1324 — all read this
session, all follow the same `**Done** (TICKET-ID) — <inline evidence/caveat>` shape). Rewrite the
bullet to: `"- Add changed-path-aware task context. **Done**
(`TCK-20260816-KGMCP-P4-CHANGED-PATH-CONTEXT`) — `changed_paths` is a real, optional
`knowledge_context` field, already wired into cache-validity revalidation (integration point (a),
built incidentally by the Phase 2/3 cache-wiring tickets); routing-integration (point (b), preferring
the Parity adapter's `impact(changed_path=...)`) was evaluated and explicitly declined — see
`INFRA-352`."` Keep the caveat inline and short, consistent with how `INFRA-351`'s own two disclosed
limitations are phrased inline in its bullet (lines 1370-1397) rather than omitted.
**Do NOT touch:** Any other bullet in Phase 4 or any other phase section of this file. Do not
reflow or renumber surrounding bullets; this is a single-bullet edit.
**Verify:** No automated test covers this doc's prose directly (confirmed: no test file greps
`knowledge-gateway-mcp-proposal.md` for `"Add changed-path-aware task context"` specifically); this
step is verified by direct read/diff review, consistent with how `INFRA-351`'s own bullet update
was handled (no dedicated test either — cross-checked via `grep -rn "knowledge-gateway-mcp-proposal"
tests/` returning no hits this session).

### Step 5 — Final regression confirmation (no new code paths introduced)
**Files:** none changed. Verification only.
**Change:** Re-run the full scoped test_plan.md command plus the router-specific guard slice to
confirm nothing in Steps 2-4 (all docs/tests, no `tools/`/`src/` production code) regressed anything:
```
.venv/bin/python3 -m pytest tests/tools/test_knowledge_gateway_mcp.py tests/tools/test_knowledge_gateway_cache.py tests/tools/test_knowledge_gateway_contract_schemas.py tests/tools/test_evidence_cache_identity_contract.py tests/tools/test_retrieval_cache.py tests/tools/test_parity_ledger_writer.py tests/tools/test_knowledge_gateway_router.py -q
```
**Do NOT touch:** Nothing — this step is a pure verification gate before Finalize.
**Verify:** All tests pass, including
`test_changed_path_impact_call_is_not_wired_by_this_ticket` and
`test_symbol_filter_on_impact_remains_unused_for_parity_provider`, both unmodified and still
asserting the true state.

## Scope Guards

- Do NOT edit `tools/knowledge_gateway_mcp.py` or `tools/knowledge_gateway_cache.py` — AC1 and AC3
  are already satisfied by existing code; no production code change is needed or wanted there.
- Do NOT edit `tools/knowledge_gateway_router.py::_run_parity_provider()` in any way — no
  `impact()`/`changed_path` wiring, per the Decision Record. This is the ticket's own explicit
  Out-of-Scope clause plus the guard test.
- Do NOT edit or rewrite `tests/tools/test_knowledge_gateway_router.py:486-495`
  (`test_changed_path_impact_call_is_not_wired_by_this_ticket`,
  `test_symbol_filter_on_impact_remains_unused_for_parity_provider`) — both must remain exactly as
  committed by the sibling ticket.
- Do NOT edit `tools/parity_index.py` — untouched per ticket Out of Scope and Decision Record.
- Do NOT edit `docs/engine/contracts/knowledge_gateway_mcp/evidence_cache_identity_contract.md` or
  `docs/engine/contracts/knowledge_gateway_mcp/knowledge_context_request.schema.json` — both already
  correctly describe the live behavior (verified by direct read this session); editing them without
  a real behavior change would be documentation drift.
- Do NOT modify any existing entry in `docs/parity_ledger/infrastructure.yaml` other than appending
  `INFRA-352` — `INFRA-341`/`343`/`348`/`349`/`351` stay exactly as committed.
- Do NOT widen `knowledge_context_request.schema.json`'s `additionalProperties: false` allow-list
  with any new caller option beyond `changed_paths` itself — explicit ticket Out-of-Scope item.
- Do NOT add a second, parallel `changed_paths`-reading code path anywhere "to prove AC1/AC3" — the
  existing path is the only path and is already exercised end-to-end.

## Dependency Map

- Step 1 has no dependencies; run first to establish a clean baseline before any doc/ledger claims
  reference "already passing" as fact.
- Step 2 depends on Step 1 (the ledger entry's `v2_evidence` cites test results that must be
  reconfirmed green first).
- Step 3 depends on Step 2 (asserts against the entry Step 2 writes).
- Step 4 depends on Step 2 (the bullet's inline text references `INFRA-352` by id).
- Step 5 depends on Steps 2-4 (final confirmation that the additive doc/test-only changes introduced
  no regressions).

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC1 — `changed_paths` is a real, optional field on `knowledge_context`'s request schema and `_run_knowledge_context()`'s signature | Already satisfied pre-existing (`tools/knowledge_gateway_mcp.py:153`); Step 1 confirms | `tests/tools/test_knowledge_gateway_contract_schemas.py:179-180`; existing signature read |
| AC2 — the integration-point decision is documented explicitly, with real reasoning | Step 2 (ledger entry text/support_boundary), Step 3 (content-lock test), Decision Record in this plan.md | `tests/tools/test_parity_ledger_writer.py::test_infra_352_documents_changed_paths_integration_decision` (new, Step 3) |
| AC3 — a real test proves `changed_paths` genuinely changes observed behavior for a real input | Already satisfied pre-existing; Step 1 confirms | `tests/tools/test_knowledge_gateway_mcp.py:820-834` `test_level2_hit_rejected_on_changed_paths_intersection_triggers_real_refresh` |
| AC4 — a real, schema-valid `docs/parity_ledger/infrastructure.yaml` entry is added | Step 2 (`write_entry()` enforces schema validity via `validate_entry()`) | `write_entry()`'s internal `validate_entry()` call (raises on violation); Step 3's content-lock test additionally checks required-field presence |

## Anti-Drift Notes

- The single biggest risk named in investigation.md is Implement writing redundant `tools/`/`src/`
  code "to make the ticket feel implemented" because (a) is already fully live. This plan
  deliberately contains zero `tools/`/`src/` production-code steps — only ledger/doc/test-content
  additions. If Implement finds itself about to touch
  `tools/knowledge_gateway_mcp.py`, `tools/knowledge_gateway_cache.py`, or
  `tools/knowledge_gateway_router.py`, stop and re-read this Decision Record — that is drift, not
  progress.
- Do not treat `INFRA-351`'s `support_boundary` deferral text ("changed_paths threading are
  explicitly out of this entry's scope — this ticket's job") as a mandate to build (b). That text
  only establishes *which ticket owns the decision*, not what the decision must be. This plan is
  the deciding document; `INFRA-351`'s text does not override this ticket's own Out-of-Scope
  section (investigation.md's own stated hazard).
- The optional Level 1 explicit `_run_knowledge_context()` end-to-end test suggested in
  test_plan.md's "New Tests Required" section (`test_level1_hit_rejected_on_changed_paths_intersection_triggers_real_refresh`)
  is deliberately **not** added by this plan: AC3's literal text ("a real test proves changed_paths
  genuinely changes observed behavior") is already satisfied by the existing Level 2 end-to-end test
  plus the existing Level 1 unit-level coverage in `tests/tools/test_knowledge_gateway_cache.py`
  (`revalidate_cache_row`/`working_tree_overlap_forces_revalidation` tests). Adding a second
  redundant integration test would be exactly the "manufactured code for count" pattern
  CLAUDE.md's gate-gaming rule and investigation.md's Risk 2 warn against. If a future reviewer
  judges the existing coverage genuinely insufficient, that test remains available in test_plan.md
  as a pre-scoped, ready-to-add option.
- `tests/docs/test_parity_ledger_schema.py` does **not** exist — test_plan.md's suggested location
  for the AC2 test was a guess and is corrected in this plan: the real, only schema-structure test
  is `tests/tools/test_parity_ledger_schema.py` (validates `schema.json`'s own `allOf` structure,
  not per-entry content), and no generic "every entry validates against schema.json" test exists
  anywhere in the repo. `write_entry()`'s own `validate_entry()` call (used in Step 2) is therefore
  the real schema-validity enforcement mechanism for AC4, not a separate test — do not hand-roll a
  duplicate schema validator.
- `tools/parity_index.py:599`'s `impact()` remaining unused is itself intentional per the sibling
  ticket's committed test (investigation.md Risk 3) — any future ticket that wires it must do so as
  a deliberate, explicit, separately-scoped amendment to both this ticket's Out-of-Scope text and
  the named guard test, never as a side effect of unrelated work.
