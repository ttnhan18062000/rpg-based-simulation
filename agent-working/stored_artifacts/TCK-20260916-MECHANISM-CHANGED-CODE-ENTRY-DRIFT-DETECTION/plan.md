---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260916-MECHANISM-CHANGED-CODE-ENTRY-DRIFT-DETECTION
artifact_type: plan
tags: [architecture, schema, simulation-quality]
---

# Plan — TCK-20260916-MECHANISM-CHANGED-CODE-ENTRY-DRIFT-DETECTION

## Goal
Mechanically flag a PR/diff that changes `implemented_by`-cited code without touching the citing
mechanism's own registry entry — the mechanical version of the parity ledger's own decayed
"update your entry when behavior changes" rule.

## Design
1. `check_drift(old_data, new_data, changed_files)` — pure core, no git dependency. Compares two
   already-loaded registry snapshots against a set of changed file paths.
2. `check_replacements(old_data, new_data)` — a related, separately-reported signal: an
   `implemented_by` citation replaced rather than first-bound. Reuses the same old/new comparison.
3. `check_drift_from_git(base_ref, head_ref)` — thin CLI wrapper: `git diff --name-only` for
   changed files, `git show <ref>:registries/mechanisms.yaml` to load the registry at each ref.
4. Report-only `main()`, always exits 0, same convention as every sibling detector.
5. `make mechanism-registry-changed-code-check` target, not CI-wired (matching
   `mechanism-state-caller-check`/`mechanism-wiring-map-classdef-check`'s own precedent).

## Non-goals
- Any enforcement stronger than report-only.
- Extending to the parity ledger's own `test_path` drift (separate, already-solved problem).
