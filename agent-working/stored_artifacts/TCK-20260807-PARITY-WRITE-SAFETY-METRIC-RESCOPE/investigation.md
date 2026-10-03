---
status: active
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260807-PARITY-WRITE-SAFETY-METRIC-RESCOPE
artifact_type: investigation
tags: [agent-monitoring, data-quality]
---

# Investigation — TCK-20260807-PARITY-WRITE-SAFETY-METRIC-RESCOPE

## Current logic (confirmed against `tools/agent-monitoring/generate_retro.py`)

`_is_parity_ledger_yaml_write(tool_row)` (line 235): `True` for ANY `Edit`/`Write` row whose
`input_summary` contains both `"docs/parity_ledger/"` and `".yaml"` — no other condition,
independent of `run_id`.

`compute_tool_safety_metrics(events, tools)` (line 743) calls it over the **whole `tools`
argument as passed in**, unscoped to any `(run_id, seq)` pair (unlike `search_before_grep`, which
IS scoped to real Investigate-phase pairs derived from `events`). This is the exact gap: any
correct, ordinary `parity-updater` edit to a ledger YAML — the very thing CLAUDE.md's
Authoritative Mechanics Rule *requires* after a behavior change — counts identically to a genuine
`parity_index.py` read-only-guarantee violation.

`_is_unsafe_parity_build_call(tool_row)` (line 242) is unaffected and stays out of scope — it is
already narrow (flags `parity_index.py build` calls missing `--db-path` or pointing at the real
`parity-index/parity.db` path), not implicated in this finding.

## Rescope design

Change `parity_write_safety`'s definition from "any yaml edit" to "a yaml edit AND a
`parity_index.py` invocation co-occurring in the same run" — the actual dangerous pattern
(editing the YAML source and separately touching the derived read-only index/db within one
agent's own run), not a normal parity-ledger edit alone.

**Granularity: same `run_id`, not same `(run_id, seq)`.** The ticket's own Assumptions section
raised this as open. Chose `run_id`-level (broader) over `(run_id, seq)`-level (narrower) because:
the risk this metric protects against is an agent's own session touching both the human-editable
YAML source and the machine-built index/db at any point during one run — not necessarily in the
same phase. A same-run, different-phase occurrence (e.g. Implement phase edits the yaml, Parity
phase separately runs a `parity_index.py build`) is still the same run's own tool history creating
the risk this metric exists to catch. Narrowing to `(run_id, seq)` would under-count real risk
without a documented reason to prefer it.

## Baseline preservation check

`TCK-20260731-PARITY-INDEX-EPIC`'s 4 child runs (the metric's own original validation baseline,
per `TCK-20260803-RETRO-TOOL-SAFETY-AUDIT`'s re-verification) already show
`parity_ledger_yaml_write_count = 0` under the CURRENT unscoped logic — none of those 4 runs touch
`docs/parity_ledger/*.yaml` directly at all (they build/test `parity_index.py` itself, not edit
ledger content). Since the rescoped logic is *more* restrictive (a superset condition — a row must
already satisfy the current predicate before the new co-occurrence check even applies), any run
that already yields 0 under the old logic still yields 0 under the new logic. Baseline preserved
by construction, no separate live re-run of those 4 historical runs needed to confirm this.

## Real-corpus false-signal confirmation (re-verified this session — correcting an initial over-broad check)

First pass used a broad `"parity_index.py" in input_summary` co-occurrence signal and found 2
`run_id`s that would still, incorrectly, count as "violations": `TCK-20260803-RETRO-TOOL-SAFETY-AUDIT`
(its only `parity_index.py` mentions are inside `grep` PATTERN TEXT searching for that literal
filename — investigating this exact metric, never actually invoking the tool) and
`TCK-20260803-DOC-UPDATER-VOCAB-REGISTRATION` (a single harmless `python3 tools/parity_index.py
--help` call, no `build` subcommand, no db touched at all). Neither is a real risk — a broad
substring match on the filename is too permissive and would have re-introduced 2 new false
positives even after the rescope. **Corrected the co-occurrence signal to require the
`parity_index.py build` subcommand specifically** (reusing `_is_unsafe_parity_build_call`'s own
existing narrower precondition: `"parity_index.py" in summary and "build" in summary`) rather than
any mention of the filename — this is the actual dangerous action (writing/rebuilding the derived
index), not merely referencing the tool.

Re-run with the corrected signal: **zero** overlap between the 121 `run_id`s that have a
`docs/parity_ledger/*.yaml` `Edit`/`Write` and the 1 `run_id`
(`TCK-20260731-PARITY-IMPACT-PROOF`) that has a real `parity_index.py build` call anywhere in the
current corpus. The rescoped count drops the false-signal population to 0 without discarding any
genuine risk case (there is currently no genuine co-occurrence anywhere in the corpus to preserve).
Matches `TCK-20260803-RETRO-TOOL-SAFETY-AUDIT`'s own prior finding (355 matches, 114 unrelated
tickets, all ordinary edits) at full-corpus scale, and refines it with the corrected signal.

## Report copy

The rendered "Parity Ledger Write-Safety" heading and its surrounding prose in
`compute_tool_safety_metrics`'s docstring / the Markdown-render function both describe the OLD
"zero-tolerance count of every Edit/Write" semantics — both need updating to describe the new,
narrower "yaml edit co-occurring with a parity_index.py invocation in the same run" condition so
the label doesn't stay misleading even after the undercount.
