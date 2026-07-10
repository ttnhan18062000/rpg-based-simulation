---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260710-FEATURE-FLAGS-GUIDE
artifact_type: test_plan
tags: [feature-flags, documentation, claude-md]
---

# Test Plan — TCK-20260710-FEATURE-FLAGS-GUIDE

This is a documentation-only ticket (Out of Scope explicitly excludes any `src/` change). There is no runtime behavior to regress-test with `pytest`. "Tests" here are documentation-consistency checks: frontmatter validation and grep-based content-parity checks, run directly, not via `pytest`.

## Regression Surface

No existing `pytest` suite exercises `docs/` content directly for this ticket's scope — `tests/docs/` (referenced in `docs/README.md`'s Verification section, "All documentation is verified against source code via `tests/docs/`") is the closest thing to a regression surface for documentation/source parity, and should be run to confirm this ticket's edits don't newly violate any existing doc-parity assertion it makes.

- **Unit**: none applicable — no `src/` files are touched.
- **Integration**: none applicable.
- **Docs/content parity** (closest thing to "regression" for this ticket):
  - `tests/docs/` — run in full; this is the standing suite that checks documentation against source code. Confirm it passes both before and after the edit (baseline, then post-edit) so any failure is attributable to this ticket's changes, not pre-existing drift.
  - `tests/integration/test_scenario_feature_flag_defaults.py` — the closest behavioral regression guard for the flag system this guide documents (45 tests, `TCK-20260627-P2E-FEATURE-FLAG-TEST`). Not expected to be affected by a docs-only change, but running it confirms the source-of-truth flag list this investigation used (10 flags, all OFF) is still accurate at Implement/Verify time — i.e., a sanity check that no concurrent change to `feature_flags.py` has landed between Investigation and Verify that would invalidate the new guide's flag table before it's even merged.
  - `tests/integration/scenarios/test_balance_regression.py::test_adventure_routing_defaults_off` — the DEV-002 sentinel test cited (by link) in the new guide. Confirms the guide isn't citing a sentinel that has since been removed or renamed.

## New Tests Required

None. Per the Acceptance Criteria, the only "pass/fail" checks required for this ticket are static/deterministic content checks, not new test functions:

1. **`docs/guides/feature_flags.md` frontmatter validity**
   - Category: documentation validation (not a pytest test)
   - Verifies: AC #1, #6 — file exists, frontmatter is well-formed per the `docs/guides/*.md` convention (matching `simulation_quality.md`/`observability.md`'s actual field set: `title`, `layer`, `authority`, `audience`, `tags` — confirmed via investigation to lack a `status:` field, unlike the generic `docs/` schema in README).
   - Where: verified via `python3 tools/validate_frontmatter.py docs/guides/feature_flags.md`, not a new test file.

2. **10-flag table parity check**
   - Category: content-parity grep, not a pytest test
   - Verifies: AC #1 ("all 10 `ENABLE_*` flags, name-matched 1:1"), AC #5 (`optimization_contract.md`'s table lists exactly the 10 flags in `FeatureFlagManager.__init__`).
   - Mechanism: `grep -oE 'ENABLE_[A-Z_]+' src/domains/optimization/feature_flags.py | sort -u` (10 lines) diffed against `grep -oE 'ENABLE_[A-Z_]+' docs/guides/feature_flags.md | sort -u` and against `grep -oE 'ENABLE_[A-Z_]+' docs/simulation/domains/optimization_contract.md | sort -u` — all three sets must be identical after the edit.
   - Where it should live: not a file — a one-off verification command run at Verify time (see Scoped Pytest Commands section; this is not a pytest command, listed there for convenience of a single "run this at Verify" block).

3. **Stale-citation-zero check**
   - Category: content-parity grep, not a pytest test
   - Verifies: AC #3 exactly as literally specified by the ticket.
   - Mechanism: `grep -rn "v2_intentional_divergences" CLAUDE.md docs/plans/audit_fix_plan.md docs/plans/idea_simq_near_perfect_roadmap.md` must return zero matches (exit code 1) after the edit. Baseline (pre-edit, confirmed by this investigation): CLAUDE.md 2 matches (lines 227, 285), audit_fix_plan.md 2 matches (lines 55, 480), idea_simq_near_perfect_roadmap.md 1 match (line 246) — 5 total occurrences across 3 files to fix.

4. **`D06_longrun_health.md` untouched check**
   - Category: negative-change guard, not a pytest test
   - Verifies: AC #4.
   - Mechanism: `git diff --stat docs/audits/D06_longrun_health.md` must produce no output after the ticket's changes are staged. Confirmed via this investigation that the file has 0 occurrences of the stale string at baseline, so it should never be touched by the citation-fix step regardless.

5. **`docs/README.md` Developer Guides table row check**
   - Category: content-parity grep, not a pytest test
   - Verifies: AC #2.
   - Mechanism: `grep -c "guides/feature_flags.md" docs/README.md` must be ≥1 after the edit (currently 0).

No new `pytest` test function is warranted — there is no runtime behavior being introduced or changed that a unit/integration/architecture-guard test would exercise. If a future ticket later implements `rollout_hardening_rulebook.md`'s `overhaul_features`/`use_*_v2` system in `src/`, *that* ticket would need real tests; this ticket only documents that it currently does not exist.

## Scoped Pytest Commands

```bash
# Confirm no regression in the existing flag-behavior test suite the guide describes
# (sanity-check only — this ticket makes no src/ change, so no failure is expected;
# a failure here would indicate the flag system changed underneath this investigation
# between Investigation and Verify, invalidating the guide's flag table).
pytest tests/integration/test_scenario_feature_flag_defaults.py -m "not slow"

# Confirm the DEV-002 sentinel test the new guide links to still exists and passes.
pytest tests/integration/scenarios/test_balance_regression.py -k test_adventure_routing_defaults_off -m "not slow"

# Confirm the standing documentation/source parity suite still passes after the edit.
pytest tests/docs/ -m "not slow"
```

Never run `pytest tests/` unscoped, per project rule — the above three scoped invocations cover the entire regression surface relevant to this ticket (the flag system's own behavioral tests, plus the docs-parity suite).

## Anti-Drift Test Guards

- **`test_adventure_routing_defaults_off` failing** would mean the OFF-by-default policy the new guide documents (and DEV-002 records) has silently changed — this ticket's guide content would then misdescribe current behavior. Running it at Verify time (not just trusting the investigation's read of `known_limitations.md`) catches this class of drift between Investigation and Verify.
- **`test_scenario_feature_flag_defaults.py`'s 45 tests failing** would mean the 10-flag, all-OFF baseline this investigation and the new guide both assert has drifted — same class of guard, at the scenario-configuration level rather than the single sentinel-flag level.
- **The `ENABLE_*` grep-diff (New Tests Required #2)** is itself the primary anti-drift guard for this ticket's core claim (10 flags, not 7) — it must be re-run at Verify time against the *final* state of all three files (source, new guide, corrected contract table), not just checked once during Investigation, since Plan/Implement could introduce a typo or omission while transcribing the flag list.
- **The stale-citation grep (New Tests Required #3)** guards against a partial fix — e.g. fixing `CLAUDE.md` and `audit_fix_plan.md` but missing one of the two `audit_fix_plan.md` occurrences (line 55 and line 480 are far apart in the file and easy to fix only one of via a naive single-instance find/replace).
- **`git diff --stat docs/audits/D06_longrun_health.md` empty (New Tests Required #4)** guards specifically against scope creep into a file the ticket explicitly excludes — this is the single highest-value anti-drift check in this plan, since the ticket's own Request Summary named this file as a suspect before investigation ruled it out; an implementer re-deriving scope from the Request Summary alone (rather than the ticket's own Out of Scope section) could mistakenly "fix" it.
- Do not let the new guide's `RolloutProfile`/`HardwareClass` section imply `RolloutProfileManager` automatically wires a profile into a live `FeatureFlagManager` (see investigation.md Risk #5) — no automated guard exists for prose accuracy; this is a manual reviewer check at Verify, called out here so it isn't missed.
