"""Impact report v0: changed paths -> domains, recommended levels, tests and lanes, with reasons.

RECOMMENDATION ONLY. This report must never be used to skip, remove or narrow a test or a CI lane: it
adds reasons and flags, it takes none away. It carries no field designed for skipping; a change with no
runtime-impact rule (documentation only) is stated as such, informationally, and CI's own rules still decide
what runs. Unknown impact is stated as `impact-unknown` and falls back to the PR-eligible lane set.

Inputs (v0):
* the ownership map -- the per-domain import roots in `core_rpg_report` (architecture_design_notes.md
  section 3.1), applied to changed `src/` modules;
* a static import graph: which tests import a changed module, and which `src/` modules import it
  (one hop, used only to name dependent domains);
* content/config rules for `data/worlds/**`, `data/content/**` and `config/**`.

Three separate facts per recommended test: `selected` (the model chose it), `lane_triggered` (the CI path
filter in `.github/workflows/test.yml` would run its lane for THIS change; parsed from the workflow) and
`executed` (from supplied JUnit, otherwise `not-run`). A selected test whose lane is not triggered is
shown as such, not hidden.

Known gaps (also in output): "tactical navigation" is listed under Movement in the ownership map but has
no code root, so no path can be mapped to it; such paths surface as `impact-unknown`. The PR-eligible
fallback is every parsed lane whose pytest step excludes slow tests; jobs outside that set are named as
nightly/main-only evidence, never PR evidence. Transitive `src/` dependents are not followed.

Run: `python3 -m tools.test_architecture.impact_report [--base origin/main] [--paths a b ...] [--junit x.xml]`
Exit status is always 0.
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set

from tools.test_architecture import core_rpg_report as report

SCHEMA_VERSION = 1
SCENARIO_LANE_PATH = "tests/mechanic_scenarios"
CONTENT_PREFIXES = ("data/worlds/", "data/content/", "config/")
DOC_PREFIXES = ("docs/", "tickets/", "stored_artifacts/", "staging_artifacts/", "agent-monitoring/", "registries/")
GAP_TACTICAL_NAVIGATION = (
    "tactical navigation is listed under Movement in the ownership map but has no code root; changed paths "
    "that only belong to it cannot be mapped and are reported as impact-unknown"
)
MAX_TESTS_LISTED = 60

_FILTER_RE = re.compile(r"""(\w+_RE)='([^']*)'""")
_FILTER_USE_RE = re.compile(r"""run_(\w+)=\$\(echo "\$CHANGED" \| grep -qE "\$(\w+)\"""")


def _module_of(rel_path: str) -> Optional[str]:
    if not rel_path.startswith("src/") or not rel_path.endswith(".py"):
        return None
    mod = rel_path[:-3].replace("/", ".")
    return mod[: -len(".__init__")] if mod.endswith(".__init__") else mod


def _owner_of(module: str) -> Optional[str]:
    """Domain owning `module` per the ownership map (substrate included), or None."""
    for domain, prefixes in report.DOMAIN_IMPORT_PREFIXES.items():
        if report._has_prefix([module], prefixes):
            return domain
    if report._has_prefix([module], report._SUBSTRATE_IMPORT_PREFIXES):
        return "substrate"
    return None


def path_filters(workflow: Path) -> Dict[str, "re.Pattern[str]"]:
    """Job id -> the changed-files path filter CI applies to it (jobs without a filter are always-on)."""
    if not workflow.is_file():
        return {}
    text = workflow.read_text(encoding="utf-8")
    patterns = {name: pat for name, pat in _FILTER_RE.findall(text)}
    return {job.replace("_", "-"): re.compile(patterns[var]) for job, var in _FILTER_USE_RE.findall(text) if var in patterns}


def _lane_job(lane: Dict[str, Any]) -> str:
    return lane["lane"].split("/", 1)[0]


class _Index:
    """Static import graph over tests/ and src/ for one repo root."""

    def __init__(self, repo_root: Path):
        self.root = repo_root
        self.test_imports = {}
        for p in sorted((repo_root / "tests").rglob("test_*.py")) if (repo_root / "tests").is_dir() else []:
            if "__pycache__" not in p.parts:
                self.test_imports[report._rel(p, repo_root)] = report._imports_of(p) or []
        self._src_imports: Optional[Dict[str, List[str]]] = None
        self._texts: Optional[Dict[str, str]] = None

    def tests_importing(self, module: str) -> List[str]:
        return [f for f, imps in self.test_imports.items() if any(i == module or i.startswith(module + ".") for i in imps)]

    def tests_mentioning(self, token: str) -> List[str]:
        out = []
        for f in self.test_imports:
            try:
                if token in (self.root / f).read_text(encoding="utf-8"):
                    out.append(f)
            except OSError:
                pass
        return out

    def tests_reaching_path(self, rel_path: str) -> List[str]:
        """Tests that read `rel_path`: naming it directly, or importing a tools/ or src/ module that names it."""
        direct = self.tests_mentioning(rel_path)
        if self._texts is None:
            self._texts = {}
            for top in ("tools", "src"):
                for p in sorted((self.root / top).rglob("*.py")) if (self.root / top).is_dir() else []:
                    try:
                        self._texts[report._rel(p, self.root)] = p.read_text(encoding="utf-8")
                    except (OSError, UnicodeDecodeError):
                        pass
        via = set()
        for f, text in self._texts.items():
            module = _module_of(f) if f.startswith("src/") else f[:-3].replace("/", ".")
            if rel_path in text:
                via.update(self.tests_importing(module))
        return sorted(set(direct) | via)

    def src_dependent_domains(self, module: str) -> Set[str]:
        if self._src_imports is None:
            self._src_imports = {}
            src = self.root / "src"
            for p in sorted(src.rglob("*.py")) if src.is_dir() else []:
                mod = _module_of(report._rel(p, self.root))
                if mod:
                    self._src_imports[mod] = report._imports_of(p) or []
        domains = set()
        for mod, imps in self._src_imports.items():
            if mod != module and any(i == module or i.startswith(module + ".") for i in imps):
                owner = _owner_of(mod)
                if owner:
                    domains.add(owner)
        return domains


def build_impact_report(repo_root: Path, changed: Sequence[str], junit_paths: Sequence[Path] = ()) -> Dict[str, Any]:
    changed = sorted(set(changed))
    index = _Index(repo_root)
    lanes = report.parse_lanes(repo_root / ".github" / "workflows" / "test.yml")
    filters = path_filters(repo_root / ".github" / "workflows" / "test.yml")
    known_files = set(index.test_imports)
    runs = [report.parse_junit(p, known_files) for p in junit_paths]

    changes: List[Dict[str, Any]] = []
    domains: Dict[str, List[str]] = {}
    unknown: List[Dict[str, str]] = []
    tests: Dict[str, List[str]] = {}
    scenario_level = False

    def add_domain(domain: str, reason: str) -> None:
        domains.setdefault(domain, [])
        if reason not in domains[domain]:
            domains[domain].append(reason)

    for path in changed:
        module = _module_of(path)
        entry: Dict[str, Any] = {"path": path}
        if module is not None:
            owner = _owner_of(module)
            if owner is None:
                entry.update(status="impact-unknown", rule="unmapped-src-path",
                             reason="src module is in no ownership-map component root")
                unknown.append({"path": path, "reason": entry["reason"]})
            else:
                entry.update(status="mapped", rule="ownership-map", domains=[owner],
                             reason=f"module {module} is under the {owner} component roots")
                add_domain(owner, f"{path}: {entry['reason']}")
                for dep in sorted(index.src_dependent_domains(module) - {owner}):
                    add_domain(dep, f"{path}: imported by {dep} code (one hop)")
                for t in index.tests_importing(module):
                    tests.setdefault(t, []).append(f"imports {module}")
                scenario_level = scenario_level or owner != "substrate"
        elif path.startswith("tests/") and Path(path).name.startswith("test_") and path.endswith(".py"):
            entry.update(status="mapped", rule="changed-test", reason="the test file itself changed")
            tests.setdefault(path, []).append("changed test file")
        elif path.startswith(CONTENT_PREFIXES):
            entry.update(status="mapped", rule="content-config", domains=[],
                         reason="content/config change: activated behaviour is not derivable from the path; "
                                "domain not-derived, scenario and migration lanes recommended")
            scenario_level = True
            parts = path.split("/")
            if path.startswith("data/worlds/") and len(parts) > 2:
                for t in index.tests_mentioning(parts[2]):
                    tests.setdefault(t, []).append(f"references world {parts[2]}")
        elif path.startswith(DOC_PREFIXES):
            readers = index.tests_reaching_path(path)
            entry.update(status="no-runtime-impact-rule", rule="documentation",
                         reason="documentation/ticket/registry path: no runtime code; informational only, "
                                "CI rules still decide what runs"
                                + (f"; but {len(readers)} test(s) read this path" if readers else ""))
            for t in readers:
                tests.setdefault(t, []).append(f"reads {path}")
        else:
            entry.update(status="impact-unknown", rule="no-rule", reason="no impact rule covers this path")
            unknown.append({"path": path, "reason": entry["reason"]})
        changes.append(entry)

    cross_domain = len({d for d in domains if d != "substrate"}) >= 2
    levels: List[Dict[str, str]] = []
    if any(c["rule"] == "ownership-map" for c in changes):
        levels += [{"level": "unit", "reason": "src component changed"},
                   {"level": "kernel_integration", "reason": "src component changed"}]
    if scenario_level:
        levels.append({"level": "mechanic_scenario", "reason": "gameplay-domain or content/config change"})
    if cross_domain:
        levels.append({"level": "cross_domain_scenario", "reason": "two or more non-substrate domains impacted"})

    fast = [ln for ln in lanes if ln["fast"]]

    def trigger_state(job: str) -> str:
        pattern = filters.get(job)
        if pattern is None:
            return "always-on"
        return "triggered" if any(pattern.search(p) for p in changed) else "not-triggered"

    recommended_lane_jobs: Dict[str, List[str]] = {}
    for t in tests:
        for ln in fast:
            if report._lane_covers(ln, t):
                recommended_lane_jobs.setdefault(_lane_job(ln), []).append("covers a selected test")
    if scenario_level:
        for ln in fast:
            if report._lane_covers(ln, SCENARIO_LANE_PATH):
                recommended_lane_jobs.setdefault(_lane_job(ln), []).append("scenario level recommended")
    if any(c["rule"] == "content-config" for c in changes):
        for job in filters:
            if "migration" in job:
                recommended_lane_jobs.setdefault(job, []).append("content/config change")

    fallback = sorted({_lane_job(ln) for ln in fast}) if unknown else []
    nightly = sorted({_lane_job(ln) for ln in lanes if not ln["fast"]})

    rec_tests = []
    for t in sorted(tests)[:MAX_TESTS_LISTED]:
        covering = sorted({_lane_job(ln) for ln in fast if report._lane_covers(ln, t)})
        executed = "not-run"
        if runs:
            executed = {r["run_id"]: (report._file_state(r["per_file"][t]) if t in r["per_file"] else "not-run")
                        for r in runs}
        rec_tests.append({"file": t, "selected": True, "reasons": sorted(set(tests[t])),
                          "lanes": covering,
                          "lane_triggered": {j: trigger_state(j) for j in covering},
                          "executed": executed})

    gaps = [GAP_TACTICAL_NAVIGATION,
            "transitive src dependents are not followed (one hop, domains only)",
            "tests are matched to docs/registry paths by literal path mention, directly or through an imported "
            "tools/src module; a test that builds the path dynamically is missed",
            "PR-eligible lanes are approximated as the parsed lanes that exclude slow tests"]
    workflow_text = (repo_root / ".github" / "workflows" / "test.yml")
    if workflow_text.is_file() and "changed-files" in workflow_text.read_text(encoding="utf-8") and not filters:
        gaps.append("path filters unparsed; lane_triggered is unreliable (every lane shows always-on)")

    return {
        "schema_version": SCHEMA_VERSION,
        "report": "impact-report-v0",
        "advisory": "Recommendation only. Never use this report to skip, remove or narrow a test or a lane.",
        "changed_paths": changed,
        "changes": changes,
        "domains": {d: sorted(r) for d, r in sorted(domains.items())},
        "cross_domain": cross_domain,
        "levels": levels,
        "recommended_tests": rec_tests,
        "recommended_tests_total": len(tests),
        "recommended_tests_truncated": max(0, len(tests) - MAX_TESTS_LISTED),
        "lanes": {
            "recommended": [{"lane": j, "reasons": sorted(f"{n} x {reason}" if n > 1 else reason
                                                    for reason, n in ((x, r.count(x)) for x in set(r))),
                             "lane_triggered": trigger_state(j)}
                            for j, r in sorted(recommended_lane_jobs.items())],
            "pr_eligible_fallback": fallback,
            "nightly_or_main_only_reported_separately": nightly,
        },
        "impact_unknown": unknown,
        "known_gaps": gaps,
    }


def changed_paths(repo_root: Path, base: str) -> List[str]:
    def run(*args: str) -> List[str]:
        out = subprocess.run(["git", *args], cwd=repo_root, capture_output=True, text=True)
        return out.stdout.splitlines() if out.returncode == 0 else []

    names = set(run("diff", "--name-only", f"{base}...HEAD")) | set(run("diff", "--name-only", "HEAD"))
    names |= set(run("ls-files", "--others", "--exclude-standard"))
    return sorted(names)


def render_markdown(rep: Dict[str, Any]) -> str:
    lines = ["# Impact report v0", "", f"_{rep['advisory']}_", "", "## Changes"]
    lines += [f"- `{c['path']}` — {c['status']} ({c['rule']}): {c['reason']}" for c in rep["changes"]]
    lines += ["", "## Domains"] + [f"- **{d}**: {'; '.join(r)}" for d, r in rep["domains"].items()]
    lines += ["", "## Levels"] + [f"- {lv['level']}: {lv['reason']}" for lv in rep["levels"]]
    lines += ["", f"## Recommended tests ({rep['recommended_tests_total']})"]
    for t in rep["recommended_tests"]:
        lines.append(f"- `{t['file']}` — {'; '.join(t['reasons'])} | lanes: {t['lane_triggered']} | executed: {t['executed']}")
    lines += ["", "## Lanes"]
    lines += [f"- {ln['lane']} ({ln['lane_triggered']}): {'; '.join(ln['reasons'])}" for ln in rep["lanes"]["recommended"]]
    if rep["impact_unknown"]:
        lines += ["", "## impact-unknown"] + [f"- `{u['path']}`: {u['reason']}" for u in rep["impact_unknown"]]
        lines.append(f"PR-eligible fallback lanes: {', '.join(rep['lanes']['pr_eligible_fallback'])}")
    lines += ["", "## Known gaps"] + [f"- {g}" for g in rep["known_gaps"]]
    return "\n".join(lines) + "\n"


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repo-root", type=Path, default=Path.cwd())
    ap.add_argument("--base", default="origin/main")
    ap.add_argument("--paths", nargs="*", help="changed paths (default: git diff against --base)")
    ap.add_argument("--junit", type=Path, action="append", default=[])
    ap.add_argument("--format", choices=("markdown", "json"), default="markdown")
    args = ap.parse_args(argv)
    root = args.repo_root.resolve()
    rep = build_impact_report(root, args.paths if args.paths is not None else changed_paths(root, args.base), args.junit)
    sys.stdout.write(json.dumps(rep, indent=2, sort_keys=True) + "\n" if args.format == "json" else render_markdown(rep))
    return 0


if __name__ == "__main__":
    sys.exit(main())
