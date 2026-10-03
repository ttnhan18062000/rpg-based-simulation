---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260731-PARITY-READPATH-GATE
artifact_type: test_plan
tags: [ai, agent-monitoring, observability, process-improvement, testing, workflows]
---

# Test Plan — TCK-20260731-PARITY-READPATH-GATE

## Regression Surface

This ticket touches no `src/` code and, per its own Out of Scope, must not modify
`tools/parity_index.py`, `tools/parity_ledger_scan.py`, `tools/gate_checks/parity_updater_static.py`,
any `docs/parity_ledger/*.yaml` file, `tools/context_packet_assembler.py`, or
`.claude/workflows/implement-ticket.js`. The regression surface is therefore "prove these stayed
exactly as they were," not "these still pass after a code change."

**Unit (must stay green, unmodified, confirmed passing before this ticket's review runs):**
- `tests/tools/test_parity_index.py` — Phase 1 + Phase 2's full suite, including
  `TestEquivalenceFixtures` (4 tests) and `TestAllShardsCoverage`. Zero edits authorized.
- `tests/tools/test_parity_ledger_scan.py` — 3 tests. Read-only comparison target; zero edits.
- `tests/tools/test_parity_updater_static.py` — 10 tests. Read-only comparison target; zero edits.
- `tests/tools/test_parity_index_baseline.py` — Phase 0 suite. Zero edits.
- `tests/tools/test_context_packet_assembler.py` — named Related Code Area, "protected regression
  boundary" — must remain green and untouched; this ticket must not add fixture-adapter code that
  changes its behavior.

**Known pre-existing failure, not part of this ticket's regression surface:**
`tests/tools/test_build_index.py::TestMakeTarget::test_makefile_dry_run_agent_monitoring_index`
(Makefile phony-target quirk, documented by Phase 0/1/2 investigations, unrelated here).

**Frontmatter / ticket-field validation (must stay green):**
`python3 tools/validate_frontmatter.py` against this ticket's staging artifacts;
`python3 tools/ticket_field_values.py tickets/inprogress/TCK-20260731-PARITY-READPATH-GATE.md`.

**No integration or arena-combat tests apply** — this is a process/decision-gate review over
agent-infrastructure tooling; no `docs/mechanics/` or `docs/engine/` contract governs it, and
`docs/engine/contracts/context_packet_contract.md` is boundary-only (documents an unimplemented
future schema, per investigation.md's Mechanics/Engine Constraints).

## New Tests Required

This ticket's core deliverable is a versioned rubric/corpus and a decision document, not new
production code — its own Out of Scope forbids implementing or changing `tools/parity_index.py`,
the legacy tools, or any workflow/config surface. Accordingly, "new tests" here are **verification
guards over the review's own integrity**, mapped to the ticket's Acceptance Criteria, not new
unit tests of application logic. Whether these are persisted as `pytest` tests or as a documented,
re-runnable verification transcript inside the decision doc is a Plan decision
(investigation.md Risk #1) — both options are listed below; Plan must pick one and state why.

**AC #1 — Corpus and rubric are reviewable before results are generated; every case has
reproducible source references/hashes and expected-set/adjudication fields.**

1. `test_gate_a_corpus_cases_have_pinned_source_and_expected_set`
   Category: unit / corpus-schema guard
   Verifies: every case in the versioned corpus file records (a) a git commit SHA and/or
   `canonical_fragment_hash` pinning its source ledger entry, (b) an explicit expected
   obligation-ID/shard set, and (c) a field distinguishing asserted ground truth from evaluator
   judgement — per investigation.md Risk #2's pinning requirement.
   Where: `tests/tools/` (new file, e.g. `test_gate_a_readpath_corpus.py`) if the corpus is a
   loadable YAML/JSON fixture; otherwise a manual review checklist item in the decision doc if the
   corpus is prose-only. Plan decides the corpus's file format first.

**AC #2 — Legacy and index results are captured for all cases; every mismatch is adjudicated
rather than silently averaged away.**

2. `test_gate_a_every_case_has_legacy_and_index_result_and_adjudication_when_they_differ`
   Category: unit / anti-drift guard
   Verifies: for each corpus case, both a legacy-selection result and an index-selection result are
   present, and any case where they differ carries a non-empty adjudication field — no case is
   allowed to report only an aggregate/averaged pass rate.
   Where: same file as test 1, or a decision-doc review checklist item.

**AC #3 — The decision reports recall, false positives, selection size/context estimate, and
analyst effort; records zero unexplained obligation false negatives against the adjudicated set.**

3. `test_gate_a_decision_reports_all_four_named_metrics`
   Category: unit / completeness guard
   Verifies: the decision document contains an explicit value (or an explicitly flagged
   "not defensible a priori" note, per `TCK-20260730-SHADOW-PROMOTION-GATE-THRESHOLDS`'s precedent)
   for each of: recall, false positives, selection size/context-byte-or-token estimate, and analyst
   effort — no silent omission of any of the four.
   Where: same file, or a manual checklist.

4. `test_gate_a_zero_unexplained_false_negatives_against_adjudicated_set`
   Category: unit / anti-drift guard
   Verifies: no corpus case's adjudicated expected-obligation set contains an ID that `impact`'s
   result set misses without an explicit, recorded explanation in that case's adjudication field.
   Where: same file, or a manual checklist.

**AC #4 — A GO additionally demonstrates faction/all-shard coverage, fewer false positives, or
smaller selection size without recall regression. NO-GO/INCONCLUSIVE leaves legacy behavior live
and files/backlogs only a bounded follow-up if warranted.**

5. `test_gate_a_go_decision_cites_at_least_one_named_advantage_without_recall_regression`
   Category: unit / decision-integrity guard
   Verifies: if and only if the decision is GO, the document names at least one of
   faction/all-shard coverage, fewer false positives, or smaller selection size as evidence, and
   explicitly states no recall regression was observed. A NO-GO/INCONCLUSIVE decision is exempt
   from this check but must state that legacy behavior remains live.
   Where: same file, or a manual checklist.

6. `test_gate_a_go_next_action_only_authorizes_scoping_not_implementation`
   Category: unit / anti-drift guard (this is the ticket's own explicit constraint, restated as a
   test)
   Verifies: a GO decision's "next action" field names a future ticket-scoping step, never a direct
   code/config/workflow change to make immediately.
   Where: same file, or a manual checklist.

**AC #5 — No production consumer, telemetry event, guidance/config/workflow change, or source
YAML write occurs.**

7. `test_gate_a_review_leaves_protected_files_byte_identical`
   Category: architecture guard (durable, recommended as a persisted pytest test regardless of how
   Plan resolves tests 1-6, since this is the one check with genuine regression value across time)
   Verifies: `git hash-object`/`sha256` of `tools/parity_index.py`, `tools/parity_ledger_scan.py`,
   `tools/gate_checks/parity_updater_static.py`, every `docs/parity_ledger/*.yaml` file,
   `tools/context_packet_assembler.py`, and `.claude/workflows/implement-ticket.js`, captured before
   and after this ticket's review work, are identical.
   Where: `tests/tools/test_gate_a_readpath_review.py` (new) — this one is recommended as an actual
   pytest test rather than a checklist item, since "no mutation occurred" is exactly the kind of
   read-only-logic claim CLAUDE.md's Architecture Rule requires a test for.

## Scoped Pytest Commands

```
pytest tests/tools/test_parity_index.py tests/tools/test_parity_index_baseline.py \
       tests/tools/test_parity_ledger_scan.py tests/tools/test_parity_updater_static.py -v
```
Regression confirmation — this ticket's own review must not have altered any of these four files'
behavior. Confirmed passing (44/44 + 13 + Phase-0 suite) before this ticket's review began.

```
pytest tests/tools/test_context_packet_assembler.py -v
```
Confirms the protected boundary named in Related Code Areas is untouched.

```
pytest tests/tools/test_gate_a_readpath_review.py -v
```
If Plan adopts test 7 (recommended) as a persisted test — the review's own "no mutation occurred"
guard.

```
python3 tools/validate_frontmatter.py staging_artifacts/TCK-20260731-PARITY-READPATH-GATE/investigation.md staging_artifacts/TCK-20260731-PARITY-READPATH-GATE/test_plan.md staging_artifacts/TCK-20260731-PARITY-READPATH-GATE/plan.md
```

**Never:** `pytest tests/` (repo-wide) — this ticket's regression surface is `tests/tools/` only.

**Do NOT include** `tests/tools/test_build_index.py` — pre-existing, unrelated Makefile failure,
documented by Phase 0/1/2 investigations.

## Anti-Drift Test Guards

- **`test_gate_a_review_leaves_protected_files_byte_identical`** — the single most load-bearing
  guard in this plan. It is the durable, mechanical proof behind the ticket's own AC #5 ("No
  production consumer, telemetry event, guidance/config/workflow change, or source YAML write
  occurs"), and it is the one check that remains meaningful after the review itself is historical.
- **`test_gate_a_zero_unexplained_false_negatives_against_adjudicated_set`** — guards against a
  well-intentioned but wrong practice of reporting an aggregate recall percentage that hides one
  case's real, unexplained miss — directly enforcing AC #3's "zero unexplained... rather than
  silently averaged away" language.
- **`test_gate_a_go_next_action_only_authorizes_scoping_not_implementation`** — guards against the
  single most likely scope-creep failure mode for this ticket: a GO decision that reads as (or is
  later treated as) implicit permission to wire `impact`/`entry`/`health` into a real workflow phase.
- A guard (manual or automated) confirming Phase 2's synthetic `TestEquivalenceFixtures` cases are
  **not** relabeled or cited as this ticket's "immutable, ticket-derived cases" — they must remain
  attributed to their own ticket as separate, valid-but-distinct evidence, per investigation.md's
  Anti-Drift Hazards.
- A guard confirming every real corpus case (e.g. `FAC-012`, `INFRA-296`/`297`/`299`/`300`) records
  a git commit SHA or `canonical_fragment_hash` pin at capture time — protects the decision's
  reproducibility claim against a future, unrelated ticket editing the same ledger entries.
