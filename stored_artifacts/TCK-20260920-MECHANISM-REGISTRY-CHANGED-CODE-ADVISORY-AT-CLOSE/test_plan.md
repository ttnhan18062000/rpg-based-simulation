# Test Plan — TCK-20260920-MECHANISM-REGISTRY-CHANGED-CODE-ADVISORY-AT-CLOSE

| Case | Verification |
|---|---|
| Planted drift case fires | Disposable temp git repo: commit tagged `TCK-FAKE-...` changes a cited file, registry entry untouched → `check_drift_for_ticket` returns 1 finding |
| Planted no-drift case is silent | Same shape, but the registry entry also changes in the same commit → 0 findings |
| Uncommitted state is picked up | Modify a cited file in the working tree without committing → still detected (proves the "run before final commit" timing gap is closed) |
| Cross-ticket contamination avoided | A second commit on the same repo, tagged with a DIFFERENT ticket ID, touching a DIFFERENT cited file → not included in the first ticket's `changed_files` |
| `--ticket-id` CLI path never fails | `main(["--ticket-id", "..."])` returns 0 even when findings exist |
| Existing `--base`/`--head` CLI path unaffected | Existing `test_main_always_exits_zero` / `test_make_target_runs_clean` / `test_unresolvable_base_ref_reports_skipped_not_a_crash` still pass unmodified |
| `implement-ticket.js` Finalize-tail wiring never blocks | Manual read-through: the new block matches the exact non-blocking shape of `phaseMetaCheck` (log-only, no `status` mutation) |
| CLAUDE.md hand-orchestration bullet reachable | Manual read: the new bullet sits next to `record_hand_orchestrated_closure.py`, same section |

Scoped pytest: `pytest tests/unit/tools/test_mechanism_registry_changed_code_check.py -v`
