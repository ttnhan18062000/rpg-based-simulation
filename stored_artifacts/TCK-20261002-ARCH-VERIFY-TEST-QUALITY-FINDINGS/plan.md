---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261002-ARCH-VERIFY-TEST-QUALITY-FINDINGS
artifact_type: plan
phase: done
date: 2026-10-02
tags: [agent-monitoring, workflows]
---

# Plan

1. `schema_format_tail.py` (new, `tools/agent-monitoring/`): `extract_schema_keys(js_text, name)` brace-matches `const NAME = {`, returns top-level `properties` keys in order; `format_tail(keys)` returns the single sentence "Return your answer as a single JSON object with keys: a, b, c."; CLI `--workflow <path> --schema NAME`. Fail loudly (exit 1) on an unknown schema; never guesses.
2. `implement-ticket.js`: add `test_quality_findings` to `ARCH_VERIFY_SCHEMA` (not required); `pushEvent` gets optional 8th param `extra` merged only when defined; Architecture-Verify ok/failed pushes pass `{ test_quality_findings }` built by a small `cleanFindings` (array of strings, `'` replaced, empty/absent -> omitted). No prompt text change.
3. `record_events.validate_record`: when present, `test_quality_findings` must be a list of strings.
4. `record_hand_orchestrated_closure.build_records`: carry `test_quality_findings` when the input event has it.
5. `docs/agent-monitoring/schema.md`: new optional field row + note.
6. Both SKILL.md: "Output-format tail" rule (generated via the helper, recorded verbatim, nothing appended when the schema is enforced natively) and a drift note pointing at TCK-20260804-SKILL-JS-PHASE-SYNC.
7. Tests as in test_plan.md; send the diff to test-architecture-implementer before merge.

Scope guards: no edit to the Architecture-Verify prompt wording or the reviewer agent file; no real Workflow run.
