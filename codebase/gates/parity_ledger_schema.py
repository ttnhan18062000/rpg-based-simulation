"""Ratchet over the parity ledger: `docs/parity_ledger/*.yaml` against `docs/parity_ledger/schema.json`.

    python3 -m codebase.gates.parity_ledger_schema check
    python3 -m codebase.gates.parity_ledger_schema tighten [--yes]
    python3 -m codebase.gates.parity_ledger_schema seed [--force]

TCK-20261003-PARITY-LEDGER-SCHEMA-RATCHET. Nothing validated the ledger data: `parity_ledger_writer.validate_entry`
runs on writes only and never loads the schema, so the entries already in the shards carry thousands of schema errors.
This gate validates every shard with jsonschema (Draft 7) and counts the errors per `(shard file, rule)`, where the
rule is the failing schema path without its leading `items/` (for example
`allOf/0/then/properties/test_path/type`). The counts are compared with the committed baseline
`codebase/baselines/parity_ledger_schema_baseline.json`:

- `check` exits 1 when any `(file, rule)` count rose or a `(file, rule)` that is not in the baseline appeared, and
  names the file, the rule, both counts and up to a few failing entry ids. A decrease never fails; it is reported with
  a hint to run `tighten`. It exits 2 when it cannot run (an unparsable shard, a missing or invalid baseline or
  schema): an unusable gate is never a green one.
- `tighten` rewrites the baseline to the current counts, but only when nothing rose and nothing is new (it never raises
  a ceiling). It is a dry run unless `--yes` is given.
- `seed` writes the first baseline and refuses to overwrite an existing one without `--force`.

Known limit: counts cannot see a swap (one entry fixed and another broken in the same file and rule leave the count
equal). `schema.json` itself is never edited here.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Sequence

import jsonschema
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
LEDGER_DIR = Path("docs/parity_ledger")
SCHEMA_NAME = "schema.json"
BASELINE_REL = Path("codebase/baselines/parity_ledger_schema_baseline.json")
BASELINE_VERSION = 1
IDS_SHOWN = 5

Counts = dict[str, dict[str, int]]


class CannotRunError(Exception):
    """The gate could not produce a verdict (exit 2): never reported as a pass."""


@dataclass
class Scan:
    """Error counts per shard file and rule, plus the entry labels that failed each `(file, rule)`."""

    counts: Counts = field(default_factory=dict)
    labels: dict[tuple[str, str], list[str]] = field(default_factory=dict)


@dataclass
class Comparison:
    """Counts that rose, rules that are new to the baseline, and counts that fell (the last never fail the gate)."""

    rises: list[tuple[str, str, int, int]] = field(default_factory=list)  # file, rule, baseline, current
    new: list[tuple[str, str, int]] = field(default_factory=list)  # file, rule, current
    decreases: list[tuple[str, str, int, int]] = field(default_factory=list)  # file, rule, baseline, current (0: gone)

    @property
    def failed(self) -> bool:
        """True when a count rose or a `(file, rule)` is not in the baseline."""
        return bool(self.rises or self.new)


def load_schema(path: Path) -> dict[str, Any]:
    """Read `schema.json` and check it is a valid Draft 7 schema, so a broken schema is exit 2, not a traceback."""
    try:
        schema = json.loads(path.read_text(encoding="utf-8"))
        jsonschema.Draft7Validator.check_schema(schema)
    except OSError as exc:
        raise CannotRunError(f"cannot read the schema {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise CannotRunError(f"the schema {path} is not valid JSON: {exc}") from exc
    except jsonschema.SchemaError as exc:
        raise CannotRunError(f"the schema {path} is not a valid Draft 7 schema: {exc.message}") from exc
    return schema


def rule_of(error: jsonschema.ValidationError) -> str:
    """The failing schema path, without the leading `items` (a root-level failure keeps its whole path)."""
    parts = [str(part) for part in error.relative_schema_path]
    if parts and parts[0] == "items":
        parts = parts[1:]
    return "/".join(parts) or "(root)"


def _label(error: jsonschema.ValidationError, data: Any) -> str:
    """The id of the failing entry, or `#<index>` when the item has no usable id (or is not a mapping)."""
    index = error.path[0] if error.path else None
    if not isinstance(index, int):
        return "(root)"
    item = data[index] if isinstance(data, list) and index < len(data) else None
    if isinstance(item, dict) and isinstance(item.get("id"), str) and item["id"]:
        return item["id"]
    return f"#{index}"


def count_errors(ledger_dir: Path, schema: dict[str, Any]) -> Scan:
    """Validate every `*.yaml` shard and count the errors per `(file, rule)`; an unreadable shard is `CannotRunError`."""
    shards = sorted(ledger_dir.glob("*.yaml"))
    if not shards:
        raise CannotRunError(f"no *.yaml shard found in {ledger_dir}")
    validator = jsonschema.Draft7Validator(schema)
    scan = Scan()
    for shard in shards:
        try:
            data = yaml.safe_load(shard.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError) as exc:
            raise CannotRunError(f"{shard.name} is not readable as YAML: {' '.join(str(exc).split())[:200]}") from exc
        for error in validator.iter_errors(data):
            rule = rule_of(error)
            per_file = scan.counts.setdefault(shard.name, {})
            per_file[rule] = per_file.get(rule, 0) + 1
            scan.labels.setdefault((shard.name, rule), []).append(_label(error, data))
    return scan


def load_baseline(path: Path) -> Counts:
    """Read and shape-check the committed baseline: version 1, integer counts of at least 1."""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise CannotRunError(f"cannot read the baseline {path}: {exc} (create it with `seed`)") from exc
    except json.JSONDecodeError as exc:
        raise CannotRunError(f"the baseline {path} is not valid JSON: {exc}") from exc
    counts = raw.get("counts") if isinstance(raw, dict) else None
    if not isinstance(raw, dict) or raw.get("version") != BASELINE_VERSION or not isinstance(counts, dict):
        raise CannotRunError(f"the baseline {path} must be an object with version {BASELINE_VERSION} and a `counts` object")
    for name, rules in counts.items():
        ok = isinstance(rules, dict) and all(
            isinstance(rule, str) and isinstance(n, int) and not isinstance(n, bool) and n >= 1 for rule, n in rules.items()
        )
        if not isinstance(name, str) or not ok:
            raise CannotRunError(f"the baseline {path} has an invalid entry for {name!r}: counts must be integers of at least 1")
    return counts


def compare(current: Counts, baseline: Counts) -> Comparison:
    """Compare the current counts with the baseline per `(file, rule)`."""
    result = Comparison()
    for name in sorted(set(current) | set(baseline)):
        have, allowed = current.get(name, {}), baseline.get(name, {})
        for rule in sorted(set(have) | set(allowed)):
            now, before = have.get(rule, 0), allowed.get(rule)
            if before is None:
                result.new.append((name, rule, now))
            elif now > before:
                result.rises.append((name, rule, before, now))
            elif now < before:
                result.decreases.append((name, rule, before, now))
    return result


def write_baseline(path: Path, counts: Counts) -> None:
    """Write the baseline sorted, one count per line, so two tightening PRs merge cleanly."""
    body = {"version": BASELINE_VERSION, "counts": {name: dict(sorted(rules.items())) for name, rules in sorted(counts.items())}}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(body, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _ids(scan: Scan, name: str, rule: str, latest: int | None = None) -> str:
    """Entry ids that fail `rule` in `name`: the first few, or (for a rise) the last `latest`, where new entries usually are."""
    labels = scan.labels.get((name, rule), [])
    if latest is not None and len(labels) > IDS_SHOWN:
        return f"most likely the last {min(latest, IDS_SHOWN)}, as new entries are normally appended: {', '.join(labels[-min(latest, IDS_SHOWN):])}; {len(labels)} fail in all, see git diff"
    shown = ", ".join(labels[:IDS_SHOWN])
    return shown + (f", ... ({len(labels)} in all)" if len(labels) > IDS_SHOWN else "")


def format_report(result: Comparison, scan: Scan, total: int) -> str:
    """The text `check` prints: one line per failing or fallen rule, a hint, and a summary line."""
    lines: list[str] = []
    for name, rule, before, now in result.rises:
        lines.append(f"FAIL {name}: rule {rule} rose from {before} to {now} (entries: {_ids(scan, name, rule, latest=now - before)})")
    for name, rule, now in result.new:
        lines.append(f"FAIL {name}: rule {rule} is new, {now} error(s) not in the baseline (entries: {_ids(scan, name, rule)})")
    for name, rule, before, now in result.decreases:
        lines.append(f"better {name}: rule {rule} fell from {before} to {now}")
    if result.failed:
        lines.append("The ledger must not gain schema errors: fix the entry, do not raise the baseline. schema.json is not to be loosened.")
    elif result.decreases:
        lines.append("Counts fell: run `python3 -m codebase.gates.parity_ledger_schema tighten --yes` and commit the baseline.")
    lines.append(f"{'FAILED' if result.failed else 'OK'}: {total} schema error(s) in the ledger, "
                 f"{len(result.rises)} rule(s) rose, {len(result.new)} new, {len(result.decreases)} fell")
    return "\n".join(lines)


def _paths(args: argparse.Namespace) -> tuple[Path, Path, Path]:
    ledger = args.ledger_dir or REPO_ROOT / LEDGER_DIR
    return ledger, args.schema or ledger / SCHEMA_NAME, args.baseline or REPO_ROOT / BASELINE_REL


def _total(counts: Counts) -> int:
    return sum(n for rules in counts.values() for n in rules.values())


def _cmd_check(args: argparse.Namespace) -> int:
    ledger, schema_path, baseline_path = _paths(args)
    scan = count_errors(ledger, load_schema(schema_path))
    result = compare(scan.counts, load_baseline(baseline_path))
    print(format_report(result, scan, _total(scan.counts)))
    return 1 if result.failed else 0


def _cmd_tighten(args: argparse.Namespace) -> int:
    ledger, schema_path, baseline_path = _paths(args)
    scan = count_errors(ledger, load_schema(schema_path))
    result = compare(scan.counts, load_baseline(baseline_path))
    if result.failed:
        print(format_report(result, scan, _total(scan.counts)))
        print("tighten refused: it never raises a count. Nothing was written.")
        return 1
    if not result.decreases:
        print("The baseline is already tight; nothing to do.")
        return 0
    for name, rule, before, now in result.decreases:
        print(f"{name}: {rule} {before} -> {now}")
    if not args.yes:
        print("dry run: nothing written; pass --yes to write the baseline")
        return 0
    write_baseline(baseline_path, scan.counts)
    print(f"baseline tightened: {baseline_path} now holds {_total(scan.counts)} error(s)")
    return 0


def _cmd_seed(args: argparse.Namespace) -> int:
    ledger, schema_path, baseline_path = _paths(args)
    if baseline_path.exists() and not args.force:
        print(f"{baseline_path} exists; `seed --force` overwrites it (a raised count is never allowed by hand)", file=sys.stderr)
        return 1
    scan = count_errors(ledger, load_schema(schema_path))
    write_baseline(baseline_path, scan.counts)
    print(f"baseline written: {baseline_path} holds {_total(scan.counts)} error(s) in {len(scan.counts)} file(s)")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry: exit 0 clean, 1 on a rise or new rule (or a refused tighten), 2 when the gate cannot run."""
    parser = argparse.ArgumentParser(prog="python3 -m codebase.gates.parity_ledger_schema", description=__doc__.split("\n\n")[0])
    parser.add_argument("--ledger-dir", type=Path, help="directory of ledger shards (default: docs/parity_ledger)")
    parser.add_argument("--schema", type=Path, help="schema file (default: <ledger-dir>/schema.json)")
    parser.add_argument("--baseline", type=Path, help="baseline file (default: codebase/baselines/parity_ledger_schema_baseline.json)")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("check")
    sub.add_parser("tighten").add_argument("--yes", action="store_true")
    sub.add_parser("seed").add_argument("--force", action="store_true")
    args = parser.parse_args(argv)
    commands = {"check": _cmd_check, "tighten": _cmd_tighten, "seed": _cmd_seed}
    try:
        return commands[args.command](args)
    except CannotRunError as exc:
        print(f"parity-ledger-schema: could not run: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
