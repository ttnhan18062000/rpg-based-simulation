"""Advisory check: a path a closing ticket cites must be in git, not silently gitignored
(TCK-20260930-CITED-EVIDENCE-PATH-GITIGNORE-CHECK).

`.gitignore` drops `stored_artifacts/**/*.json` (only `manifest.json` is excepted), so evidence
written as `.json` passes locally and is missing from a clean checkout: PR #270's first CI run failed
that way. Report-only, in the style of `proof_plan_advisory.py`: `check_cited_evidence_paths()`
returns `(status, evidence)` with status `OK` / `WARN` / `NA`, never raises, never blocks.

Citations are the backticked tokens of the ticket body that start with `stored_artifacts/`,
`staging_artifacts/` or `tickets/` and end in a file extension. Wildcards and `{placeholder}` forms
are skipped. A path written in plain prose or a markdown link is never checked. A cited path that does not exist on disk is skipped (a ticket cites its own
`tickets/inprogress/` path, which is skipped outright, and `staging_artifacts/` paths that migrate
to `stored_artifacts/` at close); a `staging_artifacts/X` citation is checked at `stored_artifacts/X` once migrated.
"""

import re
import subprocess
from pathlib import Path

_PREFIXES = ("stored_artifacts/", "staging_artifacts/", "tickets/")
_TICKS = re.compile(r"`([^`\n]+)`")


def _ticket_text(ticket_id: str, root: Path) -> str | None:
    tickets = root / "tickets"
    candidates = [tickets / "inprogress" / f"{ticket_id}.md", *sorted((tickets / "done").rglob(f"{ticket_id}.md"))]
    for path in candidates:
        try:
            return path.read_text(encoding="utf-8")
        except OSError:
            continue
    return None


def cited_paths(text: str) -> list[str]:
    """Backticked repo paths under the tracked-evidence roots, in first-seen order, de-duplicated."""
    seen: dict[str, None] = {}
    for token in _TICKS.findall(text):
        token = token.strip()
        if not token.startswith(_PREFIXES) or any(c in token for c in "*{}<> \t"):
            continue
        if not re.search(r"\.[A-Za-z0-9]+$", token):
            continue
        seen.setdefault(token)
    return list(seen)


def _resolve_on_disk(rel: str, root: Path) -> str | None:
    if (root / rel).is_file():
        return rel
    if rel.startswith("staging_artifacts/"):
        migrated = "stored_artifacts/" + rel[len("staging_artifacts/"):]
        if (root / migrated).is_file():
            return migrated
    return None


def _git(args: list[str], root: Path) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, timeout=30)


def check_cited_evidence_paths(ticket_id: str, tier: str = "", root: Path = Path(".")) -> tuple[str, str]:
    """Return `(status, evidence)`; status is `OK`, `WARN` or `NA`. Never raises. `tier` is accepted
    for signature parity with the other advisories and not used: every tier can cite evidence."""
    try:
        text = _ticket_text(ticket_id, root)
        if text is None:
            return ("NA", f"no ticket file found for {ticket_id}")
        own = f"{ticket_id}.md"
        cited = [c for c in cited_paths(text) if not (c.startswith("tickets/") and c.endswith("/" + own))]
        paths = [p for p in (_resolve_on_disk(c, root) for c in cited) if p]
        if not paths:
            return ("NA", "no cited evidence path exists on disk")
        ignored_proc = _git(["check-ignore", "-v", "--", *paths], root)
        if ignored_proc.returncode not in (0, 1):
            return ("WARN", f"could not run git check-ignore: {ignored_proc.stderr.strip()}")
        ignored: dict[str, str] = {}
        for line in ignored_proc.stdout.splitlines():
            rule, _, path = line.partition("\t")
            ignored[path] = rule.split(":", 2)[-1] if rule.count(":") >= 2 else rule
        tracked_proc = _git(["ls-files", "--", *paths], root)
        if tracked_proc.returncode != 0:
            return ("WARN", f"could not run git ls-files: {tracked_proc.stderr.strip()}")
        tracked = set(tracked_proc.stdout.splitlines())
        findings = []
        for p in paths:
            if p in ignored and p not in tracked:
                findings.append(f"{p}: gitignored by rule `{ignored[p]}` (absent from a clean checkout; store as .jsonl)")
            elif p not in tracked:
                findings.append(f"{p}: not tracked by git (git add it before the closing commit)")
        if not findings:
            return ("OK", f"all {len(paths)} cited evidence path(s) are tracked by git")
        return ("WARN", "; ".join(findings))
    except Exception as exc:  # advisory: never propagate
        return ("WARN", f"could not evaluate cited evidence paths for {ticket_id}: {exc}")
