#!/usr/bin/env python3
"""Derive the GitHub Project items for ticket state, dry run only (TCK-20261112-PROJECT-SYNC-DRY-RUN, P0 of
TCK-20261112-EPIC-GITHUB-PROJECT-TICKET-VIEW).

The Project is a generated, read-only VIEW of ticket state: the ticket files stay authoritative. This tool reads ticket files on
origin/main (no fetch), the worktrees and seats of this host (the builders in `tools/sessions/status.py`), each worktree's ticket
changes against the merge base (read-only), and open PRs, then prints the create / update / archive plan. It writes nothing to
GitHub and nothing to the repo; `--apply` and `--init` are P1 and are refused. Every subprocess goes through `_guard`, which only
lets read verbs through.

Status, first match wins (design section 3): Done -> In review -> Blocked -> In progress (or Stale) -> To do. Stale replaces In progress
only: every branch working the ticket is older than `stale_branch_days` (newest commit or index change, status.py `_activity`; approximate). A `todos/` copy on a branch or in a
PR is filing, not progress, and never moves a ticket past To do.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import socket
import subprocess
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path

import yaml

if __package__ in (None, ""):  # run as `python3 tools/sessions/project_sync.py`: put the repo root on sys.path
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.agent_working_paths import TICKETS
from tools.sessions import state as st
from tools.sessions.launch import _worktree_entries as worktree_entries
from tools.sessions.launch import main_checkout
from tools.sessions.roster import REPO_ROOT, load_roster

# Deliberate reuse of status.py's private `_worktree_for` (seat -> physical worktree): same package, and renaming it would only
# churn status.py's unchanged tests (designer review of plan.md, 2026-11-12).
from tools.sessions.status import _worktree_for, inspect_worktree, seat_infos  # noqa: F401

CONFIG_REL = Path("registries") / "session_project.yaml"
DEFAULTS = {
    "project": {"owner": "PLACEHOLDER", "number": 0},
    "pilot_lanes": ["rpg"],
    "pilot_start": "2026-11-12",
    "done_window_days": 14,
    "stale_host_hours": 24,
    "stale_branch_days": 14,
    "host_names": {},
}
PR_LIMIT = 300  # the value of ticket_queue.PR_LIMIT: gh's own default is 30
FOLDERS = ("todos", "inprogress", "done")
PROGRESS_FOLDERS = ("inprogress", "done")  # only these count as progress; todos/ on a branch or PR is filing
HASH_FIELDS_V1 = ("Title", "Ticket ID", "Status", "Domain", "Seat", "Host", "Branch", "PR", "Tier")
HASH_FIELDS = HASH_FIELDS_V1 + ("Layer", "Priority", "Epic", "Tags")  # the current version (v2)
HASH_VERSIONS = {"v1": HASH_FIELDS_V1, "v2": HASH_FIELDS}  # a stored hash is "v2:<sha>"; an unprefixed value is v1
CURRENT_HASH_VERSION = "v2"
PRIORITIES = ("P0", "P1", "P2", "P3")
STATUSES = ("To do", "In progress", "Stale", "In review", "Blocked", "Done")
FILING_SUFFIX = "[filing]"
BODY = "Generated from {path} by tools/sessions/project_sync.py — edits are overwritten."
_TICKET_RE = re.compile(r"(TCK-[A-Z0-9][A-Z0-9-]*)\.md$")
READ_GIT = {"ls-tree", "show", "merge-base", "diff", "status", "log", "rev-parse", "worktree"}

Runner = Callable[[list[str], Path | None], "subprocess.CompletedProcess[str]"]


class WriteRefused(Exception):
    """A command that could write was about to run; the dry run never does."""


GH_API_FLAGS = ("--paginate",)  # a flag with no value
GH_API_VALUE_FLAGS = ("-q", "--jq", "-H", "--header")  # a flag followed by one value


def _gh_api_is_read(rest: list[str]) -> bool:
    """Allowlist: exactly one `repos/...` endpoint (never `graphql`: a POST that can carry a mutation), and every other
    dash token is in a small set. Any joined spelling (`-XPOST`, `--method=POST`, `-fk=v`, ...) is not in it, so it is refused."""
    endpoints, i = [], 0
    while i < len(rest):
        arg = rest[i]
        if arg in GH_API_FLAGS:
            i += 1
        elif arg in GH_API_VALUE_FLAGS:
            if i + 1 >= len(rest):
                return False
            i += 2
        elif arg.startswith("-"):
            return False
        else:
            endpoints.append(arg)
            i += 1
    return len(endpoints) == 1 and endpoints[0].startswith("repos/")


def _guard(args: list[str]) -> None:
    """Only read verbs: git ls-tree/show/merge-base/diff/status/log/rev-parse/worktree-list; gh `pr list` and an allowlisted `api` read."""
    if not args:
        raise WriteRefused("empty command")
    tool, rest = args[0], [a for a in args[1:] if a != "--no-optional-locks"]
    if tool == "git":
        verb = rest[0] if rest else ""
        if verb not in READ_GIT or (verb == "worktree" and rest[1:2] != ["list"]):
            raise WriteRefused(f"git {verb}")
        return
    if tool == "gh":
        if rest[:2] == ["pr", "list"]:
            return
        if rest[:1] == ["api"] and _gh_api_is_read(rest[1:]):
            return
        raise WriteRefused("gh " + " ".join(rest[:2]))
    raise WriteRefused(tool)


def run_command(args: list[str], cwd: Path | None = None) -> "subprocess.CompletedProcess[str]":
    _guard(args)
    try:
        return subprocess.run(args, cwd=None if cwd is None else str(cwd), capture_output=True, text=True, timeout=60, check=False)
    except (OSError, subprocess.SubprocessError) as exc:
        return subprocess.CompletedProcess(args, 1, "", str(exc))


# ---------------------------------------------------------------- data


@dataclass(frozen=True)
class TicketCopy:
    id: str
    folder: str
    path: str
    title: str = ""
    tier: str = ""
    blocked: bool = False
    date: str = ""
    layer: str = ""
    priority: str = ""
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class BranchFact:
    host: str
    branch: str
    worktree: str
    seat: str
    domain: str
    copies: tuple[TicketCopy, ...]
    last_activity: float = 0.0  # epoch seconds, status.py `_activity`; 0.0 = unknown, never stale


@dataclass(frozen=True)
class PrFact:
    number: int
    url: str
    paths: frozenset[str]  # ticket file paths the PR adds or changes


@dataclass
class Plan:
    creates: list[dict] = field(default_factory=list)
    updates: list[tuple[dict, list[str]]] = field(default_factory=list)
    archives: list[tuple[str, str]] = field(default_factory=list)  # (ticket id or item title, reason)
    archive_item_ids: list[str] = field(default_factory=list)  # parallel to `archives`: the live item's id ("" when read from --items)
    hand_edits: list[str] = field(default_factory=list)
    findings: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


# ---------------------------------------------------------------- ticket files


def ticket_id_of(path: str) -> str | None:
    m = _TICKET_RE.search(path)
    return m.group(1) if m else None


def folder_of(path: str) -> str | None:
    prefix = TICKETS.as_posix() + "/"
    if not path.startswith(prefix):
        return None
    head = path[len(prefix):].split("/", 1)[0]
    return head if head in FOLDERS else None


def parse_copy(path: str, text: str) -> TicketCopy:
    def section(name: str) -> str:
        m = re.search(rf"^## {name}\s*\n+([^\n#][^\n]*)", text, re.M)
        return m.group(1).strip() if m else ""

    fm = re.search(r"^date:\s*(\S+)", text, re.M)
    layer = re.search(r"^layer:\s*(\S+)", text, re.M)
    tags = re.search(r"^tags:\s*\[([^\]]*)\]", text, re.M)
    return TicketCopy(
        id=ticket_id_of(path) or "", folder=folder_of(path) or "", path=path, title=section("Title"), tier=section("Tier").lower(),
        blocked=section("Status").upper() == "BLOCKED", date=fm.group(1) if fm else "",
        layer=layer.group(1) if layer else "", priority=section("Priority").upper(),
        tags=tuple(x.strip().strip("'\"") for x in tags.group(1).split(",") if x.strip()) if tags else (),
    )


def read_main_index(root: Path, run: Runner = run_command, ref: str = "origin/main") -> dict[str, list[tuple[str, str]]]:
    """ticket id -> [(folder, path)] on `ref`. Names only: the 3,000+ done files are never opened."""
    out = run(["git", "ls-tree", "-r", "--name-only", ref, "--", TICKETS.as_posix()], root)
    index: dict[str, list[tuple[str, str]]] = {}
    for path in out.stdout.splitlines() if out.returncode == 0 else []:
        tid, folder = ticket_id_of(path), folder_of(path)
        if tid and folder:
            index.setdefault(tid, []).append((folder, path))
    return index


def read_main_copy(root: Path, path: str, run: Runner = run_command, ref: str = "origin/main") -> TicketCopy:
    shown = run(["git", "show", f"{ref}:{path}"], root)
    return parse_copy(path, shown.stdout if shown.returncode == 0 else "")


def origin_info(root: Path, run: Runner = run_command, ref: str = "origin/main") -> tuple[str, float | None]:
    sha = run(["git", "rev-parse", ref], root)
    when = run(["git", "log", "-1", "--format=%ct", ref], root)
    stamp = float(when.stdout.strip()) if when.returncode == 0 and when.stdout.strip().isdigit() else None
    return (sha.stdout.strip() if sha.returncode == 0 else "unknown"), stamp


def done_date(root: Path, path: str, run: Runner = run_command, ref: str = "origin/main") -> datetime | None:
    """When the ticket file reached done/ on `ref` (git, not frontmatter: the `date` field is the filing date)."""
    out = run(["git", "log", "-1", "--diff-filter=A", "--format=%cI", ref, "--", path], root)
    text = out.stdout.strip() if out.returncode == 0 else ""
    try:
        return datetime.fromisoformat(text) if text else None
    except ValueError:
        return None


# ---------------------------------------------------------------- worktrees


def attribute(branch: str, seats: list[tuple[str, str]]) -> tuple[str, str]:
    """(Seat, Domain): the seat the launcher recorded (status.py mapping); else `<domain> (seat not recorded)` from the branch prefix,
    a known gap (hand-made batch worktrees have no record); else `unknown`."""
    if seats:
        return "/".join(s for s, _ in seats), seats[0][1]
    prefix = branch.split("-", 1)[0]
    return (f"{prefix} (seat not recorded)", prefix) if "-" in branch else ("unknown", "")


def read_branch_facts(root: Path, host: str, lanes_note: list[str], run: Runner = run_command) -> tuple[list[BranchFact], int]:
    """(branch facts for this host, count of detached worktrees skipped). Read-only: status.py's builders, then per worktree
    `git diff --name-status <merge-base> HEAD` and `git status --porcelain`, both limited to the ticket folders."""
    roster = load_roster(root)
    main = main_checkout(root)
    try:
        state_root = st.state_root(root)
    except st.StateError:
        state_root = root / ".git" / "session-roles-unavailable"
    infos = [inspect_worktree(e, main, lambda b, c: "none", lambda p: 0) for e in worktree_entries(root) if e.get("worktree")]
    seat_of: dict[Path, list[tuple[str, str]]] = {}
    for role in roster.roles:
        wt = _worktree_for(role, infos, main, state_root)
        if wt is not None:
            seat_of.setdefault(wt.path.resolve(), []).append((role.role, role.domain))
    facts, detached = [], 0
    for info in infos:
        if info.prunable or info.is_main and info.branch in (None, "main"):
            continue
        copies = _worktree_ticket_copies(info.path, run)
        if info.branch is None:
            detached += 1
            if copies:
                lanes_note.append(f"unattributed: detached worktree {info.path} changes {', '.join(sorted(c.id for c in copies))}")
            continue
        if not copies:
            continue
        seat, domain = attribute(info.branch, seat_of.get(info.path.resolve(), []))
        facts.append(BranchFact(host, info.branch, str(info.path), seat, domain, tuple(copies), info.last_activity))
    return facts, detached


def _worktree_ticket_copies(wt: Path, run: Runner) -> list[TicketCopy]:
    folder = TICKETS.as_posix()
    base = run(["git", "--no-optional-locks", "merge-base", "origin/main", "HEAD"], wt)
    changed: set[str] = set()
    if base.returncode == 0 and base.stdout.strip():
        diff = run(["git", "--no-optional-locks", "diff", "--name-status", base.stdout.strip(), "HEAD", "--", folder], wt)
        for line in diff.stdout.splitlines() if diff.returncode == 0 else []:
            parts = line.split("\t")
            if parts and parts[0][:1] in ("A", "M", "R", "C") and len(parts) >= 2:
                changed.add(parts[-1])
    # -z: NUL-separated entries, no quoting and no line splitting, so a leading-space ` M <path>` (unstaged-only) is read exactly
    status = run(["git", "--no-optional-locks", "status", "--porcelain", "-z", "--untracked-files=all", "--", folder], wt)
    on_disk: set[str] = set()
    entries = status.stdout.split("\0") if status.returncode == 0 else []
    i = 0
    while i < len(entries):
        entry = entries[i]
        i += 1
        if len(entry) < 4:
            continue
        code, path = entry[:2], entry[3:]
        if code[0] in "RC":
            i += 1  # the next entry is the rename or copy source
        if "D" not in code:
            changed.add(path)
            on_disk.add(path)
    out = []
    for path in sorted(changed):
        if not (ticket_id_of(path) and folder_of(path)):
            continue
        if path in on_disk and (wt / path).is_file():
            text = (wt / path).read_text(encoding="utf-8", errors="replace")
        else:
            shown = run(["git", "show", f"HEAD:{path}"], wt)
            text = shown.stdout if shown.returncode == 0 else ""
        out.append(parse_copy(path, text))
    return out


# ---------------------------------------------------------------- pull requests


class PrList(list):
    """The open PRs; `complete` is False when a per-PR file list could not be read, so rule 2 (In review) may be wrong for some ticket."""

    complete = True


def read_open_prs(root: Path, notes: list[str], run: Runner = run_command) -> list[PrFact] | None:
    """Open PRs and the ticket files each adds or changes; GETs only. None when gh cannot answer (rule 2 is then skipped)."""
    listed = run(["gh", "pr", "list", "--state", "open", "--limit", str(PR_LIMIT), "--json", "number,url"], root)
    if listed.returncode != 0:
        notes.append("open PRs unknown (gh failed): rule 2 (In review) is skipped this run")
        return None
    try:
        prs = json.loads(listed.stdout or "[]")
    except ValueError:
        notes.append("open PRs unknown (gh answered badly): rule 2 (In review) is skipped this run")
        return None
    if len(prs) >= PR_LIMIT:
        notes.append(f"gh returned {PR_LIMIT} open PRs, the limit: some PRs may be missing")
    facts = PrList()
    for pr in prs:
        files = run(["gh", "api", "--paginate", f"repos/{{owner}}/{{repo}}/pulls/{pr['number']}/files", "--jq", ".[].filename"], root)
        if files.returncode != 0:
            facts.complete = False
            notes.append(f"files of PR #{pr['number']} unknown (gh failed): its tickets may show the wrong status this run")
        names = files.stdout.split() if files.returncode == 0 else []
        facts.append(PrFact(int(pr["number"]), pr["url"], frozenset(n for n in names if ticket_id_of(n) and folder_of(n))))
    return facts


# ---------------------------------------------------------------- derivation (pure)


def sync_hash(fields: dict, version: str = CURRENT_HASH_VERSION) -> str:
    """sha256 over the fields of that version. v1 is the bare digest (P1b stored it); later versions are `<version>:<digest>`."""
    blob = json.dumps([[k, fields.get(k, "")] for k in HASH_VERSIONS[version]], ensure_ascii=False)
    digest = hashlib.sha256(blob.encode("utf-8")).hexdigest()
    return digest if version == "v1" else f"{version}:{digest}"


def hash_version(stored: str) -> str:
    prefix = stored.split(":", 1)[0] if ":" in stored else "v1"
    return prefix if prefix in HASH_VERSIONS else CURRENT_HASH_VERSION


def _split(value: str) -> list[str]:
    return [p.strip() for p in (value or "").split(",") if p.strip()]


def merge_host_entries(current: str, mine: list[str], tag: str) -> str:
    """Replace only this host's entries (`tag` is `host:` for Branch, the bare host name for Host), keep the other hosts'."""
    kept = [e for e in _split(current) if not (e.startswith(tag) if tag.endswith(":") else e == tag)]
    return ", ".join(sorted(set(kept) | set(mine)))


def derive_status(tid: str, main: list[TicketCopy], branches: list[BranchFact], prs: list[PrFact] | None,
                  other_host_branches: list[str], stale_before: float | None = None) -> tuple[str, list[str], list[str]]:
    """(status, PR urls, findings). First match wins; see the module docstring."""
    findings = []
    folders = {c.folder for c in main}
    if len(folders) > 1:
        findings.append(f"{tid}: in two folders on origin/main ({', '.join(sorted(folders))}); the higher status is used")
    if "done" in folders:
        return "Done", [], findings
    review = [pr for pr in prs or [] if any(ticket_id_of(p) == tid and folder_of(p) in PROGRESS_FOLDERS for p in pr.paths)]
    if review:
        return "In review", [pr.url for pr in review], findings
    branch_copies = [c for b in branches for c in b.copies if c.id == tid]
    if any(c.blocked for c in branch_copies) or (not branch_copies and any(c.blocked for c in main)):
        return "Blocked", [], findings
    progressing = any(c.folder in PROGRESS_FOLDERS for c in branch_copies) or any(not e.endswith(FILING_SUFFIX) for e in other_host_branches)
    if progressing:
        # Stale replaces In progress only. Filing branches and a fresh other-host entry keep it In progress.
        working = [b for b in branches if any(c.id == tid and c.folder in PROGRESS_FOLDERS for c in b.copies)]
        if (stale_before is not None and working and all(0 < b.last_activity < stale_before for b in working)
                and not any(not e.endswith(FILING_SUFFIX) for e in other_host_branches)):
            return "Stale", [], findings
        return "In progress", [], findings
    if "inprogress" in folders and not branch_copies and not other_host_branches:
        findings.append(f"{tid}: in inprogress/ on origin/main with no branch seen (orphaned in-progress ticket)")
    return "To do", [], findings


@dataclass
class Extras:
    """Registries and the Epic resolver for Layer / Priority / Epic / Tags. None / empty means "do not validate"."""

    layers: frozenset[str] | None = None
    tag_order: tuple[str, ...] | None = None
    epic_of: Callable[[str, str, str], tuple[str, list[str]]] | None = None  # (ticket id, best copy path, tier) -> (value, notes)


_ID_RE = re.compile(r"TCK-[A-Z0-9][A-Z0-9-]*[A-Z0-9]")


def folder_key(path: str) -> str | None:
    """`todos/<folder>` or `done/<folder>` for a ticket inside an epic folder, else None (a flat ticket)."""
    parts = Path(path).as_posix().split("/")
    base = TICKETS.as_posix().split("/")
    if parts[: len(base)] != base or len(parts) != len(base) + 3 or parts[len(base)] not in ("todos", "done"):
        return None
    return f"{parts[len(base)]}/{parts[len(base) + 1]}"


def sequence_ids(text: str) -> set[str]:
    """Ticket ids of a SEQUENCE.md: those in `## Order` when that section exists, else those anywhere in the file."""
    m = re.search(r"^## Order\b.*?(?=^## |\Z)", text, re.M | re.S)
    return set(_ID_RE.findall(m.group(0) if m else text))


def make_epic_resolver(main_index: dict[str, list[tuple[str, str]]], load_main: Callable[[str], TicketCopy],
                       sequences: dict[str, set[str]]) -> Callable[[str, str, str], tuple[str, list[str]]]:
    """Epic, first match wins: (a) the ticket sits in a todos/ or done/ epic folder; (b) exactly one folder's SEQUENCE.md names it; (c) standalone.
    A folder's epic is its ticket whose `## Tier` is epic (none -> the folder name; several -> the folder name plus a note)."""
    members: dict[str, list[str]] = {}
    for entries in main_index.values():
        for _, path in entries:
            key = folder_key(path)
            if key:
                members.setdefault(key, []).append(path)
    cache: dict[str, tuple[str, list[str]]] = {}

    def folder_epic(key: str) -> tuple[str, list[str]]:
        if key not in cache:
            epics = sorted({ticket_id_of(p) or "" for p in members.get(key, []) if load_main(p).tier == "epic"} - {""})
            name = key.split("/", 1)[1]
            if len(epics) == 1:
                cache[key] = (epics[0], [])
            else:
                cache[key] = (name, [f"folder {key} has {len(epics)} epic tickets: Epic is the folder name"] if len(epics) > 1 else [])
        return cache[key]

    def resolve(tid: str, path: str, tier: str) -> tuple[str, list[str]]:
        key = folder_key(path)
        if key:
            if tier == "epic" and key not in members:
                return tid, []
            return folder_epic(key)
        hits = sorted(k for k, ids in sequences.items() if tid in ids)
        if len(hits) == 1:
            return folder_epic(hits[0])
        if len(hits) > 1:
            return "standalone", [f"{tid} is named in {len(hits)} SEQUENCE.md files ({', '.join(hits)}): Epic is standalone"]
        return "standalone", []

    return resolve


def derive_item(tid: str, main: list[TicketCopy], branches: list[BranchFact], prs: list[PrFact] | None, current: dict | None,
                host: str, source: str, stale_before: float | None = None, extras: Extras | None = None) -> tuple[dict, list[str]]:
    mine = [b for b in branches if any(c.id == tid for c in b.copies)]
    other = [e for e in _split((current or {}).get("Branch", "")) if not e.startswith(f"{host}:")]
    status, pr_urls, findings = derive_status(tid, main, mine, prs, other, stale_before)
    branch_copies = [c for b in mine for c in b.copies if c.id == tid]
    # Seat names who is working on the ticket: only a branch holding it in inprogress/ or done/, never one that merely filed it
    working = [b for b in mine if any(c.id == tid and c.folder in PROGRESS_FOLDERS for c in b.copies)]
    best = (branch_copies or sorted(main, key=lambda c: FOLDERS.index(c.folder), reverse=True))[0] if (branch_copies or main) else None
    entries = [f"{host}:{b.branch}" + ("" if any(c.id == tid and c.folder in PROGRESS_FOLDERS for c in b.copies) else f" {FILING_SUFFIX}")
               for b in mine]
    title = best.title if best else ""
    extras = extras or Extras()
    layer, priority, tags, epic = "", "", "", "standalone"
    if best:
        layer = best.layer
        if layer and extras.layers is not None and layer not in extras.layers:
            findings.append(f"{tid}: layer '{layer}' is not in registries/layer_registry.jsonl: Layer left empty")
            layer = ""
        lead = re.match(r"(P[0-3])(?![0-9A-Za-z])", best.priority)  # "P2 (raised from P3 ...)" is P2: the leading token is the value
        priority = lead.group(1) if lead else best.priority
        if priority and priority not in PRIORITIES:
            findings.append(f"{tid}: priority '{priority}' is not one of {', '.join(PRIORITIES)}: Priority left empty")
            priority = ""
        order = extras.tag_order
        known = [x for x in (order or ()) if x in best.tags]
        unknown = [x for x in best.tags if order is not None and x not in order]
        if unknown:
            findings.append(f"{tid}: tags not in registries/tag_registry.jsonl, put last: {', '.join(unknown)}")
        tags = " ".join(known + unknown) if order is not None else " ".join(best.tags)
        if extras.epic_of:
            epic, notes = extras.epic_of(tid, best.path, best.tier)
            findings += notes
    fields = {
        "Title": f"{tid}: {title}".rstrip(": ") if title else tid,
        "Ticket ID": tid,
        "Status": status,
        "Domain": ", ".join(sorted({b.domain for b in mine if b.domain})) or (current or {}).get("Domain", ""),
        "Seat": ", ".join(sorted({b.seat for b in working})) or ("" if status == "To do" else (current or {}).get("Seat", "")),
        "Host": merge_host_entries((current or {}).get("Host", ""), [host] if mine else [], host),
        "Branch": merge_host_entries((current or {}).get("Branch", ""), entries, f"{host}:"),
        "PR": ", ".join(pr_urls),
        "Tier": best.tier if best else "",
        "Layer": layer, "Priority": priority, "Epic": epic, "Tags": tags,
        "Body": BODY.format(path=best.path if best else "agent-working/tickets/"),
        "Source": source,
    }
    fields["Sync hash"] = sync_hash(fields)
    return fields, findings


def hand_edits(item: dict, derived: dict) -> list[str]:
    """The item's fields no longer hash to the Sync hash the sync stored: someone edited it. One line per differing field."""
    stored = item.get("Sync hash")
    if not stored:
        return []
    version = hash_version(stored)
    if sync_hash(item, version) == stored:  # checked against that version's fields only
        return []
    return [f"hand edit: {derived['Ticket ID']} {f} '{item.get(f, '')}' -> '{derived[f]}'" for f in HASH_VERSIONS[version] if item.get(f, "") != derived[f]]


def in_pilot_lane(fact: BranchFact, lanes: list[str]) -> bool:
    return fact.domain in lanes or any(fact.branch.startswith(f"{lane}-") for lane in lanes)


def build_plan(main_index: dict[str, list[tuple[str, str]]], load_main: Callable[[str], TicketCopy], branches: list[BranchFact],
               prs: list[PrFact] | None, items: list[dict], host: str, source: str, config: dict,
               done_at: Callable[[str], datetime | None], now: datetime, extras: Extras | None = None) -> Plan:
    plan = Plan()
    by_id: dict[str, dict] = {}
    for item in items:
        tid = item.get("Ticket ID")
        if not tid:
            continue
        first = by_id.get(tid)
        if first is None:
            by_id[tid] = item
            continue
        # duplicate Ticket ID (a half-made create, or two writers): keep the item whose stored Sync hash still matches, else the first
        keep_new = bool(item.get("Sync hash")) and sync_hash(item) == item["Sync hash"] and not (
            first.get("Sync hash") and sync_hash(first) == first["Sync hash"])
        loser = first if keep_new else item
        by_id[tid] = item if keep_new else first
        plan.archives.append((tid, "duplicate Ticket ID"))
        plan.archive_item_ids.append(loser.get("_item_id", ""))
        plan.findings.append(f"duplicate Ticket ID {tid}: one item kept, the other archived")
    pilot_start = date.fromisoformat(str(config["pilot_start"]))
    window = int(config["done_window_days"])
    stale_before = now.timestamp() - int(config.get("stale_branch_days", 14)) * 86400
    candidates = {c.id for b in branches if in_pilot_lane(b, config["pilot_lanes"]) for c in b.copies} | set(by_id)
    known = set(main_index) | {c.id for b in branches for c in b.copies}
    for tid in sorted(candidates):
        if tid not in known:
            continue
        main = [load_main(path) for _, path in main_index.get(tid, [])]
        derived, findings = derive_item(tid, main, branches, prs, by_id.get(tid), host, source, stale_before, extras)
        plan.findings += findings
        done_path = next((c.path for c in main if c.folder == "done"), None)
        finished = done_at(done_path) if done_path else None
        current = by_id.get(tid)
        if derived["Status"] == "Done":
            if finished is None and current is not None:
                plan.notes.append(f"done date unreadable: {tid}")
            if finished is None or finished.date() < pilot_start and current is None:
                continue
            if finished is not None and (now - finished).days > window:
                if current is not None:
                    plan.archives.append((tid, f"Done more than {window} days ago ({finished.date()})"))
                    plan.archive_item_ids.append(current.get("_item_id", ""))
                continue
        if current is None:
            plan.creates.append(derived)
            continue
        plan.hand_edits += hand_edits(current, derived)
        changed = [f for f in HASH_FIELDS if current.get(f, "") != derived[f]]
        if not changed and current.get("Sync hash", "") != derived["Sync hash"]:
            changed = ["Sync hash"]  # same values, older hash version: rewrite the hash only
        if changed:
            carried = {**derived, "_item_id": current.get("_item_id", ""), "_draft_id": current.get("_draft_id", "")}
            plan.updates.append((carried, changed))
    for item in items:
        tid = item.get("Ticket ID", "")
        if not tid:
            plan.archives.append((item.get("Title", "(untitled item)"), "no Ticket ID"))
            plan.archive_item_ids.append(item.get("_item_id", ""))
        elif tid not in known and by_id.get(tid) is item:
            plan.archives.append((tid, "no ticket file for this ID"))
            plan.archive_item_ids.append(item.get("_item_id", ""))
    return plan


# ---------------------------------------------------------------- output / CLI


def read_registry(root: Path, rel: str, key: str, notes: list[str]) -> tuple[str, ...] | None:
    """The `key` values of a JSONL registry, in file order; None (and a note) when it cannot be read, so nothing is validated against it."""
    try:
        rows = [json.loads(line) for line in (root / rel).read_text(encoding="utf-8").splitlines() if line.strip()]
        return tuple(r[key] for r in rows if key in r)
    except (OSError, ValueError):
        notes.append(f"{rel} unreadable: not validated against it")
        return None


def read_sequences(root: Path, run: Runner = run_command, ref: str = "origin/main") -> dict[str, set[str]]:
    """`todos/<folder>` or `done/<folder>` -> the ticket ids its SEQUENCE.md names (exact basename SEQUENCE.md; git ls-tree and git show only)."""
    listed = run(["git", "ls-tree", "-r", "--name-only", ref, "--", f"{TICKETS.as_posix()}/todos", f"{TICKETS.as_posix()}/done"], root)
    out: dict[str, set[str]] = {}
    for path in listed.stdout.split("\n") if listed.returncode == 0 else []:
        if Path(path).name != "SEQUENCE.md" or folder_key(path.removesuffix("SEQUENCE.md") + "x.md") is None:
            continue
        shown = run(["git", "show", f"{ref}:{path}"], root)
        if shown.returncode == 0:
            out[folder_key(path.removesuffix("SEQUENCE.md") + "x.md")] = sequence_ids(shown.stdout)
    return out


def load_config(root: Path, notes: list[str]) -> dict:
    cfg = dict(DEFAULTS)
    try:
        loaded = yaml.safe_load((root / CONFIG_REL).read_text(encoding="utf-8")) or {}
        cfg.update({k: v for k, v in loaded.items() if k in DEFAULTS})
    except (OSError, yaml.YAMLError):
        notes.append(f"{CONFIG_REL.as_posix()} unreadable: built-in defaults used")
    return cfg


def render(plan: Plan, host: str, sha: str, age_hours: float | None, detached: int, items_n: int, prs_n: int | None,
           mode: str = "DRY RUN (no GitHub or repo write)") -> str:
    age = "unknown age" if age_hours is None else f"{age_hours:.1f} h old"
    lines = [f"project_sync {mode} host={host} origin/main={sha[:9]} ({age}, no fetch) "
             f"items-in={items_n} open-PRs={'unknown' if prs_n is None else prs_n} detached-skipped={detached}"]
    for item in plan.creates:
        lines.append(f"create  {item['Ticket ID']}  {item['Status']}  seat={item['Seat'] or '-'}  branch={item['Branch'] or '-'}  pr={item['PR'] or '-'}")
    for item, changed in plan.updates:
        lines.append(f"update  {item['Ticket ID']}  {item['Status']}  changed: {', '.join(changed)}")
    for ident, reason in plan.archives:
        lines.append(f"archive {ident}  ({reason})")
    lines += plan.hand_edits + [f"finding: {f}" for f in plan.findings] + [f"note: {n}" for n in plan.notes]
    if not (plan.creates or plan.updates or plan.archives):
        lines.append("nothing to do")
    return "\n".join(lines)


def _client(config: dict, notes: list[str] | None = None):
    """The one GraphQL client, built lazily so a plain dry run never imports it. Raises ClientRefused when the Project isn't configured."""
    from tools.sessions.project_client import ClientRefused, ProjectClient

    number = int(config["project"].get("number") or 0)
    if number <= 0:
        raise ClientRefused("project.number is 0 in registries/session_project.yaml: set it to the Project's number first")
    return ProjectClient(str(config["project"]["owner"]), number)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Derive the ticket-state Project plan. Default: dry run (writes nothing). --init creates the "
                                                 "Project's fields; --apply carries out the plan. Items are never deleted, only archived.")
    parser.add_argument("--root", type=Path, default=REPO_ROOT)
    parser.add_argument("--host", default=None, help="this host's tag for Branch/Host entries (default: host_names[hostname] in session_project.yaml, else the hostname)")
    parser.add_argument("--items", type=Path, help="JSON file of the current Project items, for offline runs (default: a live read when the Project is configured)")
    parser.add_argument("--dry-run", action="store_true", help="accepted; the default mode")
    parser.add_argument("--apply", action="store_true", help="write the plan to the Project (needs project.number and the token file)")
    parser.add_argument("--init", action="store_true", help="create the Project's missing fields by name; writes nothing else")
    parser.add_argument("--replace-status-options", action="store_true", help="with --init: allow replacing the Status options on a Project that has items")
    args = parser.parse_args(argv)
    if (args.init and args.apply) or (args.apply and args.items) or (args.replace_status_options and not args.init):
        print("project_sync: use --init and --apply as separate runs, --apply never with --items, --replace-status-options only with --init.", file=sys.stderr)
        return 2
    plan_notes: list[str] = []
    config = load_config(args.root, plan_notes)
    args.host = args.host or config["host_names"].get(socket.gethostname(), socket.gethostname())
    from tools.sessions.project_client import ClientRefused, ProjectError, init_fields

    client = None
    if args.init or args.apply or (not args.items and int(config["project"].get("number") or 0) > 0):
        try:
            client = _client(config)
            if args.init:
                layers = read_registry(args.root, "registries/layer_registry.jsonl", "layer", plan_notes) or ()
                lines, code = init_fields(client, STATUSES, args.replace_status_options, layers)
                print("\n".join(lines))
                return code
        except ClientRefused as exc:
            if args.init or args.apply:
                print(f"project_sync: refused: {exc}", file=sys.stderr)
                return 2
            plan_notes.append(f"live read skipped: {exc}")
        except ProjectError as exc:
            print(f"project_sync: GitHub refused: {exc}", file=sys.stderr)
            return 1
    try:
        if client is not None:
            items = client.list_items()
        else:
            items = json.loads(args.items.read_text(encoding="utf-8")) if args.items else []
    except ClientRefused as exc:
        print(f"project_sync: refused: {exc}", file=sys.stderr)
        return 2
    except ProjectError as exc:
        print(f"project_sync: GitHub refused: {exc}", file=sys.stderr)
        return 1
    sha, stamp = origin_info(args.root)
    now = datetime.now(timezone.utc)
    branches, detached = read_branch_facts(args.root, args.host, plan_notes)
    prs = read_open_prs(args.root, plan_notes)
    if args.apply and (prs is None or not getattr(prs, "complete", True)):
        print("project_sync: --apply refused, nothing written: the open PRs or one PR's files could not be read, so In review / PR would be "
              "written wrong. Re-run when gh answers.", file=sys.stderr)
        return 1
    index = read_main_index(args.root)
    source = f"{sha[:9]} @ {now.strftime('%Y-%m-%dT%H:%MZ')}"
    load_main = lambda path: read_main_copy(args.root, path)  # noqa: E731
    layers = read_registry(args.root, "registries/layer_registry.jsonl", "layer", plan_notes)
    extras = Extras(frozenset(layers) if layers is not None else None, read_registry(args.root, "registries/tag_registry.jsonl", "tag", plan_notes),
                    make_epic_resolver(index, load_main, read_sequences(args.root)))
    plan = build_plan(index, load_main, branches, prs, items, args.host, source, config,
                      lambda path: done_date(args.root, path), now, extras)
    plan.notes = plan_notes + plan.notes
    mode = "APPLY (writes to the GitHub Project)" if args.apply else ("DRY RUN, live read (no write)" if client is not None else "DRY RUN (no GitHub or repo write)")
    print(render(plan, args.host, sha, None if stamp is None else (time.time() - stamp) / 3600, detached, len(items),
                 None if prs is None else len(prs), mode))
    if args.apply:
        from tools.sessions.project_client import apply_plan
        try:
            project = client.load_project()
            done, not_done, error = apply_plan(client, project, plan)
        except ClientRefused as exc:
            print(f"project_sync: refused: {exc}", file=sys.stderr)
            return 2
        except ProjectError as exc:
            print(f"project_sync: GitHub refused: {exc}", file=sys.stderr)
            return 1
        print(f"applied {len(done)} step(s)" + (f"; STOPPED, {len(not_done)} not done" if error else "; nothing left"))
        if error:
            print(f"error: {error}", file=sys.stderr)
            print("not done: " + "; ".join(not_done), file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
