#!/usr/bin/env python3
"""M0 probe hook: append the raw stdin payload plus a few env facts to logs/<tag>.jsonl."""
import json, os, sys, time
tag = sys.argv[1]
raw = sys.stdin.read()
try:
    payload = json.loads(raw)
except Exception:
    payload = {"_unparseable": raw[:500]}
env = {k: v for k, v in os.environ.items() if k.startswith(("CLAUDE", "SESSION", "ANTHROPIC_AGENT")) and "KEY" not in k and "TOKEN" not in k}
rec = {"tag": tag, "ts": time.time(), "pid": os.getpid(), "ppid": os.getppid(), "payload": payload, "env": env}
with open(os.path.join(os.path.dirname(__file__), "..", "logs", "all.jsonl"), "a") as f:
    f.write(json.dumps(rec) + "\n")
mode = os.environ.get("M0_DECISION", "")
if tag == "PreToolUse" and mode:
    if mode == "deny":
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": "m0 probe deny"}}))
    elif mode == "ask":
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "ask", "permissionDecisionReason": "m0 probe ask"}}))
    elif mode == "allow":
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "allow"}}))
    elif mode == "garbage":
        print("not json {{{")
    elif mode == "exit2":
        sys.stderr.write("m0 probe exit 2\n"); sys.exit(2)
    elif mode == "exit1":
        sys.exit(1)
