"""Command line for the store: `python -m visual_assets.store <command>`.

Every command that writes the store or exports from it takes the store lock (`ADR D24`, `store/lock.py`); a second writer exits 2 at once. Read-only or local: `intake <dir>`, `review <id>`, `list`, `show <id>`, `audit`, `verify`, `export-runtime` (reads committed candidates, writes a NEW directory outside the catalog). HUMAN-GATED (never run by an agent): `adopt` and
`revoke`, which write the tracked catalog, refuse unless stdin is a terminal, and make the operator type the id after reading what
they are about to decide. Exit codes: 0 success (a PASSED intake, a clean audit, a review whose preview matches or could not be checked here), 1 a QUARANTINED intake, a preview that does NOT match the source, or an audit with breaks,
2 a refusal or error. This is the only module that reads the clock; library code takes timestamps as parameters.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from datetime import datetime, timedelta, timezone

from visual_assets.store import adoption, audit, config, deletionlog, draftexport, drafts, gc, lock, records, release, revoke, runtime_export, setadoption, verify
from visual_assets.store import review as review_api
from visual_assets.store.build import exporter
from visual_assets.store import intake as intake_api
from visual_assets.store.contracts.base import IntakeVerdict
from visual_assets.store.contracts.review import RenderVerdict
from visual_assets.store.contracts.intake import IntakeResult
from visual_assets.store.errors import GateError, StageError, StoreError
from visual_assets.store.intake.validator import file_hash


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _retention_cutoff() -> str:
    """`now` minus the retention bound, as a UTC timestamp: intakes created before it are expired (the clock is read here, not in the library)."""
    return (datetime.now(timezone.utc) - timedelta(days=config.MAX_UNADOPTED_INTAKE_AGE_DAYS)).strftime("%Y-%m-%dT%H:%M:%SZ")


def _renderer():
    """The real sandboxed Aseprite renderer when this machine has Aseprite and bwrap, else None (then nothing is verified and `adopt` refuses)."""
    return exporter.default_renderer()


def _stdin_is_tty() -> bool:
    return sys.stdin.isatty()


def _prompt(expected: str, notices: Sequence[str]) -> bool:
    """Show what is being decided, then require the operator to type the exact id."""
    for line in notices:
        print(line)
    return input(f"Type {expected} to confirm: ").strip() == expected


def _print_result(result: IntakeResult) -> None:
    print(f"{result.intake_id}  {result.verdict.value}  candidate {result.candidate_id}")
    for finding in result.findings:
        print(f"  {finding.code.value}: {finding.detail}")


def _print_claims(intake_id: str) -> None:
    package = intake_api.claims(intake_id)
    if package is None:
        return
    shown = lambda value: str(getattr(value, "value", value))  # noqa: E731
    print("  claimed by the producer (unverified statements, not a clearance):")
    print(f"    licence {shown(package.licence_state)}, evidence {shown(package.licence_evidence_ref)}")
    print(f"    producer {shown(package.producer_class)}, creator {shown(package.creator)}, brief {shown(package.brief_id)}")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m visual_assets.store", description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("intake", help="stage and validate a candidate package directory").add_argument("directory")
    sub.add_parser("review", help="export a PASSED intake's preview and summary to the local review area").add_argument("intake_id")
    sub.add_parser("list", help="list quarantined intakes and adopted sources")
    sub.add_parser("show", help="print an intake (in-...), an adoption (ad-...) or a source revision (<id>/<rNNNN>)").add_argument("id")
    sub.add_parser("audit", help="rebuild and check the catalog's provenance chain (read-only)")
    sub.add_parser("verify", help="whole-store integrity check in pure Python (read-only); exits non-zero on any blocking finding")
    build = sub.add_parser("build", help="export adopted sources to PNG artifacts (needs Aseprite and bwrap)")
    build.add_argument("source_asset_id", nargs="?")
    rel = sub.add_parser("release", help="assemble an immutable release CANDIDATE manifest (there is no active release)")
    rel.add_argument("--catalog-id", required=True)
    rel.add_argument("--release-id", help="rc-NNNN; default is the next one")
    exp = sub.add_parser("export-runtime", help="write the client's runtime manifest and PNGs for one release candidate into a NEW directory outside the catalog")
    exp.add_argument("--catalog-id", required=True)
    exp.add_argument("--release-id", required=True, help="rc-NNNN")
    exp.add_argument("--out", required=True, help="a directory that does not exist yet")
    exp.add_argument("--atlas", action="store_true", help="also write one atlas PNG and JSON per family next to the per-file export (opt-in; nothing reads them yet)")
    collect = sub.add_parser("gc", help="list files nothing needs; deletes only with --delete")
    collect.add_argument("--delete", action="store_true")

    dels = sub.add_parser("deletions", help="list the local deletion log of `gc --delete` (read-only); --archive moves a full log aside (takes the store lock)")
    dels.add_argument("--archive", action="store_true")

    adopt = sub.add_parser("adopt", help="HUMAN ONLY: adopt a PASSED intake as a new source revision")
    adopt.add_argument("intake_id")
    adopt.add_argument("--visual-key", required=True)
    adopt.add_argument("--approver", required=True)
    adopt.add_argument("--approver-role", required=True)
    adopt.add_argument("--licence", required=True, help="your own licence decision (only CLEARED is adoptable)")
    adopt.add_argument("--licence-evidence", required=True, help="your own evidence reference, never taken from the package")
    adopt.add_argument("--source-asset-id", required=True)
    adopt.add_argument("--detail", default=None, help="the key's detail value this fills (only for a key that declares a detail axis; omitted = its default)")
    lineage = adopt.add_mutually_exclusive_group(required=True)
    lineage.add_argument("--new", action="store_true", help="start a new source asset (refused if the id exists)")
    lineage.add_argument("--parent", metavar="rNNNN", help="the latest unrevoked revision of an existing source asset")

    draft = sub.add_parser("draft", help="draft sets: unadopted drafts kept in git outside the catalog (no approval is recorded)")
    draft_sub = draft.add_subparsers(dest="draft_command", required=True)
    keep = draft_sub.add_parser("keep", help="keep a PASSED intake as a draft in a set (an agent may run this)")
    keep.add_argument("intake_id")
    keep.add_argument("--set", dest="set_id", required=True)
    keep.add_argument("--as", dest="visual_key", required=True, help="the visual key this draft is for")
    keep.add_argument("--detail", default=None, help="the key's detail value (only for a key that declares a detail axis)")
    keep.add_argument("--source-asset-id", default=None, help="the id it will be adopted under (default: the key with dots as underscores, plus _<detail>)")
    keep.add_argument("--replace", action="store_true", help="replace the set's existing draft for this slot")
    keep.add_argument("--revises", dest="parent_revision", default=None, metavar="rNNNN", help="the draft is the NEXT revision of the existing source asset named by --source-asset-id; rNNNN must be its latest unrevoked revision")
    drop = draft_sub.add_parser("drop", help="remove one draft from a set and record it in the set (an agent may run this; it records no approval)")
    drop.add_argument("set_id")
    drop.add_argument("--slot", required=True, metavar="KEY[:DETAIL]", help="the draft's slot, for example icon.item.tool or terrain.forest:bush")
    drop.add_argument("--reason", required=True, help="why (plain text, at most 80 characters); recorded in the set")
    dexport = draft_sub.add_parser("export", help="write a draft preview manifest and its preview PNGs for the isolated preview page into a NEW directory (read-only on the drafts)")
    dexport.add_argument("set_id")
    dexport.add_argument("out_dir", help="a directory that does not exist yet")
    dverify = draft_sub.add_parser("verify", help="check every draft's hashes, declared keys and no stray files (read-only)")
    dverify.add_argument("set_id", nargs="?")
    aset = sub.add_parser("adopt-set", help="HUMAN ONLY: adopt every entry of a REVIEWED draft set in one decision (all or nothing)")
    aset.add_argument("set_id")
    aset.add_argument("--approver", required=True)
    aset.add_argument("--approver-role", required=True)
    aset.add_argument("--licence", required=True, help="your own licence decision (only CLEARED is adoptable)")
    aset.add_argument("--licence-evidence", required=True, help="your own evidence reference, never taken from any draft")
    aset.add_argument("--review-evidence", required=True, help="what you reviewed, for example the preview page of this set")

    rev = sub.add_parser("revoke", help="HUMAN ONLY: revoke an intake (in-...) or a source revision (<id>/<rNNNN>)")
    rev.add_argument("target")
    rev.add_argument("--reason", required=True)
    rev.add_argument("--approver", required=True)
    rev.add_argument("--approver-role", required=True)
    return parser


def _require_terminal(command: str) -> None:
    if not _stdin_is_tty():
        raise GateError("no_terminal", f"{command} is a human decision: it refuses to run unless stdin is a terminal")


def _show(identifier: str) -> int:
    if identifier.startswith("in-"):
        _print_result(intake_api.show(identifier))
        _print_claims(identifier)
    elif identifier.startswith("ad-"):
        a = records.load_adoption(identifier)
        print(f"{a.adoption_id}  intake {a.intake_id}  {a.source_asset_id} {a.source_revision}  key {a.visual_key}")
        print(f"  approved by {a.approver_name} ({a.approver_role}) at {a.decided_at}; licence {a.licence_state.value} "
              f"(stated by the approver), evidence {getattr(a.licence_evidence_ref, 'value', a.licence_evidence_ref)}")
    else:
        sid, _, rev = identifier.partition("/")
        s = records.load_source(sid, rev)
        print(f"{s.source_asset_id} {s.source_revision}  parent {s.parent_revision}  adoption {s.adoption_id}  {s.width}x{s.height}")
        print(f"  revoked: {rev in records.revoked_revisions(sid)}")
    return 0


# ADR D24: every command is classified, so a new one cannot forget the lock decision (a test compares these sets with the parser).
# WRITING commands take the store lock for the whole command (exports count: a concurrent adopt must not change the state mid-read).
WRITING_COMMANDS = frozenset({"intake", "review", "build", "release", "export-runtime", "adopt", "adopt-set", "revoke"})
READ_ONLY_COMMANDS = frozenset({"list", "show", "audit", "verify"})
CONDITIONAL_COMMANDS = frozenset({"gc", "draft", "deletions"})  # lock only for `gc --delete`, `draft keep|drop|export`, `deletions --archive`
HUMAN_GATED = frozenset({"adopt", "adopt-set", "revoke"})
_LOCKED_DRAFT = frozenset({"keep", "drop", "export"})


def lock_name(args: argparse.Namespace) -> str | None:
    """The holder name to lock under, or None when this invocation only reads."""
    command = args.command
    if command in WRITING_COMMANDS:
        return command
    if command == "gc":
        return "gc" if args.delete else None
    if command == "draft":
        return f"draft {args.draft_command}" if args.draft_command in _LOCKED_DRAFT else None
    if command == "deletions":
        return "deletions" if args.archive else None
    return None


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command in HUMAN_GATED:
            _require_terminal(args.command)  # refused before the lock, so a refusal leaves no trace
        name = lock_name(args)
        if name is None:
            return _run(args)
        with lock.store_write_lock(name, started_at=_now()):
            return _run(args)
    except StoreError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


def _run(args: argparse.Namespace) -> int:
    if args.command == "intake":
        result = intake_api.intake(args.directory, created_at=_now())
        _print_result(result)
        return 0 if result.verdict is IntakeVerdict.PASSED else 1
    if args.command == "review":
        outcome = review_api.review(args.intake_id, created_at=_now(), renderer=_renderer())
        print(outcome.directory)
        print(outcome.note)
        return 1 if outcome.verdict is RenderVerdict.MISMATCH else 0
    if args.command == "show":
        return _show(args.id)
    if args.command == "audit":
        report = audit.audit_chain()
        for item in report.breaks:
            print(f"BREAK {item.code}  {item.path}  {item.detail}")
        for note in report.notes:
            print(f"note: {note}")
        print("chain ok" if report.ok else f"{len(report.breaks)} break(s)")
        return 0 if report.ok else 1
    if args.command == "verify":
        findings = verify.verify()
        for f in findings:
            print(f"{'FINDING' if f.blocking else 'note'} {f.code}  {f.path}  {f.detail}")
        blocking = [f for f in findings if f.blocking]
        print("store ok" if not blocking else f"{len(blocking)} blocking finding(s)")
        return 1 if blocking else 0
    if args.command == "build":
        for item in exporter.build(args.source_asset_id, renderer=_renderer()):
            print(f"{item.artifact_id} {item.source_revision} {item.pixel_hash} {'built' if item.created else 'unchanged'}")
        return 0
    if args.command == "release":
        manifest = release.assemble_release(args.catalog_id, release_id=args.release_id)
        print(f"{manifest.catalog_id}/{manifest.release_id}: {len(manifest.entries)} entries (candidate only, nothing is active)")
        return 0
    if args.command == "export-runtime":
        runtime = runtime_export.export_runtime(args.catalog_id, args.release_id, args.out, atlases=args.atlas)
        print(f"{runtime.catalog_id}/{runtime.release_id}: {len(runtime.entries)} entries exported to {args.out}")
        return 0
    if args.command == "gc":
        for item in gc.gc(delete=args.delete, expire_before=_retention_cutoff(), decided_at=_now() if args.delete else None):
            print(f"{'deleted' if args.delete else 'would delete'} {item.kind} {item.path.name}  ({item.reason})")
        if not args.delete:  # a dry-run-only report; tracked history is never deleted
            for path in gc.tracked_unreferenced():
                print(f"kept: tracked history, never deleted: {path.name}  (no committed release candidate references it)")
        return 0
    if args.command == "deletions":
        if args.archive:
            print(f"archived the deletion log as {deletionlog.archive().name}; the next log continues the same chain")
            return 0
        for line in deletionlog.listing():
            print(line)
        return 0
    if args.command == "adopt":
        _require_terminal("adopt")
        record = adoption.adopt(
            args.intake_id, visual_key=args.visual_key, approver=args.approver, approver_role=args.approver_role,
            licence_state=args.licence, licence_evidence_ref=args.licence_evidence, source_asset_id=args.source_asset_id,
            new=args.new, parent=args.parent, detail_value=args.detail, decided_at=_now(), confirm=_prompt, renderer=_renderer(),
        )
        print(f"adopted {record.intake_id} as {record.source_asset_id} {record.source_revision} ({record.adoption_id})")
        return 0
    if args.command == "draft":
        if args.draft_command == "keep":
            entry = drafts.keep(args.intake_id, set_id=args.set_id, visual_key=args.visual_key, detail=args.detail,
                                source_asset_id=args.source_asset_id, replace=args.replace, parent_revision=args.parent_revision)
            how = f"as the next revision of {entry.source_asset_id} (parent {entry.parent_revision})" if entry.parent_revision else f"as {entry.source_asset_id}"
            print(f"kept {entry.draft_id} in {args.set_id} as {entry.visual_key}{'' if entry.detail is None else ' [' + entry.detail + ']'} "
                  f"(will be adopted {how}); nothing is adopted")
            return 0
        if args.draft_command == "drop":
            key, _, detail = args.slot.partition(":")
            dropped = drafts.drop(args.set_id, visual_key=key, detail=detail or None, reason=args.reason)
            _, data = drafts.load_set(args.set_id)
            print(f"dropped {dropped.draft_id} ({args.slot}) from {args.set_id}: {dropped.reason}; the draft set hash is now {file_hash(data)} "
                  "(a review of the old hash no longer describes this set); nothing is adopted")
            return 0
        if args.draft_command == "export":
            manifest = draftexport.export_draft_preview(args.set_id, args.out_dir)
            print(f"{args.set_id}: {len(manifest.entries)} drafts exported to {args.out_dir}; draft set hash {manifest.draft_set_hash}")
            return 0
        findings = drafts.verify_set(args.set_id) if args.set_id else drafts.verify_all()
        for finding in findings:
            print(f"{finding.code}  {finding.path}: {finding.detail}")
        print("drafts ok" if not findings else f"{len(findings)} finding(s)")
        return 1 if findings else 0
    if args.command == "adopt-set":
        _require_terminal("adopt-set")
        record = setadoption.adopt_set(
            args.set_id, approver=args.approver, approver_role=args.approver_role, licence_state=args.licence,
            licence_evidence_ref=args.licence_evidence, review_evidence_ref=args.review_evidence, decided_at=_now(), confirm=_prompt,
            renderer=_renderer(),
        )
        print(f"adopted set {record.set_id}: {len(record.entries)} entries ({record.set_adoption_id})")
        return 0
    if args.command == "revoke":
        _require_terminal("revoke")
        record = revoke.revoke(
            args.target, reason=args.reason, approver=args.approver, approver_role=args.approver_role,
            decided_at=_now(), confirm=_prompt,
        )
        print(f"revoked {args.target} ({record.revocation_id})")
        return 0
    results, problems = intake_api.list_results()
    for result in results:
        revoked = " REVOKED" if records.intake_revoked_locally(result.intake_id) else ""
        print(f"{result.intake_id}  {result.verdict.value}  candidate {result.candidate_id}  {result.created_at}{revoked}")
    for name in problems:
        print(f"{name}  UNREADABLE")
    for sid in records.list_source_ids():
        for rev in records.list_revisions(sid):
            print(f"source {sid}/{rev}  eligible {revoke.is_build_eligible(sid, rev)}")
    return 0
