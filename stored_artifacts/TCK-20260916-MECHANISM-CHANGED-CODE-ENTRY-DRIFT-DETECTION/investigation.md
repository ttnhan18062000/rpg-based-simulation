---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260916-MECHANISM-CHANGED-CODE-ENTRY-DRIFT-DETECTION
artifact_type: investigation
tags: [architecture, schema, simulation-quality]
---

# Investigation — TCK-20260916-MECHANISM-CHANGED-CODE-ENTRY-DRIFT-DETECTION

## The AC's own suggested positive control does not exist

AC #3 suggested "the `causal_spatial_memory` state-drift fix commit, which changed both the
citing code's own surrounding context and the registry entry together" as a positive control.
Checked directly: `git log --oneline --all -- src/domains/memory/phase.py` shows no commit after
2026-09-15 (when `registries/mechanisms.yaml` was created) — the file's own last real change
predates the registry's own existence, so no single commit could possibly satisfy "both changed
together." Used synthetic fixtures instead, which the AC's own "e.g." phrasing permits.

## Real-history validation, run manually rather than committed

Ran `check_drift_from_git("42528c527", "ba3588fa5")` against this session's own two real commits
(the `trauma` misattribution's own correction, then its same-day self-correction) as a manual
sanity check before trusting the synthetic tests alone: 0 drift findings, 1 replacement finding —
`trauma: ['.../RecoveryReadinessService'] -> ['.../WoundService']`. Confirms the replacement
signal would have surfaced this session's own real incident.

Not committed as a test: pinning a specific commit SHA from a feature branch breaks the moment
that branch squash-merges (`CLAUDE.md`'s own "PR Lifecycle" §7) — those individual commits stop
being reachable from `main` and are eventually garbage-collected. A test asserting against them
would start failing post-merge for a reason entirely unrelated to the tool's own correctness.

## The replacement signal — offered by peer review, included after checking it fit

Peer review, while discussing the `trauma` misattribution incident, suggested the inverse of the
core drift check: an `implemented_by` being REPLACED (already had one, now points elsewhere) is a
stronger claim than a first binding and deserves visibility in review. Checked whether it fit
cleanly before including it: `check_replacements()` reuses the exact same `old_mechs`/`new_mechs`
comparison `check_drift()` already builds, adds one new field comparison
(`old.get("implemented_by")` truthy and changed), and is reported in its own clearly separate
section rather than merged into the drift findings. No scope expansion to the core check's own
`changed_files` requirement — replacements are detected independent of whether the newly-cited file
happens to appear in the same diff's changed-file list.
