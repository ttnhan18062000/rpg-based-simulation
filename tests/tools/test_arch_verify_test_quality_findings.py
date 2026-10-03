"""Tests for TCK-20261002-ARCH-VERIFY-TEST-QUALITY-FINDINGS.

Covers the four parts of the change without running the real `implement-ticket` Workflow:
the ARCH_VERIFY_SCHEMA key, the event carry-through (`pushEvent`/`cleanFindings` executed in node
against the real source text, `record_events.validate_record`, the hand-orchestrated closure
tool), the schema-derived output-format helper, and the SKILL.md rule in both copies.
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).parent.parent.parent
_MONITORING_TOOLS_DIR = _REPO_ROOT / "tools" / "agent-monitoring"
if str(_MONITORING_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_MONITORING_TOOLS_DIR))

import schema_format_tail as sft  # noqa: E402
from record_events import validate_record as validate_event  # noqa: E402
from record_hand_orchestrated_closure import build_records  # noqa: E402

_WORKFLOW = _REPO_ROOT / ".claude" / "workflows" / "implement-ticket.js"
_NODE = shutil.which("node")
_SKILLS = [
    _REPO_ROOT / ".claude" / "skills" / "implement-ticket" / "SKILL.md",
    _REPO_ROOT / ".agents" / "skills" / "implement-ticket" / "SKILL.md",
]


def _real_keys() -> list:
    return sft.extract_schema_keys(_WORKFLOW.read_text(encoding="utf-8"), "ARCH_VERIFY_SCHEMA")


# ---- AC1: the schema key ---------------------------------------------------------------------

def test_arch_verify_schema_has_optional_test_quality_findings_after_the_existing_keys():
    assert _real_keys() == ["verdict", "violations", "summary", "ts", "verified_by", "test_quality_findings"]


def test_test_quality_findings_is_not_a_required_key():
    text = _WORKFLOW.read_text(encoding="utf-8")
    start = text.index("const ARCH_VERIFY_SCHEMA = {")
    block = text[start:text.index("properties:", start)]
    assert "required: ['verdict', 'violations', 'summary']" in block
    assert "test_quality_findings" not in block


def test_the_architecture_verify_prompt_wording_is_untouched():
    """Out of scope by test-architecture's evidence rule: the 'Return:' list still names exactly the
    four original fields and the phrase 'a narrow verification' is still there."""
    text = _WORKFLOW.read_text(encoding="utf-8")
    assert "This is a narrow verification, not a full re-review." in text
    assert "verified_by (list which findings came from the static script vs. independent judgment" in text
    assert "Return: APPROVED (no confirmed real violations)" in text
    prompt = text[text.index("Post-implementation architecture verification for ticket"):text.index("label: 'architecture-verify'")]
    assert "test_quality_findings" not in prompt


# ---- AC2: pushEvent / cleanFindings, executed for real in node --------------------------------

def _run_push_event(calls: list) -> list:
    """Extracts cleanFindings + pushEvent verbatim from the real workflow and runs them in node."""
    text = _WORKFLOW.read_text(encoding="utf-8")
    start = text.index("const cleanFindings = ")
    end = text.index("\n}\n", text.index("const pushEvent = ", start)) + 3
    program = (
        "const events = []; const seqOffset = 0;\n"
        "const truncateSummary = (s) => { const str = (s || '').toString(); return str.length > 200 ? str.slice(0, 196) + ' […]' : str }\n"
        + text[start:end]
        + f"\nfor (const c of {json.dumps(calls)}) pushEvent(...c)\nconsole.log(JSON.stringify(events))\n"
    )
    out = subprocess.run([_NODE, "-e", program], capture_output=True, text=True, timeout=30)
    assert out.returncode == 0, out.stderr
    return json.loads(out.stdout)


def _av(findings):
    return ["Architecture-Verify", "architecture-reviewer", "ok", "APPROVED", "2026-10-02T00:00:00Z", None, None, findings]


@pytest.mark.skipif(_NODE is None, reason="node not installed")
def test_push_event_carries_string_findings_verbatim_and_distinguishes_empty_from_absent():
    events = _run_push_event([
        _av(["tests/a.py: asserts nothing about X", "tests/b.py: mock hides Y"]),
        _av([]),
        _av(None),
        ["Scope", "ticket-scoper", "ok", "scoped", "2026-10-02T00:00:03Z"],
    ])
    assert events[0]["test_quality_findings"] == ["tests/a.py: asserts nothing about X", "tests/b.py: mock hides Y"]
    assert "test_quality_findings_normalized" not in events[0]  # verbatim: no marker
    assert events[1]["test_quality_findings"] == [] and "test_quality_findings_normalized" not in events[1]
    assert "test_quality_findings" not in events[2] and "test_quality_findings" not in events[3]
    assert [e["seq"] for e in events] == [1, 2, 3, 4]
    assert all(len(e["summary"]) <= 200 for e in events)


@pytest.mark.skipif(_NODE is None, reason="node not installed")
def test_push_event_keeps_object_items_as_json_strings_and_says_so():
    """The reviewer's own definition says only 'a list'; a shadow reviewer returned objects. They must
    survive (as their JSON text) with the transformation recorded, never be dropped or rejected."""
    obj = {"severity": "high", "file": "tests/x.py", "finding": "asserts on a mock"}
    event = _run_push_event([_av(["plain finding", obj])])[0]
    assert event["test_quality_findings"][0] == "plain finding"
    assert json.loads(event["test_quality_findings"][1]) == obj
    assert event["test_quality_findings_normalized"] == 1
    assert validate_event(_event(**{k: event[k] for k in ("test_quality_findings", "test_quality_findings_normalized")})) == []


@pytest.mark.skipif(_NODE is None, reason="node not installed")
def test_push_event_wraps_a_non_array_reply_and_drops_only_empty_items():
    wrapped = _run_push_event([_av("one lone string"), _av({"finding": "lone object"})])
    assert wrapped[0]["test_quality_findings"] == ["one lone string"] and wrapped[0]["test_quality_findings_normalized"] == 1
    assert json.loads(wrapped[1]["test_quality_findings"][0]) == {"finding": "lone object"}
    assert wrapped[1]["test_quality_findings_normalized"] == 2  # wrapped + serialized
    dropped = _run_push_event([_av(["keep", "", None])])[0]
    assert dropped["test_quality_findings"] == ["keep"] and dropped["test_quality_findings_normalized"] == 2
    all_empty = _run_push_event([_av(["", None])])[0]
    assert all_empty["test_quality_findings"] == [] and all_empty["test_quality_findings_normalized"] == 2


@pytest.mark.skipif(_NODE is None, reason="node not installed")
def test_push_event_swaps_single_quotes_and_counts_it():
    event = _run_push_event([_av(["it's a finding", "ok"])])[0]
    assert event["test_quality_findings"] == ["it\u2019s a finding", "ok"]
    assert event["test_quality_findings_normalized"] == 1
    assert all("'" not in x for x in event["test_quality_findings"])


def test_both_architecture_verify_outcomes_pass_the_findings_to_push_event():
    text = _WORKFLOW.read_text(encoding="utf-8")
    pushes = [ln for ln in text.splitlines() if "pushEvent('Architecture-Verify', 'architecture-reviewer', '" in ln and "archVerify" in ln]
    assert len(pushes) == 2
    assert all(ln.rstrip().endswith("archVerify.test_quality_findings)") for ln in pushes), pushes


# ---- AC3: validator and closure tool ---------------------------------------------------------

def _event(**extra):
    return {"run_id": "R", "seq": 1, "ts": "2026-10-02T00:00:00Z", "phase": "Architecture-Verify",
            "agent": "architecture-reviewer", "summary": "s", "status": "ok", **extra}


def test_record_events_accepts_absent_empty_and_string_lists():
    assert validate_event(_event()) == []
    assert validate_event(_event(test_quality_findings=[])) == []
    assert validate_event(_event(test_quality_findings=["a", "b"])) == []


@pytest.mark.parametrize("bad", ["a string", ["ok", 3], {"k": "v"}, 5])
def test_record_events_rejects_other_shapes(bad):
    errs = validate_event(_event(test_quality_findings=bad))
    assert errs and "test_quality_findings must be a list of strings" in errs[0]


def _closure_events(events):
    _, recs = build_records("TCK-X", "standard", "DONE", events, None, None, "implement-ticket", "claude", "claude")
    return recs


def test_record_events_validates_the_normalized_count():
    assert validate_event(_event(test_quality_findings=["a"], test_quality_findings_normalized=2)) == []
    for bad in (-1, "2", 1.5, True):
        errs = validate_event(_event(test_quality_findings=["a"], test_quality_findings_normalized=bad))
        assert errs and "test_quality_findings_normalized must be a non-negative integer" in errs[0], bad


def test_closure_tool_carries_findings_per_event_and_adds_no_key_otherwise():
    recs = _closure_events([
        {"phase": "Architecture-Verify", "status": "ok", "summary": "s", "test_quality_findings": ["x", "y"]},
        {"phase": "Test", "status": "ok", "summary": "s"},
        {"phase": "Verify", "status": "ok", "summary": "s", "test_quality_findings": []},
    ])
    assert recs[0]["test_quality_findings"] == ["x", "y"]
    assert "test_quality_findings" not in recs[1]
    assert recs[2]["test_quality_findings"] == []
    carried = _closure_events([{"phase": "Architecture-Verify", "status": "ok", "summary": "s",
                                "test_quality_findings": ["{}"], "test_quality_findings_normalized": 1}])[0]
    assert carried["test_quality_findings_normalized"] == 1 and validate_event(carried) == []
    assert "test_quality_findings_normalized" not in recs[0]
    assert all(validate_event(r) == [] for r in recs)


# ---- AC4: the helper ---------------------------------------------------------------------------

_FIXTURE = """
const OTHER = { type: 'object', properties: { nope: {} } }
const SCHEMA_X = {
  type: 'object',
  required: ['a'],
  properties: {
    a: { type: 'string', description: 'has } and { and a "quote" and a, comma' },
    b: { type: 'array', items: { type: 'object', properties: { inner: { type: 'string' } } } },
    // c: commented out
    "d": { type: 'string' },
    e: { type: 'number', description: `tpl ${'{'} brace` },
  },
}
"""


def test_helper_returns_top_level_keys_in_order_ignoring_nesting_strings_and_comments():
    assert sft.extract_schema_keys(_FIXTURE, "SCHEMA_X") == ["a", "b", "d", "e"]


def test_helper_sentence_lists_every_key_in_schema_order():
    assert sft.format_tail(["verdict", "x"]) == "Return your answer as a single JSON object with keys: verdict, x."


def test_helper_pins_the_real_arch_verify_schema():
    tail = sft.format_tail(_real_keys())
    assert tail == ("Return your answer as a single JSON object with keys: "
                    "verdict, violations, summary, ts, verified_by, test_quality_findings.")


def test_helper_cli_prints_the_sentence_and_fails_loudly_on_an_unknown_schema():
    ok = subprocess.run([sys.executable, str(_MONITORING_TOOLS_DIR / "schema_format_tail.py"), "--schema", "ARCH_VERIFY_SCHEMA"],
                        capture_output=True, text=True)
    assert ok.returncode == 0 and ok.stdout.strip() == sft.format_tail(_real_keys())
    bad = subprocess.run([sys.executable, str(_MONITORING_TOOLS_DIR / "schema_format_tail.py"), "--schema", "NO_SUCH_SCHEMA"],
                         capture_output=True, text=True)
    assert bad.returncode == 1 and bad.stdout == "" and "cannot derive" in bad.stderr


# ---- AC5: docs ---------------------------------------------------------------------------------

@pytest.mark.parametrize("path", _SKILLS, ids=lambda p: str(p.relative_to(_REPO_ROOT)))
def test_both_skill_copies_state_the_generated_format_tail_rule(path):
    text = path.read_text(encoding="utf-8")
    assert "schema_format_tail.py" in text
    assert "never hand-written" in text
    assert "TCK-20260804-SKILL-JS-PHASE-SYNC" in text


def test_schema_md_documents_the_optional_event_field():
    text = (_REPO_ROOT / "docs" / "agent-monitoring" / "schema.md").read_text(encoding="utf-8")
    assert "`test_quality_findings`" in text and "`test_quality_findings_normalized`" in text
    assert "No item is dropped" in text
