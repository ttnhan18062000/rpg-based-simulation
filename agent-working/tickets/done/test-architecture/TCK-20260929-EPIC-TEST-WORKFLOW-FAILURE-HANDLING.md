---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260929-EPIC-TEST-WORKFLOW-FAILURE-HANDLING
phase: done
date: 2026-09-29
tags: [testing]
---

# TCK-20260929-EPIC-TEST-WORKFLOW-FAILURE-HANDLING

## Title
Epic C — Test workflow and failure handling: test-plan fields, an advisory test-quality checklist, and one failure-triage procedure

## Status
DONE

## Tier
epic

## Type
feature

## Priority
P2

## Request Summary

In `implement-ticket`:
- only the test *level* is decided in `test_plan.md`;
- the implementer writes both code and tests;
- no phase reviews test quality;
- the installed test skills are never invoked.

Failure handling is also split across three sources:
- `docs/testing/regression_policy.md` §4–7;
- the CI Failure Triage section of `docs/guides/delivery_process.md`;
- CLAUDE.md's gate-integrity rule.

`regression_policy.md` §6 allows unbounded `xfail(strict=False)` for flaky tests.

Roadmap: `docs/plans/test_architecture/roadmap.md` §2–3.

## Scope

**Decision record (2026-09-30).** D-M2 and D-MF are approved with changes (roadmap §11); both HOLDs are lifted. Approval does not close this epic. Status 2026-10-01: criterion 1 met with a caveat, criterion 2 not met (partially demonstrated), criterion 4 open, criterion 5 met (text only).

1. **Test-plan fields** (existing `investigator`):
   - mandatory: proof kind, oracle source (Bible/contract section + parity-ledger id), expected
     effect, selected commands;
   - optional: negative cases, fixtures, non-functional risk.
2. **Advisory test-quality checklist** in the existing `architecture-reviewer` at
   Architecture-Verify, diff-scoped. A clean review is a valid outcome.
3. **Epic coordination note** for `implement-epic` children: shared fixtures and patterns recorded
   at the epic level.
4. **Unified failure-triage procedure** in `docs/testing/regression_policy.md`, with the other
   sources linking to it:
   - an evidence record (reproduction command, seed/world/config, SHA, run ids, expected vs
     observed, rerun result);
   - failure classes, each with a role, an immediate action and a closure condition;
   - the prohibitions of roadmap §2.5;
   - defects found by tests handed to the feature team.
5. **Oracle-review step** (D-M2 approved with changes; text only in the 2026-09-30 batch): when an acceptance criterion adds or
   changes an expectation, the Bible/contract and parity ledger change first. Silence, missing
   ownership, disputes and intra-Bible conflicts escalate to the user. Advisory during the pilot; it never authorizes an agent to change an expectation. An expected value no document states (a balance or emergent threshold) stays an exploratory measurement, not a proof, until the owner or feature team approves a derivation. **This batch records the rule in `regression_policy.md` §13.5 and the roadmap only. Wiring it into an agent file (for example the `architecture-reviewer` checklist) is NOT done and stays open**; it needs agent-working-design's agreement.
6. **Bounded-quarantine policy text** (D-MF approved with changes; policy text landed 2026-09-30): replaces §6's unbounded rule. Nondeterminism only; node-level strict xfail; owner, ticket, expiry of at most 14 days, one 14-day renewal that keeps the original start date (28 days maximum); a recorded failure signature. **No quarantine is applied until a minimal expiry check exists.** **Enforcement tooling is deferred until a real case needs quarantine.** Existing failures stay visible.

## Out of Scope

- A new workflow phase or a dedicated test-writing agent. That is a later option, triggered only by
  shortcomings the pilot observes.
- Review-record storage or validator (deferred to its trigger); no new proof-status record.
- Quarantine tooling (deferred).
- Changing Bible/contract content (feature teams and the user).

## Acceptance Criteria

1. **MET (2026-10-01), with a caveat.** (Earlier status, 2026-09-30: not met, because the `done-checker` check did not exist.) On at least 2 tickets (real, or clearly labelled synthetic), the mandatory `test_plan.md` fields
   are present and `done-checker` checks their presence. The fields were present in the pilot, but the `done-checker` check was
   removed from PR #265 as a contested area and does not exist. agent-working-design agreed (2026-09-30) to an **advisory WARN** (never
   blocking), owned and built by agent-working (`agent-working-implementer`, its next batch); they will report the PR number. This criterion
   stays not met until that PR merges. A blocking variant is not to be built here; a request for one goes back to agent-working-design.
   **Update 2026-10-01:** that PR (#268, `TCK-20260930-DONE-CHECKER-PROOF-PLAN-ADVISORY`) merged. The advisory ran inside a real `implement-ticket` run at Verify on `TCK-20260930-CONSERVATION-REJECTION-PATH-ASSERTION-GAP` and reported OK (fields written by the real investigator), and the same check run afterwards by hand on pilot D1's stored `test_plan.md` also reported OK. Caveat: D1 was checked after the fact with the same script, not inside a pipeline.
2. **NOT MET; partially demonstrated (2026-10-01).** The checklist runs on changed tests. Each substantive finding is acted on, or declined with a
   reason. **Update 2026-10-01:** in the real pipeline run on `TCK-20260930-CONSERVATION-REJECTION-PATH-ASSERTION-GAP` the checklist ran at Architecture-Verify on the two changed test files and found nothing, **but only because the orchestrator added a prompt sentence asking about it** (the workflow script does not contain it). The checklist is wired into `.claude/agents/architecture-reviewer.md`, so it should run unprompted; this run shows only that it runs when asked, and a clean diff shows nothing about detection. The criterion closes on the first later pipeline run that changes tests with the orchestrator prompt unmodified. **Update 2026-10-02 (`TCK-20260914-BOSS-KINDS-OBSERVABILITY-CONSTANT-DRIFT`; standard tier chosen by test-architecture to reach Architecture-Verify; orchestrator prompt text taken verbatim from `implement-ticket.js`, plus one output-format sentence appended by the hand-orchestrator to every agent prompt ("Return your answer as a single JSON object with keys: ...", listing the schema's keys), because the skill path does not enforce the schema; no checklist sentence was added): NOT MET; partially demonstrated.** **Correction recorded 2026-10-02:** an earlier version of this entry said the prompts were unmodified; that was inaccurate, as just stated. The appended key list for Architecture-Verify named verdict, violations, summary, verified_by and ts, mirroring `ARCH_VERIFY_SCHEMA`, which has no `test_quality_findings` field, so it may itself have steered the remark into `notes`; that is untested, and it weakens the "unprompted" reading of this run. Unprompted invocation observed: the production architecture-reviewer emitted a test-quality remark without a prompt sentence. Application to changed tests NOT demonstrated: the reviewer stated "test files were not read in depth", and returned the remark inside `notes` rather than the `test_quality_findings` list prescribed by `.claude/agents/architecture-reviewer.md`. The advisory shadow reviewer (not read by the gate) read the tests and returned a structured list with one advisory finding, declined as no action required. It is recorded separately and does not count toward this criterion. Sample size 1. Verbatim records: `agent-working/stored_artifacts/TCK-20260914-BOSS-KINDS-OBSERVABILITY-CONSTANT-DRIFT/architecture_verify_production_verbatim.jsonl` and `.../architecture_verify_shadow_verbatim.jsonl`. The `ARCH_VERIFY_SCHEMA` in `.claude/workflows/implement-ticket.js` has no `test_quality_findings` field (verdict, violations, summary, ts, verified_by only) and the Architecture-Verify prompt does not ask for one, so the `notes` placement is a schema gap, not necessarily reviewer behaviour; "not read in depth" is a separate item. Both routed to agent-working-design as a test-architecture finding, with no fix proposed here.

   **Protocol for the next run (recorded 2026-10-02, after the schema field landed in PR #282, merge commit `af14da4e1`; reviewer-approved).**
   - **"Unmodified" means:** no checklist-specific sentence anywhere in any agent prompt. Any output-format text on the hand-executed skill path is generated mechanically from the schema key list by `python3 tools/agent-monitoring/schema_format_tail.py --schema ARCH_VERIFY_SCHEMA`, appended verbatim, and recorded verbatim in the run's evidence. On the native Workflow path the schema is enforced by the runtime and no format text is appended. "Run in foreground" notes are allowed and recorded. Every addition to a prompt is listed; nothing is called "unmodified" without that list.
   - **The run's pre-dispatch sidecar must be written** (`writeSidecar` shape) before the Architecture-Verify dispatch. Attribution in `tools/agent-monitoring/arch_verify_read_check.py` depends on it; without it every Read row has a null `run_id` and the checker can only report UNATTRIBUTED.
   - **MET only if** (a) the production reviewer returns the `test_quality_findings` list (empty is fine), AND (b) the reviewer's own output shows it read the changed test files (it names or quotes them, or engages with their assertions), AND (c) every substantive finding is acted on or declined with a reason in the ticket. A list alongside "test files were not read" does NOT meet it. A clean empty list with no sign of having read the tests does NOT meet it.
   - **The checker's class is corroboration only, never the deciding signal.** Run `python3 tools/agent-monitoring/arch_verify_read_check.py --ticket-id <TCK-ID>` and record its READ / POSSIBLY-READ / NOT-READ / UNATTRIBUTED class per changed test file next to the reviewer's output. A Read row shows a file was opened, not that it was reviewed, and a Bash `cat`/`grep` read leaves no Read row (so NOT-READ is "no Read-tool row", not "never looked at"); the hook cuts a Read's path at 120 characters (36% of Read rows on 2026-10-02), so a cut row is at most POSSIBLY-READ.
   - **A rerun needs** a test-changing ticket (not one whose edits touch `implement-ticket.js` or the reviewer agent itself, which would edit the instrument being measured) and the user's go-ahead to launch. Cost is reported observationally: the final pass separate from the total, orchestrator context excluded (run 1: final 742,229 / first pass 176,589 / total 918,818 subagent tokens).

   **Run 2: BLOCKED on an available test-changing ticket (2026-10-02).** Searched on 2026-10-02: RPG todos are parked by owner decision 7 (`docs/plans/systemic_world/owner_decision_memo.md` row 7; balance, dormant-path and feature work), and rpg-feature-planning declined to carve a ticket out of the foundation epic or out of work-order items 1-4 for the pilot. `search_docs` was down (MCP server failed to connect), so the non-RPG scan was by layer frontmatter and ticket text, not semantic search. Judged, with the one-line reason each failed:
   - `TCK-20260914-BOSS-KINDS-OBSERVABILITY-CONSTANT-DRIFT`: already done and merged in #278; it was run 1 and has no test change left.
   - `TCK-20260914-CALAMITY-RANDOM-CHANCE-UNUSED-CONSTANT`: wiring a dormant constant is parked by decision 7; deleting it changes no test.
   - `TCK-20260908-RAID-SIZE-FORMULA-DOC-CODE-MISMATCH`: needs a balance decision; parked by decision 7.
   - `TCK-20260822-STANDARD-SLOW-REGRESSION-CI-JOB-EXIT-CODE-2`: BLOCKED by user decision 2026-09-16 until the engine re-architecture lands; a CI job, not tests.
   - `TCK-20260929-PROFILE-API-PAYLOAD-DEAD-API-REFS`: hotfix tier, which has no Architecture-Verify phase, and its scope names no test files.
   - `TCK-20260930-SAME-NAME-DIVERGENT-CLASS-PAIRS`: touches `src/` mechanism classes and the registry (rpg-feature-planning's surface), and is large.
   - `TCK-20260914-PERF-THRESHOLD-SOFT-GATE-DEFECT`: declined by the reviewer. Its first deliverable is a migration plan that may change no tests, and hardening call sites would turn green-but-breaching tests red and force a recalibration outside its scope, which would tangle the measurement with an expectation change nobody owns.
   - **Judged from sibling/title, not read in full:** `TCK-20260914-DECISION-TRACE-WRITE-COST-OBSERVED`, `TCK-20260914-COOPERATION-FIND-PENDING-OFFER-COST-OBSERVED`, `TCK-20260914-STATE-FINGERPRINT-COST-OBSERVED` (report-only cost observations), `TCK-20261001-SIMQ-UNIT-SELFMODEL-PILOT-ECONOMY-ANCHOR-REBASELINE` and `TCK-20261001-FRONTIER-MARCHES-NARRATIVE-ANCHOR-ZERO-SCORE-REBASELINE` (SimQ rebaselines, balance-adjacent, probably inside decision 7's parked set).
   - **Known possible future sources, undated, not commitments; relayed from rpg-feature-planning 2026-10-02:** `TCK-20260919-RAW-LEGACY-FACTION-ENUM-HOSTILITY-SWEEP` (work-order item 2; planned but deliberately NOT dispatched by the owner's decision of 2026-10-02, held until item 1 `TCK-20261002-GOAL-WINNER-CONSUMPTION-DISCARDS-DECIDED-OBJECTIVE-KIND` lands on main, because item 1 creates the shared hostility helper its call sites consume; a hard bug with many changed tests, so the pilot would ride the sweep and not shape it, and using it is the user's call) and `TCK-20261002-EPIC-SEMANTIC-FOUNDATION-COMPLETION` child B (expectation-first, so it may also exercise criterion 4; not started).
   - **Re-opens when:** the next test-changing ticket outside decision 7's parked set, from any owner, appears; it re-enters through the protocol above.

   **Run 2 (2026-10-04, `TCK-20260919-RAW-LEGACY-FACTION-ENUM-HOSTILITY-SWEEP`, standard tier; judged by `test-architecture-reviewer`): NOT MET.** The user approved this run as the rerun on 2026-10-04, after #291 merged (`f4146ddbbf6ebe923453d0ec3b07481510ac2f08`); it was dispatched by `rpg-implementer`.
   - **Path:** hand-executed skill path, execution_id `claude-TCK-20260919-RAW-LEGACY-FACTION-ENUM-HOSTILITY-SWEEP-1791116151380-59afb654`. Two native attempts came first and are not counted:
     - `watti6za3` was rejected at launch for missing `start_ts` / `execution_id_suffix`;
     - `wf_ca51b3b4-356` died after Scope with `ReferenceError: bash is not defined`. The native gate sites are unported (implement-ticket-native-port items 4-5, deferred 2026-10-01). The reviewer's protocol message had wrongly called the native path "preferred"; that is corrected, and agent-working-design ticketed a zero-token refusal for this case.
   - **Prompt additions at Architecture-Verify (complete list, as reported by the dispatcher):**
     1. the schema tail from `schema_format_tail.py --schema ARCH_VERIFY_SCHEMA`, verbatim: "Return your answer as a single JSON object with keys: verdict, violations, summary, ts, verified_by, test_quality_findings.";
     2. the implementer's file list, as the files-changed line.

     No checklist-specific sentence and no foreground note.
   - **Other deviations (other phases):** Investigate and Plan were skipped because the planning session's artifacts already existed; the Review prompt's plan summary was replaced by a pointer to plan.md; the Implement and Document-Update prompts got appended operating constraints (no commit/push, no edits to the instrument, foreground only). The sidecar was hand-written before Architecture-Verify (seq 8).
   - **Against the MET conditions:**
     - (a) met: the production reviewer returned `test_quality_findings: []` (verdict APPROVED);
     - (b) NOT met: nothing in the returned output shows the changed test file `tests/unit/combat/test_catalog_hostility_sweep.py` was read, and the reviewer's own full reply says verbatim: "I did not read `tests/unit/combat/test_catalog_hostility_sweep.py`, so `test_quality_findings` is empty by omission rather than by review." "A clean empty list with no sign of having read the tests does NOT meet it";
     - (c) not applicable (no findings).
   - **Corroboration (never the deciding signal):** the run's tools shard in its worktree holds 7 rows attributed to Architecture-Verify (3 Bash, 1 Write, 1 Agent, 1 SubagentHandback, 1 SendMessage), 0 Read rows, and no row naming the test file. `arch_verify_read_check.py` reported 0 attributed Read rows and "the branch changes no file under tests/": the test file was still untracked when it ran, and the checker sees only the committed branch diff. That checker limit was routed to agent-working-design.
   - **Pattern across runs:** run 1 (`TCK-20260914-BOSS-KINDS-OBSERVABILITY-CONSTANT-DRIFT`) also said "test files were not read in depth". Two of two production Architecture-Verify passes did not read the changed tests. Reported to agent-working-design as a finding about the reviewer prompt or the phase, with no fix proposed here.
   - **Not affected:** the open nondeterminism ticket `TCK-20261003-COMBAT-TACTICAL-PATH-NONDETERMINISM-SURVIVES-AUDIT-MODE` lies on this code path, but criteria 2 and 4 use no simulation counts.
   - **Criterion 4:** not exercised; the dispatcher reports no hash-pinned fixture or expectation moved.
   - **Evidence:** the verbatim output landed with the sweep's own PR (#333, `898c6f35aeeeb269a60eab68aeb9f24f0e960b0d`), at `agent-working/stored_artifacts/TCK-20260919-RAW-LEGACY-FACTION-ENUM-HOSTILITY-SWEEP/architecture_verify_output.jsonl` (the schema JSON) and `.../architecture_verify_full_reply.jsonl` (the full reply, including the sentence quoted above).
   - **Criterion 2 stays NOT DEMONSTRATED.** It re-opens at the next eligible test-changing run through the protocol above.
   - **Instrument change before run 3:** `TCK-20261004-ARCH-VERIFY-TESTS-READ-EVIDENCE` merged in #332 (`ad194bec41e5f452a0f44a46ce4cc3c5fd5e9639`). It adds an optional `tests_read` field, an advisory "unverified" flag and one line to the reviewer prompt, and lets `arch_verify_read_check.py` see uncommitted test files. Run 3 is the first eligible test-changing run after that merge, never that ticket's own run. The prompt line is an instrument change and must be listed among the prompt additions. `tests_read` meets condition (b) only when the tools shard or the read-check corroborates it. On the hand-executed skill path, `tests_read` comes from the prompt only, not the schema (the ticket's open question), so run 3 must record whether the reply carried it.
3. The triage procedure is one document, and the other sources link to it. A drill classifies at
   least one real case (the Epic A leak) and one synthetic case, and routes each to the right role.
4. **Exercised three times: #385 and #398 MET-with-caveat (document-and-ledger route); #422 MET-clean (escalation-record route). The document-and-ledger route has not yet been shown clean.** A ticket that changes an expectation shows the document and ledger change before
   the test change, or an escalation record. **Update 2026-10-02: not exercised** on `TCK-20260914-BOSS-KINDS-OBSERVABILITY-CONSTANT-DRIFT` (no fixture, hash, baseline or scorer moved).

   **Exercised 2026-10-06 (#385, `TCK-20261006-HELD-ATTACK-TASK-AGAINST-AN-OUT-OF-RANGE-TARGET-IS-NEVER-RE-DECIDED`, Lane A; merged as `bbaaf20347b6a16fdd1fbb1b524b6537d1f7c2ea`, final head `9147f5a15f95deb161386cd80cda403246a62f9a`; judged by `test-architecture-reviewer`, PR comments 6018288876 and 6018849999): MET, with a caveat.** It is the first expectation change observed since this epic closed. Two tests changed their expectation under one rule change (an `ATTACK` that returns `OUT_OF_RANGE` now ends its task instead of being kept):
   - `tests/unit/actions/test_action_routing_task_reset.py::test_attack_out_of_range_does_not_reset_task` was **reversed** to `test_attack_out_of_range_resets_task_to_idle`. It had pinned the defect (a kept payload is never re-decided; 267 swings measured in one run). Its docstring cites the ticket and the mechanism. Disabling control: with `OUT_OF_RANGE` removed from `_ENDS_HELD_ATTACK_REASONS`, 6 tests fail.
   - `tests/unit/core/test_partial_rejection.py::test_partial_rejection_occupancy_vs_combat` **moved its observation point**, from the kept task's `FAILURE`/`OUT_OF_RANGE` annotation to the audit trail (`rejections_delta`, one `rejection_event` with reason `OUT_OF_RANGE` and action kind `ATTACK`), and asserts that the task ended. Its intent (the move proceeds; the combat is rejected for range, not faction) is preserved and slightly strengthened. CI found it, not the plan: the first local sweep left out `tests/unit/core`. That is a test-plan scoping gap (criterion 1's "selected commands"), not a criterion-4 failure.
   - **Authority first:** world rule MOV-07 (orthogonal melee adjacency) landed on `main` in #382 (`82b07b9e483134da3829d0d4130454e74cdcaeb5`) before the change. **Document and ledger:** `docs/mechanics/02_combat_laws.md` drops the exact sentence the old test pinned ("`OUT_OF_RANGE` … deliberately not reset") and states the new rule with its measured reason; `docs/parity_ledger/combat_movement.yaml` adds `COMB-333` (verified, with v2 evidence and a support boundary); `intentional_divergences.md` §2.74, `tactical_contract.md` and `kernel.md` follow.
   - **Caveat:** the document and ledger change ship in the same commit as the test changes rather than strictly before them. The rule's own authority change (MOV-07) did come first. Under criterion 4's wording ("shows the document and ledger change before the test change"), this is MET-with-caveat, not MET-clean. A future expectation-first ticket that lands the ledger entry in an earlier commit would make it clean.
   **Exercised a second time 2026-10-07 (#398, `TCK-20261007-SAFETY-DISPOSITION-TRIGGERS-RETREAT-ON-SIGHT-AGENCY-07` with `TCK-20261006-CAMPAIGN-EPISODE-COOPERATION-SHARE-ABOVE-HALF-UNDER-A-PINNED-NORMAL-GOVERNOR`; merged as `d9fc65e8c2902a2c54c93bdeeda8ea173f172239`, final head `33fc1dad10b8b30c805609d36f728869d4e3a7fa`; judged by `test-architecture-reviewer`): MET, with the same caveat as #385, and an accepted weakening.** One expectation changed:
   - `tests/integration/campaigns/test_catalog_entity_spawn_wiring.py::test_real_campaign_episode_event_mix_is_not_dominated_by_cooperation` lost its strict `xfail` and was **reformulated** from seed 42 alone to the cooperation share pooled over seeds {42, 1337}, still `< 0.5`, with the per-seed shares in the failure message. Seed 42 alone sat at 0.4962 under AGENCY-07, a margin too thin to assert.
   - **Authority first:** owner delegation row 21 (a cautious disposition lowers the bar for flight but never decides it alone; AGENCY-07) landed on `main` in #392 (`c1c2acdb23a89bd78cdaa0d600c3ca554f6ae6fc`) before the change. **Document and ledger:** `docs/parity_ledger/combat_movement.yaml` adds `COMB-335` (verified, `test_path` the new `tests/unit/engine/test_safety_retreat_needs_present_threat.py`); `intentional_divergences.md` §2.76 and `tactical_contract.md` follow. The reformulation and its weakening are written into the closed COOPERATION-SHARE ticket.
   - **Weakening, accepted:** the pooled form also passes on the pre-AGENCY-07 tree (pooled 0.4960, while seed 42 alone was 0.5271). Accepted because the test guards the ~79% co-location artefact, not the 0.50–0.53 band.
   - **Caveat:** the document and ledger change ship in the same commit as the test change (`d23e578d160e80de481faad53b7ee5b5897566e8`); the behaviour change and its own test came one commit earlier (`8c956880eac27eb6a7c1a21065a569933cd7f8e7`). As with #385, the authority came first, so this is MET-with-caveat, not MET-clean.
   **Exercised a third time 2026-10-08 (#422, `TCK-20261007-SPECIES-HOSTILITY-METAMORPHIC-ENGAGEMENT-CHECK-RED-SINCE-6E7EF56EC`; merged as `10944422c0de07c792f38ca8195e213b564e2945`; test commit approved by `testing-planner` before the PR): MET-clean, via the escalation-record route.** One expectation changed its observation setup, not its form:
   - `tests/integration/lab/test_species_relations_metamorphic_validation.py` now measures on a contact-rich layout of the same world content (a test-scoped `load_world` override moves `wolf_den` to (41,30,48,40) and its nest to (44,35)), with the governor pinned to NORMAL by a test-scoped monkeypatch of `src.engine.governor.ResourceGovernor` and fixed seeds 301-310. The assertion keeps its exact form (pooled high >= pooled baseline, no tolerance band). A non-vacuity guard requires at least 2 baseline seeds with contact; two identical runs show it is deterministic.
   - **Escalation record first:** rpg-planner's ruling (a), that the law (CONFLICT-03) is unchanged and is observed faithfully only where the groups meet, is recorded verbatim in the ticket, with the pinned rescope measurements, in `f78c547a648733ae3e60d5dc47c9ea305f3f8fd0` ("No test change yet"). The test change follows in its own later commit, `2a9b41b30472562633a04081d5f68a9c7f89d63d`. No document or ledger change was due, because the law did not change.
   - **Scope of the claim:** this shows the escalation-record route cleanly. It does not show the document-and-ledger route cleanly; that still waits for a ticket that lands the ledger entry in a commit before its test change.
   - **Live on `main` (2026-10-08):** the first scheduled `Slow regression` run whose head contains #422, run 37761664046 at `39e65eb5a` (#441), concluded success: every remaining red maps to an in-date `tools/test_architecture/slow_known_reds.yaml` entry, and `test_species_relations_metamorphic_validation` neither fails nor needs a mapping (its entry was removed in #422). The run's only NEW red, `test_generated_frontier_3_42_extended_population_stability`, falls under the corpus-diversity catch-all, which names it in its note.
5. **Met, text only (2026-09-30).** §6 states the bounded policy. No existing failure is quarantined.

## Related Tickets
- Depends on Epic B (taxonomy doc) for the field vocabulary.
- Feeds Epic D.
- Child: `TCK-20260930-TEST-PLAN-PROOF-FIELDS-AND-TRIAGE-PROCEDURE` (parts 1–4, done). Part 6 (policy text) and the part 5 rule text landed in the 2026-09-30 decisions batch; the part 5 agent wiring remains open.

## Related Docs
- `docs/plans/test_architecture/roadmap.md`
- `docs/plans/test_architecture/reference/architecture_design_notes.md` §5, §6.3, §7 (non-binding;
  includes the observed pytest 9.0.2 xfail semantics)
- `docs/testing/regression_policy.md`, `docs/guides/delivery_process.md`

## Related Stored Artifacts
None.

## Related Code Areas
`.claude/agents/investigator.md`, `.claude/agents/architecture-reviewer.md`,
`.claude/agents/done-checker.md`, `.claude/workflows/implement-epic.js` (notes only),
`docs/testing/regression_policy.md`.

## Assumptions / Open Questions
- **D-M2, D-MF approved with changes (2026-09-30).** As of 2026-10-01: criterion 1 met (caveat above), criterion 2 not met (partially demonstrated), criterion 4 open, criterion 5 met (text only). This epic stays open in `todos/`.
- The installed `obra/superpowers` `testing-anti-patterns.md` is the checklist basis.

## Implementation Notes
- The cost of the added fields is observed via `tool_call_count` per phase: a coarse proxy, not time
  or tokens.

## Test Summary
Defined by child tickets.

## Files Changed
(Child tickets.)

## Completion Summary
**Closed 2026-10-03 by owner decision** (the user's answers, relayed by `test-architecture-reviewer`), **with criteria 2 and 4 recorded as NOT DEMONSTRATED**, not met. Classed in `tickets/done/test-architecture/INDEX.md` (closure-readiness audit of 2026-10-03, base `origin/main` c0980e27a): C1 MET-with-caveat; C3 and C5 MET; **C2 and C4 NOT DEMONSTRATED (closed by user decision)**. Their protocols stay as written in this epic (criterion 2's protocol and run-2-blocked record, criterion 4's rule text), and the first eligible run is to be recorded against them later: C2 needs a test-changing pipeline run meeting the recorded protocol; C4 needs a ticket that changes an expectation and shows the document/ledger change first. Both are roadmap watch items.
