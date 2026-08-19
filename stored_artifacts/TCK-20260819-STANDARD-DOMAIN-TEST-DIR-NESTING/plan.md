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

2. **Check for path-relative assumptions inside the moved files, and fix the one confirmed hit.**
   Grep the 6 directories for `Path(__file__).parent` chains, relative `sys.path` manipulation, or
   any hardcoded string containing the old bare path (`tests/unit/campaigns` etc.) before assuming
   a pure directory move is risk-free. **A real, confirmed regression exists and must be fixed as
   part of this step, not merely detected**:
   `tests/unit/campaigns/test_campaign_state.py:290` (`test_campaign_state_module_has_no_engine_imports`)
   uses `Path(__file__).parent.parent.parent.parent / "src" / "domains" / "campaigns" /
   "state.py"` — 4 `.parent` hops resolve from the *pre-move* location
   (`tests/unit/campaigns/...`) to repo root. After nesting one level deeper under
   `tests/unit/domains/campaigns/`, this must become 5 `.parent` hops, or it resolves to
   `tests/src/domains/campaigns/state.py` (does not exist) and the test fails at runtime, not at
   collection — `pytest --collect-only` counts alone (Acceptance Criterion #2) will NOT catch
   this; only a full test *execution* run does (see test_plan.md / Step 8). Confirmed via a real
   `git mv` + full run in an isolated worktree during Review: this file is the *only*
   `Path(__file__)`-chain hit across all 6 directories. The 4 hits of the old bare path string
   inside file-header docstring comments (`test_campaign_state.py`, `test_campaign_orchestrator.py`,
   `test_narrative_ledger.py`, `test_chronicle_compiler.py`) are cosmetic path references in
   comments, not executable code — update them for accuracy but they carry no correctness risk.
   `tests/unit/domains/__init__.py` is empty and needs no changes — this repo's `pyproject.toml`
   uses pytest's default import mode with `pythonpath=["."]`, so no package registration step is
   needed for the 6 newly-nested subpackages (confirmed via a real `pytest --collect-only`
   before/after comparison in the Review worktree: 713 collected both times, unchanged).

3. **Repo-wide grep sweep** for the 6 exact old path strings (`tests/unit/campaigns`,
   `tests/unit/chronicle`, `tests/unit/culture`, `tests/unit/faction`, `tests/unit/feature_packs`,
   `tests/unit/optimization`) across `docs/`, `tickets/`, `.claude/`, `Makefile`, and any
   `conftest.py` outside the moved dirs. **`docs/parity_ledger/*.yaml` is an explicit, high-priority
   in-scope target for this sweep, not an afterthought** — confirmed via Review: ~45 live
   `test_path` citations exist across 8 shard files (`faction.yaml` ×13, `social_narrative.yaml`
   ×18, `infrastructure.yaml` ×6, `world_dynamics.yaml` ×2, `progression.yaml` ×3,
   `strategic_cognition.yaml` ×1, `substrate.yaml` ×1, `combat_movement.yaml` ×1), including **two
   P0 entries** (`SUB-383`, `COMB-310`) whose `test_path` field is literally
   `tests/unit/optimization/test_movement_candidate_selector.py` — per CLAUDE.md, P0 entries
   require a passing `test_path`, so these must be updated to the new nested path in the same
   commit as the `git mv`, not left stale. Also update the live citations found in
   `docs/optimization_audit_ledger.md`, `docs/logic_checklist_exhaustive.md`,
   `docs/simulation/domains/chronicle_contract.md`, `docs/guidelines/design_patterns.md`,
   `docs/guidelines/intentional_divergences.md`, `docs/performance/optimization_invariants.md`,
   `docs/engine/candidate_selection.md`, `docs/engine/authoritative_apply_contract.md`, and
   `docs/plans/codebase_navigability_hygiene_epic.md`. Leave historical references untouched in
   `tickets/done/`, `stored_artifacts/`, `docs/audits/`, and `docs/archive/**` (the last one
   confirmed during Review to contain old-path hits that are historical, same treatment as
   `docs/audits/`) — those are point-in-time records, not living state (same rule applied
   throughout this epic's other sub-tickets' downgrade notes). `docs/REGISTRY.yaml` needs no
   manual edit — it is auto-regenerated at Finalize.

4. **Update `.github/workflows/test.yml`.** Remove the 6 now-redundant explicit path lines (in
   `unit-core-world` and `unit-gameplay` jobs); `unit-infra`'s existing `tests/unit/domains` entry
   already covers the moved content. Confirm resulting YAML is still valid
   (`python3 -c "import yaml; yaml.safe_load(open('.github/workflows/test.yml'))"`).

5. **Update `.claude/agents/test-scoper.md`'s Test Directory Map** (real current lines 19-30, not
   "~13-23" — re-verify the exact range at implementation time since this doc may have shifted).
   Of the 6 moved names, only `campaigns` (line 22) and `optimization` (line 26) currently appear
   as flat top-level entries in the map today — `chronicle`, `culture`, `faction`, `feature_packs`
   are already absent from it (a pre-existing incompleteness in the map, not introduced by this
   ticket, and not a blocker to fix here since removing 2 real stale entries and ensuring
   `domains/` lists all 18 nested-with-tests subpackages is still the correct end state). Show
   `domains/` containing all 18 nested-with-tests subpackages (19 total minus `demographics`,
   which has no test directory). This is a descriptive map of real structure, only correct to
   update once the move has actually happened (not before, which would create doc/code drift in
   the other direction).

6. **Reconcile with `docs/testing/content_migration_test_ownership.md`'s already-committed rules
   6 and 7 — do NOT add a duplicate rule.** A prior commit on this same branch
   (`92b6f02e`, made before the `git mv` itself landed) already added New Suite Creation Rules #6
   (domain-nesting convention) and #7 (test.yml wiring rule) to this doc, phrased in past tense
   ("fixed by TCK-20260819-STANDARD-DOMAIN-TEST-DIR-NESTING") even though the move hadn't happened
   yet at commit time. Implement must **verify these two rules' wording is now accurate** (it
   already is, since Steps 1-4 make the past-tense claim true) rather than adding a third,
   duplicate rule — read the doc first and confirm before touching it. Separately, this doc's
   **Ownership Table has no `tests/unit/domains/` row at all today** — the plan's original
   instruction to "update" that row was wrong; **add a new row** for `tests/unit/domains/`
   (marker: `unit`; Owns: all 18 domain-subpackage suites with tests, listing the 6 newly-nested
   plus the 12 already-nested; `demographics` has no test directory — a separate, out-of-scope
   coverage question, not touched by this ticket).

7. **Run `graphify update .`** (files under `tests/` changed) **and `make knowledge-index-update`**
   (files under `docs/` changed by Steps 3 and 6 — required per CLAUDE.md's "After Work" rule,
   not optional).

8. **Verify.** See test_plan.md.

## Explicitly out of scope

- `demographics` (no existing test directory under either layout) — a coverage gap, not a
  placement question; not created by this ticket.
- Any change to the *content* of the moved tests — pure directory/path relocation only.
- Splitting `unit-infra` into a 4th CI job even if its runtime grows meaningfully — flagged as a
  follow-up decision if the growth turns out to be a real problem in practice, not pre-committed.

## Unresolved Questions

- Whether `unit-infra`'s CI runtime growth (absorbing ~61 files' worth of tests currently split
  across `unit-core-world`/`unit-gameplay`) is meaningful enough to warrant a 4th CI job — not
  pre-judged; measure the job's real wall-clock time after Step 4 lands and report it in
  Implementation Notes, but do not act on it beyond reporting (a job split is explicitly out of
  scope for this ticket per the section above).
- Minor: investigation.md's summary prose says "13" domain subpackages are already correctly
  nested under `tests/unit/domains/`, but its own enumerated list names only 12 — the discrepancy
  traces to `tests/unit/domains/__pycache__/` being counted as a 13th entry by directory listing,
  which is not a real domain subpackage. Does not change scope (12 nested + 6 flat + 1
  no-test-dir `demographics` = 19, matching `src/domains/`'s real count) — flagged for the
  investigation.md record, not a blocking ambiguity.
