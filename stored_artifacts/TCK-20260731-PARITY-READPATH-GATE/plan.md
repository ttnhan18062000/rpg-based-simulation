---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260731-PARITY-READPATH-GATE
artifact_type: plan
tags: [ai, agent-monitoring, observability, process-improvement, testing, workflows]
---

# Implementation Plan — TCK-20260731-PARITY-READPATH-GATE

## Summary

This ticket produces one reviewable decision, no production code. The plan builds a two-file,
git-pinned corpus (`gate_a_corpus.json` frozen first, `gate_a_results.json` filled in only after
the corpus is reviewable), exercises `tools/parity_index.py`'s unmodified `entry()`/`impact()`/
`health()` against it alongside the two legacy comparison surfaces
(`tools/parity_ledger_scan.py::find_p0_intersection`,
`tools/gate_checks/parity_updater_static.py::derive_mapping`/`cross_reference_touched`), adjudicates
every discrepancy explicitly (never averaged away), computes the four AC #3 metrics per case, and
closes with a GO/NO-GO/INCONCLUSIVE decision document at `docs/ai/parity_readpath_gate_a_decision.md`
mirroring `docs/ai/shadow_promotion_gate_thresholds_decision.md`'s falsifiable, gap-honest shape. The
harness that produces and re-verifies all of this is a single new, persisted pytest file,
`tests/tools/test_gate_a_readpath_review.py` — not a throwaway script and not a prose-only transcript
(Decision 1 below) — which re-extracts each real case's pinned git blob content at test time, rebuilds
a temporary index via the untouched `parity_index.build()`, and asserts corpus integrity, result
capture, adjudication completeness, and byte-identical protected-file state, all in one place. No file
named in the ticket's Out of Scope or this ticket's Related Code Areas as a protected boundary is
edited by any step.

## Decisions (resolving investigation.md's open questions 1-4)

**Decision 1 — harness location and form.** A persisted pytest file,
`tests/tools/test_gate_a_readpath_review.py`, is both the execution harness and the reproducibility
proof — not a throwaway script under `staging_artifacts/` and not a documented command transcript
prose-only inside the decision doc. Rationale: `test_plan.md` already independently proposed this
exact file as the natural location for the AC-mapped guard tests (items 1-7); a real pytest file is
mechanically re-runnable (`pytest tests/tools/test_gate_a_readpath_review.py -v`) in a way a prose
transcript is not, and it lives in `tests/tools/` — a normal, unprotected location for new tests, not
`tools/` itself, so it does not touch any file this ticket's Out of Scope forbids. The decision doc
still contains a short "how to reproduce" section naming this one pytest command, but the command
*is* the harness; the doc does not re-embed a separate copy of the procedure.

**Decision 2 — corpus pinning mechanism.** Every real (non-synthetic) corpus case records: (a) the
git commit SHA that added/last-touched the entry, (b) the shard filename, (c) the entry's
`canonical_fragment_hash` computed with the exact same formula `parity_index.py:231-233` uses
(`hashlib.sha256(json.dumps(entry, sort_keys=True, ensure_ascii=True).encode("utf-8")).hexdigest()`)
applied to the entry dict as it existed in that commit — replicated independently in the harness
test, never imported from `parity_index.py` as a function call (it has no such importable helper;
the formula is copied as a literal, commented as "must stay byte-identical to
`_populate_entries`'s fragment_hash formula"). At harness run time, the test re-extracts the pinned
entry via `git show <sha>:docs/parity_ledger/<shard>.yaml`, re-computes the hash, and asserts it
still matches the recorded pin — if a future ticket edits that same entry in place at the same
commit-reachable history (impossible for a merged commit, but guards a corpus-authoring transcription
error) or if the corpus file itself was hand-edited incorrectly, this fails loudly instead of silently
drifting. Synthetic legacy-edge cases (Decision below, Step 2) have no git SHA — they pin instead to a
literal fixture dict embedded directly in `gate_a_corpus.json`, hashed the same way, so they are
reproducible without git history at all.

**Decision 3 — analyst-effort proxy.** No existing tool measures human analyst time-on-task (same gap
`TCK-20260730-SHADOW-PROMOTION-GATE-THRESHOLDS` §4 found for causal attribution). Rather than
fabricate a time figure, this plan defines and consistently applies a simple, mechanically-derived
proxy with two named sub-components, computed identically for every case and reported as an explicit
proxy — never presented as measured wall-clock time:
- `shards_scanned`: for both legacy functions this is always `8` (fixed — `find_p0_intersection` and
  `cross_reference_touched`/`derive_mapping` both linearly scan the full `CANONICAL_LEDGER_FILES` list
  regardless of match, per investigation.md's confirmed reading of both modules); for the index path
  this is always `0` (an exact-match indexed `WHERE path = ?` lookup touches no whole file). This
  captures the real, structural difference in how much an analyst would need to open just to run the
  query, independent of how many results come back.
- `candidates_to_review`: the returned result-set size for each surface on that case (an analyst must
  still read every returned candidate regardless of which tool produced it).
Both sub-components are reported per case in `gate_a_results.json` and summarized in the decision doc,
labeled explicitly as "a structural proxy for analyst burden, not a measured time-on-task figure" —
mirroring the SHADOW-PROMOTION-GATE-THRESHOLDS precedent's own honest-gap framing.

**Decision 4 — P0 corpus coverage (resolves investigation.md Open Question 4 / this plan's former
"Unresolved Questions" section).** The user was asked and chose option 1 from the two paths this
plan's prior revision left open: time-box a mine for a real P0 case before falling back to
documenting the gap. The bounded search succeeded on the first candidate checked — no fallback
was needed and no further shards were mined. Confirmed directly via `git show 46c5ae59 --
docs/parity_ledger/world_dynamics.yaml`:

- **`WORLD-076`** (`docs/parity_ledger/world_dynamics.yaml`, commit `46c5ae598f0f05d7f4f162a742ae60575c26b781`
  / `46c5ae59`, `TCK-20260716-PLACELEGAL-HARDLAW`) is `priority: P0`. Its `v2_evidence` genuinely cites
  `src/observability/hard_law_monitor.py` (`HardLawMonitor.check_initial_placement()`,
  `LAW-SPAWN-OCCUPANCY`) and `src/engine/kernel.py` (`Kernel._run_initial_placement_check()`) — both
  files are confirmed touched by the same commit (`git show 46c5ae59 --stat`). This is the corpus's
  one real, non-synthetic P0 case; it is added to Step 1's `real_cases` array below.
- One nuance carried forward explicitly, not smoothed over: `WORLD-076`'s `status` is `divergent`
  (flipped from `verified` by this same commit), not `verified` like the other five real cases.
  This does not disqualify it as a Gate A corpus case — Gate A tests *read-path retrieval*
  (whether `impact()`/the legacy scanners surface the right entry ID for a given changed path), not
  whether the entry's own parity claim currently holds. A `divergent`-status P0 entry is still a
  real, git-pinned obligation a read path must be able to surface, and using it means the corpus's
  one P0 case also happens to exercise the `status` field honestly rather than cherry-picking only
  `verified` entries. Step 10's decision-doc limitations section must state this distinction
  explicitly (updated below) so the recall claim is never misread as also certifying `WORLD-076`'s
  own parity correctness.
- The same commit's `WORLD-112` (`P1`, `status: verified`) also genuinely cites
  `src/observability/hard_law_monitor.py` in its own `v2_evidence`; `WORLD-113` (`P2`) cites
  `src/engine/kernel.py` but not `src/observability/hard_law_monitor.py`. This is reflected in
  `WORLD-076`'s case's `expected_obligation_ids` in Step 1 below (ground truth taken directly from
  the commit diff, not invented).

No further shard mining beyond this one candidate check was performed or is authorized — the
time-box was honored, the P0 gap is now closed with real data, and expanding further would be
scope creep against this plan's own git-mining-is-a-Step-1-input framing.

## Steps

### Step 1 — Git-mine and pin the real ticket-derived corpus cases
**Files:** `staging_artifacts/TCK-20260731-PARITY-READPATH-GATE/gate_a_corpus.json` (new)
**Change:** Create the corpus file's `real_cases` array using investigation.md's Prior Work findings
verbatim — do not re-derive from scratch:
- `FAC-012` (`docs/parity_ledger/faction.yaml`, commit `68f168ff`, `TCK-20260702-SIMQ-UPLIFT2-FACTION`,
  priority `P1`). This is the ticket's required "faction source-path case."
- `INFRA-296`, `INFRA-297`, `INFRA-299` (priority `P1` each, confirmed by `git show ab06fc10`), and
  `INFRA-300` (priority `P2`, confirmed by the same commit) — `docs/parity_ledger/infrastructure.yaml`,
  commit `ab06fc10`, `TCK-20260729-SHADOW-PACKET-CALL-SITE`/`TCK-20260729-SHADOW-BASELINE-COMPARISON`.
- `WORLD-076` (`docs/parity_ledger/world_dynamics.yaml`, commit `46c5ae598f0f05d7f4f162a742ae60575c26b781`
  / `46c5ae59`, `TCK-20260716-PLACELEGAL-HARDLAW`, priority `P0`, `status: divergent`) — the corpus's
  one real P0 case, per Decision 4. `changed_path_query: "src/observability/hard_law_monitor.py"`.
  `expected_obligation_ids: ["WORLD-076", "WORLD-112"]` — both entries' `v2_evidence` genuinely cite
  this exact path in this exact commit (confirmed via `git show 46c5ae59 --
  docs/parity_ledger/world_dynamics.yaml`); `WORLD-113` (same commit) cites `src/engine/kernel.py`
  but not `src/observability/hard_law_monitor.py` and is correctly excluded from this case's expected
  set. Record `WORLD-076`'s `status: divergent` verbatim in the case (do not normalize it to
  `verified`) — Decision 4 explains why this is not disqualifying.
Each case record has: `case_id`, `source_type: "real_ticket_derived"`, `ledger_shard_file`,
`entry_id`, `source_ticket_id`, `commit_sha`, `canonical_fragment_hash` (computed per Decision 2),
`changed_path_query` (the real `src/`/`tools/` path from that entry's `v2_evidence` to feed into
`impact(changed_path=...)` and the two legacy functions), `expected_obligation_ids` (asserted ground
truth — the entry ID(s) whose real `v2_evidence` genuinely cites `changed_path_query`, taken directly
from the commit diff, not invented), `expected_shard`, and
`ground_truth_or_judgement: "ground_truth"` (every field in this real-case group is asserted from the
actual ticket/commit record, not an evaluator's own judgement call).
**Do NOT touch:** any `docs/parity_ledger/*.yaml` file (read via `git show`, never edited in place);
do not add any further real case beyond these six entries (`FAC-012`, `INFRA-296/297/299/300`,
`WORLD-076`) — Decision 4 already resolved the corpus's P0-coverage gap with a time-boxed search
that stopped at the first candidate checked, and further shard mining now would be scope creep
against that closed decision, not a continuation of it.
**Verify:** `test_gate_a_corpus_cases_have_pinned_source_and_expected_set` (test_plan.md item 1),
scoped to the `real_cases` array only at this step.

### Step 2 — Construct labeled synthetic legacy-edge-case fixtures
**Files:** `staging_artifacts/TCK-20260731-PARITY-READPATH-GATE/gate_a_corpus.json` (same file,
`synthetic_edge_cases` array)
**Change:** The ticket's own Scope requires "legacy edge fixtures **plus** immutable, ticket-derived
cases" — both, not either/or (investigation.md Risk #3). Add freshly-authored (not copied verbatim
from `tests/tools/test_parity_index.py::TestEquivalenceFixtures`) fixture cases covering the same
*shapes* of known legacy-vs-index divergence, each with `source_type: "synthetic_legacy_edge"` and
`ground_truth_or_judgement: "evaluator_judgement"` (an evaluator constructed these, not a real ticket):
one P0/P1-pair-same-path case (P0-only-filter shape), one two-shard-same-path case (ANY-of
multi-shard shape), one malformed-shard-alongside-valid-shard case (silent-skip-vs-abort shape). Each
case embeds its own literal fixture entry dict directly in the JSON (no git SHA — pinned by the
embedded literal itself, per Decision 2) plus its own `canonical_fragment_hash` computed the same way.
**Do NOT touch:** `tests/tools/test_parity_index.py::TestEquivalenceFixtures` — read as a shape
reference only, never imported, copied field-for-field, or relabeled as this ticket's corpus (the
single most-cited anti-drift hazard in investigation.md).
**Verify:** `test_gate_a_corpus_cases_have_pinned_source_and_expected_set` (test_plan.md item 1),
extended to also cover the `synthetic_edge_cases` array; a dedicated assertion that no
`synthetic_edge_cases` entry's `case_id` or fixture content string-matches any
`TestEquivalenceFixtures` fixture ID (`COMB-501`, `COMB-502`, `CM-601`, `SC-601`, `TR-701`, `FAC-801`).

### Step 3 — Write the rubric field schema and freeze the corpus file
**Files:** `staging_artifacts/TCK-20260731-PARITY-READPATH-GATE/gate_a_corpus.json` (same file, a
top-level `rubric_schema` object), `staging_artifacts/TCK-20260731-PARITY-READPATH-GATE/gate_a_results.json`
(new, empty skeleton only — one entry per `case_id` from Steps 1-2, all result fields `null`)
**Change:** `rubric_schema` documents, once, the exact field names every result entry must carry (so
the corpus is reviewable before any result is generated, per AC #1): `legacy_find_p0_result`,
`legacy_derive_mapping_result`, `index_impact_result`, `index_entry_result`, `discrepancy_adjudication`
(non-empty string required whenever the two legacy results or a legacy result and the index result
disagree on membership; `null` only when they agree), `selection_size_legacy_find_p0`,
`selection_size_legacy_derive_mapping`, `selection_size_index_impact`, `context_byte_estimate_index`
(`len(json.dumps(index_impact_result))`, explicitly labeled `"is_estimate": true` — never a claimed
production token/byte saving, per Out of Scope), `analyst_effort_proxy` (object with
`shards_scanned_legacy: 8`, `shards_scanned_index: 0`, `candidates_to_review_legacy`,
`candidates_to_review_index`, per Decision 3). `gate_a_results.json`'s skeleton is committed with every
field present and `null` so a diff against the filled-in version (Steps 5-8) is reviewable.
**Do NOT touch:** the `real_cases`/`synthetic_edge_cases` arrays written in Steps 1-2 — this step only
adds the schema and the empty results skeleton, it does not alter any case record.
**Verify:** `test_gate_a_corpus_cases_have_pinned_source_and_expected_set` (full pass, all cases +
schema); `python3 -m json.tool` validity check on both files (part of the same test file's setup).

### Step 4 — Harness: pinned-source re-verification and index build
**Files:** `tests/tools/test_gate_a_readpath_review.py` (new)
**Change:** Add `TestCorpusIntegrity` with `test_gate_a_corpus_cases_have_pinned_source_and_expected_set`
(the full version, superseding the partial checks from Steps 1-3): for every `real_cases` entry, run
`git show <commit_sha>:docs/parity_ledger/<shard>` (via `subprocess.run`, `cwd=repo root`), parse the
`entry_id` out of the YAML, recompute the fragment hash per Decision 2's literal formula, and assert
it equals the recorded `canonical_fragment_hash`; for `synthetic_edge_cases`, recompute the hash
against the embedded literal dict and assert the same. Add a shared fixture
`_build_temp_index_for_case(case, tmp_path)` that writes the case's shard YAML (extracted or literal)
into a `tmp_path` ledger dir and calls the real, unmodified `parity_index.build(ledger_dir=tmp_path,
db_path=tmp_path / "parity.db")` (imported directly, matching Phase 2's own test idiom) — this is the
only place `build()` is invoked, reused across Steps 5-6, never reimplemented.
**Do NOT touch:** `parity_index.build`, `_populate_entries`, `_load_shards`, or any other importer
internal — call only, never modify.
**Verify:** `test_gate_a_corpus_cases_have_pinned_source_and_expected_set` green for all cases.

### Step 5 — Run the two legacy functions against every case
**Files:** `tests/tools/test_gate_a_readpath_review.py` (same file, `TestLegacyCapture` class),
`staging_artifacts/TCK-20260731-PARITY-READPATH-GATE/gate_a_results.json` (filled in)
**Change:** For each case, call `find_p0_intersection(files_changed=[case["changed_path_query"]],
ledger_dir=<the case's tmp fixture dir from Step 4>)` (imported from `tools.parity_ledger_scan`) and
`cross_reference_touched`/`derive_mapping` (imported from `tools.gate_checks.parity_updater_static`,
same fixture dir). Record each raw result plus `selection_size_legacy_find_p0` /
`selection_size_legacy_derive_mapping` into `gate_a_results.json` under that `case_id`. The test
asserts the results file's legacy fields are all non-null after this step and match what a fresh
re-run produces (determinism check, mirroring Phase 2's own `TestDeterminism` idiom).
**Do NOT touch:** `find_p0_intersection`, `cross_reference_touched`, `derive_mapping`, or
`CANONICAL_LEDGER_FILES` — call only.
**Verify:** New assertion within `test_gate_a_every_case_has_legacy_and_index_result_and_adjudication_when_they_differ`
(test_plan.md item 2), legacy half only at this step.

### Step 6 — Run `entry()`/`impact()`/`health()` against every case
**Files:** `tests/tools/test_gate_a_readpath_review.py` (same file, `TestIndexCapture` class),
`gate_a_results.json` (filled in further)
**Change:** For each case, call `impact(changed_path=case["changed_path_query"], db_path=<Step 4's
temp db>)` and `entry(case["entry_id"], db_path=...)` (both imported directly from
`tools.parity_index`); record `index_impact_result`, `index_entry_result`, and
`selection_size_index_impact` into `gate_a_results.json`. Additionally, once per distinct subsystem
represented in the corpus (`faction`, `infrastructure`), call `health(subsystem=<name>, db_path=...)`
and record its output under a `health_snapshots` object in `gate_a_results.json` — `health()` has no
legacy equivalent to diff against (it is an aggregate observability query, not a per-case obligation
selector), so its output is recorded as supporting corpus evidence only, never folded into the
recall/false-positive arithmetic in Step 8.
**Do NOT touch:** `entry`, `impact`, `health`, `_connect_readonly`, or any SQL inside
`tools/parity_index.py` — call only, per the ticket's own Out of Scope.
**Verify:** Remainder of `test_gate_a_every_case_has_legacy_and_index_result_and_adjudication_when_they_differ`
(index half); `test_gate_a_zero_unexplained_false_negatives_against_adjudicated_set` depends on this
step's `index_impact_result` values being populated.

### Step 7 — Adjudicate every discrepancy explicitly
**Files:** `gate_a_results.json` (filled in), `tests/tools/test_gate_a_readpath_review.py` (same file,
`TestAdjudication` class)
**Change:** For every case where `index_impact_result`'s entry-ID set differs from either legacy
result's entry-ID set (in either direction), write a non-empty, human-readable
`discrepancy_adjudication` string into that case's result record explaining the difference by
citing the specific known legacy behavior it stems from (all-priority vs. P0-only, ANY-of-multi-shard,
faction-exclusion, malformed-shard silent-skip) — never leaving a diff unexplained, and never
collapsing multiple cases' discrepancies into one aggregate note. Cases where all three surfaces agree
get `discrepancy_adjudication: null`, recorded explicitly (not omitted). Add
`test_gate_a_every_case_has_legacy_and_index_result_and_adjudication_when_they_differ`'s full
assertion: every result record has non-null legacy and index result fields, and every record whose
result sets differ has a non-empty `discrepancy_adjudication`.
**Do NOT touch:** any of the underlying functions being compared — adjudication is a written
explanation of an observed, real difference, never a code change to reconcile it (the ticket's Out
of Scope's single most explicit prohibition).
**Verify:** `test_gate_a_every_case_has_legacy_and_index_result_and_adjudication_when_they_differ`
(test_plan.md item 2, full); `test_gate_a_zero_unexplained_false_negatives_against_adjudicated_set`
(test_plan.md item 4) — for every case, every ID in `expected_obligation_ids` that is absent from
`index_impact_result` must have an explicit adjudication entry explaining why (e.g., "not expected to
appear — see divergence note"), or the test fails as an unexplained false negative.

### Step 8 — Compute recall, false positives, selection size, and analyst effort
**Files:** `gate_a_results.json` (filled in, top-level `aggregate_metrics` object),
`tests/tools/test_gate_a_readpath_review.py` (same file, `TestMetrics` class)
**Change:** Per case and in aggregate across `real_cases` only (synthetic edge cases inform
adjudication shape, not the headline recall/FP numbers, since they were constructed to exercise a
known divergence rather than represent a real obligation set): `recall = |expected_obligation_ids ∩
index_impact_result_ids| / |expected_obligation_ids|`; `false_positives = index_impact_result_ids -
expected_obligation_ids` minus any ID whose presence is explained by Step 7's adjudication as an
intentional broadening (all-priority/ANY-of-shard) rather than a genuine error — each surviving
unexplained false positive is itself a distinct adjudication-required item. `selection_size` and
`context_byte_estimate_index` are read directly from Step 6/3's recorded per-case fields and summed/
averaged for the aggregate. `analyst_effort_proxy` aggregate reports total `shards_scanned` and total
`candidates_to_review` summed across all real cases for each surface, per Decision 3.
**Do NOT touch:** nothing outside `gate_a_results.json` and the new test file.
**Verify:** `test_gate_a_decision_reports_all_four_named_metrics` (test_plan.md item 3) — asserts
`aggregate_metrics` has non-null `recall`, `false_positives`, `selection_size` (or context estimate),
and `analyst_effort_proxy` values, or an explicit `"not_defensible_a_priori"` flag string in place of
a value, never a silent omission.

### Step 9 — Protected-file byte-identical regression guard
**Files:** `tests/tools/test_gate_a_readpath_review.py` (same file, `TestNoMutation` class)
**Change:** Add `test_gate_a_review_leaves_protected_files_byte_identical`: before any of Steps 4-8
run (module-level `setup_module` or a session fixture), capture `git hash-object` (or `sha256`) for
`tools/parity_index.py`, `tools/parity_ledger_scan.py`, `tools/gate_checks/parity_updater_static.py`,
every `docs/parity_ledger/*.yaml` file, `tools/context_packet_assembler.py`, and
`.claude/workflows/implement-ticket.js`; re-hash the same files at the end of the test module's run
and assert every hash is unchanged. This is the durable, mechanical proof of AC #5 and remains
meaningful after this ticket is historical.
**Do NOT touch:** any of the files being hashed — this step only reads and compares hashes.
**Verify:** `test_gate_a_review_leaves_protected_files_byte_identical` (test_plan.md item 7,
independently the plan's single most load-bearing test per test_plan.md's own Anti-Drift Test Guards).

### Step 10 — Write the GO/NO-GO/INCONCLUSIVE decision document
**Files:** `docs/ai/parity_readpath_gate_a_decision.md` (new)
**Change:** Mirror `docs/ai/shadow_promotion_gate_thresholds_decision.md`'s shape: (1) restate the
idea doc's Gate A bullet verbatim as the evidentiary bar; (2) a per-case table citing
`gate_a_corpus.json`/`gate_a_results.json` by path (not re-embedding the JSON) — case ID, source type,
pin (commit SHA or "synthetic/embedded"), recall, false positives, adjudication summary; (3) the
aggregate metrics from Step 8, each reported or explicitly flagged not-defensible; (4) the verdict
itself — GO only if at least one of {faction/all-shard coverage (already structurally true per
`FAC-012`), fewer false positives, smaller selection size} holds with zero recall regression across
the real cases; NO-GO/INCONCLUSIVE otherwise, explicitly stating legacy behavior remains live; (5) a
"next action" field that, if GO, names a future ticket-scoping step only (e.g., "scope a Phase-3
ticket to wire `impact` behind a workflow gate") — never a config/workflow change to make now; (6) an
explicit limitations section stating that the real corpus's one P0 case (`WORLD-076`, per Decision 4)
carries a `divergent` parity status rather than `verified` — the case proves read-path *retrieval* of
a real, git-pinned P0 obligation, not that `WORLD-076`'s own underlying `src/` behavior is currently
parity-clean; state this distinction explicitly so the recall claim is never misread as also
certifying `WORLD-076`'s own parity correctness; (7) a "how to reproduce" section naming exactly
`pytest tests/tools/test_gate_a_readpath_review.py -v` (Decision 1) and nothing else.
**Do NOT touch:** `docs/ai/shadow_promotion_gate_thresholds_decision.md` itself — read as a shape
reference only, never edited.
**Verify:** `test_gate_a_go_decision_cites_at_least_one_named_advantage_without_recall_regression`
(test_plan.md item 5), `test_gate_a_go_next_action_only_authorizes_scoping_not_implementation`
(test_plan.md item 6) — both implemented as a lightweight text-scan test in
`tests/tools/test_gate_a_readpath_review.py`'s `TestDecisionDocIntegrity` class, parsing the committed
Markdown for the required verdict/next-action shape rather than re-deriving the verdict.

### Step 11 — Full regression and validation run
**Files:** none (verification only)
**Change:** Run, in order: `pytest tests/tools/test_parity_index.py tests/tools/test_parity_index_baseline.py
tests/tools/test_parity_ledger_scan.py tests/tools/test_parity_updater_static.py -v` (confirm
unmodified and still green); `pytest tests/tools/test_context_packet_assembler.py -v` (protected
boundary unchanged); `pytest tests/tools/test_gate_a_readpath_review.py -v` (this ticket's own new
suite, all classes from Steps 4-10); `python3 tools/validate_frontmatter.py` against this ticket's
staging artifacts and `docs/ai/parity_readpath_gate_a_decision.md`;
`python3 tools/ticket_field_values.py tickets/inprogress/TCK-20260731-PARITY-READPATH-GATE.md`.
**Do NOT touch:** `tests/tools/test_build_index.py` (excluded, pre-existing unrelated failure);
never run `pytest tests/` repo-wide.
**Verify:** All commands exit 0.

## Scope Guards

- No edit to `tools/parity_index.py`, `tools/parity_ledger_scan.py`,
  `tools/gate_checks/parity_updater_static.py`, `tools/context_packet_assembler.py`, or any
  `.claude/workflows/*.js` file, at any step. Step 9's guard exists specifically to make this
  mechanically checkable, not just declared.
- No edit to any `docs/parity_ledger/*.yaml` file — real corpus content is read via `git show`
  against historical commits, never written to or checked out in place.
- No new `docs/parity_ledger/*.yaml` entry and no `status`/`v2_evidence` change to any existing
  entry — this ticket produces no `src/` behavior change (confirmed by investigation.md's Parity
  Ledger Overlap section).
- No context-packet/retrieval-cache/workflow/gate/config/monitoring mutation of any kind.
- No live token-savings claim — `context_byte_estimate_index` is explicitly labeled
  `"is_estimate": true` in `gate_a_results.json` and referred to only as an estimate in the decision
  doc, never as a measured production saving.
- No implementation of Phase 3+ (no real `ContextRequest`/`ContextPacket` construction, no wiring of
  `impact`/`entry`/`health` into any workflow phase or agent prompt).
- No "fixing" `find_p0_intersection`, `derive_mapping`/`cross_reference_touched`, or
  `impact`/`entry`/`health` in response to a discrepancy found during review — every discrepancy is
  adjudicated in writing (Step 7), never patched away to improve the gate's own outcome.
- No silent substitution of Phase 2's `TestEquivalenceFixtures` synthetic fixtures as this ticket's
  required real corpus — Step 2's synthetic cases are freshly authored and explicitly labeled
  `"synthetic_legacy_edge"`, distinct `case_id`s, never copied verbatim from that test class.
- No averaging of discrepancies into a single pass-rate number that would hide any one case's
  unexplained miss (Step 7's per-case adjudication requirement).

## Dependency Map

- Steps 1 and 2 are independent of each other (real vs. synthetic corpus halves) and both must
  complete before Step 3 (which freezes the combined corpus file and writes the results skeleton).
- Step 3 is a prerequisite for Step 4 (the harness reads the frozen corpus schema).
- Step 4 is a prerequisite for Steps 5 and 6 (both reuse Step 4's `_build_temp_index_for_case`
  fixture and pinned-source re-verification).
- Steps 5 and 6 are mutually independent (legacy vs. index capture) and both must complete before
  Step 7 (adjudication needs both result halves to compare).
- Step 7 is a prerequisite for Step 8 (metrics are computed from adjudicated, not raw, discrepancies).
- Step 8 is a prerequisite for Step 10 (the decision doc cites Step 8's aggregate metrics).
- Step 9 (protected-file hashing) is independent of Steps 5-8's content and can be written any time
  after Step 4, but its assertion window must span the full Steps 4-8 execution to be meaningful —
  place it so its `setup`/`teardown` bracket the whole test module's run.
- Step 10 depends on Steps 1-9 all being complete and green.
- Step 11 depends on all prior steps.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC #1 — Corpus and rubric reviewable before results; reproducible source refs/hashes; expected-set/adjudication fields present | Steps 1, 2, 3, 4 | `test_gate_a_corpus_cases_have_pinned_source_and_expected_set` |
| AC #2 — Legacy and index results captured for all cases; every mismatch adjudicated, never silently averaged | Steps 5, 6, 7 | `test_gate_a_every_case_has_legacy_and_index_result_and_adjudication_when_they_differ` |
| AC #3 — Decision reports recall, false positives, selection size/context estimate, analyst effort; zero unexplained false negatives | Steps 7, 8 | `test_gate_a_decision_reports_all_four_named_metrics`, `test_gate_a_zero_unexplained_false_negatives_against_adjudicated_set` |
| AC #4 — GO demonstrates a named advantage without recall regression; NO-GO/INCONCLUSIVE leaves legacy live | Step 10 | `test_gate_a_go_decision_cites_at_least_one_named_advantage_without_recall_regression`, `test_gate_a_go_next_action_only_authorizes_scoping_not_implementation` |
| AC #5 — No production consumer/telemetry/config/workflow change or source YAML write | Step 9 (all steps constrained by Scope Guards) | `test_gate_a_review_leaves_protected_files_byte_identical` |

## Anti-Drift Notes

- `health()` has no legacy counterpart and must never be folded into the recall/false-positive
  arithmetic (Step 6) — it is recorded as supporting corpus evidence only.
- The `canonical_fragment_hash` formula (Decision 2) must be copied as a literal in the test file,
  commented as needing to stay byte-identical to `_populate_entries`'s formula at
  `tools/parity_index.py:231-233` — there is no importable helper to reuse, and the two must never
  silently diverge.
- `analyst_effort_proxy`'s `shards_scanned_legacy: 8` is fixed by the real, confirmed behavior of both
  legacy functions (full linear scan of `CANONICAL_LEDGER_FILES` regardless of match) — do not
  recompute or vary it per case; it is a structural constant, not a per-case measurement.
- Step 7's adjudication must name the *specific* known legacy behavior (P0-only filter, ANY-of-shard,
  faction exclusion, malformed-shard silent-skip) behind each discrepancy — a generic "expected,
  documented divergence" note without naming which one is not sufficient adjudication.
- `false_positives` (Step 8) is computed against the adjudicated expected set, not the raw narrower
  legacy output — `impact()` is intentionally all-priority and broader by design (Phase 2's own
  `TestEquivalenceFixtures` precedent), so a naive diff against `find_p0_intersection` alone would
  manufacture false positives that are not real errors.
- A GO verdict's "next action" (Step 10) must name a ticket-scoping step, never a direct change —
  this is the single most likely scope-creep failure mode named in both investigation.md and
  test_plan.md.
- `WORLD-076`'s `status: divergent` must be carried into the corpus verbatim, never silently
  upgraded to `verified` or filtered out for looking "messy" — it is the corpus's one real P0 case
  (Decision 4) and the divergence is itself real, documented history, not a data-quality defect to
  clean up.

## Decisions Made During Human Review

**Resolution of investigation.md Open Question 4 / this plan's former "Unresolved Questions"
section — does the corpus need a confirmed real P0 case?** Prior to human review, `FAC-012` was `P1`;
`INFRA-296`/`297`/`299` were `P1` (confirmed via `git show ab06fc10`); `INFRA-300` was `P2`. No real,
non-synthetic case in the corpus was `P0`, and `find_p0_intersection`'s own legacy behavior is P0-only
by definition, so a P0-blind real corpus would have meant this Gate's recall claim, however clean, had
never actually exercised the one priority tier the older of the two legacy tools exists specifically
to protect.

The user was presented two paths and explicitly chose **option 1 — time-boxed mine for a real P0 case
first** — check the one already-identified candidate (`46c5ae59` / `TCK-20260716-PLACELEGAL-HARDLAW`,
touching `docs/parity_ledger/world_dynamics.yaml`) plus at most 1-2 other shards' commit history if
needed, falling back to option 2 (documenting the gap as a stated limitation) only if the bounded
search came up empty.

**Outcome: the search succeeded on the first candidate checked.** `git show 46c5ae59 --
docs/parity_ledger/world_dynamics.yaml` confirmed `WORLD-076` is `priority: P0` with a genuine
`v2_evidence` citation of `src/observability/hard_law_monitor.py` and `src/engine/kernel.py`, and
`git show 46c5ae59 --stat` confirmed the same commit touched both of those exact `src/` files. No
further shards were checked — the time-box was honored and the fallback (option 2) was not needed.
`WORLD-076` (plus its co-cited sibling `WORLD-112` in `expected_obligation_ids`) is now part of the
`real_cases` corpus specified in Step 1, and Decision 4 above records the full resolution, including
the one nuance carried forward honestly rather than smoothed over: `WORLD-076`'s `status` is
`divergent`, not `verified`, which Step 10's decision-doc limitations section must state explicitly.

This section previously read "## Unresolved Questions" and, before human review, framed the choice as
two open, undecided paths — (1) time-boxed further mining, or (2) documenting a stated P0-blindness
limitation — with an explicit note that Step 1 should not freeze the corpus until the main session
picked one. That framing is now fully superseded by the resolution recorded above: path 1 was chosen,
attempted, and succeeded on the first candidate, so Step 1 proceeds with `WORLD-076` included in
`real_cases` and no residual open question remains.

## Deviations (recorded during Implementation)

None of these change the plan's Steps, Decisions, or Scope Guards — they are corrections and
additional real findings discovered while executing Steps 1 and 7 exactly as specified, recorded
here per CLAUDE.md's "never silently deviate" rule.

1. **Step 1's ground-truth derivation was corrected mid-construction, before any result was
   computed.** The plan's own worked example for `WORLD-076` derived `expected_obligation_ids`
   by reading `v2_evidence` text directly (Step 1's bullet: "the entry ID(s) whose real
   `v2_evidence` genuinely cites `changed_path_query`"). Applying that same v2_evidence-only
   method to `INFRA-296`/`INFRA-297` during corpus construction would have produced an
   incomplete expected set (`["INFRA-296"]` / `["INFRA-297"]` only) — a spot-check against
   `tools/parity_index.py`'s actual `_PATH_REF_RE` extraction (which scans `v2_evidence`,
   `legacy_evidence`, AND `text`, per `_populate_ref_tables`) showed `INFRA-299`'s own `text`
   field genuinely cites both `tools/context_packet_assembler.py` and
   `tools/retrieval_events.py` verbatim. Using a `v2_evidence`-only ground truth would have
   manufactured two spurious "false positives" for a real, human-confirmable citation the
   importer is designed to catch. Corrected before Step 3's freeze: all six real cases' expected
   sets are derived by applying `_PATH_REF_RE` to all three evidence fields the importer itself
   scans, matching real index behavior exactly. `INFRA-296`/`INFRA-297`'s `expected_obligation_ids`
   each grew from 1 entry to 2 (adding `INFRA-299`) as a result.
2. **Step 7 surfaced two real divergences beyond the plan's four originally-named shapes**
   (P0-only filter, ANY-of-multi-shard, faction-exclusion, malformed-shard silent-skip). Per the
   ticket's own instruction ("if a discrepancy is found... document and adjudicate it explicitly
   — never patch"), both are recorded, not smoothed into an existing category:
   - `derive_mapping`'s `_SRC_PATH_RE` only ever extracts `src/*.py` citations — it can never
     answer a `tools/*.py`-path query at all, regardless of citation quality (exercised by
     `INFRA-296`/`297`/`300`).
   - `tools/parity_index.py`'s `_PATH_REF_RE` only recognizes `src/`/`tools/`/`tests/`/`docs/`
     -prefixed paths; a genuinely-cited `.claude/`-prefixed path (`INFRA-299`'s own defining
     subject, `.claude/workflows/implement-ticket.js`) produces zero structured `code_refs`
     anywhere, even though 7 real entries' evidence text cites it. This is a shared blind spot
     (legacy is equally unable to serve this query for independent reasons), not a regression —
     but it is the review's single most important limitation and is stated as such in the
     decision document's §6.2, not omitted.
   - A third, related finding surfaced by the synthetic `SYN-MALFORMED-001` case:
     `find_p0_intersection` has no `try`/`except` around `yaml.safe_load` and raises an
     uncaught `yaml.YAMLError` on a malformed canonical shard — a real fragility beyond
     `TestEquivalenceFixtures`'s original malformed-shard scope (that suite only ever exercised
     `derive_mapping` against it, never `find_p0_intersection`). Documented in the decision
     doc's §6.3; not fixed.

Neither deviation required reopening Decisions 1-4 or the Steps' ordering; both are captured in
`gate_a_corpus.json`'s per-case `case_notes` and `docs/ai/parity_readpath_gate_a_decision.md`'s
§6 limitations section.
