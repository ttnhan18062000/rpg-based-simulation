"""Regression tests for TCK-20260710-CURRENT-RUN-SIDECAR-BASH and its follow-up,
TCK-20260711-MONITORING-TOOLCOUNT-SIDECAR-COLLISION.

Static, raw-source-text-parsing tests against `.claude/workflows/implement-ticket.js` and
`docs/agent-monitoring/schema.md` — reuses tests/tools/test_tag_skill_mapping_check.py's
established pattern of `Path.read_text()` against these non-Python source files. The workflow
file is never executed (no JS test runner exists in this repo for `.claude/workflows/*.js`).

Covers: the former per-prompt "Step 0b" (and Finalize's combined "Step 0") sidecar-write
agent-prompt-text instruction has been replaced by an orchestrator-side `writeSidecar(seq)`
helper invoked via `bash()` immediately before each of the 10 corresponding `await agent(...)`
calls (the 9 two-line sites: Investigate, Plan, Review, Implement, Architecture-Verify, Test,
Parity, Security-Review, Verify; plus Finalize's single combined site).

Two follow-up fixes from TCK-20260711-MONITORING-TOOLCOUNT-SIDECAR-COLLISION, which found (via
direct empirical cross-check of tool_call_count against tools.jsonl ground truth) that ~35% of
historical events had a wrong count:
- Scope (`ticket-scoper`) now HAS sidecar coverage (previously permanently sidecar-free by
  design — this was TCK-20260710-CURRENT-RUN-SIDECAR-BASH's own recommended follow-up, Decision
  1). It can't reuse the `writeSidecar(seq)` helper (which closes over `tid`, not yet known when
  creating a brand-new ticket) — it inlines two bash() branches instead.
- `writeMonitoring`'s own `agent()` call remains permanently sidecar-*tracking*-free (it never
  gets its own `(run_id, seq)`), but its internal Step 5 "clear the sidecar" instruction moved to
  Step 0 (run first, not last) — previously, Steps 1-4's own Bash/python calls executed *before*
  the clear, so they were silently attributed to whatever phase's sidecar was still active,
  inflating that phase's true tools.jsonl row count beyond what Step 2's own snapshot recorded.
"""
import re
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent.parent
_WORKFLOW_PATH = _REPO_ROOT / ".claude" / "workflows" / "implement-ticket.js"
_SCHEMA_DOC_PATH = _REPO_ROOT / "docs" / "agent-monitoring" / "schema.md"

_MONITORING_TOOLS_DIR = _REPO_ROOT / "tools" / "agent-monitoring"
if str(_MONITORING_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_MONITORING_TOOLS_DIR))

from record_events import REQUIRED  # noqa: E402

_SIDECAR_WRITE_PROMPT_TEXT = (
    "run \\`python3 -c \"import json; open('.claude/current_run','w')"
    ".write(json.dumps({'run_id':'"
)

# The 10 covered call sites: the exact text immediately preceding each `await agent(` opening,
# after the Step 0b relocation. Order matches the file's phase order.
_COVERED_SITE_ADJACENCY = [
    "  await writeSidecar(events.length + 1, 'Investigate', 'investigator')\n  investigation = await agent(",
    "  await writeSidecar(events.length + 1, 'Plan', 'planner')\n  plan = await agent(",
    "  await writeSidecar(events.length + 1, 'Review', 'architecture-reviewer')\n  review = await agent(",
    "await writeSidecar(events.length + 1, 'Implement', 'implementer')\nconst implementation = await agent(",
    "  await writeSidecar(events.length + 1, 'Architecture-Verify', 'architecture-reviewer')\n  const archVerify = await agent(",
    "await writeSidecar(events.length + 1, 'Test', 'test-scoper')\nconst testResult = await agent(",
    "  await writeSidecar(events.length + 1, 'Parity', 'parity-updater')\n  const parity = await agent(",
    "  await writeSidecar(events.length + 1, 'Security-Review', 'security-reviewer')\n  const securityReview = await agent(",
    "await writeSidecar(events.length + 1, 'Verify', 'done-checker')\nconst doneCheck = await agent(",
    "await writeSidecar(events.length + 1, 'Finalize', 'finalizer')\nawait agent(",
]

_NINE_TWO_LINE_SITE_LABELS = [
    "investigate", "plan", "architecture-review", "implement", "architecture-verify",
    "test-scope-and-run", "parity-update", "security-review", "done-check",
]


def _read_workflow_source() -> str:
    return _WORKFLOW_PATH.read_text(encoding="utf-8")


def _read_schema_doc() -> str:
    return _SCHEMA_DOC_PATH.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# 1. No leftover Step 0b sidecar-write prompt text
# ---------------------------------------------------------------------------


def test_no_step_0b_agent_prompt_sidecar_text_remains():
    source = _read_workflow_source()
    assert _SIDECAR_WRITE_PROMPT_TEXT not in source
    assert "register this agent call for tool tracking" not in source


# ---------------------------------------------------------------------------
# 2. writeSidecar(seq) precedes each of the 10 covered agent() calls, with
#    nothing else (no other agent() call) interleaved.
# ---------------------------------------------------------------------------


def test_sidecar_bash_write_precedes_each_covered_agent_call():
    source = _read_workflow_source()
    for adjacency in _COVERED_SITE_ADJACENCY:
        assert adjacency in source, f"expected adjacency not found: {adjacency!r}"

    # Exactly 10 writeSidecar() calls total (9 two-line sites + Finalize).
    assert len(re.findall(r"await writeSidecar\(events\.length \+ 1, '[^']+', '[^']+'\)", source)) == 10

    # No other `await agent(` call sits between a writeSidecar call and its paired agent() call —
    # each adjacency string above already asserts direct (whitespace-only) adjacency, so a passing
    # match on all 10 already proves nothing is interleaved.


# test_step_0_ts_capture_lines_unchanged_at_all_nine_sites removed —  its guard (protecting this
# ticket's Step 0 `date -u` sites from C1's sidecar work) is obsolete now that
# TCK-20260710-STEP0-TS-ORCHESTRATOR-BASH has itself removed those sites. See
# tests/tools/test_step0_ts_orchestrator.py for the replacement coverage.


# ---------------------------------------------------------------------------
# 3. Finalize's combined single-line "Step 0" sidecar write is relocated too
# ---------------------------------------------------------------------------


def test_finalize_call_site_still_registers_sidecar():
    source = _read_workflow_source()
    finalize_block_match = re.search(
        r"phase\('Finalize'\).*?await writeSidecar\(events\.length \+ 1, 'Finalize', 'finalizer'\)\nawait agent\(\n"
        r"\s*`Finalize ticket \$\{tid\}",
        source,
        re.DOTALL,
    )
    assert finalize_block_match is not None
    # Finalize's prompt no longer contains its own combined "Step 0" sidecar-write line.
    finalize_prompt_start = finalize_block_match.end()
    finalize_prompt_excerpt = source[finalize_prompt_start:finalize_prompt_start + 400]
    assert "current_run" not in finalize_prompt_excerpt


# ---------------------------------------------------------------------------
# 4. writeMonitoring's own agent() call remains untracked (no orchestrator-side writeSidecar()
#    call precedes it) — but its own Step 0/Steps 1-3 ordering is covered separately below (item 7).
# ---------------------------------------------------------------------------


def test_writeMonitoring_call_has_no_preceding_sidecar_write():
    source = _read_workflow_source()

    monitoring_write_start = source.index("const writeMonitoring = async")
    monitoring_write_label = source.index("{ label: 'monitoring-write' }", monitoring_write_start)
    monitoring_write_region = source[monitoring_write_start:monitoring_write_label]
    assert "writeSidecar(" not in monitoring_write_region


def test_scope_phase_has_sidecar_coverage():
    # TCK-20260711-MONITORING-TOOLCOUNT-SIDECAR-COLLISION: Scope now registers a sidecar value
    # before its agent() call — net-new coverage, not a relocation, so it can't reuse the
    # writeSidecar(seq) helper (tid isn't known yet for a brand-new ticket). Two inline branches:
    # real {run_id: ticketId, seq: 1} when resuming; a neutral clear when creating a new ticket.
    source = _read_workflow_source()

    phase_scope_idx = source.index("phase('Scope')")
    scope_start = source.index("const ticketInfo = await agent(")
    scope_label = source.index("{ label: 'scope',", scope_start)
    pre_scope_region = source[phase_scope_idx:scope_start]
    scope_region = source[scope_start:scope_label]

    assert "if (ticketId) {" in pre_scope_region
    assert "open('.claude/current_run', 'w').write(json.dumps({'run_id': sys.argv[1], 'seq': 1, 'phase': 'Scope', 'agent': 'ticket-scoper'}))" in pre_scope_region
    assert '"${ticketId}" 2>/dev/null || true' in pre_scope_region
    assert "printf '{}' > .claude/current_run 2>/dev/null || true" in pre_scope_region

    # Scope's own "Step 0b" (inside the agent prompt itself) is an unrelated context-warm-start
    # instruction (search_docs/graphify), never a sidecar write — must not be confused with the
    # orchestrator-side sidecar registration added above pre_scope_region.
    assert "search_docs" in scope_region
    assert "writeSidecar(" not in scope_region


# ---------------------------------------------------------------------------
# 5. writeSidecar(seq) helper shape — argv-quoted, not JSON-embedded
# ---------------------------------------------------------------------------


def test_tid_and_seq_and_phase_and_agent_passed_as_argv_not_json_embedded():
    source = _read_workflow_source()
    helper_match = re.search(
        r"const writeSidecar = async \(seq, phase, agent\) => \{.*?\n\}\n",
        source,
        re.DOTALL,
    )
    assert helper_match is not None
    helper_body = helper_match.group(0)

    # Args passed as individually-quoted argv elements, never JSON-embedded in the -c string.
    assert '"${tid}" "${seq}" "${phase}" "${agent}"' in helper_body
    assert "sys.argv[1]" in helper_body
    assert "sys.argv[2]" in helper_body
    assert "sys.argv[3]" in helper_body
    assert "sys.argv[4]" in helper_body
    # No inline JSON literal containing ${tid}/${seq}/${phase}/${agent} directly inside the python3 -c string.
    assert "'run_id':'${tid}'" not in helper_body
    assert "'seq':${seq}" not in helper_body
    assert "'phase': '${phase}'" not in helper_body
    assert "'agent': '${agent}'" not in helper_body
    # Fail-open per CLAUDE.md's "monitoring write failure must never fail the workflow" rule.
    assert "2>/dev/null || true" in helper_body


def test_writeSidecar_defined_once_after_pushEvent_before_classifyChecklistFailure():
    source = _read_workflow_source()
    push_event_idx = source.index("const pushEvent = (phaseLabel")
    write_sidecar_idx = source.index("const writeSidecar = async (seq, phase, agent)")
    classify_idx = source.index("const classifyChecklistFailure")
    assert push_event_idx < write_sidecar_idx < classify_idx
    assert source.count("const writeSidecar = async (seq, phase, agent)") == 1


# ---------------------------------------------------------------------------
# 6. schema.md no longer describes the agent-self-report sidecar mechanism
# ---------------------------------------------------------------------------


def test_schema_doc_no_longer_describes_agent_self_report_mechanism():
    doc = _read_schema_doc()
    assert "Each agent prompt includes an early Bash step that writes" not in doc
    assert "Written by the agent to `.claude/current_run` as its first Bash step" not in doc
    assert "not computed the way it is for implement-ticket/implement-epic" not in doc

    # New orchestrator-side mechanism description present.
    assert "writeSidecar(seq)" in doc
    assert "implement-ticket.js" in doc

    # Both create-tickets and implement-epic gaps documented (implement-epic's gap was previously
    # undocumented — this ticket's investigation surfaced it).
    assert "create-tickets" in doc
    assert "implement-epic" in doc
    assert "neither ever has" in doc


def test_schema_doc_documents_tools_jsonl_phase_agent_fields():
    doc = _read_schema_doc()

    fields_table_start = doc.index("## `agent-monitoring/tools.jsonl`")
    fields_table_end = doc.index("### Write locking", fields_table_start)
    fields_table_region = doc[fields_table_start:fields_table_end]

    assert "| `phase` | string | Yes |" in fields_table_region
    assert "| `agent` | string | Yes |" in fields_table_region
    assert "TCK-20260719-LIVE-PHASE-AGENT-LABEL" in fields_table_region


# ---------------------------------------------------------------------------
# 7. Anti-drift guard: writeMonitoring's sidecar-clear now runs FIRST (Step 0), not last.
#
# TCK-20260711-MONITORING-TOOLCOUNT-SIDECAR-COLLISION found (via direct empirical cross-check of
# tool_call_count against tools.jsonl ground truth) that the clear-last ordering caused
# writeMonitoring's own Bash/python calls to be silently attributed to whatever phase's sidecar
# was still active — inflating that phase's true row count. Moving the clear to Step 0 (before
# every other step) makes writeMonitoring's own calls correctly unattributed (run_id: null)
# instead. This intentionally supersedes the original clear-last ordering asserted by this test's
# previous version — the original intent ("writeMonitoring stays sidecar-free by design") is
# preserved and, in fact, more faithfully achieved this way than the previous ordering actually
# achieved it.
#
# TCK-20260719-COST-PROXY-WRITE-PATH removed the old Step 2 (an inline python3 -c TOOL_STATS
# compute, now done deterministically inside record_events.py at write time instead) — the prompt
# is now 4 steps (0-3), not 5 (0-4). Updated below to match; the Step 0-runs-first invariant this
# test guards is otherwise unchanged.
# ---------------------------------------------------------------------------


def test_writeMonitoring_step0_sidecar_clear_precedes_other_steps():
    source = _read_workflow_source()
    assert "Run via Bash: printf '{}' > .claude/current_run" in source

    monitoring_write_start = source.index("const writeMonitoring = async")
    step0_idx = source.index("Step 0 — clear the tool-tracking sidecar FIRST", monitoring_write_start)
    step1_idx = source.index("Step 1 — get current timestamp", monitoring_write_start)
    step2_idx = source.index("Step 2 — build and write events", monitoring_write_start)
    step3_idx = source.index("Step 3 — write run record", monitoring_write_start)
    assert step0_idx < step1_idx < step2_idx < step3_idx

    # The old inline TOOL_STATS-compute step is gone — record_events.py computes
    # tool_call_count/cost_proxy_score itself now (TCK-20260719-COST-PROXY-WRITE-PATH).
    assert "Step 4 — write run record" not in source
    assert "compute tool_call_count and cost_proxy_score per agent seq from tools.jsonl" not in source
    assert "Save the JSON dict result as TOOL_STATS" not in source

    # The old trailing "Step 5 — clear..." label is gone — there is exactly one sidecar-clear
    # instruction in writeMonitoring now, at Step 0, not a duplicate leftover at the end.
    assert "Step 5 — clear the tool-tracking sidecar" not in source
    monitoring_write_label_idx = source.index("{ label: 'monitoring-write' }", monitoring_write_start)
    monitoring_prompt_region = source[monitoring_write_start:monitoring_write_label_idx]
    assert monitoring_prompt_region.count("printf '{}' > .claude/current_run") == 1


# ---------------------------------------------------------------------------
# 8. Anti-drift guard: record_events.py's REQUIRED field set is unmodified
# ---------------------------------------------------------------------------


def test_record_events_required_fields_unchanged():
    assert REQUIRED == {"run_id", "seq", "ts", "phase", "agent", "summary", "status"}


# ---------------------------------------------------------------------------
# 9. All 9 two-line site labels are still present in the file (sanity check
#    that no call site was accidentally dropped during relocation)
# ---------------------------------------------------------------------------


def test_all_nine_two_line_site_labels_present():
    source = _read_workflow_source()
    for label in _NINE_TWO_LINE_SITE_LABELS:
        assert f"label: '{label}'" in source, f"missing label site: {label}"
