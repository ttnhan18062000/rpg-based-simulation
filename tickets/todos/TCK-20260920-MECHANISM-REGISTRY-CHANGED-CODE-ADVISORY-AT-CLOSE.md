---
status: active
layer: ticket
authority: P1
audience: agent
ticket_id: TCK-20260920-MECHANISM-REGISTRY-CHANGED-CODE-ADVISORY-AT-CLOSE
phase: open
date: 2026-09-20
tags: [ai, workflows, process-improvement, registry]
---

# TCK-20260920-MECHANISM-REGISTRY-CHANGED-CODE-ADVISORY-AT-CLOSE

## Title
Surface the mechanism-registry changed-code check at ticket close as a non-blocking advisory — the
closer is the only person who can cheaply judge whether a mechanism's claim still holds

## Status
OPEN

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
- [ ] Closing a ticket surfaces the advisory when a mechanism's cited code changed without its entry
      changing, naming the mechanism id and the changed files.
- [ ] It surfaces on the **hand-orchestrated** close path, demonstrated on a real closure — not only
      inside `implement-ticket.js`.
- [ ] It **never** blocks a close, fails a check, or changes an exit code. Proven by a planted case
      that reports findings and still exits zero.
- [ ] A planted no-drift case produces no advisory, so the signal means something when it appears.
- [ ] The "changed files" definition is recorded in the ticket and in the code, with the reason for
      choosing it over the alternative.
- [ ] No gate, ratchet, or blocking check is introduced anywhere.

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
- None yet.

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
Do not start by writing code. Start by measuring: run the existing check against the last few real
ticket closures and see what it would have said. That answers the noise question, the changed-files
question, and whether this is worth wiring at all — and it costs almost nothing, since the check
already exists and runs.

If the measurement shows the advisory would fire constantly or never, report that instead of
building. Either result is more useful than a wired advisory nobody reads.

## Test Summary
_To be completed by the implementer._

## Files Changed
_To be completed by the implementer._

## Completion Summary
_Open._
