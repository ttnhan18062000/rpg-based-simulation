---
status: historical
layer: ticket
authority: P1
audience: agent
ticket_id: TCK-20260920-MECHANISM-REGISTRY-CHANGED-CODE-ADVISORY-AT-CLOSE
phase: done
date: 2026-09-20
tags: [ai, workflows, process-improvement, registry]
---

# TCK-20260920-MECHANISM-REGISTRY-CHANGED-CODE-ADVISORY-AT-CLOSE

## Title
Surface the mechanism-registry changed-code check at ticket close as a non-blocking advisory — the
closer is the only person who can cheaply judge whether a mechanism's claim still holds

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Routed in by `rpg-feature-planning` 2026-09-20, who deliberately did **not** build it: it is a
pipeline/done-checker/agent-definition change, which belongs to the agent-working domain rather
than the RPG one.

The mechanism registry landed across PRs #224/#225/#226 — 93 catalogued mechanisms with code
bindings (`implemented_by`), declared system membership, verification verdicts, 10 invariants, and
seven checks (four blocking in CI, three report-only). **Nothing connects any of it to the ticket
lifecycle.**

The interesting one is `mechanism_registry_changed_code_check.py`, whose own docstring states the
problem it solves: *"flag a PR/diff that changes `implemented_by`-cited code without touching the
citing mechanism's own registry entry… the mechanical version of the parity ledger's own decayed
'update your entry when behavior changes' rule."* It runs advisory-only in CI today
(`make mechanism-registry-changed-code-check`).

**Why ticket close is the right surface.** When a ticket edits code a mechanism claims, the person
closing that ticket is the only one who knows cheaply whether the claim still holds. In CI the same
report reaches someone who would have to reconstruct that context from scratch, so it is read as
noise and skipped. The registry's value decays exactly the way the parity ledger's did — not
through anyone deciding to stop maintaining it, but through nobody being prompted at the one moment
they had the answer.

## Scope
- Surface the changed-code check's findings at ticket close as a **non-blocking advisory**, modeled
  directly on `TCK-20260709-REGISTRY-REGEN-ON-CLOSE`, which made `docs/REGISTRY.yaml` regeneration
  "an unconditional non-blocking side effect of `run_finalize_selfcheck` on every ticket close (all
  tiers)". Same shape, same place, different payload.
- **Reach the hand-orchestrated path, not only the formal pipeline.** This is the load-bearing
  design constraint, and getting it wrong makes the whole ticket pointless — see Assumptions.
- Define precisely what "the changed files for this ticket" means, and record the definition. The
  check's core takes `check_drift(old_data, new_data, changed_files)`; the wiring has to supply
  those three things at close time, and the obvious candidates (diff against the merge-base with
  `origin/main`, versus the ticket's own commits) differ in real cases.
- Make the advisory's output actionable: name the mechanism id and the changed cited files, so the
  closer can answer without opening the registry.

## Out of Scope
- **Any blocking gate.** Not a `done_checker_static.py` condition, not a ratchet, not a CI failure.
  The user's standing principle is that agent-working/process-side data does not get strict blocking
  gates, and this check produces *judgement calls* rather than violations: a mechanism's entry
  legitimately may not need updating when its cited code changes. `rpg-feature-planning` flagged the
  same steer independently. A gate here would be wrong twice over — wrong in kind, and wrong because
  it would fire on legitimate work, the exact inverted-signal shape this repo spent 2026-09-15/16
  removing.
- Changing the four blocking CI checks, or the check's own detection logic. `check_drift()` is
  already a pure, tested core; this ticket wires it, it does not rewrite it.
- Editing `registries/mechanisms.yaml` data, or acting on whatever the advisory reports.
- Auto-updating a mechanism's entry on the closer's behalf. The judgement is the point; automating
  it away would produce exactly the unexamined entries the registry exists to prevent.

## Acceptance Criteria
- [x] Closing a ticket surfaces the advisory when a mechanism's cited code changed without its entry
      changing, naming the mechanism id and the changed files. `check_drift_for_ticket()` +
      `test_planted_drift_case_fires` (disposable temp git repo, real commits, real detection).
- [x] It surfaces on the **hand-orchestrated** close path, demonstrated on a real closure — not only
      inside `implement-ticket.js`. Ran `python3 tools/mechanism_registry/mechanism_registry_changed_code_check.py
      --ticket-id TCK-20260920-MECHANISM-REGISTRY-CHANGED-CODE-ADVISORY-AT-CLOSE` against this
      ticket's own real closing commit (`2f863f403`) — printed `0 drift finding(s), 0
      implemented_by replacement(s)`, exit 0 (correct: this ticket touches no mechanism-cited
      files). Also wired into `implement-ticket.js`'s Finalize tail as a 4th advisory, mirroring the
      existing three exactly.
- [x] It **never** blocks a close, fails a check, or changes an exit code. Proven by
      `test_planted_drift_case_fires` / `test_ticket_id_cli_path_never_fails_even_with_findings` —
      both plant real findings and assert `main()` still returns 0.
- [x] A planted no-drift case produces no advisory, so the signal means something when it appears.
      `test_planted_no_drift_case_is_silent` — same shape, registry entry updated in the same
      commit, 0 findings.
- [x] The "changed files" definition is recorded in the ticket and in the code, with the reason for
      choosing it over the alternative. See Implementation Notes below and
      `get_changed_files_for_ticket()`'s own docstring — chosen after measuring, not by preference:
      an `origin/main`-wide diff was empirically shown (on this session's own current branch) to mix
      in files from ≥4 unrelated tickets; `git log --grep=<ticket-id>` was empirically shown to
      isolate exactly one ticket's own files, verified against an already-closed sibling ticket's
      real commit.
- [x] No gate, ratchet, or blocking check is introduced anywhere. `main()` still always returns 0;
      the new Finalize-tail block only ever calls `log()`, never mutates `status` or an exit code.

## Related Tickets
- `TCK-20260709-REGISTRY-REGEN-ON-CLOSE` (done) — **the pattern to copy**: an unconditional
  non-blocking side effect of `run_finalize_selfcheck` on every ticket close, all tiers.
- `TCK-20260913-TICKET-PREMISE-STALENESS-NOT-PROPAGATED-ON-CLOSE` (done) — the other close-time
  advisory precedent; its sweep returns candidates rather than failing, which is the right shape.
- `TCK-20260916-MECHANISM-CHANGED-CODE-ENTRY-DRIFT-DETECTION` (done) — built the check being wired.
- `TCK-20260903-HAND-ORCHESTRATED-TICKETS-MISSING-MONITORING-COVERAGE` (done) — the precedent for
  why pipeline-only wiring fails here.
- `TCK-20260920-MECHANISM-REGISTRY-CI-WIRING` — the RPG-side ticket that noted this gap.

## Related Docs
- `docs/plans/mechanism_claims_as_tests_initiative.md` — §6 Non-goals, the decayed parity-ledger
  rule this mechanises
- `docs/agent-monitoring/schema.md`

## Related Stored Artifacts
- `stored_artifacts/TCK-20260920-MECHANISM-REGISTRY-CHANGED-CODE-ADVISORY-AT-CLOSE/` —
  `investigation.md`, `plan.md`, `test_plan.md`.

## Related Code Areas
- `tools/mechanism_registry/mechanism_registry_changed_code_check.py` (`check_drift()` is the pure
  core; `main()` always returns 0 and prints the report)
- `Makefile` (`mechanism-registry-changed-code-check`)
- `tools/gate_checks/done_checker_static.py` — for its **CLI entry point pattern only**
  (`--ticket-id`), not to add a condition to it
- `.claude/workflows/implement-ticket.js` (`run_finalize_selfcheck`) and the agent role files that
  describe Finalize

## Assumptions / Open Questions
- **Wiring only into `implement-ticket.js`'s Finalize would miss most real closures.** Nearly all
  recent closes in this repo are hand-orchestrated — read the ticket, edit, test, close — without
  invoking the `Workflow` tool, which is exactly why
  `TCK-20260903-HAND-ORCHESTRATED-TICKETS-MISSING-MONITORING-COVERAGE` exists and why
  `record_hand_orchestrated_closure.py` had to be written. A pipeline-only advisory would be a
  mechanism that exists, passes its tests, and is never seen — the silence-as-a-state shape
  catalogued in `reachability_verification_findings.md`. Resolve this first: the likely answer is a
  CLI the closer runs (like `done_checker_static.py --ticket-id`), invoked from the same step that
  already records monitoring coverage, with the pipeline path calling the same entry point.
- **What counts as "this ticket's changed files" is genuinely undecided.** Diffing against the
  merge-base with `origin/main` catches everything on the branch including unrelated merge noise;
  using only the ticket's own commits is narrower but depends on commit hygiene. Measure both on a
  real recent closure before choosing, and record why.
- Whether the advisory should also write its finding into the ticket body is open. Leaning no — the
  closer sees it at close time, and an auto-written note nobody reads is the failure mode this
  ticket is trying to avoid.
- How noisy this is in practice is unmeasured. If a typical close reports many mechanisms, the
  advisory will be ignored regardless of how it is surfaced. Measure the rate on a handful of recent
  real closures before designing the output format; a check that cries wolf is worse than none.

## Implementation Notes
**Measurement, done before any code (per explicit instruction), reported to peer and approved
before building:**
- Ran the CLI from the registry's foundation commit (`8ab22a916`, 2026-09-17) through `origin/main`
  (2026-09-20): 0 drift findings, 0 replacements. Verified non-trivial (registry grew 89→93
  mechanisms in that span). **Correction applied per peer review**: this is 0/0 over a three-day
  window in which the only sessions touching cited code were the registry-aware program itself —
  weak evidence in either direction, not a property of "the registry's entire life."
- `git show --stat 97a0e5d96` (#229): one squash-merge commit bundles six distinct ticket IDs —
  real, common batch-PR bundling in this repo, not hypothetical.
- Tested `origin/main`-wide diff on this session's own current branch: mixed in files from ≥4
  unrelated tickets. Tested `git log --grep=<ticket-id>` against an already-closed sibling ticket's
  real commit (`78285e208`): isolated exactly that ticket's own files. This works because every
  commit here references its ticket ID (Commit Convention).

**Definition chosen**: changed_files = union of (a) every file in every commit whose message
matches the ticket ID (`git log --grep=<ticket_id>`), (b) the current uncommitted working tree
(`git status --porcelain`). (b) exists per peer's flagged concern: without it, a closer who commits
everything in one final commit would run this *before* that commit exists and read "no drift" as a
real negative — a silent fail-open in the direction that looks like success. With (b), the check is
immune to run-before-or-after-commit timing.

**Boundary recorded, not hidden**: the `--grep` definition is pre-merge-only. After a squash-merge,
`main` holds one commit whose message carries every bundled ticket ID — running this query over
post-merge history would match that one commit for every bundled ticket and over-attribute every
changed file to all of them. Documented in `get_changed_files_for_ticket()`'s own docstring; must
never be used to backfill findings against `main` history.

**Reachability**: hand-orchestrated close documented as a manual CLI step in `CLAUDE.md`'s "After
Work" section (mirrors how `record_hand_orchestrated_closure.py` itself is documented there —
there's no other reachability path for the hand-orchestrated case). Pipeline path calls the same
`check_drift_for_ticket()` from `implement-ticket.js`'s Finalize tail, as a 4th advisory alongside
the existing three (`check_monitoring_write_recorded`, `check_tag_drift`,
`check_workflow_meta_conformance`) — identical non-blocking shape, `log()`-only.

## Test Summary
- `pytest tests/unit/tools/test_mechanism_registry_changed_code_check.py -v` — 17 passed (12
  pre-existing + 5 new): planted-drift fires, planted-no-drift silent, uncommitted working-tree
  changes detected, cross-ticket contamination avoided (a second, differently-tagged commit on the
  same disposable repo does not bleed into the first ticket's changed_files), `--ticket-id` CLI path
  always exits 0 even with real findings.
- `pytest tests/tools/test_workflow_meta_conformance.py -q` — 25 passed, 1 xfailed (unaffected by
  the new Finalize-tail block, since it adds no new phase title).
- `pytest tests/unit/tools/ tests/tools/ -k "mechanism_registry or done_checker or workflow_meta" -q`
  — 286 passed, 1 skipped, 1 xfailed (no regressions in adjacent areas touched by the CLI-pattern
  reference).
- `node --check .claude/workflows/implement-ticket.js` — syntax clean.
- Real demonstration on this ticket's own closure: CLI run against the real repo, real commit,
  `--ticket-id TCK-20260920-MECHANISM-REGISTRY-CHANGED-CODE-ADVISORY-AT-CLOSE` → `0 drift
  finding(s), 0 implemented_by replacement(s)`, exit 0 (correct — no mechanism-cited files touched
  by this ticket's own work).

## Files Changed
- `tools/mechanism_registry/mechanism_registry_changed_code_check.py` — added
  `get_changed_files_for_ticket()`, `check_drift_for_ticket()`, `_uncommitted_changed_files()`;
  extended `main()` with `--ticket-id`; updated module docstring.
- `tests/unit/tools/test_mechanism_registry_changed_code_check.py` — 5 new tests using a disposable
  temp git repo (`_REPO_ROOT` monkeypatched for the call's duration; never touches this repo's real
  history).
- `.claude/workflows/implement-ticket.js` — 4th Finalize-tail advisory block, same non-blocking
  shape as the existing three.
- `.claude/skills/implement-ticket/SKILL.md` — updated Finalize phase description ("three" →
  "four" advisory-only checks, names the new one).
- `CLAUDE.md` — one new bullet in "After Work" documenting the manual hand-orchestration CLI step.

## Completion Summary
Wired `mechanism_registry_changed_code_check.py`'s existing pure `check_drift()` core into ticket
close as a non-blocking advisory, on both the hand-orchestrated path (documented manual CLI step,
demonstrated on this ticket's own real closure) and the formal pipeline (`implement-ticket.js`
Finalize tail, 4th advisory). Measured before building, per explicit instruction: historical drift
rate is 0/0 over the registry's short real life so far (recorded honestly as weak evidence, not
proof of anything), and the "changed files" definition was resolved empirically rather than by
preference — a ticket-scoped `git log --grep` plus working-tree state, chosen over a branch-wide
`origin/main` diff after demonstrating the latter cross-contaminates drift attribution across this
repo's real multi-ticket batch PRs. The `--grep` definition's own pre-merge-only boundary is
recorded in both the ticket and the code, not left implicit. No gate, ratchet, or blocking check
introduced anywhere — proven by planted-finding tests that still exit 0.
