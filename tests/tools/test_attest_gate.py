"""Attested gate results (TCK-20260930-NATIVE-PORT-ATTESTED-GATE-SITES).

``tools/gate_checks/attest_gate.py`` runs a gate command and prints one ``ATTEST:`` line; ``verifyAttestation`` and
``shAttested`` in ``.claude/workflows/implement-ticket.js`` verify it. The JS block between the ``ATTEST-VERIFIER``
markers is the code under test: it is extracted from the real script and run under node, with lines produced by the real
Python wrapper, so the two halves cannot drift apart unnoticed.

The mechanism is anti-misreport, not tamper-proof (see the wrapper's docstring); ``test_forgery_with_the_known_nonce_
passes`` pins that stated limit instead of hiding it.
"""

from __future__ import annotations

import base64
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "tools"))

from gate_checks.attest_gate import attest, compute_mac, main  # noqa: E402

SCRIPT = REPO_ROOT / ".claude" / "workflows" / "implement-ticket.js"
_NODE = shutil.which("node")
needs_node = pytest.mark.skipif(_NODE is None, reason="node not installed")

NONCE = "run-nonce-1"
GATE = "demo_gate"


def _verifier_block() -> str:
    text = SCRIPT.read_text(encoding="utf-8")
    start = text.index("// ATTEST-VERIFIER-BEGIN")
    end = text.index("// ATTEST-VERIFIER-END")
    return text[start:end]


def _node_verify(cases: list[dict]) -> list[dict]:
    program = (
        _verifier_block()
        + "\nconst cases = JSON.parse(process.argv[1]);"
        + "\nprocess.stdout.write(JSON.stringify(cases.map((c) => verifyAttestation(c.output, c.expect))));"
    )
    proc = subprocess.run([_NODE, "-e", program, json.dumps(cases)], capture_output=True, text=True, timeout=30)
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def _line_and_out(cmd: str, nonce: str = NONCE, gate: str = GATE) -> tuple[str, str]:
    return attest(nonce, gate, cmd)


def _case(output: str, cmd: str, nonce: str = NONCE, gate: str = GATE) -> dict:
    return {"output": output, "expect": {"nonce": nonce, "gate": gate, "expectedCmd": cmd}}


def test_wrapper_runs_the_command_and_prints_attest_line_then_stdout(capsys):
    cmd = "echo hello; exit 0"
    assert main(["--nonce", NONCE, "--gate-id", GATE, "--cmd-b64", base64.b64encode(cmd.encode()).decode()]) == 0
    first, rest = capsys.readouterr().out.split("\n", 1)
    record = json.loads(first.removeprefix("ATTEST:"))
    assert rest == "hello\n"
    assert record["exit_code"] == 0 and record["cmd"] == cmd and record["gate"] == GATE
    assert record["stdout_sha"] == hashlib.sha256(b"hello\n").hexdigest()
    assert record["mac"] == compute_mac(NONCE, GATE, cmd, 0, record["stdout_sha"])


def test_wrapper_reports_the_real_exit_code_and_still_exits_zero_itself():
    line, _ = _line_and_out("exit 3")
    assert json.loads(line.removeprefix("ATTEST:"))["exit_code"] == 3


def test_wrapper_handles_multiline_commands_with_nested_quotes():
    cmd = "python3 -c \"\nprint('a \\\"b\\\" c')\n\" 'x y'"
    line, out = _line_and_out(cmd)
    assert json.loads(line.removeprefix("ATTEST:"))["cmd"] == cmd
    assert out == 'a "b" c\n'


@needs_node
def test_node_sha256_and_base64_match_python_including_multibyte():
    program = (
        _verifier_block()
        + "\nconst t = JSON.parse(process.argv[1]);"
        + "\nprocess.stdout.write(JSON.stringify(t.map((x) => [sha256Hex(x), base64Utf8(x)])));"
    )
    texts = ["", "abc", "é — 漢字 😀", "x" * 1000, "a|b|c"]
    proc = subprocess.run([_NODE, "-e", program, json.dumps(texts)], capture_output=True, text=True, timeout=30)
    assert proc.returncode == 0, proc.stderr
    for text, (sha, b64) in zip(texts, json.loads(proc.stdout)):
        assert sha == hashlib.sha256(text.encode()).hexdigest(), text
        assert b64 == base64.b64encode(text.encode()).decode(), text


@needs_node
def test_checker_verdicts_for_honest_pass_honest_fail_and_each_tamper():
    ok_cmd, bad_cmd = "echo ok", "echo no; exit 1"
    ok_line, ok_out = _line_and_out(ok_cmd)
    bad_line, bad_out = _line_and_out(bad_cmd)
    record = json.loads(ok_line.removeprefix("ATTEST:"))
    tampered = dict(record, exit_code=1)  # mac not recomputed
    cases = [
        _case(ok_line + "\n" + ok_out, ok_cmd),  # 0 honest pass
        _case(bad_line + "\n" + bad_out, bad_cmd),  # 1 honest fail
        _case(ok_line + "\n" + ok_out, "echo something else"),  # 2 wrong command
        _case(ok_line + "\n" + ok_out, ok_cmd, gate="other_gate"),  # 3 wrong gate
        _case("ATTEST:" + json.dumps(tampered), ok_cmd),  # 4 tampered exit_code
        _case(ok_line + "\n" + ok_out, ok_cmd, nonce="a-different-nonce"),  # 5 wrong nonce
        _case("all gates passed, trust me", ok_cmd),  # 6 no line
        _case("ATTEST:{not json}", ok_cmd),  # 7 unparseable
    ]
    got = _node_verify(cases)
    assert [(g["ok"], g["reason"]) for g in got] == [
        (True, "pass"),
        (False, "command exited 1"),
        (False, "wrong command"),
        (False, "wrong gate"),
        (False, "bad mac"),
        (False, "bad mac"),
        (False, "no ATTEST line"),
        (False, "unparseable"),
    ]


@needs_node
def test_forgery_with_the_known_nonce_passes():
    """The stated limit: an agent handed the nonce can compute a valid mac for exit 0 without running the command."""
    cmd = "false"
    stdout_sha = hashlib.sha256(b"").hexdigest()
    forged = {"gate": GATE, "cmd": cmd, "exit_code": 0, "stdout_sha": stdout_sha, "mac": compute_mac(NONCE, GATE, cmd, 0, stdout_sha)}
    (got,) = _node_verify([_case("ATTEST:" + json.dumps(forged), cmd)])
    assert got["ok"] is True, "if this starts failing the docs saying 'not tamper-proof' need revisiting"


_E2E = """
const fs = require('fs');
const { execFileSync } = require('child_process');
const scenario = JSON.parse(process.argv[1]);
const block = fs.readFileSync(process.argv[2], 'utf8');
const start = block.indexOf('const legacyBash');
const end = block.indexOf('\\n}\\n', block.indexOf('const shAttested')) + 3;
const helpers = block.slice(start, end);
const agent = async (prompt) => {
  const cmdLine = prompt.split('\\n').find((l) => l.startsWith('python3 tools/gate_checks/attest_gate.py'));
  if (scenario.agent === 'honest') {
    const stdout = execFileSync('bash', ['-c', cmdLine], { cwd: process.argv[3], encoding: 'utf8' });
    return { exit_code: 0, stdout };
  }
  if (scenario.agent === 'skips') return { exit_code: 0, stdout: 'GATE_JSON:[]' };
  if (scenario.agent === 'wrong_cmd') {
    const stdout = execFileSync('bash', ['-c', cmdLine.replace(/--cmd-b64 \\S+/, '--cmd-b64 ' + Buffer.from('echo other').toString('base64'))], { cwd: process.argv[3], encoding: 'utf8' });
    return { exit_code: 0, stdout };
  }
};
const bashCalls = [];
const bash = scenario.legacy ? async (c) => { bashCalls.push(c); return 'LEGACY'; } : undefined;
const args = { execution_id_suffix: scenario.suffix || 'abc123' };
const ticketId = scenario.ticket_id || '';
const make = new Function('agent', 'bash', 'args', helpers + '; return { shAttested };');
(async () => {
  let out = null, err = null;
  try { out = await make(agent, bash, args).shAttested(scenario.cmd, 'g1', 'lbl'); } catch (e) { err = e.message; }
  process.stdout.write(JSON.stringify({ out, err, bashCalls }));
})();
"""


def _e2e(**scenario) -> dict:
    proc = subprocess.run(
        [_NODE, "-e", _E2E, json.dumps(scenario), str(SCRIPT), str(REPO_ROOT)],
        capture_output=True, text=True, timeout=60,
    )
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


@needs_node
def test_shAttested_native_returns_stdout_without_the_attest_line():
    got = _e2e(cmd="printf 'MARK:%s\\n' 1; echo second", agent="honest")
    assert got["err"] is None
    assert got["out"].startswith("MARK:1\nsecond") and "ATTEST:" not in got["out"]


@needs_node
@pytest.mark.parametrize("agent,reason", [("skips", "no ATTEST line"), ("wrong_cmd", "wrong command")])
def test_shAttested_native_fails_closed_on_an_unverifiable_result(agent, reason):
    got = _e2e(cmd="echo real", agent=agent)
    assert got["out"] is None
    assert got["err"] == f"GATE_ATTESTATION_FAILED g1: {reason}"


@needs_node
def test_shAttested_native_fails_closed_on_a_non_zero_exit():
    got = _e2e(cmd="echo broken; exit 4", agent="honest")
    assert got["err"] == "GATE_ATTESTATION_FAILED g1: command exited 4"


@needs_node
def test_shAttested_native_refuses_a_nonce_that_is_unsafe_in_a_shell_command():
    got = _e2e(cmd="echo x", agent="honest", suffix="a b; rm -rf /")
    assert got["err"].startswith("GATE_ATTESTATION_FAILED g1: execution_id_suffix must match")


@needs_node
def test_shAttested_legacy_runtime_runs_the_bare_bash_unchanged():
    got = _e2e(cmd="echo x", legacy=True)
    assert got == {"out": "LEGACY", "err": None, "bashCalls": ["echo x"]}


def test_shAttested_passes_the_ticket_id_to_the_wrapper_so_native_verdict_rows_carry_it():
    text = SCRIPT.read_text(encoding="utf-8")
    shatt = text[text.index("const shAttested"):]
    wrapper_call = shatt[:shatt.index("label || gate")]
    assert "${ticketId ? ` --ticket-id ${ticketId}` : ''}" in wrapper_call
