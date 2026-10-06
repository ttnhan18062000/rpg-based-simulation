"""`submit_candidate`, `store_list`, `store_show` over real stdio, against an ISOLATED copy of the package (its own catalog and quarantine).

No Aseprite needed: the handoff directories are written with the test builders, so these run in CI. The real chain with Aseprite is in
`integration/test_server_stdio.py`.
"""

from __future__ import annotations

import hashlib
import json

import pytest

from tests.visual_assets.drawing.stdio_support import data, isolated_repo, run, session, text
from tests.visual_assets.store import builders as b
from tests.visual_assets.store.unit.conftest import snapshot


@pytest.fixture
def world(tmp_path):
    from types import SimpleNamespace

    root = isolated_repo(tmp_path)
    return SimpleNamespace(root=root, workspace=tmp_path / "ws", catalog=root / "visual_assets" / "catalog", quarantine=root / "visual_assets" / "catalog" / ".quarantine")


def make_handoff(world, *, tamper=False, width=16, brief="brief") -> str:
    """A handoff directory shaped exactly like export_handoff's, named by its handoff id."""
    source = b.aseprite(width=width)
    preview = b.png(width * 8, 16 * 8)
    package = b.package_bytes(source, preview, brief_id=brief)
    if tamper:
        source = source[:-1] + bytes([source[-1] ^ 1])  # the claimed hash no longer matches
    candidate = "cand-" + hashlib.sha256(source).hexdigest()[:16]
    handoff_id = f"{candidate}--{hashlib.sha256(package).hexdigest()[:12]}"
    b.write_dir(world.workspace / "handoffs" / handoff_id, package, source, preview)
    return handoff_id


def call(world, name, args=None, *, many=None):
    async def go():
        async with session(world.workspace, world.root) as s:
            if many is not None:
                return [await s.call_tool(n, a) for n, a in many]
            return await s.call_tool(name, args or {})

    return run(go())


def test_the_tool_surface_is_exact_and_the_new_tools_say_what_they_are(world):
    async def go():
        async with session(world.workspace, world.root) as s:
            return await s.list_tools()

    from tests.visual_assets.drawing.stdio_support import EXPECTED_TOOLS

    listed = run(go())
    assert {t.name for t in listed.tools} == EXPECTED_TOOLS
    descriptions = {t.name: t.description for t in listed.tools}
    assert "NOT an adoption" in descriptions["submit_candidate"] and "read-only" in descriptions["store_list"].lower()
    assert "read-only" in descriptions["store_show"].lower()


def test_the_server_instructions_state_the_gates_in_one_sentence():
    from visual_assets.drawing.server.app import mcp

    sentence = next(part for part in mcp.instructions.split(". ") if part.startswith("Gates:"))
    assert "human decisions with no tool on this server" in sentence
    assert all(word in sentence for word in ("adopting", "revoking", "building", "releasing", "deleting"))


def test_submitting_a_handoff_gives_a_verdict_and_writes_only_the_quarantine(world):
    handoff_id = make_handoff(world)
    before = snapshot(world.catalog)
    result = call(world, "submit_candidate", {"handoff_id": handoff_id})
    assert not result.isError
    out = data(result)
    assert out["verdict"] == "PASSED" and out["findings"] == [] and out["handoff_id"] == handoff_id and out["intake_id"].startswith("in-")
    assert "human" in out["note"] and "/" not in "".join(v for v in out.values() if isinstance(v, str) and v is not out["note"])
    after = snapshot(world.catalog)
    changed = {k for k in set(before) | set(after) if before.get(k) != after.get(k)}
    assert changed and all(k == ".quarantine" or k.startswith(".quarantine/") for k in changed)  # only the quarantine was written
    assert (world.quarantine / out["intake_id"] / "intake_result.json").is_file()


def test_submitting_twice_returns_the_same_intake_and_writes_nothing_more(world):
    handoff_id = make_handoff(world)
    first = data(call(world, "submit_candidate", {"handoff_id": handoff_id}))
    before = snapshot(world.catalog)
    second = data(call(world, "submit_candidate", {"handoff_id": handoff_id}))
    assert second["intake_id"] == first["intake_id"] and snapshot(world.catalog) == before


def test_a_tampered_handoff_is_quarantined_with_findings(world):
    result = call(world, "submit_candidate", {"handoff_id": make_handoff(world, tamper=True)})
    out = data(result)
    assert not result.isError and out["verdict"] == "QUARANTINED"
    codes = {f["code"] for f in out["findings"]}
    assert "SOURCE_HASH_MISMATCH" in codes and all(f["detail"] for f in out["findings"])


@pytest.mark.parametrize("bad", [
    "..", "../x", "/etc/passwd", "cand-0123456789abcdef", "cand-0123456789abcdef--", "cand-0123456789abcdef--0123456789ab/..",
    "cand-0123456789abcdef--0123456789ab/../../x", "cand-0123456789abcdef--0123456789ab\n", "CAND-0123456789ABCDEF--0123456789AB", "", " ", "x" * 300,
    "cand-0123456789abcdef--0123456789ab", "handoffs/cand-0123456789abcdef--0123456789ab", "..\\x", "cand-0123456789abcdeg--0123456789ab",
])
def test_an_unknown_path_like_or_bare_id_is_refused_and_writes_nothing(world, bad):
    before = snapshot(world.catalog)
    result = call(world, "submit_candidate", {"handoff_id": bad})
    assert result.isError and "/home/" not in text(result) and "/tmp/" not in text(result)
    assert snapshot(world.catalog) == before and not world.quarantine.exists()


def test_a_bare_candidate_id_is_refused_even_when_that_handoff_exists(world):
    handoff_id = make_handoff(world)
    candidate = handoff_id.split("--")[0]
    result = call(world, "submit_candidate", {"handoff_id": candidate})
    assert result.isError and "handoff id" in text(result) and not world.quarantine.exists()


def test_a_symlinked_handoff_directory_is_refused(world):
    handoff_id = make_handoff(world)
    real = world.workspace / "handoffs" / handoff_id
    moved = world.workspace / "elsewhere"
    real.rename(moved)
    real.symlink_to(moved, target_is_directory=True)
    result = call(world, "submit_candidate", {"handoff_id": handoff_id})
    assert result.isError and not world.quarantine.exists()


def test_store_list_and_show_read_the_store_and_change_nothing(world):
    handoff_id = make_handoff(world)
    intake_id = data(call(world, "submit_candidate", {"handoff_id": handoff_id}))["intake_id"]
    before = snapshot(world.catalog)
    results = call(world, None, many=[("store_list", {"kind": "intake"}), ("store_list", {"kind": "source"}), ("store_list", {"kind": "artifact"}),
                                      ("store_list", {"kind": "release"}), ("store_show", {"kind": "intake", "id": intake_id}),
                                      ("store_list", {"kind": "intake", "limit": 1})])
    assert all(not r.isError for r in results)
    listed, sources, artifacts, releases, shown, limited = (data(r) for r in results)
    assert [i["intake_id"] for i in listed["items"]] == [intake_id] and sources["count"] == 34 and artifacts["count"] == 34 and releases["count"] == 5
    # the owner adopted terrain-v1 on 2026-10-05T18:17:03Z: 34 sources (forest's three + 22 terrain tiles + 9 border masks); `build` produced one artifact per source (34) and `pilot/rc-0005` (the user approved both on 2026-10-06) joined rc-0001 to rc-0004 (5 candidates)
    assert shown["verdict"] == "PASSED" and "unverified" in shown["claimed_by_producer"]["note"] and limited["count"] == 1
    for r in results:
        assert "/home/" not in text(r) and "/tmp/" not in text(r) and "pytest-of-" not in text(r)
        assert len(text(r)) < 20_000
    assert snapshot(world.catalog) == before  # byte-identical


def test_store_tools_refuse_bad_kinds_ids_and_limits(world):
    results = call(world, None, many=[
        ("store_list", {"kind": "adopt"}), ("store_list", {"kind": "intake", "limit": 0}), ("store_list", {"kind": "intake", "limit": 10_000}),
        ("store_show", {"kind": "intake", "id": "../x"}), ("store_show", {"kind": "source", "id": "ghost/r0001"}),
        ("store_show", {"kind": "release", "id": "main/latest"}), ("store_show", {"kind": "secrets", "id": "x"}),
    ])
    assert all(r.isError for r in results)
    assert not world.quarantine.exists()


def test_a_listing_is_bounded_even_with_many_intakes(world):
    for width in range(1, 8):
        call(world, "submit_candidate", {"handoff_id": make_handoff(world, width=width)})
    page = data(call(world, "store_list", {"kind": "intake", "limit": 3}))
    assert page["count"] == 3 and page["truncated"] is True
    assert json.dumps(page).count("in-") >= 3


def test_tool_failures_are_plain_value_errors_carrying_the_coded_path_free_message():
    """The helper's contract (the same convention as the drawing tools' `call`): a store or drawing refusal reaches the agent as a ValueError, not an internal exception."""
    from visual_assets.drawing.server import store_readonly_tools as tools
    from visual_assets.store.errors import StoreError

    for fn, args, fragment in ((tools.store_show, ("intake", "../x"), "invalid_id"), (tools.store_list, ("adopt",), "unknown_kind"),
                               (tools.submit_candidate, ("..",), "handoff id looks like")):
        with pytest.raises(ValueError) as err:
            fn(*args)
        assert not isinstance(err.value, StoreError) and fragment in str(err.value)
        assert "/home/" not in str(err.value) and "Traceback" not in str(err.value)
