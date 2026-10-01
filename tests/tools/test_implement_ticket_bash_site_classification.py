"""TCK-20260930-IMPLEMENT-TICKET-GATE-VS-BOOKKEEPING-CLASSIFICATION: the stored classification of
implement-ticket.js's `bash(` call sites stays in step with the file.

The classification itself is a decision record (stored_artifacts/<ticket>/classification.jsonl); this
test only guards that it covers every real call site and that every row is complete, so a new
`bash(` added to the script without a classification fails here.
"""
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

from workflow_bash_sites import find_bash_call_sites  # noqa: E402

TABLE = REPO / "stored_artifacts" / "TCK-20260930-IMPLEMENT-TICKET-GATE-VS-BOOKKEEPING-CLASSIFICATION" / "classification.jsonl"
SCRIPT = REPO / ".claude" / "workflows" / "implement-ticket.js"
CLASSES = {"gate", "advisory", "bookkeeping", "input", "control"}
ROUTES = {"args", "runcommand", "runcommand-attested", "defer"}


def _rows():
    return [json.loads(line) for line in TABLE.read_text(encoding="utf-8").splitlines() if line.strip()]


def _unported_rows():
    # A row stamped `ported_by` was moved off bash() by a native-port ticket (sh()/shOmit() route).
    return [r for r in _rows() if not r.get("ported_by")]


def test_row_count_matches_real_call_sites_not_grep_matches():
    sites = find_bash_call_sites(SCRIPT)
    assert len(_unported_rows()) == len(sites), (
        f"classification has {len(_unported_rows())} unported rows but {SCRIPT.name} has {len(sites)} bash( call sites; "
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
    need = Counter(r["anchor"] for r in _unported_rows())
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


def test_ported_rows_route_through_sh_helpers_and_legacy_bash_is_kept():
    text = SCRIPT.read_text(encoding="utf-8")
    assert "const legacyBash = typeof bash === 'function' ? bash : null" in text
    assert "if (legacyBash) return legacyBash(cmd)" in text
    assert "const shOmit = async (cmd) => (legacyBash ? legacyBash(cmd) : '')" in text
    ported = [r for r in _rows() if r.get("ported_by")]
    assert len(ported) == 23 and {r["ported_by"] for r in ported} == {"TCK-20260930-NATIVE-PORT-BOOKKEEPING-ADVISORY-SITES"}


def test_sh_helpers_behave_per_runtime_under_node():
    import shutil, subprocess, textwrap
    node = shutil.which("node")
    if node is None:
        import pytest
        pytest.skip("node not found on PATH")
    text = SCRIPT.read_text(encoding="utf-8")
    block = text[text.index("const legacyBash"): text.index("const shOmit")]
    block += text[text.index("const shOmit"): text.index("\n", text.index("const shOmit"))]
    prog = textwrap.dedent("""
        const run = async (hasBash) => {
          const calls = [];
          const agent = async (p) => { calls.push('agent'); return { exit_code: 0, stdout: 'native-out' }; };
          const bash = hasBash ? async (c) => { calls.push('bash'); return 'legacy-out'; } : undefined;
          const f = new Function('agent', 'bash', BLOCK + '; return { sh, shOmit }')(agent, bash);
          return { a: await f.sh('x'), b: await f.shOmit('y'), calls };
        };
        (async () => { process.stdout.write(JSON.stringify({ legacy: await run(true), native: await run(false) })); })();
    """)
    out = subprocess.run([node, "-e", "const BLOCK = " + __import__("json").dumps(block) + ";" + prog],
                         capture_output=True, text=True, timeout=30)
    assert out.returncode == 0, out.stderr
    got = json.loads(out.stdout)
    assert got["legacy"] == {"a": "legacy-out", "b": "legacy-out", "calls": ["bash", "bash"]}
    assert got["native"] == {"a": "native-out", "b": "", "calls": ["agent"]}
