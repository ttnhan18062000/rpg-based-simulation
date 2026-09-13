# Test Plan — TCK-20260912-OPTIMIZATION-ORPHANED-CAPABILITY-DETERMINATION

- Post-deletion: `grep -rln "GracefulDegradationManager\|CacheStrategy\b\|DirtyWorkScheduler\|
  TraceVolumeGovernor"` across `src/`/`tests/` returns zero real matches (one docstring reference
  in `test_degraded_fallback.py` explaining the deletion itself, not a real usage).
- `grep -n` against `.github/workflows/*.yml`/`Makefile` for module filenames, class names, and
  dedicated test filenames — zero matches (the non-import-reference guard).
- `pytest tests/unit/domains/optimization/ tests/unit/perf/ tests/perf/ tests/unit/core/
  tests/unit/observability/ tests/unit/world/providers/ tests/integration/perf/
  tests/api/test_admission_control.py -q -m "not slow and not extra_slow"`: 1528 passed, 1 skipped
  — full regression sweep across every directory touched, no failures.
- `tests/unit/core/test_degraded_fallback.py` specifically: 4 passed (down from 10 — the 6 removed
  tests exclusively covered the deleted `GracefulDegradationManager.resolve_content_source()`; the
  4 kept tests cover live, independent code and pass unchanged).
