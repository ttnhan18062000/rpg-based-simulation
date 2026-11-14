#!/usr/bin/env python3
"""Report role cards that cite an amended decision without citing the doc that amends it.

Report-only: always exits 0. A card source (docs/guidelines/session_roles/{domains,functions}/*.md) lists the
decisions it uses under `## Cites`. A finding is: the card cites C, an active doc D has `amends:` covering C,
and the card does not also cite D. Seat ids come from the roster. Run
`python3 -m tools.sessions.card_citation_check`; `generate_agents --check` prints one advisory line when
this finds anything.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

from tools.sessions.decisions import (
    TEMPLATE_DIR,
    amending_docs,
    covers,
    load_decisions,
    parse_cites,
    split_target,
)
from tools.sessions.roster import REPO_ROOT, load_roster

ADVISORY_SEAT_LIMIT = 4


@dataclass(frozen=True)
class Finding:
    card: str  # repo-relative path of the card source
    cited: str  # vocabulary short name the card cites
    amended_by: str  # path of the amending doc, or a problem text
    seats: tuple[str, ...]
    kind: str = "amended"  # amended | unlisted-amender | malformed

    def render(self, seat_limit: int | None = None) -> str:
        seats = list(self.seats)
        shown = seats if seat_limit is None or len(seats) <= seat_limit else seats[:seat_limit]
        more = f" (+{len(seats) - len(shown)} more)" if len(shown) < len(seats) else ""
        seat_text = ", ".join(shown) + more
        if self.kind == "malformed":
            return f"{self.amended_by}: {self.cited} (affects seats: {seat_text})"
        if self.kind == "unlisted-amender":
            return (
                f"{self.amended_by} amends {self.cited} but has no entry in registries/session_decisions.yaml; "
                f"{self.card} cites {self.cited} (seats: {seat_text})"
            )
        return f"{self.card} cites {self.cited}, amended by {self.amended_by} (seats: {seat_text})"


def _seats(root: Path, card_rel: str) -> tuple[str, ...]:
    kind, _, name = Path(card_rel).relative_to(TEMPLATE_DIR).as_posix().partition("/")
    stem = Path(name).stem
    roster = load_roster(root)
    if kind == "domains":
        return tuple(r.role for r in roster.roles if r.domain == stem)
    return tuple(r.role for r in roster.roles if r.function == stem)


def find_findings(root: Path = REPO_ROOT) -> list[Finding]:
    vocab = load_decisions(root)
    amenders = amending_docs(root)
    by_path = {d.path: d.name for d in vocab.values()}
    findings: list[Finding] = []
    for card in sorted((root / TEMPLATE_DIR).glob("*/*.md")):
        if card.parent.name not in ("domains", "functions"):
            continue
        rel = card.relative_to(root).as_posix()
        cites = parse_cites(card.read_text(encoding="utf-8"))
        if not cites:
            continue
        cited_targets = {name: (vocab[name].target if name in vocab else split_target(t)[0]) for name, t in cites.items()}
        cited_paths = {split_target(t)[0] for t in cited_targets.values()}
        seats = _seats(root, rel)
        for amender in amenders:
            if amender.problem:
                findings.append(Finding(rel, amender.doc, amender.problem, seats, "malformed"))
                continue
            hit = next(
                (name for name, target in cited_targets.items() if any(covers(a, target) for a in amender.targets)), None
            )
            if hit is None or amender.doc in cited_paths:
                continue
            kind = "amended" if amender.doc in by_path else "unlisted-amender"
            findings.append(Finding(rel, hit, amender.doc, seats, kind))
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--root", type=Path, default=REPO_ROOT)
    args = parser.parse_args(argv)
    findings = find_findings(args.root)
    for f in findings:
        print(f"CITATION {f.render()}")
    print(f"{len(findings)} citation finding(s) (report-only)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
