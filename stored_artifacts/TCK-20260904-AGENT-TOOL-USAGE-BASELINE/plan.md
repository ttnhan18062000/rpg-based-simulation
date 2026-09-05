---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260904-AGENT-TOOL-USAGE-BASELINE
artifact_type: plan
tags: [agent-monitoring, ai, governance]
---

# Implementation Plan — TCK-20260904-AGENT-TOOL-USAGE-BASELINE

## Summary

Build one new read-only script, `tools/agent-monitoring/agent_tool_usage_baseline.py`, that
aggregates `agent-monitoring/data/*/tools.jsonl` rows into a per-agent tool-usage table: one row
per currently-registered `.claude/agents/*.md` agent (live-globbed, never hardcoded) plus one
`unattributed` row for every non-matching `agent` value (`null`, pseudo-agent literals, drift
literals like `orchestrator`), with per-(agent, tool-name) representative examples drawn verbatim
from `input_summary`. The script composes existing helpers rather than reimplementing them —
`load_data_glob` (`tools/agent-monitoring/validate.py:238`, re-exported via
`tools/agent-monitoring/generate_retro.py:38`) for the shard glob, and structurally mirrors
`tools/agent-monitoring/retrieval_baseline_metrics.py`'s shape (JSON-report `build_*_section`
functions feeding one `build_*_report` composer, a `main()` printing `json.dumps(..., sort_keys=True)`
to stdout) and its test file's reuse-guard / real-corpus zero-mutation pattern
(`tests/tools/test_retrieval_baseline_metrics.py:56` reuse guard, `:374-395` porcelain zero-diff
guard). This is new tooling only — no existing module, doc, or write path is modified except one
additive `docs/agent-monitoring/README.md` section.

**AC3 granularity resolved:** one representative example **per (agent, tool-name) pair** with a
nonzero count — not one example per tool-name globally. Rationale: the investigation's own stated
purpose (`investigation.md` lines 216–223) is that this table is evidence for M3's *per-agent*
`tools:` frontmatter scoping decision — "which tools does *this specific agent* actually invoke,
with what real inputs" — which only the per-(agent, tool) reading answers; a single global example
per tool name would tell M3 nothing about e.g. whether `investigator`'s own `Bash` calls look
different from `security-reviewer`'s. The `unattributed` bucket also gets its own per-tool examples
under this same rule (it behaves like any other row for AC3 purposes), since a non-matching-value
example is still useful context (e.g. showing what `orchestrator`'s tool calls look like) even
though `unattributed` itself is out of scope for frontmatter scoping.

## Steps

### Step 1 — Live agent-roster and shard-glob helpers, no aggregation logic yet
**Files:** `tools/agent-monitoring/agent_tool_usage_baseline.py` (new)
**Change:**
- Add `REPO_ROOT = Path(__file__).resolve().parent.parent.parent` and
  `AGENTS_DIR = REPO_ROOT / ".claude" / "agents"`.
- Add `def registered_agents() -> list[str]:` that globs `AGENTS_DIR.glob("*.md")`, strips the
  `.md` suffix, and returns a **sorted** list. Confirmed by direct `ls .claude/agents/*.md` during
  planning (2026-09-05) this currently returns exactly 16 names (`architecture-reviewer`,
  `concern-investigator`, `doc-updater`, `done-checker`, `implementer`, `investigator`,
  `mechanics-auditor`, `parity-updater`, `planner`, `security-reviewer`, `simulation-analyst`,
  `spec-document-reviewer`, `test-scoper`, `ticket-scoper`, `world-debugger`,
  `world-render-reviewer`) — but the function must never hardcode this list; it is derived live
  every call, per AC1's "not hardcoded or stale" wording and the investigation's Anti-Drift Hazards
  section.
- Add `DEFAULT_DATA_DIR = REPO_ROOT / "agent-monitoring" / "data"` and
  `def load_all_tool_rows(data_dir: Path = DEFAULT_DATA_DIR) -> list:` that imports and calls
  `load_data_glob(data_dir, "tools")` — the exact function defined at
  `tools/agent-monitoring/validate.py:238` (`def load_data_glob(data_dir: Path, source: str) -> list`,
  confirmed by direct read: sorts `data_dir.glob(f"*/{source}.jsonl")` and concatenates
  `load_jsonl()` results). Import it the same way `retrieval_baseline_metrics.py:29` does
  (`from generate_retro import load_data_glob`, itself re-exporting
  `tools/agent-monitoring/generate_retro.py:38`'s `from validate import load_data_glob`) — do not
  import directly from `validate.py`, to stay consistent with the one existing sibling's import
  path and keep a single reuse chain, not a second parallel one.
**Do NOT touch:** `validate.py`, `generate_retro.py`, `vocabulary.py` — read-only imports only, no
edits to any of their function bodies or exports.
**Verify:** `test_output_has_exactly_16_agent_rows_plus_unattributed` (agent roster half),
`test_glob_matches_all_dated_week_shards_and_unknown_week` (glob half).

### Step 2 — Agent-bucketing logic (registered vs. unattributed)
**Files:** `tools/agent-monitoring/agent_tool_usage_baseline.py`
**Change:** Add `def bucket_for(row: dict, known_agents: set[str]) -> str:` returning
`row.get("agent")` if it is a non-null string present in `known_agents`, else the literal string
`"unattributed"`. Per `docs/agent-monitoring/schema.md` (`agent` field row, confirmed by direct
read): `agent` is nullable, "Agent identifier active during this tool call, matching the `agent`
literal at the corresponding call site" — no schema-level allowlist exists, so bucketing must be a
pure membership check against the *live* `registered_agents()` set, not against
`vocabulary.py`'s `WORKFLOW_AGENTS`/`WORKFLOW_AGENT_PREFIXES` (`tools/agent-monitoring/vocabulary.py:39,68`,
confirmed by direct read of `is_known_agent()` at line 73) — those two sets classify
*legitimate-pseudo-agent-vs-drift within* the unattributed bucket, which this ticket's scope
explicitly does not need to distinguish (investigation.md: "this ticket's scope does not require
distinguishing documented-legitimate from undocumented-anomalous within that bucket"). Do not
import or call `is_known_agent` — that would silently reintroduce exactly the distinction the
ticket scopes out, and would also route `finalizer`/`claude`/`create-tickets`/
`implement-ticket-orchestrator` differently from `orchestrator`/`-resume`-suffixed values, when the
ticket's Scope requires all non-`.claude/agents/*.md` values to land in one bucket uniformly.
**Do NOT touch:** `vocabulary.py` itself, or any `WORKFLOW_AGENTS`/`WORKFLOW_AGENT_PREFIXES` set.
**Verify:** `test_null_and_non_matching_agent_values_bucket_to_unattributed`.

### Step 3 — Per-agent, per-tool count + example aggregation
**Files:** `tools/agent-monitoring/agent_tool_usage_baseline.py`
**Change:** Add `def build_usage_table(rows: list, known_agents: list) -> dict:` that:
1. Initializes every known agent (from Step 1's live list) plus `"unattributed"` as a key in the
   output dict, each starting with `{"count": 0, "tools": {}}` — this guarantees the zero-count
   rows AC1 requires exist even before any row is processed (satisfies
   `test_agent_row_present_with_zero_count_for_agents_with_no_real_rows` structurally, not by
   post-hoc backfill).
2. For each row: compute `agent = bucket_for(row, known_agents)` (Step 2), `tool = row.get("tool")`.
   Increment `table[agent]["count"]`. Under `table[agent]["tools"].setdefault(tool, {"count": 0,
   "example": None})`, increment `["count"]` and, only if `["example"]` is still `None`, set it to
   `row.get("input_summary")` verbatim (first-seen-wins; no attempt to pick a "best" example,
   since `input_summary` is already pre-truncated per-tool by the write path — see
   `docs/agent-monitoring/schema.md`'s `input_summary` field description, confirmed by direct read:
   "Max 120 chars", "first 80 chars of command for Bash" — this ticket's script must not
   re-truncate or otherwise transform the string, only pass it through and label it, per the
   Out-of-Scope line "Deriving exact Bash 'command class' beyond what input_summary's 120-char
   truncation actually supports").
3. Label every non-null example with an explicit `"truncated": true` marker (a sibling key next to
   `"example"`), satisfying AC3's "explicitly labeled as truncated/summarized" wording. This
   resolves the AC3 granularity question stated in the Summary above: the example lives under
   `table[agent]["tools"][tool]["example"]`, i.e. one example per (agent, tool) pair, not a single
   global per-tool-name example collapsed across agents.
**Do NOT touch:** No other reader of `agent-monitoring/data/` runs concurrently with this
aggregation in a way that matters here — this step only *reads* rows already loaded into memory by
Step 1's `load_all_tool_rows()`; it performs no file I/O of its own, so there is no write-race to
reason about for this step specifically (the write-side lock protocol in
`docs/agent-monitoring/schema.md`'s "Write locking" section, confirmed by direct read, governs
`PostToolUse` hook appends via `writer.py::write_line()` — this script never calls that path and
never opens `tools.jsonl` for writing).
**Verify:** `test_agent_row_present_with_zero_count_for_agents_with_no_real_rows`,
`test_every_nonzero_tool_entry_has_a_labeled_truncated_example`,
`test_example_is_verbatim_substring_of_a_real_row_not_paraphrased`.

### Step 4 — Sanity-check row-count reconciliation + CLI entrypoint
**Files:** `tools/agent-monitoring/agent_tool_usage_baseline.py`
**Change:** Add `def build_report(rows: list) -> dict:` that calls `registered_agents()`,
`build_usage_table(rows, known_agents)`, and additionally computes
`"total_rows_seen": len(rows)` and `"total_rows_across_all_agent_rows": sum(v["count"] for v in
table.values())` as two top-level report keys — both derived independently inside the script (one
from the raw loaded-rows list, one from summing the just-built table), so a discrepancy between
them is visible in the script's own output without relying on the test suite to catch it. Add
`def main(argv=None):` with an `argparse` parser (mirroring
`tools/agent-monitoring/retrieval_baseline_metrics.py`'s `main()` shape: no required args, prints
`json.dumps(report, indent=2, sort_keys=True)` to stdout, `if __name__ == "__main__": main()`).
Do not add a `--output` file-write flag unless the sibling precedent's `_assert_safe_output_path`
guard (`tools/agent-monitoring/manifest.py`, imported by `retrieval_baseline_metrics.py:31`) is
also reused verbatim — simplest compliant choice is to omit the flag entirely (stdout-only), since
AC4's read-only guarantee is strictly easier to prove with zero write capability in the script at
all; do not add unused write-capable surface area.
**Do NOT touch:** No file-write path is added to this script. Do not add a `--output` flag unless
reusing `manifest.py`'s existing path-safety guard exactly as `retrieval_baseline_metrics.py` does.
**Verify:** `test_sum_of_per_agent_counts_matches_wc_l_sanity_check_on_real_corpus`,
`test_cli_runs_against_real_corpus_and_prints_valid_json_or_table`.

### Step 5 — New test file
**Files:** `tests/tools/test_agent_tool_usage_baseline.py` (new)
**Change:** Write all 9 tests named in `test_plan.md`, structurally mirroring
`tests/tools/test_retrieval_baseline_metrics.py`'s own layout (confirmed by direct read of that
file's header comment and imports, lines 1–35): inline-dict unit tests per function for Steps 1–3
(no file I/O — construct synthetic row dicts directly), an `ast`-based reuse-guard test for Step 1
(mirror `test_retrieval_baseline_metrics.py:56`'s `_imported_names()` / `ast.parse` pattern —
assert `"load_data_glob"` appears in the module's imported names, not that a `load_data_glob`-named
local function was independently defined), a `tmp_path`-constructed fixture test for the
glob-matches-unknown-week case (synthetic `YYYY-Www` + `unknown-week` folders under `tmp_path`, per
test_plan.md — never the real corpus for this one, to stay deterministic and fast), and two
real-corpus integration tests using the exact `_porcelain_snapshot()` subprocess-based
`git status --porcelain -- agent-monitoring/` helper at
`tests/tools/test_retrieval_baseline_metrics.py:374-380` (copy this helper verbatim into the new
test file — it has no shared-import home today, so duplicating this specific ~7-line helper is the
same pattern the sibling file itself uses, not new drift) plus one CLI-subprocess smoke test.
**Do NOT touch:** `tests/tools/test_retrieval_baseline_metrics.py` itself — it must keep passing
unmodified (test_plan.md's Regression Surface section), proving this ticket didn't touch shared
helpers.
**Verify:** All 9 named tests pass; `pytest tests/tools/test_agent_tool_usage_baseline.py -v`.

### Step 6 — Regression sweep
**Files:** none (verification only)
**Change:** Run the three scoped pytest commands from `test_plan.md`'s "Scoped Pytest Commands"
section:
```
pytest tests/tools/test_agent_tool_usage_baseline.py -v
pytest tests/tools/test_record_events.py tests/tools/test_validate_agent_monitoring.py \
  tests/tools/test_retrieval_baseline_metrics.py tests/tools/test_agent_monitoring_manifest.py \
  tests/tools/test_monitoring_writer.py tests/tools/test_monitoring_writer_single_source.py \
  tests/tools/test_migrate_monitoring_data.py -v
pytest tests/tools/ -k "monitoring or agent_tool_usage or retrieval_baseline" -v
```
**Do NOT touch:** Do not edit any existing test in this regression list to make it pass — if one
fails, the failure is real and must be root-caused (per the project's Gate Integrity rule), not
routed around.
**Verify:** All commands exit 0.

### Step 7 — Docs: add README section
**Files:** `docs/agent-monitoring/README.md`
**Change:** Add one new section following the existing convention (confirmed by
investigation.md's citation of the "Skill Usage Metric" / "Done-Ticket Monitoring Coverage Audit" /
"Security Gate Firing Check" sections in this same file) — a short paragraph naming
`tools/agent-monitoring/agent_tool_usage_baseline.py`, what it reports (per-agent tool-call counts
+ labeled truncated examples, plus an `unattributed` bucket), and this ticket ID
(`TCK-20260904-AGENT-TOOL-USAGE-BASELINE`). Match the existing section's length and tone — a short
paragraph, not a full spec.
**Do NOT touch:** Any other section of this README; do not touch
`docs/agent-monitoring/schema.md` (confirmed accurate already, per investigation.md) or the epic
doc `docs/plans/agent_infrastructure/ai_first_hardening_epics/governance_capability_policy_epic.md`
(investigation.md explicitly recommends leaving that edit to whoever scopes M3 next, not this
ticket).
**Verify:** Manual read-through; no automated test covers doc prose content for this ticket.

## Scope Guards

- Do NOT modify `.claude/agents/*.md` `tools:` frontmatter on any agent file — that is
  `TCK-20260904-AGENT-TOOL-USAGE-BASELINE`'s dependent follow-up ticket's job, gated on this
  ticket's output table.
- Do NOT modify `agent-monitoring/` write paths, schema, shard-migration tooling, or any file under
  `agent-monitoring/data/` itself (the new script must be provably read-only per AC4/Step 6).
- Do NOT modify `tools/agent-monitoring/validate.py`, `generate_retro.py`, or `vocabulary.py` —
  import from them only.
- Do NOT attempt to derive a finer-grained "Bash command class" than `input_summary`'s existing
  120-char (80-char for Bash) truncation supports — pass the string through verbatim, label it
  truncated, do not re-parse or reconstruct.
- Do NOT edit `docs/agent-monitoring/schema.md` or the epic plan doc
  (`governance_capability_policy_epic.md`) — both explicitly out of scope per investigation.md.
- Do NOT edit `tests/tools/test_retrieval_baseline_metrics.py` or any other existing test file in
  the regression list — they must pass unmodified.
- Do NOT add a `docs/parity_ledger/` entry — no `src/` file is touched, no parity ledger overlap
  exists (investigation.md's Parity Ledger Overlap section).

## Dependency Map

- Step 1 (roster + glob helpers) has no dependency — first.
- Step 2 (bucketing) depends on Step 1's `registered_agents()`.
- Step 3 (aggregation) depends on Step 2's `bucket_for()`.
- Step 4 (report + CLI) depends on Step 3's `build_usage_table()`.
- Step 5 (tests) depends on Steps 1–4 existing to import against; individual tests within Step 5
  can be written in any order once the corresponding function exists.
- Step 6 (regression sweep) depends on Step 5 being complete.
- Step 7 (docs) is independent of Steps 1–6's code and can be done any time after the script's
  final shape (name, what it reports) is settled — placed last only so the README description is
  accurate to the finished script, not because of a hard technical dependency.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC1: exactly 16 agent rows + 1 unattributed row, live-derived, zero-count rows explicit | Steps 1, 2, 3 | `test_output_has_exactly_16_agent_rows_plus_unattributed`, `test_agent_row_present_with_zero_count_for_agents_with_no_real_rows`, `test_null_and_non_matching_agent_values_bucket_to_unattributed` |
| AC2: globs all shards, sum matches wc -l sanity check | Steps 1, 4 | `test_glob_matches_all_dated_week_shards_and_unknown_week`, `test_reuses_load_data_glob_not_a_fourth_loader`, `test_sum_of_per_agent_counts_matches_wc_l_sanity_check_on_real_corpus` |
| AC3: every tool-name entry has a real, labeled-truncated representative example | Step 3 | `test_every_nonzero_tool_entry_has_a_labeled_truncated_example`, `test_example_is_verbatim_substring_of_a_real_row_not_paraphrased` |
| AC4: script proven read-only against agent-monitoring/data/ | Step 4 (no write path added), Step 5's porcelain test | `test_script_is_read_only_against_real_agent_monitoring_data` |

## Anti-Drift Notes

- Every number cited in this plan (16 agents, 14 shards, 191,653 rows) is already stale evidence
  from investigation/planning time, not something to hardcode. The implementer must call
  `registered_agents()` and `load_data_glob()` live and let the real counts fall out at run/test
  time — do not assert a literal `16` or `191653` anywhere in the script itself; only the *test
  file* may assert `len(registered_agents()) == len(expected_from_live_glob)` style relative
  checks, never an absolute literal.
- The 6 agents with zero real tool-call rows today (`concern-investigator`, `mechanics-auditor`,
  `simulation-analyst`, `spec-document-reviewer`, `world-debugger`, `world-render-reviewer`) are the
  single most important finding for the downstream M3 scoping ticket — Step 3's initialize-first
  design (every known agent seeded with `count: 0` before any row is processed) is what guarantees
  they surface as explicit rows rather than silent omissions if the aggregation loop ever short-
  circuits or is refactored later.
- Do not import `vocabulary.py`'s `is_known_agent`/`WORKFLOW_AGENTS` into the bucketing logic
  (Step 2) — that would reintroduce a legitimate-vs-drift distinction inside `unattributed` that
  this ticket's scope explicitly defers to the (not-yet-scoped) ticket that would own
  `vocabulary.py` drift detection for `tools.jsonl`'s `agent` field.
- `input_summary` is a pre-truncated, per-tool-shaped string already (verbatim per
  `docs/agent-monitoring/schema.md`'s field table) — for the `Skill` tool specifically it is a
  Python dict-repr string, not JSON (`generate_retro.py:450` comment, confirmed by direct read);
  this script must not attempt `json.loads()` on any `input_summary` value or assume any tool's
  `input_summary` is machine-parseable beyond passing it through as an opaque, labeled string.
- The read-only guard (Step 5/AC4) must use the real `git status --porcelain -- agent-monitoring/`
  diff pattern, not a weaker mtime/size proxy — copy `_porcelain_snapshot()` verbatim from
  `test_retrieval_baseline_metrics.py:374-380`.

## Unresolved Questions

None. AC3's granularity ambiguity is resolved above (per-(agent, tool-name) pair). No other open
question from investigation.md blocks implementation: the `orchestrator`-literal root-cause
mystery and the 6-zero-count-agents finding are both flagged for downstream tickets, not decisions
this plan needs to make.

## Deviations

- **Neither this plan nor investigation.md anticipated 2 legacy-shaped `tools.jsonl` rows with no
  `tool` key at all** (`agent-monitoring/data/2026-W27/tools.jsonl:43`,
  `agent-monitoring/data/2026-W29/tools.jsonl:6946` — pre-dating the `tool`/`input_summary` fields'
  introduction, the same family of legacy shape `legacy_reader.py`'s `classify_provenance` already
  documents for `runs`/`events`). Step 3's literal `row.get("tool")` returns `None` for these two
  rows, and `json.dumps(..., sort_keys=True)` in Step 4's `main()` cannot sort a dict whose keys mix
  `None` with strings (`TypeError: '<' not supported between instances of 'NoneType' and 'str'`) —
  this only surfaces when running against the real corpus, not any synthetic fixture, since the
  plan's own Step 3 spec never mentioned this shape. Fixed with `tool = row.get("tool") or
  "unknown"` — a visible, explicitly-labeled fallback bucket rather than a crash or a silently
  unsortable `None` key. Both rows also lack `input_summary`, so this `"unknown"` bucket's `example`
  is `None` where it is the only match for a given agent — disclosed, not fabricated. This does not
  change any AC or step's intent; it is a defensive fix for real data the plan's steps did not
  foresee. No test in test_plan.md's 10 named tests exercises this exact 2-row edge case directly
  (the real-corpus integration tests exercise it implicitly, since they run against the real
  corpus and passed after the fix).

- **Reversal of the "Do NOT add a `docs/parity_ledger/` entry" scope guard above.** The Parity
  phase's independent review found that `docs/parity_ledger/infrastructure.yaml` already tracks
  agent-monitoring meta-tooling additions as first-class entries regardless of `src/` involvement
  (precedent: `INFRA-275`, `INFRA-282`, `INFRA-291`, `INFRA-315`, all citing `tools/agent-monitoring/
  *.py` scripts under the "Replay, telemetry, observability, workers" subsystem definition) — a
  precedent this plan's "no `src/` touched" reasoning did not check against. A new `verified`/`P2`
  entry, `INFRA-402`, was added citing this script as `v2_evidence`. This plan's Scope Guard above
  is superseded by that finding, recorded here rather than silently edited away.
