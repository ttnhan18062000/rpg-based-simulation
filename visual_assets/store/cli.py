"""Command line for the store: `python -m visual_assets.store <command>`.

Commands so far (all local, none adopts anything): `intake <dir>`, `review <id>`, `list`, `show <id>`.
Exit codes: 0 success (a PASSED intake), 1 a QUARANTINED intake, 2 a refusal or error. This is the only module that
reads the clock; library code takes timestamps as parameters.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from datetime import datetime, timezone

from visual_assets.store import intake as intake_api
from visual_assets.store.contracts.base import IntakeVerdict
from visual_assets.store.contracts.intake import IntakeResult
from visual_assets.store.errors import StoreError


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _print_result(result: IntakeResult) -> None:
    print(f"{result.intake_id}  {result.verdict.value}  candidate {result.candidate_id}")
    for finding in result.findings:
        print(f"  {finding.code.value}: {finding.detail}")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m visual_assets.store", description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("intake", help="stage and validate a candidate package directory").add_argument("directory")
    sub.add_parser("review", help="export a PASSED intake's preview and summary to the local review area").add_argument("intake_id")
    sub.add_parser("list", help="list quarantined intake results")
    sub.add_parser("show", help="print one intake result").add_argument("intake_id")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "intake":
            result = intake_api.intake(args.directory, created_at=_now())
            _print_result(result)
            return 0 if result.verdict is IntakeVerdict.PASSED else 1
        if args.command == "review":
            print(intake_api.review(args.intake_id))
            return 0
        if args.command == "show":
            _print_result(intake_api.show(args.intake_id))
            return 0
        results, problems = intake_api.list_results()
        for result in results:
            print(f"{result.intake_id}  {result.verdict.value}  candidate {result.candidate_id}  {result.created_at}")
        for name in problems:
            print(f"{name}  UNREADABLE")
        return 0
    except StoreError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
