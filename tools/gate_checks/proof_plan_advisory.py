"""Advisory presence check for a ticket's `test_plan.md` `## Proof Plan` section
(TCK-20260930-DONE-CHECKER-PROOF-PLAN-ADVISORY, test-architecture Epic C criteria 1-2).

Report-only, like `doc_staleness_check.py` / `epic_staleness_check.py`: `check_proof_plan_fields()`
returns `(status, evidence)` with status `OK` / `WARN` / `NA` and never raises or returns a
blocking verdict. The Proof Plan is advisory during the pilot (`.claude/agents/investigator.md`
`## Proof Plan`); whether it becomes required is a post-pilot decision, so nothing here feeds a
gate.

Presence only: a mandatory field counts as present when its name appears (a table column with a
non-empty cell, or a `name: value` line in a per-criterion block). Whether the value is *right* is
not judged. `oracle: unresolved` is a filled value by design (the investigator prose asks for it
when the document is silent).
"""

import re
from pathlib import Path

# Single list of the mandatory per-criterion fields, mirrored from the investigator prose. A test
# asserts every name here still appears in `.claude/agents/investigator.md`'s Proof Plan section, so
# the two cannot drift apart silently.
MANDATORY_FIELDS = ("level", "proof kind", "oracle source", "expected effect", "selected commands")

_TIERS_CHECKED = ("standard",)


def _proof_plan_section(text: str) -> str | None:
    match = re.search(r"^## Proof Plan[ \t]*$", text, re.MULTILINE)
    if match is None:
        return None
    rest = text[match.end():]
    nxt = re.search(r"^## ", rest, re.MULTILINE)
    return (rest[: nxt.start()] if nxt else rest).strip()


def _norm(cell: str) -> str:
    return re.sub(r"[*`_]", "", cell).strip().lower()


def _table_rows(lines: list[str]) -> list[list[str]]:
    rows = []
    for line in lines:
        s = line.strip()
        if s.startswith("|") and s.endswith("|"):
            cells = [c.strip() for c in s.strip("|").split("|")]
            if all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
                continue  # separator row
            rows.append(cells)
    return rows


def _missing_in_table(rows: list[list[str]]) -> list[tuple[str, list[str]]]:
    if not rows:
        return []
    header = [_norm(c) for c in rows[0]]
    col = {f: header.index(f) for f in MANDATORY_FIELDS if f in header}
    findings = []
    data = rows[1:]
    if not data:
        return [("(no criterion rows)", list(MANDATORY_FIELDS))]
    for cells in data:
        label = f"AC {cells[0]}" if cells and cells[0] else "row"
        missing = [
            f for f in MANDATORY_FIELDS
            if f not in col or col[f] >= len(cells) or not cells[col[f]].strip()
        ]
        if missing:
            findings.append((label, missing))
    return findings


def _missing_in_block(block: str) -> list[str]:
    missing = []
    for f in MANDATORY_FIELDS:
        pat = re.compile(rf"(?im)^[\s>*\-\d.]*\**{re.escape(f)}\**\s*[:—\-]?\**\s*(\S.*)$")
        if not pat.search(block):
            missing.append(f)
    return missing


def _closed_by_disposition(ticket_id: str, tickets_dir: Path) -> bool:
    """A ticket closed with a `## Disposition` (no implementation) has no test_plan.md by design."""
    candidates = [tickets_dir / "inprogress" / f"{ticket_id}.md", *sorted((tickets_dir / "done").rglob(f"{ticket_id}.md"))]
    for path in candidates:
        try:
            if re.search(r"^## Disposition[ \t]*$", path.read_text(encoding="utf-8"), re.MULTILINE):
                return True
        except OSError:
            continue
    return False


def check_proof_plan_fields(
    ticket_id: str,
    tier: str,
    staging_dir: Path = Path("staging_artifacts"),
    stored_dir: Path = Path("stored_artifacts"),
    tickets_dir: Path = Path("tickets"),
) -> tuple[str, str]:
    """Return `(status, evidence)`; status is `OK`, `WARN` or `NA`. Never raises."""
    if tier not in _TIERS_CHECKED:
        return ("NA", f"{tier} tier - no per-criterion test_plan.md Proof Plan expected")
    try:
        if _closed_by_disposition(ticket_id, tickets_dir):
            return ("NA", "closed with a ## Disposition (no implementation) - no test_plan.md expected")
        path = next(
            (p for p in (staging_dir / ticket_id / "test_plan.md", stored_dir / ticket_id / "test_plan.md")
             if p.exists()),
            None,
        )
        if path is None:
            return ("WARN", f"no test_plan.md under {staging_dir}/ or {stored_dir}/ for {ticket_id}")
        section = _proof_plan_section(path.read_text(encoding="utf-8"))
        if section is None:
            return ("WARN", f"{path}: no '## Proof Plan' section; missing all of: {', '.join(MANDATORY_FIELDS)}")

        lines = section.splitlines()
        rows = _table_rows(lines)
        blocks = re.split(r"(?m)^### ", section)[1:]
        findings: list[tuple[str, list[str]]] = []
        if rows:
            findings = _missing_in_table(rows)
        elif blocks:
            for b in blocks:
                head = b.splitlines()[0].strip() if b.strip() else "block"
                miss = _missing_in_block(b)
                if miss:
                    findings.append((head, miss))
        else:
            nonempty = [ln for ln in lines if ln.strip()]
            if len(nonempty) <= 1:
                return ("OK", f"{path}: Proof Plan declares no testable acceptance criterion (one-line statement)")
            miss = _missing_in_block(section)
            if miss:
                findings.append(("Proof Plan", miss))

        if not findings:
            return ("OK", f"{path}: all mandatory Proof Plan fields present")
        detail = "; ".join(f"{label}: missing {', '.join(m)}" for label, m in findings)
        return ("WARN", f"{path}: {detail}")
    except Exception as exc:  # advisory: never propagate
        return ("WARN", f"could not evaluate Proof Plan for {ticket_id}: {exc}")
