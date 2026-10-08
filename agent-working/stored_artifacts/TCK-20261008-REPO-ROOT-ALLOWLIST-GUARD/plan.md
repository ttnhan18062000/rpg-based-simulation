---
status: historical
layer: architecture
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261008-REPO-ROOT-ALLOWLIST-GUARD
phase: done
date: 2026-10-08
tags: [architecture, delivery]
---

# plan — TCK-20261008-REPO-ROOT-ALLOWLIST-GUARD

1. Add the Repo root section and allowlist (from `git ls-files` after B1 to B3) to `repo_tooling_layout.md`.
2. Add `tests/codebase/test_repo_root_allowlist.py`, reading the allowlist from the guideline.
3. Prove the guard fails on an extra tracked root file.

Scope guard: keep `perf_baselines.json` and `skills-lock.json`; untracked clutter is not checked; no root entry is moved here.
