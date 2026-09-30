"""Advisory `domain` / `level` marker consistency check (report only, never a gate).

The vocabulary is defined once, in docs/testing/test_taxonomy.md section 10; this module reads it from
there. Two findings families:

* marker problems in a file that declares markers (`unknown-domain`, `unknown-level`, `domain-mismatch`,
  `level-placement-mismatch`);
* `unmarked-core-rpg`: a new or modified test file that the core-RPG report classifies as a core-RPG
  candidate but that declares no `domain` or `level` marker.

Run: `python3 -m tools.test_architecture.marker_check [--base origin/main] [--files ...]`.
Exit status is always 0: findings are printed, not enforced. Existing tests are not bulk-marked; a
file only appears here when it is in the diff (or named with --files).
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

import yaml

from tools.test_architecture import core_rpg_report as report

TAXONOMY_DOC = Path("docs/testing/test_taxonomy.md")
_VOCAB_RE = re.compile(r"<!-- marker-vocabulary:begin -->\s*```yaml\n(.*?)```\s*<!-- marker-vocabulary:end -->", re.S)

# Levels a test may declare, by where it lives (section 5 placement column). Paths not listed here are
# not checked for placement.
_PLACEMENT_LEVELS = (
    ("tests/mechanic_scenarios/", {"mechanic_scenario", "cross_domain_scenario"}),
    ("tests/unit/", {"unit"}),
    ("tests/integration/", {"kernel_integration", "mechanic_scenario", "cross_domain_scenario"}),
)


def load_vocabulary(repo_root: Path) -> Dict[str, Any]:
    text = (repo_root / TAXONOMY_DOC).read_text(encoding="utf-8")
    match = _VOCAB_RE.search(text)
    if not match:
        raise ValueError(f"no marker-vocabulary block in {TAXONOMY_DOC}")
    return yaml.safe_load(match.group(1))


def _imported_domains(imports: Sequence[str]) -> set:
    return {d for d, prefixes in report.DOMAIN_IMPORT_PREFIXES.items() if report._has_prefix(imports, prefixes)}


def check_file(repo_root: Path, rel_path: str, vocab: Dict[str, Any]) -> List[Dict[str, str]]:
    path = repo_root / rel_path
    findings: List[Dict[str, str]] = []
    declared = report.declared_markers(path)
    domains, levels = declared["domains"], declared["levels"]
    imports = report._imports_of(path)

    def add(kind: str, detail: str) -> None:
        findings.append({"file": rel_path, "finding": kind, "detail": detail})

    if not domains and not levels:
        if imports is not None and report.classify_file(rel_path, imports)["class"] in ("classified", "uncertain"):
            add("unmarked-core-rpg", "core-RPG candidate declares no domain or level marker")
        return findings

    for d in domains:
        if d not in vocab["domain"]:
            add("unknown-domain", d)
    for lv in levels:
        if lv not in vocab["level"]:
            add("unknown-level", lv)
    gameplay = _imported_domains(imports or [])
    known_declared = {d for d in domains if d in vocab["domain"]}
    if gameplay and known_declared and not (gameplay & known_declared):
        add("domain-mismatch", f"declares {sorted(known_declared)}, imports code of {sorted(gameplay)}")
    for prefix, allowed in _PLACEMENT_LEVELS:
        if rel_path.startswith(prefix):
            for lv in levels:
                if lv in vocab["level"] and lv not in allowed:
                    add("level-placement-mismatch", f"level {lv!r} is not placed under {prefix} (allowed: {sorted(allowed)})")
            break
    return findings


def changed_test_files(repo_root: Path, base: str) -> List[str]:
    """New or modified `tests/**/test_*.py`: committed since `base`, plus uncommitted and untracked."""
    def run(*args: str) -> List[str]:
        out = subprocess.run(["git", *args], cwd=repo_root, capture_output=True, text=True)
        return out.stdout.splitlines() if out.returncode == 0 else []

    names = set(run("diff", "--name-only", "--diff-filter=AM", f"{base}...HEAD"))
    names |= set(run("diff", "--name-only", "--diff-filter=AM", "HEAD"))
    names |= set(run("ls-files", "--others", "--exclude-standard"))
    return sorted(n for n in names if n.startswith("tests/") and Path(n).name.startswith("test_")
                  and n.endswith(".py") and (repo_root / n).is_file())


def run_check(repo_root: Path, files: Iterable[str]) -> List[Dict[str, str]]:
    vocab = load_vocabulary(repo_root)
    findings: List[Dict[str, str]] = []
    for rel in files:
        findings.extend(check_file(repo_root, rel, vocab))
    return findings


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repo-root", type=Path, default=Path.cwd())
    ap.add_argument("--base", default="origin/main", help="diff base for new/modified tests")
    ap.add_argument("--files", nargs="*", help="check these test files instead of the diff")
    args = ap.parse_args(argv)
    root = args.repo_root.resolve()
    files = args.files if args.files else changed_test_files(root, args.base)
    findings = run_check(root, files)
    for f in findings:
        print(f"ADVISORY {f['finding']}: {f['file']}: {f['detail']}")
    print(f"marker-check: {len(files)} file(s) checked, {len(findings)} advisory finding(s); advisory only, exit 0")
    return 0


if __name__ == "__main__":
    sys.exit(main())
