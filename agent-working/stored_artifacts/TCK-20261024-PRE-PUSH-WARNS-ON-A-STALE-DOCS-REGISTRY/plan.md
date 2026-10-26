---
status: active
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261024-PRE-PUSH-WARNS-ON-A-STALE-DOCS-REGISTRY
artifact_type: plan
tags: [delivery, process-improvement]
---

# Plan

1. `tools/delivery/pre_push_advisory_hook.py`: add `check_registry_fresh(run_command, base_ref)`. One `git diff --name-only <base>...HEAD`; only a `.md` under `docs/`, the tickets tree or the stored-artifacts tree (constants from `tools.agent_working_paths`, mirroring what `generate_registry.py` reads) runs `python3 tools/generate_registry.py --check` with a 60 s timeout.
2. Exit 2 (the tool's documented drift code) returns one advisory line naming `make docs-registry` and `git add docs/REGISTRY.yaml`. Any other exit, a timeout or an exception returns nothing (fail-open).
3. Wire it last in `run_all_checks`; update the module docstring ("Five checks") and the check list in `docs/guides/delivery_process.md` step 2b.
4. Tests in `tests/tools/test_delivery_pre_push_advisory.py`.
