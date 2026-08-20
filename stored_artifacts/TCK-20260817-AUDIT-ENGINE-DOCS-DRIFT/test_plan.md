---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260817-AUDIT-ENGINE-DOCS-DRIFT
artifact_type: test_plan
tags: [documentation, engine, architecture]
---

# Test Plan — TCK-20260817-AUDIT-ENGINE-DOCS-DRIFT

## Regression Surface

This is a docs-only ticket (audit doc + callout boxes + cross-links + one new living test). No
production code changes. Regression surface is limited to the doc-integrity test suite and any
tests whose docstrings/assertions cite the phase counts or hardware classes touched.

**Unit / doc-integrity:**
- `tests/docs/test_doc_integrity.py` — all 6 tests (manifest existence, structural compliance,
  terminology alignment, scoped reporting, recorder enforcement, link integrity). Must keep passing
  unchanged — this ticket does not modify `docs/engine/manifest.json`'s existing
  `mandatory_documents`/`forbidden_terms`/`monitored_terminology` content, only potentially adds new
  keys/checks (additive, not destructive).
- `tests/agent_orchestration_codex_adapter/test_agents_md_generation.py` — all 3 tests, especially
  `test_agents_md_pipeline_note_matches_live_engine_doc` (asserts `"37 phases"` is in
  `docs/engine/authoritative_pipeline.md`). This ticket does not touch that file's content, but the
  new living test this ticket adds follows this file's exact pattern — verify no import/collection
  conflicts.

**Integration:**
- `tests/integration/kernel/test_simulation_kernel_contract.py` — cited by the concurrency seed
  ticket as touching `simulation_kernel_contract.md`; not modified by this ticket, but must not be
  broken by any callout-box or cross-link addition (this ticket does not edit §9's actual text).
- `tests/integration/kernel/test_milestone_a_closure.py` — cited by the phase-count seed ticket as
  carrying a "6-phase" docstring/assertion consistent with `substrate_baseline_contract.md`'s
  framing; this ticket does not alter it, only confirms no new reconciling text conflicts with it.

**Architecture guard:**
- `tests/architecture/test_phase_domain_permissions.py` (RPG-INFRA-155/156/157) — the real
  enforcement behind kernel.md's Phase Domain Permissions table cited in this investigation; unaffected
  by this ticket's doc-only changes but should stay green as a sanity check that the phase-name
  reconciliation didn't accidentally touch anything code-adjacent.

## New Tests Required

Per Acceptance Criteria #3 ("at least one example wired into a living test"):

1. **`test_no_fabricated_phase_names_in_kernel_docs`**
   - Category: unit / doc-integrity (living test, `tests/docs/` pattern)
   - Verifies: `GOVERNANCE` and `PACKETIZATION` — the two fabricated phase names this
     investigation traced to 4 independent drift sites (architecture.md, README.md, CLAUDE.md,
     docs/guides/simulation.md) — do not appear in any doc that narrates the kernel's phase
     sequence, once the seed tickets (TCK-20260817-FIX-PHASE-COUNT-CONTRADICTION and its
     README.md/guides.md folds) land.
   - Where: new file `tests/docs/test_kernel_phase_names_consistent.py` (exact source given in
     investigation.md's "Proposed Structural Convention" section — copy directly, do not
     re-derive).
   - **Sequencing note**: this test will fail today (both seed tickets are still `OPEN`, and
     architecture.md/README.md currently contain the forbidden names). Do not add it un-guarded
     before those tickets close. Plan must decide: (a) sequence this ticket's implementation after
     both seed tickets close, or (b) add the test now with an explicit `pytest.mark.xfail(reason=...,
     strict=True)` citing the two open seed ticket IDs, flipped to a real assertion when they land.
     Either is acceptable; silently skipping without a reason string is not.

2. **`test_kernel_doc_states_all_seven_real_phases`**
   - Category: unit / doc-integrity
   - Verifies: `docs/engine/kernel.md` (the canonical doc per this ticket's proposed
     canonical-doc-per-topic map) names all 7 real phases (INIT, SCHEDULING, COLLECTION,
     RESOLUTION, CLEANUP, ADVANCEMENT, PERSISTENCE) — guards the *positive* direction (a future
     edit accidentally dropping a real phase from the canonical doc), complementing test 1's
     negative-direction guard (fabricated names creeping back in).
   - Where: same new file as test 1.
   - Not sequencing-blocked — kernel.md is already correct today; this test can be added and pass
     immediately.

3. **Doc-path-existence check** (if Plan adopts this ticket's recommendation to implement it here
   rather than defer it further, per the roadmap's Epic C framing it as "genuinely new scope,"
   already assigned to this ticket)
   - Category: unit / doc-integrity, CI-wired
   - Verifies: every path-shaped string in `docs/**/*.md` that looks like a repo-relative source
     path (heuristic: matches `src/`, `tests/`, `tools/`, `docs/` prefix + a file extension)
     resolves via `os.path.exists()`. Would have caught `docs/guides/simulation.md`'s
     `src/engine/authoritative_pipeline.py` citation directly.
   - Where: `tests/docs/test_doc_path_existence.py` (new), or as an added check function inside the
     existing `tests/docs/test_doc_integrity.py` if Plan prefers consolidation — either location is
     acceptable, Plan should pick one and note it in plan.md.
   - Needs a documented exclusion list for intentionally-archived/historical paths (e.g.
     `docs/archive/`, deliberately-removed-infra references in `infrastructure_compat_contract.md`
     that describe what *used to* exist) — do not let this test force-delete legitimate historical
     references; scope it to `status: active` docs only, or explicitly excluded directories.

4. **Callout-box presence check** (optional, lower priority — only if Plan wants machine
   enforcement that the new hardware-class callout box was actually added, not just described in
   this investigation)
   - Category: unit / doc-integrity
   - Verifies: `docs/engine/architecture.md` contains a `> Known conflict, not resolved here` block
     (the same convention `perf_baseline_policy.md` already uses) once this ticket's audit doc adds
     it.
   - Where: could be folded into the audit-doc's own accompanying test if one is created, or
     skipped if Plan judges a single grep-able convention string too brittle to assert on. Leave
     this to Plan's discretion — not required by the acceptance criteria the way tests 1-3 are.

## Scoped Pytest Commands

```bash
# Full doc-integrity suite (existing + any new tests added here)
pytest tests/docs/ -v

# Living-test precedent this ticket's new test follows — confirm no regression
pytest tests/agent_orchestration_codex_adapter/test_agents_md_generation.py -v

# Kernel/phase-adjacent integration tests this ticket must not break
pytest tests/integration/kernel/test_simulation_kernel_contract.py tests/integration/kernel/test_milestone_a_closure.py -v

# Phase-domain-permissions architecture guard (sanity check, unaffected but cheap to confirm)
pytest tests/architecture/test_phase_domain_permissions.py -v
```

Never `pytest tests/` — scope stays within `tests/docs/`, the two named integration files, and the
one architecture guard file, per this ticket's docs-only footprint.

## Anti-Drift Test Guards

- **`test_no_fabricated_phase_names_in_kernel_docs` is itself the anti-drift guard for the
  contradiction class this whole ticket exists to address** — it directly encodes the "fixed once
  in kernel.md, re-drifted independently in architecture.md" failure pattern this investigation
  confirmed really happened. If this test is *not* added (or is added but never un-xfail'd once the
  seed tickets close), the ticket has not actually satisfied its own acceptance criteria's
  "wired into a living test" requirement — a prose-only audit doc without this test would silently
  repeat the exact gap D17 already left once.
- **Guard against re-fixing out-of-scope items**: no test in this ticket's scope should assert that
  `simulation_kernel_contract.md` §9's concurrency/scheduler-optimization/adaptive-degradation/
  broker-mode bullets have been corrected — that would indicate scope creep into the two seed
  tickets' and the §9-hypothesis's explicitly out-of-scope territory. If a future PR for this ticket
  includes such an assertion, that's a signal the implementation over-reached.
- **Guard against re-declaring `simulation_watchdog.md` as broken**: this investigation confirmed
  it's already fixed (Epic B). No test or doc change in this ticket's scope should treat it as an
  open item — if Plan/Implement adds work against it, that's stale-context drift from the roadmap
  doc's pre-fix description, not a real gap.
- **Guard against silently "fixing" CLAUDE.md's 32-phase claim**: it doesn't exist (verified: line
  259 already says 37-phase). A diff touching that line for this reason would indicate the
  implementer worked from the ticket's stale evidence text instead of this investigation's verified
  correction — the real, still-open CLAUDE.md issue is line 258 (kernel-loop phase count), not 259
  (pipeline phase count).
