#!/usr/bin/env python3
"""Verify each record's own authoritative timestamp field is consistent with the
ISO week of the folder it physically lives in, across the multi-week
agent-monitoring/data/<ISO-week>/{runs,events,tools}.jsonl corpus
(TCK-20260904-MONITORING-TEMPORAL-WEEK-CONSISTENCY-CHECK).

This is a single-file, single-record self-consistency check — a record's own
timestamp field vs. the ISO week of the folder it sits in — not a join. It is a
sibling to, not an extension of, verify_referential_integrity.py (which checks the
2 documented foreign-key relationships between different .jsonl files); this
script imports load_all_weeks()/DEFAULT_DATA_DIR from that module (documented
reuse of the existing multi-week loader) but defines its own report shape.

The check is source-aware by design, because each source's write path relates a
record's own timestamp field to its containing folder's ISO week differently
(TCK-20260903-MONITORING-DATA-WRITE-PATH-UNIFY):

  - tools.jsonl: post_tool_hook.py computes the folder's iso_week and the record's
    own `ts` field from the literal same `now_dt` value in the same statement
    block — bit-for-bit identical by construction. Any mismatch here has no
    legitimate explanation under the current write path and is reported as a
    GENUINE ANOMALY.
  - events.jsonl: record_events.py computes the folder's iso_week once per batch
    (write-time), independent of each event's own earlier-set `ts`. A mismatch is
    plausible (the batch write can lag the event's own timestamp by the gap
    between phases) but not necessarily a bug — reported as a POSSIBLE DIVERGENCE.
  - runs.jsonl: record_run.py computes the folder's iso_week at write-time,
    independent of `start_ts`, which is captured much earlier (session start).
    A long-running or paused/resumed ticket can legitimately span many ISO weeks
    between `start_ts` and the write that lands its runs.jsonl row — reported as
    EXPECTED DIVERGENCE, never anomaly-toned language.

Records living in the unknown-week fallback folder are structurally exempt: there
is no real ISO week to compare a folder-less record against. This is a distinct
bucket from "no usable/parseable timestamp field in a known week folder" (a
record's own content gap, not a property of where it physically sits) — the two
are never conflated in this report.

This tool is report-only: it never gates, never writes, never repairs/re-buckets
any record it finds, and never exits non-zero on finding volume — matching
verify_referential_integrity.py's own precedent exactly. main() always exits 0.
"""
import argparse
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from verify_referential_integrity import load_all_weeks, DEFAULT_DATA_DIR  # noqa: E402
from migrate_monitoring_data import RUNS_FIELD_PRIORITY, EVENTS_FIELD_PRIORITY  # noqa: E402
from migrate_tools_shards import _parse_ts_to_week, UNKNOWN_WEEK_KEY  # noqa: E402

# Not a duplicate of RUNS_FIELD_PRIORITY/EVENTS_FIELD_PRIORITY above: those 2 are
# imported (never re-typed) because they are the sanctioned lists that determined
# where every pre-migration runs/events row physically landed. tools.jsonl has
# never had a legacy timestamp-field variant beyond the single already-migrated
# unknown-week row, so this single-field list is a new, independent constant with
# no prior-existing canonical source to import from.
TOOLS_FIELD_PRIORITY = ["ts"]

GENUINE_ANOMALY = "genuine anomaly"
POSSIBLE_DIVERGENCE = "possible divergence"
EXPECTED_DIVERGENCE = "expected divergence"


def _select_ts_value(record: dict, field_priority: list[str]) -> str | None:
    """Same truthy-first fallback idiom as
    migrate_monitoring_data.py::bucket_lines_by_week_multi_field() (reused by
    description, not by import — that function operates on raw JSONL line
    strings, this one on already-parsed dicts)."""
    return next((record.get(f) for f in field_priority if record.get(f)), None)


@dataclass
class SourceFinding:
    """Per-source classification result. `category_label` names what a non-empty
    `mismatches` means for THIS source — "genuine anomaly" for tools.jsonl,
    "possible divergence" for events.jsonl, "expected divergence" for runs.jsonl —
    so a consumer never has to infer severity from the source name alone.

    `checked`/`matched` cover only records in a known (non-unknown-week) folder
    that carry a usable, parseable timestamp field — `exempt_unknown_week` and
    `skipped_unparseable` are two structurally different, both-legitimate
    "cannot compute a mismatch" buckets and are never folded into `checked`.
    """

    source: str
    category_label: str
    checked: int = 0
    matched: int = 0
    mismatches: list[dict] = field(default_factory=list)
    exempt_unknown_week: int = 0
    skipped_unparseable: int = 0


def check_temporal_consistency(
    records: list[tuple[dict, str]],
    field_priority: list[str],
    category_label: str,
    source: str,
) -> SourceFinding:
    """Classify every (record, week_folder) pair from one source into exactly one
    of 4 buckets: exempt (unknown-week folder), skipped (no usable/parseable
    timestamp field in a known folder), matched, or mismatch (tagged with this
    source's own `category_label`).

    No directionality special-case is needed for runs.jsonl: because
    record_run.py's bucketing key is always computed at write time (necessarily
    >= the record's own start_ts, captured earlier in the pipeline), every
    runs.jsonl mismatch this check can ever find has computed_week <= week_folder
    by construction — there is no legitimate "later" case to special-case.
    """
    finding = SourceFinding(source=source, category_label=category_label)

    for record, week_folder in records:
        if week_folder == UNKNOWN_WEEK_KEY:
            finding.exempt_unknown_week += 1
            continue

        ts_value = _select_ts_value(record, field_priority)
        if ts_value is None:
            finding.skipped_unparseable += 1
            continue

        computed_week = _parse_ts_to_week(ts_value)
        if computed_week == UNKNOWN_WEEK_KEY:
            finding.skipped_unparseable += 1
            continue

        finding.checked += 1
        if computed_week == week_folder:
            finding.matched += 1
        else:
            finding.mismatches.append(
                {
                    "run_id": record.get("run_id"),
                    "seq": record.get("seq"),
                    "ts_value": ts_value,
                    "computed_week": computed_week,
                    "week_folder": week_folder,
                }
            )

    return finding


@dataclass
class TemporalWeekConsistencyReport:
    """Structured result of all 3 source checks. A human reads .to_text(); a
    structured caller (e.g. done_checker_static.py's evidence string builder)
    reads tools/events/runs directly.
    """

    tools: SourceFinding
    events: SourceFinding
    runs: SourceFinding

    def _section(self, finding: SourceFinding, header: str, sample_size: int) -> list[str]:
        lines = [header]
        lines.append(
            f"  Checked (known folder, usable field): {finding.checked}"
        )
        lines.append(f"  Matched (ts is inside its own folder's week): {finding.matched}")
        lines.append(
            f"  Mismatches — {finding.category_label.upper()}: {len(finding.mismatches)}"
        )
        if finding.mismatches:
            lines.append(f"  Sample {finding.category_label} entries:")
            for m in finding.mismatches[:sample_size]:
                lines.append(
                    f"    run_id={m['run_id']} seq={m['seq']} ts={m['ts_value']!r} "
                    f"computed_week={m['computed_week']} folder={m['week_folder']}"
                )
            if len(finding.mismatches) > sample_size:
                lines.append(f"    ... and {len(finding.mismatches) - sample_size} more")
        lines.append(
            f"  Exempt (unknown-week folder — no ISO week to compare against): "
            f"{finding.exempt_unknown_week}"
        )
        lines.append(
            f"  Skipped (known folder, no usable/parseable timestamp field): "
            f"{finding.skipped_unparseable}"
        )
        return lines

    def to_text(self, sample_size: int = 20) -> str:
        total_rows = sum(
            finding.checked
            + finding.exempt_unknown_week
            + finding.skipped_unparseable
            for finding in (self.tools, self.events, self.runs)
        )
        lines = [
            "--- Temporal Week Consistency Report ---",
            "",
            f"Total rows examined across all 3 sources: {total_rows} "
            "(0 mismatches does not mean this check is inert — it means the "
            "corpus's existing week-folder layout is currently self-consistent)",
            "",
        ]

        lines += self._section(
            self.tools,
            "tools.jsonl — ts vs. folder week "
            "(mismatches are GENUINE ANOMALIES — ts and the bucketing key are "
            "the same value at write time, so any mismatch is a real bug)",
            sample_size,
        )
        lines.append("")

        lines += self._section(
            self.events,
            "events.jsonl — ts vs. folder week "
            "(mismatches are POSSIBLE DIVERGENCES — plausible from batch-write "
            "timing, not necessarily bugs)",
            sample_size,
        )
        lines.append("")

        lines += self._section(
            self.runs,
            "runs.jsonl — start_ts vs. folder week "
            "(mismatches are EXPECTED DIVERGENCE, NOT BUGS — a long-running or "
            "paused/resumed ticket can legitimately span multiple ISO weeks "
            "between start_ts and its write-time folder; see "
            "TCK-20260903-MONITORING-DATA-WRITE-PATH-UNIFY)",
            sample_size,
        )

        return "\n".join(lines)


def compute_temporal_week_consistency_report(
    data_dir: Path = DEFAULT_DATA_DIR,
) -> TemporalWeekConsistencyReport:
    """Library-callable entry point: loads the full corpus (every week folder
    under data_dir, via the shared load_all_weeks() loader) and classifies all 3
    sources. data_dir is overridable so tests can point it at a tmp_path fixture
    directory instead of the real corpus."""
    tools_records = load_all_weeks(data_dir, "tools")
    events_records = load_all_weeks(data_dir, "events")
    runs_records = load_all_weeks(data_dir, "runs")

    return TemporalWeekConsistencyReport(
        tools=check_temporal_consistency(
            tools_records, TOOLS_FIELD_PRIORITY, GENUINE_ANOMALY, "tools"
        ),
        events=check_temporal_consistency(
            events_records, EVENTS_FIELD_PRIORITY, POSSIBLE_DIVERGENCE, "events"
        ),
        runs=check_temporal_consistency(
            runs_records, RUNS_FIELD_PRIORITY, EXPECTED_DIVERGENCE, "runs"
        ),
    )


def build_parser():
    parser = argparse.ArgumentParser(
        description=(
            "Verify each record's own timestamp is consistent with the ISO week "
            "of the folder it lives in, across "
            "agent-monitoring/data/<week>/{runs,events,tools}.jsonl"
        )
    )
    parser.add_argument(
        "--data-dir",
        default=str(DEFAULT_DATA_DIR),
        help="Path to the agent-monitoring weekly data directory",
    )
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    report = compute_temporal_week_consistency_report(Path(args.data_dir))
    print(report.to_text())
    # Report-only tool — never gates, never exits non-zero on finding volume (see
    # module docstring). No --strict flag: gate/CI wiring is a deliberate,
    # separate future decision, matching verify_referential_integrity.py's own
    # precedent.


if __name__ == "__main__":
    main()
