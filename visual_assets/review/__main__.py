"""`python -m visual_assets.review evaluate|review-sheets --set <id>`: the one supported command for judging and reviewing a draft set.

    evaluate       prints the evidence (sheet rule, lint, measurements, compliance where the set has it) as JSON; the verdict is the recorded output, never a test
    review-sheets  writes the owner's review folder (six labelled PNG canvases and a README with the exact owner commands) outside every repository
    key-usage      REPORT ONLY: which visual keys the code references against the registry, the adopted sources and the latest release candidate

Read-only on the drafts and the catalog records. `python -m visual_assets.store` is untouched (it owns the human gates).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from visual_assets.review import key_usage, review_sheets, sets
from visual_assets.review.sprites import DRAFTS


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m visual_assets.review", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    evaluate = sub.add_parser("evaluate", help="print the evidence of one draft set as JSON")
    evaluate.add_argument("--set", dest="set_id", required=True, help="one of: " + ", ".join(sets.SET_IDS))
    evaluate.add_argument("--drafts-root", type=Path, default=DRAFTS, help="default: visual_assets/drafts")
    evaluate.add_argument("--recorded", action="store_true", help="print the exact text committed as the frontend fixture's rule_result.json (sorted keys)")
    review_sheets.add_arguments(sub.add_parser("review-sheets", help="write the owner review folder for one draft set"))
    sub.add_parser("key-usage", help="report which visual keys the code references against the registry, the adopted sources and the latest release candidate (report only, exit 0)")
    args = parser.parse_args(argv)
    if args.command == "review-sheets":
        return review_sheets.run(args)
    if args.command == "key-usage":
        sys.stdout.write(key_usage.report_json())
        return 0
    try:
        sys.stdout.write(sets.evaluation_json(args.set_id, args.drafts_root, recorded=args.recorded))
    except sets.UnknownSet as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
