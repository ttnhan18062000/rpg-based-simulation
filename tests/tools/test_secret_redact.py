"""Secret-shaped strings are redacted on write: tool rows and the handover transit bundle.

TCK-20261031-SDLC-GUARD-PAYLOADS-AND-SECRET-REDACTION. Every fake credential here is BUILT by concatenation, so no
token-shaped literal is ever in this file or in git (gitleaks and the Phase 0 scan would flag one). The last test scans
this file and the two writers with the shared shape list, after a positive control proves the scan can match.
"""
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO / "tools" / "agent-monitoring"))
sys.path.insert(0, str(_REPO / "tools"))

import secret_redact as sr  # noqa: E402
import handover_transit as ht  # noqa: E402

A36 = "A" * 36


def fakes() -> dict:
    """One fake credential per redacted shape, assembled from pieces."""
    return {
        "github_token": "gh" + "p_" + A36,
        "github_pat": "github" + "_pat_" + "B" * 30,
        "aws_access_key_id": "AK" + "IA" + "ABCDEFGHIJKLMNOP",
        "slack_token": "xo" + "xb-" + "1234567890-abcdef",
        "openai_api_key": "s" + "k-" + "C" * 30,
        "anthropic_api_key": "s" + "k-" + "ant-" + "api03-" + "Zz_9-" * 10,  # hyphenated tail, as real keys are
        "bearer_token": "Bea" + "rer " + "d" * 24,
        "basic_auth_in_url": "https://" + "user" + ":" + "hunter22" + "@",
        "generic_api_key_assignment": "api" + "_key" + '="' + "E" * 20 + '"',
        "pem_private_key_header": "-----BEGIN " + "RSA PRIVATE KEY" + "-----\nMIIEow\n-----END " + "RSA PRIVATE KEY" + "-----",
    }


@pytest.mark.parametrize("name,value", sorted(fakes().items()))
def test_every_shape_is_replaced_by_a_marker(name, value):
    out = sr.redact_text(f"before {value} after")
    assert value not in out and out.startswith("before [REDACTED:") and out.endswith("] after")
    assert sr.count_text(value) >= 1


def test_the_marker_names_the_shape():
    assert sr.redact_text(fakes()["github_token"]) == "[REDACTED:github_token]"
    assert sr.redact_text(fakes()["aws_access_key_id"]) == "[REDACTED:aws_access_key_id]"
    assert sr.redact_text(fakes()["anthropic_api_key"]) == "[REDACTED:anthropic_api_key]"
    assert sr.redact_text(fakes()["pem_private_key_header"]) == "[REDACTED:pem_private_key_header]"


def test_a_private_key_block_is_redacted_whole_not_just_its_header_line():
    block = fakes()["pem_private_key_header"] + "\nafter"
    assert sr.redact_text(block) == "[REDACTED:pem_private_key_header]\nafter"
    truncated = "-----BEGIN " + "EC PRIVATE KEY" + "-----\nMHcCAQEE"  # a cut-off block: the rest of the text goes
    assert "MHcCAQEE" not in sr.redact_text(truncated)


def test_a_hyphenated_anthropic_key_is_redacted_whole():
    key = fakes()["anthropic_api_key"]
    out = sr.redact_text(f"export K={key}; echo done")
    assert out == "export K=[REDACTED:anthropic_api_key]; echo done"


def test_redaction_is_idempotent_and_leaves_ordinary_text_alone():
    ordinary = "git push origin feature-branch && python3 -m pytest tests/tools -q  # sk-short, ghp_short, AKIA123, password=hunter2"
    assert sr.redact_text(ordinary) == ordinary
    once = sr.redact_text("x " + fakes()["openai_api_key"])
    assert sr.redact_text(once) == once


def test_there_is_one_shape_list_and_it_is_the_write_path_guards():
    import write_path_guard as wpg  # noqa: PLC0415 -- the tools dir is on sys.path above
    assert set(sr.REDACTED_SHAPES) <= set(wpg._SECRET_SCAN_PATTERNS)  # nothing of its own
    assert sr._PATTERNS["github_token"] is wpg._SECRET_SCAN_PATTERNS["github_token"]  # the same compiled object, not a copy
    assert "generic_password_or_secret_assignment" not in sr.REDACTED_SHAPES  # `password=` stays out (false positives)
    for name, value in fakes().items():
        assert wpg.scan_for_secrets(value) is not None  # the scan and the redactor agree on every redacted shape


def test_known_limits_are_stated_not_hidden():
    """Shapes the shared list does not have. Widening it is a separate decision; this test changes with that decision."""
    jwt = "ey" + "J" + "hbGciOiJIUzI1NiJ9" + "." + "ey" + "J" + "zdWIiOiIxMjM0NTY3ODkwIn0" + "." + "sig_part-1"
    hyphen_key = "s" + "k-" + "proj-" + "A1b2C3d4E5f6G7h8I9j0K1l2"
    assert sr.redact_text(jwt) == jwt
    assert sr.redact_text(hyphen_key) == hyphen_key


def test_bytes_redaction_counts_and_passes_other_bytes_through():
    data = b"\xff\xfe binary " + fakes()["github_token"].encode() + b" tail " + fakes()["aws_access_key_id"].encode()
    out, hits = sr.redact_bytes(data)
    assert hits == 2 and out.startswith(b"\xff\xfe binary ") and b"[REDACTED:github_token]" in out
    assert fakes()["github_token"].encode() not in out


def test_safe_redact_never_raises_and_never_returns_the_raw_text(monkeypatch):
    token = fakes()["github_token"]
    monkeypatch.setattr(sr, "redact_text", lambda text: (_ for _ in ()).throw(RuntimeError("boom")))
    assert sr.safe_redact_text("x " + token) == sr.REDACTION_FAILED
    assert sr.safe_redact_text("") == ""
    monkeypatch.undo()
    assert sr.safe_redact_text(None) is None or sr.safe_redact_text(None) == sr.REDACTION_FAILED


# --- tool rows -----------------------------------------------------------------------------------------------

def _hook_summary(tool, tool_input):
    """Run the real hook's `_input_summary` without running the hook (the module executes on import)."""
    src = (_REPO / "tools" / "agent-monitoring" / "post_tool_hook.py").read_text(encoding="utf-8")
    start = src.index("def _input_summary")
    end = src.index("\ntry:\n    payload = json.load")
    ns = {"redact_text": sr.redact_text}
    exec(src[start:end], ns)  # noqa: S102 - the function body only, from this repository's own file
    return ns["_input_summary"](tool, tool_input)


@pytest.mark.parametrize("tool,key", [("Bash", "command"), ("Read", "file_path"), ("Agent", "description"), ("Edit", "file_path")])
def test_a_token_in_a_tool_input_never_reaches_the_row_summary(tool, key):
    token = fakes()["github_token"]
    out = _hook_summary(tool, {key: f"x {token} y"})
    assert token not in out and "[REDACTED:github_token]" in out


def test_a_token_that_the_cut_would_split_is_still_redacted():
    token = fakes()["github_token"]
    command = "a" * 70 + token  # the 80-character cut would land inside the token
    out = _hook_summary("Bash", {"command": command})
    assert len(out) <= 80 and token[:12] not in out.replace("[REDACTED", "")


def test_mcp_query_and_other_tool_inputs_are_redacted_too():
    token = fakes()["openai_api_key"]
    assert token not in _hook_summary("mcp__x__search", {"query": token})
    assert token not in _hook_summary("WebFetch", {"url": "https://x/?k=" + token})


def _run_hook(tmp_path, payload, hook_dir=None):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    script = (hook_dir or (_REPO / "tools" / "agent-monitoring")) / "post_tool_hook.py"
    subprocess.run([sys.executable, str(script)], input=json.dumps(payload), text=True, cwd=tmp_path, capture_output=True, check=True)
    rows = [p for p in tmp_path.rglob("*tools.jsonl")]
    return "".join(p.read_text(encoding="utf-8") for p in rows)


def test_the_real_hook_writes_a_row_without_the_token(tmp_path):
    token = fakes()["github_token"]
    text = _run_hook(tmp_path, {"tool_name": "Bash", "tool_input": {"command": f"echo {token}"}, "session_id": "redact-test",
                                "hook_event_name": "PostToolUse", "tool_response": {}})
    assert "redact-test" in text and token not in text and "[REDACTED:github_token]" in text


def test_every_string_field_of_the_row_is_redacted_not_only_the_summary(tmp_path):
    token = fakes()["github_token"]
    text = _run_hook(tmp_path, {"tool_name": "Bash", "tool_input": {"command": "ls"}, "session_id": "sess-" + token,
                                "hook_event_name": "PostToolUse", "tool_response": {}})
    assert token not in text and "sess-[REDACTED:github_token]" in text  # session_id is not free text, and is still covered


@pytest.mark.parametrize("failure", ["missing", "broken"])
def test_if_the_redactor_fails_the_summary_is_a_marker_never_raw_and_the_row_stays_valid(tmp_path, failure):
    token = fakes()["github_token"]
    work = tmp_path / "work"
    shutil.copytree(_REPO / "tools", work / "tools", ignore=shutil.ignore_patterns("__pycache__"))  # the hook finds its repo from its own path
    redactor = work / "tools" / "agent-monitoring" / "secret_redact.py"
    if failure == "missing":
        redactor.unlink()  # the import fails
    else:
        redactor.write_text("raise RuntimeError('broken redactor')\n")  # the import raises
    text = _run_hook(work, {"tool_name": "Bash", "tool_input": {"command": f"echo {token}"}, "session_id": "redact-fail",
                            "hook_event_name": "PostToolUse", "tool_response": {}}, hook_dir=work / "tools" / "agent-monitoring")
    row = json.loads(text.strip().splitlines()[-1])
    assert token not in text and row["input_summary"] == "[REDACTION_FAILED]"
    assert row["status"] == "ok" and row["tool"] == "Bash" and row["ts"].endswith("Z")  # identifiers are not turned into markers


def test_a_failure_while_redacting_one_value_marks_that_value(monkeypatch):
    token = fakes()["github_token"]
    monkeypatch.setattr(sr, "redact_text", lambda text: (_ for _ in ()).throw(RuntimeError("boom")))
    assert _hook_summary_with_safe("Bash", {"command": f"echo {token}"}) == "[REDACTION_FAILED]"


def _hook_summary_with_safe(tool, tool_input):
    src = (_REPO / "tools" / "agent-monitoring" / "post_tool_hook.py").read_text(encoding="utf-8")
    ns = {"redact_text": sr.safe_redact_text}
    exec(src[src.index("def _input_summary"):src.index("\ntry:\n    payload = json.load")], ns)  # noqa: S102
    return ns["_input_summary"](tool, tool_input)


# --- transit bundle ---------------------------------------------------------------------------------------------

def _export(tmp_path, notes: dict):
    handover = tmp_path / "handover"
    handover.mkdir()
    for name, text in notes.items():
        (handover / name).write_text(text, encoding="utf-8")
    memory = tmp_path / "memory"
    memory.mkdir()
    (memory / "MEMORY.md").write_text("# index\n", encoding="utf-8")
    root = tmp_path / "transit"
    bundle = ht.export_bundle(root=root, handover_dir=handover, memory_dir=memory, host="h1", draft_filter=None)
    return handover, bundle


def test_the_export_replaces_a_token_in_a_note_and_leaves_the_local_file_alone(tmp_path):
    token = fakes()["github_token"]
    handover, bundle = _export(tmp_path, {"role.md": f"# note\nthe token is {token}\n"})
    stored = (bundle / "files" / "handover" / "role.md.txt").read_text(encoding="utf-8")
    assert token not in stored and "[REDACTED:github_token]" in stored
    assert token in (handover / "role.md").read_text(encoding="utf-8")  # the local note is not rewritten
    assert token not in "".join(p.read_text(encoding="utf-8", errors="replace") for p in bundle.rglob("*") if p.is_file())
    rows = {r["path"]: r for r in ht._read_manifest(bundle)}
    assert rows["role.md"]["redacted"] == 1


def test_the_manifest_hash_describes_the_stored_file_so_import_still_verifies(tmp_path):
    token = fakes()["openai_api_key"]
    handover, bundle = _export(tmp_path, {"role.md": f"{token}\n"})
    target = tmp_path / "other-handover"
    actions = ht.import_bundle("h1", root=tmp_path / "transit", handover_dir=target, memory_dir=tmp_path / "mem2", local_host="h2")
    assert any("create" in a for a in actions)
    assert "[REDACTED:openai_api_key]" in (target / "role.md").read_text(encoding="utf-8")


def test_a_note_without_a_token_exports_byte_identically(tmp_path):
    handover, bundle = _export(tmp_path, {"role.md": "# plain note\nno secrets here\n"})
    assert (bundle / "files" / "handover" / "role.md.txt").read_bytes() == (handover / "role.md").read_bytes()
    assert "redacted" not in ht._read_manifest(bundle)[0]


def test_a_file_whose_redaction_fails_is_left_out_and_named_in_the_manifest(tmp_path, monkeypatch):
    token = fakes()["github_token"]
    real = ht.redact_bytes

    def flaky(data):
        if b"POISON" in data:
            raise RuntimeError("boom")
        return real(data)

    monkeypatch.setattr(ht, "redact_bytes", flaky)
    handover, bundle = _export(tmp_path, {"bad.md": f"POISON {token}\n", "good.md": f"fine {token}\n"})
    assert not (bundle / "files" / "handover" / "bad.md.txt").exists()
    assert (bundle / "files" / "handover" / "good.md.txt").is_file()
    assert [r["path"] for r in ht._read_manifest(bundle)] == ["good.md", "MEMORY.md"] or {r["path"] for r in ht._read_manifest(bundle)} >= {"good.md"}
    skipped = ht.skipped_rows(bundle)
    assert [(r["path"], r["skipped"]) for r in skipped] == [("bad.md", "redaction_failed")]
    assert token not in "".join(p.read_text(encoding="utf-8", errors="replace") for p in bundle.rglob("*") if p.is_file())
    assert "bad.md" not in {r["path"] for r in ht._read_manifest(bundle)}
    # the bundle still imports: a skipped row has no stored copy and is not an error
    ht.import_bundle("h1", root=tmp_path / "transit", handover_dir=tmp_path / "h2", memory_dir=tmp_path / "m2", local_host="h2")


def test_every_file_type_in_the_bundle_is_redacted_notes_drafts_memory_and_non_text(tmp_path):
    token = fakes()["github_token"]
    handover = tmp_path / "handover"
    (handover / "drafts" / "x").mkdir(parents=True)
    (handover / "role.md").write_text(f"note {token}\n", encoding="utf-8")
    (handover / "drafts" / "x" / "ticket.yaml").write_text(f"k: {token}\n", encoding="utf-8")
    (handover / "drafts" / "x" / "data.json").write_text(json.dumps({"t": token}), encoding="utf-8")
    (handover / "drafts" / "x" / "blob.bin").write_bytes(b"\x00\xff" + token.encode() + b"\x00")
    memory = tmp_path / "memory"
    memory.mkdir()
    (memory / "MEMORY.md").write_text(f"- [x](x.md) {token}\n", encoding="utf-8")
    bundle = ht.export_bundle(root=tmp_path / "transit", handover_dir=handover, memory_dir=memory, host="h1", draft_filter=None)
    stored = [p for p in (bundle / "files").rglob("*") if p.is_file()]
    assert len(stored) >= 5
    assert all(token.encode() not in p.read_bytes() for p in stored)
    assert all(token.encode() in p.read_bytes() for p in handover.rglob("*") if p.is_file())  # the local copies are untouched


# --- no token-shaped literal in git ----------------------------------------------------------------------------

def test_no_token_shaped_literal_in_this_file_or_the_redactor_or_the_writers():
    import write_path_guard as wpg  # noqa: PLC0415 -- the tools dir is on sys.path above
    # positive control first: the scan must be able to match, or an empty result means nothing
    assert wpg.scan_for_secrets("gh" + "p_" + A36) == "github_token"
    for rel in ("tests/tools/test_secret_redact.py", "tools/agent-monitoring/secret_redact.py",
                "tools/agent-monitoring/post_tool_hook.py", "tools/handover_transit.py"):
        hit = wpg.scan_for_secrets((_REPO / rel).read_text(encoding="utf-8"))
        assert hit is None, f"{rel} holds a {hit} shape"
