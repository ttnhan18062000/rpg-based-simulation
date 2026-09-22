#!/usr/bin/env python3
"""
Report-only scan for an entry whose own `verified.note` prose names an instrument/verdict value
that contradicts its own structured `verified.instrument`/`verified.verdict` fields.

TCK-20260921-MECHANISM-PROGRESSION-VALUE-DIFFERENTIAL-INSTRUMENT. Registry narrative and registry
data have now disagreed twice, by two different mechanical causes, with the identical symptom:

1. A duplicate YAML key (`strategic_intelligence_core`, Program A) left `yaml.safe_load()` keeping
   the LAST (stale, `code_trace`) value of a `verified:` block despite every prose sentence in the
   surviving note claiming `scenario` -- caught only by hand arithmetic disagreeing with the
   registry's own count. `check_duplicate_keys()` (`registry.py`) now catches that specific cause
   (a repeated mapping key), but it cannot catch this one:
2. Three addenda (`aging_death`, `succession`, `entity_role`, this same program, waves 2-3) each
   said "instrument upgraded `code_trace` -> `scenario`" in prose, but the edit that should have
   changed the `instrument:` field itself was never made -- no duplicate key, no parse-time data
   loss, just an editing miss. Caught only by a close-out's own arithmetic cross-check disagreeing
   with the registry's structured field count.

Different causes, identical shape: the note said one thing, the field said another, and nothing
noticed either time until a human did the arithmetic by hand -- exactly the kind of catch that
does not repeat reliably. This scan looks for the specific, already-established idiom this
registry's own edit history uses for stating a transition -- `instrument ... -> WORD` / `verdict
... -> WORD` (four real prior instances of exactly this phrasing were found in the corpus before
writing this scanner: `grep -n "instrument upgraded" registries/mechanisms.yaml`) -- and flags any
case where the transition's own claimed destination does not match the entry's current field.

Report-only, same convention as `mechanism_status_language_check.py` (which this scanner's
approach mirrors, pointed inward at the registry's own prose instead of outward at the atlas/
capabilities pages) -- never fails the build. Prose legitimately discusses history and other
mechanisms' verdicts (e.g. "see `xp_leveling`'s own verified block"), so false positives are
expected; a blocking gate here would push authors toward vaguer notes, the wrong direction
(`docs/plans/mechanism_claims_as_tests_initiative.md` §4.1's report-first rule).

Usage:
  python3 tools/mechanism_registry/mechanism_prose_field_drift_check.py
  python3 tools/mechanism_registry/mechanism_prose_field_drift_check.py --registry path/to/other.yaml
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import yaml

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_DEFAULT_REGISTRY_PATH = _REPO_ROOT / "registries" / "mechanisms.yaml"

# Same vocabulary the registry's own validator treats as canonical (registry.py's
# VALID_INSTRUMENTS/VALID_VERDICTS) -- kept as a local literal rather than imported, so this
# report-only scanner has no import-time dependency on registry.py's own blocking validation path.
_VALID_INSTRUMENTS = frozenset({"code_trace", "census", "scenario", "corpus_run"})
_VALID_VERDICTS = frozenset({"observed", "contradicted", "inconclusive"})

# Matches "instrument ... -> WORD" / "verdict ... -> WORD" within a short window, tolerating
# backticks/spaces around the destination word (the corpus's own established idiom, e.g.
# "instrument upgraded `code_trace` -> `scenario`", "verdict correction, observed -> contradicted").
_TRANSITION_RE = re.compile(
    r"\b(instrument|verdict)\b[^\n]{0,80}?->\s*`?([A-Za-z_]+)`?", re.IGNORECASE
)


@dataclass(frozen=True)
class Hit:
    mechanism_id: str
    field: str  # "instrument" or "verdict"
    claimed: str
    actual: Optional[str]
    snippet: str


def _snippet(text: str, match: re.Match, radius: int = 30) -> str:
    start = max(0, match.start() - radius)
    end = min(len(text), match.end() + radius)
    return text[start:end].replace("\n", " ")


def _load_mechanisms(registry_path: Path) -> List[dict]:
    with open(registry_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data.get("mechanisms", data) if isinstance(data, dict) else data


def check(mechanisms: List[dict]) -> List[Hit]:
    hits: List[Hit] = []
    for mech in mechanisms:
        verified = mech.get("verified") or {}
        note = verified.get("note") or ""
        if not note:
            continue
        actual_instrument = verified.get("instrument")
        actual_verdict = verified.get("verdict")

        # The note is append-only across dated addenda -- the LAST transition claim for a given
        # field is the one that should match the current field, not any earlier (already-
        # superseded) transition mentioned along the way.
        last_claim = {}
        for m in _TRANSITION_RE.finditer(note):
            field = m.group(1).lower()
            claimed = m.group(2).lower()
            valid_set = _VALID_INSTRUMENTS if field == "instrument" else _VALID_VERDICTS
            if claimed not in valid_set:
                continue  # not a real enum value -- likely an unrelated "-> something" in prose
            last_claim[field] = (claimed, m)

        if "instrument" in last_claim:
            claimed, m = last_claim["instrument"]
            if claimed != actual_instrument:
                hits.append(Hit(
                    mechanism_id=mech["id"], field="instrument", claimed=claimed,
                    actual=actual_instrument, snippet=_snippet(note, m),
                ))
        if "verdict" in last_claim:
            claimed, m = last_claim["verdict"]
            if claimed != actual_verdict:
                hits.append(Hit(
                    mechanism_id=mech["id"], field="verdict", claimed=claimed,
                    actual=actual_verdict, snippet=_snippet(note, m),
                ))
    return hits


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=_DEFAULT_REGISTRY_PATH)
    args = parser.parse_args()

    mechanisms = _load_mechanisms(args.registry)
    hits = check(mechanisms)

    print(f"Prose/field drift scan (report-only, never fails): {len(hits)} hit(s) across "
          f"{len(mechanisms)} mechanism(s)")
    for h in hits:
        print(f"  [{h.mechanism_id}] note claims {h.field}={h.claimed!r}, "
              f"field actually reads {h.actual!r}: ...{h.snippet}...")
    return 0  # Always 0 -- this check never fails the build.


if __name__ == "__main__":
    sys.exit(main())
