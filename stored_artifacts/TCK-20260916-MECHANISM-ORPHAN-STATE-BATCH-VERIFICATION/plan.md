---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260916-MECHANISM-ORPHAN-STATE-BATCH-VERIFICATION
artifact_type: plan
tags: [architecture, schema, simulation-quality]
---

# Plan — TCK-20260916-MECHANISM-ORPHAN-STATE-BATCH-VERIFICATION

## Steps

1. Enumerate all `state: orphan` mechanisms in the real registry (11 total); confirm the 5 already
   bound in earlier tickets need no re-investigation.
2. For each of the 6 remaining, find the real implementing code directly (not from atlas prose
   alone), check real callers (comment/docstring-excluded), check flag-gating.
3. Correct any mechanism found wrong, with the same rigor as `causal_spatial_memory`/
   `demographic_cohort_cycle`: real `verified` block citing the exact evidence, propagate to every
   consumer (atlas badge + prose, capabilities, wiring map).
4. Bind the two confirmed-orphan mechanisms (`declared_cognition_schema`, `committed_intentions`)
   with `implemented_by`, using symbol-level binding where the file mixes written and unwritten
   symbols (avoiding the exact aggregation mistake `demographic_cohort_cycle` exposed).
5. Where a finding contradicts an existing peer-authored `verified` block (`succession`), stop and
   flag with full evidence rather than unilaterally overwrite.
6. Regenerate all four derived views; re-verify with `graphify-out/` genuinely moved aside and
   restored.

## Acceptance-criteria map

| AC | Satisfied by |
|---|---|
| Real caller check, not assumed from atlas prose | investigation.md's per-mechanism evidence |
| Corrections propagated to every consumer | atlas card prose/badges for `genetics_aptitude`, `emotion`, `cross_episode_social_consequences`; capabilities; wiring map (`EMO` node) |
| Symbol-level binding used to avoid aggregation mistakes | `declared_cognition_schema` → `RiskModel`, `committed_intentions` → `CommitmentModel`, not file-level |
| Contradicting a peer's own prior finding is flagged, not silently overwritten | `succession` left unresolved, reported with full evidence |
