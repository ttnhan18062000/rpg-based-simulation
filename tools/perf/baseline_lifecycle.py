"""Promote a benchmark record to a new versioned baseline, and check a baselines directory (PERF-M2-T05).

``promote`` is the only supported way to add a baseline. It refuses, and writes nothing, when the candidate:

* is not a valid ``BenchmarkRecord`` (schema 1.0);
* was measured on a dirty ``src/`` tree (``identity.engine.dirty_src``);
* left ``NORMAL`` (or has no ``runtime_mode_sequence``): it does not prove it did the nominal work;
* lacks the current ``result.cost_accounting_version`` (a stale or missing one is not comparable);
* cites no cause: a ticket id, a divergence id (``DEV-nnn``) or a behaviour PR (``PR #n``). A ticket or divergence that does not exist
  in this repository is refused too. A PR number cannot be checked offline and is accepted by shape.

A baseline change is a reviewed change of evidence, not a way to make a build pass, so the cause is required and recorded.

A promotion writes ``<name>.vNNNN.json`` next to the earlier versions and never touches them. The file is the record, with
``identity.baseline_ref`` pointing at the previous version (``{id, schema_version, record_digest}``), plus a top-level ``promotion`` object
(cause, note, time, the before identity and the after identity). ``BenchmarkRecord.from_dict`` ignores that key, so the file is still a
valid record.

``check`` verifies a baselines directory: every ``*.json`` is a valid ``BenchmarkRecord`` or named in ``LEGACY_TRIPWIRE_REFERENCES`` (the 15
unlabelled-identity files from before schema 1.0, kept as tripwire references until ``PERF-M2-T08`` re-records them), and the version
chain of each promoted baseline is intact.

Exit codes: 0 done, 1 usage or unreadable input, 2 refused (the reasons are printed, one per line, as ``REFUSED: <code>: <message>``).
"""
from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.core.governance import RuntimeMode  # noqa: E402
from src.perf.benchmark_record import (  # noqa: E402
    COST_ACCOUNTING_VERSION,
    BaselineRef,
    BenchmarkRecord,
    BenchmarkRecordError,
)

DEFAULT_BASELINES_DIR = REPO_ROOT / "tests" / "perf" / "baselines"

#: The 15 files committed before schema 1.0. They are tripwire references with no identity, not records.
LEGACY_TRIPWIRE_REFERENCES = frozenset(
    {
        "combat_10_concurrent.json",
        "combat_10_local.json",
        "idle_100_concurrent.json",
        "idle_100_local.json",
        "mixed_200_concurrent.json",
        "mixed_200_local.json",
        "movement_100_concurrent.json",
        "movement_100_local.json",
        "resource_100_concurrent.json",
        "resource_100_local.json",
        "simq_corpus_crowded_frontier.json",
        "simq_corpus_frontier_extended.json",
        "simq_corpus_frontier_marches.json",
        "strategic_100_concurrent.json",
        "strategic_100_local.json",
    }
)

_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9_]*$")
_VERSIONED_RE = re.compile(r"^(?P<name>[a-z0-9][a-z0-9_]*)\.v(?P<version>\d{4})\.json$")
_TICKET_RE = re.compile(r"^TCK-\d{8}-[A-Z0-9][A-Z0-9-]*$")
_DIVERGENCE_RE = re.compile(r"^DEV-\d{3,}$")
_PR_RE = re.compile(r"^(?:PR ?#?|#)(?P<number>\d+)$")


@dataclass(frozen=True)
class Refusal:
    """One reason a promotion was refused."""

    code: str
    message: str


def record_digest(record: BenchmarkRecord) -> str:
    """sha256 of the record's canonical JSON (sorted keys). The ``promotion`` object is not part of the record, so it is not hashed."""
    payload = json.dumps(record.to_dict(), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _load_record(data: Dict[str, Any]) -> BenchmarkRecord:
    return BenchmarkRecord.from_dict({k: v for k, v in data.items() if k != "promotion"})


def _cause_refusal(cause: Optional[str], repo_root: Path) -> Optional[Refusal]:
    cause = (cause or "").strip()
    if not cause:
        return Refusal("no_cause", "no cause cited: give a ticket id, a divergence id (DEV-nnn) or a behaviour PR (PR #n)")
    if _TICKET_RE.match(cause):
        if not any(repo_root.joinpath("agent-working", "tickets").rglob(f"{cause}.md")):
            return Refusal("unknown_cause", f"ticket {cause} does not exist under agent-working/tickets/")
        return None
    if _DIVERGENCE_RE.match(cause):
        divergences = repo_root / "docs" / "guidelines" / "intentional_divergences.md"
        text = divergences.read_text(encoding="utf-8") if divergences.exists() else ""
        if f"### {cause} " not in text:
            return Refusal("unknown_cause", f"divergence {cause} is not recorded in docs/guidelines/intentional_divergences.md")
        return None
    if _PR_RE.match(cause):
        return None
    return Refusal("no_cause", f"{cause!r} is not a ticket id, a divergence id (DEV-nnn) or a behaviour PR (PR #n)")


def refusals(record: BenchmarkRecord, cause: Optional[str], repo_root: Path = REPO_ROOT) -> List[Refusal]:
    """Every reason ``record`` may not be promoted. Empty means it may."""
    found: List[Refusal] = []
    if record.identity.engine.dirty_src:
        found.append(Refusal("dirty_src", "identity.engine.dirty_src is true: a baseline must come from a clean src/ tree"))
    sequence = record.result.runtime_mode_sequence
    off_normal = sorted({run.mode for run in sequence} - {RuntimeMode.NORMAL.name})
    if not sequence:
        found.append(Refusal("mode_sequence_empty", "runtime_mode_sequence is empty: the run cannot prove it stayed NORMAL"))
    elif off_normal:
        found.append(Refusal("mode_not_normal", f"runtime_mode_sequence left NORMAL ({', '.join(off_normal)})"))
    version = record.result.cost_accounting_version
    if not version:
        found.append(Refusal("cost_accounting_version_missing", "result.cost_accounting_version is missing"))
    elif version != COST_ACCOUNTING_VERSION:
        found.append(
            Refusal("cost_accounting_version_stale", f"result.cost_accounting_version is {version!r}, the current one is {COST_ACCOUNTING_VERSION!r}")
        )
    cause_refusal = _cause_refusal(cause, repo_root)
    if cause_refusal is not None:
        found.append(cause_refusal)
    return found


def version_files(baselines_dir: Path, name: str) -> List[Tuple[int, Path]]:
    """The ``<name>.vNNNN.json`` files of one baseline, oldest first."""
    found = []
    for path in baselines_dir.glob(f"{name}.v*.json"):
        match = _VERSIONED_RE.match(path.name)
        if match and match.group("name") == name:
            found.append((int(match.group("version")), path))
    return sorted(found)


def _cause_kind(cause: str) -> str:
    if _TICKET_RE.match(cause):
        return "ticket"
    return "divergence" if _DIVERGENCE_RE.match(cause) else "pull_request"


def promote(
    candidate: Dict[str, Any],
    name: str,
    cause: Optional[str],
    baselines_dir: Path = DEFAULT_BASELINES_DIR,
    note: str = "",
    repo_root: Path = REPO_ROOT,
) -> Path:
    """Write the next version of baseline ``name`` from ``candidate`` (a record dict) and return its path.

    Raises ``ValueError`` listing every refusal when the candidate may not be promoted; nothing is written then.
    """
    reasons: List[Refusal] = []
    if not _NAME_RE.match(name):
        reasons.append(Refusal("bad_name", f"baseline name {name!r} must match {_NAME_RE.pattern}"))
    try:
        record = _load_record(candidate)
    except (BenchmarkRecordError, KeyError, TypeError, AttributeError) as exc:
        raise ValueError(_format([*reasons, Refusal("invalid_candidate", f"not a valid BenchmarkRecord: {exc}")])) from None
    reasons.extend(refusals(record, cause, repo_root))
    if reasons:
        raise ValueError(_format(reasons))

    previous = version_files(baselines_dir, name)
    before: Optional[Dict[str, Any]] = None
    if previous:
        last_version, last_path = previous[-1]
        last_record = _load_record(json.loads(last_path.read_text(encoding="utf-8")))
        digest = record_digest(last_record)
        record = dataclasses.replace(
            record,
            identity=dataclasses.replace(
                record.identity, baseline_ref=BaselineRef(id=f"{name}.v{last_version:04d}", schema_version=last_record.schema_version, record_digest=digest)
            ),
        )
        before = {"file": last_path.name, "record_digest": digest, "identity": last_record.to_dict()["identity"]}
    else:
        record = dataclasses.replace(record, identity=dataclasses.replace(record.identity, baseline_ref=None))
    version = previous[-1][0] + 1 if previous else 1

    payload = record.to_dict()
    payload["promotion"] = {
        "name": name,
        "version": version,
        "cause": {"kind": _cause_kind(str(cause).strip()), "id": str(cause).strip()},
        "note": note,
        "promoted_at": datetime.now(timezone.utc).isoformat(),
        "before": before,
        "after": {"record_digest": record_digest(record), "identity": record.to_dict()["identity"]},
    }
    baselines_dir.mkdir(parents=True, exist_ok=True)
    path = baselines_dir / f"{name}.v{version:04d}.json"
    with open(path, "x", encoding="utf-8") as handle:  # "x": never overwrite an existing version
        handle.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return path


def _format(reasons: Sequence[Refusal]) -> str:
    return "\n".join(f"REFUSED: {r.code}: {r.message}" for r in reasons)


def _check_promoted(path: Path, record: BenchmarkRecord, data: Dict[str, Any], baselines_dir: Path) -> List[str]:
    match = _VERSIONED_RE.match(path.name)
    assert match is not None
    name, version = match.group("name"), int(match.group("version"))
    problems: List[str] = []
    promotion = data.get("promotion")
    if not isinstance(promotion, dict) or not promotion.get("cause", {}).get("id"):
        problems.append(f"{path.name}: a versioned baseline needs a promotion object with a cited cause")
    ref = record.identity.baseline_ref
    if version == 1:
        if ref is not None:
            problems.append(f"{path.name}: version 1 must have no baseline_ref")
        return problems
    prior = baselines_dir / f"{name}.v{version - 1:04d}.json"
    if not prior.exists():
        return [*problems, f"{path.name}: the previous version {prior.name} is missing"]
    if ref is None:
        return [*problems, f"{path.name}: baseline_ref is missing"]
    try:
        expected = record_digest(_load_record(json.loads(prior.read_text(encoding="utf-8"))))
    except (BenchmarkRecordError, ValueError, KeyError, TypeError):
        return [*problems, f"{path.name}: the previous version {prior.name} is not a valid record"]
    if ref.id != prior.stem or ref.record_digest != expected:
        problems.append(f"{path.name}: baseline_ref does not match {prior.name} (the chain is broken or {prior.name} was edited)")
    return problems


def check(baselines_dir: Path = DEFAULT_BASELINES_DIR) -> List[str]:
    """Problems in a baselines directory; an empty list means every file is a valid record or a listed legacy reference."""
    problems: List[str] = []
    for path in sorted(baselines_dir.glob("*.json")):
        if path.name in LEGACY_TRIPWIRE_REFERENCES:
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            record = _load_record(data)
        except (BenchmarkRecordError, ValueError, KeyError, TypeError, AttributeError) as exc:
            problems.append(f"{path.name}: neither a valid BenchmarkRecord nor a listed legacy tripwire reference ({exc})")
            continue
        if _VERSIONED_RE.match(path.name):
            problems.extend(_check_promoted(path, record, data, baselines_dir))
    return problems


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)
    promote_parser = sub.add_parser("promote", help="write the next versioned baseline from a candidate record")
    promote_parser.add_argument("--candidate", required=True, type=Path, help="JSON file holding a BenchmarkRecord (to_dict form)")
    promote_parser.add_argument("--name", required=True, help="baseline name, e.g. idle_100_local")
    promote_parser.add_argument("--cause", default="", help="ticket id, DEV-nnn or PR #n that justifies the new baseline")
    promote_parser.add_argument("--note", default="", help="free-text reason, recorded in the promotion")
    for sp in (promote_parser, sub.add_parser("check", help="verify a baselines directory")):
        sp.add_argument("--baselines-dir", type=Path, default=DEFAULT_BASELINES_DIR)
    promote_parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    """CLI entry point. Returns the exit code (see the module docstring)."""
    args = _build_parser().parse_args(argv)
    if args.command == "check":
        problems = check(args.baselines_dir)
        for problem in problems:
            print(f"PROBLEM: {problem}", file=sys.stderr)
        return 1 if problems else 0
    try:
        candidate = json.loads(args.candidate.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"cannot read candidate {args.candidate}: {exc}", file=sys.stderr)
        return 1
    try:
        path = promote(candidate, args.name, args.cause, args.baselines_dir, args.note, args.repo_root)
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 2
    print(f"PROMOTED: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
