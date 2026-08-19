---
status: active
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20260819-STANDARD-DOMAIN-TEST-DIR-NESTING
artifact_type: investigation
tags: [testing]
---

# Investigation — TCK-20260819-STANDARD-DOMAIN-TEST-DIR-NESTING

## Origin
User exploratory-question session on the test-base structure, continuing the
`TCK-20260817-CODEBASE-HEALTH-RESILIENCE-EPIC` audit line of work. Item 3 of
`TCK-20260817-CODEBASE-NAVIGABILITY-HYGIENE-EPIC` ("standardize `tests/unit/domains/` vs. flat
domains-subpackage test-dir placement") flagged this as a real inconsistency but explicitly left
it unverified ("coverage exists for all 19 `domains` subpackages, just inconsistently located" —
asserted, not confirmed with an exact list). This ticket supplies that exact evidence and pulls
the item out of Epic J as a standalone, concretely-scoped ticket, matching the pattern already
used for A/B/D/E/F/G/H/I in the same epic tree.

## Finding — the exact split, verified via `git ls-files`

`src/domains/` has 19 subpackages:
```
adventure, campaigns, chronicle, combat_engagement, commitment, cooperation, culture,
demographics, emotion, faction, feature_packs, information, memory, motivation, optimization,
perception, progression, time, world_emergence
```

`tests/unit/domains/` (git-tracked) contains only 13 of them as nested subdirectories:
```
adventure, combat_engagement, commitment, cooperation, emotion, information, memory, motivation,
perception, progression, time, world_emergence
```
(`demographics` has no tests directory at all under either layout — out of scope for this ticket,
a coverage question not a placement question; not touched here.)

The other 6 have their tests as flat siblings directly under `tests/unit/`, not nested under
`tests/unit/domains/`:
```
tests/unit/campaigns/      (17 files)
tests/unit/chronicle/      (5 files)
tests/unit/culture/        (5 files)
tests/unit/faction/        (12 files)
tests/unit/feature_packs/  (5 files)
tests/unit/optimization/   (17 files)
```
Total: 61 files across 6 directories to move.

## CI wiring for the 6 dirs (`.github/workflows/test.yml`, current lines)

- `unit-core-world` job: `tests/unit/feature_packs` (line 43), `tests/unit/culture` (line 44)
- `unit-gameplay` job: `tests/unit/faction` (line 66), `tests/unit/campaigns` (line 69)
- `unit-infra` job: `tests/unit/domains` (line 87, already present), `tests/unit/optimization`
  (line 89), `tests/unit/chronicle` (line 99)

Once nested under `tests/unit/domains/`, all 6 are automatically covered by the `unit-infra` job's
existing `tests/unit/domains` path entry (pytest recurses). The 6 individual explicit entries
become redundant and should be removed, not left as harmless duplicates — a stale explicit path
next to its own parent path is exactly the kind of drift this ticket exists to reduce.

**Side effect on job balance:** `unit-infra` gains ~61 files' worth of tests that
`unit-core-world`/`unit-gameplay` currently run; those two jobs lose the same. Net test count
across all three jobs is unchanged — this is a pure re-homing, not new work — but `unit-infra`'s
wall-clock time will grow somewhat and the other two will shrink. Not expected to be a problem at
current suite size (raised as a Plan-phase check, not pre-judged).

## Downstream references needing updates

1. **`.github/workflows/test.yml`** — remove 6 explicit entries (lines 43-44, 66, 69, 89, 99),
   confirmed above.
2. **`.claude/agents/test-scoper.md`** — its "Test Directory Map" (lines 13-23) lists `campaigns/`,
   `cognition/`, `combat/`, `domains/` etc. as flat siblings with no indication some nest under
   `domains/` — this is a live, agent-facing map an agent would consult before this ticket's fix
   lands, so it must be updated to show the corrected nesting once the directories actually move
   (not before — see Plan).
3. **`docs/testing/content_migration_test_ownership.md`** — the "New Suite Creation Rules" section
   (5 rules) has no rule at all about domain-subpackage placement. This is the actual root cause:
   there was never a stated convention to violate. Needs a new rule stating domain-subpackage
   tests always nest under `tests/unit/domains/<name>/`.
4. No other doc/ticket references the 6 old bare paths as *current, load-bearing* fact (a
   repo-wide grep sweep for the 6 exact path strings is part of the Plan's verification step, to
   catch anything missed here).

## Alternative considered and rejected: flipping to a Domain→Type axis

A generic (non-project-specific) reference on test-suite organization patterns was reviewed
(`tmp/test_base_structure.md`, sourced externally, not derived from this repo) proposing a
"Hybrid" layout for large multi-domain projects: domain-first, type-second nesting
(`payments/unit/`, `payments/integration/`, `payments/contract/`), with cross-domain concerns
pulled into a separate `system-tests/` tree.

This project's real structure is the opposite axis — type-first, domain-second
(`tests/unit/<domain>/`, `tests/integration/<domain>/`) — and already has a de facto
`system-tests/` equivalent (`tests/arena/`, `tests/certification/`, `tests/perf/`, all
cross-domain, all separately owned per `content_migration_test_ownership.md`'s Ownership Table).
Domain ownership here is expressed as a *documentation-level* map over the type-first physical
tree, not via physical domain-first nesting — a different mechanism for the same underlying
principle the generic doc states (domain-specific tests owned by the domain).

**Decision: do not flip the axis.** Three project-specific reasons, none present in the generic
comparison:
1. `.github/workflows/test.yml`'s CI job split is deliberately type-first
   (`unit-core-world`/`unit-gameplay`/`unit-infra`/`integration`/...), tuned for balanced runtime
   across a single shared Python package — not independently-deployable domain modules. A
   domain-first physical tree would require re-deriving every job's path list around domain
   boundaries instead of type boundaries — a much larger, riskier migration than either finding
   in this epic tree actually calls for.
2. `.claude/agents/test-scoper.md` and `docs/testing/content_migration_test_ownership.md` are both
   built around the type-first axis today; flipping it would require rewriting both, not just
   moving files.
3. This isn't a monorepo of separately-ownable packages (the generic doc's "Package/Module Owned"
   and "Bounded Context (DDD)" rows) — it's one deterministic simulation kernel with domain
   subpackages under a single `src/domains/`, sharing one `pyproject.toml`/venv/CI pipeline. The
   generic doc's own caveat on DDD-bounded-context structuring ("overkill for simpler systems")
   applies here.

The single concrete problem this generic doc's "poor domain locality... scattered as the project
grows" downside predicts *did* materialize (the 6 stray domain dirs this ticket fixes) — but the
fix is enforcing consistency **within** the existing type-first axis (this ticket) plus an
automated completeness guard (`TCK-20260819-HOTFIX-CI-TEST-DIR-COVERAGE-CHECK`), not adopting a
different axis wholesale.

## Related
- `TCK-20260817-CODEBASE-NAVIGABILITY-HYGIENE-EPIC` (item 3 extracted from here; epic remains open
  for its other 3 items: `src/lab/workflows.py` split, `mining/` naming investigation,
  `pipeline.py`/`tactical.py` coverage verification)
- `docs/audits/D24_codebase_health_observatory.md` §D, §F (original source finding)
- `TCK-20260819-HOTFIX-CI-TEST-DIR-COVERAGE-CHECK` (sibling ticket; its completeness check, once
  built, is the mechanism that should catch any *future* instance of this same drift — this
  ticket only fixes the current, already-existing instance)
