"""The human gate at the command line: a terminal, an approver, and the typed id. These stop accidents and scripts, not impersonation."""

from __future__ import annotations

import builtins

import pytest

from tests.visual_assets.store import adoption_support as s
from tests.visual_assets.store.unit.conftest import snapshot
from visual_assets.store import cli, records
from visual_assets.store.adoption import PREVIEW_WARNING

ARGS = ["--visual-key", s.KEY, "--approver", "Pat Approver", "--approver-role", "art lead", "--licence", "CLEARED",
        "--licence-evidence", "note-1", "--source-asset-id", "hero"]


@pytest.fixture(autouse=True)
def clock(monkeypatch):
    monkeypatch.setattr(cli, "_now", lambda: s.NOW)
    # the fixture registry stands in for the committed (empty) one so a synthetic key can be adopted
    monkeypatch.setattr("visual_assets.store.adoption.load_registry", lambda *a, **k: s.registry())


def terminal(monkeypatch, typed):
    monkeypatch.setattr(cli, "_stdin_is_tty", lambda: True)
    prompts = []
    monkeypatch.setattr(builtins, "input", lambda prompt="": (prompts.append(prompt), typed(prompt))[1])
    return prompts


def test_adopt_refuses_without_a_terminal_and_writes_nothing(env, monkeypatch, capsys):
    result = s.make_intake(env.tmp)
    monkeypatch.setattr(cli, "_stdin_is_tty", lambda: False)
    monkeypatch.setattr(builtins, "input", lambda prompt="": pytest.fail("must not even prompt without a terminal"))
    assert cli.main(["adopt", result.intake_id, *ARGS, "--new"]) == 2
    assert "no_terminal" in capsys.readouterr().err and snapshot(env.catalog) == {}


def test_revoke_refuses_without_a_terminal_and_writes_nothing(env, monkeypatch, capsys):
    result = s.make_intake(env.tmp)
    s.do_adopt(result.intake_id)
    before = snapshot(env.catalog)
    monkeypatch.setattr(cli, "_stdin_is_tty", lambda: False)
    assert cli.main(["revoke", "hero/r0001", "--reason", "x", "--approver", "Pat", "--approver-role", "lead"]) == 2
    assert "no_terminal" in capsys.readouterr().err and snapshot(env.catalog) == before


@pytest.mark.parametrize("missing", ["--approver", "--approver-role", "--licence", "--licence-evidence", "--visual-key", "--source-asset-id"])
def test_adopt_requires_every_decision_argument(env, monkeypatch, missing):
    result = s.make_intake(env.tmp)
    terminal(monkeypatch, lambda p: result.intake_id)
    args = list(ARGS)
    index = args.index(missing)
    del args[index:index + 2]
    with pytest.raises(SystemExit) as err:
        cli.main(["adopt", result.intake_id, *args, "--new"])
    assert err.value.code == 2 and snapshot(env.catalog) == {}


def test_adopt_needs_exactly_one_of_new_or_parent(env, monkeypatch):
    result = s.make_intake(env.tmp)
    terminal(monkeypatch, lambda p: result.intake_id)
    for extra in ([], ["--new", "--parent", "r0001"]):
        with pytest.raises(SystemExit) as err:
            cli.main(["adopt", result.intake_id, *ARGS, *extra])
        assert err.value.code == 2
    assert snapshot(env.catalog) == {}


def test_revoke_requires_an_approver(env, monkeypatch):
    terminal(monkeypatch, lambda p: "x")
    for args in (["revoke", "hero/r0001", "--reason", "x", "--approver-role", "lead"],
                 ["revoke", "hero/r0001", "--reason", "x", "--approver", "Pat"],
                 ["revoke", "hero/r0001", "--approver", "Pat", "--approver-role", "lead"]):
        with pytest.raises(SystemExit) as err:
            cli.main(args)
        assert err.value.code == 2


def test_the_operator_must_type_the_exact_id_and_sees_the_warning_first(env, monkeypatch, capsys):
    result = s.make_intake(env.tmp)

    def typed(prompt):
        shown = capsys.readouterr().out
        assert PREVIEW_WARNING in shown, "the preview warning must be on screen BEFORE the prompt"
        assert "hero r0001" in shown and "stated by you, not taken from the package" in shown
        assert result.intake_id in prompt
        return result.intake_id

    prompts = terminal(monkeypatch, typed)
    assert cli.main(["adopt", result.intake_id, *ARGS, "--new"]) == 0
    assert len(prompts) == 1 and "adopted" in capsys.readouterr().out
    assert records.list_revisions("hero") == ["r0001"]


@pytest.mark.parametrize("answer", ["", "yes", "y", "IN-0123456789ABCDEF", "in-0000000000000000", "hero"])
def test_a_wrong_or_lazy_answer_confirms_nothing(env, monkeypatch, capsys, answer):
    result = s.make_intake(env.tmp)
    terminal(monkeypatch, lambda p: answer)
    assert cli.main(["adopt", result.intake_id, *ARGS, "--new"]) == 2
    assert "not_confirmed" in capsys.readouterr().err and snapshot(env.catalog) == {}


def test_revoke_asks_for_the_target_id_and_warns_it_is_final(env, monkeypatch, capsys):
    result = s.make_intake(env.tmp)
    s.do_adopt(result.intake_id)

    def typed(prompt):
        assert "never be undone" in capsys.readouterr().out and "hero/r0001" in prompt
        return "hero/r0001"

    terminal(monkeypatch, typed)
    assert cli.main(["revoke", "hero/r0001", "--reason", "rights withdrawn", "--approver", "Pat", "--approver-role", "lead"]) == 0
    assert records.revoked_revisions("hero") == {"r0001"}


def test_a_revoke_with_the_wrong_typed_id_changes_nothing(env, monkeypatch, capsys):
    result = s.make_intake(env.tmp)
    s.do_adopt(result.intake_id)
    before = snapshot(env.catalog)
    terminal(monkeypatch, lambda p: "hero")
    assert cli.main(["revoke", "hero/r0001", "--reason", "x", "--approver", "Pat", "--approver-role", "lead"]) == 2
    assert snapshot(env.catalog) == before


def test_adopt_refusals_surface_as_exit_2_with_the_code(env, monkeypatch, capsys):
    terminal(monkeypatch, lambda p: "x")
    assert cli.main(["adopt", "in-0000000000000000", *ARGS, "--new"]) == 2
    assert "unknown_intake" in capsys.readouterr().err
    result = s.make_intake(env.tmp)
    bad = [a if a != "CLEARED" else "RESTRICTED" for a in ARGS]
    assert cli.main(["adopt", result.intake_id, *bad, "--new"]) == 2
    assert "licence_not_cleared" in capsys.readouterr().err


def test_list_show_and_audit_cover_sources(env, monkeypatch, capsys):
    a, b_ = s.make_intake(env.tmp, 16), s.make_intake(env.tmp, 17)
    ad = s.do_adopt(a.intake_id)
    s.do_adopt(b_.intake_id, new=False, parent="r0001")
    from visual_assets.store.revoke import revoke

    revoke("hero/r0002", reason="x", approver="Pat", approver_role="lead", decided_at=s.NOW, confirm=s.yes)
    assert cli.main(["list"]) == 0
    listing = capsys.readouterr().out
    assert "source hero/r0001  eligible True" in listing and "source hero/r0002  eligible False" in listing
    assert cli.main(["show", ad.adoption_id]) == 0
    shown = capsys.readouterr().out
    assert "Pat Approver" in shown and "stated by the approver" in shown
    assert cli.main(["show", "hero/r0002"]) == 0 and "revoked: True" in capsys.readouterr().out
    assert cli.main(["show", a.intake_id]) == 0
    claimed = capsys.readouterr().out
    assert "claimed by the producer" in claimed and "not a clearance" in claimed
    assert cli.main(["audit"]) == 0 and "chain ok" in capsys.readouterr().out
    (env.catalog / "sources" / "hero" / "r0001.aseprite").write_bytes(b"tampered")
    assert cli.main(["audit"]) == 1
    assert "SOURCE_BYTES_HASH_MISMATCH" in capsys.readouterr().out


def test_the_server_cannot_reach_adopt_or_revoke():
    import ast
    from pathlib import Path

    server = Path(cli.__file__).resolve().parents[1] / "drawing"
    for path in server.rglob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            names = []
            if isinstance(node, ast.ImportFrom):
                names = [node.module or ""] + [f"{node.module}.{a.name}" for a in node.names]
            elif isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            for name in names:
                assert not any(name.endswith(f"store.{g}") or f"store.{g}." in name for g in ("adoption", "revoke", "catalogwrite")), (path, name)
