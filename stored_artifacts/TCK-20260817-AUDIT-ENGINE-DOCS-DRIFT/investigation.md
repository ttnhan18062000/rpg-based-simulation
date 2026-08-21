---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260817-AUDIT-ENGINE-DOCS-DRIFT
artifact_type: investigation
tags: [documentation, engine, architecture]
---

# Investigation — TCK-20260817-AUDIT-ENGINE-DOCS-DRIFT

## Current Behavior

### Doc surface size (verified, not the ticket's estimate)
`find docs/engine docs/architecture docs/performance -name '*.md' | wc -l` = **110** files
(docs/engine 92 [25 top-level + 34 `contracts/` + ~21 `matrices/` + misc], docs/architecture 14,
docs/performance 4). The ticket's own estimate ("~102 files: engine 83") undercounts by ~8 — mostly
the `matrices/` subdirectory, which the ticket's own Related Code Areas list never named. This
matters for the Plan-phase sizing decision (see Risks).

### The 4 mandatory issues — verified current state

**1. Concurrency contradiction (TCK-20260817-FIX-CONCURRENCY-DOC-CONTRADICTION, still `OPEN` in
`tickets/todos/kernel-concurrency-design-review/`).** Confirmed still live:
`docs/engine/kernel.md:55` — *"Concurrent Collection: the Deliberation phase is the only window
for parallel execution"* — vs. `docs/engine/contracts/simulation_kernel_contract.md:57` — *"No
concurrency or parallel execution."* Both `status: active, authority: P1`. Code
(`src/engine/worker_manager.py`, `ThreadPoolExecutor`/`ProcessPoolExecutor`) matches kernel.md.
A third P1 doc, `docs/engine/contracts/worker_contract.md`, independently and correctly documents
bounded worker-pool concurrency (Payload Discipline, Deterministic Equivalence Law) with no
contradiction — it's simulation_kernel_contract.md §9 that's the stale outlier, as the seed ticket
already concludes. **Resolve-by-cross-reference**: cite the seed ticket, do not re-fix.

**2. Phase-count contradiction (TCK-20260817-FIX-PHASE-COUNT-CONTRADICTION, still `OPEN`).**
Verified current state of all docs the seed ticket names, plus the two new evidence pieces:
- `docs/engine/architecture.md:47` — 6-phase table (INIT, **GOVERNANCE**, SCHEDULING,
  **PACKETIZATION**, RESOLUTION, PERSISTENCE) — still stale, GOVERNANCE/PACKETIZATION are fabricated
  phase names not present in `src/engine/kernel.py`.
- `docs/engine/kernel.md:21-27` and `docs/engine/contracts/simulation_kernel_contract.md:27-33` —
  both correctly state the real 7-phase list (INIT, SCHEDULING, COLLECTION, RESOLUTION, CLEANUP,
  ADVANCEMENT, PERSISTENCE).
- `docs/engine/README.md:13` — **also still stale**, not just architecture.md: *"The 6-phase
  orchestrator (Init, Governance, Scheduling, Packetization, Resolution, Persistence)"* — this is
  already in the seed ticket's scope, confirmed still unfixed.
- `docs/engine/README.md:14` — **a second, independent stale claim on the same line pair**, not
  named by either seed ticket: *"The 17-phase refinement sequence for world mutation"* — this
  contradicts `docs/engine/authoritative_pipeline.md`, which was already corrected to 37 phases by
  `TCK-20260817-STANDARD-AGENTS-MD-PIPELINE-PHASE-COUNT-DRIFT` (verified: `authoritative_pipeline.md:11`
  now reads *"refined through these 37 phases"*, and `src/engine/pipeline.py` has 38 `run_phase(...)`
  call sites, 33+ uniquely named — the "37" figure was verified against source by that ticket, not
  re-derived here). README.md was missed by that ticket's propagation pass. **New finding, add to
  scope**: `docs/engine/README.md` needs both its stale phase claims fixed, not just the 6-phase one
  the seed ticket already names.
- `docs/engine/contracts/substrate_baseline_contract.md:27` — states *"6 phases in strict
  sequential order"* with PERSISTENCE framed as a non-authoritative 7th "hook" — the seed ticket
  already correctly scopes this as needing a *reconciling note* (not a fix), since it's
  self-consistent with `tests/integration/kernel/test_milestone_a_closure.py`'s own "6-phase"
  docstring. Confirmed unchanged; no new action needed beyond what the seed ticket already scopes.

**New evidence item (a) — verified accurate, add to scope:**
`docs/guides/simulation.md:19-26` currently reads:
```
Every simulation run is a deterministic 6-phase loop (Init → Governance → Scheduling →
Packetization → Resolution → Persistence) repeated per tick. ...
- `src/engine/kernel.py` — the 6-phase loop
- `src/engine/authoritative_pipeline.py` — the 17-phase mutation sequence
```
Confirmed both claims are wrong: the 6-phase/Governance/Packetization framing is the same stale
pattern as architecture.md/README.md, **and** `src/engine/authoritative_pipeline.py` does not
exist — `ls` confirms `src/engine/pipeline.py` + `src/engine/pipeline_phases/` is the real
implementation. This doc was not named in either seed ticket. **Confirmed accurate — include in
audit and cross-link/defer to the phase-count seed ticket's scope** (per the roadmap doc's own
instruction that this fold-in belongs to this ticket, not a new one).

**New evidence item (b) — verified INACCURATE, do not carry forward as stated:**
The ticket text (and `docs/plans/architecture_resilience_remediation_roadmap.md`'s Epic C) both
assert root `CLAUDE.md` "states a third number, a 32-phase refinement sequence." Direct check of
the live file: `CLAUDE.md:259` currently reads *"`authoritative_pipeline.md` | 37-phase refinement
sequence for world mutation"* — **already correct, not 32**. `tickets/working_log.csv:1435`
confirms `TCK-20260817-STANDARD-AGENTS-MD-PIPELINE-PHASE-COUNT-DRIFT` (completed same day this
ticket was filed) explicitly "regenerated AGENTS.md/.agents/skills, **CLAUDE.md**, and 5 living
skill docs" as part of its propagation pass. This evidence item is now **stale itself** — the
underlying claim it describes no longer exists in the file. Per the ticket's own instruction to
"verify these citations are accurate before recording them": **do not record CLAUDE.md's 32-phase
claim as an open finding** — record instead that it was independently resolved by a different
ticket before this audit ran, so Plan doesn't spend effort re-fixing something already fixed.

**New finding (c) — CLAUDE.md still carries a live instance of the phase-count contradiction,
just not the one the ticket named.** `CLAUDE.md:258`, in the same Engine Contracts table, still
reads: *"`kernel.md` | 6-phase deterministic loop (Init → Governance → Scheduling → Packetization
→ Resolution → Persistence)"* — this is CLAUDE.md's own one-line summary of what `kernel.md`
covers, and it's wrong: kernel.md actually documents the real 7-phase loop, not this fabricated
6-phase one. The AGENTS-MD-PIPELINE-PHASE-COUNT-DRIFT ticket fixed the *pipeline* phase-count line
(259) but not the adjacent *kernel-loop* phase-count line (258) in the same table — same failure
mode the roadmap's own "prose-only fixes re-drift" observation warns about, caught here in the
very doc used as evidence for a different, now-resolved claim. **Add to scope**: this is a
previously-unflagged fourth live instance of the phase-count contradiction, in a P1-adjacent
project-instructions file every agent reads on every session.

**3. Hardware-class conflict (per TCK-20260702-OBSISO-ISOLATION-PROOF).** Already has a callout
box at `docs/performance/perf_baseline_policy.md:30-35` following the exact `> Known conflict, not
resolved here` convention, cross-linking `certification_contract.md` §3 and
`simq_isolation_overhead.md`'s own worked numeric example (`simq_isolation_overhead.md:48-62`,
which independently confirms the conflict with real measured hardware: 4 cores/5.8GB is `CLASS_C`
under certification_contract.md's binary rule but doesn't clearly fit perf_baseline_policy.md's
table either). **This callout box already satisfies the "formally defer" requirement** — no new
callout is needed, only a cross-reference from the new audit doc to this existing one.

**New finding, not previously flagged anywhere: a *third*, independently-drifted hardware-class
taxonomy.** `docs/engine/architecture.md:88-93` §5 "Performance Monitoring" defines:
```
Class A (Low-Power): Bounded to strictly degraded profiles (10 TPS).
Class B (Consumer): Standard profile (20 TPS).
Class C (High-Performance): Enhanced observability profiles.
```
This is not just a third set of numeric thresholds — it **inverts the letter-to-capability
mapping** relative to both other docs. `certification_contract.md` §3 and
`perf_baseline_policy.md` §2.2 both make **Class A the most powerful tier** (≥16 cores/≥32GB, or
"High-Performance Server"); architecture.md makes **Class A the least powerful tier**
("Low-Power," 10 TPS) and Class C the most powerful ("High-Performance"). A reader consulting
architecture.md instead of certification_contract.md would misclassify hardware in the *opposite*
direction. This is more severe than the already-flagged OBSISO conflict (which is a threshold
disagreement between two docs that agree on direction) and was found by directly reading
architecture.md during this audit, not previously documented anywhere. **Add as a new callout box
in the audit doc**, cross-linking this ticket per the acceptance criteria's "any newly-found
P1-vs-P1 contradiction NOT fixed in this ticket is recorded via the same callout-box format."

**4. `simulation_kernel_contract.md` §9 broader staleness.** All three named bullets independently
verified stale against real source:
- *"No scheduler optimization"* — `src/engine/scheduler.py:33` `DeterministicScheduler.select_work()`
  implements LOD gating (`# M7 Law: Adaptive Level of Detail (LOD)`, line 49,
  `LODService.should_execute()`) and cadence-based gating (`should_run()`,
  `cadence.strategic_intelligence`) — this is scheduler optimization by any reasonable reading.
- *"No adaptive degradation"* — `src/core/governance.py:8-16` defines `class RuntimeMode(IntEnum)`
  with exactly the ladder `NORMAL=0, CONSTRAINED=1, DEGRADED=2, SURVIVAL=3`, driving
  `GovernorPolicy.from_mode()` (`src/engine/policy.py`) — this is a fully-built, actively-used
  adaptive degradation system, not a stub.
- *"No external event brokers"* — `src/simulation_quality/feed.py` and `worker.py` implement a real
  Redis-backed `QUALITY_FEED_MODE=broker` mode (`QualityFeedMode.BROKER`, `broker_url`,
  `QualityWorker` "Orchestrates broker-mode quality scoring in a dedicated process"). This is a real
  external message broker in active use, measured and gated by
  `docs/performance/simq_isolation_overhead.md`'s own "(c) broker" column.

**Supporting evidence for the ticket's own hypothesis** (§9 may be describing
`minimal_kernel.md`'s narrower scope): `docs/engine/contracts/minimal_kernel.md` §9 "Non-Goals"
(lines 52-56) states nearly the same 4 concepts — *"Concurrency or worker dispatch. Resource
governor or adaptive degradation. Scheduler optimization."* — for the explicitly-scoped
single-threaded minimal kernel (§2: *"Single-Threaded: All authoritative changes occur
sequentially in one process"*). The overlap in wording and concept set (concurrency,
adaptive-degradation/governor, scheduler-optimization all present in both; only "external event
brokers" vs. "Replay system or persistence" differ) is consistent with §9 having been copied or
derived from minimal_kernel.md's Non-Goals and never re-scoped when simulation_kernel_contract.md
grew to describe the full production kernel. This remains an **unconfirmed hypothesis** — record
it as such, needing owner confirmation, per the ticket's explicit instruction not to silently fix.

## Mechanics / Engine Constraints

This ticket is documentation-only and does not touch runtime mechanics. The relevant constraint is
`docs/engine/kernel.md`'s Phase Domain Permissions table and
`tests/architecture/test_phase_domain_permissions.py` (RPG-INFRA-155/156/157), which is the real,
enforced source of truth for phase read/write/emit boundaries — any doc claim about phase
responsibilities should defer to that table + test, not restate it independently (this is itself an
instance of the canonical-doc-per-topic pattern this ticket needs to formalize).

## Docs Requiring Update

This ticket's own deliverable (Plan/Implement phase) is the audit doc itself
(`docs/audits/D2x_engine_docs_drift.md` or similar, following D17's naming precedent) plus the
callout-box additions and cross-links below. The following existing docs need direct edits as part
of implementing this ticket's scope (not the two out-of-scope seed tickets' own fixes):

- `docs/engine/README.md`: still states the stale 6-phase/Governance/Packetization kernel loop
  AND a stale "17-phase" pipeline claim (two separate stale facts on adjacent lines); the 6-phase
  half is already in TCK-20260817-FIX-PHASE-COUNT-CONTRADICTION's scope, but the 17-phase half is
  a new finding this ticket surfaces and should fold in per the same "fold new evidence into this
  ticket, don't re-ticket" pattern the roadmap already established for the CLAUDE.md/guides items
- `CLAUDE.md`: line 258's one-line kernel.md summary ("6-phase deterministic loop... Packetization")
  is a newly-found, previously-unflagged live instance of the phase-count contradiction
- `docs/architecture.md` (i.e. `docs/engine/architecture.md`) §5: newly-found third, inverted
  hardware-class taxonomy needs a `> Known conflict, not resolved here` callout box (same pattern
  as `perf_baseline_policy.md`'s existing one), cross-linking this ticket and the OBSISO ticket
- A new audit doc under `docs/audits/` (path TBD by Plan, following `D17_documentation_currency.md`'s
  naming convention, e.g. `D2x_engine_docs_drift.md`): the ticket's primary deliverable, enumerating
  the sampled file set with stale/current/uncertain/duplicate/contradictory classifications
- `docs/engine/manifest.json` and `tests/docs/test_doc_integrity.py`: if Plan adopts the
  doc-path-existence check or the phase-name-forbidden-terms extension recommended below, these
  are the concrete files that change
- `docs/plans/kernel_concurrency_design_review_proposal.md`: the "Known documentation drift" section
  should get a completion cross-link back to wherever this ticket's audit doc lands, closing the
  loop C8 opened

## Parity Ledger Overlap

- `docs/parity_ledger/substrate.yaml` `SUB-008` (P0, `legacy_verified`, **`test_path: null`**):
  *"Engine phase order preserves gameplay semantics and subsystem tick integrity."* This P0 entry
  rests on exactly the phase-order claim that's contradicted across 4 docs (architecture.md,
  README.md x2, CLAUDE.md) and has no passing `test_path` today. Per CLAUDE.md's own rule, "P0
  entries require a passing test_path" — this is a pre-existing gap, not caused by this ticket, but
  directly relevant: fixing the doc contradiction without also addressing this P0 entry's missing
  test_path leaves the parity ledger's strongest claim about phase order unverified by any test.
  Flag for Plan; not this ticket's scope to add the test, but the audit doc should note the gap.
- `docs/parity_ledger/substrate.yaml` `SUB-307`/`SUB-308`/`SUB-309` (all P0, `verified`,
  `test_path: null` in the YAML despite `kernel.md` itself citing a real test file,
  `tests/architecture/test_phase_domain_permissions.py`) — likely a parity-ledger metadata gap
  (missing `test_path` field) rather than a real doc-vs-code divergence; noted for completeness,
  not actionable within this ticket's scope.
- No parity ledger entry currently exists for the hardware-class conflict, the §9 staleness, or the
  phase-count contradiction itself — these are structural/documentation entries, and the seed
  tickets' own Acceptance Criteria already call for adding/updating parity entries where relevant
  (TCK-20260817-FIX-CONCURRENCY-DOC-CONTRADICTION's AC #4). This ticket does not need to add new
  parity entries since it defers rather than fixes.

## Prior Work

- `docs/audits/D17_documentation_currency.md` — the format/depth precedent this ticket follows (3-5
  claims/doc, `stale`/`current`/`uncertain` classification, severity scoring). D17 already found and
  a later ticket (`TCK-20260619-P0-DOC-REPAIR`) already fixed kernel.md's first dual-phase-table
  contradiction and authoritative_pipeline.md's 17-phase table (once, to 31 phases) — both have
  since re-drifted or were superseded: kernel.md's fix held, but the *same* contradiction pattern
  reappeared independently in architecture.md (never fixed by that ticket, since it didn't touch
  architecture.md), and authoritative_pipeline.md needed a second fix (31 → 37,
  `TCK-20260817-STANDARD-AGENTS-MD-PIPELINE-PHASE-COUNT-DRIFT`) when the pipeline grew further.
  This "fixed once, re-drifted independently elsewhere" pattern is the direct evidence this
  ticket's own Assumptions section cites for why a durable structural check (not another one-off
  fix) is needed — confirmed accurate by this investigation.
- `docs/plans/kernel_concurrency_design_review_proposal.md` — the C1-C8 origin document. C8 is this
  ticket. Its "Appendix A" drafted design doc (Kernel Concurrency Model & Design Philosophy, status:
  draft) is C1's deliverable, not this ticket's — out of scope here, but the audit doc should note
  C1 as still unlanded so a future reader doesn't assume it already exists.
- `docs/plans/architecture_resilience_remediation_roadmap.md` §"Epic C" — explicitly declares itself
  *"not new work — it extends [this ticket]"* and is the source of both new-evidence items (CLAUDE.md
  32-phase [now stale itself, see above], guides/simulation.md). It also identifies the
  doc-path-existence CI check as "genuinely new scope, not covered by the existing kernel-concurrency
  epic" and flags coordination with Epic B on the watchdog doc.
- `docs/architecture/simulation_watchdog.md` — Epic B's roadmap entry describes this doc as stale
  (wrong path, "Proposed" status, no external alert channel) as of before Epic B ran. **Verified
  during this investigation: already fixed.** Current content correctly describes
  `src/observability/watchdog.py`, `AlertsManager`/`AlertRouter`/`WebhookAlertSink` routing with
  `SIM_ALERTS_WEBHOOK_URL`/`SIM_ALERTS_WEBHOOK_ENABLED` gating, and explicitly states "No
  PagerDuty/Discord integration exists." This matches Epic B's (`TCK-20260817-ENGINE-LIVENESS-HEALTH-EPIC`)
  own completion description exactly — **no further action needed on this doc**, it's current, not
  stale. Epic C's roadmap bullet describing it as needing a fix is pre-fix history now.
- `tests/agent_orchestration_codex_adapter/test_agents_md_generation.py` — the living-test pattern
  this ticket must replicate. Three tests: a staleness-drift guard (generated file ≠ frozen stale
  draft), a forbidden-string + required-string assertion on the generated artifact
  (`"17-phase" not in text`, `"37-phase" in text`), and — the specific pattern the ticket names —
  `test_agents_md_pipeline_note_matches_live_engine_doc`, a 2-line test that just asserts a fact
  string ("37 phases") appears in the live source-of-truth doc
  (`docs/engine/authoritative_pipeline.md`). This is deliberately minimal: no parsing, no diffing,
  just a substring assertion against two real files read at test time. See "Anti-Drift Hazards" /
  the enforcement-mechanism design below for the concrete new test this ticket should design.

## Risks and Open Questions

- **Scope-size risk, confirmed real.** 110 actual files (not ~102) across the three directories.
  This investigation deep-checked 4-5 claims each on 15 high-value docs (kernel.md, architecture.md,
  simulation_kernel_contract.md, minimal_kernel.md, authoritative_pipeline.md, README.md,
  certification_contract.md, performance_contract.md, worker_contract.md, project_lawbook.md,
  project_lawbook_m10.md, simulation_watchdog.md, perf_baseline_policy.md,
  simq_isolation_overhead.md, docs/guides/simulation.md) plus CLAUDE.md — comparable to or exceeding
  D17's own 9-doc sample. Extending that same depth to the full 110 is not achievable in this
  ticket's remaining Plan/Implement budget without either (a) reducing per-doc depth well below
  D17's 3-5-claim precedent (violating the ticket's own instruction to sample "at D17's own depth"),
  or (b) a directory-scoped split. **Recommendation for Plan**: treat this ticket's audit doc as
  covering the 15+ docs already deep-checked here (all with real evidence, several with genuinely
  new findings) plus a lighter existence/self-consistency pass over the remaining ~95 (mostly
  `docs/engine/contracts/` and `docs/engine/matrices/`, which are narrower, single-topic contract
  docs less likely to carry cross-doc contradictions than the broad narrative docs already checked),
  and explicitly recommend a follow-up standard ticket (e.g.
  `TCK-<date>-AUDIT-ENGINE-CONTRACTS-MATRICES-DRIFT`) scoped to `docs/engine/contracts/` (34 files)
  and `docs/engine/matrices/` (~21 files) for full D17-depth coverage, per this ticket's own Out of
  Scope clause permitting exactly this split.
- **§9 hypothesis genuinely needs owner confirmation, not an assumed answer.** The minimal_kernel.md
  wording-overlap evidence is suggestive but circumstantial — it's equally possible
  simulation_kernel_contract.md was *always* meant to be the aspirational/idealized full-kernel
  contract and never got updated as scheduler optimization / adaptive degradation / broker mode
  were added, independent of minimal_kernel.md's existence. Do not let Plan/Implement silently pick
  one reading — this needs to stay flagged for a human/owner decision per the ticket's explicit
  instruction.
- **The architecture.md hardware-class inversion is more severe than OBSISO's already-flagged
  conflict** (opposite direction, not just different thresholds) and was not caught by any prior
  audit or ticket. Recommend Plan treat this as a new callout box with equal priority to the
  existing OBSISO one, not a lesser footnote.
- **The enforcement-mechanism scope decision (canonical-doc-map vs. periodic/automated parity check)
  is a real trade-off Plan needs to make explicitly**, not default into. See the enforcement-mechanism
  design below for both options with a concrete recommendation.

## Anti-Drift Hazards

- **Do not re-fix the concurrency or phase-count contradictions in this ticket.** Both have their
  own `OPEN` seed tickets with their own Acceptance Criteria; this ticket's job is cross-reference
  and defer, plus the two named new-evidence folds (guides/simulation.md, and now README.md's
  17-phase line — CLAUDE.md's 32-phase claim is *not* live, do not "fix" something already fixed).
- **Do not resolve the hardware-class conflict or the §9 hypothesis** — both are explicitly Out of
  Scope; the deliverable is a callout box / recorded hypothesis, not a corrected value.
- **The `simulation_watchdog.md` doc is already fixed** — do not schedule work against it; Epic C's
  roadmap bullet describing it as broken is stale history, verified during this investigation.
- **Watch for a repeat of the exact "fixed once, re-drifted independently" pattern this ticket exists
  to prevent.** If the new audit doc or callout boxes are added as pure prose with no test/mechanism
  behind them, the same class of drift will recur elsewhere in the 110-file surface within another
  audit cycle — the acceptance criteria's requirement for "at least one example wired into a living
  test" is not optional decoration, it's the point of this ticket.
- **The manifest.json / `test_doc_integrity.py` mechanism already exists but doesn't cover
  architecture.md or README.md at all** (neither is in `mandatory_documents`), and even for docs it
  does cover, it only checks required-header presence, cross-link existence, and enum-membership
  against live code (`RuntimeMode`, `HardwareClass`, `FailureKind`) — **it does not check prose
  content accuracy** (e.g. phase names, phase counts). Do not assume this existing suite would have
  caught any of the findings above; it wouldn't have, by design. Any enforcement-mechanism proposal
  needs to either extend this suite's checked-content model or add a parallel one — see below.

---

## Proposed Structural Convention + Enforcement Mechanism

**Recommendation: adopt both halves of the ticket's suggested options, not just one — they solve
different failure modes.**

1. **Canonical-doc-per-topic map** (prevents *authoring* new drift): for each of the 4 contradiction
   topics found (and by extension, for future ones), name exactly one canonical doc; every other doc
   touching the same fact must cross-link, never restate the fact independently.

   | Topic | Canonical doc | Satellites (cross-link only) |
   |---|---|---|
   | Kernel phase count & names | `docs/engine/kernel.md` | `architecture.md`, `README.md`, `CLAUDE.md`, `docs/guides/simulation.md`, `simulation_kernel_contract.md` §4 (may restate the *law*, i.e. "phases run in this order," but not redefine phase *names*) |
   | Pipeline refinement phase count | `docs/engine/authoritative_pipeline.md` | `README.md`, `CLAUDE.md`, `docs/guides/simulation.md`, `project_lawbook*.md` |
   | Collection-phase concurrency | `docs/engine/contracts/worker_contract.md` | `kernel.md` (may restate consistent with worker_contract), `simulation_kernel_contract.md` §9 |
   | Hardware-class thresholds | `docs/engine/contracts/certification_contract.md` §3 (already declared canonical by `simq_isolation_overhead.md`) | `perf_baseline_policy.md` (already cross-links via callout box — good precedent), `architecture.md` §5 (needs the same treatment) |
   | Architectural pillars / lawbook | `docs/engine/project_lawbook.md` | `project_lawbook_m10.md` (already says "See project_lawbook.md for the full law text" — but then independently restates a *different*, 5-item pillar list instead of cross-linking; this is itself a newly-found instance of the same drift class this ticket audits for) |

2. **Automated doc-parity check** (catches drift *after* it happens, the durable backstop):
   two concrete, complementary mechanisms, both cheap and already precedented in this repo:

   **(a) Doc-path-existence check** — already scoped by the roadmap's Epic C as "genuinely new,"
   not duplicated elsewhere: a script extracting path-shaped strings from `docs/**/*.md` and
   asserting `os.path.exists()`. This would have caught `docs/guides/simulation.md`'s
   `src/engine/authoritative_pipeline.py` citation immediately. Cheapest, highest-leverage single
   addition; recommend Plan implement this as part of this ticket rather than deferring it further,
   since it's explicitly named as this ticket's scope by the roadmap doc.

   **(b) Fact-parity living tests** — extend the existing `tests/docs/test_doc_integrity.py` +
   `docs/engine/manifest.json` pattern (which already does exactly this for `RuntimeMode`/
   `HardwareClass`/`FailureKind` enum membership via `test_terminology_alignment`) with a new,
   analogous check for **phase names**, following precisely the
   `test_agents_md_pipeline_note_matches_live_engine_doc` pattern the ticket names (`ROOT / "docs" /
   ... .read_text()`, plain substring assertions, no parsing).

   **Concrete example to wire in now** (Plan/Implement should build this exact test — it is the
   "at least one example" the acceptance criteria require, and it directly targets the recurrence
   this ticket's own Assumptions section flags as "strongest evidence a durable check is needed"):

   ```python
   # tests/docs/test_kernel_phase_names_consistent.py
   from pathlib import Path

   ROOT = Path(__file__).parent.parent.parent
   # "GOVERNANCE" is case-sensitive only (a case-insensitive check would false-positive
   # on legitimate uses: docs/engine/contracts/governance_logic.md, architecture.md's own
   # "Phase Governance" section heading). "PACKETIZATION" has no legitimate use in any
   # casing, so it's checked case-insensitively — this closes a false-negative gap found
   # at Review: README.md/CLAUDE.md/docs/guides/simulation.md all use Title-Case
   # "Packetization", which a case-sensitive-only check would miss entirely.
   FORBIDDEN_PHASE_NAME_GOVERNANCE = "GOVERNANCE"  # case-sensitive
   FORBIDDEN_PHASE_NAME_PACKETIZATION = "packetization"  # checked case-insensitively
   REAL_PHASES = ("INIT", "SCHEDULING", "COLLECTION", "RESOLUTION", "CLEANUP",
                  "ADVANCEMENT", "PERSISTENCE")

   # Every doc that narrates the kernel's phase sequence in prose (not the ones that
   # explicitly document an intentionally-different framing, e.g. substrate_baseline_contract.md's
   # documented "6 authoritative + 1 hook" equivalence note).
   PHASE_NARRATING_DOCS = [
       "docs/engine/kernel.md",
       "docs/engine/architecture.md",
       "docs/engine/README.md",
       "docs/engine/contracts/simulation_kernel_contract.md",
       "docs/guides/simulation.md",
       "CLAUDE.md",
   ]

   def test_no_fabricated_phase_names_in_kernel_docs():
       """GOVERNANCE and PACKETIZATION are not real _phase_* methods in src/engine/kernel.py.
       This exact fabricated pair has independently drifted into architecture.md, README.md,
       CLAUDE.md, and docs/guides/simulation.md after being fixed once in kernel.md
       (TCK-20260619-P0-DOC-REPAIR) — TCK-20260817-AUDIT-ENGINE-DOCS-DRIFT."""
       for rel_path in PHASE_NARRATING_DOCS:
           text = (ROOT / rel_path).read_text()
           assert FORBIDDEN_PHASE_NAME_GOVERNANCE not in text, (
               f"{rel_path} contains fabricated phase name {FORBIDDEN_PHASE_NAME_GOVERNANCE!r}"
           )
           assert FORBIDDEN_PHASE_NAME_PACKETIZATION not in text.lower(), (
               f"{rel_path} contains fabricated phase name 'packetization' (any casing)"
           )

   def test_kernel_doc_states_all_seven_real_phases():
       """The canonical doc (kernel.md) must name all 7 real phases — guards against a future
       partial/stale rewrite in the other direction."""
       text = (ROOT / "docs/engine/kernel.md").read_text()
       for phase in REAL_PHASES:
           assert phase in text, f"kernel.md missing real phase name {phase!r}"
   ```

   This is deliberately the cheapest version that still catches the exact, twice-repeated failure
   mode found in this investigation (fabricated GOVERNANCE/PACKETIZATION names reappearing
   independently across 4 files) — it does not attempt full prose-parity checking, matching the
   "living test" pattern's own minimalism (substring assertions, not semantic diffing).

**Do not implement either mechanism as a fix to the 2 known-open contradictions in this ticket** —
both seed tickets are still `OPEN`; landing this test before they land would make it fail
immediately (architecture.md/README.md/CLAUDE.md currently *do* contain the forbidden names). Plan
should either sequence this test's introduction after the seed tickets close, or write it now as
`xfail`/skip-with-reason until they do, and flip it live as part of this ticket's own closure. This
sequencing decision belongs in plan.md, not implementation notes here.
