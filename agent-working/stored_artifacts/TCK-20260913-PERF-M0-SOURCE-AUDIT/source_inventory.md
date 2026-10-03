---
status: active
layer: performance
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20260913-PERF-M0-SOURCE-AUDIT
date: 2026-10-02
tags: [performance, architecture, investigation]
---

# PERF-M0 Source Inventory and Overlap Disposition

Audit date: 2026-10-02. Base: `origin/main` at `7dfd1349`, branch `perf-optimization-foundation`,
worktree `/home/vboxuser/Work/rpg-perf`. This is the input PERF-M0-T02 cites. Nothing below was
fixed or edited; plan-doc findings (§4) are for the planner session to apply.

Tracked status is `git ls-files` on the index at the audit date. Registry status is membership of
the path in the working-tree `docs/REGISTRY.yaml` (see §5 for why that distinction matters).

## 1. Registered-source inventory

Cited sources: the nineteen paths in `performance_optimization_conflict_approval_review.md` §9, plus
the four in `performance_m0_architecture_governance_epic.md` "References" (one of those, the
`authoritative_pipeline.md` link, repeats a §9 path; the other three are package siblings).

| # | Path | Cited by | Exists | Tracked | In REGISTRY.yaml |
|---|---|---|---|---|---|
| 1 | `docs/brainstorm/codex/system-design/performance_optimization_architecture_proposal.md` | review §9 | yes | yes | **no** (see note A) |
| 2 | `docs/plans/design_enhancement/performance_optimization/performance_optimization_prerequisite_execution_plan.md` | review §9, epic refs | yes | yes | yes |
| 3 | `docs/plans/design_enhancement/design_enhancement_roadmap.md` | review §9 | yes | yes | yes |
| 4 | `docs/plans/design_enhancement/determinism_envelope_epic.md` | review §9 | yes | yes | yes |
| 5 | `docs/plans/design_enhancement/subphase_domain_contracts_epic.md` | review §9 | yes | yes | yes |
| 6 | `docs/plans/design_enhancement/performance_milestones_epic.md` | review §9 | yes | yes | yes |
| 7 | `docs/architecture/performance_optimization.md` | review §9 | yes | yes | yes |
| 8 | `docs/performance/optimization_architecture.md` | review §9 | yes | yes | yes |
| 9 | `docs/engine/authoritative_pipeline.md` | review §9, epic refs | yes | yes | yes |
| 10 | `docs/engine/deterministic_execution.md` | review §9 | yes | yes | yes |
| 11 | `docs/engine/performance_contract.md` | review §9 | yes | yes | yes |
| 12 | `docs/engine/contracts/certification_contract.md` | review §9 | yes | yes | yes |
| 13 | `docs/performance/perf_baseline_policy.md` | review §9 | yes | yes | yes |
| 14 | `src/engine/pipeline.py` | review §9 | yes | yes | n/a (code, note B) |
| 15 | `src/engine/kernel.py` | review §9 | yes | yes | n/a |
| 16 | `src/engine/worker_manager.py` | review §9 | yes | yes | n/a |
| 17 | `src/engine/governor.py` | review §9 | yes | yes | n/a |
| 18 | `src/engine/checkpoint.py` | review §9 | yes | yes | n/a |
| 19 | `tests/perf/test_perf_regression_baseline.py` | review §9 | yes | yes | n/a |
| 20 | `docs/plans/design_enhancement/performance_optimization/performance_optimization_conflict_approval_review.md` | epic refs | yes | yes | yes |
| 21 | `docs/plans/design_enhancement/performance_optimization/system_design_terms_and_concepts.md` | epic refs | yes | yes | yes |

Result: 21 distinct paths, all exist, all tracked; 15 docs are registered; the one unregistered doc
is #1; the six code/test paths are outside the registry's scope by design.

- **Note A.** #1 has valid frontmatter but sits under `docs/brainstorm/`, which
  `tools/generate_registry.py` skips (`_SKIP_DOC_SUBDIRS` includes `"brainstorm"`, line 61). So the
  proposal that the whole program derives from is tracked but never registered, and therefore not
  reachable through registry queries. This is a property of the generator, not a registration
  mistake.
- **Note B.** The registry holds docs and closed tickets only (CLAUDE.md "Graphify Integration").

Cited-but-relocated doc-set: the epic's `system_design_terms_and_concepts.md §§13–14` resolves to
the package copy (#21); the file is not at the location its own text claims (finding F-02).

## 2. Durability status, measured 2026-10-02

Commands run in `/home/vboxuser/Work/rpg-perf` (HEAD `7dfd1349`):

```
$ git ls-files docs/plans/design_enhancement/performance_optimization | wc -l
11
$ git ls-files docs/brainstorm/codex/system-design/performance_optimization_architecture_proposal.md
docs/brainstorm/codex/system-design/performance_optimization_architecture_proposal.md
$ git log --oneline --diff-filter=A -- docs/plans/design_enhancement/performance_optimization/performance_optimization_roadmap.md
2f6b1551 Review + reconcile performance-optimization and render-and-art draft packages (#185)
$ git show HEAD:docs/REGISTRY.yaml | grep -c "design_enhancement/performance_optimization/"
18
```

- The package folder holds **11** tracked files (the ticket said 12; 11 plus the source proposal is
  12 — the ticket counted the proposal). All 11 are in the working-tree registry.
- The source proposal is tracked.
- **C-17 status: RESOLVED** (as expected). The folder and the proposal are tracked since PR #185.
  Of the 18 lines matched in the committed registry, 11 are the package files' own `path:` entries
  (lines 5534–5661) and 7 are closed-ticket `related_code_areas` lines (13221–13241) that cite the
  folder; so `HEAD` already registers all 11 package files.
  Residual: the proposal itself remains unregistered (Note A), which C-17 as written did not cover.

## 3. Reuse / merge / supersede / defer dispositions

Disposition vocabulary: **reuse** (consume as input), **merge** (fold its content into a PERF
ticket), **supersede** (a PERF deliverable replaces it), **defer** (leave alone, revisit at a named
gate). All tickets are recorded only; none were investigated or edited.

### 3.1 Tickets named in the ticket's Assumptions

| Ticket | Tier / state | Disposition | Reason / owner milestone |
|---|---|---|---|
| TCK-20260914-PERF-THRESHOLD-SOFT-GATE-DEFECT | standard, OPEN (todos) | **defer** to M2/M4 under the entry gate | Diagnosed defect: `assert_perf_threshold()` defaults `hard=False`. Making a check blocking changes what RPG-core PRs must pass; roadmap says no soft check becomes blocking until the entry gate lifts. M4 epic already cites it. |
| TCK-20260919-PERF-SCENARIO-METROPOLIS-SPAWN-COLLISION | hotfix, OPEN (todos) | **defer**; M4-T09 depends on it | `build_metropolis_state()` is in `src/perf/scenarios.py`; fix needs a `src/` edit, frozen. M4-T09 must not map a scenario to it until fixed. |
| TCK-20260914-STATE-FINGERPRINT-COST-OBSERVED | standard, OPEN | **merge** (as evidence) into PA-03A call-site inventory; cost numbers **defer** | Report of an observed cost in `AuthoritativeState.fingerprint()`; the measurement is provisional under the entry gate. |
| TCK-20260914-DECISION-TRACE-WRITE-COST-OBSERVED | standard, OPEN | **defer** (M4/M5 candidate evidence) | Observability write cost; belongs to the Gate A baseline, not the foundation slice. |
| TCK-20260914-COOPERATION-FIND-PENDING-OFFER-COST-OBSERVED | standard, OPEN | **defer** (M5 candidate evidence) | Single-domain hotspot; an exact-optimization candidate for Gate A, which cannot start before the entry gate. |
| TCK-20260915-SIMQ-CORPUS-BLIND-TO-SCALE-DEPENDENT-BEHAVIOR | standard, OPEN | **defer**; dependency of M4-T05 | SimQ cannot serve as a gate at ~10 entities. Owned by the SimQ track. |
| TCK-20261001-SIMQ-GRADE-ANCHORS-RED-ON-MAIN-UNREPORTED | standard, INPROGRESS | **defer**; dependency of M4-T05 | In-flight on another track; do not touch. Re-check state before M4-T05. |
| TCK-20260822-STANDARD-SLOW-REGRESSION-CI-JOB-EXIT-CODE-2 | standard, BLOCKED | **defer** | Deliberately parked until the engine re-architecture lands; slow job runs only on push to `main`. |
| TCK-20260821-EPIC-LIVE-MAP-INTEREST-MANAGEMENT | epic, OPEN | **defer / no merge** (ownership boundary, conflict C-12) | C-12 and M5-T08 name this epic as owner of interest-management implementation unless its owner transfers or merges the scope. The performance program only measures serving cost and must not open a second implementation stream. |
| TCK-20260911-WORKER-UTILIZATION-ZERO-WORKERS-DEGRADED-MISTRIGGER | done | **reuse** | Fixed C-03's worker half to `0.0`. PERF-D1 must ratify or revise it; the zero-queue case still reports `1.0`. |

### 3.2 Additional tickets surfaced by the searches

| Ticket | State | Disposition | Reason |
|---|---|---|---|
| TCK-20260627-P1E-DOMAIN-INVENTORY | done | **reuse** as prior art; **supersede** its static table with the PA-05A script | Produced `docs/audits/D19_domain_phase_inventory.md` (pipeline.py:refine() = 38 phases at that time). Counts drift (39 contract / 43–44 AST), so a one-off table is insufficient. |
| TCK-20260614-HASH-SCHEDULER | done | **reuse** as the PA-03A starting point | Added `CanonicalHashScheduler`; roadmap states `BudgetedCanonicalHasher` has no caller outside its module and FULL persistence still hashes directly. PA-03A should reconcile what the scheduler does and does not govern. |
| TCK-20260627-P2F-CANON-HASH-DOC | done | **reuse** | `docs/engine/known_limitations.md` §2.4 documents hash availability by RuntimeMode; input to PERF-D5. |
| TCK-20260518-PERF-REGRESSION-GATE | done | **reuse** | Origin of `PerfRegressionGate`; M2-T01 inventories its clauses against what runs. |
| TCK-20260420-PERF-FOUNDATION | done | **reuse** | Origin of the performance contract, kernel phase timing and `BenchHarness`. |
| TCK-20260518-PHASE-DEPENDENCY-GRAPH | done | **reuse** | Existing dependency/skip scheduling; relevant to PERF-D6 catalog identity. |
| TCK-20260518-PHASE-BUDGET-GOVERNOR | done | **reuse** | Existing per-phase budget logic; relevant to the M3 observability foundation. |
| TCK-20260512-PERF-HARDENING, TCK-20260517-PERF-OPT-HARDENING | done | **reuse** | Earlier hardening layers cited by the P1 docs; no open scope. |
| TCK-20260518-OPTIMIZATION-DOCS | done | **reuse** | Source of the P1 optimization docs (`docs/performance/*`, `docs/architecture/performance_optimization.md`) that the review lists as authority P1. |
| TCK-20260628-E-LONGRUN-REGRESSION | done | **reuse** | The 5000-tick behavioral baseline; evidence for M2-T01. |
| TCK-20260821-EPIC-LIVE-MAP-RENDERING-PERFORMANCE | epic, OPEN | **defer / not related** | Confirmed by reading its Request Summary: browser-side chunked terrain caching and layered entity rendering (`GameCanvas.tsx`); no engine, pipeline or measurement-gate content, and no C-xx conflict names it. |
| TCK-20260818-STANDARD-PERF-THRESHOLD-SOFT-WARNING | done | **reuse** | Origin of the `hard=False` default that the open SOFT-GATE-DEFECT ticket is about; read as history before M2-T01/M4 touch thresholds. |
| TCK-20260818-STANDARD-PERF-SLOW-CI-FIRST-RUN-CALIBRATION | done | **reuse** | First calibration of the performance thresholds against the Slow regression job; context for the soft-warning decision. |
| TCK-20260908-DEGRADED-POLICY-NONURGENT-MOVEMENT-STARVATION | done | **reuse** (PERF-D1) | Wall-clock-driven DEGRADED consequence on behavior; evidence for the Live determinism contract. |
| TCK-20260908-GOVERNOR-DEGRADED-AT-TICK-ONE-EMPTY-WORLD-DISPOSITION | done | **reuse** (PERF-D1) | Parent of the worker-utilization fix; its disposition is the C-03 evidence. |
| TCK-20260907-CAMPAIGN-BRIDGE-FIELDS-STATE-HASH-COVERAGE | done | **reuse** (PERF-D5, PA-03A) | Canonical-hash coverage evidence. |
| TCK-20260902-KNOWLEDGE-CANONICAL-HASH-GAP, TCK-20260902-SOCIAL-CANONICAL-HASH-GAP, TCK-20260903-NAVIGATION-CANONICAL-HASH-GAP, TCK-20260920-TEMPORAL-MODEL-CANONICAL-HASH-SERIALIZATION-GAP, TCK-20260830-HOTFIX-PROGRESSION-DECISION-CANONICAL-HASH-CRASH | done | **reuse** (PERF-D5, PA-03A) | Hash-coverage and serialization gaps closed per component; PA-03A's consumer inventory should state hash coverage is a moving, per-component property. |
| TCK-20260912-OPTIMIZATION-ORPHANED-CAPABILITY-DETERMINATION, TCK-20260912-OPTIMIZATION-BUDGET-MANAGER-MISSING-DETERMINATION, TCK-20260912-OPTIMIZATION-PROVIDER-ENFORCEMENT-MISSING-DETERMINATION | done | **reuse** (M5 candidate menu) | Deleted aged-out orphaned optimization modules (`performance_milestones_epic.md` "Preserved capability ideas"); the deletions, not the code, are the evidence. |
| TCK-20260914-HOTFIX-PERF-METROPOLIS-LONGEVITY-RETIER | done | **reuse** (M4) | Cited as the second confirmed instance in the M4 epic; scenario-tiering precedent. |
| TCK-20260829-SIMQ-PERSISTENCE-BACKPRESSURE-PERF-INVESTIGATION | done | **reuse** (M3/M4 observer cost) | Tick-time persistence/telemetry I/O overhead; evidence for observer-overhead measurement. |
| TCK-20260914-COMBAT-ENGAGEMENT-PERCEIVED-POWER, TCK-20260915-CROSS-FACTION-COMBAT-RARITY-INVESTIGATION (todos) | done / OPEN | **defer / not a PERF ticket** | Cited only as field evidence (combat change moved behavior at 1000 entities) for the SimQ-blindness gap; owned by the combat track. |

### 3.3 Tracking tickets the P1 plans name but nobody created

`TCK-20260825-EPIC-PERFORMANCE-EVOLUTION` (cited in `performance_milestones_epic.md:11`) and
`TCK-20260825-EPIC-SUBPHASE-DOMAIN-CONTRACTS` (cited in `subphase_domain_contracts_epic.md:11`)
exist nowhere under `tickets/`; both docs say "not yet created". Recorded as a finding. Not created
here.

### 3.4 Search queries (repeatable)

**Pass 1, semantic.** `mcp__knowledge-search__search_docs`, hybrid mode, `top_k` 10 unless noted:

1. `performance optimization M0 source audit inventory architecture governance` (top_k 8)
2. `phase timing instrumentation benchmark baseline performance gate threshold`
3. `determinism hash BudgetedCanonicalHasher persistence state hash cost`
4. `resource governor worker utilization zero workers queue capacity pressure`
5. `AuthoritativeApplyPipeline refine phase catalog inventory 39 phases 43 run_phase`
6. `performance contract authority CI-fast scheduled long-run debt harness`

Plus `graphify query "performance optimization source audit"` (only skill and SimQ-corpus tests; nothing new).

**Pass 2, keyword** (added after planner review; the semantic index returns mostly `working_log.csv`
rows and misses open tickets and unusual vocabulary):

- 2a. Every ticket id cited inside the 11 package files plus `design_enhancement_roadmap.md` and
  `performance_milestones_epic.md` (regex `TCK-\d{8}-[A-Z0-9-]*[A-Z0-9]`), located under
  `tickets/{todos,inprogress,done}`: 16 distinct ids.
- 2b. File names in `tickets/todos/` and `tickets/inprogress/` (recursive) matching
  `perf|hash|fingerprint|degraded|governor|worker|baseline|benchmark|determinism` (case-insensitive).
- 2c. File names in `tickets/done/` (recursive) plus the `ticket_id` and `title` columns of
  `tickets/working_log.csv` matching the same regex: 171 distinct ids.
- The 2a ids that exist are dispositioned in §3.1/§3.2; the two that do not exist are in §3.3.

### 3.5 Keyword-pass dispositions (2b and 2c hits not already in §3.1–§3.2)

Open tickets from 2b:

| Ticket | Disposition |
|---|---|
| TCK-20260913-PERF-M0-ARCHITECTURE-GOVERNANCE-EPIC, TCK-20260913-PERF-M0-OWNER-TRIAGE, TCK-20260913-PERF-M0-SOURCE-AUDIT | this program itself |
| TCK-20260929-EPIC-TEST-BASELINE-RELIABILITY | not related ("baseline" means pinned test expectations, not performance) |
| TCK-20260822-HUD-BASELINE-MEASUREMENT | not related (frontend HUD measurement) |
| TCK-20261001-FRONTIER-MARCHES-NARRATIVE-ANCHOR-ZERO-SCORE-REBASELINE, TCK-20261001-SIMQ-UNIT-SELFMODEL-PILOT-ECONOMY-ANCHOR-REBASELINE | defer (SimQ grade-anchor track; relevant only through the M4-T05 dependency recorded in §3.1) |

Done tickets and working-log rows from 2c, by family (every hit falls in one of these lines):

| Family (ids) | Disposition |
|---|---|
| Earlier performance programs: TCK-20260322-PERF_OPT, TCK-20260401-AOA-STABILIZE, TCK-20260401-HARDENING-PERF, TCK-20260402-VALIDATION, TCK-20260417-ARENA-PERF-HARDENING, TCK-20260512-PERF-{COMPLETION,HARDENING,HARNESS-ENHANCEMENT,INVESTIGATION,PROFILES,SCENARIOS,STAGGERED-SCHEDULER,TESTS}, TCK-20260513-PERF-{API-SNAPSHOTS,APPLY-PATH,CADENCE-CORE,CADENCE-INTEGRATION,CI-GUARD,HARDENING,HARDENING-DIRTY-SPATIAL,HARDENING-LOD,PROFILES-TUNING,WORKER-HARDENING}, TCK-20260514-{ENGINE-PERF-HARDENING,PERF-OPTIMIZATION,PERF-PROFILING,PERSISTENCE-OPT}, TCK-20260515-GOV-PERF, TCK-20260516-{ENGINE-PERFORMANCE-PHASE2,FIX-PERF-REGRESSION,PERF-OPTIMIZATION-FINAL}, TCK-20260517-{PERF-OPT-HARDENING,STATE-UPDATE-COMPACTOR}, TCK-20260518-{DOC-CHECKLIST-UPDATE,PERF-REGRESSION-GATE,PHASE-BUDGET-GOVERNOR}, TCK-20260616-DOCS-ARCHIVE-SPECS-PERF-PLANS | **reuse as history** (all done): they built the optimization and gate machinery the P1 docs describe and M2-T01 inventories; no open scope |
| Perf guard and budget fixes: TCK-20260619-FIX-PERF-BUDGETS-RESET, TCK-20260624-{FIX-PERF-BUDGETS,PERF-GUARD-INFRA}, TCK-20260817-STANDARD-PERF-COMBAT-MISSING-SLOW-MARKER, TCK-20260818-HOTFIX-PERF-BUDGET-GUARD-TEST-STALE-RAISE-EXPECTATION, TCK-20260819-CI-NARROW-PATH-FILTERED-JOBS | **reuse** for M2-T01; the last is the origin of the path-filtered `perf-cert-arena` job the entry gate relies on |
| Perf in CI/regression: TCK-20260628-E-LONGRUN-REGRESSION, TCK-20260817-STANDARD-BEHAVIORAL-5K-BASELINE-REFRESH, TCK-20260806-PUSH-SHAPER-PERF-REGRESSION-GATE, TCK-20260806-PUSH-SHADOW-VALIDATION-PERF, TCK-20260806-PUSH-SHADOW-VALIDATION-PERF-PHASE2, TCK-20260808-SIMQ-CORPUS-PERF-BASELINE-INTEGRATION | **reuse** (M2-T01/M4 gate inventory) |
| Bench/measurement scoping: TCK-20260817-RUNTIMEMODE-BENCH-SCOPING, TCK-20260614-CERT-MEMRAY-BUDGET, TCK-20260529-OBS-PHASE20, TCK-20260527-COG-PHASE1-BUDGETS, TCK-20260523-COGNITION-SAFETY-VERIFICATION | **reuse** (M3/M4: RuntimeMode as a measurement dimension, profiling lane) |
| Hash and determinism: TCK-20260419-MA-TASK4-HARDEN-HASHING, TCK-20260627-P2F-CANON-HASH-DOC, TCK-20260902-PLACE-MIGRATION-{RECALIBRATION,STAGE-A-PILOT}, TCK-20260812-DETERMINISM-PARITY-SHADOW-BASELINE-HASH-STALE, TCK-20260817-DETERMINISM-VERIFICATION-GAP-EPIC, TCK-20260818-STANDARD-LONGRUN-DETERMINISM-WATCHDOG-AUDITMODE, TCK-20260401-TEST-STABILIZATION, TCK-20260413-STRAT-REPLAY-DETERMINISM, TCK-20260501-E4-PHASE-ONE, TCK-20260505-HARDENING-DETERMINISM-V2, TCK-20260619-P0-DETERMINISM, TCK-20260713-SIMQ-COGNITION-LOOPDET-NONDETERMINISM, TCK-20260821-NOISE-FILL-DETERMINISM-TEST | **reuse** (PERF-D1/D5 evidence); none has open scope |
| Governor, workers, concurrency: TCK-20260418-RESOURCE-KERNEL-M5, TCK-20260418-RESOURCE-CONCURRENCY-M8, TCK-20260419-MB-TASK3-GOVERNOR-HARDENING, TCK-20260419-MD-TASK2-HARDEN-PROTOCOL-AND-COMMIT-LAW, TCK-20260817-DOC-CONCURRENCY-LIMIT-RATIONALE, TCK-20260614-LIFECYCLE-SUPERVISOR, TCK-20260610-{THREAD-LEAK-CONFTEST,WORKER-SINGLETON-GUARD}, TCK-20260624-FIX-WORKER-SHUTDOWN, TCK-20260818-STANDARD-QUEUEDRAINWORKER-CI-THREAD-LEAK-BISECTION, TCK-20260830-KERNEL-SHUTDOWN-PERSISTENCE-DRAIN-ORDERING-HAZARD | **reuse** (PERF-D1) |
| TCK-20260627-P2N-DEGRADED-FALLBACK | not related (content-source fallback, not pressure semantics) |
| Scale and scenario: TCK-20260807-SCALE-VALIDATION-ENTITY-COLLISION-BUG, TCK-20260821-LIVE-MAP-PERF-VALIDATION, TCK-20260929-RETIRE-SCRIPTS-DIR, TCK-20260928-TEST-SCOPE-MAP-MISSES-TOOLS-SUBPACKAGES | **reuse**: the first is the same stacking pattern as the open METROPOLIS-SPAWN-COLLISION ticket; the live-map one is that program's own measurement; `RETIRE-SCRIPTS-DIR` moved perf scripts into `tools/perf`, where the planned phase-inventory script belongs; the last concerns test scoping of `tools/` packages |
| Doc/skill housekeeping: TCK-20260817-AUDIT-ENGINE-DOCS-DRIFT, TCK-20260822-SCAN-POLICY-DOC-FIX, TCK-20260805-COMMUNITY-SKILL-SWAP-UNDISCLOSED, TCK-20260805-SKILL-GATE-CONVERSION-DECISION | not related (matched on the word "performance") |
| Other-meaning "baseline"/"benchmark" rows: AOA, M1 core freeze, balance baseline, SimQ recalibration and grade-anchor re-baselines, every `*PARITY*BASELINE*` drift hotfix, KGMCP baselines, retrieval and agent-monitoring baselines, codebase-health baseline, mutation baseline, test-lane baselines (e.g. TCK-20260330-AOA-COMPOSITION-COMPLETED, TCK-20260420-M1-CORE-FREEZE, TCK-20260420-MA-BASELINE-ISOLATION, TCK-20260619-E12-BALANCE-BASELINE, TCK-20260630-SIMQ-RECALIBRATE, TCK-20260731-PARITY-INDEX-BASELINE, TCK-20260814-KGMCP-MEASUREMENT-BASELINE, TCK-20260916-HEADROOM-HARM-CHECK-BASELINE, TCK-20260929-CONSERVATION-MUTATION-BASELINE, TCK-20260930-CORE-RPG-TEST-BASELINE-POST-REPAIR) | not related (pinned test expectations or other measurement programs); the SimQ re-baseline family matters only through the M4-T05 dependency |
| Observability baselines: TCK-20260519-SIM-OBS-BASE-LOKI, TCK-20260520-SIM-OBS-{M29-M33,PHASE4-M18}, TCK-20260521-SIM-OBS-M48 | not related (observability analyzers); M3 may cite them as prior art |
| Legacy slug-only working-log rows: epic-16-performance-audit, infra-02-performance-profiling, infra-05-multiprocessing-ai-workers, resource_v2_governor_reactivity_e6_0 | reuse as history (legacy format, not investigated) |

Limitation after the second pass: the regex sees only ticket ids and working-log titles, so a ticket
whose id and title avoid those words is still missed. The list is a superset on purpose;
PERF-M0-T02 may promote entries to "merge" when it builds the matrix.

## 4. Findings for the planner (F-02a, F-02b, F-03 applied by the planner; the rest taken into OWNER-TRIAGE or left as planned deliverables)

Broken citations (cited path does not exist at HEAD `7dfd1349` plus the planner's working-tree
edits). Line numbers are for the current working tree.

| ID | File:line | Cited path | Classification |
|---|---|---|---|
| F-01a | `performance_optimization_prerequisite_execution_plan.md`:64, 233, 245, 258 | `docs/architecture/performance_optimization_decisions.md` | Planned deliverable (PERF-D decision records), not yet created. Not broken if read as a future output; should be labeled "to be created". |
| F-01b | `performance_optimization_prerequisite_execution_plan.md`:66, 507 | `docs/performance/performance_optimization_gate_a.md` | Planned deliverable, as above. |
| F-01c | `performance_optimization_roadmap.md`:241 | `docs/audits/performance/` | Planned output directory; the roadmap itself says the path needs M4 owner approval. |
| F-02a (applied by planner 2026-10-02) | `system_design_terms_and_concepts.md`:93, 629 | `docs/plans/design_enhancement/system_design_terms_and_concepts.md` | **Broken.** The file lives in `.../performance_optimization/`. The "Location retained" row is stale. |
| F-02b (applied by planner 2026-10-02) | `system_design_terms_and_concepts.md`:430 | `tests/unit/perf/test_phase10_cache_invalidation.py` | **Broken.** No such file; nearest real file is `tests/unit/domains/optimization/test_cache_invalidation_policy.py`. Planner to confirm intent. |
| F-03 (applied by planner 2026-10-02) | `performance_optimization_roadmap.md`:126 | `docs/plans/codebase_health/python_code_craft_roadmap.md` | **Unresolved on this base.** The file exists only on branch `python-code-craft` (worktree `rpg-code-craft`), not on `origin/main`. The roadmap's `src/` freeze rule points at a document `main` does not yet contain. |

Other findings:

- F-04: the ticket and plan say the package has 12 files; it has 11 (12 only counting the proposal).
- F-05: `docs/brainstorm/` is a registry-skipped subtree, so the program's source proposal is never
  registered (Note A). Decide whether the epic's "registered-source" wording should cover it.
- F-06: neither named P1 tracking ticket exists (§3.3).
- F-07: the roadmap's live-state count (44 `run_phase()` calls) and the D19 inventory's 38 phases
  are different counted units; confirms PA-05A needs a script, not another table.
- F-08 (the ticket's own open question): `docs/REGISTRY.yaml` is regenerated from the working
  tree, not from git HEAD. At audit time the working-tree and committed registries agreed for the
  package (11/11), but the planner's uncommitted edits to package files would be registered
  whether or not they are ever committed. A general durability gap beyond this ticket.

## 5. Acceptance criteria evidence map

| Criterion | Evidence |
|---|---|
| Inventory table with existence, tracked, registry per doc | §1 |
| Durability status of the package and proposal with command output; C-17 status | §2 (C-17 resolved) |
| Disposition for every surfaced ticket, queries listed, named tickets covered | §3.1–§3.4 |
| Output at the stated path; diff touches only allowed paths | this file; checked in test_plan.md §3 |
