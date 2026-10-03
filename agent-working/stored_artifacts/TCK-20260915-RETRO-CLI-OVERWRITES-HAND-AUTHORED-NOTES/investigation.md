# Investigation — TCK-20260915-RETRO-CLI-OVERWRITES-HAND-AUTHORED-NOTES

Root cause confirmed exactly as scoped: `main()`'s `out_path.write_text(report)` (previously
unconditional) discards the entire existing file, including any hand-authored `## Notes` content —
the sole documented hand-authoring surface per
`.claude/skills/agent-monitoring-retro/SKILL.md` ("Fills in the `## Notes` section... Commit the
filled-in report. Do not discard the notes").

`generate()` always appends `## Notes` as the report's final section, unconditionally (verified
directly — not gated by any `if`), so a freshly-generated report always has a `## Notes` heading to
splice against.

## Reproduction

This hazard was hit for real during this epic's own ticket 1 (`TCK-20260915-DUPLICATE-RUN-RECORDS`)
investigation earlier this session: `python3 tools/agent-monitoring/generate_retro.py --days 14`
rewrote `RETRO-LAST14D.md` from scratch, destroying 177 lines of a peer's own hand-authored "Deep
review" section. Caught via `git diff --stat` immediately after the run, reverted via
`git checkout --`. From that point forward, every verification this session performed against
`RETRO-LAST14D.md` specifically used direct Python imports (`_load_runs_and_events()` /
`compute_retro_metrics()` / `generate()`), never the CLI, until this ticket's own fix landed.

## Fix shape chosen

Of the ticket's own three suggested shapes (refuse-unless-force, preserve-a-delimited-region,
write-elsewhere-by-default), **preserve** was chosen: it matches the skill's actual documented
cadence (regenerate routinely, refreshing the generated sections, while `## Notes` accumulates
hand-written analysis across regenerations) without requiring every routine regeneration to pass
`--force` (which "refuse" would have forced) or silently diverging report content across two
different file paths (which "write-elsewhere" would have caused).

`_extract_notes_section(existing_text)`: returns everything from the first `## Notes` heading
onward, or `None` if no such heading exists (nothing to preserve — e.g. a non-standard or
hand-truncated file).

`_write_report_preserving_notes(report, out_path, force)`: the single write path. If `force` is
set, or no existing file is present, or the existing file has no `## Notes` heading to preserve —
writes the fresh report directly (same as the prior unconditional behavior). Otherwise, splices the
existing file's own `## Notes`-onward text onto the fresh report's own content above its `## Notes`
heading, discarding only the *freshly generated* placeholder Notes text (never anything
hand-authored), and returns a human-readable status string explicitly naming what happened
(never silent, per AC #1).

## Real-file validation

Verified against the actual at-risk file, `RETRO-LAST14D.md` (backed up first as an extra
precaution) — this is the first time this session ran the CLI against that file directly, since
doing so before this fix landed would have repeated the original incident. Result:
`Written: agent-monitoring/retro/RETRO-LAST14D.md (preserved 13459 chars of existing ## Notes
content -- pass --force to discard it instead)`. Diffed against the pre-regeneration backup:
only the generated `## Run Summary`/etc. sections' numbers changed (fresh run/event counts); both
hand-authored sections ("Deep review — 2026-09-15", "Duplicate run records corrected — 2026-09-15")
are byte-for-byte present in the result.
