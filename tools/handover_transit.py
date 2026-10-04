#!/usr/bin/env python3
"""Carry session handover notes between machines through a committed, rolling transit bundle.

`.claude/handover/` and the project memory dir are local-only, and a session transcript does not
cross machines, so the handover note is the only continuity that can. `export` copies the notes,
the untracked `.claude/handover/drafts/` tree and (by default) the project memory into
`agent-working/handover-transit/<host>/`; `import <host>` restores them on another machine.

Rolling and temporary: one bundle per source host, each export replaces that host's previous
bundle, so a tree holds at most one small current bundle per machine (git history keeps old ones).
Files are stored with a `.txt` suffix appended so the doc registry, frontmatter validators and the
knowledge index never see them as docs; import strips it.

Only OPEN state is exported: role notes, drafts that are neither activated nor merged, and memory. A draft is
skipped when its ticket id is in `agent-working/tickets/done/` or tracked on `origin/main`, when it sits under an
`evidence` directory, when every ticket draft of its folder is skipped (the folder's README and notes go with
them), or when a file with identical bytes is already tracked on `origin/main`. `--include-all` exports
everything. A role also removes its own completed drafts when closing (docs/guides/agent_session_reset_boundaries.md).

Subcommands: export, import, status, discard. TCK-20261004-HANDOVER-CROSS-MACHINE-TRANSIT.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import socket
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

TRANSIT_ROOT = Path("agent-working/handover-transit")
HANDOVER_DIR = Path(".claude/handover")
MANIFEST = "MANIFEST.jsonl"
STORE_SUFFIX = ".txt"
KINDS = ("handover", "memory")


class TransitError(Exception):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def host_id() -> str:
    return re.sub(r"[^A-Za-z0-9._-]", "-", socket.gethostname()) or "unknown-host"


def _git_head() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, timeout=10, check=True
        ).stdout.strip()
    except Exception:
        return ""


def default_memory_dir() -> Path:
    """`~/.claude/projects/<slug>/memory` for this checkout; slug is the main checkout path with
    `/` replaced by `-`, matching how Claude Code keys project memory."""
    try:
        common = subprocess.run(
            ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
            capture_output=True, text=True, timeout=10, check=True,
        ).stdout.strip()
        root = Path(common).parent
    except Exception:
        root = Path.cwd()
    slug = str(root.resolve()).replace("/", "-")
    return Path.home() / ".claude" / "projects" / slug / "memory"


_BRANCH_LINE = re.compile(r"^\s*[-*]?\s*\**Branch\**\s*:\s*`?([A-Za-z0-9._/-]+)`?", re.MULTILINE)
UNATTRIBUTED = "unattributed"


def _note_branch(path: Path) -> str | None:
    """The first `Branch:` value in a note, ignoring the template placeholder `<name>`."""
    try:
        m = _BRANCH_LINE.search(path.read_text(encoding="utf-8", errors="replace"))
    except OSError:
        return None
    return m.group(1) if m else None


def exporting_role(environ=None, roster=None, explicit: str | None = None) -> str | None:
    """The role of the exporting session: `--role` when given, else the M2 resolution of `SESSION_ROLE` (set by the
    launcher). Never guessed: no signal or an unknown role is None, and the export summary flags it."""
    if explicit:
        return explicit
    env = (environ if environ is not None else os.environ).get("SESSION_ROLE")
    if not env or roster is None:
        return None
    from tools.sessions.resolve import RESOLVED, Signals, resolve
    res = resolve(Signals(source="startup", env_role=env), roster)
    return res.role if res.status == RESOLVED else None


def belongs_to(kind: str, rel: str, src: Path, role: str | None, roster=None) -> dict:
    """What an exported file belongs to: role, domain, ticket id, branch (note only) and its kind."""
    domain = None
    ticket = None
    branch = None
    if kind == "memory":
        return {"role": None, "domain": None, "ticket_id": None, "branch": None, "kind": "memory"}
    if "/" not in rel and rel.endswith(".md"):  # a role note, named after its role
        kind_name, who = "note", rel[:-3]
        branch = _note_branch(src)
    else:
        kind_name, who = "draft", role
        stem = Path(rel).stem
        ticket = stem if stem.startswith("TCK-") else None
    r = roster.role(who) if (roster is not None and who) else None
    domain = r.domain if r else None
    return {"role": who, "domain": domain, "ticket_id": ticket, "branch": branch, "kind": kind_name}


def _list_files(base: Path) -> list[Path]:
    return sorted(p for p in base.rglob("*") if p.is_file()) if base.is_dir() else []


@dataclass(frozen=True)
class DraftFilter:
    """What counts as already completed or merged, for pruning drafts from an export."""

    done_ids: frozenset[str] = frozenset()   # ticket ids in agent-working/tickets/done/
    main_ids: frozenset[str] = frozenset()   # ticket ids tracked on origin/main
    main_blobs: frozenset[str] = frozenset()  # git blob ids of every file tracked on origin/main

    def ticket_closed(self, ticket_id: str) -> bool:
        return ticket_id in self.done_ids or ticket_id in self.main_ids


def load_draft_filter(repo_root: Path = Path("."), ref: str = "origin/main") -> DraftFilter:
    done = frozenset(p.stem for p in (repo_root / "agent-working/tickets/done").rglob("TCK-*.md"))
    try:
        out = subprocess.run(["git", "ls-tree", "-r", ref], cwd=str(repo_root), capture_output=True, text=True,
                             timeout=60, check=True).stdout
    except Exception:
        return DraftFilter(done_ids=done)  # no origin/main: only the local done/ folder prunes
    ids, blobs = set(), set()
    for line in out.splitlines():
        meta, _, path = line.partition("\t")
        blobs.add(meta.split()[2])
        name = path.rsplit("/", 1)[-1]
        if name.startswith("TCK-") and name.endswith(".md"):
            ids.add(name[:-3])
    return DraftFilter(done_ids=done, main_ids=frozenset(ids), main_blobs=frozenset(blobs))


def _blob_id(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def _prune_drafts(files: list[Path], drafts_dir: Path, flt: DraftFilter) -> list[Path]:
    """Keep only open drafts (see the module docstring for what is skipped)."""
    closed: dict[Path, bool] = {}
    for f in files:
        if f.name.startswith("TCK-") and f.suffix == ".md":
            closed[f] = flt.ticket_closed(f.stem)
    by_folder: dict[str, list[bool]] = {}
    for f, c in closed.items():
        rel = f.relative_to(drafts_dir).parts
        if len(rel) > 1:
            by_folder.setdefault(rel[0], []).append(c)
    finished_folders = {k for k, v in by_folder.items() if v and all(v)}
    kept = []
    for f in files:
        rel = f.relative_to(drafts_dir).parts
        if "evidence" in rel[:-1]:
            continue
        if closed.get(f):
            continue
        if len(rel) > 1 and rel[0] in finished_folders:
            continue
        if _blob_id(f) in flt.main_blobs:
            continue
        kept.append(f)
    return kept


def _collect(roles: list[str] | None, drafts: bool, memory: bool,
             handover_dir: Path, memory_dir: Path, draft_filter: DraftFilter | None = None
             ) -> list[tuple[str, str, Path]]:
    """(kind, relative path, source file) for everything the export should carry."""
    out: list[tuple[str, str, Path]] = []
    for note in sorted(handover_dir.glob("*.md")) if handover_dir.is_dir() else []:
        if roles is None or note.stem in roles:
            out.append(("handover", note.name, note))
    if drafts:
        drafts_dir = handover_dir / "drafts"
        files = _list_files(drafts_dir)
        if draft_filter is not None:
            files = _prune_drafts(files, drafts_dir, draft_filter)
        for f in files:
            out.append(("handover", f.relative_to(handover_dir).as_posix(), f))
    if memory:
        for f in _list_files(memory_dir):
            out.append(("memory", f.relative_to(memory_dir).as_posix(), f))
    return out


def export_bundle(*, roles: list[str] | None = None, drafts: bool = True, memory: bool = True,
                  root: Path = TRANSIT_ROOT, handover_dir: Path = HANDOVER_DIR,
                  memory_dir: Path | None = None, host: str | None = None,
                  draft_filter: DraftFilter | None = None, role: str | None = None, roster=None,
                  worktree: str | None = None, branch: str | None = None) -> Path:
    """`draft_filter=None` exports every draft (`--include-all`); main() passes `load_draft_filter()`."""
    host = host or host_id()
    memory_dir = memory_dir if memory_dir is not None else default_memory_dir()
    items = _collect(roles, drafts, memory, handover_dir, memory_dir, draft_filter)
    if not items:
        raise TransitError("nothing to export (no handover notes, drafts or memory found)")
    bundle = root / host
    if bundle.exists():
        shutil.rmtree(bundle)  # rolling: replace this host's previous bundle wholesale
    head, stamp = _git_head(), _now()
    rows = []
    for kind, rel, src in items:
        dest = bundle / "files" / kind / (rel + STORE_SUFFIX)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dest)
        rows.append({
            "kind": kind, "path": rel, "sha256": _sha256(src), "bytes": src.stat().st_size,
            "host": host, "head": head, "exported_at": stamp,
            "worktree": worktree, "branch": branch,
            "belongs_to": belongs_to(kind, rel, src, role, roster),
        })
    (bundle / MANIFEST).write_text(
        "".join(json.dumps(r, sort_keys=True) + "\n" for r in rows), encoding="utf-8"
    )
    return bundle


def _read_manifest(bundle: Path) -> list[dict]:
    mf = bundle / MANIFEST
    if not mf.is_file():
        raise TransitError(f"no {MANIFEST} in {bundle}")
    rows = [json.loads(line) for line in mf.read_text(encoding="utf-8").splitlines() if line.strip()]
    for r in rows:
        if r.get("kind") not in KINDS:
            raise TransitError(f"unknown kind in manifest: {r.get('kind')!r}")
        parts = Path(r["path"]).parts
        if Path(r["path"]).is_absolute() or ".." in parts:
            raise TransitError(f"unsafe path in manifest: {r['path']!r}")
    return rows


def _stored(bundle: Path, row: dict) -> Path:
    return bundle / "files" / row["kind"] / (row["path"] + STORE_SUFFIX)


def _row_role(row: dict) -> str | None:
    return (row.get("belongs_to") or {}).get("role")


def group_by_role(rows: list[dict]) -> dict[str, list[dict]]:
    """role -> rows; memory under `memory`, role-less non-memory rows under `unattributed` (never dropped)."""
    groups: dict[str, list[dict]] = {}
    for r in rows:
        key = "memory" if r["kind"] == "memory" else (_row_role(r) or UNATTRIBUTED)
        groups.setdefault(key, []).append(r)
    return groups


def summarize_groups(rows: list[dict]) -> str:
    groups = group_by_role(rows)
    order = sorted(k for k in groups if k not in ("memory", UNATTRIBUTED)) + [k for k in (UNATTRIBUTED, "memory") if k in groups]
    return ", ".join(f"{k}: {len(groups[k])}" for k in order)


def import_bundle(host: str, *, dry_run: bool = False, root: Path = TRANSIT_ROOT,
                  handover_dir: Path = HANDOVER_DIR, memory_dir: Path | None = None,
                  local_host: str | None = None, role: str | None = None, no_memory: bool = False) -> list[str]:
    """Verify every hash first (abort before any write), then copy. Returns action lines.

    `role` limits the copy to that role's notes and drafts; memory is still imported unless `no_memory`. Items with
    no role are never copied by a role-limited import and never silently dropped: they are listed as skipped."""
    bundle = root / host
    memory_dir = memory_dir if memory_dir is not None else default_memory_dir()
    rows = _read_manifest(bundle)
    for r in rows:
        src = _stored(bundle, r)
        if not src.is_file():
            raise TransitError(f"missing stored file: {src}")
        if _sha256(src) != r["sha256"]:
            raise TransitError(f"sha256 mismatch for {r['kind']}/{r['path']}; nothing imported")
    stamp = _now().replace(":", "")
    actions: list[str] = []
    for r in rows:
        if r["kind"] == "memory" and no_memory:
            continue
        if role is not None and r["kind"] != "memory" and _row_role(r) != role:
            who = _row_role(r) or UNATTRIBUTED
            actions.append(f"skipped {r['kind']}/{r['path']} (belongs to {who}, not {role})")
            continue
        src = _stored(bundle, r)
        target = (handover_dir if r["kind"] == "handover" else memory_dir) / r["path"]
        if target.is_file():
            if _sha256(target) == r["sha256"]:
                actions.append(f"unchanged {target}")
                continue
            backup = target.with_name(target.name + f".local-backup-{stamp}")
            actions.append(f"replace {target} (local copy backed up to {backup.name})")
            if not dry_run:
                shutil.copyfile(target, backup)
        else:
            actions.append(f"create {target}")
        if not dry_run:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, target)
    if not dry_run:
        (bundle / f".imported-{local_host or host_id()}").write_text(_now() + "\n", encoding="utf-8")
    return actions


def _bundles(root: Path) -> list[Path]:
    return sorted(p for p in root.iterdir() if p.is_dir()) if root.is_dir() else []


def pending_bundles(root: Path = TRANSIT_ROOT, local_host: str | None = None) -> list[str]:
    """Bundle ids from other hosts this machine has not imported (the hook's input)."""
    local = local_host or host_id()
    return [
        b.name for b in _bundles(root)
        if b.name != local and (b / MANIFEST).is_file() and not (b / f".imported-{local}").exists()
    ]


def bundle_summary(bundle_id: str, root: Path = TRANSIT_ROOT) -> str:
    """`role: n, ..., unattributed: n, memory: n` for one bundle ("" when unreadable)."""
    try:
        return summarize_groups(_read_manifest(root / bundle_id))
    except (TransitError, ValueError, OSError):
        return ""


def status_lines(root: Path = TRANSIT_ROOT, local_host: str | None = None) -> list[str]:
    local = local_host or host_id()
    lines = []
    for b in _bundles(root):
        try:
            rows = _read_manifest(b)
        except (TransitError, ValueError) as exc:
            lines.append(f"{b.name}: unreadable ({exc})")
            continue
        when = max((r["exported_at"] for r in rows), default="?")
        mine = "imported here" if (b / f".imported-{local}").exists() else "NOT imported here"
        markers = sorted(m.name[len(".imported-"):] for m in b.glob(".imported-*"))
        lines.append(f"{b.name}: {len(rows)} files ({summarize_groups(rows)}), exported {when}, {mine}; imported by: "
                     f"{', '.join(markers) or 'nobody'}")
    return lines


def discard_bundle(host: str, *, force: bool = False, root: Path = TRANSIT_ROOT) -> None:
    bundle = root / host
    if not bundle.is_dir():
        raise TransitError(f"no bundle for host {host!r}")
    if not force and not any(bundle.glob(".imported-*")):
        raise TransitError(f"bundle {host!r} has no .imported-* marker; use --force to discard anyway")
    tracked = subprocess.run(["git", "ls-files", "--error-unmatch", str(bundle)],
                             capture_output=True).returncode == 0
    if tracked:
        subprocess.run(["git", "rm", "-r", "-q", "-f", str(bundle)], check=True)
    if bundle.exists():
        shutil.rmtree(bundle)


def _load_roster():
    try:
        from tools.sessions.roster import load_roster
        return load_roster()
    except Exception:
        return None


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("export")
    e.add_argument("--roles", help="comma-separated role names (default: all notes)")
    e.add_argument("--no-drafts", action="store_true")
    e.add_argument("--no-memory", action="store_true")
    e.add_argument("--include-all", action="store_true",
                   help="also export completed or merged drafts and evidence directories")
    i = sub.add_parser("import")
    i.add_argument("host")
    i.add_argument("--dry-run", action="store_true")
    i.add_argument("--role", help="import only this role's notes and drafts (memory still comes along)")
    i.add_argument("--no-memory", action="store_true")
    e.add_argument("--role", help="role of the exporting session (default: resolved from SESSION_ROLE; never guessed)")
    sub.add_parser("status")
    d = sub.add_parser("discard")
    d.add_argument("host")
    d.add_argument("--force", action="store_true")
    a = ap.parse_args(argv)
    try:
        if a.cmd == "export":
            roles = [r.strip() for r in a.roles.split(",")] if a.roles else None
            flt = None if a.include_all else load_draft_filter()
            roster = _load_roster()
            role = exporting_role(roster=roster, explicit=a.role)
            wt = str(Path.cwd().resolve())
            br = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True).stdout.strip() or None
            b = export_bundle(roles=roles, drafts=not a.no_drafts, memory=not a.no_memory, draft_filter=flt,
                              role=role, roster=roster, worktree=wt, branch=br)
            rows = _read_manifest(b)
            print(f"exported to {b} ({len(rows)} files: {summarize_groups(rows)}) from {wt} on {br}")
            if role is None and any(r["kind"] == "handover" and (r["belongs_to"]["kind"] == "draft") for r in rows):
                print("WARNING: the exporting role is unresolved (no --role, no SESSION_ROLE): drafts are listed as "
                      "unattributed. Pass --role <role> to attribute them.", file=sys.stderr)
        elif a.cmd == "import":
            for line in import_bundle(a.host, dry_run=a.dry_run, role=a.role, no_memory=a.no_memory):
                print(line)
        elif a.cmd == "status":
            for line in status_lines() or ["no transit bundles"]:
                print(line)
        else:
            discard_bundle(a.host, force=a.force)
            print(f"discarded {a.host}")
    except TransitError as exc:
        print(f"handover_transit: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
