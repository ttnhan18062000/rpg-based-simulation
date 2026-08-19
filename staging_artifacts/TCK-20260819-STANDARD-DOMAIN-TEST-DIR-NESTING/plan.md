---
status: active
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20260819-STANDARD-DOMAIN-TEST-DIR-NESTING
artifact_type: plan
tags: [testing]
---

# Plan — TCK-20260819-STANDARD-DOMAIN-TEST-DIR-NESTING

## Steps

1. **Move the 6 directories.**
   `git mv tests/unit/{campaigns,chronicle,culture,faction,feature_packs,optimization} tests/unit/domains/`
   — one `git mv` per directory so history follows each file individually.

2. **Check for path-relative assumptions inside the moved files.** Grep the 6 directories for
   `Path(__file__).parent` chains, relative `sys.path` manipulation, or any hardcoded string
   containing the old bare path (`tests/unit/campaigns` etc.) before assuming a pure directory
   move is risk-free. `tests/unit/domains/__init__.py` must still import cleanly with 19 nested
   packages instead of 13.

3. **Repo-wide grep sweep** for the 6 exact old path strings (`tests/unit/campaigns`,
   `tests/unit/chronicle`, `tests/unit/culture`, `tests/unit/faction`, `tests/unit/feature_packs`,
   `tests/unit/optimization`) across `docs/`, `tickets/`, `.claude/`, `Makefile`, and any
   `conftest.py` outside the moved dirs. Update any *live* reference (current convention/rule
   text); leave historical references inside `tickets/done/`/`stored_artifacts/`/
   `docs/audits/` untouched — those are point-in-time records, not living state (same rule applied
   throughout this epic's other sub-tickets' downgrade notes).

4. **Update `.github/workflows/test.yml`.** Remove the 6 now-redundant explicit path lines (in
   `unit-core-world` and `unit-gameplay` jobs); `unit-infra`'s existing `tests/unit/domains` entry
   already covers the moved content. Confirm resulting YAML is still valid
   (`python3 -c "import yaml; yaml.safe_load(open('.github/workflows/test.yml'))"`).

5. **Update `.claude/agents/test-scoper.md`'s Test Directory Map** (lines ~13-23) to show
   `domains/` containing all 19 nested subpackages and remove `campaigns`/`chronicle`/`culture`/
   `faction`/`feature_packs`/`optimization` as flat top-level siblings — this is a descriptive map
   of real structure, only correct to update once the move has actually happened (not before,
   which would create doc/code drift in the other direction).

6. **Update `docs/testing/content_migration_test_ownership.md`.** Add a new "New Suite Creation
   Rules" entry stating: domain-subpackage tests (anything with a same-named counterpart under
   `src/domains/`) always nest under `tests/unit/domains/<name>/`, never as a flat
   `tests/unit/<name>/` sibling. Update the Ownership Table's `tests/unit/domains/` row to note it
   now covers all 19 subpackages (18 with tests; `demographics` has none — a separate, out-of-scope
   coverage question, not touched by this ticket).

7. **Run `graphify update .`** (files under `tests/` changed, per CLAUDE.md's Graphify
   Integration rule).

8. **Verify.** See test_plan.md.

## Explicitly out of scope

- `demographics` (no existing test directory under either layout) — a coverage gap, not a
  placement question; not created by this ticket.
- Any change to the *content* of the moved tests — pure directory/path relocation only.
- Splitting `unit-infra` into a 4th CI job even if its runtime grows meaningfully — flagged as a
  follow-up decision if the growth turns out to be a real problem in practice, not pre-committed.
