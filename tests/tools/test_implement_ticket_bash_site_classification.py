"""TCK-20260930-IMPLEMENT-TICKET-GATE-VS-BOOKKEEPING-CLASSIFICATION: the stored classification of
implement-ticket.js's `bash(` call sites stays in step with the file.

The classification itself is a decision record (stored_artifacts/<ticket>/classification.json); this
test only guards that it covers every real call site and that every row is complete, so a new
`bash(` added to the script without a classification fails here.
"""
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

from workflow_bash_sites import find_bash_call_sites  # noqa: E402

TABLE = REPO / "stored_artifacts" / "TCK-20260930-IMPLEMENT-TICKET-GATE-VS-BOOKKEEPING-CLASSIFICATION" / "classification.json"
SCRIPT = REPO / ".claude" / "workflows" / "implement-ticket.js"
CLASSES = {"gate", "advisory", "bookkeeping", "input", "control"}
ROUTES = {"args", "runcommand", "runcommand-attested", "defer"}


def _rows():
    return json.loads(TABLE.read_text(encoding="utf-8"))


def test_row_count_matches_real_call_sites_not_grep_matches():
    sites = find_bash_call_sites(SCRIPT)
    assert len(_rows()) == len(sites), (
        f"classification has {len(_rows())} rows but {SCRIPT.name} has {len(sites)} bash( call sites; "
        "classify the new/removed site (and update the table)"
    )


def test_comment_mentions_are_not_counted():
    total_mentions = SCRIPT.read_text(encoding="utf-8").count("bash(")
    assert total_mentions > len(find_bash_call_sites(SCRIPT))  # grep over-counts; that is why this tool exists


def test_every_row_has_class_route_and_risk():
    for r in _rows():
        assert r["class"] in CLASSES, r
        assert r["route"] in ROUTES, r
        assert r["misreport_risk"].strip(), r
        assert r["purpose"].strip() and r["feeds"] is not None, r


def test_every_gate_or_attested_row_states_a_real_misreport_risk():
    for r in _rows():
        if r["class"] == "gate" or r["route"] == "runcommand-attested":
            assert len(r["misreport_risk"]) > 40 and not r["misreport_risk"].startswith("none"), r


def test_every_anchor_occurs_in_the_script_enough_times():
    text = SCRIPT.read_text(encoding="utf-8")
    from collections import Counter
    need = Counter(r["anchor"] for r in _rows())
    for anchor, n in need.items():
        assert text.count(anchor) >= n, f"anchor {anchor!r} expected >= {n} time(s) in {SCRIPT.name}"


def test_gate_class_rows_are_never_routed_to_args_or_plain_runcommand():
    for r in _rows():
        if r["class"] == "gate":
            assert r["route"] == "runcommand-attested", r


def test_site_finder_ignores_comments_and_block_comments(tmp_path):
    js = tmp_path / "x.js"
    js.write_text("// bash( in a comment\nconst a = await bash('x') // trailing\n/* bash(\n bash( */\nawait bash(`y`)\n", encoding="utf-8")
    assert [n for n, _ in find_bash_call_sites(js)] == [2, 5]
