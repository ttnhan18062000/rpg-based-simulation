"""Architecture-guard tests for TCK-20260904-COST-PROXY-EPIC-TICKETS.

Static, raw-source-text-parsing tests against `.claude/workflows/implement-epic.js` and
`.claude/workflows/create-tickets.js`, mirroring `test_current_run_sidecar_orchestrator.py`'s
established pattern (applied here to these 2 newly-touched `.js` files instead of scattering
these assertions into that unrelated file, which targets `implement-ticket.js` only and stays
untouched). Neither workflow file is executed (no JS test runner exists in this repo for
`.claude/workflows/*.js`).

Covers:
- implement-epic.js: a new `writeSidecar(seq, phase, agentName)` helper, closing over a hoisted
  `batchRunId` (declared once, before the Discover `agent()` call), wired at its 4 real top-level
  `agent()` call sites using a disjoint, monotonic NEGATIVE seq range (-1..-4) — never positive,
  since `batchEvents` already occupies seq=1..N under the same run_id (the
  TCK-20260711-MONITORING-TOOLCOUNT-SIDECAR-COLLISION bug class a prior draft of this ticket's
  plan reintroduced and architecture review caught).
- create-tickets.js: the same 4-arg helper, using this file's own `events.length + 1` seq
  numbering, wired at 4 real sites (comprehend, structure, write-sequence, link-epic) and
  EXCLUDED at 3 (writeMonitoring's own agent() call — mirrors implement-ticket.js's own permanent
  exclusion; the 2 `pipeline()` fan-out sites `investigate:${concern.id}`/
  `write:${task.short_scope}` — genuine concurrency race, confirmed by architecture review).
"""
import re
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent.parent
_EPIC_PATH = _REPO_ROOT / ".claude" / "workflows" / "implement-epic.js"
_CREATE_TICKETS_PATH = _REPO_ROOT / ".claude" / "workflows" / "create-tickets.js"


def _read_epic_source() -> str:
    return _EPIC_PATH.read_text(encoding="utf-8")


def _read_create_tickets_source() -> str:
    return _CREATE_TICKETS_PATH.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# 1. create-tickets.js — writeMonitoring's own agent() call has no preceding
#    writeSidecar() call (mirrors implement-ticket.js's own permanent exclusion).
# ---------------------------------------------------------------------------


def test_create_tickets_writeMonitoring_call_has_no_preceding_sidecar_write():
    source = _read_create_tickets_source()

    monitoring_write_start = source.index("const writeMonitoring = async")
    monitoring_write_label = source.index("{ label: 'monitoring-write' }", monitoring_write_start)
    monitoring_write_region = source[monitoring_write_start:monitoring_write_label]
    # Checks for an actual writeSidecar( call, not the documenting comment above the agent() call
    # that explains the exclusion (which necessarily mentions "writeSidecar()" in prose).
    assert "await writeSidecar(" not in monitoring_write_region


# ---------------------------------------------------------------------------
# 2. Adjacency — each covered site's writeSidecar(...) call immediately
#    precedes its paired agent( call.
# ---------------------------------------------------------------------------

_EPIC_COVERED_ADJACENCY = [
    "await writeSidecar(-1, 'Discover', 'discover')\nconst discovery = await agent(",
    "await writeSidecar(-2, 'Implement', 'batch-monitoring-write')\nawait agent(",
    "await writeSidecar(-3, 'Implement', 'folder-cleanup')\n  await agent(",
    "await writeSidecar(-4, 'Report', 'tracking-doc-update')\n  const trackingDocResult = await agent(",
]

_CREATE_TICKETS_COVERED_ADJACENCY = [
    "await writeSidecar(events.length + 1, 'Comprehend', 'comprehend')\nconst comprehension = await agent(",
    "await writeSidecar(events.length + 1, 'Structure', 'structure')\nconst structured = await agent(",
    "await writeSidecar(events.length + 1, 'Write', 'write-sequence')\n  await agent(",
    "await writeSidecar(events.length + 1, 'Link', 'link-epic')\n  const linkResult = await agent(",
]


def test_implement_epic_writeSidecar_precedes_each_of_its_4_covered_agent_calls():
    source = _read_epic_source()
    for adjacency in _EPIC_COVERED_ADJACENCY:
        assert adjacency in source, f"expected adjacency not found: {adjacency!r}"


def test_create_tickets_writeSidecar_precedes_each_of_its_4_covered_agent_calls():
    source = _read_create_tickets_source()
    for adjacency in _CREATE_TICKETS_COVERED_ADJACENCY:
        assert adjacency in source, f"expected adjacency not found: {adjacency!r}"


# ---------------------------------------------------------------------------
# 3. implement-epic.js's collision fix — exact literal seq values -1/-2/-3/-4
#    (in that order), never a positive/colliding value. Plus exactly one
#    batchRunId declaration, hoisted before Discover's agent( call.
# ---------------------------------------------------------------------------


def test_implement_epic_writeSidecar_calls_use_exact_negative_seq_literals_in_order():
    source = _read_epic_source()
    calls = re.findall(r"await writeSidecar\((-?\d+), '([^']+)', '([^']+)'\)", source)
    seqs = [int(c[0]) for c in calls]
    assert seqs == [-1, -2, -3, -4], f"expected exactly [-1, -2, -3, -4] in order, got {seqs}"


def test_implement_epic_has_exactly_one_batchRunId_declaration_hoisted_before_discover():
    source = _read_epic_source()
    assert source.count("const batchRunId = ") == 1

    batch_run_id_idx = source.index("const batchRunId = ")
    discover_ts_idx = source.index("const discoverTs = await captureTs()")
    discover_agent_idx = source.index("const discovery = await agent(")

    assert discover_ts_idx < batch_run_id_idx < discover_agent_idx


# ---------------------------------------------------------------------------
# 4. create-tickets.js — the 2 pipeline() fan-out sites have no writeSidecar()
#    call, with an explicit documenting comment (not silent).
# ---------------------------------------------------------------------------


def test_create_tickets_investigate_pipeline_callback_has_no_sidecar_write():
    source = _read_create_tickets_source()

    pipeline_start = source.index("const investigations = await pipeline(")
    pipeline_end = source.index("const validInvestigations = investigations.filter(Boolean)")
    pipeline_region = source[pipeline_start:pipeline_end]

    assert "writeSidecar(" not in pipeline_region
    # Documenting comment precedes the pipeline() call, not silent.
    preceding_comment = source[max(0, pipeline_start - 700):pipeline_start]
    assert "structural race" in preceding_comment or "concurrent" in preceding_comment


def test_create_tickets_write_pipeline_callback_has_no_sidecar_write():
    source = _read_create_tickets_source()

    pipeline_start = source.index("const written = await pipeline(")
    pipeline_end = source.index("const succeeded = written.filter(Boolean)")
    pipeline_region = source[pipeline_start:pipeline_end]

    assert "writeSidecar(" not in pipeline_region
    preceding_comment = source[max(0, pipeline_start - 300):pipeline_start]
    assert "concurrent" in preceding_comment


# ---------------------------------------------------------------------------
# 5. implement-epic.js's 2 fire-and-forget bash()-only early-return paths still
#    use direct bash() only — no agent( call introduced on either path.
# ---------------------------------------------------------------------------


def test_implement_epic_fire_and_forget_paths_still_use_bash_only_no_agent_call():
    source = _read_epic_source()

    request_mode_start = source.index("if (discovery.mode === 'request') {")
    request_mode_end = source.index("const ticketIds = discovery.ticket_ids")
    request_mode_region = source[request_mode_start:request_mode_end]
    assert "await agent(" not in request_mode_region
    assert "await bash(" in request_mode_region

    nothing_to_do_start = source.index("if (ticketIds.length === 0) {")
    nothing_to_do_end = source.index("log(`Implementing ${ticketIds.length}")
    nothing_to_do_region = source[nothing_to_do_start:nothing_to_do_end]
    assert "await agent(" not in nothing_to_do_region
    assert "await bash(" in nothing_to_do_region


# ---------------------------------------------------------------------------
# 6. Dual-write guard — both new helpers write both the unscoped and the
#    session-scoped sidecar copy (mirrors implement-ticket.js's own
#    test_write_sidecar_also_writes_session_scoped_copy exactly).
# ---------------------------------------------------------------------------


def test_implement_epic_writeSidecar_helper_dual_writes():
    source = _read_epic_source()
    helper_match = re.search(
        r"const writeSidecar = async \(seq, phase, agentName\) => \{.*?\n\}\n",
        source,
        re.DOTALL,
    )
    assert helper_match is not None
    helper_body = helper_match.group(0)

    assert "open('.claude/current_run', 'w')" in helper_body
    assert "os.environ.get('CLAUDE_CODE_SESSION_ID', '')" in helper_body
    assert "open('.claude/current_run.' + sid, 'w')" in helper_body


def test_create_tickets_writeSidecar_helper_dual_writes():
    source = _read_create_tickets_source()
    helper_match = re.search(
        r"const writeSidecar = async \(seq, phase, agentName\) => \{.*?\n\}\n",
        source,
        re.DOTALL,
    )
    assert helper_match is not None
    helper_body = helper_match.group(0)

    assert "open('.claude/current_run', 'w')" in helper_body
    assert "os.environ.get('CLAUDE_CODE_SESSION_ID', '')" in helper_body
    assert "open('.claude/current_run.' + sid, 'w')" in helper_body


# ---------------------------------------------------------------------------
# 7. Neither helper's signature carries execution_id/provider — explicit scope
#    narrowing from implement-ticket.js's own 6-arg helper (out of scope here).
# ---------------------------------------------------------------------------


def test_neither_new_helper_carries_execution_id_or_provider():
    for source in (_read_epic_source(), _read_create_tickets_source()):
        helper_match = re.search(
            r"const writeSidecar = async \(seq, phase, agentName\) => \{.*?\n\}\n",
            source,
            re.DOTALL,
        )
        assert helper_match is not None
        helper_body = helper_match.group(0)
        assert "execution_id" not in helper_body
        assert "provider" not in helper_body
