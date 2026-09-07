---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260907-FILTERED-REPLAY-EVAL-PILOT
artifact_type: plan
tags: [ai, agent-monitoring, testing]
---

# Implementation Plan — TCK-20260907-FILTERED-REPLAY-EVAL-PILOT

## Summary

This plan builds the pilot in 9 ordered steps, each producing one new module/artifact under
`tools/agent_replay/` (or a results doc), verified by the matching test(s) in
`staging_artifacts/TCK-20260907-FILTERED-REPLAY-EVAL-PILOT/test_plan.md`. All new detection/
isolation/read logic is additive — it never edits `runner.py`'s 4 existing branch points or
`fixture_envelope.py`'s current required-key set (investigation.md Current Behavior §2, citing
`tools/agent_replay/runner.py` lines 79-98 and `fixture_envelope.py` lines 72-77). The 5 Risks
flagged in investigation.md's "Risks and Open Questions" are each resolved explicitly below,
crediting the investigation's own reasoning, not left open. The approach: sample → convert →
detect (M2 real-historical, M3 synthetic-disclosed) → isolate (reuse proven zero-write pattern,
not a literal `git worktree add`) → run twice → compute 3-tier metrics → report into both
`stored_artifacts/{id}/results.md` and the frozen spec doc + roadmap.md → document (not execute)
a refresh procedure.

## Steps

### Step 1 — Sampler: stratified manifest builder

**Files:** `tools/agent_replay/sampler.py` (new), `stored_artifacts/TCK-20260907-FILTERED-REPLAY-EVAL-PILOT/sample_manifest.yaml` (new, durable output)

**Change:** Build `build_sample_manifest(done_dir, monitoring_root, sample_size_range=(20, 40)) ->
SampleManifest` that:
1. Enumerates top-level `tickets/done/*.md` files (excluding tracking subfolders, matching
   investigation.md Current Behavior §6's "1,852 top-level `.md`... 1,815 are `TCK-*.md`" count
   methodology — re-derive live, never hardcode the investigation's numbers, per ticket Assumptions
   section and AC #6).
2. For each ticket, parses body field `## Tier` (hotfix/standard/epic) and frontmatter `layer:` —
   same fields the ticket format mandates per the project's own Ticket Format rules.
3. Reads `agent-monitoring/data/*/runs.jsonl` for terminal gate-failure statuses (DOD_BLOCKED,
   NEEDS_HUMAN_INPUT, NEEDS_CHANGES, CONFLICTS_DETECTED, TESTS_FAILED, and related) to derive the
   success/failure stratum per ticket, using `tools/agent_replay_codex/monitoring_shards.py`'s
   `source_paths()`/`read_source_bytes()` (74 lines, confirmed already reads across all
   `agent-monitoring/data/<week>/<source>.jsonl` shards including the `unknown-week` fallback —
   investigation.md Current Behavior §8) — never the 4 forbidden `tools/agent-monitoring/` scripts
   (`pre_tool_hook.py`, `post_tool_hook.py`, `record_run.py`, `record_events.py`), per the
   unconditional containment law (`docs/ai/replay_fixture_spec.md` lines 89-96, cited in
   investigation.md Current Behavior §4).
4. Stratifies and samples 20-40 tickets across tier × layer × success/failure cells (proportional
   sampling, exact algorithm at implementer's discretion — the test only asserts the resulting
   manifest properties, per test_plan.md test #1).
5. Splits into dev/validation/holdout at ~60/20/20 (Scope item 2), recording the split in the same
   manifest object, not a separate file.
6. Serializes the manifest to `stored_artifacts/{ticket_id}/sample_manifest.yaml` (a real file on
   disk, re-loadable) — this satisfies Scope item 1's "durable, inspectable artifact (not a local
   variable)" requirement directly.

**Other writers to this resource:** `stored_artifacts/{ticket_id}/` is a per-ticket directory this
pilot owns exclusively during this ticket's execution — no other live code path writes into it
concurrently (it does not yet exist until this ticket creates it). `agent-monitoring/data/*/
runs.jsonl` (read-only here) is written by many other paths (the 4 forbidden scripts, concurrent
live `implement-ticket.js` sessions) — Step 1 only reads it via `monitoring_shards.py`, never
writes, so no ordering/race concern applies to this step specifically (the write-side race is
handled in Step 5's isolation evidence, not here).

**Do NOT touch:** `tools/agent_replay/runner.py`, `fixture_envelope.py` (unmodified in this step);
do not read `agent-monitoring/runs.jsonl` as a single top-level file (confirmed not to exist,
investigation.md Current Behavior §6) — always the sharded `data/<week>/` layout.

**Verify:** test_plan.md tests #1 (`test_sampler_produces_valid_stratified_manifest`) and #2
(`test_sampler_persists_manifest_as_durable_artifact`), `tests/agent_replay/test_sampler.py`.

---

### Step 2 — Fixture converter: ticket + stored_artifacts → FixtureEnvelope YAML

**Files:** `tools/agent_replay/fixture_converter.py` (new), `tests/fixtures/agent_replay/pilot/` (new dir for generated fixtures), `stored_artifacts/{ticket_id}/conversion_log.yaml` (new)

**Change:** Build `convert_ticket_to_fixture(ticket_id, ticket_path, stored_artifacts_dir) ->
ConversionResult` modeled directly on the one existing hand-built example
`tests/fixtures/agent_replay/TCK-20260721-ORCHESTRATION-CONTRACT-ADR.yaml` (70 lines, full shape
confirmed in investigation.md Current Behavior §3: `version: 1`, `source: {ticket_id, ticket_path,
stored_artifacts_dir, events_run_id, events_seq_range, final_status, tier}`, then 4 `phases`
entries for Scope/Investigate/Plan/Review, each with the 5 required phase keys `phase`/`agent`/
`input`/`output`/`transition` per `fixture_envelope.py`'s `_REQUIRED_PHASE_KEYS` (lines 74-75,
investigation.md Current Behavior §2)). Concretely:
1. Reads the real permanent files (`ticket_path`, `stored_artifacts_dir/investigation.md`,
   `.../plan.md`) by path reference only — never embeds copies inline, matching the existing
   fixture's own documented convention ("the runner reads the real permanent files at replay time,
   not a copy embedded here" — investigation.md Current Behavior §4).
2. Reconstructs `Review.output.verdict`/`.violations` from `agent-monitoring/data/*/events.jsonl`'s
   truncated `summary` field (200-char cap, `docs/agent-monitoring/schema.md` line ~445-462, cited
   investigation.md Current Behavior §3) where no fuller record exists.
3. **Resolves Risk #5 (per-fixture fidelity disclosure):** for every converted fixture, records a
   `review_output_fidelity: full | reconstructed_from_truncated_summary` field in
   `conversion_log.yaml` alongside the ticket ID — this makes the known 200-char-cap limitation
   visible per-fixture rather than smoothed over, directly per investigation.md Risk #5's
   requirement ("should be surfaced per-fixture in the manifest/conversion-exclusion log, not
   silently smoothed over"). This field is metadata in the conversion log, not a new required key
   on the `FixtureEnvelope` schema itself, so `fixture_envelope.py`'s existing required-key set is
   unchanged (see the conditional doc-update note under Docs Requiring Update below).
4. For a ticket missing `stored_artifacts/{id}/` entirely, or missing `investigation.md`/
   `plan.md` within it, does NOT attempt conversion — appends an entry to `conversion_log.yaml`
   with a specific reason string (e.g. `"missing stored_artifacts/{id}/plan.md"`), satisfying the
   ticket's Scope item 3 exclusion requirement.
5. Every successfully converted fixture is validated by loading it through the existing,
   unmodified `fixture_envelope.py::load_fixture()` before being accepted — a fixture that fails
   `load_fixture()`'s fail-closed validation is treated the same as an unconvertible ticket (logged
   exclusion, not silently dropped).

**Other writers to this resource:** `tests/fixtures/agent_replay/pilot/` and
`stored_artifacts/{ticket_id}/conversion_log.yaml` are new, pilot-owned paths with no other
concurrent writer. `agent-monitoring/data/*/events.jsonl` is read-only here (written by the 4
forbidden scripts and live sessions elsewhere) — same no-write, no-race posture as Step 1.

**Do NOT touch:** `fixture_envelope.py`'s required-key sets (unless the conditional envelope
extension in Docs Requiring Update is actually needed — default assumption for this plan is it is
NOT needed, since fidelity metadata lives in `conversion_log.yaml`, not the envelope itself); the
one existing hand-built fixture `TCK-20260721-ORCHESTRATION-CONTRACT-ADR.yaml` (read as a shape
reference only, never modified).

**Verify:** test_plan.md tests #3 (`test_fixture_converter_handles_convertible_ticket`) and #4
(`test_fixture_converter_logs_exclusion_reason_for_unconvertible_ticket`),
`tests/agent_replay/test_fixture_converter.py`.

---

### Step 3 — M2 detector: doc-update self-report gap (historical, real-signal)

**Files:** `tools/agent_replay/defect_detectors.py` (new, M2 function)

**Change:** Build `detect_m2_doc_update_gap(ticket_id, closing_commit_diff_docs_paths,
files_changed_text, related_docs_text) -> M2Result` that reimplements the same forward/reverse
comparison logic as the live `check_docs_to_update_coverage`'s reverse direction
(`tools/gate_checks/done_checker_static.py` lines 553-570 per investigation.md Current Behavior
§5), but against a **historical** git diff source instead of live `git status`:
1. Input: the set of `docs/`-prefixed paths shown as touched in the ticket's own closing commit(s)
   (obtained via `git log --name-only`/`git show --name-only` restricted to `docs/`, per
   investigation.md Current Behavior §5's confirmed reconstructability claim — "fully
   reconstructable for a *historical* ticket without any live git working-tree state").
2. Compares against the ticket's own resolved `## Files Changed`/`## Related Docs` body-section
   text (parsed from the closed ticket's `.md` file).
3. Flags a gap when a real `docs/` path was touched in the commit but never mentioned in either
   section — the same signal shape `check_docs_to_update_coverage` already computes live, per
   investigation.md's explicit statement "the comparison logic is directly reusable, only the diff
   source changes."
4. Do not modify `done_checker_static.py` itself — this is new, separate logic in
   `tools/agent_replay/defect_detectors.py` that models the same comparison against historical
   input, per test_plan.md's Regression Surface requirement that
   `tests/tools/test_gate_checks_static.py` stay unaffected.
5. Known-positive fixtures (per investigation.md Current Behavior §5, all confirmed real instances
   where the gap fired and was caught at Verify): `TCK-20260831-ITEM-INSTANCE-HISTORY`,
   `TCK-20260831-RACE-RELATIONS-MATRIX`, `TCK-20260831-READINESS-SPEED-FORMULA`. Use at least one
   of these three (converted via Step 2's converter) as the known-positive input for the required
   unit test.
6. Also build a "clean" case — a normal closed ticket where every touched `docs/` path IS listed —
   to prove the detector does not fire on non-gap fixtures (test_plan.md test #6 explicitly guards
   against a trivial always-true stub).

**Other writers to this resource:** `defect_detectors.py` is a new file with no other writer.
`done_checker_static.py` (read as reference implementation only, never imported/modified — the M2
detector reimplements the comparison logic locally rather than importing the live gate check, to
avoid coupling the pilot's replay-time logic to the live orchestrator's gate module).

**Do NOT touch:** `tools/gate_checks/done_checker_static.py` (the live M2 fix, already shipped by
`TCK-20260904-DOC-COVERAGE-REVERSE-CHECK` — read-only reference, per Anti-Drift Hazards).

**Verify:** test_plan.md tests #5 (`test_m2_doc_update_self_report_gap_detector_fires_on_known_positive`)
and #6 (`test_m2_detector_does_not_fire_on_clean_fixture`), `tests/agent_replay/test_defect_detectors.py`.

---

### Step 4 — M3 detector: test-scoper background-hang pattern (synthetic, disclosed)

**Files:** `tools/agent_replay/defect_detectors.py` (same file, M3 function), `tests/fixtures/agent_replay/pilot/m3_synthetic_known_positive.yaml` (new)

**Change: resolves Risk #1 explicitly, adopting investigation.md's recommended option (c).**
Per investigation.md Current Behavior §5 and Risks §1: `background_tasks` is a live-runtime-only
signal (per `tools/agent-monitoring/subagent_stop_background_guard.py`'s module docstring, "a live
per-session task registry," confirmed via a full grep of `docs/agent-monitoring/schema.md` finding
zero schema field for it) that is never persisted to any stored artifact for a past ticket — there
is no reliable way to reconstruct a genuine per-ticket historical instance from
`tickets/done/`/`stored_artifacts/`/`events.jsonl`/`tools.jsonl`. Given this, and per the frozen
spec's own "Terminology discipline" clause (only claim what's directly observed), this plan adopts
**option (c)**: the M3 known-positive fixture is an explicitly synthetic, hand-built payload —
NOT derived from or claimed to represent any real `tickets/done/` sample member. Concretely:
1. Build `detect_m3_background_hang(subagent_stop_payload) -> M3Result` that reimplements the same
   detection condition as the live hook (`background_tasks` array non-empty and
   `stop_hook_active` is false — `tools/agent-monitoring/subagent_stop_background_guard.py`, 76
   lines, per investigation.md Current Behavior §5), without importing or subprocessing that
   forbidden script (per the unconditional containment law).
2. Hand-build `m3_synthetic_known_positive.yaml`: a minimal payload simulating a `SubagentStop`
   event with a non-empty `background_tasks` array at a `test-scoper` phase. Its header comment
   must explicitly state: "SYNTHETIC — hand-built to exercise the M3 detector's own logic; does NOT
   represent a real historical `tickets/done/` instance; no reliable historical signal for this
   defect class exists (see investigation.md Risks and Open Questions #1)."
3. The known-positive unit test (test_plan.md test #7) and any later results-report reference to
   this test must use the word "synthetic" explicitly — never phrase M3's detection result as
   validated "against a real historical ticket" the way M2's is. This provenance distinction must
   also propagate into Step 8's results report (Primary metric tier: M2 evidenced against real
   historical fixtures, M3 evidenced against a synthetic guard-level fixture only).
4. Build the paired "clean" case (empty `background_tasks`) confirming the detector does not fire,
   matching the real hook's own "allows completed"/"allows no-task case" behavior (investigation.md
   Current Behavior §5).

**Other writers to this resource:** `defect_detectors.py` (shared with Step 3, additive function,
no conflict). `subagent_stop_background_guard.py` (read as reference only, never imported —
inheriting the same containment-law reasoning as Step 3's M2 detector).

**Do NOT touch:** `tools/agent-monitoring/subagent_stop_background_guard.py` (the live M3 fix,
already shipped — read-only reference per Anti-Drift Hazards; never import or subprocess it).

**Verify:** test_plan.md tests #7 (`test_m3_test_scoper_background_hang_detector_fires_on_known_positive`)
and #8 (`test_m3_detector_does_not_fire_on_clean_fixture`), `tests/agent_replay/test_defect_detectors.py`.

---

### Step 5 — Isolation mechanism: reused snapshot-diff pattern, widened to the sharded layout

**Files:** `tools/agent_replay/pilot_isolation.py` (new)

**Change: resolves Risk #2 and Risk #3 explicitly, adopting investigation.md's recommended
options.**

**Risk #2 resolution (option (b), not a literal `git worktree add`):** This plan does NOT create a
real git worktree for the pilot's 2 replay runs. Instead it reuses the existing, already-proven
zero-write execution path: `replay_slice()` (`tools/agent_replay/runner.py`) is already proven
zero-write by `tests/agent_replay/test_no_mutation_snapshot.py` (132 lines, full read per
investigation.md Current Behavior §7) — its own `_fake_write_monitoring`/`_fake_hook_boundary`
no-ops (runner.py lines 50-59) mean it never touches durable state regardless of which directory it
runs from. Rationale, crediting investigation.md Risks §2: this is lower-risk than standing up a
literal worktree and directly reuses already-tested code. **This plan's results report (Step 8)
must state explicitly that "isolated worktree" (Method step 3's literal wording) was satisfied via
a proven zero-write execution path plus a snapshot-diff check, not via literal `git worktree add`
creation** — this disclosure is a required content item of Step 8, not optional framing.

**Risk #3 resolution (corrected during Review — see Review Round 1 below):** `tools/
agent_replay_codex/containment.py`'s `_WATCHED_GIT_PATHSPECS`/`_watched_files()` hardcode the
retired 3-file layout (`agent-monitoring/{runs,events,tools}.jsonl` — confirmed via
investigation.md Current Behavior §7/§8, this is the same vacuous-pass bug
`test_no_mutation_snapshot.py`'s own regression test was built to catch, in the *other* module),
and `capture_snapshot(repo_root)`/`assert_no_diff(pre, post)` take no path-list parameter — they
read the module-level constant internally. This plan does NOT call `capture_snapshot`/
`assert_no_diff` with a substituted path list (they accept none); it reimplements their exact
porcelain-if-clean/content-hash-if-dirty technique locally in `pilot_isolation.py`, mirroring the
same pattern `containment.py`'s own docstring describes for itself ("Reimplements (does not
import — the source lives in a test file, not an importable module)"), parameterized by a path
list sourced from `tools/agent_replay_codex/monitoring_shards.py::source_paths()` (74 lines,
already confirmed correct for the real sharded `agent-monitoring/data/<week>/<source>.jsonl`
layout including the `unknown-week` fallback bucket, per investigation.md Current Behavior §8) plus
`tickets/`. Separately — and unlike the porcelain/hash check — `containment.py`'s
`snapshot_monitoring_lines`/`assert_monitoring_prefix_preserved` wrappers ARE reused as-is
(imported, not reimplemented): confirmed by reading `tools/agent-monitoring/manifest.py`'s
`capture_lines()`/`_source_paths()` directly during Review, these already resolve paths through the
real sharded `data/<week>/<filename>` layout (fixed by a prior ticket,
`TCK-20260904-HOTFIX-MANIFEST-DASHBOARD-SCRATCH-SHAPE-FALLBACK`) — no widening or reimplementation
needed for the append-only-specific check, only for the porcelain/content-hash check.

Concretely, `pilot_isolation.py` provides `run_pilot_isolated(sample_fixtures, run_label) ->
IsolationEvidence`:
1. Before either replay run: snapshot every path from `monitoring_shards.py::source_paths()` plus
   every `.claude/current_run*` sidecar path (both the scoped `.claude/current_run.<SESSION_ID>`
   and unscoped `.claude/current_run`, since `writeSidecar()` in the live orchestrator writes both
   side by side per investigation.md Prior Work — the pilot must prove it never calls that function
   at all).
2. Runs `replay_slice()` over each converted fixture (the sample from Step 2), twice, independently.
3. After each run: re-snapshot the same path set. If ambient concurrent-session writes occurred
   (the common case — this repo is routinely dirty per investigation.md Current Behavior §7), assert
   append-only prefix-preservation (no existing line mutated) via the imported, unmodified
   `containment.py::assert_monitoring_prefix_preserved` (confirmed sharding-aware — see Risk #3
   resolution above), AND assert that none of the newly-appended lines carry the pilot's own
   `run_id` — this is the concrete distinguishing check investigation.md Current Behavior §7 calls
   for ("distinguish 'grew because another concurrent session wrote its own attributed lines' from
   'grew because the pilot's own `replay_slice()` execution wrote something'"). If nothing ambient
   occurred, assert pure zero-diff (porcelain-clean or content-hash-identical) via
   `pilot_isolation.py`'s own local reimplementation of that technique (see Risk #3 resolution
   above — `containment.py`'s `capture_snapshot`/`assert_no_diff` are not called here, since they
   accept no path-list parameter and hardcode the stale 3-file pathspec).
4. Separately asserts the unscoped `.claude/current_run` file's mtime/content is unchanged across
   both runs (static proof the pilot never calls `writeSidecar()`), satisfying AC #4's
   session-scoped-sidecar-exclusivity requirement.

**Other writers to this resource — enumerated (this step is explicitly about a shared-write
surface, per Fact-Verification Requirement #2):**
- `agent-monitoring/data/*/{runs,events,tools}.jsonl` — written by: (1) the 4 forbidden
  `tools/agent-monitoring/{pre_tool_hook,post_tool_hook,record_run,record_events}.py` scripts
  during any live, concurrent `implement-ticket.js` session in this shared repo (per CLAUDE.md's
  Hard Rules, "the repo already runs this way today... several active worktrees on different
  branches at once"); (2) this pilot's OWN Step 1/Step 2 read calls (read-only, no write); (3)
  potentially the pilot's own 2 replay runs if `replay_slice()`'s no-op containment
  (`_fake_write_monitoring`/`_fake_hook_boundary`) were ever bypassed — this is exactly the failure
  mode the isolation evidence in this step must positively rule out, not assume away.
  Interaction: the pilot's isolation evidence must tolerate (1) as legitimate ambient growth
  (prefix-preservation check) while treating (3) as a hard failure (any new line whose `run_id`
  matches the pilot's own is a violation) — ordering between (1) and the pilot's own runs is
  irrelevant since the check is prefix-preservation + run_id exclusion, not exact byte-count
  matching.
- `.claude/current_run` (unscoped) / `.claude/current_run.<SESSION_ID>` (scoped) — written by:
  `writeSidecar()` in the live `.claude/workflows/implement-ticket.js` orchestrator, for any
  concurrent live session (per investigation.md Prior Work, "both `.claude/current_run` unscoped
  and `.claude/current_run.<SESSION_ID>` scoped paths are written side by side by the live
  orchestrator's `writeSidecar()`"). The pilot's own code must never call this function — Step 5's
  evidence proves this by mtime/content-identity assertion on the unscoped path specifically, since
  a concurrent live session legitimately mutates ITS OWN scoped path (a different filename per
  session ID) but should never mutate the shared unscoped path in a way attributable to the pilot.

**Do NOT touch:** `tools/agent_replay_codex/containment.py`'s own `_WATCHED_GIT_PATHSPECS`
constant (read/reused via its exposed functions, not edited in place — widening happens by passing
a different path list sourced from `monitoring_shards.py`, not by patching the constant itself,
which would risk affecting `TCK-20260721-CODEX-REPLAY-PARITY`'s own already-closed, already-tested
consumers of that module); `.claude/workflows/implement-ticket.js`'s `writeSidecar()` (never
imported/called).

**Verify:** test_plan.md tests #9 (`test_isolation_produces_zero_diff_across_agent_monitoring_shards`)
and #10 (`test_isolation_uses_session_scoped_sidecar_path_exclusively`),
`tests/agent_replay/test_pilot_isolation.py`.

---

### Step 6 — Metrics module: 3-tier computation

**Files:** `tools/agent_replay/metrics.py` (new)

**Change:** Build `compute_metrics(run1_results, run2_results, isolation_evidence,
timing_data) -> PilotMetrics` producing concrete values for all 3 tiers, per the frozen spec's
Metrics section (investigation.md Current Behavior §1, lines 79-94):
1. **Primary**: per-defect-class (M2, M3) flag-rate agreement between run1 and run2 — for each
   sampled fixture, did both runs agree on whether M2/M3 fired? Report as a repeatability
   percentage plus the raw per-ticket agreement table. Must NOT compute or claim a false-pass/
   false-block rate for anything beyond M2/M3 (Anti-Drift Hazards, restated in Scope Guards below).
2. **Safety**: pass/fail derived directly from Step 5's `IsolationEvidence` (zero-diff or
   prefix-preserved-with-no-pilot-attributed-new-lines, and unscoped-sidecar-unchanged) — boolean
   plus the supporting evidence artifact reference, not a bare assertion.
3. **Efficiency**: wall-clock duration and tool-call volume for each of the 2 replay runs
   (informative only, explicitly not pass/fail per the frozen spec's own framing).
4. Build a companion `compare_repeatability(run1, run2) -> RepeatabilityResult` function that must
   correctly report non-repeatable when 2 synthetic run results deliberately disagree on one flag —
   this dedicated regression-guard case is required by test_plan.md test #12, mirroring the same
   detects-a-real-discrepancy pattern already used elsewhere in this ticket's test suite (Steps 3/4
   clean-fixture tests, Step 5's mutation-detection guard).

**Other writers to this resource:** `metrics.py` is a new file, pure computation over inputs
already produced by Steps 1-5 in this same pilot execution — no external concurrent writer applies
(it consumes `run1_results`/`run2_results`/`isolation_evidence` as function arguments, not shared
mutable files).

**Do NOT touch:** Nothing outside this new module; do not add a task-success-rate metric for the
retro loop (explicitly Out of Scope, a separate Bucket-C item per the ticket).

**Verify:** test_plan.md tests #11 (`test_metrics_computation_produces_all_3_tiers`) and #12
(`test_metrics_repeatability_comparison_detects_a_real_discrepancy`), `tests/agent_replay/test_metrics.py`.

---

### Step 7 — Execute the pilot: run the sample through Steps 1-6 end to end

**Files:** none new (orchestration only, e.g. a short driver script or notebook-equivalent under
`tools/agent_replay/` such as `run_pilot.py`, OR executed manually by the implementer as a one-off
script not committed — implementer's discretion, since Scope item 8 distinguishes "documenting the
refresh procedure" (in scope) from re-running (out of scope for future refreshes, but this
*initial* run is the ticket's own deliverable, not a "refresh")

**Change:** Using the manifest from Step 1, the fixtures from Step 2, the detectors from Steps 3-4,
the isolation wrapper from Step 5, and the metrics module from Step 6: run the full sample through
`replay_slice()` twice under `run_pilot_isolated()`, apply both detectors to every fixture on both
runs, and call `compute_metrics()` on the combined results. This step's output (the raw per-run,
per-fixture results plus the computed `PilotMetrics`) is the direct input to Step 8's results
report. If a real defect class's flag-rate disagrees between runs, or the isolation evidence shows
a violation, this must be reported honestly as a Kill Criterion trigger in Step 8 — not silently
retried or smoothed into a passing claim (per Gate Integrity and the frozen spec's own "report a
negative finding honestly" clause, restated in the ticket's Scope item 7).

**Other writers to this resource:** None beyond what Step 5 already enumerates for the isolation
window this execution runs inside.

**Do NOT touch:** No production code path; this step only calls the read-only modules built in
Steps 1-6.

**Verify:** Indirectly verified by tests #9/#10 (isolation held during a real execution) and #11/12
(metrics computed from real run output); no new dedicated test — this step's correctness is the
precondition for Step 8's content, not an independently-testable unit.

---

### Step 8 — Results report: append to the frozen spec doc + roadmap.md, and stored_artifacts

**Files:** `stored_artifacts/{ticket_id}/results.md` (new), `docs/plans/agent_infrastructure/ai_first_hardening_epics/agent_evaluation_foundation_experiment.md` (append `## Results` / `## Decision` section), `docs/plans/agent_infrastructure/ai_first_hardening_epics/roadmap.md` (update item 13's status line)

**Change: resolves Risk #4 explicitly, adopting investigation.md's recommendation.** The results
report is NOT placed only in `stored_artifacts/{id}/results.md` — that alone would leave the
frozen spec doc "stranded as not yet run" for any reader who doesn't know to look in
`stored_artifacts/` (investigation.md Risks §4). This plan writes the results in three places:
1. `stored_artifacts/{ticket_id}/results.md` — the full, detailed report: for each of the frozen
   spec's 3 verbatim Exit Criteria (investigation.md Current Behavior §1, lines 96-105), a
   met/not-met statement with concrete evidence; for each of the 2 verbatim Kill Criteria (lines
   107-117), an explicit fired/not-fired statement; the 3-tier metric numbers from Step 6/7's
   output; the freshly re-derived corpus/baseline counts (ticket-done count, tier breakdown,
   artifact-coverage percentage, `runs.jsonl` record count — per AC #6, computed live by Step 1's
   sampler, not copied from investigation.md's own already-stale-by-the-time-of-writing numbers,
   Current Behavior §6's table shows the count moved even within one investigation session); the M2
   vs. M3 known-positive provenance distinction from Step 4 (real-historical vs. synthetic,
   disclosed).
2. `agent_evaluation_foundation_experiment.md` — append a `## Results` / `## Decision` section
   (per the doc's own stated lifecycle, "Frozen Architecture Proposal → ... → Run Experiment →
   Decision," investigation.md Docs Requiring Update) summarizing the same met/not-met and
   fired/not-fired findings, without editing the existing Hypothesis/Baseline/Method/Metrics/Exit/
   Kill Criteria/Out-of-Scope text above it (Out of Scope, restated in Scope Guards below).
3. `roadmap.md` — update item 13's Horizon-1 status line to reflect whether Exit Criteria were met
   (unblocking the Bucket-C dependency notes for items 18-20) or a Kill Criterion fired (keeping
   them blocked) — per investigation.md Docs Requiring Update, "the roadmap is the doc other
   tickets read to know whether items 18-20 are actionable yet."

**Other writers to this resource — enumerated (both docs are shared, per Fact-Verification
Requirement #2):**
- `agent_evaluation_foundation_experiment.md` and `roadmap.md` are both read/potentially-written by
  `TCK-20260904-AI-FIRST-HARDENING-FOLLOWON-EPIC` (the tracking epic this ticket is enumerated
  under, `tickets/inprogress/`, per the ticket's own Related Tickets section) — that epic ticket is
  `epic` tier and per its own scope only tracks child tickets, so it should not concurrently edit
  item 13's status line itself, but the implementer should re-read both docs immediately before
  appending (not rely on a stale in-memory copy from Investigate time) to avoid clobbering any
  concurrent edit, and should use additive edits (append a new section / update one status line)
  rather than a full-file rewrite, minimizing collision surface if another sibling Bucket-B/C
  ticket under the same epic touches an unrelated part of either doc concurrently.
- No other identified writer for these two docs within this ticket's scope.

**Do NOT touch:** The existing Hypothesis/Baseline/Method/Metrics/Exit Criteria/Kill
Criteria/Out-of-Scope text in `agent_evaluation_foundation_experiment.md` (Out of Scope, explicit);
`bucket_c_future_options.md` items 18-20 (investigation.md Docs Requiring Update: "this ticket's
job is to produce the gating evidence... not to itself unblock or re-scope items 18-20's own doc");
`docs/parity_ledger/*.yaml` (no entry applies, per ticket Out of Scope and investigation.md Parity
Ledger Overlap — confirmed no overlap across all 8 subsystem files).

**Verify:** test_plan.md test #13 (`test_results_report_states_all_3_exit_criteria_and_both_kill_criteria`),
`tests/agent_replay/test_results_report.py`.

---

### Step 9 — Refresh procedure: document only, do not execute

**Files:** `docs/ai/replay_pilot_refresh_procedure.md` (new, short) or a `## Refresh Procedure` section appended to `stored_artifacts/{ticket_id}/results.md`

**Change:** Write a short script + instructions describing how to add newer closed tickets to the
eligible sampling pool later (re-run `sampler.py` against an updated `tickets/done/` snapshot,
re-run `fixture_converter.py` on any newly-eligible tickets, etc.). Per Scope item 8 and Anti-Drift
Hazards, this step produces documentation/tooling instructions ONLY — it must NOT actually execute
a refreshed pilot run as part of this ticket.

**Other writers to this resource:** None — new file/section, no other writer.

**Do NOT touch:** Do not re-run the sampler against a live/refreshed pool as part of closing this
ticket; the manifest and results from Step 1/Step 8 remain the ticket's actual deliverable.

**Verify:** No dedicated automated test (this is documentation) — covered qualitatively by Scope
item 8's requirement; the done-checker's doc-coverage check (M2, per Step 3) will itself verify
this new doc file, if created, is referenced in the ticket's own `## Files Changed`.

## Scope Guards

Restated from the ticket's Out of Scope section and investigation.md's Anti-Drift Hazards — the
implementer must not:

- Rewrite, re-derive, or second-guess the Hypothesis/Baseline/Method/
Metrics/Exit Criteria/Kill Criteria text in `agent_evaluation_foundation_experiment.md` (only
append a Results/Decision section, per Step 8).
- Widen the sample beyond 20-40 tickets, or build a general eval platform, before this pilot's own
  exit criteria are met (Step 1's sampler must hard-bound to the 20-40 range).
- Derive a task-success-rate metric for the retro loop (Step 6's metrics module computes exactly
  the 3 named tiers, nothing else).
- Change `implement-ticket.js`'s production behavior in any way — the replay calls the same real,
  already-tested imported functions read-only, in isolation (Steps 3-5); it never modifies the
  orchestrator, and never live-re-dispatches real `implement-ticket.js` agents against real
  tickets (the 2 runs in Step 7 are 2 static-fixture replay executions, not 2 fresh live ticket
  implementations).
- Do any live Codex provider comparison work or model-based routing decisions.
- Update `docs/parity_ledger/` entries (none apply; confirmed by investigation.md's Parity Ledger
  Overlap section).
- Modify `replay_slice()`'s 4 existing branch points (Scope conflicts/tags, Plan unresolved-
  questions, Review verdict) — Steps 3-5 only add new, separate functions alongside it.
- Import or subprocess any of the 4 forbidden `tools/agent-monitoring/{pre_tool_hook,
  post_tool_hook,record_run,record_events}.py` scripts anywhere in new code (Steps 1, 3, 4, 5) —
  use `monitoring_shards.py`'s helpers or plain file I/O only. `test_runner_no_forbidden_calls.py`
  must be extended to scan every new module this ticket adds (Steps 1-6), not just `runner.py`.
- Turn Step 9's "document a refresh procedure" into actually re-running a refreshed pilot.
- Claim a "false-pass"/"false-block" rate for anything beyond the 2 named defect classes (M2, M3)
  anywhere in Step 6's metrics or Step 8's results report.
- Edit `done_checker_static.py` or `subagent_stop_background_guard.py` (the live M2/M3 fixes) —
  Steps 3-4 build separate, new logic that models their signals, never imports or modifies them.
- Edit `containment.py`'s `_WATCHED_GIT_PATHSPECS` constant in place (Step 5 sources a widened path
  list from `monitoring_shards.py::source_paths()` instead, passed as a parameter).
- Edit `bucket_c_future_options.md` (Step 8 produces gating evidence in the 2 other docs; items
  18-20's own doc is not touched).

## Dependency Map

- Step 1 (sampler) — independent, no dependency.
- Step 2 (fixture converter) — depends on Step 1's manifest (needs the list of sampled ticket IDs)
  but can be developed/unit-tested against any single ticket independently of a completed
  manifest.
- Step 3 (M2 detector) — independent of Steps 1/2 for its own unit tests (uses named known-positive
  tickets directly), but consumes Step 2's converter output when applied to the full sample in
  Step 7.
- Step 4 (M3 detector) — fully independent (synthetic fixture, no dependency on Steps 1/2).
- Step 5 (isolation) — independent for its own unit tests (wraps `replay_slice()` directly); used
  in Step 7 to wrap the full-sample execution.
- Step 6 (metrics) — independent for its own unit tests (synthetic run-result inputs); consumes
  Steps 3/4/5's real output only in Step 7.
- Step 7 (execute) — depends on Steps 1-6 all being complete; this is the integration point.
- Step 8 (results report) — depends on Step 7's output.
- Step 9 (refresh procedure doc) — independent, can be written any time after Step 1 (describes
  Step 1's sampler being re-run later).

Steps 1-6 can be implemented and unit-tested in any order or in parallel; Steps 7-9 are strictly
sequential after Steps 1-6.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC #1 — durable sample manifest, 20-40 tickets, strata + split | Step 1 | test #1, #2 |
| AC #2 — every sampled ticket has a fixture or logged exclusion reason | Step 2 | test #3, #4 |
| AC #3 — extended replay layer detects both M2 and M3 with passing unit tests on ≥1 known-positive each | Steps 3, 4 | test #5, #6, #7, #8 |
| AC #4 — full sample replayed twice, isolated worktree, session-scoped sidecar exclusively, logged no-contamination evidence | Step 5 (mechanism), Step 7 (execution) | test #9, #10 |
| AC #5 — results report states met/not-met for 3 Exit Criteria + fired/not-fired for 2 Kill Criteria | Step 8 | test #13 |
| AC #6 — results report has concrete numbers for all 3 metric tiers + freshly-measured corpus/baseline counts (not the stale spec-doc figures) | Step 6 (metrics), Step 1 (live-derived counts), Step 8 (report content) | test #11, #12, #13 |

## Review Round 1 (NEEDS_CHANGES, resolved)

The architecture-reviewer found: Step 5's original wording claimed `pilot_isolation.py` would call
`containment.py`'s `capture_snapshot(repo_root)`/`assert_no_diff(pre, post)` "against that widened
path list" — but those functions accept no path-list parameter; they read the module-level
`_WATCHED_GIT_PATHSPECS` constant internally. Verified directly against
`tools/agent_replay_codex/containment.py` (lines 24-29, 63-67, 69-86): confirmed correct. Verified
further against `tools/agent-monitoring/manifest.py` (lines 62-76, 103-117): `_source_paths()` is
already sharding-aware (fixed by `TCK-20260904-HOTFIX-MANIFEST-DASHBOARD-SCRATCH-SHAPE-FALLBACK`),
so the manifest-wrapped append-only check (`snapshot_monitoring_lines`/
`assert_monitoring_prefix_preserved`) needs no changes and stays an as-is import; only the
git-porcelain/content-hash check needed correcting, to a local reimplementation rather than a
parameterized call. Step 5 and the Risk #3 Anti-Drift Note above are corrected accordingly. All
other findings from Review Round 1 (forbidden-import avoidance, non-modification of the 4 shipped
modules, AC-to-step-to-test mapping) checked out clean with no changes required.

## Anti-Drift Notes

- **Risk #1 (M3 known-positive provenance) is resolved as investigation.md's option (c):** the M3
  known-positive fixture is explicitly synthetic and must be labeled as such everywhere it is
  referenced (test name, fixture header comment, Step 8's results report) — never presented as
  equivalent to M2's real-historical known-positive instances. This is a disclosure requirement,
  not a implementation blocker.
- **Risk #2 (isolated worktree) is resolved as investigation.md's option (b):** no literal `git
  worktree add` is created; the pilot reuses `replay_slice()`'s already-proven zero-write property
  plus a widened snapshot-diff check. Step 8's results report must say so explicitly, so a future
  reader does not conclude Method step 3 was skipped.
- **Risk #3 (stale `_WATCHED_GIT_PATHSPECS`)** is resolved by `pilot_isolation.py` locally
  reimplementing the porcelain/content-hash zero-diff technique (mirroring
  `test_no_mutation_snapshot.py`'s own pattern, the same way `containment.py` itself does),
  parameterized by a watch-set sourced from `monitoring_shards.py::source_paths()` plus `tickets/`
  — NOT by calling `containment.py`'s `capture_snapshot`/`assert_no_diff` with a substituted path
  list, since those functions accept no such parameter and hardcode the stale 3-file list
  internally (corrected during Review Round 1 — see below). The append-only-specific check
  (`snapshot_monitoring_lines`/`assert_monitoring_prefix_preserved`) IS reused as-is via import,
  since `manifest.py::_source_paths()` is already sharding-aware. Either way, this must actually
  watch the real `agent-monitoring/data/<week>/*.jsonl` shard layout, or the isolation evidence is
  vacuous (the same failure class `test_no_mutation_snapshot.py`'s own regression test was built to
  catch, per investigation.md and test_plan.md's Anti-Drift Test Guards). Test #9 must specifically
  prove the watch set detects a deliberate mutation, not merely assert an untested "no diff" result.
- **Risk #4 (results-report location)** is resolved by writing to all three of
  `stored_artifacts/{id}/results.md`, `agent_evaluation_foundation_experiment.md` (append-only
  Results/Decision section), and `roadmap.md` (status line update) — not `stored_artifacts/` alone.
- **Risk #5 (bulk-converted fixture fidelity)** is resolved by Step 2's `conversion_log.yaml`
  recording `review_output_fidelity` per fixture — any fixture whose `Review.output` was
  reconstructed from a truncated `events.jsonl` summary (200-char cap) is marked as such, not
  silently treated as equivalent to a verbatim-recorded verdict.
- **Numbers must be re-derived live, never hardcoded from investigation.md.** Current Behavior §6's
  own table shows the corpus count moved even within a single investigation session (1,849 →
  1,852) — Step 1's sampler and Step 8's results report must compute counts at run time.
- **The M2/M3 detectors are new, separate logic — not live imports of the production gate/hook
  modules** (`done_checker_static.py`, `subagent_stop_background_guard.py`). This keeps the
  replay's read-only/imported-function containment intact (only the 4 pre-existing branch-point
  functions in `runner.py` are live imports; M2/M3 detection is reimplemented against historical
  input shapes) and avoids accidentally coupling pilot code to production gate internals in a way
  that could break if those modules change independently later.

## Deviations (found during Implement)

1. **`_closing_commit_docs_paths` initial implementation was wrong, caught and fixed before Step
   8's results.md was finalized.** The first working version resolved a ticket's "closing commit"
   via `git log --follow --diff-filter=A -- tickets/done/{id}.md` (the commit that first added the
   file). For tickets closed inside a large batch/PR-merge commit, this incorrectly resolved to an
   unrelated giant merge commit (e.g. `6e25d4f2`, "Engine audit documentation, simulation quality
   (in-progress)..." for `TCK-20260702-SIMQ-UPLIFT-GRADE-DECAY`), producing a spurious 5/5 M2
   fire rate across the pilot's first live sample run — hundreds of unrelated `docs/` paths from
   the wrong commit, none of them genuinely gap-relevant. Root-caused and fixed by replacing it
   with `_build_ticket_commit_index()`, which finds the commit whose subject follows this
   project's own Commit Convention (`TCK-YYYYMMDD-SHORT-SCOPE: ...`, read before the first colon)
   — the real, dedicated per-ticket closing commit where one exists. A second, related bug was
   found in the same fix pass: the initial `git log` scan used the current worktree branch's own
   history only, which stops after ~197 commits and omits real per-ticket commits (confirmed:
   commit `aa72872a`, `TCK-20260702-SIMQ-UPLIFT-GRADE-DECAY`'s real closing commit, exists in the
   repo but is absent from `git log` without `--all` on this branch) — fixed by scanning `--all`
   refs. After both fixes, the pilot's real sample run correctly resolves closing commits for all
   5 converted fixtures and M2 fires 0/5 (verified by hand against one ticket's real `git show`
   output vs. its real `## Files Changed` text — genuinely no gap, not a detector defect). Neither
   fix touches `defect_detectors.py`'s own M2 comparison logic (already correct per its unit
   tests, Steps 3's own known-positive/clean fixtures) — both fixes are local to
   `run_pilot.py`'s git-history-resolution helpers.
2. **A significant, disclosed fraction of the sampled+converted tickets have no isolable
   per-ticket closing commit at all** (closed only inside a multi-ticket batch/epic-merge commit
   whose subject carries no ticket id) — `_build_ticket_commit_index()` deliberately returns no
   match for these rather than guessing, and `run_pilot.py` records them separately
   (`m2_no_isolable_commit_tickets`) so M2's live sample application is never silently conflated
   with "confirmed clean." This is disclosed explicitly in `results.md`'s Exit Criterion 2
   evidence — not anticipated in this plan's original text, which assumed a single-commit-per-
   ticket model throughout (matching the 3 named known-positive tickets, which do each have a
   dedicated commit).
3. **`test_results_report.py`'s vocabulary-marker assertion was corrected during Implement.** The
   test as first written asserted the literal strings "met", "not met", "fired", "not fired" all
   appear somewhere in `results.md`. Since this pilot's real run found all 3 Exit Criteria MET and
   neither Kill Criterion FIRED, the string "not met" never legitimately appears — and the plan's
   own Gate Integrity rule forbids writing report text designed merely to satisfy a test's
   vocabulary rather than reporting the real outcome. Corrected to check, per criterion, that the
   verbatim criterion text is immediately followed by a MET/NOT MET (or FIRED/NOT FIRED) label —
   "NOT MET" contains "MET" and "NOT FIRED" contains "FIRED", so the assertion is agnostic to
   which way each criterion actually resolved, matching test_plan.md test #13's own stated scope
   ("a structural completeness check... not a check on which way they resolved").
