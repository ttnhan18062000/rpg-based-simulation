---
status: active
layer: engine
authority: P2
audience: agent
artifact_type: audit
tags: [documentation, engine, architecture]
---

# D25 — Engine Docs Drift Audit

## Audit Profile

| Axis | Value |
|---|---|
| **Subject** | `docs/engine/`, `docs/architecture/`, `docs/performance/` |
| **Total surface** | 110 files (`find docs/engine docs/architecture docs/performance -name '*.md' \| wc -l`) — supersedes the originating ticket's own "~102" estimate; the gap is mostly `docs/engine/matrices/` (~21 files), which the ticket's own Related Code Areas list never named |
| **Depth of this audit** | 16 files reviewed at D17 depth (3-5 verifiable claims/doc, independently re-verified against source during Plan/Implement); remaining ~94 files given a lighter existence/self-consistency pass only |
| **Method** | code-read + review, following `docs/audits/D17_documentation_currency.md`'s format and depth precedent |
| **Audit date** | 2026-08-21 |
| **Origin** | TCK-20260817-AUDIT-ENGINE-DOCS-DRIFT |

## Methodology

This audit deliberately does not claim exhaustive coverage of the 110-file surface. It covers
16 files at D17's own depth — comparable to or exceeding D17's own 9-doc sample — because these
are the broad, cross-cutting narrative docs (kernel loop, pipeline, architecture overview,
performance/hardware classification, project-wide contracts) where all four known contradictions
this audit was commissioned to investigate actually live. The remaining ~94 files, concentrated in
`docs/engine/contracts/` (34 files) and `docs/engine/matrices/` (~21 files), are narrower
single-topic contract docs with lower prior probability of cross-doc narrative contradiction; they
received only an existence/self-consistency pass (see "Remaining Files" below), not full D17-depth
fact-checking. A directory-scoped follow-up is recommended, not filed, to close that gap (see
"Recommended Follow-Up").

### Staleness Classification (per D17's convention)

| Status | Meaning |
|---|---|
| `current` | Claim verified against source code — correct |
| `stale` | Claim contradicts current source code with specific evidence |
| `uncertain` | Claim is qualitative, or numeric constants exist but were not traced to source |
| `duplicate` | Doc independently restates content owned by another canonical doc, rather than cross-linking |
| `contradictory` | Doc directly conflicts with another individually-authoritative doc |

## 16-Doc Classification Table

| Doc | Classification | Evidence |
|---|---|---|
| `docs/engine/kernel.md` | current (canonical) | 7-phase list at lines 21-27; canonical doc for phase count/names |
| `docs/engine/architecture.md` | **contradictory** | §2 "6-Phase" table with fabricated GOVERNANCE/PACKETIZATION phases (`docs/engine/architecture.md:47`, table rows 53-58) — neither is a real phase in `src/engine/kernel.py`'s 7-phase sequence. Also §5 hardware-class inversion (see "Known Contradictions" #3). |
| `docs/engine/README.md` | **stale (2 claims)** | Line 13 "6-phase orchestrator (Init, Governance, Scheduling, Packetization, Resolution, Persistence)"; line 14 "17-phase refinement sequence" — both fixed by this ticket (see Files Changed) |
| `docs/engine/contracts/simulation_kernel_contract.md` | current (phase count) / **uncertain (§9)** | Phase list correct (lines 27-33); §9 has 3 stale non-goal bullets contradicted by real scheduler/governor/broker code — recorded as unconfirmed hypothesis, not resolved (see "Known Contradictions" #4) |
| `docs/engine/contracts/minimal_kernel.md` | current | §9 Non-Goals (lines 52-56) correctly scoped to the single-threaded minimal kernel; source of the §9 hypothesis, not itself stale |
| `docs/engine/authoritative_pipeline.md` | current | States "37 phases," matching `tests/agent_orchestration_codex_adapter/test_agents_md_generation.py:18`'s own passing assertion; already fixed by TCK-20260817-STANDARD-AGENTS-MD-PIPELINE-PHASE-COUNT-DRIFT |
| `docs/engine/contracts/certification_contract.md` | current (canonical for hardware class) | §3 binary AND-rule, cross-linked by `perf_baseline_policy.md`'s own callout box |
| `docs/engine/performance_contract.md` | uncertain | Not independently re-verified beyond an existence check; noted as such, not overclaimed |
| `docs/engine/contracts/worker_contract.md` | current | Correctly documents bounded worker-pool concurrency; not the stale outlier in the concurrency contradiction |
| `docs/engine/project_lawbook.md` | current (canonical for pillar list) | Master pillar-list source |
| `docs/engine/project_lawbook_m10.md` | **duplicate** | Says "See project_lawbook.md for full law text" but independently restates a different 5-item pillar list instead of cross-linking only — a newly-found instance of the same drift class, not fixed (out of scope) |
| `docs/architecture/simulation_watchdog.md` | current | Already matches `src/observability/watchdog.py`; Epic C's roadmap description of it as broken is stale history — no work scheduled against it |
| `docs/performance/perf_baseline_policy.md` | current (has its own defer-callout) | §2.2 table + existing `> Known conflict, not resolved here` box at lines 30-35 |
| `docs/performance/simq_isolation_overhead.md` | current | Worked numeric example independently confirms the hardware-class conflict |
| `docs/guides/simulation.md` | **stale (2 claims), now fixed** | Lines 19-20 same 6-phase/Governance/Packetization framing (still stale, deferred to the phase-count seed ticket); line 26 cited nonexistent `src/engine/authoritative_pipeline.py` — corrected to `src/engine/pipeline.py` as part of this ticket (Step 7) |
| `CLAUDE.md` | **contradictory (1 line), fixed; current (1 line), untouched** | Line 258 "6-phase deterministic loop... Packetization" was stale, fixed by this ticket; line 259 "37-phase refinement sequence" was already correct — left untouched |

## Remaining Files (existence/self-consistency pass only)

`docs/engine/contracts/` (34 files), `docs/engine/matrices/` (~21 files), plus the remaining
top-level `docs/engine/`, `docs/architecture/`, and `docs/performance/` files not in the table
above (~94 files total), were checked only for (a) file existence matching any
manifest/registry reference and (b) no internal self-contradiction spotted on a single
read-through — they were not cross-doc fact-checked at D17 depth. This is stated plainly as a
lighter pass, not a gap being hidden — see "Recommended Follow-Up" below for how this gap is
proposed to be closed.

## Known Contradictions

### 1. Concurrency contradiction

`docs/engine/kernel.md:55` ("Concurrent Collection: the Deliberation phase is the only window
for parallel execution") vs. `docs/engine/contracts/simulation_kernel_contract.md:57` ("No
concurrency or parallel execution"). Both `status: active, authority: P1`. Code
(`src/engine/worker_manager.py`, `ThreadPoolExecutor`/`ProcessPoolExecutor`) matches kernel.md, not
simulation_kernel_contract.md — `simulation_kernel_contract.md` §9 is the stale outlier.

**Resolved-by-cross-reference, not re-fixed here.** Owned by
`TCK-20260817-FIX-CONCURRENCY-DOC-CONTRADICTION` (status `OPEN`,
`tickets/todos/kernel-concurrency-design-review/`). See also D17 (`TCK-20260618-AUDIT-D17-DOCS`)
and P0-DOC-REPAIR (`TCK-20260619-P0-DOC-REPAIR`), which previously fixed kernel.md's first
dual-phase-table contradiction — this concurrency contradiction is a different, still-open issue
in the same area.

### 2. Phase-count contradiction

`docs/engine/architecture.md:47` and (until this ticket's edits) `docs/engine/README.md:13` and
`CLAUDE.md:258` all narrated a fabricated 6-phase loop (Init, **Governance**, Scheduling,
**Packetization**, Resolution, Persistence) against the real 7-phase loop (INIT, SCHEDULING,
COLLECTION, RESOLUTION, CLEANUP, ADVANCEMENT, PERSISTENCE) correctly stated in `kernel.md:21-27`
and `simulation_kernel_contract.md:27-33`.

**Resolved-by-cross-reference for `architecture.md` (core fix deferred), directly fixed for two
new-evidence folds by this ticket:**
- The core `architecture.md` contradiction is owned by
  `TCK-20260817-FIX-PHASE-COUNT-CONTRADICTION` (status `OPEN`, same folder) — not re-fixed here.
- `docs/engine/README.md`'s two stale lines (the 6-phase framing at line 13, and an independent
  stale "17-phase" pipeline claim at line 14) are fixed directly by this ticket, since they are
  newly-found evidence for the same contradiction class, not previously named by either seed
  ticket.
- `CLAUDE.md:258`'s one-line kernel.md summary (also 6-phase/Governance/Packetization) is fixed
  directly by this ticket — a previously-unflagged fourth live instance of the phase-count
  contradiction, found in a P1-adjacent file every agent reads on every session. `CLAUDE.md:259`
  (the adjacent pipeline-phase-count row) was already correct and is untouched.
- `docs/guides/simulation.md:19-20`'s same 6-phase/Governance/Packetization framing remains stale
  and is deferred to `TCK-20260817-FIX-PHASE-COUNT-CONTRADICTION`'s scope, consistent with the
  other satellite docs. Only its separate `authoritative_pipeline.py` path citation (line 26) was
  fixed by this ticket (see "Doc-Path-Existence Check" below) — that is an existence-check fix, not
  a phase-count prose fix.

See D17 (`TCK-20260618-AUDIT-D17-DOCS`) and P0-DOC-REPAIR (`TCK-20260619-P0-DOC-REPAIR`) for the
first occurrence and first fix of this same fabricated-name pattern in `kernel.md` itself.

### 3. Hardware-class conflict (OBSISO, plus a newly-found third taxonomy)

`docs/performance/perf_baseline_policy.md:30-35` already carries a
`> **Known conflict, not resolved here**` callout box cross-linking
`docs/engine/contracts/certification_contract.md` §3 and
`docs/performance/simq_isolation_overhead.md`'s own worked numeric example, per
`TCK-20260702-OBSISO-ISOLATION-PROOF`. **That existing box already satisfies the "formally defer"
requirement** — this audit only adds a cross-reference to it, no new callout box was needed there.

**Newly found by this audit, not previously flagged anywhere:** `docs/engine/architecture.md:88-93`
§5 "Performance Monitoring" defines a *third*, independently-drifted hardware-class taxonomy that
does not merely disagree on thresholds but **inverts the letter-to-capability mapping** relative to
both other docs — `certification_contract.md` §3 and `perf_baseline_policy.md` §2.2 both make Class
A the *most* powerful tier (≥16 cores/≥32GB, "High-Performance Server"), while `architecture.md`
makes Class A the *least* powerful ("Low-Power," 10 TPS) and Class C the most powerful. This is
more severe than the OBSISO conflict (a threshold disagreement between docs that agree on
direction) and was found by directly reading `architecture.md` during this audit. A `> **Known
conflict, not resolved here**` callout box matching `perf_baseline_policy.md`'s convention has been
added immediately after the §5 table in `docs/engine/architecture.md`, citing this ticket
(TCK-20260817-AUDIT-ENGINE-DOCS-DRIFT) and cross-linking `TCK-20260702-OBSISO-ISOLATION-PROOF`. Not
fixed here — pending owner decision on which mapping is canonical.

### 4. `simulation_kernel_contract.md` §9 broader staleness (unconfirmed hypothesis)

All three named §9 non-goal bullets are contradicted by real, actively-used source code:

- *"No scheduler optimization"* — `src/engine/scheduler.py:33`'s `DeterministicScheduler.select_work()`
  implements LOD gating (`LODService.should_execute()`, line 49) and cadence-based gating
  (`should_run()`, `cadence.strategic_intelligence`).
- *"No adaptive degradation"* — `src/core/governance.py:8-16` defines `class RuntimeMode(IntEnum)`
  with the ladder `NORMAL=0, CONSTRAINED=1, DEGRADED=2, SURVIVAL=3`, driving
  `GovernorPolicy.from_mode()` (`src/engine/policy.py`) — a fully-built, actively-used adaptive
  degradation system, not a stub.
- *"No external event brokers"* — `src/simulation_quality/feed.py` and `worker.py` implement a real
  Redis-backed `QUALITY_FEED_MODE=broker` mode (`QualityFeedMode.BROKER`, `broker_url`,
  `QualityWorker`), measured and gated by `docs/performance/simq_isolation_overhead.md`'s own "(c)
  broker" column.

**Supporting but circumstantial evidence for one possible explanation:**
`docs/engine/contracts/minimal_kernel.md` §9 "Non-Goals" (lines 52-56) states nearly the same
concept set (concurrency, adaptive-degradation/governor, scheduler-optimization) for the
explicitly-scoped single-threaded minimal kernel (§2: "Single-Threaded: All authoritative changes
occur sequentially in one process"). The wording/concept overlap is *consistent with* §9 having
been copied or derived from `minimal_kernel.md`'s Non-Goals and never re-scoped when
`simulation_kernel_contract.md` grew to describe the full production kernel — but it is equally
possible `simulation_kernel_contract.md` was always meant to be an aspirational/idealized contract
that was never updated as these three features were added, independent of `minimal_kernel.md`'s
existence.

**This remains an unconfirmed hypothesis. Needs owner confirmation before any fix — do not
silently adopt the minimal_kernel.md-scope reading.** No edit to `simulation_kernel_contract.md`
§9's actual text is made anywhere in this ticket.

## Parity Ledger Notes

- `docs/parity_ledger/substrate.yaml` `SUB-008` (`status: legacy_verified`, `priority: P0`,
  `test_path: null`, text: "Engine phase order preserves gameplay semantics and subsystem tick
  integrity.") rests on exactly the phase-order claim contradicted across the docs named in
  "Known Contradictions" #2 (architecture.md, README.md's two lines, CLAUDE.md's line 258). Per
  CLAUDE.md's own rule, P0 parity entries require a passing `test_path` — this entry has none
  today. This is a pre-existing gap, not caused by this ticket, and adding a test for SUB-008 is
  not in this ticket's scope — flagged here so the gap is visible rather than silently carried
  forward.
- `docs/parity_ledger/substrate.yaml` `SUB-307`/`SUB-308`/`SUB-309` (all P0, `verified`,
  `test_path: null`) despite `kernel.md` itself citing a real test file,
  `tests/architecture/test_phase_domain_permissions.py`, that appears to cover exactly this claim
  set (phase read/write/emit domain permissions). This looks like a parity-ledger metadata gap
  (missing `test_path` field) rather than a real doc-vs-code divergence — noted for completeness
  only, not actionable within this ticket's scope.
- No parity ledger entry currently exists for the hardware-class conflict, the §9 staleness, or the
  phase-count contradiction itself — these are structural/documentation entries. The two seed
  tickets' own Acceptance Criteria already call for adding/updating parity entries where relevant.
  This ticket does not add new parity entries since it defers rather than fixes; no logic changed,
  only doc prose, so CLAUDE.md's "if logic changes, update the parity ledger" rule does not trigger.

## Proposed Structural Convention + Enforcement Mechanism

**Adopt both halves — they solve different failure modes.**

### 1. Canonical-doc-per-topic map (prevents *authoring* new drift)

For each of the 4 contradiction topics found (and by extension, future ones), exactly one
canonical doc owns the fact; every other doc touching the same fact must cross-link, never
restate the fact independently.

| Topic | Canonical doc | Satellites (cross-link only) |
|---|---|---|
| Kernel phase count & names | `docs/engine/kernel.md` | `architecture.md`, `README.md`, `CLAUDE.md`, `docs/guides/simulation.md`, `simulation_kernel_contract.md` §4 (may restate the *law*, i.e. "phases run in this order," but not redefine phase *names*) |
| Pipeline refinement phase count | `docs/engine/authoritative_pipeline.md` | `README.md`, `CLAUDE.md`, `docs/guides/simulation.md`, `project_lawbook*.md` |
| Collection-phase concurrency | `docs/engine/contracts/worker_contract.md` | `kernel.md` (may restate consistent with worker_contract), `simulation_kernel_contract.md` §9 |
| Hardware-class thresholds | `docs/engine/contracts/certification_contract.md` §3 (already declared canonical by `simq_isolation_overhead.md`) | `perf_baseline_policy.md` (already cross-links via callout box — good precedent), `architecture.md` §5 (now has the same treatment, see "Known Contradictions" #3) |
| Architectural pillars / lawbook | `docs/engine/project_lawbook.md` | `project_lawbook_m10.md` (already says "See project_lawbook.md for the full law text" but then independently restates a *different*, 5-item pillar list instead of cross-linking — a newly-found instance of the same drift class this audit is for) |

### 2. Automated doc-parity check (catches drift *after* it happens — the durable backstop)

Two concrete, complementary, already-precedented mechanisms:

**(a) Doc-path-existence check.** A test extracting path-shaped strings from
`docs/engine/`, `docs/architecture/`, `docs/performance/` `.md` files and asserting each resolves
via `Path(...).exists()`. This would have caught `docs/guides/simulation.md`'s former
`src/engine/authoritative_pipeline.py` citation (fixed directly, though that doc is technically
outside this test's own directory scope). Implemented by this ticket as
`tests/docs/test_doc_path_existence.py`.

Running it for real surfaced far more than the one anticipated citation: **34 dead path citations**
across 17 files in the three scoped directories, none previously flagged by any audit. 22 were
real renames/relocations and were fixed directly during this ticket's Implement pass (e.g.
`tests/engine/test_worker_integrity.py` → `tests/unit/kernel/test_worker_integrity.py`,
`docs/guidelines/v2_intentional_divergences.md` → `docs/guidelines/intentional_divergences.md`,
plus two regex/exemption bugs in the check itself: a missing word-boundary that mis-truncated
`dashboard-frontend/src/...` paths, and a missing `src/legacy/` exemption for
`docs/engine/legacy_replacement_ledger.md`'s intentionally-dead historical entries). The remaining
**12 citations could not be fixed with confidence** — most (`tests/replay/test_authoritative_export_shape.py`,
`tests/engine/test_pipeline_contract.py`, three citations in `contracts/regression_and_verification.md`,
two in `docs/performance/optimization_invariants.md`) have zero candidate matches anywhere in the
tree under any name, suggesting the cited tests were never implemented rather than simply moved;
one (`tests/engine/test_phase_order.py`) has four plausible-but-ambiguous candidates; two
(`docs/architecture/2026-08-11-adventure-as-cognition-strategy-subcomponent-design.md`'s citations
of `src/domains/adventure/phase.py` and its shadow-migration-parity test) are historical —
`git log` confirms `src/domains/adventure/phase.py` was intentionally deleted by
`TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE`, the same "accurate-as-history" category as the
already-exempted `legacy_replacement_ledger.md`, just not caught by the structural `src/legacy/`
exemption since this file never lived under that prefix. Resolving these 12 with confidence needs
per-doc investigation at the depth this ticket's own plan already reserved for the recommended
follow-up ticket (see "Recommended Follow-Up" below) — the test is wired in and passing for the 22
fixed citations, with the residual 12 tracked via `pytest.mark.xfail(strict=True)` citing this
paragraph, following the identical pattern already used for
`test_no_fabricated_phase_names_in_kernel_docs` (Step 6/§2b below).

**(b) Fact-parity living tests.** Extends the existing `tests/docs/test_doc_integrity.py` +
`docs/engine/manifest.json` pattern (which already does exactly this for `RuntimeMode`/
`HardwareClass`/`FailureKind` enum membership via `test_terminology_alignment`) with a new,
analogous, deliberately minimal check for **phase names** — plain substring assertions against
real files read at test time, no parsing, following the
`test_agents_md_pipeline_note_matches_live_engine_doc` precedent
(`tests/agent_orchestration_codex_adapter/test_agents_md_generation.py`). Implemented by this
ticket as `tests/docs/test_kernel_phase_names_consistent.py`, kept as a separate, parallel
mechanism rather than folded into `manifest.json`'s existing
`mandatory_documents`/`forbidden_terms`/`monitored_terminology` schema — this is a check for
*narrative fabrication* (fake phase names appearing in prose), not the header-presence /
cross-link-existence / enum-membership checks `test_doc_integrity.py` already performs.

This is the exact "at least one example wired into a living test" this ticket's own Acceptance
Criteria require: it directly targets the recurrence pattern found repeatedly in this
investigation (GOVERNANCE/PACKETIZATION fixed once in `kernel.md` by
`TCK-20260619-P0-DOC-REPAIR`, then independently re-drifted into `architecture.md`, `README.md`,
`CLAUDE.md`, and `docs/guides/simulation.md`).

`test_no_fabricated_phase_names_in_kernel_docs` is currently wired as
`pytest.mark.xfail(strict=True)`: `architecture.md` still narrates the fabricated names pending
`TCK-20260817-FIX-PHASE-COUNT-CONTRADICTION` (still `OPEN`), so the test cannot pass for real yet.
Because `strict=True`, the test will hard-fail (XPASS) the moment `architecture.md`'s fix lands
without the xfail marker being removed — forcing whoever closes that seed ticket to notice and
remove the marker, rather than the drift-guard silently going stale a second time.

## Recommended Follow-Up

**Follow-up ticket recommendation (not filed by this ticket):**
`TCK-<date>-AUDIT-ENGINE-CONTRACTS-MATRICES-DRIFT`, tier `standard`, layer `engine`, scoped to full
D17-depth (3-5 verifiable claims/doc) coverage of `docs/engine/contracts/` (34 files) and
`docs/engine/matrices/` (~21 files) — the ~55 files this ticket's lighter existence/self-consistency
pass did not deep-check within the ~94-file "Remaining Files" set above. Rationale: these are
narrower, single-topic contract docs individually less likely to carry cross-doc narrative
contradictions than the broad docs this ticket already deep-checked, but have not been verified at
D17 depth by any ticket to date. This ticket's own Out of Scope clause explicitly permits this
split ("Full D17-depth audit of all 102 files if Plan-phase confirms breadth exceeds one ticket —
may split into directory-scoped follow-ups"). **This ticket's Implement phase does not create that
follow-up ticket file** — filing it (via the `create-tickets` skill) is a separate, later action,
left to whoever picks up this recommendation.

**Concrete starter backlog for that follow-up**, from running `tests/docs/test_doc_path_existence.py`
for real during this ticket's Implement pass (see "Automated doc-parity check" above for full
detail) — 12 dead path citations, currently tracked via `pytest.mark.xfail(strict=True)` on that
test, that the follow-up ticket should resolve or formally re-scope:

| Doc | Dead citation(s) |
|---|---|
| `docs/engine/authoritative_export_contract.md` | `tests/replay/test_authoritative_export_shape.py` |
| `docs/engine/authoritative_mutation_pipeline_contract.md` | `tests/engine/test_pipeline_contract.py` |
| `docs/engine/authoritative_refinement_contract.md` | `tests/engine/test_phase_order.py` (4 ambiguous candidates found) |
| `docs/engine/contracts/regression_and_verification.md` | `src/engine/arena/runner.py`, `src/testing/headless_regression_runner.py`, `tests/e2e/strategy/test_strategic_regression.py`, `tests/unit/combat/test_ranged_combat.py`, `tests/unit/core/gameplay/test_item_contracts.py` |
| `docs/architecture/2026-08-11-adventure-as-cognition-strategy-subcomponent-design.md` | `src/domains/adventure/phase.py`, `tests/integration/domains/adventure/test_adventure_shadow_migration_parity.py` (both historical — file confirmed deleted by TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE) |
| `docs/performance/optimization_invariants.md` | `tests/integration/optimization/test_degraded_mode_correctness.py`, `tests/integration/optimization/test_static_dirtyset_guard.py` |
