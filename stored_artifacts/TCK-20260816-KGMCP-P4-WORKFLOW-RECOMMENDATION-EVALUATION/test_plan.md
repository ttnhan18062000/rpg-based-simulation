---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260816-KGMCP-P4-WORKFLOW-RECOMMENDATION-EVALUATION
artifact_type: test_plan
tags: [ai, mcp, testing]
---

# Test Plan — TCK-20260816-KGMCP-P4-WORKFLOW-RECOMMENDATION-EVALUATION

This ticket produces no code and no runtime behavior change (Out of Scope forbids any diff to
`.claude/workflows/*.js`, `.claude/skills/*/SKILL.md`, or `.claude/agents/*.md`). Its deliverable is a
recommendation document. "Testing" this deliverable therefore means testing the document's own
*structure and citation integrity* — mirroring `tests/docs/test_redaction_retention_policy_doc.py`'s
precedent for a documentation-only Knowledge Gateway MCP ticket — never asserting new runtime behavior
that does not exist.

## Regression Surface

No source or workflow code changes, so no runtime regression surface applies. The only pre-existing
tests this ticket's own new doc-structure test must not disturb:

- **unit / docs:** `tests/docs/test_doc_integrity.py`, `tests/docs/test_contributor_guardrails.py`,
  `tests/docs/test_design_patterns_currency.py`, `tests/docs/test_redaction_retention_policy_doc.py`,
  `tests/docs/test_prescan_mandate_instruction_draft.py` — the sibling doc-structure test suite the new
  test file joins; run the whole directory to confirm no naming/fixture collision.
- **unit / parity ledger schema:** any existing `docs/parity_ledger/` schema-validation test (e.g.
  `tools/validate_frontmatter.py`-backed or `parity_index.py`-backed checks already covering
  `infrastructure.yaml`) — the new `INFRA-353` entry this ticket's own Implement/Parity phase adds must
  not break schema validation for the file as a whole.

## New Tests Required

1. **Test name:** `test_phase4_workflow_recommendation_doc_exists_and_has_required_sections`
   **Category:** unit (doc-structure, static assertion — mirrors
   `test_redaction_retention_policy_doc_exists_and_has_required_sections`)
   **Verifies:** `docs/engine/contracts/knowledge_gateway_mcp/phase4_workflow_recommendation.md` exists
   and contains, as literal substrings, a required-heading set covering at minimum: a headline/verdict
   section, one section per candidate integration point this investigation identified (Scope/Investigate
   phases; Document-Update/doc-updater; Architecture Review; the dormant shadow-packet hook), and an
   explicit "does not create a mandatory phase/gate/ticket step" statement.
   **Where:** `tests/docs/test_phase4_workflow_recommendation_doc.py` (new file).

2. **Test name:** `test_every_candidate_point_has_an_explicit_recommendation_verdict`
   **Category:** unit (doc-structure)
   **Verifies:** each candidate-point section contains one of the three literal verdict markers this
   ticket's own Acceptance Criteria require (e.g. `**Recommend:**`, `**Recommend against:**`,
   `**Insufficient evidence:**` — exact strings to be fixed once the recommendation doc's own final
   heading text is written in Plan/Implement) — catches a candidate point silently left unaddressed,
   which AC2 explicitly forbids.
   **Where:** `tests/docs/test_phase4_workflow_recommendation_doc.py` (same file as above).

3. **Test name:** `test_recommendation_doc_cites_real_evidence_paths_not_fabricated`
   **Category:** unit (doc-structure / citation integrity)
   **Verifies:** every numeric latency/token claim in the document is adjacent to (same paragraph or
   table) a citation to one of the three real measurement docs
   (`phase1_baseline_comparison.md`, `phase2_baseline_recomparison.md`,
   `phase3_pilot_acceptance_measurement.md`) or `RETRO-2026-W33.md`, and that each of those four cited
   paths actually exists on disk (`Path(...).exists()`) — this is the concrete, automatable proxy for
   "no candidate recommendation is asserted without citing real retro/measurement data" (AC2). It cannot
   verify the *numbers themselves* are transcribed correctly (that is a human/Architecture-Verify
   judgment call against the source docs), but it can catch the doc citing a source that does not exist,
   or making a quantitative claim with zero adjacent citation.
   **Where:** `tests/docs/test_phase4_workflow_recommendation_doc.py` (same file).

4. **Test name:** `test_recommendation_doc_never_states_a_mandatory_requirement`
   **Category:** unit (anti-drift / anti-mandate guard)
   **Verifies:** the document contains none of a small deny-list of mandate-shaped phrases in a
   normative context — e.g. a regex-guarded check that `must call`, `is required to call`, `shall
   invoke`, or `mandatory ... gateway` do not appear describing the gateway itself (the phrase "does not
   create a mandatory phase" is explicitly allow-listed since it is itself a negation). This is the
   direct static enforcement of AC3 and of `tmp/mcp-followup-instruction.md` §1's "should not
   mechanically require" prohibition, and of this ticket's own Out of Scope.
   **Where:** `tests/docs/test_phase4_workflow_recommendation_doc.py` (same file).

5. **Test name:** `test_infra_353_parity_entry_is_schema_valid_and_certifies_methodology_not_conclusion`
   **Category:** integration (parity ledger schema)
   **Verifies:** `docs/parity_ledger/infrastructure.yaml` parses, contains an entry with `id: INFRA-353`
   (or whatever ID is actually free at Implement time — re-check, do not hardcode past the point of
   drift) matching `schema.json`'s `required: [id, text, status, priority]` plus (since `status` will be
   `verified`) the schema's own conditional `v2_evidence`/`test_path` requirement, and that its `text`
   field explicitly states it certifies the evaluation *methodology*, not any particular workflow
   integration's correctness — mirroring `INFRA-344`'s own "This entry certifies the measurement tool
   itself as real, correct, and tested -- it does NOT claim the measured cache/gateway performance
   succeeded" phrasing pattern (`docs/parity_ledger/infrastructure.yaml:9352-9353`).
   **Where:** existing parity-ledger schema-validation suite (locate via
   `grep -rl infrastructure.yaml tests/tools/ tests/docs/` at Implement time), or a new
   `tests/docs/test_phase4_workflow_recommendation_doc.py`-adjacent case if no existing suite already
   parametrizes over all `infrastructure.yaml` entries.

## Scoped Pytest Commands

```
pytest tests/docs/ -v
pytest tests/docs/test_phase4_workflow_recommendation_doc.py -v
pytest tests/tools/test_knowledge_gateway_contract_schemas.py -v   # confirm no schema drift from citing these docs
```

Never `pytest tests/` — scoped to the docs/knowledge-gateway domain this ticket touches, per this
repo's Testing Rule.

## Anti-Drift Test Guards

- **Guard against scope creep into implementation:** none of the tests above may assert anything about
  `.claude/workflows/*.js`, `.claude/skills/*/SKILL.md`, or `.claude/agents/*.md` file *contents*
  changing — only that the recommendation document exists and is well-formed. A test that greps those
  files for a new gateway call site would itself be evidence of scope creep and must not be added.
- **Guard against silently softening a real FAIL into a recommendation:** test 3 above
  (citation-existence check) is deliberately shallow — it cannot verify numeric accuracy — so the
  Architecture-Verify pass on this ticket must independently spot-check at least one FAIL-carrying claim
  (e.g. the Phase 1 cold-latency numbers, or Phase 3's §12 budget-enforcement FAIL) against its cited
  source doc by direct read, not by trusting this test's green result alone. This mirrors
  `RETRO-2026-W33.md`'s own "never trust a reviewer's or planner's own suggested fix at face value —
  re-verify it against the live file" discipline.
- **Guard against the INFRA-353 entry drifting into a conclusion-certifying entry:** test 5's explicit
  check for "certifies methodology, not conclusion" phrasing exists specifically to catch a future edit
  that quietly upgrades the entry's language into asserting a workflow integration is validated —
  which this ticket's own Acceptance Criteria explicitly forbid, since no integration is implemented.
