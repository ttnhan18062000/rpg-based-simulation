---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260924-EPIC-GITHUB-DELIVERY-PROCESS
phase: done
date: 2026-09-24
tags: [delivery, ai, process-improvement]
---

# TCK-20260924-EPIC-GITHUB-DELIVERY-PROCESS

## Title
GitHub delivery process — make the commit → push → PR → CI → merge lane explicit, rendered and
measurable, the way the ticket lane already is

## Status
EPIC_SCOPED

## Tier
epic

## Type
feature

## Priority
P2

## Request Summary
The ticket lane has a format, a registry, gates, a done-checker and monitoring records. The
delivery lane has none of that — it has 84 lines of hard-won prose in `CLAUDE.md` that a
human-shaped agent must read and obey by hand, every time, with no check that it did.

Measured over `agent-monitoring/data/2026-W3*/tools.jsonl` (W30–W39, 116,168 Bash calls, read from
`origin/main` at `75ab942b4`), four gaps in descending order of cost — full evidence in
`docs/plans/agent_infrastructure/github_delivery_process/plan.md` §1:

1. **Observation cost** — 1,796 `gh` invocations against 106 `gh pr create` = **16.9 `gh` calls per
   PR, ~86% of it pure observation** (~14 polling round-trips per PR), because no tool answers
   "what is the state of this PR?" in one call. (§1.1)
2. **Unexecutable lore** — 84 of `CLAUDE.md`'s 440 lines (19%) are delivery process. Every bullet
   cites a real incident; none of it is executable. (§1.2)
3. **No templates** — `.github/` contains exactly two files, both workflows
   (`workflows/test.yml`, `workflows/deploy-docs.yml`). No `pull_request_template.md`, no
   `.gitmessage`. Every PR title and body is composed from scratch. (§1.3)
4. **Subject-line traceability** — of the last 60 `origin/main` subjects, 60/60 carry `(#NNN)` and
   only **17/60 (28%)** carry a `TCK-` ID. Because the repo squash-merges, the PR title becomes the
   mainline subject. Traceability is *not lost* (bodies carry 770 `TCK-` mentions), it is absent
   from the line `git log --oneline` and blame views show. A real but **moderate** gap. (§1.4)

The organising idea is not "give the agent a form to fill in" — that is a human process
transplanted. It is: **the PR title and body are rendered from the tickets on the branch, not
authored**, and PR state is returned as one typed verdict rather than assembled from five `gh`
calls and reasoned about in prose. (§3.1)

## Scope
Six child tickets, in `SEQUENCE.md` order. The sequence deliberately inverts the original request's
M1-first ordering — see `SEQUENCE.md` for the reasoning.

1. **`TCK-20260924-DELIVERY-STATUS-TOOL`** (plan M4) — `tools/delivery/pr_status.py` returning a
   typed `GREEN`/`PENDING`/`FAILING`/`ABSENT`/`UNKNOWN` verdict in one call, per plan §3.7. Largest
   measured cost, most incident-backed logic, zero dependencies. Runs first.
2. **`TCK-20260924-DELIVERY-CONTRACT-AND-TEMPLATES`** (plan M1) — `docs/guides/delivery_process.md`
   as the single source, `.gitmessage`, `.github/pull_request_template.md`, and the
   machine-readable template spec the renderer consumes. Collapses `CLAUDE.md`'s delivery lines and
   `ai_first_hardening_epics/roadmap.md`'s overlapping section to pointers.
3. **`TCK-20260924-DELIVERY-PR-RENDERER`** (plan M2) — `tools/delivery/pr_render.py`, emitting
   title + body from the ticket files on the branch per plan §3.5/§3.6, with a `--check` mode.
4. **`TCK-20260924-DELIVERY-PRE-PUSH-ADVISORY`** (plan M3) — advisory pre-push check following the
   existing `cd_prefix_advisory_hook.py` shape. Never blocking.
5. **`TCK-20260924-DELIVERY-CI-TRIAGE-CLASSIFIER`** (plan M5) — encodes the `CLAUDE.md` triage
   decision tree as a classifier over a failing run. Advisory; the agent still files the ticket.
6. **`TCK-20260924-DELIVERY-COST-MEASUREMENT`** (plan M6) — reports `gh`-calls-per-PR and
   subject traceability over a week range on top of the existing
   `tools/agent-monitoring/bash_command_mix.py`, so before/after is one command.

## Out of Scope
- **Auto-merging.** Merge stays the user's call, unchanged.
- **Auto-opening PRs.** PR creation stays where `CLAUDE.md` puts it: user-authorized.
- **A release/versioning pipeline**, changelog generation, or semantic-release. This repo does not
  release a versioned artifact; adopting `feat:`/`fix:` to drive a changelog nobody reads would be
  cargo cult (plan §3.2).
- **Changing `test.yml` or what CI runs.** This epic is about the process *around* CI, not CI.
- **Anything blocking — settled decision, not an open question.** No blocking commit-lint, no
  blocking PR-shape CI check, no blocking commit-subject-names-a-real-ticket job. Every check this
  epic ships prints and exits zero. Per
  [[feedback_agent_tooling_checks_proportionate]]: these are process conveniences, not correctness
  gates. Children 4 and 5 restate this as their own scope guard.
- **Ticket IDs in the PR title — settled decision.** They go in a `Closes:` block in the PR body
  only (plan §3.5/§3.6). Three 40-char IDs would crowd out the readable part of the very
  `git log --oneline` view that motivates §1.4.
- **Reviewer checklists and "I have tested this" tick-boxes.** A self-certifying agent ticking a
  box is theatre; the real signals (done-checker conditions, the CI run) already exist (plan §3.2).
- **Touching the parked red "Slow regression" on main** — a user decision, not news.

## Acceptance Criteria
Epic-level, each proven by its own child's criteria:

1. PR state is obtainable in **one** tool call returning a typed verdict, and `UNKNOWN` is never
   reported as green.
2. The delivery rules live in exactly **one** hand-authored place (`docs/guides/delivery_process.md`),
   with `CLAUDE.md` and `roadmap.md` reduced to pointers — [[feedback_define_information_once_never_repeat]].
3. A PR title and body are **rendered** from the ticket files on the branch; only `## Review notes`
   is hand-written.
4. Every check shipped by this epic is advisory: it prints and exits zero, and a test asserts the
   zero exit on a deliberately non-conforming input.
5. `gh`-calls-per-PR and subject traceability are reportable over a week range by one command that
   records the ref/SHA it measured.
6. No PR body produced by this epic's tooling contains an attribution trailer
   ([[feedback_no_coauthor_footer_in_pr]]).

## Related Tickets
- `TCK-20260915-CI-TRIAGE-HAS-NO-ABSENT-RUN-BRANCH` — the absent-run branch child 1 encodes
- `TCK-20260923-BASH-COMMAND-MIX-BASELINE` — shipped `bash_command_mix.py`; child 6 builds on it
- `TCK-20260924-WORKFLOW-AGENT-LITERAL-VOCABULARY-CHECK` — scoped alongside this epic from the same
  review, deliberately **not** a child of it (different subsystem: monitoring vocabulary, not
  delivery)

## Related Docs
- `docs/plans/agent_infrastructure/github_delivery_process/plan.md` — the authoritative design;
  §1 evidence, §3 design, §3.5/§3.6 templates, §3.7 status-tool verdicts, §7 resolved decisions
- `docs/plans/agent_infrastructure/ai_first_hardening_epics/roadmap.md` §"Git & delivery process"
  (lines 280–318) — the overlapping forward-looking section child 2 reduces to a pointer
- `docs/testing/regression_policy.md` — the documented-flake category child 5 classifies against

## Related Stored Artifacts
None yet. The plan doc above carries the investigation; per the standing no-plan-only-PRs rule it
is untracked until this epic's implementation PR folds it in.

## Related Code Areas
- `tools/delivery/` — does not exist yet; created by child 1
- `docs/guides/delivery_process.md` — does not exist yet; created by child 2
- `.github/` — currently only `workflows/test.yml` and `workflows/deploy-docs.yml`
- `tools/agent-monitoring/bash_command_mix.py` — exists on `main`; child 6's foundation
- `tools/agent-monitoring/cd_prefix_advisory_hook.py` — the advisory-hook shape child 4 follows
- `CLAUDE.md` — `## Worktree & Branch Isolation` (129), `### CI Failure Triage` (399),
  `### PR Lifecycle` (418), Commit Convention; 440 lines total

## Assumptions / Open Questions
1. **All seven scoping decisions are settled** (plan §7): status tool first; `Closes:` in the body
   only; advisory everywhere; the `CLAUDE.md` edit is in scope; `roadmap.md` collapses too; epic
   folder rather than two batches. Children must not re-open them.
2. **Whether `gh`'s own output is stable enough** to parse for child 1's verdicts, or whether the
   REST API via `gh api` is the more durable surface. Child 1 decides on evidence; the `ABSENT`
   branch already requires `gh api .../actions/runs?head_sha=` and `gh pr view --json mergeable`.
3. **How much of the 16.9 `gh` calls per PR is actually collapsible.** A single status call replaces
   the *polling* portion (~86%), not `gh pr create` or a legitimate re-poll after a push. The honest
   target is a large reduction in observation round-trips, not 16.9 → 1.
4. Whether the rendered-body approach survives a batch PR whose tickets span two unrelated themes.
   Plan §6 names thin ticket content as the main risk; a two-theme batch is the untested shape.

## Implementation Notes
Epic tier — scope only, no direct implementation. Children carry their own plans.

Sequencing is not advisory: child 6 measures what children 1–5 changed, so it must run last, and
child 1 must run first so child 6 has a real before/after. Children 3 and 5 depend on 2 and 1
respectively. See `SEQUENCE.md`.

One branch for the whole epic, one PR when the batch is complete, per the standing batch rule
([[feedback_pr_creation_no_ask_after_batch]]). Merge remains the user's call.

## Test Summary
Per child ticket.

## Files Changed
None (epic).

## Completion Summary
All six children closed, in `SEQUENCE.md` order, plus one hotfix correction discovered during
review:

1. `TCK-20260924-DELIVERY-STATUS-TOOL` — `tools/delivery/pr_status.py`, five-verdict CI status tool.
1b. `TCK-20260924-DELIVERY-STATUS-TOOL-WORKFLOW-SCOPE` (hotfix) — partitioned the status tool's
   verdict by workflow, fixing a doc/code disagreement found in review.
2. `TCK-20260924-DELIVERY-CONTRACT-AND-TEMPLATES` — `docs/guides/delivery_process.md`,
   `.gitmessage`, `.github/pull_request_template.md`; `CLAUDE.md` (440→387 lines) and `roadmap.md`
   collapsed to pointers, both committed only after the user's direct confirmation of the literal
   diff.
3. `TCK-20260924-DELIVERY-PR-RENDERER` — `tools/delivery/pr_render.py`.
4. `TCK-20260924-DELIVERY-PRE-PUSH-ADVISORY` — `tools/delivery/pre_push_advisory_hook.py`, wired
   into `.claude/settings.json` after the same direct-confirmation rule.
5. `TCK-20260924-DELIVERY-CI-TRIAGE-CLASSIFIER` — `tools/delivery/ci_triage_classifier.py`.
6. `TCK-20260924-DELIVERY-COST-MEASUREMENT` — `tools/delivery/delivery_cost_measurement.py`, plus
   the real pre-epic baseline (`origin/main` W30–W39, SHA `0e0ff8f2172634226b1e8a04338fec8b5972a2c6`):
   16.04 `gh` calls per PR (`gh_pr_create_count` matches plan §1.1's cited 106 exactly; the modest
   difference in total `gh` calls from the plan's own 16.9 figure is ref drift, not a discrepancy).
   No "after" number was computed — the epic's own tools were not yet in use while tickets 1–5 were
   implemented, so this batch's corpus is not a valid after-datapoint; that measurement waits for a
   real PR delivered using the new tools.

Every check this epic shipped is advisory (zero-exit asserted by test in every case). No PR body
produced by this epic's tooling carries an attribution trailer (asserted by test). All governing-
file edits (`CLAUDE.md`, `roadmap.md`, `.claude/settings.json`) were shown to and approved directly
by the user, never inferred from scope agreement or a peer's relay. `docs/testing/regression_
policy.md` is read at runtime by child 5, never duplicated. `tools/agent-monitoring/
bash_command_mix.py` was extended, not duplicated, by child 6. `data_runs_clean` FAILed on every
close for the same pre-existing, shared-worktree reason (not attributable to any child ticket) —
reported each time, not routed around.

`TCK-20260924-MONITORING-SHARD-SQUASH-MERGE-CONFLICT-AVOIDANCE` rides the same branch as a
deliberate non-child (different subsystem), now unblocked with this ticket's own closure.
