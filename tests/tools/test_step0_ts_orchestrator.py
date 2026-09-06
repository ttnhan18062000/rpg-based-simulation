"""Regression tests for TCK-20260710-STEP0-TS-ORCHESTRATOR-BASH.

Static, raw-source-text-parsing tests against `.claude/workflows/implement-ticket.js`,
`.claude/workflows/implement-epic.js`, `.claude/workflows/create-tickets.js`, and
`docs/agent-monitoring/schema.md` — reuses tests/tools/test_tag_skill_mapping_check.py's and
tests/tools/test_current_run_sidecar_orchestrator.py's established pattern of `Path.read_text()`
against these non-Python source files. The workflow files are never executed (no JS test runner
exists in this repo for `.claude/workflows/*.js`).

Covers: the former per-prompt "Step 0: run `date -u ...`" agent-prompt-text instruction (13
JSON-schema `ts` sites across all 3 files, plus the free-text `PHASE_TS:` prefix convention at
Investigate/Plan) has been replaced by an orchestrator-side `captureTs()` helper (mirroring C1's
`writeSidecar(seq)` shape), invoked immediately before each corresponding `await agent(...)` call
(or immediately before the paired `writeSidecar(...)` call, where one exists, per the ordering
constraint in plan.md's Anti-Drift Notes). This file is scoped purely to this ticket's ts-capture
mechanism — the sidecar-write mechanism itself
(`tests/tools/test_current_run_sidecar_orchestrator.py`) is out of scope here.

Two documented exceptions: implement-epic.js's Discover site and create-tickets.js's Comprehend
site no longer have their literal captureTs()->agent() adjacency checked in this file, since
TCK-20260904-COST-PROXY-EPIC-TICKETS inserted a writeSidecar() call between the two at both sites;
the superseding writeSidecar()->agent() adjacency for both is asserted instead by
tests/tools/test_epic_create_tickets_sidecar_orchestrator.py.
"""
import re
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent.parent
_IMPLEMENT_TICKET_PATH = _REPO_ROOT / ".claude" / "workflows" / "implement-ticket.js"
_IMPLEMENT_EPIC_PATH = _REPO_ROOT / ".claude" / "workflows" / "implement-epic.js"
_CREATE_TICKETS_PATH = _REPO_ROOT / ".claude" / "workflows" / "create-tickets.js"
_SCHEMA_DOC_PATH = _REPO_ROOT / "docs" / "agent-monitoring" / "schema.md"

# The 10 implement-ticket.js call sites where `captureTs()` composes alongside `writeSidecar()`
# (9) or stands alone (Scope, which has no writeSidecar). Order matches the file's phase order.
# Since TCK-20260728-MONITORING-PAUSE-RESUME-SEQ-COLLISION, each `events.length + 1` expression
# carries a `+ seqOffset` term so a resumed session's seq numbering continues past a prior
# session's instead of restarting at 1.
_IMPLEMENT_TICKET_ADJACENCY = [
    "const scopeTs = await captureTs()\nconst ticketInfo = await agent(",
    "const investigationTs = await captureTs()\n  await writeSidecar(events.length + 1 + seqOffset, 'Investigate', 'investigator')\n  investigation = await agent(",
    "const planTs = await captureTs()\n  await writeSidecar(events.length + 1 + seqOffset, 'Plan', 'planner')\n  plan = await agent(",
    "const reviewTs = await captureTs()\n  await writeSidecar(events.length + 1 + seqOffset, 'Review', 'architecture-reviewer')\n  review = await agent(",
    "const implementTs = await captureTs()\nawait writeSidecar(events.length + 1 + seqOffset, 'Implement', 'implementer')\nconst implementation = await agent(",
    "const archVerifyTs = await captureTs()\n  await writeSidecar(events.length + 1 + seqOffset, 'Architecture-Verify', 'architecture-reviewer')\n  const archVerify = await agent(",
    "const testTs = await captureTs()\nawait writeSidecar(events.length + 1 + seqOffset, 'Test', 'test-scoper')\nconst testResult = await agent(",
    "const parityTs = await captureTs()\n  await writeSidecar(events.length + 1 + seqOffset, 'Parity', 'parity-updater')\n  const parity = await agent(",
    "const securityReviewTs = await captureTs()\n  await writeSidecar(events.length + 1 + seqOffset, 'Security-Review', 'security-reviewer')\n  const securityReview = await agent(",
    "const doneCheckTs = await captureTs()\nawait writeSidecar(events.length + 1 + seqOffset, 'Verify', 'done-checker')\nconst doneCheck = await agent(",
]

# _IMPLEMENT_EPIC_ADJACENCY (literal "const discoverTs = await captureTs()\nconst discovery =
# await agent(") and _CREATE_TICKETS_ADJACENCY (literal "const comprehendTs = await
# captureTs()\nconst comprehension = await agent(") were retired by
# TCK-20260904-COST-PROXY-EPIC-TICKETS: that ticket's Step 1 inserted a hoisted `batchRunId`
# computation + implement-epic.js's first `writeSidecar()` call between `discoverTs`'s capture
# and the Discover `agent()` call (batchRunId's request-mode branch genuinely depends on
# discoverTs's value, so nothing can execute between them for free); Step 3 inserted
# create-tickets.js's first `writeSidecar()` call directly between `comprehendTs`'s capture and
# the Comprehend `agent()` call. The superseding invariant for both sites —
# `writeSidecar()` immediately precedes `agent()` — is asserted instead by
# tests/tools/test_epic_create_tickets_sidecar_orchestrator.py
# (`_EPIC_COVERED_ADJACENCY[0]` / `_CREATE_TICKETS_COVERED_ADJACENCY[0]`). The "captured value
# actually reaches downstream code" property this file still protects for both files is
# unchanged — see the `batchStartTs = discoverTs || null` / `startTs = comprehendTs || null`
# assertions below.


def _read_implement_ticket() -> str:
    return _IMPLEMENT_TICKET_PATH.read_text(encoding="utf-8")


def _read_implement_epic() -> str:
    return _IMPLEMENT_EPIC_PATH.read_text(encoding="utf-8")


def _read_create_tickets() -> str:
    return _CREATE_TICKETS_PATH.read_text(encoding="utf-8")


def _read_schema_doc() -> str:
    return _SCHEMA_DOC_PATH.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# 1. No leftover "Step 0: run `date -u ...`" prompt text at any covered site
# ---------------------------------------------------------------------------


def test_step_0_ts_capture_lines_gone_from_all_covered_sites():
    it_source = _read_implement_ticket()
    ie_source = _read_implement_epic()
    ct_source = _read_create_tickets()

    # implement-ticket.js: all 11 sites (Scope x2, Investigate, Plan, + 7 schema-ts sites) shared
    # this exact colon-phrased prefix.
    assert "Step 0: run \\`date -u +%Y-%m-%dT%H:%M:%SZ\\`" not in it_source

    # implement-epic.js: all 3 Discover branches used the em-dash-phrased variant.
    assert "Step 0 — run \\`date -u +%Y-%m-%dT%H:%M:%SZ\\`" not in ie_source

    # create-tickets.js: the Comprehend-phase site, distinct phrasing from the deferred
    # Write-phase per-task site (line ~659, "2. Run: date -u ... — save as TS.") which must
    # remain untouched (Decision 3 — explicitly out of this ticket's scope).
    assert 'Step 0: run \\`date -u +%Y-%m-%dT%H:%M:%SZ\\` and return it as "ts"' not in ct_source
    assert "2. Run: date -u +%Y-%m-%dT%H:%M:%SZ — save as TS." in ct_source

    # Must NOT disturb writeMonitoring's/batch-monitoring-write's END_TS captures — covered
    # separately and explicitly by test 5 below; they remain present in both files.
    assert "Run via Bash: date -u +%Y-%m-%dT%H:%M:%SZ" in it_source
    assert "Run via Bash: date -u +%Y-%m-%dT%H:%M:%SZ" in ie_source

    # docs/agent-monitoring/schema.md's events.jsonl `ts` field row states orchestrator
    # provenance (AC #4 / plan.md Step 9) — folded into this test per Step 9's own Verify note.
    schema_doc = _read_schema_doc()
    ts_field_row_match = re.search(r"\| `ts` \| ISO 8601 \| No \|([^\n]*)\|", schema_doc)
    assert ts_field_row_match is not None
    assert "orchestrator" in ts_field_row_match.group(1)
    assert "not self-reported by the agent" in ts_field_row_match.group(1)


# ---------------------------------------------------------------------------
# 2. captureTs() precedes each covered agent() call (or its paired writeSidecar
#    call, where one exists), with the captured value wired into pushEvent /
#    start_ts downstream.
# ---------------------------------------------------------------------------


def test_ts_capture_bash_precedes_each_covered_agent_call():
    it_source = _read_implement_ticket()
    for adjacency in _IMPLEMENT_TICKET_ADJACENCY:
        assert adjacency in it_source, f"expected adjacency not found: {adjacency!r}"

    ie_source = _read_implement_epic()
    # implement-epic.js's Discover-site captureTs()->agent() adjacency is no longer checked
    # here — see the retirement comment above _IMPLEMENT_EPIC_ADJACENCY's old location.

    ct_source = _read_create_tickets()
    # create-tickets.js's Comprehend-site captureTs()->agent() adjacency is no longer checked
    # here — see the same retirement comment (covers both constants).

    # Captured values are wired downstream, not discarded.
    assert "const startTs = scopeTs || null" in it_source
    assert "const batchStartTs = discoverTs || null" in ie_source
    assert "startTs = comprehendTs || null" in ct_source


# ---------------------------------------------------------------------------
# 3. PHASE_TS: free-text prefix convention fully removed (prompt text and the
#    orchestrator-side regex parse/strip logic)
# ---------------------------------------------------------------------------


def test_phase_ts_prefix_convention_removed_from_investigate_and_plan():
    it_source = _read_implement_ticket()
    assert "PHASE_TS" not in it_source
    assert r"/^PHASE_TS: (\S+)/m" not in it_source
    assert r"/^PHASE_TS: \S+\n?/" not in it_source


# ---------------------------------------------------------------------------
# 4. TICKET_SCHEMA / DISCOVER_SCHEMA no longer force `ts` as required
# ---------------------------------------------------------------------------


def test_ts_schema_required_field_dropped_at_scope_and_discover():
    it_source = _read_implement_ticket()
    ticket_schema_match = re.search(
        r"const TICKET_SCHEMA = \{.*?required: \[(.*?)\],", it_source, re.DOTALL
    )
    assert ticket_schema_match is not None
    ticket_required = ticket_schema_match.group(1)
    assert "'ts'" not in ticket_required
    for field in ("ticket_id", "ticket_path", "status", "conflicts", "tier", "tags", "summary"):
        assert f"'{field}'" in ticket_required

    ie_source = _read_implement_epic()
    discover_schema_match = re.search(
        r"const DISCOVER_SCHEMA = \{.*?required: \[(.*?)\],", ie_source, re.DOTALL
    )
    assert discover_schema_match is not None
    discover_required = discover_schema_match.group(1)
    assert "'ts'" not in discover_required
    for field in ("mode", "ticket_ids", "already_done", "summary"):
        assert f"'{field}'" in discover_required


# ---------------------------------------------------------------------------
# 5. Anti-drift guard: END_TS / batch END_TS captures untouched, byte-identical
# ---------------------------------------------------------------------------


def test_end_ts_and_batch_end_ts_captures_untouched():
    it_source = _read_implement_ticket()
    ie_source = _read_implement_epic()

    it_end_ts_text = (
        "Step 1 — get current timestamp (run end time):\n"
        "  Run via Bash: date -u +%Y-%m-%dT%H:%M:%SZ\n"
        "  Save result as END_TS."
    )
    assert it_end_ts_text in it_source

    ie_end_ts_text = (
        "Step 1 — get current timestamp (batch end time):\n"
        "  Run via Bash: date -u +%Y-%m-%dT%H:%M:%SZ\n"
        "  Save as END_TS."
    )
    assert ie_end_ts_text in ie_source


# ---------------------------------------------------------------------------
# 6. captureTs() helper defined once, after writeSidecar, before
#    classifyChecklistFailure (implement-ticket.js's shared module scope)
# ---------------------------------------------------------------------------


def test_captureTs_helper_defined_once_after_writeSidecar():
    it_source = _read_implement_ticket()
    assert it_source.count("const captureTs = async ()") == 1

    write_sidecar_idx = it_source.index("const writeSidecar = async (seq, phase, agent)")
    capture_ts_idx = it_source.index("const captureTs = async ()")
    classify_idx = it_source.index("const classifyChecklistFailure")
    assert write_sidecar_idx < capture_ts_idx < classify_idx

    # implement-epic.js and create-tickets.js each define their own local equivalent (no shared
    # module scope with implement-ticket.js).
    ie_source = _read_implement_epic()
    ct_source = _read_create_tickets()
    assert ie_source.count("const captureTs = async ()") == 1
    assert ct_source.count("const captureTs = async ()") == 1
