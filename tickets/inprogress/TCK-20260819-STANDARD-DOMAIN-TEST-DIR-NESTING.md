---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260819-STANDARD-DOMAIN-TEST-DIR-NESTING
phase: open
date: 2026-08-19
tags: [testing]
---

# TCK-20260819-STANDARD-DOMAIN-TEST-DIR-NESTING

## Title
Nest 6 stray domain-subpackage test directories under tests/unit/domains/ to match the other 13

## Status
OPEN

## Tier
standard

## Type
refactor

## Priority
P2

## Request Summary
`src/domains/` has 19 subpackages. Only 13 have their tests nested under
`tests/unit/domains/<name>/`; the other 6 — `campaigns`, `chronicle`, `culture`, `faction`,
`feature_packs`, `optimization` (61 files total) — sit as flat siblings directly under
`tests/unit/`. This is item 3 of `TCK-20260817-CODEBASE-NAVIGABILITY-HYGIENE-EPIC`, previously
flagged but left unverified ("coverage exists... just inconsistently located" — asserted, not
confirmed). This ticket supplies the exact verified split and pulls the item out as a standalone,
directly-actionable ticket, matching the pattern already used for that epic's siblings
(A/B/D/E/F/G/H/I). Root cause: `docs/testing/content_migration_test_ownership.md`'s "New Suite
Creation Rules" never stated a domain-nesting convention to begin with — there was no rule to
follow, so nothing was violated so much as never specified.

## Scope
Full investigation and step-by-step plan are in `staging_artifacts/` for this ticket. Concrete
scope:
- `git mv` the 6 directories into `tests/unit/domains/<name>/`.
- Remove the 6 now-redundant explicit CI path entries in `.github/workflows/test.yml`
  (`unit-core-world` and `unit-gameplay` jobs) — the moved content is automatically covered by
  `unit-infra`'s existing `tests/unit/domains` path entry.
- Update `.claude/agents/test-scoper.md`'s Test Directory Map to reflect the real, corrected
  nesting (only once the move actually happens, not before).
- Add a domain-nesting convention rule to `docs/testing/content_migration_test_ownership.md`'s
  "New Suite Creation Rules" so this doesn't recur for new domain subpackages.

## Out of Scope
- `demographics` (no test directory under either layout today) — a coverage gap, not a placement
  question; not created by this ticket.
- Any change to test content/behavior — pure directory relocation.
- Splitting `unit-infra` into an additional CI job, even if its runtime grows — a follow-up
  decision only if the growth proves to be a real problem in practice.

## Acceptance Criteria
- [ ] All 19 `src/domains/` subpackages' tests (18 that currently have any) live under
      `tests/unit/domains/<name>/` — none remain as flat `tests/unit/<name>/` siblings.
- [ ] Pre-move and post-move `pytest --collect-only` counts for the moved content match exactly.
- [ ] `.github/workflows/test.yml` still runs every moved test (from its new location) and
      remains valid YAML.
- [ ] `.claude/agents/test-scoper.md` and `docs/testing/content_migration_test_ownership.md` both
      reflect the corrected structure/convention.

## Related Tickets
- TCK-20260817-CODEBASE-NAVIGABILITY-HYGIENE-EPIC (item 3 extracted from here; epic remains open
  for its other 3 items)
- TCK-20260817-CODEBASE-HEALTH-RESILIENCE-EPIC (parent tracking epic of the wider audit line)
- TCK-20260819-HOTFIX-CI-TEST-DIR-COVERAGE-CHECK (sibling ticket — its completeness check guards
  against a *future* recurrence of this same class of drift; this ticket only fixes the current
  instance)

## Related Docs
- docs/audits/D24_codebase_health_observatory.md (§D, §F — original source finding)
- docs/plans/codebase_navigability_hygiene_epic.md
- docs/testing/content_migration_test_ownership.md
- .claude/agents/test-scoper.md

## Related Stored Artifacts
staging_artifacts/TCK-20260819-STANDARD-DOMAIN-TEST-DIR-NESTING/

## Related Code Areas
- tests/unit/campaigns/, tests/unit/chronicle/, tests/unit/culture/, tests/unit/faction/,
  tests/unit/feature_packs/, tests/unit/optimization/, tests/unit/domains/
- .github/workflows/test.yml

## Assumptions / Open Questions
- Whether `unit-infra`'s CI runtime growth (absorbing ~61 files' worth of tests previously split
  across two other jobs) is meaningful enough to warrant its own job split — not pre-judged;
  measure at implementation time.

## Implementation Notes
(pending)

## Test Summary
(pending)

## Files Changed
(pending)

## Completion Summary
(pending)
