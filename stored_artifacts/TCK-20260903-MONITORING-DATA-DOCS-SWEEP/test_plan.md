---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260903-MONITORING-DATA-DOCS-SWEEP
artifact_type: test_plan
tags: [agent-monitoring, observability, documentation, claude-md]
---

# Test Plan — TCK-20260903-MONITORING-DATA-DOCS-SWEEP

This is a docs/config/prose-only ticket (no `src/`/`tools/` behavior change, per Scope's own
Out-of-Scope line). There is no pytest suite whose behavior this ticket changes — its correctness is
verified by grep-based content checks and manual review against the real, landed physical layout,
plus a narrow re-run of the existing tests that already assert something about these files
(`.gitattributes`, `docs/parity_ledger/infrastructure.yaml`'s schema-validity) to confirm nothing was
broken.

## Regression Surface

Existing tests that must keep passing (none of these are expected to change behavior from this
ticket's edits — they are the closest thing to a regression surface a docs-only ticket has, since a
couple of them literally assert facts about the files this ticket touches):

- **unit** — `tests/tools/test_migrate_monitoring_data.py` (asserts `agent-monitoring/runs.jsonl`/`events.jsonl`
  no longer exist in the working tree, and that `.gitattributes` no longer contains the 2 legacy
  `merge=union` lines — this ticket's `.gitattributes` confirmation must not reintroduce them).
- **unit** — `tests/integrity/test_merge_union_gitattributes.py` (whatever it asserts about
  `.gitattributes`'s `merge=union` shape generally — must still pass after confirming/no-op on this
  file).
- **unit** — `tests/tools/test_parity_ledger_writer.py` (if present) or the parity-ledger schema/write-path
  tests exercised by `tools/parity_ledger_writer.py::validate_entry()`/`write_entry()` — the new
  `INFRA-291` addendum must pass `validate_entry()`'s 4 schema rules (non-empty `id`/`text`/`status`/`priority`
  etc.) the same as the 3 existing addenda did.
- **unit** — `tests/tools/test_parity_index_baseline.py` (this repo's documented "hardcoded baseline
  drift" pattern per `docs/testing/regression_policy.md` — appending to `INFRA-291` changes
  `infrastructure.yaml`'s entry count/shape; if this baseline test asserts a fixed count/hash, it may
  need a small, evidence-backed baseline update in the same session per the documented drift-handling
  policy, not a silent edit).
- **unit** — `tests/tools/test_doc_staleness_check.py`, `tests/tools/test_doc_staleness_gate_wiring.py`
  (this ticket's diff touches only `docs/`/`CLAUDE.md`/`.claude/` — confirm the doc-staleness gate
  still correctly treats a docs-only diff as not requiring a `src/` behavior-change doc pairing, i.e.
  doesn't false-positive-block Finalize).
- **architecture guard** — `tests/tools/test_kgmcp_phase5_repeated_demand_measurement.py::` (has a
  static guard asserting no module opens the live `events.jsonl` directly by name — confirm this
  ticket's `docs/`-only edits don't trip it; it scans source, not docs, so should be unaffected, but
  worth a scoped re-run since it's adjacent).

Scoped by domain, not `pytest tests/`:

```bash
pytest tests/tools/test_migrate_monitoring_data.py tests/integrity/test_merge_union_gitattributes.py \
       tests/tools/test_doc_staleness_check.py tests/tools/test_doc_staleness_gate_wiring.py -v
```

```bash
pytest tests/tools/ -k "parity_ledger_writer or parity_index_baseline" -v
```

## New Tests Required

None. This ticket changes prose/doc content only — there is no new behavior to unit-test. The
"tests" for this ticket are the verification grep commands below plus manual review of each edited
file's rendered content, run at Verify time.

If the implementer judges a durable regression guard is warranted (optional, not required by
Acceptance Criteria): a small architecture-guard test asserting `CLAUDE.md`, `docs/agent-monitoring/schema.md`,
`docs/agent-monitoring/README.md`, and `docs/guides/agent_monitoring.md` never contain the bare
strings `agent-monitoring/runs.jsonl`, `agent-monitoring/events.jsonl`, `agent-monitoring/tools/tools-`,
or bare `agent-monitoring/tools.jsonl` outside an allowlisted set of "historical citation" line
patterns (e.g. lines starting with `` `git log --follow -- ``, or inside a `### Historical
Corrections`/dated-Addendum block) would prevent this exact staleness from recurring silently after a
future physical-layout change. Not required for this ticket to pass Verify — noted as a possible
follow-up, matching the "file tickets for workflow gaps" convention rather than scope-creeping it in
here.

## Scoped Verification Commands (grep-based, no pytest)

**1. The ticket's own Acceptance-Criteria grep, re-run after edits — must return zero
current-state hits** (historical/excluded hits, individually justified in investigation.md, are the
only allowed survivors — confirm each surviving hit is one of the ones explicitly excluded there):

```bash
grep -rn "agent-monitoring/runs\.jsonl\|agent-monitoring/events\.jsonl\|agent-monitoring/tools/tools-" \
  docs/ CLAUDE.md .gitattributes .claude/workflows/implement-ticket.js .claude/skills/
```

**2. The gap this investigation found in the AC's own pattern — bare monolithic `tools.jsonl`,
not covered by pattern 1 above — must also return zero current-state hits post-edit:**

```bash
grep -rn "agent-monitoring/tools\.jsonl" \
  docs/ CLAUDE.md .gitattributes .claude/workflows/implement-ticket.js .claude/skills/
```

(Expected surviving hits after this ticket's edits, per investigation.md's "Already clean, confirmed"
and "excluded" sections: none in the 8 touched files above — `docs/observability/agent_ops_dashboard_contract.md`'s
`tools.jsonl` mentions are conceptual/dated and were already out of the primary sweep's target file
list.)

**3. `CLAUDE.md`'s 4 specific claims are gone (or their post-edit equivalents no longer assert
the stale fact) — re-locate by content, not line number, since edits shift lines:**

```bash
grep -n "tools\.jsonl\|runs\.jsonl\|events\.jsonl" CLAUDE.md
```

Manually confirm every surviving line now describes `agent-monitoring/data/YYYY-Www/{runs,events,tools}.jsonl`,
not a bare single-file path.

**4. `.gitattributes` — confirm still exactly one unified glob, no legacy lines reappeared:**

```bash
cat .gitattributes
```

Expect: `agent-monitoring/data/*/*.jsonl merge=union` present; none of
`agent-monitoring/runs.jsonl merge=union`, `agent-monitoring/events.jsonl merge=union`,
`agent-monitoring/tools.jsonl merge=union`, `agent-monitoring/tools/*.jsonl merge=union` present.

**5. `docs/parity_ledger/infrastructure.yaml`'s `INFRA-291` addendum was added via the sanctioned
writer, not a raw edit:**

```bash
git diff --stat docs/parity_ledger/infrastructure.yaml
python3 -c "
import yaml
entries = yaml.safe_load(open('docs/parity_ledger/infrastructure.yaml').read().split('---')[-1]) if False else None
"
grep -c "Addendum (TCK-20260903-MONITORING-DATA-DOCS-SWEEP" docs/parity_ledger/infrastructure.yaml
```

(The middle python snippet is a placeholder reminder — the real check is: `git diff` shows a
single-shard, well-formed YAML diff consistent with `write_entry()`'s `yaml.safe_dump(entries,
sort_keys=False)` re-serialization shape — not a hand-typed patch — and the `grep -c` above returns
`1`.) Also re-run `tools/parity_index.py health` or equivalent to confirm the derived index rebuilt
cleanly (`write_entry()` calls `build()` in-process on success).

**6. `make knowledge-index-update` completes successfully** (required by CLAUDE.md's "After Work"
rule since `docs/` files changed):

```bash
make knowledge-index-update
```

**7. Confirm no `src/`/`tools/` files appear in the diff** (this ticket must stay docs/config-only):

```bash
git status --porcelain | grep -v "^?? staging_artifacts/\|^?? stored_artifacts/" | grep -E "^ M src/|^ M tools/" || echo "clean: no src/tools changes"
```

## Anti-Drift Test Guards

- **Join Example regression check**: confirm `docs/agent-monitoring/schema.md`'s Join Example (the
  `Path('agent-monitoring/data').glob('*/runs.jsonl')`-style block, currently ~lines 470-502) is
  **unchanged** by this ticket's diff — it was already fixed by a prior child (`CONSUMERS-CORE`) and
  should not be re-touched:

  ```bash
  git diff docs/agent-monitoring/schema.md | grep -A3 -B3 "Join Example\|glob('\*/"
  ```

  Expect this hunk to show **no changes** — if it does, that's scope creep or an accidental
  regression, not a required fix.

- **Parity ledger historical-text guard**: confirm the diff to `docs/parity_ledger/infrastructure.yaml`
  touches only `INFRA-291`'s `divergence_note` field (an appended paragraph), not any other entry's
  `text`/`v2_evidence`/`divergence_note`:

  ```bash
  git diff docs/parity_ledger/infrastructure.yaml | grep "^-" | grep -v "^--- " 
  ```

  Expect **zero** removed lines (`^-` other than the diff header) — a pure-addition diff. Any removed
  line means existing historical text was altered, which this ticket's Out-of-Scope section forbids.

- **Archived/dated-doc non-touch guard**: confirm none of the explicitly-excluded historical files
  appear in the diff at all:

  ```bash
  git diff --name-only | grep -E "docs/REGISTRY\.yaml|docs/audits/D23|docs/audits/D24|docs/plans/archive/|_decision\.md$" && echo "UNEXPECTED: historical doc touched" || echo "clean"
  ```

- **`.claude/workflows/implement-ticket.js` functional-logic non-touch guard**: confirm the diff to
  this file, if any, only touches comment/string lines, never a line that is executable JS logic
  (heuristic: every changed line should contain `//` or be inside a template-literal string, not a
  bare statement):

  ```bash
  git diff .claude/workflows/implement-ticket.js
  ```

  Manually review — every hunk must be prose-only (matches the ticket's Out-of-Scope: "any functional
  code change" is forbidden here).
