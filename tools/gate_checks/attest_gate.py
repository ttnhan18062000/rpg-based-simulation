#!/usr/bin/env python3
"""Run a gate command and print one attested result line (TCK-20260930-NATIVE-PORT-ATTESTED-GATE-SITES).

The native Workflow runtime has no shell, so a gate command runs inside a dispatched agent and the script has to tell a
real result from a misreport. This wrapper runs the command itself and prints, first,

    ATTEST:{"gate","cmd","exit_code","stdout_sha","mac"}

with ``mac = sha256(nonce|gate|cmd|exit_code|stdout_sha)``, then the command's stdout verbatim. The verifier in
``.claude/workflows/implement-ticket.js`` (``verifyAttestation``) recomputes the mac from a nonce, gate id and expected
command that the script holds, never from the agent's prose.

ANTI-MISREPORT, NOT TAMPER-PROOF. The dispatched agent has to be handed the nonce to call this wrapper, so a
deliberately cheating agent can compute a valid mac for exit_code 0 without running anything (forged in 3 tool calls in
``TCK-20260930-NATIVE-GATE-RESULT-ATTESTATION-DESIGN``). What it catches is a missing, malformed, wrong-gate,
wrong-command or hand-edited line: the careless or hallucinated misreport. The unforgeable check is the orchestrator
re-run of ``done_checker_static.py`` before commit, and CI.

The command is passed base64-encoded (``--cmd-b64``) because gate commands are multi-line shell strings with nested
quotes that an agent would otherwise have to re-quote; it runs under ``bash -c``.

usage: attest_gate.py --nonce N --gate-id G --cmd-b64 B64
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

_MONITORING_DIR = str(Path(__file__).resolve().parents[1] / "agent-monitoring")
if _MONITORING_DIR not in sys.path:
    sys.path.insert(0, _MONITORING_DIR)


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def compute_mac(nonce: str, gate: str, cmd: str, exit_code: int, stdout_sha: str) -> str:
    return sha256_hex("|".join([nonce, gate, cmd, str(exit_code), stdout_sha]))


def attest(nonce: str, gate_id: str, cmd: str) -> tuple[str, str]:
    """Run ``cmd`` and return ``(attest_line, stdout)``."""
    # The wrapper records the one row for this verdict; keep a gate CLI inside it from writing a second.
    env = {**os.environ, "GATE_VERDICT_NO_RECORD": "1"}
    proc = subprocess.run(["bash", "-c", cmd], capture_output=True, text=True, env=env)
    stdout_sha = sha256_hex(proc.stdout)
    record = {
        "gate": gate_id,
        "cmd": cmd,
        "exit_code": proc.returncode,
        "stdout_sha": stdout_sha,
        "mac": compute_mac(nonce, gate_id, cmd, proc.returncode, stdout_sha),
    }
    return "ATTEST:" + json.dumps(record), proc.stdout


def _record(gate_id: str, cmd: str, line: str, stdout: str, enabled: bool, ticket_id: str | None = None) -> None:
    """Persist what the ATTEST line already prints (gate, cmd hash, exit code, stdout hash), never the mac."""
    import gate_verdicts  # noqa: PLC0415 - monitoring must never break the wrapper
    attested = json.loads(line[len("ATTEST:"):])
    failed = attested["exit_code"] != 0
    gate_verdicts.record_gate_verdict(
        enabled=enabled,
        gate_id=gate_id,
        gate_type="attested_command",
        verdict="FAIL" if failed else "PASS",
        blocking=failed,
        execution_mode="workflow",
        ticket_id=ticket_id,
        inputs_ref={"head_sha": gate_verdicts.head_sha(), "cmd_sha": gate_verdicts.sha256_hex(cmd),
                    "stdout_sha": attested["stdout_sha"], "exit_code": attested["exit_code"]},
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--nonce", required=True)
    parser.add_argument("--gate-id", required=True)
    parser.add_argument("--cmd-b64", required=True)
    parser.add_argument("--ticket-id", default=None, help="The ticket the run is for; recorded on the gate_verdicts row.")
    parser.add_argument("--no-record", action="store_true", help="Do not write this verdict to the gate_verdicts shard.")
    args = parser.parse_args(argv)
    cmd = base64.b64decode(args.cmd_b64).decode("utf-8")
    line, stdout = attest(args.nonce, args.gate_id, cmd)
    print(line)
    sys.stdout.write(stdout)
    try:
        _record(args.gate_id, cmd, line, stdout, enabled=not args.no_record, ticket_id=args.ticket_id)
    except Exception as exc:  # noqa: BLE001 - monitoring must never change the wrapper's output or exit code
        print(f"WARNING: gate verdict not recorded: {type(exc).__name__}: {exc}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
