"""The one GraphQL path of `tools/sessions/project_sync.py` (TCK-20261114-PROJECT-SYNC-INIT-AND-APPLY, P1b).

`project_sync.py` keeps its read-only `_guard` and never runs `gh api graphql`. Every GraphQL call (query or mutation) lives here:

* the query and variables go to `gh api graphql --input -` on **stdin**, so nothing secret or large is in argv;
* the token is read from the owner's file (`TOKEN_PATH`, mode exactly 600) on each call and set as `GH_TOKEN` in that one child
  process's env only. It is never stored, printed, logged, exported or put in an exception message (`_redact`);
* there is no delete mutation in this module: items are archived, fields are created or updated, never deleted.
"""

from __future__ import annotations

import json
import os
import stat
import subprocess
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

TOKEN_PATH = Path.home() / ".config" / "rpg-project-sync" / "token"
TOKEN_ENV_NAMES = ("GH_TOKEN", "GITHUB_TOKEN", "GH_ENTERPRISE_TOKEN")
FIELD_VALUES_PAGE = 25

GhRunner = Callable[[list[str], dict, str], "subprocess.CompletedProcess[str]"]


class ClientRefused(Exception):
    """The client will not run (missing or unsafe token file, unconfigured Project). The message is plain and never holds a token."""


class ProjectError(Exception):
    """GitHub or gh refused or failed a call. The message is redacted."""


def _redact(text: str, token: str) -> str:
    return text.replace(token, "***") if token else text


def read_token(path: Path = TOKEN_PATH) -> str:
    try:
        mode = stat.S_IMODE(path.stat().st_mode)
    except OSError:
        raise ClientRefused(f"token file {path} is missing or unreadable") from None
    if mode != 0o600:
        raise ClientRefused(f"token file {path} must have mode 600 (it has {mode:o})")
    try:
        token = path.read_text(encoding="utf-8").strip()
    except OSError:
        raise ClientRefused(f"token file {path} is missing or unreadable") from None
    if not token:
        raise ClientRefused(f"token file {path} is empty")
    return token


def _run_gh(args: list[str], env: dict, stdin: str) -> "subprocess.CompletedProcess[str]":
    try:
        return subprocess.run(args, input=stdin, env=env, capture_output=True, text=True, timeout=90, check=False)
    except (OSError, subprocess.SubprocessError) as exc:
        return subprocess.CompletedProcess(args, 1, "", str(exc))


@dataclass(frozen=True)
class ProjectField:
    id: str
    name: str
    type: str  # GraphQL dataType: TEXT, SINGLE_SELECT, TITLE, ...
    options: tuple[tuple[str, str], ...] = ()  # (option name, option id), in display order
    colors: tuple[tuple[str, str], ...] = ()  # (option name, color), read so a kept option keeps its colour

    def option_id(self, name: str) -> str | None:
        return dict(self.options).get(name)


@dataclass(frozen=True)
class Project:
    id: str
    fields: dict[str, ProjectField] = field(default_factory=dict)


_PROJECT_Q = """query($owner:String!,$number:Int!){organization(login:$owner){projectV2(number:$number){id
fields(first:50){nodes{__typename ... on ProjectV2FieldCommon{id name dataType} ... on ProjectV2SingleSelectField{options{id name color}}}}}}}"""

_ITEMS_Q = """query($owner:String!,$number:Int!,$after:String){organization(login:$owner){projectV2(number:$number){
items(first:100,after:$after){pageInfo{hasNextPage endCursor} nodes{id isArchived content{__typename ... on DraftIssue{id title}}
fieldValues(first:%d){pageInfo{hasNextPage} nodes{__typename
... on ProjectV2ItemFieldTextValue{text field{... on ProjectV2FieldCommon{name}}}
... on ProjectV2ItemFieldSingleSelectValue{name field{... on ProjectV2FieldCommon{name}}}}}}}}}}""" % FIELD_VALUES_PAGE


class ProjectClient:
    def __init__(self, owner: str, number: int, token_path: Path = TOKEN_PATH, runner: GhRunner = _run_gh) -> None:
        self.owner, self.number, self.token_path, self._runner = owner, number, token_path, runner

    # ---- the single GraphQL call
    def graphql(self, query: str, variables: dict | None = None) -> dict:
        token = read_token(self.token_path)
        env = {k: v for k, v in os.environ.items() if k not in TOKEN_ENV_NAMES}
        env["GH_TOKEN"] = token
        body = json.dumps({"query": query, "variables": variables or {}})
        done = self._runner(["gh", "api", "graphql", "--input", "-"], env, body)
        out = (done.stdout or "").strip()
        try:
            data = json.loads(out) if out else {}
        except ValueError:
            data = {}
        if done.returncode != 0 or data.get("errors") or "data" not in data:
            detail = json.dumps(data.get("errors")) if data.get("errors") else (done.stderr or out or "no response")
            raise ProjectError(_redact(f"GitHub GraphQL call failed: {detail}", token)[:2000])
        return data["data"]

    def _mutate(self, name: str, input_type: str, payload: dict, selection: str = "clientMutationId") -> dict:
        query = f"mutation($input:{input_type}!){{{name}(input:$input){{{selection}}}}}"
        return self.graphql(query, {"input": payload})[name]

    # ---- reads
    def load_project(self) -> Project:
        data = self.graphql(_PROJECT_Q, {"owner": self.owner, "number": self.number})
        proj = (data.get("organization") or {}).get("projectV2")
        if not proj:
            raise ClientRefused(f"Project {self.owner}/{self.number} was not found (or the token cannot see it)")
        fields = {}
        for node in proj["fields"]["nodes"]:
            if node and node.get("name"):
                opts = tuple((o["name"], o["id"]) for o in node.get("options") or [])
                cols = tuple((o["name"], o.get("color") or "GRAY") for o in node.get("options") or [])
                fields[node["name"]] = ProjectField(node["id"], node["name"], node.get("dataType", ""), opts, cols)
        return Project(proj["id"], fields)

    def list_items(self) -> list[dict]:
        """Every non-archived item as {field name: value} plus `_item_id` and `_draft_id`. Fails loudly if field values are cut off."""
        items, after = [], None
        while True:
            data = self.graphql(_ITEMS_Q, {"owner": self.owner, "number": self.number, "after": after})
            page = ((data.get("organization") or {}).get("projectV2") or {}).get("items")
            if page is None:
                raise ClientRefused(f"Project {self.owner}/{self.number} was not found (or the token cannot see it)")
            for node in page["nodes"]:
                if node.get("isArchived"):
                    continue
                if node["fieldValues"]["pageInfo"]["hasNextPage"]:
                    raise ProjectError(f"item {node['id']} has more than {FIELD_VALUES_PAGE} field values: the read would drop fields")
                content = node.get("content") or {}
                item = {"Title": content.get("title", ""), "_item_id": node["id"], "_draft_id": content.get("id", "")}
                for val in node["fieldValues"]["nodes"]:
                    name = ((val or {}).get("field") or {}).get("name")
                    if name:
                        item[name] = val.get("text", val.get("name", ""))
                items.append(item)
            if not page["pageInfo"]["hasNextPage"]:
                return items
            after = page["pageInfo"]["endCursor"]

    # ---- writes (no delete anywhere)
    def create_text_field(self, project_id: str, name: str) -> None:
        self._mutate("createProjectV2Field", "CreateProjectV2FieldInput", {"projectId": project_id, "dataType": "TEXT", "name": name})

    def create_select_field(self, project_id: str, name: str, options: list[tuple[str, str]]) -> None:
        opts = [{"name": n, "color": c, "description": ""} for n, c in options]
        self._mutate("createProjectV2Field", "CreateProjectV2FieldInput",
                     {"projectId": project_id, "dataType": "SINGLE_SELECT", "name": name, "singleSelectOptions": opts})

    def set_select_options(self, field_id: str, options: list[tuple[str, str, str | None]]) -> None:
        """`options` is (name, colour, id or None), in the order wanted. An id keeps that option's identity, so items keep their value."""
        opts = [({"id": oid} if oid else {}) | {"name": n, "color": c, "description": ""} for n, c, oid in options]
        self._mutate("updateProjectV2Field", "UpdateProjectV2FieldInput", {"fieldId": field_id, "singleSelectOptions": opts})

    def add_draft(self, project_id: str, title: str, body: str) -> tuple[str, str]:
        res = self._mutate("addProjectV2DraftIssue", "AddProjectV2DraftIssueInput", {"projectId": project_id, "title": title, "body": body},
                           "projectItem{id content{... on DraftIssue{id}}}")
        item = res["projectItem"]
        return item["id"], (item.get("content") or {}).get("id", "")

    def update_draft(self, draft_id: str, title: str, body: str) -> None:
        self._mutate("updateProjectV2DraftIssue", "UpdateProjectV2DraftIssueInput", {"draftIssueId": draft_id, "title": title, "body": body})

    def set_text(self, project_id: str, item_id: str, field_id: str, text: str) -> None:
        self._mutate("updateProjectV2ItemFieldValue", "UpdateProjectV2ItemFieldValueInput",
                     {"projectId": project_id, "itemId": item_id, "fieldId": field_id, "value": {"text": text}})

    def set_option(self, project_id: str, item_id: str, field_id: str, option_id: str) -> None:
        self._mutate("updateProjectV2ItemFieldValue", "UpdateProjectV2ItemFieldValueInput",
                     {"projectId": project_id, "itemId": item_id, "fieldId": field_id, "value": {"singleSelectOptionId": option_id}})

    def clear_value(self, project_id: str, item_id: str, field_id: str) -> None:
        self._mutate("clearProjectV2ItemFieldValue", "ClearProjectV2ItemFieldValueInput",
                     {"projectId": project_id, "itemId": item_id, "fieldId": field_id})

    def archive(self, project_id: str, item_id: str) -> None:
        self._mutate("archiveProjectV2Item", "ArchiveProjectV2ItemInput", {"projectId": project_id, "itemId": item_id})


# ---------------------------------------------------------------- --init

TEXT_FIELDS = ("Ticket ID", "Domain", "Seat", "Host", "Branch", "PR", "Source", "Sync hash", "Epic", "Tags", "Host facts")
TIER_OPTIONS = [("hotfix", "ORANGE"), ("standard", "BLUE"), ("epic", "PURPLE")]
PRIORITY_OPTIONS = [("P0", "RED"), ("P1", "ORANGE"), ("P2", "YELLOW"), ("P3", "GRAY")]
STATUS_COLORS = {"To do": "GRAY", "In progress": "BLUE", "Stale": "ORANGE", "In review": "PURPLE", "Blocked": "RED", "Done": "GREEN"}


def merge_options(field: ProjectField, wanted: list[tuple[str, str]]) -> list[tuple[str, str, str | None]]:
    """Append-only: every existing option keeps its id, colour and place; each wanted name that is missing is appended. Never drops one."""
    cols = dict(field.colors)
    kept = [(n, cols.get(n, "GRAY"), oid) for n, oid in field.options]
    have = {n for n, _ in field.options}
    return kept + [(n, c, None) for n, c in wanted if n not in have]


def replace_options(field: ProjectField, wanted: list[tuple[str, str]]) -> list[tuple[str, str, str | None]]:
    """Exactly `wanted`, in its order. A name that already exists carries its id (so its items keep their value); one not wanted is left out."""
    ids = dict(field.options)
    return [(n, c, ids.get(n)) for n, c in wanted]


def init_fields(client, statuses: tuple[str, ...], replace_status_options: bool = False,
                layers: tuple[str, ...] = ()) -> tuple[list[str], int]:
    """Create the missing fields by name; never delete or rename. Returns (report lines, exit code). All checks come before any write."""
    project = client.load_project()
    lines: list[str] = []
    problems = []
    selects = {"Tier": TIER_OPTIONS, "Priority": PRIORITY_OPTIONS}
    if layers:
        selects["Layer"] = [(n, "GRAY") for n in layers]
    for name in TEXT_FIELDS:
        f = project.fields.get(name)
        if f is not None and f.type != "TEXT":
            problems.append(f"field '{name}' exists as {f.type}, wanted TEXT")
    for name in selects:
        f = project.fields.get(name)
        if f is not None and f.type != "SINGLE_SELECT":
            problems.append(f"field '{name}' exists as {f.type}, wanted SINGLE_SELECT")
    status = project.fields.get("Status")
    if status is None or status.type != "SINGLE_SELECT":
        problems.append("the built-in 'Status' single-select field is " + ("missing" if status is None else f"a {status.type}"))
    if problems:
        return [f"init refused (nothing written): {p}" for p in problems], 1
    wanted_status = [(n, STATUS_COLORS.get(n, "GRAY")) for n in statuses]
    status_names = [n for n, _ in status.options]
    status_update, status_note = None, ""
    if replace_status_options or (status_names != list(statuses) and not client.list_items()):
        if status_names != list(statuses):
            status_update = replace_options(status, wanted_status)  # exact STATUSES; only options left out lose their items' value
    else:
        merged = merge_options(status, wanted_status)
        if len(merged) != len(status_names):
            status_update = merged
        extra = [n for n in status_names if n not in statuses]
        if extra:
            status_note = f"kept, not in STATUSES: {', '.join(extra)}"
    for name in TEXT_FIELDS:
        if name in project.fields:
            lines.append(f"left alone: {name}")
        else:
            client.create_text_field(project.id, name)
            lines.append(f"created: {name}")
    for name, wanted in selects.items():
        f = project.fields.get(name)
        if f is None:
            client.create_select_field(project.id, name, wanted)
            lines.append(f"created: {name}")
            continue
        merged = merge_options(f, wanted)
        if len(merged) > len(f.options):
            client.set_select_options(f.id, merged)
            lines.append(f"updated: {name} options + {', '.join(n for n, _, i in merged if i is None)}")
        else:
            lines.append(f"left alone: {name}")
    if status_update is not None:
        client.set_select_options(status.id, status_update)
        lines.append(f"updated: Status options -> {', '.join(n for n, _, _ in status_update)}")
    else:
        lines.append("left alone: Status")
    if status_note:
        lines.append(status_note)
    lines.append("left alone: Title (built-in)")
    return lines, 0


# ---------------------------------------------------------------- --apply

VALUE_ORDER = ("Ticket ID", "Status", "Domain", "Seat", "Host", "Branch", "PR", "Tier", "Layer", "Priority", "Epic", "Tags", "Host facts")  # Source, then Sync hash, are always last
SELECT_FIELDS = ("Status", "Tier", "Layer", "Priority")


def apply_plan(client, project: Project, plan, body_of: Callable[[dict], str] | None = None) -> tuple[list[str], list[str], str | None]:
    """Carry out plan.creates / plan.updates / plan.archives. Returns (done, not_done, error). A failing mutation stops the run."""
    needed = list(VALUE_ORDER) + ["Source", "Sync hash"]
    missing = [n for n in needed if n not in project.fields]
    if missing:
        raise ClientRefused(f"the Project has no field(s) {', '.join(missing)}: run --init first")

    def put(get_id: Callable[[], str], name: str, value: str, clear_if_empty: bool) -> Callable[[], None] | None:
        f = project.fields[name]
        if value == "":
            return (lambda: client.clear_value(project.id, get_id(), f.id)) if clear_if_empty else None
        if name in SELECT_FIELDS:
            oid = f.option_id(value)
            if oid is None:
                raise ClientRefused(f"field '{name}' has no option '{value}': run --init")
            return lambda: client.set_option(project.id, get_id(), f.id, oid)
        return lambda: client.set_text(project.id, get_id(), f.id, value)

    steps: list[tuple[str, Callable[[], None]]] = []
    for derived in plan.creates:
        holder: dict = {}

        def add(d=derived, h=holder):
            h["item"], h["draft"] = client.add_draft(project.id, d["Title"], d["Body"])
        steps.append((f"create {derived['Ticket ID']}: draft item", add))
        for name in list(VALUE_ORDER) + ["Source", "Sync hash"]:  # Ticket ID first, Sync hash last
            call = put(lambda h=holder: h["item"], name, derived.get(name, ""), False)
            if call is not None:
                steps.append((f"create {derived['Ticket ID']}: set {name}", call))
    for derived, changed in plan.updates:
        item_id = derived["_item_id"]
        if "Title" in changed:
            steps.append((f"update {derived['Ticket ID']}: title",
                          (lambda d=derived: client.update_draft(d["_draft_id"], d["Title"], d["Body"]))))
        names = [n for n in VALUE_ORDER if n in changed] + ["Source", "Sync hash"]
        for name in names:
            call = put(lambda i=item_id: i, name, derived.get(name, ""), True)
            if call is not None:
                steps.append((f"update {derived['Ticket ID']}: set {name}", call))
    for (ident, reason), item_id in zip(plan.archives, plan.archive_item_ids):
        if item_id:
            steps.append((f"archive {ident} ({reason})", (lambda i=item_id: client.archive(project.id, i))))
    done: list[str] = []
    for i, (desc, call) in enumerate(steps):
        try:
            call()
        except (ProjectError, ClientRefused) as exc:
            return done, [d for d, _ in steps[i:]], f"{desc}: {exc}"
        done.append(desc)
    return done, [], None
