"""Keep one rolling GitHub issue for the `Slow regression` workflow's failing set, and decide the run's verdict.

Built for TCK-20261001-SIMQ-GRADE-ANCHORS-RED-ON-MAIN-UNREPORTED (Reporting-Path Design P2, and "Reporting-path
hardening (2026-10-07, research-backed)", ranks 1-4 of `CI known failure tracking patterns.md`).

Reads the JUnit XML the three slow steps write, computes the failing set, compares it with the set recorded in
the tracker issue (a fenced JSON block in the body), comments when the set changes (`NEW:` / `FIXED:`), posts a
weekly digest, and exits non-zero only when something needs a human.

Rules:
- A test is red when its JUnit testcase has a `<failure>` or `<error>` child. A strict XPASS is recorded by pytest
  as a failure, so it counts. `<skipped>` (skip and xfail) is not red.
- Tracker issue (rank 1): found through the REST issues list, never by search. It is an open issue with the label
  `slow-regression`, created by `github-actions[bot]`, whose body carries `<!-- slow-regression-tracker -->`. More
  than one such issue is an error. An unmarked issue is not a tracker, whoever created it.
- First run (no tracker): create the issue with the full current set and post NO per-test comments.
- A closed issue is not reopened: a recurrence after closing creates a NEW issue, by design.
- A step that produced no JUnit file is "missing", and an expected corpus id with no result is "unmeasured":
  their previous state is carried over (never reported FIXED) and the issue is not closed.
- `slow_known_reds.yaml` entries carry owner, added_on, expires_on and kind. A failing test resolves to the FIRST
  entry whose pattern matches, so a narrower entry must precede any broader one covering it (the lint rejects a
  shadowed entry). A failing test matching no entry is UNOWNED; one matching an entry past `expires_on` is EXPIRED
  and listed under its own heading.
- Exit status (rank 4): 1 when a failing test is UNOWNED or EXPIRED, when a step is missing or a corpus id is
  unmeasured, or when GitHub cannot be reached (a `::error` annotation is printed). Otherwise 0, so a run whose
  every red is mapped and in date is green; a NEW mapped red still gets its NEW comment but does not fail the job.
- Weekly digest (rank 3): the first run in each ISO week posts one comment carrying
  `<!-- slow-regression-digest YYYY-Www -->`; it is not re-posted in the same week.
- `first_seen` is kept in the state block. When a previous state has none, every id in it is seeded from the
  issue's created_at, so the digest column says "tracked since", not "first seen".

GitHub access goes through a small client object (`GhClient` shells out to the `gh` CLI), so the logic is tested
with a fake client.
"""

from __future__ import annotations

import argparse
import datetime as dt
import fnmatch
import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Set, Tuple

import yaml

LABEL = "slow-regression"
BOT_LOGIN = "github-actions[bot]"
TRACKER_MARKER = "<!-- slow-regression-tracker -->"
DIGEST_MARKER_FMT = "<!-- slow-regression-digest {week} -->"
STEP_BY_FILE_PREFIX = (
    ("corpus_", "corpus diversity"),
    ("slow_tests", "slow tests"),
    ("legacy_regression", "legacy regression"),
)
EXPECTED_STEPS = tuple(step for _, step in STEP_BY_FILE_PREFIX)
REQUIRED_ENTRY_FIELDS = ("match", "ticket", "owner", "added_on", "expires_on", "kind")
KINDS = ("broken", "flaky")
_STATE_RE = re.compile(r"```json\s*(\{.*?\})\s*```", re.S)


class TrackerError(Exception):
    """The tracker issue cannot be chosen unambiguously; reported as a ::error, exit 1."""


@dataclass
class Result:
    message: str
    reasons: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def exit_code(self) -> int:
        return 1 if self.reasons else 0


# ── JUnit ────────────────────────────────────────────────────────────────────────────────────


def step_for_file(name: str) -> Optional[str]:
    for prefix, step in STEP_BY_FILE_PREFIX:
        if name.startswith(prefix):
            return step
    return None


def node_to_junit_id(nodeid: str) -> str:
    """`a/b/test_x.py::Cls::test_f[p]` -> `a.b.test_x.Cls::test_f[p]` (pytest's JUnit classname::name)."""
    path, _, rest = nodeid.partition("::")
    parts = rest.split("::") if rest else []
    module = path[:-3].replace("/", ".") if path.endswith(".py") else path.replace("/", ".")
    if not parts:
        return module
    return ".".join([module, *parts[:-1]]) + "::" + parts[-1]


def load_expected_ids(junit_dir: Path) -> Set[str]:
    path = Path(junit_dir) / "corpus_expected.txt"
    if not path.exists():
        return set()
    return {node_to_junit_id(line.strip()) for line in path.read_text(encoding="utf-8").splitlines() if "::" in line}


def parse_junit_dir(junit_dir: Path) -> Tuple[Dict[str, str], Set[str], Set[str]]:
    """Return ({test id: step} for every red test, steps that produced at least one file, every measured id)."""
    failing: Dict[str, str] = {}
    seen: Set[str] = set()
    measured: Set[str] = set()
    for path in sorted(Path(junit_dir).glob("*.xml")):
        step = step_for_file(path.name)
        if step is None:
            continue
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError:
            continue  # a truncated file proves nothing: the step stays "missing"
        seen.add(step)
        for case in root.iter("testcase"):
            measured.add(f"{case.get('classname', '')}::{case.get('name', '')}")
            if case.find("failure") is not None or case.find("error") is not None:
                failing[f"{case.get('classname', '')}::{case.get('name', '')}"] = step
    return failing, seen, measured


# ── known reds ───────────────────────────────────────────────────────────────────────────────


def load_known_reds(path: Optional[Path]) -> List[dict]:
    if path is None or not Path(path).exists():
        return []
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    return list(data.get("known_reds", []))


def lint_known_reds(entries: Sequence[dict]) -> List[str]:
    """Problems with the YAML entries (a missing field, a bad date, expires_on before added_on, an unknown kind)."""
    problems: List[str] = []
    for index, entry in enumerate(entries):
        label = entry.get("match", f"entry {index}")
        for name in REQUIRED_ENTRY_FIELDS:
            if not entry.get(name):
                problems.append(f"{label}: missing {name}")
        dates = {}
        for name in ("added_on", "expires_on"):
            value = entry.get(name)
            if not value:
                continue
            try:
                dates[name] = dt.date.fromisoformat(str(value))
            except ValueError:
                problems.append(f"{label}: {name} is not an ISO date: {value!r}")
        if len(dates) == 2 and dates["expires_on"] < dates["added_on"]:
            problems.append(f"{label}: expires_on is before added_on")
        if entry.get("kind") and entry["kind"] not in KINDS:
            problems.append(f"{label}: kind must be one of {KINDS}, got {entry['kind']!r}")
        if "[" in str(entry.get("match", "")):
            # fnmatch reads `[...]` as a character class, so an exact parametrized id such as
            # `t::test_x[5000]` would never match itself and its failure would show as UNOWNED.
            problems.append(f"{label}: '[' is a character class in fnmatch; write the parameter part with '*' or '?' instead")
    problems.extend(shadowed_entries(entries))
    return problems


def _sample_id(pattern: str) -> str:
    """A concrete id the pattern matches: `*` -> nothing, `?` -> one character (the lint forbids `[` in patterns)."""
    return pattern.replace("*", "").replace("?", "x")


def shadowed_entries(entries: Sequence[dict]) -> List[str]:
    """Entries a test id can never reach, because owner_of() returns the first match and an earlier, broader
    pattern also matches the later entry's ids. A catch-all must come after every narrower entry it covers."""
    problems: List[str] = []
    for later_index, later in enumerate(entries):
        pattern = later.get("match")
        if not pattern:
            continue
        sample = _sample_id(pattern)
        for earlier in entries[:later_index]:
            if earlier.get("match") and fnmatch.fnmatchcase(sample, earlier["match"]):
                problems.append(f"{pattern}: shadowed by the earlier entry {earlier['match']!r}; move it before that entry")
                break
    return problems


def owner_of(test_id: str, known: Sequence[dict]) -> Optional[dict]:
    for entry in known:
        if fnmatch.fnmatchcase(test_id, entry["match"]):
            return entry
    return None


def is_expired(entry: dict, today: dt.date) -> bool:
    return dt.date.fromisoformat(str(entry["expires_on"])) < today


def days_to_expiry(entry: dict, today: dt.date) -> int:
    return (dt.date.fromisoformat(str(entry["expires_on"])) - today).days


def classify(failing: Dict[str, str], known: Sequence[dict], today: dt.date) -> Tuple[List[str], List[str]]:
    """(UNOWNED ids, EXPIRED ids) among the failing tests."""
    unowned, expired = [], []
    for test_id in sorted(failing):
        entry = owner_of(test_id, known)
        if entry is None:
            unowned.append(test_id)
        elif is_expired(entry, today):
            expired.append(test_id)
    return unowned, expired


def stale_mappings(failing: Dict[str, str], known: Sequence[dict]) -> List[dict]:
    return [e for e in known if not any(fnmatch.fnmatchcase(t, e["match"]) for t in failing)]


# ── issue body and state ─────────────────────────────────────────────────────────────────────


def render_body(
    failing: Dict[str, str],
    known: Sequence[dict],
    repo: str,
    run_id: str,
    sha: str,
    first_seen: Optional[Dict[str, str]] = None,
    today: Optional[dt.date] = None,
) -> str:
    today = today or dt.date.today()
    run_url = f"https://github.com/{repo}/actions/runs/{run_id}"
    lines = [TRACKER_MARKER]
    lines.append(f"Failing set of the `Slow regression` workflow, as of run [{run_id}]({run_url}) at `{sha[:12]}`.")
    lines.append("")
    unowned, expired = classify(failing, known, today)
    if expired:
        lines.append("### EXPIRED (counted as red until someone re-dates, fixes or removes the entry)")
        for test_id in expired:
            entry = owner_of(test_id, known)
            lines.append(f"- [{test_id}]({run_url}) — `{entry['ticket']}`, owner {entry['owner']}, expired {entry['expires_on']}")
        lines.append("")
    for step in EXPECTED_STEPS:
        ids = sorted(t for t, s in failing.items() if s == step)
        if not ids:
            continue
        lines.append(f"### {step} ({len(ids)})")
        for test_id in ids:
            entry = owner_of(test_id, known)
            owner = f"`{entry['ticket']}`" if entry else "**UNOWNED**"
            lines.append(f"- [{test_id}]({run_url}) — {owner}")
        lines.append("")
    stale = stale_mappings(failing, known)
    if stale:
        lines.append("### Stale mappings (mapped to a ticket but not failing; consider cleaning up)")
        lines.extend(f"- `{e['match']}` — `{e['ticket']}`" for e in stale)
        lines.append("")
    lines.append(f"Last seen: run [{run_id}]({run_url}) at `{sha[:12]}`.")
    lines.append("")
    state = {"failing": dict(sorted(failing.items())), "first_seen": dict(sorted((first_seen or {}).items()))}
    lines.append("```json")
    lines.append(json.dumps(state, indent=1, sort_keys=True))
    lines.append("```")
    return "\n".join(lines)


def parse_state(body: str) -> Optional[dict]:
    match = _STATE_RE.search(body or "")
    if not match:
        return None
    try:
        data = json.loads(match.group(1))
    except ValueError:
        return None
    if not isinstance(data, dict):
        return None
    return {"failing": dict(data.get("failing", {})), "first_seen": dict(data.get("first_seen", {}))}


def title_for(count: int) -> str:
    return f"Slow regression: {count} failing on main"


# ── tracker selection (rank 1) ───────────────────────────────────────────────────────────────


def select_tracker(issues: Sequence[dict]) -> Optional[dict]:
    """Return the tracker issue, or None. Raises TrackerError when more than one issue qualifies."""
    marked = [
        i for i in issues
        if i.get("user_login") == BOT_LOGIN
        and LABEL in (i.get("labels") or [])
        and TRACKER_MARKER in (i.get("body") or "")
    ]
    if len(marked) > 1:
        raise TrackerError(
            "more than one open tracker issue carries the marker: " + ", ".join(f"#{i['number']}" for i in marked)
        )
    return marked[0] if marked else None


# ── one run ──────────────────────────────────────────────────────────────────────────────────


def _week_key(today: dt.date) -> str:
    iso = today.isocalendar()
    return f"{iso[0]}-W{iso[1]:02d}"


def render_digest(
    failing: Dict[str, str],
    known: Sequence[dict],
    first_seen: Dict[str, str],
    today: dt.date,
    week: str,
) -> str:
    lines = [DIGEST_MARKER_FMT.format(week=week), f"Weekly digest, {week} ({len(failing)} failing).", ""]
    lines.append("| test | ticket | owner | kind | tracked since | age (days) | days to expiry | flags |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for test_id in sorted(failing):
        entry = owner_of(test_id, known)
        since = first_seen.get(test_id, "")
        try:
            age = (today - dt.datetime.fromisoformat(since).date()).days if since else ""
        except ValueError:
            age = ""
        if entry is None:
            lines.append(f"| `{test_id}` | — | — | — | {since[:10]} | {age} | — | UNOWNED |")
            continue
        left = days_to_expiry(entry, today)
        flag = "EXPIRED" if left < 0 else ""
        lines.append(
            f"| `{test_id}` | `{entry['ticket']}` | {entry['owner']} | {entry['kind']} | {since[:10]} | {age} | {left} | {flag} |"
        )
    stale = stale_mappings(failing, known)
    if stale:
        lines.append("")
        lines.append("Stale mappings (not failing): " + ", ".join(f"`{e['match']}`" for e in stale))
    return "\n".join(lines)


def run_report(
    client,
    failing: Dict[str, str],
    seen_steps: Set[str],
    known: Sequence[dict],
    repo: str,
    run_id: str,
    sha: str,
    unmeasured: Optional[Set[str]] = None,
    today: Optional[dt.date] = None,
    now: Optional[dt.datetime] = None,
) -> Result:
    """Apply one run's result to the tracker issue and return what was done plus why the run is red, if it is."""
    unmeasured = unmeasured or set()
    now = now or dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
    today = today or now.date()
    now_iso = now.isoformat()
    missing = [s for s in EXPECTED_STEPS if s not in seen_steps]

    issue = select_tracker(client.list_issues())
    warnings: List[str] = []
    previous = parse_state(issue["body"]) if issue else None

    if previous is not None and (missing or unmeasured):
        # Carry over what we cannot re-measure this run (a missing step, or an expected anchor with no result).
        for test_id, step in previous["failing"].items():
            if test_id not in failing and (step in missing or test_id in unmeasured):
                failing = {**failing, test_id: step}

    # first_seen: carried forward; seeded from the issue's created_at when the old state has none.
    prior_first_seen: Dict[str, str] = {}
    if previous is not None:
        prior_first_seen = dict(previous["first_seen"])
        if not prior_first_seen and previous["failing"]:
            seed = (issue or {}).get("created_at") or now_iso
            prior_first_seen = {test_id: seed for test_id in previous["failing"]}
    first_seen = {test_id: prior_first_seen.get(test_id, now_iso) for test_id in failing}

    unowned, expired = classify(failing, known, today)
    reasons: List[str] = []
    if unowned:
        reasons.append(f"{len(unowned)} failing test(s) with no known-reds entry (UNOWNED): " + ", ".join(unowned[:5]))
    if expired:
        reasons.append(f"{len(expired)} failing test(s) under an EXPIRED entry: " + ", ".join(expired[:5]))
    if missing:
        reasons.append("steps with no JUnit result: " + ", ".join(missing))
    if unmeasured:
        reasons.append(f"{len(unmeasured)} expected test(s) with no result")

    body = render_body(failing, known, repo, run_id, sha, first_seen, today)

    if issue is None:
        if not failing:
            return Result("no open tracker issue and nothing failing: nothing to do", reasons, warnings)
        client.create_issue(title_for(len(failing)), body)
        return Result(f"first run: created the issue with {len(failing)} failing, no per-test comments", reasons, warnings)

    if previous is None:
        client.update_issue(issue["number"], title_for(len(failing)), body)
        return Result("issue state block unreadable: refreshed the body, no comments", reasons, warnings)

    new = sorted(set(failing) - set(previous["failing"]))
    fixed = sorted(set(previous["failing"]) - set(failing))
    comment_lines = []
    if new:
        comment_lines.append("NEW: " + ", ".join(f"`{t}` ({failing[t]})" for t in new))
    if fixed:
        comment_lines.append("FIXED: " + ", ".join(f"`{t}`" for t in fixed))
    if missing:
        comment_lines.append("Steps with no result this run: " + ", ".join(missing))
    if unmeasured:
        comment_lines.append(f"Expected tests with no result this run: {len(unmeasured)} (previous state carried over)")
    changed = bool(new or fixed)
    if changed:
        comment_lines.append(f"Run {run_id}, head `{sha}`.")
        client.comment(issue["number"], "\n".join(comment_lines))

    week = _week_key(today)
    digest_marker = DIGEST_MARKER_FMT.format(week=week)
    if failing and not any(digest_marker in text for text in client.list_comment_bodies(issue["number"])):
        client.comment(issue["number"], render_digest(failing, known, first_seen, today, week))

    if not failing and not missing and not unmeasured:
        client.update_issue(issue["number"], title_for(0), body)
        client.close_issue(issue["number"])
        return Result("failing set is empty: closed the issue", reasons, warnings)
    client.update_issue(issue["number"], title_for(len(failing)), body)
    summary = "set changed: commented and refreshed" if changed else "set unchanged: refreshed 'last seen' only"
    return Result(summary, reasons, warnings)


class GhClient:
    """The `gh` CLI as a client. Needs GH_TOKEN in the environment and `issues: write`."""

    def __init__(self, repo: str) -> None:
        self.repo = repo

    def _gh(self, *args: str) -> str:
        return subprocess.run(["gh", *args], check=True, capture_output=True, text=True).stdout

    def list_issues(self) -> List[dict]:
        self._gh("label", "create", LABEL, "--repo", self.repo, "--force", "--description", "Slow regression failing set")
        out = self._gh(
            "api", f"repos/{self.repo}/issues?labels={LABEL}&state=open&per_page=100", "--paginate"
        )
        # `--paginate` concatenates one JSON array per page.
        rows: List[dict] = []
        decoder = json.JSONDecoder()
        text, index = out.strip(), 0
        while index < len(text):
            page, index = decoder.raw_decode(text, index)
            rows.extend(page)
            while index < len(text) and text[index].isspace():
                index += 1
        return [
            {
                "number": row["number"],
                "body": row.get("body") or "",
                "created_at": row.get("created_at"),
                "user_login": (row.get("user") or {}).get("login"),
                "labels": [label["name"] for label in row.get("labels", [])],
            }
            for row in rows
            if "pull_request" not in row
        ]

    def list_comment_bodies(self, number: int) -> List[str]:
        out = self._gh("api", f"repos/{self.repo}/issues/{number}/comments?per_page=100", "--paginate")
        bodies: List[str] = []
        decoder = json.JSONDecoder()
        text, index = out.strip(), 0
        while index < len(text):
            page, index = decoder.raw_decode(text, index)
            bodies.extend(row.get("body") or "" for row in page)
            while index < len(text) and text[index].isspace():
                index += 1
        return bodies

    def create_issue(self, title: str, body: str) -> None:
        self._gh("issue", "create", "--repo", self.repo, "--title", title, "--body", body, "--label", LABEL)

    def update_issue(self, number: int, title: str, body: str) -> None:
        self._gh("issue", "edit", str(number), "--repo", self.repo, "--title", title, "--body", body)

    def comment(self, number: int, text: str) -> None:
        self._gh("issue", "comment", str(number), "--repo", self.repo, "--body", text)

    def close_issue(self, number: int) -> None:
        self._gh("issue", "close", str(number), "--repo", self.repo, "--comment", "Failing set is empty.")


def main(argv: Optional[Sequence[str]] = None, client_factory=GhClient) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--junit-dir", required=True, type=Path)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--sha", required=True)
    ap.add_argument("--known-reds", type=Path, default=None)
    ap.add_argument("--today", default=None, help="ISO date override for tests; default is today (UTC)")
    args = ap.parse_args(argv)

    failing, seen, measured = parse_junit_dir(args.junit_dir)
    unmeasured = load_expected_ids(args.junit_dir) - measured
    known = load_known_reds(args.known_reds)
    problems = lint_known_reds(known)
    if problems:
        print("::error title=slow_known_reds::" + "; ".join(problems))
        return 1
    today = dt.date.fromisoformat(args.today) if args.today else None
    try:
        result = run_report(
            client_factory(args.repo), failing, seen, known, args.repo, args.run_id, args.sha, unmeasured, today
        )
    except TrackerError as exc:
        print(f"::error title=slow_regression_report::{exc}")
        return 1
    except (subprocess.CalledProcessError, OSError) as exc:
        # Not swallowed: a broken token or permission must not silently drop the alert.
        detail = getattr(exc, "stderr", None) or exc
        print(f"::error title=slow_regression_report::could not update the issue: {detail}")
        return 1
    for warning in result.warnings:
        print(f"::warning title=slow_regression_report::{warning}")
    for reason in result.reasons:
        print(f"::error title=slow_regression_report::{reason}")
    print(f"slow_regression_report: {result.message}")
    return result.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
