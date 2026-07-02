# SimQ Uplift Batch 2 — Implementation Sequence

Tickets derived from post-uplift-1 grade gap analysis (2026-07-02). All three target persistent
C-grade pillars after the first uplift batch.

| Order | Ticket | Why this order |
|---|---|---|
| 1 | TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA | Documentation-only hotfix; no calibration re-run required; unblocks clean baseline for tickets 2 and 3 |
| 2 | TCK-20260702-SIMQ-UPLIFT2-FACTION | Engine + schema change; requires calibration re-run for urban_political; independent of INFORMATION |
| 3 | TCK-20260702-SIMQ-UPLIFT2-INFORMATION | Engine + world spec change; requires calibration re-run for urban_political; best run after FACTION so both are re-calibrated together at the end |

## Dependency Notes
- Tickets 2 and 3 both modify `urban_political` calibration runs and will both update `grade_anchors.json`.
  Run them sequentially to avoid anchor conflicts. If both complete, a single final `make evaluate --dry-run`
  confirms 0 regressions across both changes.
- Ticket 1 (AGENCY-DA) has zero calibration impact and should be committed before tickets 2 and 3
  change any anchors, so `make evaluate --dry-run` stays green throughout.
- FACTION and INFORMATION are independent of each other and could in principle be parallelised,
  but sequential is safer given shared `grade_anchors.json` mutation.
