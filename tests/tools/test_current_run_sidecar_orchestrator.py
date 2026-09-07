"""Regression tests for TCK-20260710-CURRENT-RUN-SIDECAR-BASH and its follow-up,
TCK-20260711-MONITORING-TOOLCOUNT-SIDECAR-COLLISION.

Static, raw-source-text-parsing tests against `.claude/workflows/implement-ticket.js` and
`docs/agent-monitoring/schema.md` — reuses tests/tools/test_tag_skill_mapping_check.py's
established pattern of `Path.read_text()` against these non-Python source files. The workflow
file is never executed (no JS test runner exists in this repo for `.claude/workflows/*.js`).

Covers: the former per-prompt "Step 0b" (and Finalize's combined "Step 0") sidecar-write
agent-prompt-text instruction has been replaced by an orchestrator-side `writeSidecar(seq)`
helper invoked via `bash()` immediately before each of the 11 corresponding `await agent(...)`
calls (the 10 two-line sites: Investigate, Plan, Review, Implement, Document-Update,
Architecture-Verify, Test, Parity, Security-Review, Verify; plus Finalize's single combined site).
Document-Update site added by TCK-20260803-DOC-UPDATER-CORE-WIRING, following the exact same
writeSidecar(seq)-then-agent() adjacency template as every other two-line site.

TCK-20260904-SHADOW-REVIEWER-LOGGING adds 2 more `writeSidecar()` call sites — an advisory shadow
candidate-reviewer call each for Architecture-Verify and Security-Review — but these deliberately
use a distinct NEGATIVE-seq expression (`writeSidecar(archShadowSeq, ...)` /
`writeSidecar(securityShadowSeq, ...)`), never the positive `events.length + 1 + seqOffset`
idiom the original 11 use, since reusing the positive form would collide with the enclosing
production phase's own `(run_id, seq)` tools.jsonl bucket. They are counted and asserted
separately, below (see `test_sidecar_bash_write_precedes_each_covered_agent_call`'s second
assertion) — the original `== 11` count/adjacency list stays unchanged.

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
from record_run import REQUIRED as RUN_REQUIRED  # noqa: E402

_SIDECAR_WRITE_PROMPT_TEXT = (
    "run \\`python3 -c \"import json; open('.claude/current_run','w')"
    ".write(json.dumps({'run_id':'"
)

# The 10 covered call sites: the exact text immediately preceding each `await agent(` opening,
# after the Step 0b relocation. Order matches the file's phase order.
# Since TCK-20260728-MONITORING-PAUSE-RESUME-SEQ-COLLISION, each `events.length + 1` expression
# carries a `+ seqOffset` term so a resumed session's seq numbering continues past a prior
# session's instead of restarting at 1.
_COVERED_SITE_ADJACENCY = [
    "  await writeSidecar(events.length + 1 + seqOffset, 'Investigate', 'investigator')\n  investigation = await agent(",
    "  await writeSidecar(events.length + 1 + seqOffset, 'Plan', 'planner')\n  plan = await agent(",
    "  await writeSidecar(events.length + 1 + seqOffset, 'Review', 'architecture-reviewer')\n  review = await agent(",
    "await writeSidecar(events.length + 1 + seqOffset, 'Implement', 'implementer')\nconst implementation = await agent(",
    "await writeSidecar(events.length + 1 + seqOffset, 'Document-Update', 'doc-updater')\nconst docUpdate = await agent(",
    "  await writeSidecar(events.length + 1 + seqOffset, 'Architecture-Verify', 'architecture-reviewer')\n  const archVerify = await agent(",
    "await writeSidecar(events.length + 1 + seqOffset, 'Test', 'test-scoper')\nconst testResult = await agent(",
    "  await writeSidecar(events.length + 1 + seqOffset, 'Parity', 'parity-updater')\n  const parity = await agent(",
    "  await writeSidecar(events.length + 1 + seqOffset, 'Security-Review', 'security-reviewer')\n  const securityReview = await agent(",
    "      await writeSidecar(archShadowSeq, 'Architecture-Verify', 'architecture-reviewer-shadow')\n      const archVerifyShadow = await agent(",
    "      await writeSidecar(securityShadowSeq, 'Security-Review', 'security-reviewer-shadow')\n      const securityReviewShadow = await agent(",
    "await writeSidecar(events.length + 1 + seqOffset, 'Verify', 'done-checker')\nconst doneCheck = await agent(",
    "await writeSidecar(events.length + 1 + seqOffset, 'Finalize', 'finalizer')\nawait agent(",
]

_TEN_TWO_LINE_SITE_LABELS = [
    "investigate", "plan", "architecture-review", "implement", "doc-update", "architecture-verify",
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
# 2. writeSidecar(seq) precedes each of the 11 covered agent() calls, with
#    nothing else (no other agent() call) interleaved.
# ---------------------------------------------------------------------------


def test_sidecar_bash_write_precedes_each_covered_agent_call():
    source = _read_workflow_source()
    for adjacency in _COVERED_SITE_ADJACENCY:
        assert adjacency in source, f"expected adjacency not found: {adjacency!r}"

    # Exactly 11 writeSidecar() calls total (10 two-line sites + Finalize).
    assert len(re.findall(r"await writeSidecar\(events\.length \+ 1 \+ seqOffset, '[^']+', '[^']+'\)", source)) == 11

    # Two additional writeSidecar() calls for the shadow-reviewer mechanism
    # (TCK-20260904-SHADOW-REVIEWER-LOGGING) use a NEGATIVE seq expression on purpose — reusing
    # the positive events.length + 1 + seqOffset idiom here would collide with the enclosing
    # production phase's own (run_id, seq) tools.jsonl bucket. Counted separately from the
    # positive-seq assertion above.
    assert len(re.findall(
        r"await writeSidecar\((archShadowSeq|securityShadowSeq), '[^']+', '[^']+-shadow'\)", source
    )) == 2

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
        r"phase\('Finalize'\).*?await writeSidecar\(events\.length \+ 1 \+ seqOffset, 'Finalize', 'finalizer'\)\nawait agent\(\n"
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
    # real {run_id: ticketId, seq: seqOffset + 1} when resuming; a neutral clear when creating a
    # new ticket. seq is now resume-aware (TCK-20260728-MONITORING-PAUSE-RESUME-SEQ-COLLISION) —
    # int(sys.argv[2]) reads the seqOffset-derived value computed by resolveSeqOffset(), rather
    # than the old hardcoded literal 1, so a resumed session's Scope sidecar write continues past
    # a prior session's max seq instead of colliding with it.
    source = _read_workflow_source()

    phase_scope_idx = source.index("phase('Scope')")
    scope_start = source.index("const ticketInfo = await agent(")
    scope_label = source.index("{ label: 'scope',", scope_start)
    pre_scope_region = source[phase_scope_idx:scope_start]
    scope_region = source[scope_start:scope_label]

    assert "if (ticketId) {" in pre_scope_region
    assert "open('.claude/current_run', 'w').write(json.dumps({'run_id': sys.argv[1], 'seq': int(sys.argv[2]), 'phase': 'Scope', 'agent': 'ticket-scoper'}))" in pre_scope_region
    assert '"${ticketId}" "${seqOffset + 1}" 2>/dev/null || true' in pre_scope_region
    assert "printf '{}' > .claude/current_run 2>/dev/null || true" in pre_scope_region
    assert "resolveSeqOffset(" in pre_scope_region
    assert "seqOffset = await resolveSeqOffset(ticketId)" in pre_scope_region

    # Scope's own "Step 0b" (inside the agent prompt itself) is an unrelated context-warm-start
    # instruction (search_docs/graphify), never a sidecar write — must not be confused with the
    # orchestrator-side sidecar registration added above pre_scope_region.
    assert "search_docs" in scope_region
    assert "writeSidecar(" not in scope_region


def test_new_ticket_branch_seq_offset_is_zero_not_null():
    # TCK-20260728-MONITORING-PAUSE-RESUME-SEQ-COLLISION anti-drift guard: the brand-new-ticket
    # branch (no ticketId yet) must leave seqOffset at its safe `0` default, never call the
    # resolveSeqOffset lookup for a run_id that doesn't exist yet, and never let seqOffset become
    # NaN/null/undefined for the overwhelmingly common non-resumed path.
    source = _read_workflow_source()

    assert "let seqOffset = 0" in source

    # Slice the whole if/else statement using the next known landmark (TICKET_SCHEMA's
    # declaration, which directly follows) rather than brace-matching — the else branch's own
    # `printf '{}'` literal contains a bare `}` that would break naive brace-counting.
    seq_offset_decl_idx = source.index("let seqOffset = 0")
    ticket_schema_idx = source.index("const TICKET_SCHEMA = {", seq_offset_decl_idx)
    if_else_region = source[seq_offset_decl_idx:ticket_schema_idx]

    else_marker_idx = if_else_region.index("} else {")
    if_branch = if_else_region[:else_marker_idx]
    else_branch = if_else_region[else_marker_idx:]

    assert "resolveSeqOffset(" in if_branch
    assert "resolveSeqOffset(" not in else_branch


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

    fields_table_start = doc.index("## `tools` (`agent-monitoring/data/YYYY-Www/tools.jsonl`)")
    fields_table_end = doc.index("### Write locking", fields_table_start)
    fields_table_region = doc[fields_table_start:fields_table_end]

    assert "| `phase` | string | Yes |" in fields_table_region
    assert "| `agent` | string | Yes |" in fields_table_region
    assert "TCK-20260719-LIVE-PHASE-AGENT-LABEL" in fields_table_region


def test_schema_doc_documents_pause_resume_seq_collision_fix():
    # TCK-20260728-MONITORING-PAUSE-RESUME-SEQ-COLLISION: the third attribution mechanism must be
    # documented alongside the two TCK-20260711-MONITORING-TOOLCOUNT-SIDECAR-COLLISION mechanisms,
    # in the same "How tool calls are attributed to agent events" section.
    doc = _read_schema_doc()

    section_start = doc.index("### How tool calls are attributed to agent events")
    section_end = doc.index("### `status` values", section_start)
    section_region = doc[section_start:section_end]

    assert "TCK-20260728-MONITORING-PAUSE-RESUME-SEQ-COLLISION" in section_region
    assert "compute_seq_offset" in section_region or "seqOffset" in section_region
    assert "compute_multi_invocation_collision_report" in section_region


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
# 9. All 10 two-line site labels are still present in the file (sanity check
#    that no call site was accidentally dropped during relocation)
# ---------------------------------------------------------------------------


def test_all_ten_two_line_site_labels_present():
    source = _read_workflow_source()
    for label in _TEN_TWO_LINE_SITE_LABELS:
        assert f"label: '{label}'" in source, f"missing label site: {label}"


# ---------------------------------------------------------------------------
# 10. TCK-20260730-CLAUDE-EXECUTION-IDENTITY — executionId/PROVIDER generated once,
#     after tid, before writeSidecar/writeMonitoring are defined; threaded into both
#     function bodies via closure only (never a widened parameter list or call-site edit).
# ---------------------------------------------------------------------------


def test_execution_id_generated_once_and_reused_across_events():
    source = _read_workflow_source()

    tid_idx = source.index("const tid = ticketInfo.ticket_id")
    provider_idx = source.index("const PROVIDER = 'claude'")
    exec_id_idx = source.index("const executionId = `${PROVIDER}-${tid}-${execIdSuffix}`")
    write_sidecar_idx = source.index("const writeSidecar = async (seq, phase, agent)")
    write_monitoring_idx = source.index("const writeMonitoring = async")

    assert tid_idx < provider_idx < exec_id_idx < write_sidecar_idx < write_monitoring_idx

    # Generated exactly once — no re-computation anywhere else in the file.
    assert source.count("const executionId = ") == 1
    assert source.count("const PROVIDER = ") == 1


def test_writeSidecar_body_includes_execution_id_and_provider_via_closure_not_param():
    source = _read_workflow_source()
    helper_match = re.search(
        r"const writeSidecar = async \(seq, phase, agent\) => \{.*?\n\}\n",
        source,
        re.DOTALL,
    )
    assert helper_match is not None
    helper_body = helper_match.group(0)

    # Signature not widened — identity fields threaded via closure only.
    assert "const writeSidecar = async (seq, phase, agent) => {" in helper_body

    assert "'execution_id': sys.argv[5]" in helper_body
    assert "'provider': sys.argv[6]" in helper_body
    # New argv elements appended strictly after "${agent}" — the existing 4-arg substring
    # (asserted unbroken by test_tid_and_seq_and_phase_and_agent_passed_as_argv_not_json_embedded)
    # is a prefix of the new 6-arg argv line, never split apart.
    assert '"${tid}" "${seq}" "${phase}" "${agent}" "${executionId}" "${PROVIDER}"' in helper_body


def test_writeMonitoring_prompt_embeds_execution_id_provider_ticket_id_in_events_and_run_record():
    source = _read_workflow_source()

    monitoring_write_start = source.index("const writeMonitoring = async")
    monitoring_write_label_idx = source.index("{ label: 'monitoring-write' }", monitoring_write_start)
    monitoring_prompt_region = source[monitoring_write_start:monitoring_write_label_idx]

    step2_idx = monitoring_prompt_region.index("Step 2 — build and write events")
    step3_idx = monitoring_prompt_region.index("Step 3 — write run record")
    step2_region = monitoring_prompt_region[step2_idx:step3_idx]
    step3_region = monitoring_prompt_region[step3_idx:]

    for field in ('"execution_id"', '"provider"', '"ticket_id"'):
        assert field in step2_region, f"{field} missing from writeMonitoring Step 2 region"
        assert field in step3_region, f"{field} missing from writeMonitoring Step 3 region"

    # run_id must never be overwritten by the new fields within the same instruction.
    assert '"run_id"' in step2_region
    assert '"run_id":"${tid}"' in step3_region

    # provider is always the literal "claude" — never the legacy "claude-code" token anywhere
    # in new code this ticket adds.
    assert '"${PROVIDER}"' in step2_region
    assert '"${PROVIDER}"' in step3_region
    assert "claude-code" not in monitoring_prompt_region


def test_scope_agent_failed_and_resume_pre_tid_paths_stay_identity_less():
    # TCK-20260730-CLAUDE-EXECUTION-IDENTITY AC4: the no-ticket Scope and scope-failure paths
    # never synthesize an execution_id/provider — both run before tid is confirmed real.
    source = _read_workflow_source()

    fail_fallback_start = source.index("if (!ticketInfo || !ticketInfo.ticket_id) {")
    fail_fallback_end = source.index("const tid = ticketInfo.ticket_id")
    fail_fallback_region = source[fail_fallback_start:fail_fallback_end]
    assert "execution_id" not in fail_fallback_region
    assert "'provider'" not in fail_fallback_region
    assert '"provider"' not in fail_fallback_region

    resume_branch_start = source.index("let seqOffset = 0")
    resume_branch_end = source.index("const TICKET_SCHEMA = {")
    resume_branch_region = source[resume_branch_start:resume_branch_end]
    assert "execution_id" not in resume_branch_region
    assert "'provider'" not in resume_branch_region
    assert '"provider"' not in resume_branch_region


def test_record_run_required_fields_unchanged():
    assert RUN_REQUIRED == {"run_id", "start_ts", "workflow", "tier", "final_status", "agent_count"}


# ---------------------------------------------------------------------------
# 11. TCK-20260824-SIDECAR-CROSS-SESSION-SCOPE — writeSidecar() and the Scope-phase resume
#     branch additionally write a per-session-scoped copy, keyed by CLAUDE_CODE_SESSION_ID,
#     alongside the existing unscoped write (never replacing it).
# ---------------------------------------------------------------------------


def test_write_sidecar_also_writes_session_scoped_copy():
    source = _read_workflow_source()
    helper_match = re.search(
        r"const writeSidecar = async \(seq, phase, agent\) => \{.*?\n\}\n",
        source,
        re.DOTALL,
    )
    assert helper_match is not None
    helper_body = helper_match.group(0)

    assert "os.environ.get('CLAUDE_CODE_SESSION_ID', '')" in helper_body
    assert "open('.claude/current_run.' + sid, 'w')" in helper_body
    # The existing unscoped write is preserved, not replaced.
    assert "open('.claude/current_run', 'w')" in helper_body


def test_scope_resume_branch_also_writes_session_scoped_copy():
    source = _read_workflow_source()
    phase_scope_idx = source.index("phase('Scope')")
    scope_start = source.index("const ticketInfo = await agent(")
    pre_scope_region = source[phase_scope_idx:scope_start]

    assert "os.environ.get('CLAUDE_CODE_SESSION_ID', '')" in pre_scope_region
    assert "open('.claude/current_run.' + sid, 'w')" in pre_scope_region
    # The exact pre-existing unscoped-write line (asserted by test_scope_phase_has_sidecar_coverage)
    # is preserved unchanged, not replaced by the additive scoped write.
    assert (
        "open('.claude/current_run', 'w').write(json.dumps({'run_id': sys.argv[1], "
        "'seq': int(sys.argv[2]), 'phase': 'Scope', 'agent': 'ticket-scoper'}))"
    ) in pre_scope_region


# ---------------------------------------------------------------------------
# 12. TCK-20260907-TICKET-CLAIM-DETECTION-LOGGING — the log-only detection call is wired in right
#     after tid is confirmed real, well before writeSidecar's own definition.
# ---------------------------------------------------------------------------


def test_scope_phase_wires_detection_call_at_tid_confirmation_point():
    source = _read_workflow_source()

    tid_idx = source.index("const tid = ticketInfo.ticket_id")
    write_sidecar_def_idx = source.index("const writeSidecar = async")
    detection_call_idx = source.index("ticket_claim_detection.py")

    assert tid_idx < detection_call_idx < write_sidecar_def_idx
    assert (
        'await bash(`python3 tools/agent-monitoring/ticket_claim_detection.py "${tid}" 2>/dev/null || true`)'
        in source
    )


def test_record_run_events_seq_offset_never_read_sidecar():
    # C3 verification, folded into this ticket per its own investigation recommendation: none of
    # these three writers should ever OPEN/READ the sidecar file (they take run_id explicitly via
    # --data). record_events.py's own docstring mentions ".claude/current_run" in prose (explaining
    # *why* tool_call_count is only computed for implement-ticket run_ids) without ever opening it —
    # legitimate documentation, not a dependency, so this guards actual file access, not the bare
    # substring.
    monitoring_dir = _REPO_ROOT / "tools" / "agent-monitoring"
    for filename in ("record_run.py", "record_events.py", "seq_offset.py"):
        source = (monitoring_dir / filename).read_text(encoding="utf-8")
        assert not re.search(r"(?:open|Path)\([^)]*current_run", source), (
            f"{filename} unexpectedly opens/reads the sidecar file"
        )
