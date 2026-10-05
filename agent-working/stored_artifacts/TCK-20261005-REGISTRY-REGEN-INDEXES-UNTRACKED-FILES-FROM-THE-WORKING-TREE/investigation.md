---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261005-REGISTRY-REGEN-INDEXES-UNTRACKED-FILES-FROM-THE-WORKING-TREE
artifact_type: investigation
tags: []
---

# Investigation
Verified against `origin/main`: `record_hand_orchestrated_closure.py` called `generate_registry()` in place, which walked the filesystem, so an untracked draft under an indexed path reached the registry while CI (no such file) failed `test_check_flag_detects_no_drift_against_real_registry`.
Decision: `git ls-files` includes staged files, so staging is the way to make a new file indexable without `include`. Callers audited with `grep -rn "generate_registry(" tools .claude`: the closure tool, `done_checker_static` (two call sites) and the CLI.
Side note from the ticket (test-plan advisory noise about `## Proof Plan`) is out of scope and untouched.
