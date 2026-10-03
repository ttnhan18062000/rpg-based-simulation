# Test Plan — TCK-20260613-DOC-ENGINE-RUNTIME-DETAILS

Ticket: TCK-20260613-DOC-ENGINE-RUNTIME-DETAILS
Date: 2026-06-13

---

## Nature of this ticket

Documentation-only. No behavioral changes. No new code. No existing tests modified.

The test plan covers:
1. Verification that all cited test files exist and their referenced assertions match the source
2. The regression test table that each doc must include
3. Manual doc review checklist

---

## Existing tests cited per doc

### state_update_compaction.md

| Test file | Cited assertion | Verification |
|---|---|---|
| `tests/perf/test_apply_compaction_perf.py` | Line 76: `assert raw_state.fingerprint() == compacted_state.fingerprint()` — the fingerprint equivalence invariant | Confirmed by reading test file |
| `tests/perf/test_apply_compaction_perf.py` | Line 77: `assert metrics.compacted_entity_updates == count // 5` — compactor reduces 5000 entity updates to 1000 | Confirmed |
| `tests/perf/test_dirty_set_integrity.py` | `DirtySet.from_update()` behavior under various StateUpdate contents | Referenced in update_intents.md; cross-link valid |

### candidate_selection.md

| Test file | What it verifies |
|---|---|
| `tests/perf/test_dirty_parity.py::test_dirty_set_vs_full_scan_parity` | Dirty-set-optimized path and `force_full_scan=True` produce identical state hash over 100 ticks — validates that CandidateSelector routing is semantically equivalent to full scan |
| `tests/perf/test_concurrency_parity.py` | Sequential vs concurrent worker parity — indirectly validates that candidate ordering is deterministic |
| `tests/perf/test_dirty_set_integrity.py` | DirtySet correctly tracks entity domain membership — validates the dirty-set side of candidate routing |

### deterministic_execution.md

| Test file | What it verifies |
|---|---|
| `tests/perf/test_concurrency_parity.py` | `StateFingerprinter.get_fingerprint()` hash matches between sequential and concurrent execution modes after N ticks |
| `tests/perf/test_concurrency_parity.py::test_worker_chunk_boundary_determinism` | Determinism holds across different worker chunk boundaries |
| `tests/perf/test_dirty_parity.py` | State hash is identical between optimized (dirty-set) and reference (force_full_scan) runs — validates that the hash is the right correctness oracle |
| `tests/integration/pipeline/test_authoritative_apply.py` | `apply_generation()` is deterministic: same inputs produce same output |

---

## Manual review checklist

For each new doc, verify before marking complete:

- [ ] Frontmatter present with status: active, layer: engine, authority: P1, audience: agent, last_verified: 2026-06-13
- [ ] `## Regression tests` section present with real test file references
- [ ] `## Extension rules` section present with actionable steps
- [ ] Cross-links to related docs use correct relative paths
- [ ] No merge rule tables duplicated from `docs/core/update_intents.md`
- [ ] No domain routing tables duplicated from `docs/core/dirty_state_and_dependency.md`
- [ ] No 6-phase loop description duplicated from `docs/engine/kernel.md`
- [ ] Source file line references use "near line N" phrasing to tolerate minor shifts
- [ ] `docs/engine/project_lawbook.md` updated with all three new file entries
- [ ] `make knowledge-index-update` run after all docs created
- [ ] `make docs-registry` run after all docs created

---

## No tests to run

This is a documentation ticket. There is no behavior change. No `pytest` run is required. The review checklist above is the acceptance verification.
