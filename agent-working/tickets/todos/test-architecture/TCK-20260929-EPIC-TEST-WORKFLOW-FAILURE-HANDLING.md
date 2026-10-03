---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260929-EPIC-TEST-WORKFLOW-FAILURE-HANDLING
phase: open
date: 2026-09-29
tags: [testing]
---

# TCK-20260929-EPIC-TEST-WORKFLOW-FAILURE-HANDLING

## Title
Epic C — Test workflow and failure handling: test-plan fields, an advisory test-quality checklist, and one failure-triage procedure

## Status
EPIC_SCOPED

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
   reason. **Update 2026-10-01:** in the real pipeline run on `TCK-20260930-CONSERVATION-REJECTION-PATH-ASSERTION-GAP` the checklist ran at Architecture-Verify on the two changed test files and found nothing, **but only because the orchestrator added a prompt sentence asking about it** (the workflow script does not contain it). The checklist is wired into `.claude/agents/architecture-reviewer.md`, so it should run unprompted; this run shows only that it runs when asked, and a clean diff shows nothing about detection. The criterion closes on the first later pipeline run that changes tests with the orchestrator prompt unmodified. **Update 2026-10-02 (`TCK-20260914-BOSS-KINDS-OBSERVABILITY-CONSTANT-DRIFT`; standard tier chosen by test-architecture to reach Architecture-Verify; orchestrator prompt text taken verbatim from `implement-ticket.js`, plus one output-format sentence appended by the hand-orchestrator to every agent prompt ("Return your answer as a single JSON object with keys: ...", listing the schema's keys), because the skill path does not enforce the schema; no checklist sentence was added): NOT MET; partially demonstrated.** **Correction recorded 2026-10-02:** an earlier version of this entry said the prompts were unmodified; that was inaccurate, as just stated. The appended key list for Architecture-Verify named verdict, violations, summary, verified_by and ts, mirroring `ARCH_VERIFY_SCHEMA`, which has no `test_quality_findings` field, so it may itself have steered the remark into `notes`; that is untested, and it weakens the "unprompted" reading of this run. Unprompted invocation observed: the production architecture-reviewer emitted a test-quality remark without a prompt sentence. Application to changed tests NOT demonstrated: the reviewer stated "test files were not read in depth", and returned the remark inside `notes` rather than the `test_quality_findings` list prescribed by `.claude/agents/architecture-reviewer.md`. The advisory shadow reviewer (not read by the gate) read the tests and returned a structured list with one advisory finding, declined as no action required. It is recorded separately and does not count toward this criterion. Sample size 1. Verbatim records: `stored_artifacts/TCK-20260914-BOSS-KINDS-OBSERVABILITY-CONSTANT-DRIFT/architecture_verify_production_verbatim.jsonl` and `.../architecture_verify_shadow_verbatim.jsonl`. The `ARCH_VERIFY_SCHEMA` in `.claude/workflows/implement-ticket.js` has no `test_quality_findings` field (verdict, violations, summary, ts, verified_by only) and the Architecture-Verify prompt does not ask for one, so the `notes` placement is a schema gap, not necessarily reviewer behaviour; "not read in depth" is a separate item. Both routed to agent-working-design as a test-architecture finding, with no fix proposed here.

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
3. The triage procedure is one document, and the other sources link to it. A drill classifies at
   least one real case (the Epic A leak) and one synthetic case, and routes each to the right role.
4. **Open** (rule text recorded; no ticket has yet exercised it). A ticket that changes an expectation shows the document and ledger change before
   the test change, or an escalation record. **Update 2026-10-02: not exercised** on `TCK-20260914-BOSS-KINDS-OBSERVABILITY-CONSTANT-DRIFT` (no fixture, hash, baseline or scorer moved).
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
(Open.)
