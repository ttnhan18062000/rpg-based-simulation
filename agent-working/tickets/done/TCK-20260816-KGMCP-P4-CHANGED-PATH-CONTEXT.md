---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260816-KGMCP-P4-CHANGED-PATH-CONTEXT
phase: done
date: 2026-08-16
tags: [ai, mcp]
---

# TCK-20260816-KGMCP-P4-CHANGED-PATH-CONTEXT

## Title
Add a real `changed_paths` caller-facing option to `knowledge_context`

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Proposal §9's `knowledge_context` conceptual input already lists `budget_tokens`; this ticket adds
`changed_paths` alongside it, per `tmp/mcp-followup-instruction.md` §9's explicit guidance that
caller options should express needs ("token budget, changed paths, desired evidence detail, history
relevance") rather than internal implementation mechanics. This ticket's own Investigate phase must
decide where `changed_paths` actually integrates — this is not assumed here.

## Scope
- Add `changed_paths: list[str]` as a real, optional field to `knowledge_context`'s request schema
  and `_run_knowledge_context()`'s real signature.
- Investigate and decide (do not assume) whether `changed_paths` should:
  (a) thread into cache-validity revalidation, reusing the already-live, already-tested
      `working_tree_overlap_forces_revalidation()` primitive (`tools/knowledge_gateway_cache.py`,
      already called by both Level 1's `revalidate_cache_row()` and Level 2's
      `revalidate_context_packet_row()`) — likely the most direct, lowest-risk integration, since
      the underlying mechanism already exists and is already exercised by every cache hit;
  (b) thread into routing (e.g. preferring the Parity adapter's `impact(changed_path=...)` call —
      only relevant once `TCK-20260816-KGMCP-P4-PARITY-ADAPTER` lands; check that ticket's real
      status before assuming this path is available);
  (c) thread into result ranking/prioritization within an already-assembled packet; or
  (d) some combination of the above.
  Document the real decision and reasoning explicitly.
- If Investigate finds `changed_paths` is already effectively covered by the existing cache-validity
  mechanism (i.e. every cache lookup already independently re-derives its own `changed_paths`
  internally via `git diff`/working-tree inspection, making a caller-supplied value redundant or
  even a potential correctness risk if it diverges from the real repo state), report this plainly
  and scope the ticket down accordingly — do not force an integration point that doesn't add real
  value just to satisfy the epic's own bullet.
- Real tests proving whichever integration point is chosen actually changes real behavior for a real
  `changed_paths` value — not merely accepted-and-silently-ignored.

## Out of Scope
- Any change to the Parity adapter itself (`TCK-20260816-KGMCP-P4-PARITY-ADAPTER`'s job) — this
  ticket may call into it once it exists, but does not build it.
- Any change to the underlying `working_tree_overlap_forces_revalidation()` primitive's own logic —
  reused as-is if Investigate chooses path (a).
- Exposing any other internal routing/cache mechanic as a caller option beyond `changed_paths`
  itself — per `tmp/mcp-followup-instruction.md` §9's explicit prohibition.

## Acceptance Criteria
- [x] `changed_paths` is a real, optional field on `knowledge_context`'s request schema and
      `_run_knowledge_context()`'s real signature. (Pre-existing; reconfirmed live this session via
      passing regression suite — `tools/knowledge_gateway_mcp.py:153`.)
- [x] The Investigate-phase integration-point decision (cache validity / routing / ranking / some
      combination / none-needed-because-already-covered) is documented explicitly with real
      reasoning, not assumed. (Decision Record in `staging_artifacts/.../plan.md`; the authoritative
      parity-ledger recording of it is now written — `INFRA-352`'s `text`/`support_boundary` fields
      in `docs/parity_ledger/infrastructure.yaml`, locked in place by
      `tests/tools/test_parity_ledger_writer.py::
      TestInfra352DocumentsChangedPathsIntegrationDecision::test_infra_352_documents_changed_paths_integration_decision`.)
- [x] Whichever integration is chosen, a real test proves `changed_paths` genuinely changes observed
      behavior for a real input — not accepted-and-ignored.
      (`test_level2_hit_rejected_on_changed_paths_intersection_triggers_real_refresh`, reconfirmed
      passing this session; Level 1's own caller-level wiring additionally proven by the two new
      Test-phase tests, `test_revalidate_cache_row_rejects_on_changed_paths_intersection` and
      `test_revalidate_cache_row_survives_unrelated_changed_path`.)
- [x] A real, schema-valid `docs/parity_ledger/infrastructure.yaml` entry is added for this ticket's
      own behavior change. (`INFRA-352`, written via `tools/parity_ledger_writer.py::write_entry()`
      this Parity session; `status: verified`, `priority: P1`, `proof_type: regression`.)

## Related Tickets
- TCK-20260816-KNOWLEDGE-GATEWAY-MCP-PHASE4-EPIC (parent)
- TCK-20260816-KGMCP-P4-PARITY-ADAPTER (optional integration target for routing-path option (b))
- TCK-20260815-KGMCP-P2-CACHE-READ-WRITE-WIRING (DONE; built
  `working_tree_overlap_forces_revalidation()`, the candidate reuse target for option (a))

## Related Docs
- `docs/plans/knowledge-gateway-mcp-proposal.md` §9, §20 Phase 4
- `tmp/mcp-followup-instruction.md` §9
- `docs/engine/contracts/knowledge_gateway_mcp/evidence_cache_identity_contract.md` §5

## Related Stored Artifacts
None yet.

## Related Code Areas
- `tools/knowledge_gateway_mcp.py` (`_run_knowledge_context()`)
- `tools/knowledge_gateway_cache.py` (`working_tree_overlap_forces_revalidation()`)
- `docs/engine/contracts/knowledge_gateway_mcp/knowledge_context_response.schema.json`

## Assumptions / Open Questions
- The integration point (cache validity vs. routing vs. ranking vs. none-needed) is the central open
  question this ticket's own Investigate phase must resolve, not decided here.

## Implementation Notes
Investigate/Plan found AC1–AC3 already satisfied by prior sibling tickets' incidental work:
`changed_paths` is a real, live, tested, caller-facing optional field on
`_run_knowledge_context()` (`tools/knowledge_gateway_mcp.py:153`), already wired into
cache-validity revalidation (integration point (a)) via `working_tree_overlap_forces_revalidation()`
at both Level 1 and Level 2. Plan.md's Decision Record declines integration point (b) (routing
`changed_paths` into the Parity adapter's `impact(changed_path=...)`), citing a real Out-of-Scope
conflict and a committed anti-drift guard test
(`test_changed_path_impact_call_is_not_wired_by_this_ticket`).

This Implement session's real scope, per explicit orchestrator direction narrowing plan.md's steps
to what belongs in the Implement phase (Steps 2 and 4 are owned by the separate Parity and
Document-Update phases this session, per the established per-ticket phase-ownership convention):

- **Step 1 (done)** — Regression-ran the existing `changed_paths` test surface:
  `pytest tests/tools/test_knowledge_gateway_mcp.py tests/tools/test_knowledge_gateway_cache.py
  tests/tools/test_knowledge_gateway_contract_schemas.py
  tests/tools/test_evidence_cache_identity_contract.py tests/tools/test_retrieval_cache.py -q`
  → 198 passed. Also ran the anti-drift guard slice:
  `pytest tests/tools/test_knowledge_gateway_router.py -k "changed_path or impact" -q` → 3 passed.
- **Step 2 (parity ledger `INFRA-352` entry) — explicitly skipped here.** Confirmed via
  `grep -n "INFRA-35" docs/parity_ledger/infrastructure.yaml` that the highest existing id is still
  `INFRA-351` — the entry has not been written yet. Per this session's phase split, writing it is
  the Parity phase's job.
- **Step 3 (content-lock test in `tests/tools/test_parity_ledger_writer.py`) — deferred, not
  written.** Plan.md's own Dependency Map states Step 3 depends on Step 2 (it asserts against the
  `INFRA-352` entry Step 2 writes). Since Step 2 was confirmed not yet done (see above), writing
  Step 3's test now would either (a) reference a non-existent entry and fail by design, or (b)
  require guessing the entry's exact field content before Parity phase writes it — both violate the
  instruction not to write a test designed to fail and the CLAUDE.md gate-gaming rule. Deferring
  Step 3 to whichever later phase runs after `INFRA-352` exists (so both can be verified together)
  is the correct call per plan.md's own stated ordering, not a silent reordering.
- **Step 4 (mark the proposal doc bullet Done) — explicitly skipped here**, per orchestrator
  direction; this is Document-Update phase's job.
- **Step 5 (final regression re-run)** — done: re-ran the full changed_paths + parity-writer +
  router regression surface (`test_knowledge_gateway_mcp.py`, `test_knowledge_gateway_cache.py`,
  `test_knowledge_gateway_contract_schemas.py`, `test_evidence_cache_identity_contract.py`,
  `test_retrieval_cache.py`, `test_parity_ledger_writer.py`, `test_knowledge_gateway_router.py`) →
  251 passed, no regressions. No production code (`tools/`, `src/`) was touched in this session, per
  plan.md's Scope Guards.

No `tools/` or `src/` files were edited. No test files were added or edited (Step 3 deferred). No
docs were edited (Step 4 deferred). This session was verification-only.

## Test Summary
Full regression surface run twice (once per plan.md Step 1, once per Step 5) with identical
results both times: 251 passed, 0 failed, 0 skipped, 16 pre-existing deprecation warnings
(unrelated `jsonschema.RefResolver` deprecation, not introduced by this session). Includes the
anti-drift guard tests `test_changed_path_impact_call_is_not_wired_by_this_ticket` and
`test_symbol_filter_on_impact_remains_unused_for_parity_provider`, both unmodified and still
passing, confirming the declined-(b) state remains intact.

## Files Changed
Implement phase: None. That session made no code, test, or doc file changes — regression
verification only. Step 2 (`docs/parity_ledger/infrastructure.yaml` — `INFRA-352` entry) and Step 3
(`tests/tools/test_parity_ledger_writer.py` — content-lock test) remain outstanding, owned by the
Parity phase (Step 3 also blocked on Step 2 landing first, per plan.md's own Dependency Map).

### Document-Update phase
- `docs/plans/knowledge-gateway-mcp-proposal.md` — §20 Phase 4's "Add changed-path-aware task
  context." bullet marked **Done** (`TCK-20260816-KGMCP-P4-CHANGED-PATH-CONTEXT`), following the
  same inline-caveat-disclosure convention as the immediately preceding `INFRA-351`/`PARITY-ADAPTER`
  bullet. Cites `tools/knowledge_gateway_mcp.py:153`,
  `working_tree_overlap_forces_revalidation()` (`tools/knowledge_gateway_cache.py:206-211`), and the
  passing end-to-end test `test_level2_hit_rejected_on_changed_paths_intersection_triggers_real_refresh`
  for the live, tested integration point (a) capability. Explicitly states routing-integration point
  (b) into the Parity adapter was evaluated and declined, with a one-line reason (adapter-routing
  scope conflict, singular/plural shape mismatch, sibling guard test, no demonstrated need), pointing
  to the forthcoming `INFRA-352` parity ledger entry (Parity phase's job, not yet written) for the
  full reasoning.

Verified: `investigation.md`'s "Docs Requiring Update" section flagged only
`docs/parity_ledger/infrastructure.yaml` (out of scope for Document-Update — Parity phase's
exclusive territory per doc-updater's own family rules). No restructuring of that section was
needed: `check_docs_to_update_coverage()` re-derives ground truth from `investigation.md` plus real
`git status`, and `infrastructure.yaml` will genuinely be touched by the later Parity phase (plan.md
Step 2, `INFRA-352`), so the flagged path will be satisfied once that phase runs — this
Document-Update session correctly touched zero parity-ledger files.

## Completion Summary
This ticket's own Investigate/Plan phase found its central premise already satisfied: `changed_paths`
is a real, live, tested, caller-facing optional field on `_run_knowledge_context()`
(`tools/knowledge_gateway_mcp.py:153`), already wired into cache-validity revalidation (integration
point (a)) at both Level 1 (`revalidate_cache_row()`) and Level 2 (`revalidate_context_packet_row()`)
via the shared `working_tree_overlap_forces_revalidation()` primitive
(`tools/knowledge_gateway_cache.py:206-211`), built incidentally by prior sibling tickets before this
ticket formally introduced `changed_paths` as a caller option. No new gateway code was written or
needed — writing a second, redundant `tools/`/`src/` code path "to make the ticket feel implemented"
would have been exactly the gate-gaming failure mode CLAUDE.md and this ticket's own plan.md
Anti-Drift Notes warn against.

The one genuinely open decision — whether to also route `changed_paths` into the Parity adapter's
`impact(changed_path=...)` call (integration point (b)) — was decided explicitly, not deferred: **not
built**, per plan.md's Decision Record (adapter-routing scope conflict with the ticket's own Out of
Scope section, a real singular/plural shape mismatch between `impact(changed_path=...)` and the
gateway's `changed_paths` list, the sibling-committed guard test
`test_changed_path_impact_call_is_not_wired_by_this_ticket`, and no concrete demand). That guard test
and its sibling `test_symbol_filter_on_impact_remains_unused_for_parity_provider` remain unmodified
and passing.

Test phase found and closed one real, minor gap: Level 1's own caller-level `changed_paths` wiring
had only unit-level coverage of the shared primitive, not a proof exercised from
`revalidate_cache_row()`'s own caller-facing signature the way Level 2 already had via the end-to-end
MCP test. Two new tests were added to `tests/tools/test_knowledge_gateway_cache.py`:
`test_revalidate_cache_row_rejects_on_changed_paths_intersection` and
`test_revalidate_cache_row_survives_unrelated_changed_path`.

Document-Update marked `docs/plans/knowledge-gateway-mcp-proposal.md` §20 Phase 4's
"Add changed-path-aware task context." bullet **Done**, with an inline caveat disclosing that
routing-integration point (b) was evaluated and declined, pointing to `INFRA-352` for the full
reasoning.

Parity: added new entry `INFRA-352` to `docs/parity_ledger/infrastructure.yaml` via
`tools/parity_ledger_writer.py::write_entry()` (`status: verified`, `priority: P1`,
`proof_type: regression`, `v2_evidence` citing the real Level 1/Level 2 wiring line numbers and the
passing end-to-end test, `support_boundary` recording the full declined-(b) reasoning and the guard
test that locks it). Added a content-lock test,
`tests/tools/test_parity_ledger_writer.py::TestInfra352DocumentsChangedPathsIntegrationDecision::test_infra_352_documents_changed_paths_integration_decision`,
mirroring the existing doc-content-assertion pattern in
`test_evidence_cache_identity_contract.py::test_changed_paths_intersected_with_cached_evidence_paths_approach_is_documented`
— it asserts `INFRA-352`'s `text` mentions `changed_paths` and
`working_tree_overlap_forces_revalidation`, its `support_boundary` mentions `impact` and
`test_changed_path_impact_call_is_not_wired_by_this_ticket`, and `status`/`test_path` satisfy the
schema's `verified` requirements — so a future silent edit that drops either half of the disclosed
decision (live wiring vs. declined routing) fails this test. Full
`tests/tools/test_parity_ledger_writer.py` suite re-run: 14 passed. Ran
`python3 tools/parity_index.py build` as a separate, visible call after the write. Checked for
citation drift on prior entries: `tools/knowledge_gateway_cache.py` and `tools/knowledge_gateway_mcp.py`
(the two files `INFRA-352`'s citations point to) are unmodified in the working tree
(`git status --short` shows only `tools/knowledge_gateway_router.py` and
`tools/knowledge_gateway_packet_assembly.py` modified, both from the separate, already-landed
`INFRA-351`/Parity-Adapter sibling ticket, not this one) — no drift correction needed.

All four ACs are now satisfied. This was a "premise already satisfied" ticket: the real caller-facing
capability (integration point (a)) predates this ticket's own Implement session, and this ticket's
real, honest contribution is closing the Level 1 caller-level test gap, making an explicit and
well-reasoned decline decision on integration point (b) with a durable guard against silent future
drift, and recording both facts in the parity ledger and proposal doc — not originating new gateway
behavior.
