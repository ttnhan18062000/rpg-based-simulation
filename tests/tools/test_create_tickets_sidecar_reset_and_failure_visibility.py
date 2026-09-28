"""Regression tests for TCK-20260928-CREATE-TICKETS-COST-ATTRIBUTION-MISALIGNED.

Investigation found `create-tickets.js` never reset its `.claude/current_run` sidecar on any exit
path (unlike `implement-ticket.js`, which clears it inside its own `writeMonitoring` agent prompt
as "Step 0"), and that `writeSidecar()` swallowed every write failure unconditionally
(`2>/dev/null || true`), with no signal anywhere that a phase's tool-call attribution had silently
broken. Both combined to explain a real observed anomaly: a 2026-09-23 `create-tickets` run whose
Structure-phase sidecar value (seq 8) kept absorbing tool-call rows for 4 hours after the run
ended, because `write-sequence`/`link-epic`'s own sidecar writes left no trace of success or
failure and nothing downstream ever cleared the stale value.

Also found and fixed in the same pass: `write-sequence`'s own `writeSidecar()` call had no
matching `pushEvent()` anywhere in that code block, so its own tool-call rows were permanently
orphaned (no event at that seq for `compute_tool_stats()` to attribute them to) even when the
write succeeded.

Static, raw-source-text-parsing tests, mirroring `test_epic_create_tickets_sidecar_orchestrator.py`
and this repo's other `.claude/workflows/*.js` test files (no JS test runner exists here) — pins
the orchestrator's own source text and the agent PROMPT's wording, not runtime behavior.
"""
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent.parent
_CREATE_TICKETS_PATH = _REPO_ROOT / ".claude" / "workflows" / "create-tickets.js"


def _read() -> str:
    return _CREATE_TICKETS_PATH.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# AC3: create-tickets.js leaves no live sidecar behind on any exit path.
# ---------------------------------------------------------------------------


def test_write_monitoring_clears_the_sidecar_before_any_other_step():
    text = _read()
    monitoring_start = text.index("const writeMonitoring = async")
    label_idx = text.index("{ label: 'monitoring-write' }", monitoring_start)
    region = text[monitoring_start:label_idx]

    step0_idx = region.find("Step 0 — clear the tool-tracking sidecar FIRST")
    step1_idx = region.find("Step 1 — get current timestamp")
    assert step0_idx != -1, "writeMonitoring must clear the sidecar as its own first step"
    assert step1_idx != -1
    assert step0_idx < step1_idx, "the sidecar clear must run before Step 1/2/3"
    assert "printf '{}' > .claude/current_run" in region, (
        "must clear the sidecar the same way implement-ticket.js's own writeMonitoring does"
    )


def test_every_return_after_the_first_is_preceded_by_write_monitoring():
    # The very first `return` (INVALID_ARGS, no source= arg) fires before any writeSidecar() call
    # ever runs in that execution -- nothing to clear yet, so it is correctly excluded. Every
    # other real exit point in this file is checked explicitly by its own distinguishing anchor
    # text (a generic nearest-preceding-call scan is fragile here -- this file's several
    # multi-hundred-line JSON schema literals between exit points make "textually close" an
    # unreliable proxy for "immediately precedes").
    text = _read()
    exit_point_anchors = [
        "if (comprehension.concerns.length === 0) {",
        "if (activeInvestigations.length === 0) {",
        "if (structured.tasks.length === 0) {",
    ]
    for anchor in exit_point_anchors:
        anchor_idx = text.index(anchor)
        block_end = text.index("\n}", anchor_idx)
        block = text[anchor_idx:block_end]
        assert "await writeMonitoring(" in block, (
            f"exit block starting {anchor!r} has no writeMonitoring() call before its return"
        )
        wm_idx = block.index("await writeMonitoring(")
        ret_idx = block.index("return {")
        assert wm_idx < ret_idx, f"writeMonitoring() must precede return in block {anchor!r}"

    # The final DONE exit, at the very end of the file.
    tail = text[text.index("await writeMonitoring('DONE')"):]
    assert tail.index("await writeMonitoring('DONE')") < tail.index("return {\n  status: 'DONE',")


# ---------------------------------------------------------------------------
# writeSidecar() failures are surfaced, not silently swallowed.
# ---------------------------------------------------------------------------


def test_write_sidecar_no_longer_blanket_swallows_every_failure():
    text = _read()
    sidecar_start = text.index("const writeSidecar = async")
    sidecar_end = text.index("\n}", sidecar_start)
    region = text[sidecar_start:sidecar_end]

    assert "2>/dev/null || true" not in region, (
        "the old blanket swallow (redirect stderr, force exit 0) must be gone -- it made every "
        "writeSidecar failure indistinguishable from success"
    )
    assert "WRITESIDECAR_EXIT" in region, (
        "writeSidecar must capture its own python3 -c exit code via an explicit marker"
    )


def test_write_sidecar_warns_on_failure_via_log():
    text = _read()
    sidecar_start = text.index("const writeSidecar = async")
    sidecar_end = text.index("\n}", sidecar_start)
    region = text[sidecar_start:sidecar_end]

    assert "log(" in region and "WARNING: writeSidecar failed" in region, (
        "a failed writeSidecar() call must warn via this file's own log() helper, not fail "
        "silently -- mirrors this file's other WARNING conventions (e.g. failed write agents)"
    )


def test_write_sidecar_still_never_raises_on_failure():
    # The monitoring fail-open rule: a writeSidecar failure must never throw/fail the workflow.
    # Confirmed structurally: the bash() call's own promise is awaited with no try/catch needed
    # because the shell command itself always exits 0 (the final `echo "WRITESIDECAR_EXIT:$?"` is
    # unconditional, not gated behind `&&`), so `await bash(...)` itself cannot reject on the
    # inner python3 -c command's own failure -- only the appended marker communicates it.
    text = _read()
    sidecar_start = text.index("const writeSidecar = async")
    sidecar_end = text.index("\n}", sidecar_start)
    region = text[sidecar_start:sidecar_end]
    assert 'echo "WRITESIDECAR_EXIT:$?"`' in region, (
        "the exit-code echo must be the unconditional last command in the shell string (no `&&` "
        "gating it), so the shell command itself always exits 0 regardless of the python3 -c "
        "script's own success/failure"
    )


# ---------------------------------------------------------------------------
# write-sequence's own tool-call rows are no longer orphaned.
# ---------------------------------------------------------------------------


def test_write_sequence_now_has_a_matching_push_event():
    text = _read()
    sidecar_idx = text.index("await writeSidecar(events.length + 1, 'Write', 'write-sequence')")
    seq5_end = text.index("// ─── Phase 5: Link", sidecar_idx)
    region = text[sidecar_idx:seq5_end]

    assert "const seqResult = await agent(" in region, (
        "write-sequence's agent() result must be captured for use in a pushEvent() call"
    )
    assert "pushEvent('Write', 'write-sequence'," in region, (
        "write-sequence must push a matching event, or its own tool-call rows have no event at "
        "that seq for compute_tool_stats() to attribute them to"
    )


def test_write_sequence_push_event_is_after_its_writesidecar_and_agent_call():
    text = _read()
    sidecar_idx = text.index("await writeSidecar(events.length + 1, 'Write', 'write-sequence')")
    agent_idx = text.index("const seqResult = await agent(", sidecar_idx)
    push_idx = text.index("pushEvent('Write', 'write-sequence',", sidecar_idx)
    assert sidecar_idx < agent_idx < push_idx, (
        "order must be: writeSidecar (claims the seq) -> agent() dispatch (real tool calls happen "
        "under that seq) -> pushEvent (records the resulting event at the same seq)"
    )
