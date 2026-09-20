---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260920-MECHANISM-REGISTRY-CI-WIRING
phase: done
date: 2026-09-20
tags: [architecture, schema, testing]
---

# TCK-20260920-MECHANISM-REGISTRY-CI-WIRING

## Title
Wire the mechanism-registry program's own checks into CI — 14 Makefile targets and 241 tests
shipped with nothing invoking any of it automatically

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Peer review, checking `origin/main` after `TCK-20260918-EPIC-MECHANISM-SYSTEM-MEMBERSHIP`'s own
program landed (#224): the program shipped 14 Makefile targets and 241 tests, and nothing invokes
any of it automatically — no CI job, no pipeline phase, no agent definition, no guideline
reference. The only `mechanism` hit in `.github/workflows/test.yml` before this ticket was an
unrelated comment about the needs-success mechanism. Every check the program built was opt-in —
exactly the orphan-artifact shape the whole program exists to catch, now sitting in the program
itself.

Pure wiring, no logic or mechanism fixes: another session is rechecking and planning the next RPG
roadmap in parallel, and simulation behaviour needs to stay still while they measure.

## Scope
1. **Blocking, added to the `arch-docs` job** (`"Architecture / docs / static"`, where the other
   doc-consistency gates already live): `make mechanism-registry-validate`,
   `make mechanism-atlas-check`, `make mechanism-capabilities-check`,
   `make mechanism-wiring-map-classdef-check`. All four are currently clean, so the gate starts
   green and only fires on real new drift.
2. **Report-only, non-blocking, same job**: `make mechanism-state-caller-check`,
   `make mechanism-status-language-check`, `make mechanism-registry-changed-code-check`. Printed
   to the job log (`|| true` per invocation, on top of each tool's own internal exit-0 guarantee —
   defense in depth, not reliance on either alone). These surface judgement calls, not violations;
   never upgraded to blocking, per Gate Integrity.
3. **A real drift found while in there**: `mechanism-registry-validate`'s own Makefile help text
   said "its 6 invariants" — `registry.py::validate()` enforces 10 (the module's own docstring
   already had the correct count; the Makefile line was the one place still stale). Fixed.

## Out of Scope
- The pipeline, done-checker, or any agent definition — wiring the registry into ticket-close is a
  real, probably-correct idea, but it's agent-infrastructure and belongs to `agent-working-design`,
  not this session. Written up as a follow-up ticket (see Related Tickets) rather than built.
- Any logic or mechanism-state change — simulation behaviour must stay still while another session
  measures the next roadmap pass.
- Upgrading any of the three report-only checks to blocking.

## Acceptance Criteria
1. The 4 blocking checks run in `arch-docs` and currently pass (registry is clean).
2. The 3 report-only checks run in the same job and never fail it, proven by test/inspection, not
   assumed from each tool's own "report-only" docstring claim alone.
3. Each of the 4 blocking checks is proven to actually fail on deliberately broken input before
   being trusted green — not just proven to pass on clean input. The proof method is recorded here
   (Implementation Notes), not just asserted.
4. Makefile help text accurately states 10 invariants, not 6.
5. No pipeline, done-checker, or agent-definition file is touched.

## Related Tickets
- `TCK-20260918-EPIC-MECHANISM-SYSTEM-MEMBERSHIP` — the program this ticket wires in; closed via
  PR #224.
- `TCK-20260919-MECHANISM-WIRING-MAP-CLASSDEF-REGENERATE-MODE-GAP` — a separate, already-filed,
  still-open follow-up (the wiring-map classdef tool is check-only, no `--fix` mode); unrelated to
  this ticket's own CI-wiring scope, not touched here.
- Follow-up ticket for `agent-working-design` (registry-into-ticket-close wiring): not filed by
  this session per the domain-split convention — flagged here as a real idea for that session to
  pick up if they choose to, not built or ticketed on their behalf.

## Related Docs
None new.

## Related Stored Artifacts
None yet — created alongside implementation in this same session.

## Related Code Areas
- `.github/workflows/test.yml` (`arch-docs` job)
- `Makefile`

## Assumptions / Open Questions
The `mechanism-registry-changed-code-check`'s own default `--base origin/main` needs `origin/main`
resolvable as a real local ref in CI's shallow checkout — `actions/checkout@v5`'s default
(`fetch-depth: 1`, single branch) does not expose it without an explicit fetch. Added a dedicated
fetch step (`git fetch origin main:refs/remotes/origin/main --depth=1`) rather than relying on the
tool's own graceful SKIPPED fallback, since a check that always silently skips in CI is the same
false-confidence shape this ticket exists to prevent for the blocking checks — see Implementation
Notes for how this was verified.

## Implementation Notes
Added 3 new steps to `.github/workflows/test.yml`'s `arch-docs` job, right after its existing
pytest "Run" step: (1) "Mechanism registry checks (blocking)" — the 4 targets, plain sequential
`make` calls relying on GHA's own default `bash -eo pipefail` step shell to stop and fail on the
first non-zero; (2) "Fetch origin/main for mechanism registry changed-code check" — a dedicated
fetch, warning-only on failure; (3) "Mechanism registry checks (report-only)" — the 3 targets, each
suffixed `|| true`. Fixed the Makefile's own stale "6 invariants" help text to the real 10 (the
module docstring already had the correct count and full per-invariant description; only the
Makefile line was still stale).

**AC #3's own proof, performed for real** (full detail in `test_plan.md`): each of the 4 blocking
checks was deliberately broken (an unresolvable `depends_on` id for `validate`; a registry state
changed without regenerating its own consumer artifact for the 3 drift checks), confirmed to fail
with a real non-zero exit via a non-piped capture (avoiding the `command | tail; echo $?`
pipe-exit-code gotcha that would have reported the wrong code), then restored from a
`cp`-then-`git diff --stat` verified-clean backup before the next check — never left broken
between tests, never assumed correctness by inspection alone.

**The shallow-checkout fetch step was verified against a real clone topology**, not the
worktree's own directory (whose remote-tracking refs don't transfer to a plain clone the way a
real GitHub Actions checkout of the real `origin` remote does) — see investigation.md for the
bare-repo fixture used instead.

## Test Summary
`tests/unit/tools/` — 241 passed, unchanged (this ticket touches CI/Makefile configuration, not
registry content or tool logic, so no regression expected or found). No new pytest file; the load-
bearing verification here is the direct command-execution proof in `test_plan.md`, since a CI
workflow step's own correctness isn't something a pytest suite running inside that same CI can
self-certify.

## Files Changed
- `.github/workflows/test.yml` — 3 new steps in the `arch-docs` job.
- `Makefile` — `mechanism-registry-validate`'s help text corrected to 10 invariants.

## Completion Summary
**Done.** All 5 Acceptance Criteria met: the 4 blocking checks run and currently pass (AC #1); the
3 report-only checks run and are proven never to fail the job, both by design and by an added
`|| true` safety net (AC #2); each blocking check is proven to actually fail on deliberately broken
input, not just assumed from passing on clean input (AC #3, the ticket's own load-bearing
requirement); the Makefile help text is corrected (AC #4); no pipeline, done-checker, or agent-
definition file was touched (AC #5) — the registry-into-ticket-close idea is named in Related
Tickets as a real idea for `agent-working-design` to pick up, not built or filed on their behalf.
