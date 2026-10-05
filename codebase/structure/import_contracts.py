"""codebase/structure/importlinter.toml: the import-linter config, with its `layers` contract generated.

The layer order comes from `codebase/structure/package_registry.jsonl` (each row's `layer`) and the
current violations are carried as `ignore_imports` from `codebase/structure/import_layers_baseline.txt`
(one `importer -> imported` module pair per line, sorted). Only the block between the two marker
comments in the config is generated; the root packages, flags and the other contracts are hand-edited.
Advisory: nothing here fails a PR (TCK-20261004-IMPORT-LINTER-ADOPTION).

    python3 -m codebase.structure.import_contracts            rewrite the generated block
    python3 -m codebase.structure.import_contracts --check    exit 1 if the block is out of date
    python3 -m codebase.structure.import_contracts seed-baseline [--lint-imports PATH]
                                                             rerun lint-imports with an empty baseline,
                                                             rewrite the baseline file and the block
    python3 -m codebase.structure.import_contracts advisory [--summary-out PATH] [--annotate] [--lint-imports PATH]
                                                             run every contract; write the result to a Markdown
                                                             summary and one ::warning:: line; ALWAYS exit 0

`seed-baseline` accepts every current layer violation, like a ratchet reseed: use it only on purpose.
Exit 0 clean, 1 out of date, 2 could not run (`advisory` exits 0 whatever happens: it is the CI step).
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Sequence

from codebase.structure.packages import LAYERS, REGISTRY_REL_PATH, REPO_ROOT, load_rows

CONFIG_REL_PATH = Path("codebase/structure/importlinter.toml")
BASELINE_REL_PATH = Path("codebase/structure/import_layers_baseline.txt")
BEGIN_MARKER = "# BEGIN GENERATED: layers contract (python3 -m codebase.structure.import_contracts)"
END_MARKER = "# END GENERATED: layers contract"

# Top to bottom: a layer may import the layers below it, never the ones above. Matches the registry's
# `layer` vocabulary (`packages.LAYERS`); a registry layer missing here is reported, not skipped.
LAYER_ORDER = ("consumer", "simulation-systems", "engine", "domain", "content-pipeline", "foundation")

_ENTRY_RE = re.compile(r"^- (\S+) -> (\S+) \(l\.")
_ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")
_TOTALS_RE = re.compile(r"Contracts: (\d+) kept, (\d+) broken")
_BROKEN_RE = re.compile(r"^(.+?) BROKEN(?: \(\d+ ignored imports\))?$", re.M)
_STALE_RE = re.compile(r"No matches for ignored import")


def layer_packages(rows: Sequence[dict]) -> list[tuple[str, list[str]]]:
    """Return `(layer, sorted packages)` in `LAYER_ORDER`; raise if the registry uses a layer not ordered."""
    unordered = {row["layer"] for row in rows} - set(LAYER_ORDER)
    if unordered or set(LAYER_ORDER) != LAYERS:
        raise ValueError(f"layer order out of step with the registry vocabulary: {sorted(unordered or LAYERS ^ set(LAYER_ORDER))}")
    return [(layer, sorted(row["package"] for row in rows if row["layer"] == layer)) for layer in LAYER_ORDER]


def render_block(rows: Sequence[dict], baseline: Sequence[str]) -> str:
    """The generated text, markers included, ending with a newline."""
    lines = [BEGIN_MARKER, "[[tool.importlinter.contracts]]", 'id = "layers"', 'name = "Registry layer order (advisory)"']
    lines += ['type = "layers"', 'unmatched_ignore_imports_alerting = "warn"', "layers = ["]
    for layer, packages in layer_packages(rows):
        lines.append(f'    "{" : ".join(f"src.{package}" for package in packages)}",  # {layer}')
    lines += ["]", "ignore_imports = ["]
    lines += [f'    "{pair}",' for pair in baseline]
    lines += ["]", END_MARKER]
    return "\n".join(lines) + "\n"


def read_baseline(path: Path) -> list[str]:
    """Module pairs from the baseline file: blank lines and `#` comments skipped, sorted, unique."""
    if not path.exists():
        return []
    pairs = {line.strip() for line in path.read_text().splitlines() if line.strip() and not line.startswith("#")}
    return sorted(pairs)


def parse_violations(output: str) -> list[str]:
    """`importer -> imported` pairs from `lint-imports` text (entries are wrapped by the terminal width).

    An entry that is not exactly one direct `a -> b (l.N)` import (a chain of several edges) raises: its first
    edge need not be a violation itself, so accepting it could allow other paths. Baseline such a chain by hand.
    """
    pairs = set()
    for block in re.split(r"\n\s*\n", _ANSI_RE.sub("", output)):
        entry = " ".join(block.split())
        if not entry.startswith("- "):
            continue
        match = _ENTRY_RE.match(entry)
        if match is None or entry.count(" -> ") != 1:
            raise ValueError(f"indirect chain, baseline by hand: {entry[:200]}")
        pairs.add(f"{match.group(1)} -> {match.group(2)}")
    return sorted(pairs)


def splice_block(config: str, block: str) -> str:
    """Replace the generated block in `config`; raise if the markers are missing or out of order."""
    start, end = config.find(BEGIN_MARKER), config.find(END_MARKER)
    if start < 0 or end < start:
        raise ValueError("generated-block markers missing or out of order in the config")
    tail = config[end + len(END_MARKER):]
    return config[:start] + block + (tail[1:] if tail.startswith("\n") else tail)


def _expected_config(root: Path) -> tuple[str, str]:
    config = (root / CONFIG_REL_PATH).read_text()
    block = render_block(load_rows(root / REGISTRY_REL_PATH, root, kinds=()), read_baseline(root / BASELINE_REL_PATH))
    return config, splice_block(config, block)


def seed_baseline(root: Path, lint_imports: str) -> list[str]:
    """Rerun lint-imports with an empty baseline and return the violation pairs it reports."""
    rows = load_rows(root / REGISTRY_REL_PATH, root, kinds=())
    config = splice_block((root / CONFIG_REL_PATH).read_text(), render_block(rows, []))
    with tempfile.TemporaryDirectory() as tmp:
        scratch = Path(tmp) / "importlinter.toml"
        scratch.write_text(config)
        result = subprocess.run([lint_imports, "--config", str(scratch)], cwd=root, capture_output=True, text=True, check=False)
    if "Analyzed" not in result.stdout:
        raise RuntimeError(f"lint-imports did not run: {(result.stderr or result.stdout)[-300:]}")
    return parse_violations(result.stdout)


def advisory_report(root: Path, lint_imports: str) -> tuple[str, bool]:
    """Run every contract; return `(Markdown summary, needs_warning)`. Never raises: a crash is the summary."""
    lines = []
    stale_block = False
    try:
        config, expected = _expected_config(root)
        stale_block = config != expected
        if stale_block:
            lines.append("- the generated `layers` block is out of date: run `python3 -m codebase.structure.import_contracts`")
        result = subprocess.run([lint_imports, "--config", str(root / CONFIG_REL_PATH)], cwd=root, capture_output=True, text=True, check=False, timeout=300)
    except (OSError, ValueError, KeyError, RuntimeError, subprocess.SubprocessError) as exc:
        return f"**Import contracts (advisory):** could not run ({exc.__class__.__name__}: {exc})", True
    text = _ANSI_RE.sub("", result.stdout)
    totals = _TOTALS_RE.search(text)
    if totals is None:
        return f"**Import contracts (advisory):** could not run ({(result.stderr or text).strip()[-200:]})", True
    kept, broken = int(totals.group(1)), int(totals.group(2))
    names = sorted({" ".join(name.split()) for name in _BROKEN_RE.findall(text)})
    stale = len(_STALE_RE.findall(text))
    head = f"**Import contracts (advisory):** {kept} kept, {broken} broken"
    lines = [head + (f", {stale} stale ignored import(s)" if stale else "")] + lines
    lines += [f"- broken: `{name}`" for name in names]
    if broken:
        lines.append("- run `uvx --from import-linter==2.15 lint-imports --config codebase/structure/importlinter.toml` for the import lines")
    return "\n".join(lines), bool(broken or stale or stale_block)


def run_advisory(root: Path, lint_imports: str, summary_out: Path | None, annotate: bool) -> int:
    """The CI step: print and summarise the result; always return 0."""
    summary, warn = advisory_report(root, lint_imports)
    print(summary)
    if summary_out is not None:
        try:
            with summary_out.open("a", encoding="utf-8") as handle:
                handle.write(summary + "\n\n")
        except OSError as exc:  # a summary that cannot be written must never fail the step
            print(f"note: summary not written ({exc})")
    if annotate and warn:
        print("::warning::import contracts (advisory): a contract is broken, stale or could not run; see the job summary")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point; returns the process exit code (0 clean, 1 out of date, 2 could not run)."""
    parser = argparse.ArgumentParser(prog="python3 -m codebase.structure.import_contracts", description=__doc__.split("\n")[0])
    parser.add_argument("--root", type=Path, default=REPO_ROOT)
    parser.add_argument("--check", action="store_true", help="exit 1 if the generated block differs from the registry and baseline")
    sub = parser.add_subparsers(dest="command")
    seed = sub.add_parser("seed-baseline", help="accept every current layer violation into the baseline file")
    seed.add_argument("--lint-imports", default=shutil.which("lint-imports") or "lint-imports")
    advisory = sub.add_parser("advisory", help="run every contract for the CI step; always exits 0")
    advisory.add_argument("--lint-imports", default=shutil.which("lint-imports") or "lint-imports")
    advisory.add_argument("--summary-out", type=Path, help="append the result to this Markdown file (GITHUB_STEP_SUMMARY)")
    advisory.add_argument("--annotate", action="store_true", help="print one GitHub ::warning:: line when a contract is broken or stale")
    args = parser.parse_args(argv)
    if args.command == "advisory":
        return run_advisory(args.root, args.lint_imports, args.summary_out, args.annotate)
    try:
        if args.command == "seed-baseline":
            pairs = seed_baseline(args.root, args.lint_imports)
            (args.root / BASELINE_REL_PATH).write_text("\n".join(pairs) + "\n")
            print(f"import contracts: baseline holds {len(pairs)} module pair(s)")
        config, expected = _expected_config(args.root)
        if args.check:
            print("import contracts: " + ("up to date" if config == expected else "generated block is out of date"))
            return 0 if config == expected else 1
        (args.root / CONFIG_REL_PATH).write_text(expected)
        print(f"import contracts: wrote {CONFIG_REL_PATH}")
    except (OSError, ValueError, KeyError, RuntimeError) as exc:  # a crash is reported, never silent
        print(f"import contracts: could not run ({exc.__class__.__name__}: {exc})")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
