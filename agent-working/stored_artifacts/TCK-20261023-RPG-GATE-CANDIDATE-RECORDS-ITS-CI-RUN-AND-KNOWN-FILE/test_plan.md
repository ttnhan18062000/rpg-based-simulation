---
status: historical
layer: testing
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261023-RPG-GATE-CANDIDATE-RECORDS-ITS-CI-RUN-AND-KNOWN-FILE
phase: done
date: 2026-10-26
tags: [testing, regression, simulation-quality]
---

# TCK-20261023-RPG-GATE-CANDIDATE-RECORDS-ITS-CI-RUN-AND-KNOWN-FILE: test_plan

tests/unit/tools/test_rpg_gate_candidate.py (+5 tests/params): the candidate records ci (all four) and the known hash; ci is null for env {} / only RUN_ID / empty REF / missing EVENT_NAME; rebaseline refuses ci null and a non-main ref and writes nothing, accepts main; the CLI records sha256 of the known file bytes (local build: ci null; with the four variables set: recorded), using monkeypatch so it is deterministic under GitHub Actions.
tests/unit/tools/test_rpg_gate_baseline.py (+6 groups): rebaseline refuses ci None / absent / empty run_id / feature branch / refs/pull/9/merge / empty ref (match message, no file written); refuses no known hash; accepts a main run and carries both fields into the file; evidence_only refusal still holds; lint requires both fields at version 2 (None, malformed hash, uppercase hash, ci None, empty run_attempt; removing each) and rejects a non-main ci.ref; version 1 is exempt by version number; the committed rpg_gate_v1.json lints unchanged.
Regression: tests/unit/tools/test_rpg_gate_{baseline,candidate,report,workflow_support,harness}.py and tests/static (375 passed).
