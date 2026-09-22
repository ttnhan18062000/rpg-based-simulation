# Implementation Sequence — codex-runtime-activation

Tickets must be implemented in this order. This sequence intentionally separates
readiness evidence from live activation.

## Order

1. TCK-20260730-CODEX-RUNTIME-ACTIVATION-EPIC (scope-only parent)
2. TCK-20260730-CLAUDE-EXECUTION-IDENTITY (parallel with #3 after parent)
3. TCK-20260730-PROVIDER-HOOK-POLICY (parallel with #2 after parent)
4. TCK-20260730-CODEX-POSTTOOL-ADAPTER (depends on #2 and #3)
5. TCK-20260730-CODEX-RUNTIME-SHADOW (depends on #2, #3, and #4)
6. TCK-20260730-CODEX-CONTROLLED-PILOT (depends on #2 through #5 and an explicit contemporary human authorization)

## Safety Boundary

Steps 1-5 build and verify controlled readiness only. They must not create a hook-bearing
committed `.codex/config.toml`, invoke paid/live Codex, or append a real `provider=codex`
record to the repository monitoring corpus. Step 6 may perform a single live operation only
after its own final human-owned candidate, rollback, sign-off, and preflight gates pass.

## Baseline Note

The known stale-path failure tracked by `TCK-20260722-CONTRACT-STRUCTURE-TEST-STALE-PATH` is
unrelated and must be reported separately from any activation regression.
