---
status: active
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20260913-PARITY-LEDGER-CLASS2-CLASS4-RESIDUAL
artifact_type: plan
tags: [testing, registry, data-quality]
---

# Plan — TCK-20260913-PARITY-LEDGER-CLASS2-CLASS4-RESIDUAL

## Scope Guards

- Never fabricate a `test_path` citation. Every citation added must be independently verified to
  exist (file/function/class) before being written.
- All writes through `tools/parity_ledger_writer.py::write_entry()` — the one disclosed exception
  (removing a stale duplicate created by this session's own `write_entry()` rename call) is
  narrowly justified per this repo's established precedent, not a general pattern.
- Do not re-verify the behavior behind any entry — only its citation's parseability/existence.
- Do not fabricate a `.py`/`.tsx`-accepting parser change without checking it's safe for every
  other real consumer of the same shared parser first (`mechanics_auditor_static.py`).

## Step 1 — Delimiter extension (`tools/parity_test_path.py`)

Extend `_DELIM_SPLIT_RE` to accept a single ` | ` (whitespace-required both sides) as a
multi-citation delimiter, fixing INFRA-221/STRAT-236 with zero YAML edit. Verify safety first
against the real corpus (grep every `test_path` for `|`) before committing to the regex shape.

## Step 2 — Special cases named in the ticket's own Scope

INFRA-221, INFRA-405, STRAT-236 (delimiter/normalization), INFRA-406 (bad citation), INFRA-TYPE-001
(non-pytest evidence — new small static test file), SOC-ABAND-TYPE-01 (Class 4 rename). Each
investigated and fixed individually per the ticket's own AC.

## Step 3 — 63 prose-run-summary entries, shard by shard

Process `combat_movement.yaml` → `faction.yaml` → `substrate.yaml` → `town_resource.yaml` →
`social_narrative.yaml`/`strategic_cognition.yaml` → `infrastructure.yaml` (largest, ~40 entries),
in that order. For each entry: extract every real citation named in its `text`/`v2_evidence`/
`test_path` fields, verify each via grep/ls, normalize `test_path` to a plain multi-citation, move
disclosure prose into `support_boundary` (preserving the full original `test_path` verbatim via
direct variable reference for entries too large to safely hand-copy). Commit and push after each
shard, re-running `parity_corpus_check.py` to confirm the exact expected count delta each time.

## Step 4 — Genuinely unresolvable entries

For any entry whose only real evidence is non-pytest/non-Python (frontend `.ts`/`.tsx`/
`.spec.ts`), do not fabricate a citation and do not extend the parser without checking the
`mechanics_auditor_static.py::check_test_path()` consumer's own pytest-invocation assumption
first. If extending is unsafe, leave the entry untouched (its `write_entry()` validator requires a
parseable `test_path` on every write, so no partial/disclosure-only update is possible without
either fabrication or a raw-YAML bypass) and document the finding in the ticket's own investigation
and Completion Summary instead.

## Acceptance Criteria Map

- AC1 (re-measure before starting, note drift) → investigation.md §1.
- AC2 (every prose entry investigated individually) → Step 3, investigation.md §2/§6.
- AC3 (INFRA-221/405/STRAT-236 resolved) → Step 1/2, investigation.md §3.
- AC4 (INFRA-406 resolved) → Step 2.
- AC5 (INFRA-TYPE-001 resolved or deferred) → Step 2 (resolved, new static test).
- AC6 (SOC-ABAND-TYPE-01 renamed) → Step 2, investigation.md §5.
- AC7 (class2/class4 both 0, or remaining count justified) → 4 Class 2 entries remain, explicitly
  justified in investigation.md §4 and the ticket's own Completion Summary; Class 4 is 0.
- AC8 (all writes through write_entry()) → Scope Guards, one disclosed exception per investigation.md §5.
