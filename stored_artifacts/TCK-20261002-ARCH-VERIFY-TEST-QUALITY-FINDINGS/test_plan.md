---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261002-ARCH-VERIFY-TEST-QUALITY-FINDINGS
artifact_type: test_plan
phase: done
date: 2026-10-02
tags: [agent-monitoring, workflows]
---

# Test plan

| AC | Proof |
|---|---|
| AC1 | `tests/tools/test_arch_verify_test_quality_findings.py`: parse the real JS with the helper; `test_quality_findings` is a property of ARCH_VERIFY_SCHEMA and not in `required`. |
| AC2 | Same file: `cleanFindings` + `pushEvent` are extracted verbatim from the real workflow text and executed in node (skipped without node): findings carried verbatim, key absent for `[]`/null/other events, non-strings dropped, `'` neutralised, `seq` and `summary<=200` intact; plus a static pin that both Architecture-Verify `pushEvent` calls pass `archVerify.test_quality_findings`. |
| AC3 | `tests/tools/test_record_events*.py` style: valid list accepted, string/non-string-item rejected; closure tool test: input event with the field lands in the written events shard, without the field no key is added. |
| AC4 | helper unit tests on a fixture JS (nested braces, braces inside strings, schema order) plus a pin against the real `ARCH_VERIFY_SCHEMA` key list; unknown schema -> non-zero exit. |
| AC5 | doc pin: both SKILL.md copies contain the rule and name `schema_format_tail.py`; schema.md documents the field. `tests/tools/test_workflow_meta_conformance.py` still passes. |
| AC6 | existing record_events / closure tests still pass (additive); monitoring wrapper fail-open unchanged. |

Negative controls: each new test must fail on origin/main. Scoped run: tests/tools (full) + tests/docs before push.

## Proof Plan

| AC | level | proof kind | oracle source | expected effect | selected commands |
|---|---|---|---|---|---|
| AC1 | unit | static parse of the real workflow | `ARCH_VERIFY_SCHEMA` text itself via `schema_format_tail.extract_schema_keys` | key present after `verified_by`, absent from `required` | `pytest tests/tools/test_arch_verify_test_quality_findings.py -k "schema or required"` |
| AC2 | unit | real JS executed in node | `pushEvent`/`cleanFindings` source extracted verbatim from the workflow | findings carried; key omitted for none; `'` neutralised | `pytest tests/tools/test_arch_verify_test_quality_findings.py -k push_event` |
| AC3 | unit | validator and builder calls | `record_events.validate_record`, `build_records` | bad shapes rejected; closure events keep the list | `pytest tests/tools/test_arch_verify_test_quality_findings.py -k "record_events or closure"` |
| AC4 | unit | fixture plus real-file pin | fixture JS with nested braces/quoted keys; real `ARCH_VERIFY_SCHEMA` | schema-order key sentence; unknown schema exits 1 | `pytest tests/tools/test_arch_verify_test_quality_findings.py -k helper` |
| AC5 | doc pin | text assertions | both SKILL.md copies and schema.md | rule and field documented | `pytest tests/tools/test_arch_verify_test_quality_findings.py -k "skill or schema_md"` |
| AC6 | regression | existing suites | `test_record_events.py`, `test_record_hand_orchestrated_closure.py`, `test_workflow_runtime_acorn_parse.py` | all unchanged and green | `pytest tests/tools/test_record_events.py tests/tools/test_record_hand_orchestrated_closure.py tests/tools/test_workflow_runtime_acorn_parse.py` |

| AC7 | unit | fixture shards plus a real-data spot check | tools/events fixture rows; the real shards for a past run | the four classes behave; cut paths only POSSIBLY-READ; shadow ignored | `pytest tests/tools/test_arch_verify_read_check.py` |
