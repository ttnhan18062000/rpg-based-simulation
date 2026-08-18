---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260816-KGMCP-P5-REPEATED-DEMAND-MEASUREMENT
artifact_type: test_plan
tags: [ai, mcp, testing]
---

# Test Plan — TCK-20260816-KGMCP-P5-REPEATED-DEMAND-MEASUREMENT

This ticket is measurement-and-recommendation only (no gateway/cache source file is modified — see
Out of Scope). Its Investigate-phase preliminary script
(`staging_artifacts/.../investigate_measurement_script.py`) is not itself wired into the test suite.
This test plan describes (a) the regression surface that must stay green because nothing here should
touch it, and (b) the real tests required if/when Implement formalizes this measurement into a
committed artifact (mirroring `tools/agent-monitoring/kgmcp_phase4_direct_tool_comparison_runner.py`
+ `tests/tools/test_kgmcp_phase4_direct_tool_comparison.py` + a committed
`tests/tools/fixtures/kgmcp_phase5_*_results.json`), per this repo's own Phase 1-4 precedent.

## Regression Surface

Nothing in `tools/knowledge_gateway_cache.py`, `tools/knowledge_gateway_router.py`,
`tools/knowledge_gateway_packet_assembly.py`, or any other gateway source file is touched by this
ticket. The following existing suites must remain green, unmodified, as proof this ticket made no
behavioral change to the gateway itself:

**Unit**
- `tests/tools/test_kgmcp_measurement_baseline.py`
- `tests/tools/test_kgmcp_phase1_baseline_comparison.py`
- `tests/tools/test_kgmcp_phase2_baseline_recomparison.py`
- `tests/tools/test_kgmcp_phase3_pilot_acceptance_measurement.py`
- `tests/tools/test_kgmcp_phase4_direct_tool_comparison.py`
- `tests/tools/test_registry_query.py` (this ticket's own script imports
  `candidate_tags_from_text()` unmodified — confirm the function's existing tests still pass and no
  accidental edit slipped into `tools/registry_query.py`)
- `tests/tools/test_tag_registry.py`

**Integration**
- `tests/tools/test_knowledge_gateway_failure_semantics.py` (Phase 1 fail-open coverage — unrelated
  to this ticket but shares the `tools/knowledge_gateway_*` module family; confirms no accidental
  import-time side effect)

**Docs/parity content-lock**
- `tests/docs/test_redaction_retention_policy_doc.py` (precedent pattern for doc-vs-code content-
  lock tests; the new Phase 5 measurement doc, once written, should get an analogous test — see New
  Tests Required)

## New Tests Required

If/when this ticket's recommendation is formalized into a committed measurement artifact (Implement
phase's decision, not this ticket's own scope), the following tests are required — one per real
claim this investigation makes that could silently drift or regress:

1. **`test_camel_regex_excludes_bare_acronyms_and_digit_joined_tokens`**
   - Category: unit
   - Verifies: the identifier-extraction CamelCase regex does NOT match `INFRA`, `STRAT`, `TOWN`,
     `TCK`, or `E2E` (the exact false positives this investigation caught and fixed), and DOES match
     genuine symbols like `EventRecorder`, `ResourceNodeUpdate`, `DecisionTraceIndex`.
   - Location: `tests/tools/test_kgmcp_phase5_repeated_demand_measurement.py` (new file, mirroring
     the naming convention of `test_kgmcp_phase4_direct_tool_comparison.py`)

2. **`test_parity_id_regex_extracts_specific_entries_not_bare_prefixes`**
   - Category: unit
   - Verifies: `INFRA-206`, `STRAT-227`, `TOWN-173` extract as specific parity-entry identifiers;
     a bare `INFRA` with no trailing `-NNN` does not.
   - Location: same new file

3. **`test_intent_classifier_buckets_known_summaries_correctly`**
   - Category: unit
   - Verifies: a small fixed table of real, hand-picked summaries from `events.jsonl` (e.g. the
     `TCK-20260619-E22C-REST-API` / `TCK-20260702-OBSISO-TRACE-ASYNC` pair — real matched-pair data
     found in the preserved `investigate_events_jsonl_measurement_output.json:31,58-59`, not named in
     investigation.md's own prose examples) classify into the expected intent bucket — guards against
     silent classifier drift if the keyword lists are edited later.
   - Location: same new file

4. **`test_repeated_pair_requires_same_intent_and_specific_identifier_not_tag_alone`**
   - Category: unit
   - Verifies: two synthetic records sharing only a subsystem-topic tag (no specific identifier) are
     NOT counted as a repeated-demand pair; two records sharing both intent and a specific
     identifier ARE counted. This is the load-bearing conservative-matching guarantee this
     investigation's whole result depends on — must never silently degrade to tag-only matching.
   - Location: same new file

5. **`test_phase5_measurement_reproduces_committed_fixture_counts`**
   - Category: integration / regression
   - Verifies: re-running the measurement script against a frozen, committed snapshot of the
     relevant `events.jsonl`/`working_log.csv` rows (not the live, growing files, which would make
     this test non-deterministic and non-reproducible — mirrors Phase 1-4's own "frozen corpus"
     discipline) reproduces the exact committed pair counts (17 primary, 372 secondary) and the
     exact ticket-involvement percentages.
   - Location: `tests/tools/test_kgmcp_phase5_repeated_demand_measurement.py`, using a new
     `tests/tools/fixtures/kgmcp_phase5_repeated_demand_measurement_results.json` fixture (mirrors
     the existing `kgmcp_phase4_direct_tool_comparison_results.json` pattern)

6. **`test_infra_355_parity_entry_matches_committed_measurement_numbers`**
   - Category: architecture guard / doc-parity content-lock
   - Verifies: the new `docs/parity_ledger/infrastructure.yaml` `INFRA-355` entry's stated numbers
     (17 pairs / 521 tickets / 5.8%, or whichever final numbers Implement commits) match the
     committed fixture exactly — mirrors
     `tests/docs/test_redaction_retention_policy_doc.py`'s existing doc-vs-code content-lock pattern,
     preventing the doc and the measurement from silently drifting apart.
   - Location: `tests/docs/test_phase5_repeated_demand_measurement_doc.py` (new)

7. **`test_phase5_proposal_doc_annotation_does_not_overclaim_done`**
   - Category: architecture guard
   - Verifies: `docs/plans/knowledge-gateway-mcp-proposal.md` §20 Phase 5's three bullets are not
     marked as a blanket "Done" in the doc text unless a corresponding real, tested capability
     exists — mirrors the Phase 3/4 precedent of never overclaiming (`INFRA-344`'s own explicit "does
     NOT claim... succeeded" convention). A cheap regex/string-presence check against the doc file
     is sufficient; no need for a full doc parser.
   - Location: `tests/docs/test_phase5_repeated_demand_measurement_doc.py`

## Scoped Pytest Commands

```
pytest tests/tools/test_kgmcp_measurement_baseline.py tests/tools/test_kgmcp_phase1_baseline_comparison.py tests/tools/test_kgmcp_phase2_baseline_recomparison.py tests/tools/test_kgmcp_phase3_pilot_acceptance_measurement.py tests/tools/test_kgmcp_phase4_direct_tool_comparison.py -v

pytest tests/tools/test_registry_query.py tests/tools/test_tag_registry.py -v

pytest tests/tools/test_kgmcp_phase5_repeated_demand_measurement.py tests/docs/test_phase5_repeated_demand_measurement_doc.py -v   # once created by Implement
```

Never `pytest tests/` — scoped to the `tools/`-level KGMCP/registry domain only, per this repo's
Testing Rule.

## Anti-Drift Test Guards

- A test that asserts the tag-only pair count (427 primary / 10,347 secondary) is reported
  separately from, and never silently merged into, the conservative repeated-demand count — guards
  against a future edit quietly loosening the matching criterion back to tag-only.
- A test that asserts `candidate_tags_from_text()` is imported, not reimplemented, in the eventual
  committed runner (mirrors this repo's existing "imported, never reimplemented" discipline seen in
  Phase 1-4's own `_compute_threshold_4_3`/`_normalize_phase1_source_id` reuse pattern) — guards
  against silent duplication/drift of the tag-matching logic.
- A test that asserts the eventual committed fixture's `total_tickets` counts (521 primary / 1,411
  secondary) are read from a frozen snapshot file, not the live, still-growing `events.jsonl` /
  `working_log.csv` — guards against the measurement becoming non-reproducible as those files keep
  growing after this ticket closes.
- A test that the recommendation document/parity entry explicitly cross-references Phase 3's real
  FAIL (`INFRA` entries tied to `phase3_pilot_acceptance_measurement.md`) and Phase 4's real 7/7
  negative comparison by file path — guards against a future edit dropping the economics
  cross-reference and treating repeated-demand alone as sufficient justification, which this
  ticket's own Acceptance Criteria explicitly forbid.
- **New (Architecture Review 1st pass):** a test that asserts the frozen `agent-monitoring/events.jsonl`
  snapshot fixture contains zero records with `run_id == "TCK-20260816-KGMCP-P5-REPEATED-DEMAND-
  MEASUREMENT"` (this ticket's own ID) — guards against the specific, confirmed-live self-
  contamination hazard where this ticket's own mandatory Investigate-phase monitoring write lands in
  the exact dataset the ticket measures. Any ticket whose own methodology counts per-ticket
  Investigate-phase summaries will structurally self-taint by Implement time unless explicitly
  excluded; this test makes that exclusion permanent and checkable, not just a one-time fix.
