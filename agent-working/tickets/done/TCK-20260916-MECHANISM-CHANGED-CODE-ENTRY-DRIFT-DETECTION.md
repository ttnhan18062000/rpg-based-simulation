---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260916-MECHANISM-CHANGED-CODE-ENTRY-DRIFT-DETECTION
phase: done
date: 2026-09-16
tags: [architecture, schema, simulation-quality]
---

# TCK-20260916-MECHANISM-CHANGED-CODE-ENTRY-DRIFT-DETECTION

## Title
Flag a PR that changes `implemented_by`-cited code without touching the mechanism's own registry
entry

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Now that `implemented_by` exists (`TCK-20260916-MECHANISM-IMPLEMENTED-BY-BINDING`), a mechanism's
real code binding is a structured, checkable fact for the first time. This lets a mechanical check
compare a PR's changed files against every mechanism's `implemented_by` citations: if code cited
by a mechanism changed and that mechanism's own registry entry (`state`, `depends_on`, `verified`,
`implemented_by` itself) did NOT change in the same diff, flag it.

This is the mechanical version of a rule the project already has and already lost to decay: the
parity ledger's own standing instruction ("when a behavior changes, update its entry and
evidence") required exactly this discipline, and it decayed anyway —
`TCK-20260904-PARITY-LEDGER-...` (see working_log for the exact ticket) had to be run specifically
to repair stale parity-ledger `test_path` citations after they drifted from the code they were
supposed to track. A rule that depends on someone remembering is the same failure class as a
document that depends on someone reading it. This check needs no policy change or user
authorization — it is mechanical, not a new workflow rule.

## Scope
1. Given a PR's changed-file list (or a local diff against a base ref), compare against every
   mechanism's `implemented_by` paths in `mechanisms.yaml`.
2. If any `implemented_by`-cited file changed AND `mechanisms.yaml` itself did not change in the
   same diff (or changed but that specific mechanism's own entry did not), report it.
3. Report-only, same convention as every other detector in this corpus — never fails the build.
4. Wire into the same place `mechanism_registry_completeness_check.py` and
   `mechanism_registry_graphify_check.py` are surfaced (CI job / `make` target), so it runs without
   anyone remembering to invoke it.

## Out of Scope
- Any enforcement stronger than report-only (a blocking CI gate) — not requested, would need
  explicit user sign-off given it could block unrelated PRs on incidental churn.
- Extending this to the parity ledger's own `test_path` drift (already has its own baseline-check
  precedent, `tests/tools/test_parity_index_baseline.py`) — a separate, already-solved problem,
  cited here only as the argument for why this check needs to be mechanical.

## Acceptance Criteria
1. A tool exists that, given a set of changed file paths, returns every mechanism whose
   `implemented_by` citation includes a changed file, annotated with whether that mechanism's own
   entry also changed.
2. Report-only, verified never to return a non-zero/blocking exit code by itself.
3. A real test using this epic's own git history (e.g. the `causal_spatial_memory` state-drift fix
   commit, which changed both the citing code's own surrounding context and the registry entry
   together) as a positive control that the detector would NOT have flagged, and a synthetic
   negative control (a changed cited file with no registry change) that it WOULD flag.

## Related Tickets
- `TCK-20260916-MECHANISM-IMPLEMENTED-BY-BINDING` — hard precondition; this check reads
  `implemented_by`, which only exists for 20 of 89 mechanisms today. Effectiveness grows as that
  field's own coverage grows.
- `TCK-20260916-MECHANISM-STATUS-LANGUAGE-DETECTION` — sibling report-only detector filed
  alongside this one; independent, can land in either order.

## Related Docs
- `docs/plans/mechanism_claims_as_tests_initiative.md` §6 Non-goals (peer's own planning doc — read
  before implementing for the exact non-goal wording around why no new CLAUDE.md rule is needed).
- `docs/parity_ledger/` and its own `test_path` drift precedent, cited as the argument for this
  check's necessity.

## Related Stored Artifacts
None yet.

## Related Code Areas
- `registries/mechanisms.yaml`
- New: `tools/mechanism_registry/mechanism_registry_changed_code_check.py` (proposed) — the 14
  existing mechanism-registry tools were moved into `tools/mechanism_registry/` by
  `TCK-20260916-MECHANISM-REGISTRY-TOOLS-PACKAGE`; a 15th tool belongs there too, not back in the
  flat `tools/` directory.

## Assumptions / Open Questions
Exact PR-diff acquisition mechanism (local `git diff` against a base ref vs. a CI-provided
changed-file list) needs deciding during implementation based on where this actually gets wired in.

## Implementation Notes
`tools/mechanism_registry/mechanism_registry_changed_code_check.py`, two pure, testable entry
points plus a git-diff wrapper: `check_drift(old_data, new_data, changed_files)` returns every
mechanism whose `implemented_by` citation includes a changed file where the mechanism's own entry
(compared as a whole dict, old vs new) did NOT change; `check_replacements(old_data, new_data)`
separately reports mechanisms whose `implemented_by` was replaced (already had a citation, now
points elsewhere) rather than bound for the first time — cheap to compute from the same old/new
comparison already in hand, offered by peer review and included since it fit cleanly without
expanding the core drift check's own scope. `check_drift_from_git(base_ref, head_ref)` resolves
changed files via `git diff --name-only` and loads the registry at both refs via `git show`
(`"WORKTREE"` as a special `head_ref` reads the real on-disk file for uncommitted changes, rather
than requiring a commit).

**The replacement signal's own motivating validation**: run manually (not as a committed test, for
the reason below) against this session's own two real commits spanning the `trauma` misattribution
and its same-day correction — 0 drift findings, 1 replacement finding, `trauma:
['.../RecoveryReadinessService'] -> ['.../WoundService']`. The tool would have surfaced exactly the
incident that motivated adding this signal, confirmed against real history before trusting the
synthetic tests alone.

**AC #3's own suggested positive control (the `causal_spatial_memory` state-drift fix commit)
does not exist as a single real commit** — checked directly: no commit in this repo's history
changes `src/domains/memory/phase.py` and `registries/mechanisms.yaml` together (the registry
itself didn't exist until 2026-09-15, after that file's own last code change). Used synthetic
fixtures for both controls instead, which the AC's own "e.g." phrasing allows. The real-history
validation above was run manually rather than committed as a test, since hardcoding a specific
commit SHA from this feature branch would break the moment the branch squash-merges (this repo's
own PR convention, `CLAUDE.md`'s "PR Lifecycle" §7) — those exact commit objects stop being
reachable from `main` and eventually get garbage-collected. The synthetic tests are timeless; a
SHA-pinned test would not have been.

**Generalizable takeaway for whoever next builds a control against real history in this repo**: a
test pinned to a commit on a branch that will squash-merge is a test with a scheduled expiry —
validate against real history manually when it's available, keep the committed tests synthetic.

## Test Summary
`tests/unit/tools/test_mechanism_registry_changed_code_check.py` (12 new tests): AC #3's own
positive control (code + entry changed together, not flagged) and synthetic negative control
(code changed, entry untouched, flagged) as the two load-bearing tests, plus symbol-suffix
stripping, multi-file citation handling, the replacement-vs-first-binding distinction (2 tests),
report-only guarantee (`main()` always exits 0, including on git-resolution failure — "SKIPPED"
rather than a crash), and the Make target. Full `tests/unit/tools/` suite: 241 passed.

## Files Changed
- `tools/mechanism_registry/mechanism_registry_changed_code_check.py` — new.
- `Makefile` — new `mechanism-registry-changed-code-check` target.
- `tests/unit/tools/test_mechanism_registry_changed_code_check.py` — new, 12 tests.

## Completion Summary
**Done.** Last of the two remaining detectors named in the mechanism-registry program's own
pivot order, closing that arc. AC #1/#2 met directly. AC #3 met with synthetic fixtures rather
than the suggested real historical commit (confirmed not to exist as a single commit — the
registry postdates the code's own last change), plus a manual (not committed, for durability
reasons stated above) validation against this session's own real `trauma` misattribution/
correction commit pair, which the replacement signal caught exactly as designed.
