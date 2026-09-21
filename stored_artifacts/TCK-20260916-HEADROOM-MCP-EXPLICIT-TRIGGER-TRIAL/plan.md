# Plan — TCK-20260916-HEADROOM-MCP-EXPLICIT-TRIGGER-TRIAL

1. Confirm registration is already permanent on `main` (from the isolation ticket + PR #228) — no
   setup needed for this pass.
2. Copy the 4 real payloads the ticket's own Scope names into a scratch temp directory (never
   compress in place).
3. Measure each via a real MCP client (`mcp` SDK's `stdio_client`/`ClientSession`) calling
   `headroom_compress` once per payload — paired, on identical input, default install (no `[ml]`,
   the working decision).
4. Perform at least one `headroom_retrieve` round-trip and confirm it byte-exact.
5. Investigate and report any surprising transform/result honestly rather than re-running with
   different settings (`inflation_guard:reverted`, the 20s timeout) — read the real CLI warning
   lines, don't guess.
6. Reconfirm state isolation (`~/.headroom` absent, isolated dir populated) and zero repository
   mutation after the full trial, not just at the smoke-test stage.
7. Record every number exactly as measured in the ticket, including the two 0%-with-real-cause
   findings on the ticket's own top two target payload types — do not tune payload selection or
   retry to clear the plan's own ≥30% bar.
8. Close via the standard hand-orchestrated path: `stored_artifacts/`, `record_hand_orchestrated_
   closure.py`, `docs/REGISTRY.yaml` regeneration.
