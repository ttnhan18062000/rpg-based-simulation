"""Throwaway prototype: run a gate command and print one attested result line.

usage: attest_gate.py --nonce N --gate-id G -- <command...>
mac = sha256("|".join([nonce, gate, command, exit_code, sha256(stdout)]))
"""
import argparse, hashlib, json, subprocess, sys

def sha(s): return hashlib.sha256(s.encode()).hexdigest()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--nonce", required=True)
    ap.add_argument("--gate-id", required=True)
    ap.add_argument("cmd", nargs=argparse.REMAINDER)
    a = ap.parse_args()
    cmd = a.cmd[1:] if a.cmd and a.cmd[0] == "--" else a.cmd
    p = subprocess.run(cmd, capture_output=True, text=True)
    cmd_s = " ".join(cmd)
    mac = sha("|".join([a.nonce, a.gate_id, cmd_s, str(p.returncode), sha(p.stdout)]))
    print("ATTEST:" + json.dumps({"gate": a.gate_id, "cmd": cmd_s, "exit_code": p.returncode,
                                  "stdout_sha": sha(p.stdout), "mac": mac}))
    sys.stdout.write(p.stdout[-2000:])

main()
