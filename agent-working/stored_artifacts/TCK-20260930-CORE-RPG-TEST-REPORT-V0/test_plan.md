---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20260930-CORE-RPG-TEST-REPORT-V0
artifact_type: test_plan
tags: [testing]
---

# Test plan: core-RPG test report v0

Location: `tests/unit/tools/test_core_rpg_report.py` (covered by the "Run: tests/unit/tools" CI lane).
Synthetic fixtures under `tmp_path`, no dependence on live repo content beyond one smoke run.
- determinism: build twice from the same fixture inputs -> identical JSON bytes.
- execution states: no JUnit -> `no-junit-artifact`; JUnit lacking a file -> `not-run`; JUnit with it -> outcome counts; all three distinct.
- coverage: none -> `no-coverage-artifact`; supplied -> per-package %, `provisional-local`; domain coverage `not-derived`.
- classification: both signals agree -> `classified`; disagree -> `uncertain`; neither -> `not-core-rpg`.
- lanes: fixture workflow -> parsed paths, marker, junit path, uploaded flag; file with no lane -> `no-lane`.
- mutation: fresh, stale by target hash, stale by age at `as_of`, absent -> `not-run`.
- escaped defects: months from registration to `as_of`, with 0 as a real count; missing tag -> `tag-not-registered`.
- every layer count has a denominator; the output has no absolute path; the v0 limits list has the required entries.
- smoke: producer on the live repo runs and its JSON validates.
