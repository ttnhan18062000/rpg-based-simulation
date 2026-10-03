# Test Architecture — Epic Index

**Status: owner decisions recorded 2026-09-30; epics A–D remain open (see the table).** This folder holds **four epic-tier tickets only**.
Child tickets are created later by the detail planner, not here. This file is deliberately **not**
named `SEQUENCE.md`, because `implement-epic` reads that name as a child-ticket order.

Binding plan: `docs/plans/test_architecture/roadmap.md`. Decisions (2026-09-30): D-R2, D-MF and D-M2
approved with changes; D-P deferred; D-PERF assigned when its trigger fires; D-PR resolved (plan PR #256).

| Order | Epic | Starts when | Status (2026-09-30) |
|---|---|---|---|
| 1 | `TCK-20260929-EPIC-TEST-BASELINE-RELIABILITY` (A) | now | parts done; see the epic |
| 2 | `TCK-20260929-EPIC-TEST-STRUCTURE-SELECTION` (B) | now; its report-dependent criterion needs A's report v0 | part 2 (CI scenario-lane rule, D-R2 approved): implemented; cost record at 18 PRs (23 rows) as of 2026-10-03, lane ran on 7 PRs, see the closure-readiness audit below; the 2026-10-02 state was 8 PRs (13 rows): the job ran and succeeded on #271, #272, #273, #275, #277, was skipped on #274, #276 (Perf covered the scenario tests) and on #278 (docs-only skip at an earlier head; Perf-covers skip at the final head bf468aca4, row added 2026-10-02); criterion 4 part observed (src/progression-only trigger unobserved) |
| 3 | `TCK-20260929-EPIC-TEST-WORKFLOW-FAILURE-HANDLING` (C) | after B's taxonomy doc | criterion 1 met with a caveat (done-checker advisory, PR #268), criterion 2 not met (partially demonstrated: checklist ran only with an added prompt sentence; 2026-10-02 run with the JS prompt text verbatim plus an appended output-key sentence: test-quality remark observed without a checklist sentence, application to changed tests not demonstrated); criterion 4 open, criterion 5 met (text only); part 5 and 6 text landed (part 5 oracle rule and part 6 quarantine text land in this batch, text only) |
| 4 | `TCK-20260929-EPIC-CORE-RPG-TEST-PILOT` (D) | minimum usable workflow: A report v0 + A known-leak fix (≥ provisional) + B taxonomy doc + C test-plan fields + C triage procedure | open: real-pipeline gap closed by capability 7 (with interventions); CI scenario execution recorded from this change's own CI |

A and B can run in parallel. D does not wait for optional parts of A–C.

**Hold rule:** `HOLD` items may be described by detail planners, but no implementation child ticket
may be activated and no gated work may start until the owner approves the named decision. Ungated
work is independently startable. **No HOLD is open as of 2026-09-30**; D-P (deferred) and D-PERF
(trigger-based) gate nothing in A–D. Approval lifts a HOLD; it does not close an epic.

## Closure-readiness audit (2026-10-03, base `origin/main` c0980e27a)

An audit only: **no epic status text was changed by this table.** The two documentation defects the audit found (C3's parallel triage list, B1's dead link) were fixed in the same change, and B1 and C3 are classed after that fix. Each class was
re-checked against the files, tools and tests on `c0980e27a`, not copied from the epics' own status text. Method: the
`search_docs` MCP server was down, so evidence was gathered by direct grep, read and scoped pytest (a read-only
subagent covered A1-A6, B1-B3, B5, C3 and D1-D5, and I spot-checked its dead-link, parallel-triage-list and
escaped-defect-tag claims; B4, C1, C2, C4 and C5 I checked myself). Scoped test runs passed. Anything that needs
GitHub or CI is marked **unverified here**. Classes: MET / MET-with-caveat / NOT MET / NOT EXERCISED (the rule or
tool exists, no real ticket or run has exercised it).

| Criterion | Class | Evidence pointer |
|---|---|---|
| A1 report regenerates identically; explicit states | MET | `tests/unit/tools/test_core_rpg_report.py` (identical output; `no-junit-artifact`, `not-run`, outcome distinct; `no-coverage-artifact`); 115 passed across the report/impact/selection tests |
| A2 report states v0 limits | MET | `V0_LIMITS` in `tools/test_architecture/core_rpg_report.py` (names the JUnit-upload limit, now the three jobs split from `api-tools`) |
| A3 known leak: 0 failures in the 7 nodes | MET-with-caveat | `tests/unit/core/test_catalog_registry_isolation.py` plus `tests/unit/domains/progression` (35 passed); autouse reset from #259 (`f2e4b578f`). Combined-suite and random-order results were **not re-run in this audit**; last evidence: `tickets/done/TCK-20260929-CATALOG-REGISTRY-TEST-LEAK.md`; the random-order check used a private seeded scratch plugin, not committed; 11 other combined-run failures remain (baseline report "Remaining unknowns" 1) |
| A4 tracked-file write | MET-with-caveat | `generate_mechanism_verification_view.py --check` exits 0; `tests/unit/tools/test_mechanism_registry.py` (92 passed with the baseline-records test) leaves `git status` clean. The optional advisory guard was not built; other tracked-file writers remain (`docs/REGISTRY.yaml`, `tickets/working_log.csv`) outside the named file |
| A5 effectiveness: mutation record, `escaped-defect` tag | MET-with-caveat | `tests/mutation/baselines/src_core_conservation.json` and `_v2.json`; mutation layer and "Escaped defects" in the report; tag at `registries/tag_registry.jsonl:84`; zero-as-real-count rests on `test_escaped_defects_count_per_month_and_zero_is_real`. `mutmut` is not a project dependency, so the run is not reproducible from a clean install; v1 goes stale 2026-10-30 |
| A6 remaining unknowns listed | MET | `docs/testing/core_rpg_test_baseline_2026-09-30.md` "## Remaining unknowns" (8 items, order dependence outside the verified set is item 2) |
| B1 taxonomy doc | MET | `docs/testing/test_taxonomy.md` §5 (five levels with harness, oracle, placement, cadence, "Reported as"). The dead `README.md:112` link to `docs/testing/v2_test_taxonomy.md` was found by this audit and fixed in the same change (now `docs/testing/test_taxonomy.md`) |
| B2 domain/level marker advisory check | MET | `tests/unit/tools/test_marker_check.py`; `python -m tools.test_architecture.marker_check` runs advisory, exit 0 (needs `PYTHONPATH=.` as a bare script) |
| B3 worked examples, replay-diff scope | MET-with-caveat | `tests/mechanic_scenarios/synthetic_examples/test_scenario_helper_examples.py` (labelled synthetic); `tests/unit/tools/test_replay_diff.py` asserts `outside-verified-scope` (11 passed). No confirmed-stable example exists; the declared lane's own CI run **unverified here** |
| B4 scenario-lane routing and measured cost | NOT MET | Epic B cost record: 18 PRs, 23 rows, but the lane ran on **7 PRs** (34-52 s); the `src/progression/**`-only trigger is unobserved in CI; the cost summary was shared on 2026-10-03 with `rpg-feature-planning` and `agent-working-design` (sent, no reply recorded). Rule-level evidence only: `tests/unit/tools/test_scenario_lane_paths.py::test_src_progression_only_routes_to_the_dedicated_job` (against the live `PERF_RE`; not CI-observed) |
| B5 impact report | MET | `python -m tools.test_architecture.impact_report --paths src/progression/foo.py src/core/state.py src/zzz_unmapped/x.py` gives domains with reasons and `impact-unknown (unmapped-src-path)`; `tests/unit/tools/test_impact_report.py` (all five sample classes) passed |
| C1 test-plan fields checked by done-checker | MET-with-caveat | `tools/gate_checks/done_checker_static.py` (`test_plan_proof_fields` advisory, WARN only, never blocking); `tests/tools/test_proof_plan_advisory.py`. Ran once inside a real pipeline; pilot D1's `test_plan.md` was checked afterwards by hand |
| C2 checklist runs on changed tests, unprompted | NOT MET | Run 1 (`TCK-20260914-BOSS-KINDS-OBSERVABILITY-CONSTANT-DRIFT`) partially demonstrated and confounded; the schema field and read-check tool landed (#282); run 2 is **blocked** on an available test-changing ticket (Epic C criterion 2 record) |
| C3 one triage document, others link to it, drill | MET | `docs/testing/regression_policy.md` §13 (§13.1 evidence record, §13.2 classes); drill table in `stored_artifacts/TCK-20260930-TEST-PLAN-PROOF-FIELDS-AND-TRIAGE-PROCEDURE/investigation.md` (one real case, the Epic A leak, plus synthetic cases). `docs/guides/delivery_process.md:258` links §13. This audit found that `docs/guides/testing.md` kept its own parallel triage list and linked `regression_policy.md` only generically; that list was replaced in the same change with a pointer to §13, so the guide now links the single procedure |
| C4 expectation change shown doc/ledger-first | NOT EXERCISED | Rule text in `docs/testing/regression_policy.md` §13.5; no ticket has exercised it (the boss-kinds ticket moved no fixture, hash, baseline or scorer) |
| C5 bounded quarantine text | MET | `docs/testing/regression_policy.md` §6.1 ("policy text only", nothing quarantined, no enforcement tooling built); text-only by design |
| D1 pilot capability demonstrations with artifacts | MET-with-caveat | `docs/testing/core_rpg_test_pilot_2026-09-30.md` capability table (caps 1-8); pilot artifacts tracked under `stored_artifacts/TCK-20260930-CORE-RPG-PILOT-NODE-CHARGE-ACCOUNTING/pilot/`; D1's 5 tests pass. Cap 5 is an injected drill, not a real failure; the only CI run id cited (36810173881) was **not cross-checked** |
| D2 oracle-review not claimed | MET | Pilot report row 2b: "Not demonstrated; no claim is made" |
| D3 established on a real, stable surface | MET-with-caveat | Report Result says "established" for component demonstrations; surface stability was confirmed by a scope-level read and a relayed feature-team confirmation, not a line audit. Capability 8 (progression second surface) is **blocked**, not exercised |
| D4 per-intervention review | MET-with-caveat | "Per-intervention review" table in the pilot report (keep / revise / inconclusive with measurements); cost is "inconclusive" for the Proof Plan and scenario-lane rows because the real-pipeline run was hand-orchestrated |
| D5 shortfalls fixed or filed | MET | `TCK-20260930-IMPACT-REPORT-ECONOMY-CORE-OWNERSHIP-AND-DECLARED-MARKERS` and `TCK-20260930-CORE-RPG-REPORT-PARITY-TEST-PATH-PRESENCE` with before/after artifacts, in `tickets/done/` |

**What closes the folder (remaining blockers only):**
- **B4**: the lane has run on 7 PRs against "about 10", and the `src/progression/**`-only trigger is unobserved in CI. The user decides whether the rule-level test may stand in for an observed run and whether 7 lane runs are enough. The cost summary has been shared (2026-10-03), so that part of the criterion is done.
- **C2**: needs a real test-changing pipeline run meeting the recorded protocol. Run 2 is blocked until a test-changing ticket outside decision 7's parked set exists.
- **C4**: needs a ticket that changes an expectation and shows the document/ledger change first (or an escalation record).
- **Fixed in this change (found by this audit):** `docs/guides/testing.md`'s own triage list now points to `regression_policy.md` §13, and the dead `README.md:112` taxonomy link now points to `docs/testing/test_taxonomy.md`. Remaining caveat, not a criterion: A3's combined-suite and random-order results were not re-run in this audit.

**Counts (21 criteria):** MET 10 (A1, A2, A6, B1, B2, B5, C3, C5, D2, D5); MET-with-caveat 8 (A3, A4, A5, B3, C1, D1, D3, D4); NOT MET 2 (B4, C2); NOT EXERCISED 1 (C4).
