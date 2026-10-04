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

Subcommands: export, import, status, discard. TCK-20261004-HANDOVER-CROSS-MACHINE-TRANSIT.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import socket
import subprocess
import sys
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


def _list_files(base: Path) -> list[Path]:
    return sorted(p for p in base.rglob("*") if p.is_file()) if base.is_dir() else []


def _collect(roles: list[str] | None, drafts: bool, memory: bool,
             handover_dir: Path, memory_dir: Path) -> list[tuple[str, str, Path]]:
    """(kind, relative path, source file) for everything the export should carry."""
    out: list[tuple[str, str, Path]] = []
    for note in sorted(handover_dir.glob("*.md")) if handover_dir.is_dir() else []:
        if roles is None or note.stem in roles:
            out.append(("handover", note.name, note))
    if drafts:
        for f in _list_files(handover_dir / "drafts"):
            out.append(("handover", f.relative_to(handover_dir).as_posix(), f))
    if memory:
        for f in _list_files(memory_dir):
            out.append(("memory", f.relative_to(memory_dir).as_posix(), f))
    return out


def export_bundle(*, roles: list[str] | None = None, drafts: bool = True, memory: bool = True,
                  root: Path = TRANSIT_ROOT, handover_dir: Path = HANDOVER_DIR,
                  memory_dir: Path | None = None, host: str | None = None) -> Path:
    host = host or host_id()
    memory_dir = memory_dir if memory_dir is not None else default_memory_dir()
    items = _collect(roles, drafts, memory, handover_dir, memory_dir)
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


def import_bundle(host: str, *, dry_run: bool = False, root: Path = TRANSIT_ROOT,
                  handover_dir: Path = HANDOVER_DIR, memory_dir: Path | None = None,
                  local_host: str | None = None) -> list[str]:
    """Verify every hash first (abort before any write), then copy. Returns action lines."""
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
        lines.append(f"{b.name}: {len(rows)} files, exported {when}, {mine}; imported by: "
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


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("export")
    e.add_argument("--roles", help="comma-separated role names (default: all notes)")
    e.add_argument("--no-drafts", action="store_true")
    e.add_argument("--no-memory", action="store_true")
    i = sub.add_parser("import")
    i.add_argument("host")
    i.add_argument("--dry-run", action="store_true")
    sub.add_parser("status")
    d = sub.add_parser("discard")
    d.add_argument("host")
    d.add_argument("--force", action="store_true")
    a = ap.parse_args(argv)
    try:
        if a.cmd == "export":
            roles = [r.strip() for r in a.roles.split(",")] if a.roles else None
            b = export_bundle(roles=roles, drafts=not a.no_drafts, memory=not a.no_memory)
            print(f"exported to {b} ({len(_read_manifest(b))} files)")
        elif a.cmd == "import":
            for line in import_bundle(a.host, dry_run=a.dry_run):
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
