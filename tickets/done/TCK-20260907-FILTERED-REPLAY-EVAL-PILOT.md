---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260907-FILTERED-REPLAY-EVAL-PILOT
phase: done
date: 2026-09-07
tags: [ai, agent-monitoring, testing]
---

# TCK-20260907-FILTERED-REPLAY-EVAL-PILOT

## Title
Filtered replay eval pilot — dataset hygiene + 3-tier metric execution (Bucket-B item 13)

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
`docs/plans/agent_infrastructure/ai_first_hardening_epics/agent_evaluation_foundation_experiment.md`
already has a complete, frozen experiment specification (Hypothesis, Baseline, Method, 3-tier
Metrics, Exit Criteria, Kill Criteria, Out-of-Scope) for roadmap item 13 — "Filtered replay eval
pilot + dataset hygiene + metric design", Horizon 1, Bucket B (Experiment). This ticket executes
that spec's Method: sample and stratify a small (20-40 ticket) slice of `tickets/done/`, split it
into dev/validation/holdout, convert the sample into replay fixtures, extend the existing
`tools/agent_replay/` replay layer to detect the 2 known recurring defect classes, run the sample
through the replay twice in an isolated worktree using the (now-shipped) session-scoped sidecar
path, compute the 3-tier metrics, and produce a results report against the spec's own Exit/Kill
criteria. This ticket does not re-derive or change the Hypothesis/Metrics/Exit/Kill Criteria
themselves — they are inherited as already decided.

## Scope
1. **Sample + stratify**: build a sampler that selects 20-40 tickets from `tickets/done/`,
   stratified by `## Tier` (hotfix/standard/epic), `layer` frontmatter, and success/failure (using
   the gate-failure terminal statuses in `agent-monitoring/data/*/runs.jsonl` — DOD_BLOCKED,
   NEEDS_HUMAN_INPUT, NEEDS_CHANGES, CONFLICTS_DETECTED, TESTS_FAILED, and related). Persist the
   resulting manifest as a durable, inspectable artifact (not a local variable) listing exact
   ticket IDs, strata, and split assignment.
2. **Dataset hygiene**: split the manifest into development / validation / untouched-holdout
   partitions (~60/20/20, adjusted to final sample size), recorded in the same manifest artifact.
3. **Fixture conversion**: build (or extend) a converter that turns each sampled ticket + its
   `stored_artifacts/{id}/` (investigation.md/plan.md/test_plan.md, where present) into a
   `FixtureEnvelope`-shaped YAML consumable by `tools/agent_replay/runner.py`'s `replay_slice()` —
   the only existing example of this shape today is
   `tests/fixtures/agent_replay/TCK-20260721-ORCHESTRATION-CONTRACT-ADR.yaml`, so this conversion
   tooling is new work, not a reuse of something already built in bulk. Tickets that cannot be
   converted (missing required artifacts) are excluded with a logged reason, not silently dropped.
4. **Defect-class detection**: extend the replay/scoring layer to detect the 2 known recurring
   defect classes named in `guardrail_enforcement_epic.md` (M2 — doc-update self-report gap; M3 —
   test-scoper background-hang pattern). `replay_slice()` today only branches on
   CONFLICTS_DETECTED / TAGS_NOT_REGISTERED / NEEDS_HUMAN_INPUT / review verdict — neither of the 2
   target classes has any existing detection logic, so this is new build work with its own unit
   tests, not a config toggle on existing code.
5. **Isolated replay execution, twice**: run the full sample through the replay pipeline twice (2
   independent runs) in an isolated worktree, using `implement-ticket.js`'s session-scoped
   `.claude/current_run.<SESSION_ID>` sidecar path exclusively (per M1, shipped 2026-09-04 —
   `TCK-20260904-SIDECAR-SETTINGS-HOOK-MIGRATE`) — never the shared unscoped
   `.claude/current_run` path. Capture evidence that no write touched `agent-monitoring/*.jsonl` or
   any concurrent live session's sidecar during the pilot's own execution.
6. **Compute the 3-tier metrics**: Primary (repeatable flag/detection rate on the 2 known defect
   classes across the 2 runs), Safety (contamination-risk evidence from step 5), Efficiency
   (wall-clock time + tool-call volume for the replay — informative only, not pass/fail).
7. **Results report**: state explicitly, for each of the spec's 3 Exit Criteria, met/not-met with
   evidence, and state explicitly whether either Kill Criterion fired. Report a negative finding
   honestly if either fires — do not silently rescope to a smaller claim.
8. **Document a repeatable refresh procedure** (script + short instructions) for adding newer
   closed tickets to the eligible pool later — documenting the procedure is in scope; actually
   re-running the refreshed pilot is not.

## Out of Scope
- Rewriting, re-deriving, or second-guessing the Hypothesis, Baseline, Metrics definitions,
  Exit Criteria, or Kill Criteria in `agent_evaluation_foundation_experiment.md` — this ticket
  executes against them as already decided.
- Widening the sample beyond 20-40 tickets, or building a general eval platform, before this
  pilot's own exit criteria are met (explicitly the spec's own Out-of-Scope item; see
  `bucket_c_future_options.md`'s "Full agent-behavior eval platform" entry, item 20).
- Deriving a task-success-rate metric for the retro loop from this pilot's results — separate,
  larger Bucket-C item (roadmap item 19), gated on this one succeeding, not a byproduct this
  ticket produces automatically.
- Any change to `implement-ticket.js`'s production behavior — the replay calls the same real,
  already-tested functions read-only/imported, in isolation; it never modifies the orchestrator.
- Live Codex provider comparison work or model-based routing decisions (roadmap items 18/21) —
  hard-gated on this pilot's results, not part of running it.
- Updating `docs/parity_ledger/` entries — this ticket builds pilot/analysis tooling and produces
  an evidence report; it does not change any authoritative simulation/gameplay behavior, so no
  parity ledger entry applies. Called out explicitly to preempt scope confusion at the Parity
  pipeline phase.

## Acceptance Criteria
- [x] A durable sample manifest exists (checked into `stored_artifacts/{ticket_id}/` or an
      equivalent durable location) listing 20-40 ticket IDs, their tier/layer/success-failure
      strata, and their dev/validation/holdout split assignment.
- [x] Each sampled ticket has a corresponding replay fixture, or a logged exclusion reason if it
      could not be converted (e.g. missing `stored_artifacts/`).
- [x] The extended replay/scoring layer has passing unit tests demonstrating it detects both the
      doc-update self-report gap and the test-scoper background-hang pattern on at least one
      known-positive fixture each.
- [x] The full sample is replayed twice, in an isolated worktree, using the session-scoped sidecar
      path exclusively — with logged evidence (e.g. file-write audit or hash comparison) that no
      write touched `agent-monitoring/*.jsonl` or any shared/unscoped sidecar path during the
      pilot's own execution.
- [x] A results report exists that states, for each of the 3 Exit Criteria in
      `agent_evaluation_foundation_experiment.md`, met/not-met with concrete supporting evidence,
      and explicitly states whether either Kill Criterion fired.
- [x] The results report includes concrete numbers for all 3 metric tiers (Primary flag-rate
      consistency across the 2 runs; Safety contamination-check result; Efficiency wall-clock/
      tool-call figures) — not qualitative-only claims.
- [x] The results report states the real, freshly-measured corpus/baseline counts (ticket-done
      count, tier breakdown, artifact-coverage percentage, `runs.jsonl` record count) rather than
      repeating `agent_evaluation_foundation_experiment.md`'s original figures uncritically — those
      figures were found to be stale/approximate during ticket scoping (see Assumptions below).

## Related Tickets
- `TCK-20260904-AI-FIRST-HARDENING-FOLLOWON-EPIC` (`tickets/inprogress/`) — the Bucket B/C tracking
  epic this item (roadmap item 13) is enumerated under; that epic's own acceptance criteria expect
  this ticket to be linked back to it.
- `TCK-20260904-SIDECAR-SETTINGS-HOOK-MIGRATE` (done, 2026-09-04) — shipped the M1 session-scoped
  sidecar fix this pilot's Method step 5 (isolation) depends on. Confirmed landed; the spec's own
  "do not run before this milestone lands" precondition and related Kill Criterion risk are
  cleared.
- `TCK-20260824-SIDECAR-CROSS-SESSION-SCOPE`, `TCK-20260824-RETRIEVAL-CACHE-SIDECAR-UNIFY` (done) —
  earlier partial sidecar-isolation fixes M1 completed; background for why isolation now holds.
- `TCK-20260721-CODEX-REPLAY-PROOF` (done) — built the existing `tools/agent_replay/`
  runner/fixture-envelope infrastructure this pilot extends rather than reinvents.

## Related Docs
- `docs/plans/agent_infrastructure/ai_first_hardening_epics/agent_evaluation_foundation_experiment.md`
  — the frozen experiment spec this ticket executes (Hypothesis/Baseline/Method/Metrics/Exit/Kill
  Criteria/Out-of-Scope).
- `docs/plans/agent_infrastructure/ai_first_hardening_epics/roadmap.md` — item 13, Horizon 1
  placement, and the downstream Bucket-C dependency notes (items 18-20).
- `docs/plans/agent_infrastructure/ai_first_hardening_epics/guardrail_enforcement_epic.md` (M2, M3)
  — source and definition of the 2 known recurring defect classes this pilot scores against.
- `docs/plans/agent_infrastructure/ai_first_hardening_epics/workflow_reliability_epic.md` (M1) —
  the sidecar-isolation prerequisite; confirmed SHIPPED 2026-09-04.
- `docs/ai/replay_fixture_spec.md` — the fixture envelope shape and the unconditional forbidden-
  script containment law any new fixture-conversion tooling must respect.
- `docs/plans/agent_infrastructure/ai_first_hardening_epics/bucket_c_future_options.md` — items
  18-20, the downstream work explicitly gated on this pilot's exit criteria.

**Not touched by this run (pre-existing, from sibling tickets sharing this uncommitted worktree)**:
`docs/REGISTRY.yaml` (mechanically regenerated by `make docs-registry` at each sibling ticket's own
Finalize step, per CLAUDE.md's "After Work" convention — not edited by this ticket's own diff),
`docs/agent-monitoring/schema.md` (the new `claim_detections` schema section belongs to
`TCK-20260907-TICKET-CLAIM-DETECTION-LOGGING`), `docs/ai/phase_resume_validation_rule_decision.md`
(the full deliverable of `TCK-20260907-PHASE-RESUME-VALIDATION-RULE-DESIGN`),
`docs/parity_ledger/infrastructure.yaml` (the `INFRA-411` entry belongs to
`TCK-20260907-TICKET-CLAIM-DETECTION-LOGGING` — this ticket's own Out of Scope explicitly states no
parity ledger entry applies to it),
`docs/plans/agent_infrastructure/ai_first_hardening_epics/ticket_claim_detection_experiment.md`
(the Experiment Specification document `TCK-20260907-TICKET-CLAIM-DETECTION-LOGGING` writes).

## Related Stored Artifacts
- `stored_artifacts/TCK-20260721-CODEX-REPLAY-PROOF` — built the replay runner/fixture-envelope
  infra this ticket extends.
- `stored_artifacts/TCK-20260721-CODEX-REPLAY-PARITY`, `stored_artifacts/TCK-20260716-AGENTOPS-REPLAY-TIMELINE`
  — adjacent prior replay-tooling investigations, background only.
- No prior stored artifact investigates this exact pilot scope — confirmed no duplicate
  investigation exists.

## Related Code Areas
- `tools/agent_replay/runner.py`, `tools/agent_replay/fixture_envelope.py` — extend with
  defect-class detection logic.
- `tests/agent_replay/`, `tests/fixtures/agent_replay/` — add new fixtures and unit tests.
- `agent-monitoring/data/*/runs.jsonl`, `agent-monitoring/data/*/events.jsonl` — read-only source
  of the real failure-rate baseline and sample stratification.
- `tickets/done/`, `stored_artifacts/` — read-only source corpus for sampling and fixture
  conversion.
- `docs/ai/replay_fixture_spec.md` — update if the fixture envelope shape is extended for
  defect-class fields.

## Assumptions / Open Questions
- **Baseline figures in `agent_evaluation_foundation_experiment.md` are stale/approximate, not
  exact** — verified directly during scoping (2026-09-07): actual top-level `tickets/done/` file
  count is 1,849 (not the doc's 1,752), with body-field `## Tier` breakdown 1,401 standard / 312
  hotfix / 52 epic / 3 unlabeled (not 1,331/292/45 as stated — the doc's total was 1,668, actual
  typed total is 1,768). Actual standard-tier tickets with a matching `stored_artifacts/{id}/`:
  1,169 of 1,401 (83.4%), close to but not identical to the doc's 82.6%/1,099-of-1,331 claim.
  `agent-monitoring/data/*/runs.jsonl` records total 1,476+ across all weekly shards checked (not
  exactly the doc's 1,388) — and there is **no single top-level `agent-monitoring/runs.jsonl` file
  today**; records live sharded under `agent-monitoring/data/YYYY-Www/runs.jsonl` per this repo's
  current monitoring-unification convention (per `2890ad46` / `7ffe7fe4`), contradicting the doc's
  literal path reference. None of these discrepancies invalidate the experiment's premise — the
  corpus and failure-rate data genuinely exist, in sufficient volume for a 20-40 ticket stratified
  sample — but the sampler/report must re-derive exact counts live rather than citing the spec
  doc's numbers verbatim.
- **M1 (sidecar session-scoping) status: CONFIRMED SHIPPED** as of 2026-09-04
  (`TCK-20260904-SIDECAR-SETTINGS-HOOK-MIGRATE`), lifting the spec's own "do not run this
  experiment before that milestone lands" precondition and the related Kill Criterion risk. If the
  implementer's working tree somehow predates this, re-verify before proceeding.
- **`tools/agent_replay/`'s existing `replay_slice()` does not yet detect either target defect
  class.** It only replays the Scope/Investigate/Plan/Review deterministic gate branches
  (CONFLICTS_DETECTED, TAGS_NOT_REGISTERED, NEEDS_HUMAN_INPUT, review verdict) against a hand-built
  `FixtureEnvelope`, and only 1 example fixture exists repo-wide
  (`tests/fixtures/agent_replay/TCK-20260721-ORCHESTRATION-CONTRACT-ADR.yaml`). Real new-build work
  (bulk fixture-conversion tooling + defect-class detection logic) is required — this is why the
  ticket is `standard` tier, not `hotfix`.
- **Confirmed no relationship to the just-merged Provider-Adapter Boundary work**
  (`TCK-20260904-PROVIDER-PORTABILITY-CONFORMANCE-TEST`,
  `docs/architecture/agent_orchestration_contract.md`) — neither artifact mentions "replay"
  anywhere; they are unrelated subsystems that happen to sit near each other in the roadmap
  (provider portability vs. replay eval), not a shared code path or dependency in either
  direction.
- `layer: ai` chosen to match the source experiment-spec doc's own frontmatter (`layer: ai`) — this
  is Claude agent/orchestration tooling, not gameplay AI/cognition (which lives under `strategy`).

## Implementation Notes

Implemented the plan's 9 steps as new modules under `tools/agent_replay/` (all additive — none of
`runner.py`'s 4 existing branch points or `fixture_envelope.py`'s required-key set were touched):

- **Step 1** `sampler.py::build_sample_manifest()` — enumerates `tickets/done/TCK-*.md`, derives
  tier (body `## Tier`) / layer (frontmatter) / outcome-stratum (from
  `agent_replay_codex.monitoring_shards.source_paths()` over `runs.jsonl` shards), proportionally
  samples into a hard `[20, 40]` bound, splits ~60/20/20, persists to
  `stored_artifacts/{id}/sample_manifest.yaml`.
- **Step 2** `fixture_converter.py::convert_ticket_to_fixture()`/`convert_sample()` — builds a
  FixtureEnvelope YAML per ticket from real `events.jsonl` phase rows + `stored_artifacts/`
  paths, reconstructing `Review.output.verdict` from the truncated summary; records
  `review_output_fidelity` per fixture in `conversion_log.yaml`; logs a specific reason (never
  silent) for any ticket missing `stored_artifacts/`, `investigation.md`, `plan.md`, or any of the
  4 phase events (hotfix-tier tickets have no Investigate/Plan/Review events at all — the single
  largest exclusion reason in the real sample). Every accepted fixture round-trips through the
  unmodified `fixture_envelope.load_fixture()` before acceptance.
- **Steps 3-4** `defect_detectors.py` — `detect_m2_doc_update_gap()` reimplements
  `check_docs_to_update_coverage`'s reverse-direction comparison against a historical git diff
  instead of live `git status` (excludes the mechanically-regenerated `docs/REGISTRY.yaml`, which
  would otherwise false-positive-fire on almost every ticket). `detect_m3_background_hang()`
  reimplements the live `SubagentStop` hook's own condition against a fixture payload. Neither
  imports/subprocesses the live gate/hook modules they model (`done_checker_static.py`,
  `subagent_stop_background_guard.py`) — both are read-only references only.
- **Step 5** `pilot_isolation.py::run_pilot_isolated()` — no literal `git worktree add` (per
  plan.md's Risk #2 resolution). Locally reimplements the porcelain/content-hash zero-diff
  technique, watch set sourced from `monitoring_shards.source_paths()` + `tickets/`; imports
  `agent_replay_codex.containment.snapshot_monitoring_lines`/`assert_monitoring_prefix_preserved`
  as-is for the append-only + no-pilot-attributed-new-line check; separately asserts the unscoped
  `.claude/current_run` sidecar's mtime/content is unchanged across the pilot's 2-run window.
- **Step 6** `metrics.py::compute_metrics()`/`compare_repeatability()` — the 3 named tiers only.
- **Step 7** `run_pilot.py` (driver script, implementer's discretion per plan.md) — executed the
  full pilot against the real repository.
- **Step 8** `run_pilot.py::write_results_report()`/`append_spec_doc_results()`/
  `update_roadmap_status()` — wrote `stored_artifacts/{id}/results.md`, appended `## Results`/
  `## Decision` to `agent_evaluation_foundation_experiment.md` (Hypothesis/Method/Metrics/Exit/
  Kill Criteria text untouched), updated `roadmap.md` item 13's row.
- **Step 9** `docs/ai/replay_pilot_refresh_procedure.md` — documented only, never executed.

**Real bug found and fixed during the pilot's own live execution** (see plan.md's new
"Deviations" section for full detail): the first working version of `run_pilot.py`'s
closing-commit resolution (`git log --follow --diff-filter=A`) picked up an unrelated giant
batch-merge commit for tickets first added to `tickets/done/` inside a bundled PR, producing a
spurious 5/5 M2 fire rate. Root-caused and replaced with `_build_ticket_commit_index()`, which
finds the real per-ticket commit via this project's own Commit Convention (`TCK-ID: subject`),
scanned across `git log --all` (the checked-out worktree branch's own history alone stops after
~197 commits and omits real historical commits reachable only via `origin/main`/other branches).
After the fix, the real sample's M2 application is 0/5 fired — manually cross-checked against one
ticket's real `git show` output vs. its real `## Files Changed` text: genuinely no gap. A real,
disclosed limitation remains: tickets closed only inside a multi-ticket batch/epic-merge commit
have no isolable per-ticket doc diff at all — `run_pilot.py` records these separately
(`m2_no_isolable_commit_tickets`) rather than guessing, and this is disclosed in `results.md`'s
Exit Criterion 2 evidence.

`test_results_report.py`'s vocabulary-marker assertion was corrected from "the literal strings
'met'/'not met'/'fired'/'not fired' must all appear somewhere in results.md" (impossible to
satisfy honestly once the real run found all 3 Exit Criteria MET and 0 Kill Criteria FIRED,
without fabricating a false claim) to "each criterion's verbatim text is immediately followed by
a MET/NOT MET or FIRED/NOT FIRED label" — matching test_plan.md test #13's own stated scope
("a structural completeness check... not a check on which way they resolved").

## Test Summary

All 13 new tests (test_plan.md) pass, plus the full existing `tests/agent_replay/` regression
suite (42/42 total): `pytest tests/agent_replay/ -v`. The 2 read-only regression commands
(`pytest tests/tools/test_subagent_stop_background_guard.py -v`,
`pytest tests/tools/ -k "docs_to_update or check_docs" -v`) both pass unchanged, confirming this
ticket did not modify the 2 live guardrail mechanisms (M2's `check_docs_to_update_coverage`, M3's
`subagent_stop_background_guard.py`) it models fixtures against. `tests/agent_replay/
test_runner_no_forbidden_calls.py`'s existing whole-file string-constant scan already covers every
new module by directory glob (`tools/agent_replay/*.py`) with no changes needed — confirmed all 5
of its tests still pass against the 6 new modules.

## Files Changed

- `tools/agent_replay/sampler.py` — new (Step 1).
- `tools/agent_replay/fixture_converter.py` — new (Step 2).
- `tools/agent_replay/defect_detectors.py` — new (Steps 3-4).
- `tools/agent_replay/pilot_isolation.py` — new (Step 5).
- `tools/agent_replay/metrics.py` — new (Step 6).
- `tools/agent_replay/run_pilot.py` — new (Step 7-8 driver/report generator).
- `tests/agent_replay/test_sampler.py` — new, 2 tests.
- `tests/agent_replay/test_fixture_converter.py` — new, 2 tests.
- `tests/agent_replay/test_defect_detectors.py` — new, 4 tests.
- `tests/agent_replay/test_pilot_isolation.py` — new, 4 tests (2 required by test_plan.md #9/#10,
  2 additional regression guards for the mutation-detection/run_id-exclusion invariants).
- `tests/agent_replay/test_metrics.py` — new, 3 tests (2 required by test_plan.md #11/#12, 1
  additional agreement-case guard).
- `tests/agent_replay/test_results_report.py` — new, 1 test.
- `tests/fixtures/agent_replay/pilot/m3_synthetic_known_positive.yaml` — new, hand-built synthetic
  M3 known-positive fixture.
- `tests/fixtures/agent_replay/pilot/sample/*.yaml` — new, 5 real converted fixtures (this pilot's
  own live output from Step 7's execution).
- `stored_artifacts/TCK-20260907-FILTERED-REPLAY-EVAL-PILOT/sample_manifest.yaml` — new (Step 1
  durable output).
- `stored_artifacts/TCK-20260907-FILTERED-REPLAY-EVAL-PILOT/conversion_log.yaml` — new (Step 2
  durable output).
- `stored_artifacts/TCK-20260907-FILTERED-REPLAY-EVAL-PILOT/pilot_run_raw_output.json` — new (raw
  per-run results feeding Step 8's report).
- `stored_artifacts/TCK-20260907-FILTERED-REPLAY-EVAL-PILOT/results.md` — new (Step 8 full report).
- `docs/plans/agent_infrastructure/ai_first_hardening_epics/agent_evaluation_foundation_experiment.md`
  — appended `## Results`/`## Decision` sections (Hypothesis/Baseline/Method/Metrics/Exit/Kill
  Criteria/Out-of-Scope text unchanged).
- `docs/plans/agent_infrastructure/ai_first_hardening_epics/roadmap.md` — updated item 13's row
  with the pilot's outcome.
- `docs/ai/replay_pilot_refresh_procedure.md` — new (Step 9, documentation only).
- `staging_artifacts/TCK-20260907-FILTERED-REPLAY-EVAL-PILOT/investigation.md` — added the
  resolved-conditional-bullet note for `docs/ai/replay_fixture_spec.md` (condition not met — the
  envelope shape was not extended).
- `staging_artifacts/TCK-20260907-FILTERED-REPLAY-EVAL-PILOT/plan.md` — added a "Deviations"
  section documenting the closing-commit-resolution bug found/fixed during Implement and the
  `test_results_report.py` assertion correction.
- `tickets/inprogress/TCK-20260907-FILTERED-REPLAY-EVAL-PILOT.md` — this file (Status, Acceptance
  Criteria, Implementation Notes, Test Summary, Files Changed, Completion Summary).
- `tickets/todos/TCK-20260907-FILTERED-REPLAY-EVAL-PILOT.md` — deleted (stale duplicate of the
  ticket left in `tickets/todos/` from Scope; not a folder-tracked origin).

## Completion Summary

Implemented all 9 plan steps as new, additive modules under `tools/agent_replay/` and executed
the pilot end-to-end against the real repository (not a synthetic dry run): sampled 27 tickets
(hard-bounded 20-40) from the live 1815-ticket `tickets/done/` corpus, converted 5 to real
fixtures (22 excluded with logged reasons, mostly hotfix-tier tickets with no Investigate/Plan/
Review phase events), applied the M2 detector to all 5 real converted tickets (0/5 fired — a real,
disclosed finding, not a detector defect) and the M3 detector only to its own synthetic/clean
fixtures (never claimed against real historical data), replayed the sample twice under isolation
with zero contamination detected, and computed all 3 metric tiers. A real bug in the closing-
commit git-history resolution was found and fixed mid-implementation (see Implementation Notes).
All 3 Exit Criteria are MET and neither Kill Criterion FIRED in this pilot's real execution — a
genuine positive result, reported with full evidence and disclosed limitations (M2's live sample
finding is thin at n=5; a batch-merge-commit blind spot exists for a real fraction of the
corpus), not a smoothed-over claim. Results are recorded in `stored_artifacts/{id}/results.md`
and appended to the frozen spec doc and roadmap.md per plan.md Step 8.
