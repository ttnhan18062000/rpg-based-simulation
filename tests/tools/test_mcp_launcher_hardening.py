"""Static, source-text-only guards over tools/start_search_mcp.sh and tools/start_headroom_mcp.sh
for the launcher hardening in TCK-20260914-VENV-NAMING-CI-PARITY-SWAP.

No live subprocess, no real venv invocation -- CI has neither `.venv-knowledge` nor a real
headroom-ai install, so a genuine end-to-end launcher test isn't portable here (same reasoning
tests/tools/test_dashboard_makefile_targets.py already uses for the Makefile). These are pure
text/regex checks that the scripts' own selection logic can't regress back to "picks the first
candidate that merely exists" -- the exact shape that made origin/main's copy of
start_search_mcp.sh pick the freshly-renamed (headroom/sentence_transformers-less) `.venv` the
moment TCK-20260914's rename landed on this machine, a real, live breakage this hardening exists to
prevent from recurring.
"""
from __future__ import annotations

from pathlib import Path

_SEARCH_LAUNCHER = Path("tools/start_search_mcp.sh")
_HEADROOM_LAUNCHER = Path("tools/start_headroom_mcp.sh")


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_search_launcher_probes_sentence_transformers_before_selecting():
    text = _text(_SEARCH_LAUNCHER)
    assert 'import sentence_transformers' in text, (
        "expected the search launcher to probe sentence_transformers importability, not just "
        "interpreter existence, before selecting a candidate"
    )


def test_search_launcher_has_no_bare_exists_then_exec_shortcut():
    text = _text(_SEARCH_LAUNCHER)
    assert '[ -x "$py" ] && exec' not in text, (
        "expected the search launcher to no longer select a candidate on existence alone -- this "
        "exact shape is what picked the renamed, sentence_transformers-less .venv post-rename"
    )


def test_search_launcher_probe_is_quiet():
    text = _text(_SEARCH_LAUNCHER)
    assert 'import sentence_transformers" >/dev/null 2>&1' in text, (
        "expected the sentence_transformers probe to suppress both stdout and stderr on failure"
    )


def test_search_launcher_final_error_message_preserved():
    text = _text(_SEARCH_LAUNCHER)
    assert 'echo "ERROR:' in text and text.rstrip().endswith("exit 1"), (
        "expected the final no-usable-candidate error message and exit 1 to still be present"
    )


def test_search_launcher_knowledge_venv_candidates_come_before_vboxuser():
    text = _text(_SEARCH_LAUNCHER)
    knowledge_pos = text.index(".venv-knowledge/bin/python3")
    vboxuser_pos = text.index("/home/vboxuser/Work/venv/bin/python3")
    assert knowledge_pos < vboxuser_pos, (
        "expected .venv-knowledge candidates to be tried before the vboxuser fallback path"
    )


def test_headroom_launcher_probes_headroom_import_before_selecting():
    text = _text(_HEADROOM_LAUNCHER)
    assert 'import headroom' in text, (
        "expected the headroom launcher to probe `headroom` importability, not just interpreter "
        "existence, before selecting a candidate"
    )


def test_headroom_launcher_invokes_module_not_the_wrapper_binary():
    text = _text(_HEADROOM_LAUNCHER)
    assert "-m headroom.cli" in text, (
        "expected the headroom launcher to invoke `-m headroom.cli` directly -- the installed "
        "console-script wrapper bakes its interpreter path into its own shebang at pip-install "
        "time, so executing the wrapper binary itself silently breaks across any future rename "
        "even when the wrapper file is found at the right new location"
    )
    assert 'exec "$bin" mcp serve' not in text, (
        "expected the old wrapper-binary exec pattern to be gone, replaced by module invocation"
    )


def test_headroom_launcher_probe_is_quiet():
    text = _text(_HEADROOM_LAUNCHER)
    assert 'import headroom" >/dev/null 2>&1' in text, (
        "expected the headroom probe to suppress both stdout and stderr on failure"
    )


def test_headroom_launcher_has_no_bare_exists_then_select_shortcut():
    text = _text(_HEADROOM_LAUNCHER)
    assert 'if [ -x "$bin" ]; then' not in text, (
        "expected the headroom launcher to no longer select a candidate on existence alone -- "
        "existence never implied the installed wrapper's shebang still pointed at a working "
        "interpreter"
    )


def test_headroom_launcher_final_error_message_preserved():
    text = _text(_HEADROOM_LAUNCHER)
    assert 'echo "ERROR:' in text and text.rstrip().endswith("exit 1"), (
        "expected the final no-usable-candidate error message and exit 1 to still be present"
    )


def test_headroom_launcher_knowledge_venv_candidates_come_before_vboxuser():
    text = _text(_HEADROOM_LAUNCHER)
    knowledge_pos = text.index(".venv-knowledge/bin/python3")
    vboxuser_pos = text.index("/home/vboxuser/Work/venv/bin/python3")
    assert knowledge_pos < vboxuser_pos, (
        "expected .venv-knowledge candidates to be tried before the vboxuser fallback path"
    )


def test_headroom_launcher_still_sets_isolated_workspace_dir():
    text = _text(_HEADROOM_LAUNCHER)
    assert "HEADROOM_WORKSPACE_DIR=" in text, (
        "expected the isolation env var to still be exported before launching the server -- "
        "unrelated to this hardening pass, but a real regression if lost"
    )
