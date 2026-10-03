# Test Plan — TCK-20260909-UNREACHABLE-IMPLEMENTED-CODE-AUDIT

No production code is modified by this ticket — it is a static-analysis audit, and its own
"tests" are verification of the tool's output against known ground truth, not a pytest suite.

## Tool Correctness Checks
1. **Known-instance recall**: run `tools/audit_unreachable_code.py` and confirm it re-discovers
   `spawn_calamity()` and (after the test-only-usage fix) `effective_certainty()` from the original
   known-instance list. Confirm it correctly does NOT flag live code as dead — spot-checked via
   `_personality_weight` (same-file caller, must not be flagged) and the FastAPI/Pydantic-decorated
   methods (must appear in the excluded set, not the real-candidate set).
2. **Documented negative case**: confirm `BiologicalSystem.update()` does NOT appear in the tool's
   output (neither as excluded nor as a real candidate) — this is the tool's own documented
   generic-name-collision limitation, verified by direct grep showing "update" occurs thousands of
   times across the corpus, not a bug.
3. **Cluster claims independently re-verified**, not trusted from the tool's own output alone:
   - `src/domains/optimization/`'s 8-of-9-dead claim: direct `grep -rn "from src.domains.optimization"`
     confirming zero production imports for 8 modules, and that `admission_control.py`'s reference
     to `cache_strategy.py` is a comment, not an import.
   - `GracefulDegradationManager`/`ResourceGovernor` structural-duplicate claim: direct read of both
     `optimization/degradation.py` and `src/engine/governor.py`, confirming matching
     threshold-ratio-based mode logic, not inferred from naming alone.
   - `spawn_calamity()`/`CalamityService.process_world_dynamics()` duplicate claim: direct read of
     `src/world/calamity.py:23-77` confirming its own live `generator.spawn_monster(kind=
     "world_boss", ...)` call.
   - `BiologicalSystem.update()`/`apply.py` passive-decay duplicate claim: direct read of
     `src/engine/apply.py:89-100` confirming the live formula.
   - `unregister_campaign()`/`unregister_chronicle()` dead claim: direct grep across `src/`, both
     test files, and `tools/` confirming zero call sites, and direct read of both test files'
     docstrings confirming `_clear_registry()` as the real cleanup path.

## Regression Check
`tests/integrity/test_no_duplicate_content_blocks.py` — run after all ticket/doc edits, before
commit, per this repo's own standing sanity-check pattern for ticket-closure batches.

## Out of Scope for This Test Plan
Running or updating any `src/` or `tests/` suite beyond the integrity check above — no production
behavior changed.
