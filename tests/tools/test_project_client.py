"""TCK-20261114-PROJECT-SYNC-INIT-AND-APPLY: ProjectClient, --init and --apply with an injected fake. No network, no real token."""
import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from tools.sessions import project_client as pc
from tools.sessions import project_sync as ps

SENTINEL = "ghp_SENTINEL_TOKEN_VALUE_123"
STATUSES = ps.STATUSES
LAYERS = ("combat", "world")


def field(name, typ, options=()):
    return pc.ProjectField(f"F_{name}", name, typ, tuple((o, f"O_{o}") for o in options))


def project(extra=(), status_options=("Todo", "In Progress", "Done"), skip=()):
    fields = {"Title": field("Title", "TITLE"), "Status": field("Status", "SINGLE_SELECT", status_options)}
    for n in pc.TEXT_FIELDS:
        fields[n] = field(n, "TEXT")
    fields["Tier"] = field("Tier", "SINGLE_SELECT", [n for n, _ in pc.TIER_OPTIONS])
    fields["Priority"] = field("Priority", "SINGLE_SELECT", [n for n, _ in pc.PRIORITY_OPTIONS])
    fields["Layer"] = field("Layer", "SINGLE_SELECT", LAYERS)
    for n in skip:
        fields.pop(n)
    for f in extra:
        fields[f.name] = f
    return pc.Project("P1", fields)


class Fake:
    """Records every mutation as a tuple; reads come from the given project and items."""

    def __init__(self, proj, items=(), fail_on=None):
        self.proj, self.items, self.calls, self.fail_on = proj, list(items), [], fail_on

    def _rec(self, *call):
        if self.fail_on == len(self.calls):
            raise pc.ProjectError("boom")
        self.calls.append(call)

    def load_project(self):
        return self.proj

    def list_items(self):
        return self.items

    def create_text_field(self, pid, name): self._rec("create_text", name)
    def create_select_field(self, pid, name, options): self._rec("create_select", name)
    def set_select_options(self, fid, options): self._rec("options", fid, [(n, i) for n, _, i in options])
    def add_draft(self, pid, title, body):
        self._rec("add_draft", title)
        return "ITEM-NEW", "DRAFT-NEW"
    def update_draft(self, did, title, body): self._rec("update_draft", did, title)
    def set_text(self, pid, iid, fid, text): self._rec("set", iid, fid, text)
    def set_option(self, pid, iid, fid, oid): self._rec("set", iid, fid, oid)
    def clear_value(self, pid, iid, fid): self._rec("clear", iid, fid)
    def archive(self, pid, iid): self._rec("archive", iid)


# ---- init
def status_project(options):
    return project(status_options=options)


def test_init_creates_missing_fields_and_leaves_present_ones_alone():
    fake = Fake(project(status_options=STATUSES, skip=("Host", "Tier", "Epic")))
    lines, code = pc.init_fields(fake, STATUSES, layers=LAYERS)
    assert code == 0 and ("create_text", "Host") in fake.calls and ("create_text", "Epic") in fake.calls and ("create_select", "Tier") in fake.calls
    assert "left alone: Seat" in lines and "created: Host" in lines


def test_a_second_init_creates_and_updates_nothing():
    fake = Fake(project(status_options=STATUSES))
    lines, code = pc.init_fields(fake, STATUSES, layers=LAYERS)
    assert code == 0 and fake.calls == [] and not any(l.startswith(("created", "updated")) for l in lines)


def test_init_sets_exactly_the_status_options_on_an_empty_project():
    fake = Fake(project())
    pc.init_fields(fake, STATUSES, layers=LAYERS)
    assert fake.calls == [("options", "F_Status", [(n, "O_Done" if n == "Done" else None) for n in STATUSES])]  # GitHub's default Done keeps its id


def test_init_appends_status_options_on_a_board_with_items_keeping_ids_and_reporting_extras():
    fake = Fake(project(status_options=("To do", "Legacy", "Done")), items=[{"_item_id": "I1"}])
    lines, code = pc.init_fields(fake, STATUSES, layers=LAYERS)
    assert code == 0 and "kept, not in STATUSES: Legacy" in lines
    (call,) = fake.calls
    assert call[2][:3] == [("To do", "O_To do"), ("Legacy", "O_Legacy"), ("Done", "O_Done")]  # existing ids, order kept
    assert [n for n, i in call[2][3:]] == ["In progress", "Stale", "In review", "Blocked"] and all(i is None for _, i in call[2][3:])


def test_the_replace_flag_drops_only_the_option_left_out_and_keeps_the_other_ids():
    fake = Fake(project(status_options=("To do", "Legacy", "Done")), items=[{"_item_id": "I1"}])
    pc.init_fields(fake, STATUSES, replace_status_options=True, layers=LAYERS)
    (call,) = fake.calls
    got = dict(call[2])
    assert [n for n, _ in call[2]] == list(STATUSES) and "Legacy" not in got
    assert got["To do"] == "O_To do" and got["Done"] == "O_Done" and got["Stale"] is None


def test_the_replace_flag_with_statuses_reordered_keeps_every_id():
    fake = Fake(project(status_options=tuple(reversed(STATUSES))), items=[{"_item_id": "I1"}])
    pc.init_fields(fake, STATUSES, replace_status_options=True, layers=LAYERS)
    (call,) = fake.calls
    assert [n for n, _ in call[2]] == list(STATUSES) and all(i == f"O_{n}" for n, i in call[2])


def test_merge_options_keeps_ids_and_order_and_appends_without_dropping():
    f = field("X", "SINGLE_SELECT", ("a", "b"))
    merged = pc.merge_options(f, [("b", "RED"), ("c", "GREEN")])
    assert merged == [("a", "GRAY", "O_a"), ("b", "GRAY", "O_b"), ("c", "GREEN", None)]


def test_set_select_options_sends_the_id_only_for_kept_options(tmp_path):
    seen = []
    c, _ = client_with(tmp_path, lambda a, e, s: (seen.append(json.loads(s)), SimpleNamespace(returncode=0, stdout=json.dumps({"data": {"updateProjectV2Field": {}}}), stderr=""))[1])
    c.set_select_options("F1", [("a", "GRAY", "O_a"), ("c", "GREEN", None)])
    assert seen[0]["variables"]["input"]["singleSelectOptions"] == [
        {"id": "O_a", "name": "a", "color": "GRAY", "description": ""}, {"name": "c", "color": "GREEN", "description": ""}]


def test_init_adds_a_newly_registered_layer_option_and_a_rerun_is_a_no_op():
    fake = Fake(project(status_options=STATUSES))
    lines, _ = pc.init_fields(fake, STATUSES, layers=LAYERS + ("platform",))
    (call,) = fake.calls
    assert call[1] == "F_Layer" and call[2] == [("combat", "O_combat"), ("world", "O_world"), ("platform", None)]
    assert "updated: Layer options + platform" in lines
    fake2 = Fake(project(status_options=STATUSES))
    pc.init_fields(fake2, STATUSES, layers=LAYERS)
    assert fake2.calls == []


def test_init_refuses_a_same_named_field_of_the_wrong_type_and_writes_nothing():
    fake = Fake(project(extra=[field("Seat", "NUMBER")], skip=("Host",)))
    lines, code = pc.init_fields(fake, STATUSES, layers=LAYERS)
    assert code == 1 and fake.calls == [] and "Seat" in lines[0]


# ---- apply
def derived(tid="TCK-1", **kw):
    d = {"Title": f"{tid}: t", "Ticket ID": tid, "Status": "In progress", "Domain": "rpg", "Seat": "s", "Host": "h", "Branch": "h:b",
         "PR": "", "Tier": "hotfix", "Layer": "combat", "Priority": "P1", "Epic": "standalone", "Tags": "a b", "Body": "b", "Source": "src", "Sync hash": "H"}
    d.update(kw)
    return d


def full_project():
    return project(status_options=STATUSES)


def test_apply_turns_creates_updates_and_archives_into_the_expected_mutations_with_sync_hash_last():
    plan = ps.Plan(creates=[derived("TCK-1")],
                   updates=[({**derived("TCK-2", Title="TCK-2: new", PR=""), "_item_id": "I2", "_draft_id": "D2"}, ["Title", "Status", "PR"])],
                   archives=[("TCK-3", "no ticket file for this ID")], archive_item_ids=["I3"])
    fake = Fake(full_project())
    done, not_done, error = pc.apply_plan(fake, full_project(), plan)
    assert error is None and not not_done
    first = [c for c in fake.calls]
    assert first[0] == ("add_draft", "TCK-1: t")
    create_sets = first[1:14]  # thirteen value sets: PR is empty, so skipped
    assert [c[2] for c in create_sets][0] == "F_Ticket ID" and create_sets[-1][2] == "F_Sync hash"  # Ticket ID first, Sync hash last; PR "" skipped
    assert not any(c[2] == "F_PR" for c in create_sets) and all(c[1] == "ITEM-NEW" for c in create_sets)
    upd = [c for c in first if c[0] in ("update_draft", "clear") or c[1:2] == ("I2",)]
    assert upd[0] == ("update_draft", "D2", "TCK-2: new") and ("clear", "I2", "F_PR") in upd and upd[-1][2] == "F_Sync hash"
    assert first[-1] == ("archive", "I3")


def test_apply_stops_on_a_failed_mutation_and_reports_done_and_not_done():
    plan = ps.Plan(creates=[derived("TCK-1")], archives=[("TCK-3", "r")], archive_item_ids=["I3"])
    fake = Fake(full_project(), fail_on=2)
    done, not_done, error = pc.apply_plan(fake, full_project(), plan)
    assert len(done) == 2 and error and "boom" in error and any("archive TCK-3" in d for d in not_done)
    assert ("archive", "I3") not in fake.calls


def test_apply_refuses_when_a_field_is_missing_before_any_write():
    plan = ps.Plan(creates=[derived()])
    fake = Fake(project(skip=("Host",)))
    with pytest.raises(pc.ClientRefused, match="run --init"):
        pc.apply_plan(fake, fake.proj, plan)
    assert fake.calls == []


def test_two_noid_items_are_archived_by_their_own_ids():
    plan = ps.Plan(archives=[("same", "no Ticket ID")] * 2, archive_item_ids=["I1", "I2"])
    fake = Fake(full_project())
    pc.apply_plan(fake, fake.proj, plan)
    assert fake.calls == [("archive", "I1"), ("archive", "I2")]


# ---- the client: token handling
def token_file(tmp_path, mode=0o600, text=SENTINEL):
    p = tmp_path / "token"
    p.write_text(text + "\n")
    p.chmod(mode)
    return p


def client_with(tmp_path, reply, **kw):
    seen = []

    def runner(args, env, stdin):
        seen.append((args, env, stdin))
        return reply(args, env, stdin)

    return pc.ProjectClient("o", 1, token_file(tmp_path, **kw), runner), seen


def ok(data):
    return lambda a, e, s: SimpleNamespace(returncode=0, stdout=json.dumps({"data": data}), stderr="")


def test_the_token_is_only_in_the_child_env_never_in_argv_or_stdin_or_the_parent_env(tmp_path, monkeypatch):
    monkeypatch.delenv("GH_TOKEN", raising=False)
    c, seen = client_with(tmp_path, ok({"x": 1}))
    c.graphql("query{x}")
    args, env, stdin = seen[0]
    assert env["GH_TOKEN"] == SENTINEL and SENTINEL not in " ".join(args) and SENTINEL not in stdin
    assert args == ["gh", "api", "graphql", "--input", "-"] and "GH_TOKEN" not in os.environ


def test_a_stray_parent_token_is_replaced_not_forwarded(tmp_path, monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "PARENT")
    c, seen = client_with(tmp_path, ok({}))
    c.graphql("query{x}")
    assert seen[0][1]["GH_TOKEN"] == SENTINEL and "GITHUB_TOKEN" not in seen[0][1]


def test_the_token_never_appears_in_an_error_message(tmp_path, capsys):
    bad = lambda a, e, s: SimpleNamespace(returncode=1, stdout="", stderr=f"denied for {e['GH_TOKEN']}")
    c, _ = client_with(tmp_path, bad)
    with pytest.raises(pc.ProjectError) as exc:
        c.graphql("query{x}")
    assert SENTINEL not in str(exc.value) and "***" in str(exc.value)
    err = lambda a, e, s: SimpleNamespace(returncode=0, stdout=json.dumps({"errors": [{"message": f"x {e['GH_TOKEN']}"}]}), stderr="")
    c, _ = client_with(tmp_path, err)
    with pytest.raises(pc.ProjectError) as exc:
        c.graphql("query{x}")
    out = capsys.readouterr()
    assert SENTINEL not in str(exc.value) + out.out + out.err


def test_a_missing_empty_or_loose_token_file_is_refused_without_calling_gh(tmp_path):
    called = []
    run = lambda a, e, s: called.append(1)
    for path in (tmp_path / "none", token_file(tmp_path, mode=0o644), token_file(tmp_path, text="")):
        with pytest.raises(pc.ClientRefused) as exc:
            pc.ProjectClient("o", 1, path, run).graphql("q")
        assert SENTINEL not in str(exc.value)
    assert not called


# ---- the client: reads
def test_the_live_read_paginates_skips_archived_items_and_maps_values(tmp_path):
    def node(i, archived=False, more=False):
        return {"id": f"I{i}", "isArchived": archived, "content": {"id": f"D{i}", "title": f"T{i}"},
                "fieldValues": {"pageInfo": {"hasNextPage": more},
                                "nodes": [{"text": f"TCK-{i}", "field": {"name": "Ticket ID"}}, {"name": "Done", "field": {"name": "Status"}}, {}]}}
    pages = [{"organization": {"projectV2": {"items": {"pageInfo": {"hasNextPage": True, "endCursor": "c"}, "nodes": [node(1), node(2, True)]}}}},
             {"organization": {"projectV2": {"items": {"pageInfo": {"hasNextPage": False, "endCursor": None}, "nodes": [node(3)]}}}}]
    it = iter(pages)
    c, _ = client_with(tmp_path, lambda a, e, s: SimpleNamespace(returncode=0, stdout=json.dumps({"data": next(it)}), stderr=""))
    items = c.list_items()
    assert [i["_item_id"] for i in items] == ["I1", "I3"] and items[0]["Ticket ID"] == "TCK-1" and items[0]["Status"] == "Done"
    assert items[0]["_draft_id"] == "D1" and items[0]["Title"] == "T1"
    it = iter([{"organization": {"projectV2": {"items": {"pageInfo": {"hasNextPage": False}, "nodes": [node(9, more=True)]}}}}])
    with pytest.raises(pc.ProjectError, match="more than"):
        c.list_items()


# ---- guards
def test_the_read_guard_still_refuses_graphql():
    with pytest.raises(ps.WriteRefused):
        ps._guard(["gh", "api", "graphql", "-f", "query=x"])


def test_project_sync_never_runs_graphql_itself_and_the_client_has_no_delete_mutation():
    root = Path(__file__).resolve().parents[2] / "tools" / "sessions"
    assert '"--input"' not in (root / "project_sync.py").read_text(encoding="utf-8")  # the graphql subprocess call lives only in the client
    client_src = (root / "project_client.py").read_text(encoding="utf-8").lower()
    assert "deleteprojectv2" not in client_src and "def delete" not in client_src


def test_host_facts_is_a_text_field_init_creates_by_name_and_apply_writes_before_source():
    assert "Host facts" in pc.TEXT_FIELDS and pc.VALUE_ORDER[-1] == "Host facts"
    fake = Fake(project(status_options=STATUSES, skip=("Host facts",)))
    lines, code = pc.init_fields(fake, STATUSES, layers=LAYERS)
    assert code == 0 and ("create_text", "Host facts") in fake.calls and "created: Host facts" in lines
    again = Fake(project(status_options=STATUSES))
    pc.init_fields(again, STATUSES, layers=LAYERS)
    assert again.calls == []
