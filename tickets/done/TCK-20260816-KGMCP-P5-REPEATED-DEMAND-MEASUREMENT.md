---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260816-KGMCP-P5-REPEATED-DEMAND-MEASUREMENT
phase: done
date: 2026-08-16
tags: [ai, mcp, testing]
---

# TCK-20260816-KGMCP-P5-REPEATED-DEMAND-MEASUREMENT

## Title
Honestly measure real repeated/semantically-equivalent question demand before investing in Phase 5

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Proposal §20 Phase 5's three bullets (canonical entity IDs/aliases, reuse across compatible
phrasings, conservative semantic candidate matching) are all mechanisms to broaden cache-hit
eligibility beyond exact provider-native-ID identity. `tmp/mcp-followup-instruction.md` §7 already
establishes the precedent this ticket applies: "Before investing heavily in [a further capability
layer], measure how often agents ask semantically repeated project questions... Repeated cache
misses should also be treated as documentation/terminology telemetry." Phase 1-4's own cumulative,
honestly-measured evidence has repeatedly found cache economics unfavorable at real call sites (0/7
hits before a hotfix; a real FAIL on token-budget enforcement; a real 7/7 negative gateway-vs-
direct-tool comparison even on a fresh run). This ticket measures, with real data, whether the
specific problem Phase 5 exists to solve — queries missing the cache due to wording/entity-reference
variance, not due to genuine novelty — is real and material in this repository's actual usage.

## Scope
- Identify and use a real, existing data source for repeated/semantically-equivalent question
  demand — NOT the frozen 7-entry corpus (deliberately built unique-per-entry, cannot demonstrate
  repeated demand by design). Candidate real sources to investigate: `tickets/working_log.csv`'s
  own ticket titles/summaries across this repository's real history (do semantically similar
  questions recur across different tickets, e.g. multiple tickets independently investigating "how
  does X routing work"?); `agent-monitoring/retro/`'s own skill/tool-usage aggregates; `agent-
  monitoring/events.jsonl`'s own Investigate-phase summaries. This ticket's own Investigate phase
  decides which real source(s) are genuinely usable, and documents why others were rejected.
- Define a real, honest, falsifiable method for detecting "semantically repeated" (not identical)
  questions in the chosen real data source — e.g. shared entity/subsystem references plus
  overlapping intent classification, per proposal §11.2's own conservative-equivalence steps
  (normalize → extract identifiers → classify intent → compare). Do not use raw string similarity
  alone (§11.2 explicitly rules this out as insufficient) or embedding similarity alone (also ruled
  out) — the method itself must mirror the conservative, multi-signal approach Phase 5 would
  eventually implement, so the measurement genuinely tests the real mechanism's future utility, not
  a proxy that doesn't resemble it.
- Report the real count/rate of repeated-question demand found, honestly, including a null/negative
  result if that is what the data shows. Cross-reference against Phase 3/Phase 4's own already-
  measured per-hit economics (real FAIL on token-budget; real 7/7 negative comparison) to answer the
  epic's own real question: even if repeated demand exists, would resolving it as cache hits provide
  net-positive value given the currently-unproven per-hit economics, or would it just produce more
  frequent instances of an already-measured-unfavorable outcome?
- Recommend, with real reasoning: proceed with Phase 5's remaining two bullets now; proceed only
  after Phase 3's own disclosed gaps close; or do not proceed (contingent on repeated-demand
  evidence, per proposal §7 of Phase 6 — Phase 5 shares the same "contingent on repeated-demand
  evidence" framing in spirit, applied here for the first time to Phase 5 itself).

## Out of Scope
- Building canonical entity IDs, alias consolidation, or semantic candidate matching — this ticket
  measures and recommends; building (if warranted) is separately-scoped child ticket(s) this
  ticket's own recommendation may propose, not implement itself.
- Closing Phase 3's own two disclosed gaps (budget-tolerance FAIL; dedup never real-corpus-proven) —
  referenced as context for the per-hit-economics question, not fixed here.
- Any change to `tools/knowledge_gateway_cache.py`'s real identity/lookup functions or any other
  gateway/cache/router source file — this ticket is measurement-only, mirroring `TCK-20260816-KGMCP-
  P4-WORKFLOW-RECOMMENDATION-EVALUATION` and `TCK-20260816-KGMCP-P3-PILOT-ACCEPTANCE-MEASUREMENT`'s
  own precedent.
- Making the Knowledge Gateway a mandatory phase, gate, or ticket step in any workflow.

## Acceptance Criteria
- [x] A real, existing, non-corpus data source is used for the repeated-demand measurement, with
      explicit reasoning for why it's a valid real signal (not manufactured/synthetic).
- [x] The equivalence-detection method mirrors proposal §11.2's own conservative, multi-signal
      approach (never raw-string-only or embedding-only), documented and applied consistently.
- [x] The real count/rate of repeated-question demand is reported honestly, including a null/
      negative result if that is what the data shows — no manufactured positive finding.
- [x] The recommendation explicitly cross-references Phase 3/4's own real per-hit-economics findings
      (budget-tolerance FAIL; 7/7 negative comparison) rather than treating repeated-demand alone as
      sufficient justification to proceed.
- [x] A real, schema-valid `docs/parity_ledger/infrastructure.yaml` entry is added, certifying this
      ticket's measurement methodology as sound — not the recommendation's own conclusion — mirroring
      `INFRA-344`/`INFRA-353`'s precedent. **Satisfied in Parity phase**: `INFRA-355` written via the
      schema-validating `write_entry()`, followed by a visible `python3 tools/parity_index.py build`.
      `tests/docs/test_phase5_repeated_demand_measurement_doc.py::
      test_infra_355_parity_entry_matches_committed_measurement_numbers` now passes.

## Related Tickets
- TCK-20260816-KNOWLEDGE-GATEWAY-MCP-PHASE5-EPIC (parent; this ticket gates the epic's remaining
  scope)
- TCK-20260816-KGMCP-P4-WORKFLOW-RECOMMENDATION-EVALUATION (DONE; direct methodological precedent)
- TCK-20260816-KGMCP-P4-DIRECT-TOOL-COMPARISON (DONE; supplies the real 7/7 negative per-hit
  economics finding this ticket must weigh)

## Related Docs
- `docs/plans/knowledge-gateway-mcp-proposal.md` §11.2, §20 Phase 5
- `tmp/mcp-followup-instruction.md` §7

## Related Stored Artifacts
None yet.

## Related Code Areas
- `tickets/working_log.csv`, `agent-monitoring/retro/`, `agent-monitoring/events.jsonl` (candidate
  real data sources)

## Assumptions / Open Questions
- Which real data source(s) are genuinely usable is the central open question this ticket's own
  Investigate phase must resolve, not assumed here.

## Implementation Notes
Implemented per the APPROVED plan.md, Steps 1-5 only (Steps 6-7 explicitly skipped per this
session's per-phase ownership convention — Document-Update owns the proposal-doc annotation,
Parity phase owns the `INFRA-355` ledger entry).

- **Step 1 (self-contamination guard, critical):** Froze `agent-monitoring/events.jsonl`
  (`phase == "Investigate"`, deduped to first event per `run_id`, `{run_id, summary, ts}`) into
  `tests/tools/fixtures/kgmcp_phase5_events_investigate_snapshot.json`, explicitly excluding
  `run_id == "TCK-20260816-KGMCP-P5-REPEATED-DEMAND-MEASUREMENT"` before writing. Independently
  confirmed the raw live file yields 522 records for this extraction (5 of this ticket's own
  Scope/Investigate/Plan/Review×2 events already present in the live file by Implement time,
  confirming the plan's stated hazard), and that the exclusion filter brings it down to exactly
  521 — matching `investigate_events_jsonl_measurement_output.json`'s `total_tickets: 521`. Froze
  `tickets/working_log.csv` (`{ticket_id, title, summary}` for rows with non-empty title or
  summary) into `kgmcp_phase5_working_log_snapshot.json` — exactly 1,411 records.
- **Step 2:** Ported the Investigate-phase script into
  `tools/agent-monitoring/kgmcp_phase5_repeated_demand_measurement_runner.py`. `CAMEL_RE`,
  `PATH_RE`, `TICKET_RE`, `PARITY_ID_RE`, `INTENT_KEYWORDS`, `normalize()`, `classify_intent()`,
  `extract_identifiers()` ported unchanged. `candidate_tags_from_text()` imported unmodified from
  `tools/registry_query.py` (never reimplemented — mechanically verified in Step 3). Both loaders
  (`load_investigate_events()`, `load_working_log_rows()`) read only the frozen Step 1 snapshot
  JSON files, never the live `agent-monitoring/events.jsonl` / `tickets/working_log.csv`. Unified
  the primary/secondary pairwise-comparison logic into one shared `_build_records()` /
  `_compare_records()` path (both loops driven by the same code, per plan.md's explicit
  instruction not to duplicate the comparison logic twice) rather than the two separately-run
  ad hoc scripts Investigate used. Hand-ran `main()` once; it wrote
  `tests/tools/fixtures/kgmcp_phase5_repeated_demand_measurement_results.json` and printed exactly
  17/521 (primary) and 372/1411 (secondary), matching plan.md's independently-re-verified numbers
  bit-for-bit, including the sub-figures (15 strong / 2 ref-only / 427 tag-only primary; 282
  strong / 10,347 tag-only secondary; 30/521 and 261/1411 tickets involved).
- **Step 3:** Wrote `tests/tools/test_kgmcp_phase5_repeated_demand_measurement.py` with all 6
  tests plan.md's Step 3 specifies (CamelCase false-positive discipline, parity-ID specificity,
  intent classifier on real snapshot data — the `TCK-20260619-E22C-REST-API`/
  `TCK-20260702-OBSISO-TRACE-ASYNC` pair —, tag-alone-never-counts, fixture reproducibility, and
  the self-contamination-exclusion guard), plus the two anti-drift guard tests (import-not-
  reimplement; frozen-snapshot-not-live-file). 9 tests total, all passing.
- **Step 4:** Wrote
  `docs/engine/contracts/knowledge_gateway_mcp/phase5_repeated_demand_measurement.md` stating the
  real numbers, the qualitative "mostly incremental, not literal recurrence" reading, the Phase
  3/4 economics cross-reference, and the literal "not now, not never" recommendation, per plan.md
  Step 4's exact required content.
- **Step 5:** Wrote `tests/docs/test_phase5_repeated_demand_measurement_doc.py` with the two
  tests plan.md's Step 5 specifies. Both are written against real current repo state and both
  currently **fail as expected**: `test_infra_355_parity_entry_matches_committed_measurement_numbers`
  fails because `INFRA-355` does not yet exist (Parity phase's job); the second half of
  `test_phase5_proposal_doc_annotation_does_not_overclaim_done` (the narrative-paragraph-present
  assertion) fails because the proposal doc's Phase 5 section has not yet been annotated
  (Document-Update's job) — the first half (no bullet marked `**Done**`) passes today since
  nothing was ever marked Done. This is disclosed explicitly in the test file's own module
  docstring rather than weakened to force a pass; both are expected to start passing once the
  respective later phases land their artifacts in this same ticket's pipeline.
- **Steps 6-7 skipped, by explicit instruction:** `docs/plans/knowledge-gateway-mcp-proposal.md`
  and `docs/parity_ledger/infrastructure.yaml` were read only, never modified, during this
  Implement pass.

Zero gateway/cache/router source files touched (`tools/knowledge_gateway_cache.py`,
`tools/knowledge_gateway_router.py`, `tools/knowledge_gateway_packet_assembly.py` — confirmed by
`git status --porcelain`, none appear in the diff).

## Test Summary
- `tests/tools/test_kgmcp_phase5_repeated_demand_measurement.py` — 10/10 passing (9 from Implement
  + 1 added by Test phase: `test_qualitative_reading_examples_are_real_committed_pairs`, which
  grounds the results doc's "Qualitative reading" section's two named pair citations
  (ResourceNodeUpdate incremental-investigation pair; COMMUNITY-SKILL-SWAP same-day-recurrence
  pair) against the actual committed primary-pairs fixture — previously prose-only, mirroring the
  gap class closed on the Phase 4 Direct-Tool-Comparison ticket).
- `tests/docs/test_phase5_repeated_demand_measurement_doc.py` — 0/2 passing (both fail by design,
  pending Document-Update/Parity phases — see Implementation Notes; not a regression, both
  document why in their own assertion messages).
- Regression Surface (`tests/tools/test_kgmcp_measurement_baseline.py`,
  `test_kgmcp_phase1_baseline_comparison.py`, `test_kgmcp_phase2_baseline_recomparison.py`,
  `test_kgmcp_phase3_pilot_acceptance_measurement.py`, `test_kgmcp_phase4_direct_tool_comparison.py`)
  — 103/104 passed at default `--resource-budget`; the 1 apparent failure
  (`test_zero_mutation_of_agent_monitoring_and_manifest_across_full_run`) is a pre-existing,
  unrelated `extra_slow` test that requires `--resource-budget large` (its own docstring says so
  explicitly) — re-run with that flag: 1/1 passed. Not a regression caused by this ticket (this
  ticket touches zero files in these suites' dependency graph).
  `tests/tools/test_registry_query.py tests/tools/test_tag_registry.py` — 38/38 passed.
- Hand-run reproducibility check: `python3 tools/agent-monitoring/kgmcp_phase5_repeated_demand_measurement_runner.py`
  printed 17/521 primary and 372/1411 secondary, matching the committed fixture and
  plan.md's independently-re-verified figures exactly.

## Files Changed
- `tests/tools/fixtures/kgmcp_phase5_events_investigate_snapshot.json` (new)
- `tests/tools/fixtures/kgmcp_phase5_working_log_snapshot.json` (new)
- `tools/agent-monitoring/kgmcp_phase5_repeated_demand_measurement_runner.py` (new)
- `tests/tools/fixtures/kgmcp_phase5_repeated_demand_measurement_results.json` (new)
- `tests/tools/test_kgmcp_phase5_repeated_demand_measurement.py` (new)
- `docs/engine/contracts/knowledge_gateway_mcp/phase5_repeated_demand_measurement.md` (new)
- `tests/docs/test_phase5_repeated_demand_measurement_doc.py` (new)
- `tickets/inprogress/TCK-20260816-KGMCP-P5-REPEATED-DEMAND-MEASUREMENT.md` (this file, updated)

Not touched: `docs/plans/knowledge-gateway-mcp-proposal.md`, `docs/parity_ledger/infrastructure.yaml`
(Steps 6-7, explicitly out of scope for this Implement pass), and every gateway/cache/router source
file under `tools/knowledge_gateway_*.py`.

### Document-Update phase

- `docs/plans/knowledge-gateway-mcp-proposal.md` (modified) — added plan.md Step 6's narrative
  paragraph to §20 Phase 5, after the 3 existing bullets and before the `### Phase 6` header,
  mirroring the exact Phase 3 precedent shape (lines 1354-1364). States the real numbers (17/521
  primary, 372/1411 secondary conservative pairs), the mostly-non-literal qualitative reading, the
  Phase 3/4 economics cross-reference, and the literal "not now, not never" recommendation. None of
  the 3 Phase 5 bullets were marked `**Done**` — nothing was built. Verified by
  `tests/docs/test_phase5_repeated_demand_measurement_doc.py::
  test_phase5_proposal_doc_annotation_does_not_overclaim_done`, which now **passes** (was failing
  pre-Document-Update, as designed). The sibling test,
  `test_infra_355_parity_entry_matches_committed_measurement_numbers`, still correctly fails —
  deferred to Parity phase, not touched here.
- `docs/parity_ledger/infrastructure.yaml`: confirmed correctly deferred to Parity phase (`INFRA-355`
  does not yet exist in the ledger — grepped and confirmed) — investigation.md's "Docs Requiring
  Update" section already correctly flagged this as Parity's job, not Document-Update's; not
  touched here.
- `docs/engine/contracts/knowledge_gateway_mcp/phase5_repeated_demand_measurement.md`: already
  created by Implement (Step 4); read and confirmed accurate against the numbers cited in the new
  proposal-doc paragraph; not modified.
- `staging_artifacts/TCK-20260816-KGMCP-P5-REPEATED-DEMAND-MEASUREMENT/investigation.md`: reviewed;
  its "Docs Requiring Update" section correctly identified all three docs above with correct
  ownership (proposal.md and results doc as this ticket's own to update; parity ledger as Parity
  phase's). No restructuring needed — nothing was incorrectly flagged.

## Completion Summary

Delivered a real, honest measurement of repeated/semantically-equivalent question demand in this
repository's own history — not a shipped Phase 5 capability. Two real, non-corpus data sources were
used: `agent-monitoring/events.jsonl` Investigate-phase summaries (primary, 521 distinct tickets)
and `tickets/working_log.csv` ticket titles/summaries (secondary/corroborating, 1,411 tickets). The
equivalence-detection method mirrors proposal §11.2's conservative multi-signal approach exactly
(normalize → extract stable identifiers [CamelCase symbols, file paths, ticket IDs, parity-ledger
IDs] → classify intent into 6 buckets → require same-intent AND a shared specific identifier, never
raw-string similarity alone, never embedding similarity alone, never a shared subsystem-topic tag
alone). The real, honest result: **17/521 conservative repeated-demand pairs** in the primary
source (15 strong symbol/path-sharing, 2 ticket/parity-ID-only, 427 tag-only pairs explicitly not
counted; 30/521 distinct tickets involved, 5.8%) and **372/1411** in the secondary source (282
strong, 10,347 tag-only not counted; 261/1411 tickets involved, 18.5%) — a small, real signal, and
qualitatively mostly natural incremental/sequential investigation of an evolving codebase rather
than literal same-question recurrence. Cross-referenced against Phase 3's real budget-tolerance
FAIL (2/7) and Phase 4's real 7/7 negative gateway-vs-direct-tool comparison, the recommendation is
stated plainly and without softening or hardening: **proceed with Phase 5's remaining two bullets
only after Phase 3's own disclosed gaps close — not now, not never.**

Architecture Review caught and required a fix for a real, confirmed-live self-contamination bug
before implementation: this ticket's own mandatory Investigate-phase monitoring write would
otherwise land in the exact `agent-monitoring/events.jsonl` dataset this ticket measures (the live
file held 522 records at Implement time, not 521). The events snapshot fixture was frozen with an
explicit exclusion of this ticket's own `run_id` before writing, and the committed runner reads only
the frozen snapshot — never the live files — making the guard structural, not incidental. This was
independently re-verified fixed on both the Architecture Review pass and the Architecture-Verify
pass. Zero `tools/knowledge_gateway_*.py` gateway/cache/router source files were touched at any
phase of this ticket, confirmed via `git status --porcelain` at Implement, Architecture-Verify, and
again at Parity.

**Test phase closed one more real gap:** a previously prose-only qualitative claim in the results
doc (the `ResourceNodeUpdate` incremental-investigation pair and the `COMMUNITY-SKILL-SWAP`
same-day-recurrence counter-example) is now pinned against the committed primary-pairs fixture by
`test_qualitative_reading_examples_are_real_committed_pairs`, mirroring the gap class closed on the
Phase 4 Direct-Tool-Comparison ticket. All 10 tests in
`tests/tools/test_kgmcp_phase5_repeated_demand_measurement.py` pass.

**Parity phase complete:** confirmed `INFRA-354` was still the last id
(`grep -o "INFRA-[0-9]*" docs/parity_ledger/infrastructure.yaml | sort -t- -k2 -n | tail` showed
351/352/353/354 as the trailing ids) before appending `INFRA-355`
(`status: verified`, `priority: P2`, `proof_type: regression`) via the schema-validating
`write_entry()`, followed by a separate, visible `python3 tools/parity_index.py build`. The entry
mirrors `INFRA-344`/`INFRA-353`'s "methodology, not conclusion" precedent exactly: it certifies the
real, non-corpus data source, the real conservative multi-signal method, the reproducibility of the
committed runner against the frozen snapshots, and the fixed-and-reverified self-contamination
guard — it explicitly does NOT certify that Phase 5 is warranted or that the recommendation itself
is correct, that being a separate, later, human-reviewer call. `v2_evidence` cites the real runner
(with real line numbers for `_build_records()`/`_compare_records()`/`extract_identifiers()`/
`classify_intent()`), the committed results fixture, both frozen snapshot fixtures, and the results
doc; `test_path` cites both new test files, both fully green (12/12 combined, including
`test_infra_355_parity_entry_matches_committed_measurement_numbers`, which previously failed by
design pending this entry and now passes). Citation-drift check: this ticket touched no
`tools/knowledge_gateway_*.py` file at any phase (confirmed by `git status --porcelain` against
every such file, all clean), so no drift is possible on any prior gateway-code-citing parity entry.

All 5 acceptance criteria are now met.

**Epic consequence, stated plainly:** this is the FINAL and ONLY child ticket of
`TCK-20260816-KNOWLEDGE-GATEWAY-MCP-PHASE5-EPIC`. That epic's own text already explicitly
anticipates and accepts exactly this outcome as complete and valid — its AC8 states: "if it finds
insufficient demand, the epic closes honestly on that single finding without needing to build
anything further, and this is treated as full success, not an incomplete epic," and its own
Scope/AC5 language anticipates the bullets remaining "honestly unmarked with the real finding
recorded" when demand is insufficient. This ticket's real finding — a small, real, mostly-non-literal
signal, explicitly insufficient to justify Phase 5's investment right now, conditioned on Phase 3's
own still-open gaps — falls squarely within that anticipated outcome. Per this real recommendation,
the epic's remaining 2 candidate child tickets (canonical entity IDs/alias consolidation; conservative
semantic candidate matching) will **not** be created now. No Phase 5 proposal bullet was marked
`**Done**` — nothing was built, and none of Phase 5's mechanisms were implemented anywhere in this
ticket's diff.
