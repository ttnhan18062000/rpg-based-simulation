---
status: active
layer: ai
authority: P2
audience: agent
tags: [governance, ai, security]
---

# Capability-Envelope Baseline

`tools/capability_envelope_baseline.py` manages the append-only registry
(`registries/capability_envelope_registry.jsonl`) that records the approved capability envelope
for `.claude/settings.local.json`, and provides a `diff` subcommand that compares the live file
against that registry. Built for `TCK-20260904-CAPABILITY-ENVELOPE-BASELINE`.

## Why this exists

The frozen agent-infrastructure proposal's configuration-precedence invariant is "effective local
capability ⊆ approved capability envelope." `settings.local.json` is per-machine/per-worktree and
git-ignored only by the user's personal global gitignore (not this repo's own tracked
`.gitignore` — a known, disclosed gap, explicitly out of scope for this tool to fix). This module
gives that invariant something concrete to check against: a version-controlled baseline, kept
separate from the git-ignored live file, plus a script that reports where the live file has
drifted from it.

**This is audit-only tooling.** There is no confirmed runtime-enforcement mechanism today — the
`diff` report is evidence for human review, not a security control. Every report the CLI prints
carries an `audit_only_disclaimer` field saying so explicitly, and this module's own docstring
repeats it.

## Registry shape

One JSON object per line, keyed on `(field, value)`:

```json
{"field": "permissions.allow", "value": "Bash(git *)", "added_date": "2026-09-05",
 "reviewed": true, "note": "..."}
```

- `field` is one of the 4 real top-level schema fields `settings.local.json` uses:
  `permissions.allow`, `enableAllProjectMcpServers`, `enabledMcpjsonServers`,
  `disabledMcpjsonServers`. (`permissions.deny`/`permissions.ask` are absent in the live file and
  are not part of this envelope.)
- `value` is the individual permission string, boolean, or server name.
- `reviewed` is a **typed boolean**, not something recovered by parsing `note`'s text: `True` when
  the entry was added one at a time via the `add` CLI subcommand (a deliberate, individually
  reviewed governance addition), `False` when it was bulk-written by `seed`. Durable meaning about
  review status is never stored only in a free-form string — see the project's Durable State Rule.
- `note` is supplementary human-readable context only.

Lifecycle mirrors `tools/tag_registry.py` / `tools/layer_registry.py` exactly: append-only,
unique `(field, value)` key, no update/delete command. A rare manual correction happens via a
direct file edit + git history, same as those two registries.

## Why registry-style, not snapshot-style

`tools/agent-monitoring/manifest.py`'s snapshot+prefix-preservation pattern is built for a
continuously-appended, never-rewritten *log* where old lines must never change. A capability
envelope is the opposite kind of artifact — a live, occasionally *intentionally revised* statement
of what's currently approved. Forcing every revision through a hash+prefix-preservation gate would
fight that. The simpler tag/layer-registry model ("each key added exactly once, no update/delete
command") already tolerates deliberate later revision without extra machinery, and each
`permissions.allow` string or MCP server name is naturally an independent, individually-addable
unit — the same granularity `tag_registry.py`'s `add_tag()` already uses.

## Why seeded from the live 114-entry file, not the committed 48-entry file

`.claude/settings.json` (tracked, shared) and `.claude/settings.local.json` (git-ignored,
per-machine) are two structurally different, intentionally-coexisting config surfaces — see
`docs/ai/skills.md`'s `/update-config` documentation. Seeding this baseline from the *shared*
file's 48-entry list would compare it against the unrelated *local* file's live 114 entries and
immediately flag ~66+ everyday, legitimate local permissions (`git`, `grep`, `pytest`, etc.) as
"out of envelope" purely because they live in a different file — pure noise on day one, undermining
trust in the tool before its first real use.

The baseline was instead seeded, once, from the real live `settings.local.json` (see Step 5 of this
ticket's plan). Every seeded entry's `note` says explicitly: "grandfathered baseline snapshot ...
not individually security-reviewed; establishes the drift-detection floor going forward." **In the
baseline does not mean individually vetted** — the `reviewed=False` typed field on every seeded
entry is the durable record of that fact. Day-one drift detection is therefore meaningful for
*new* additions after this ticket landed, not a grandfather-everything-forever no-op. A future
manual security review of the seeded entries' contents is a separate, later ticket — not something
this tool performs or claims.

## CLI

```bash
python3 tools/capability_envelope_baseline.py add <field> <value> --note "why this entry exists"
python3 tools/capability_envelope_baseline.py seed --settings-path <path> --note "why"
python3 tools/capability_envelope_baseline.py list
python3 tools/capability_envelope_baseline.py diff --settings-path <path>
```

- `add` — register one new `(field, value)` entry. Raises if already registered. `reviewed`
  defaults to `True`.
- `seed` — bulk-register every entry found in a live `settings.local.json`. Idempotent: an
  already-registered entry is silently skipped, not an error. Writes `reviewed=False` for every
  entry it appends. `--settings-path` defaults to `.claude/settings.local.json` under the repo
  root; always pass it explicitly when auditing a different machine's file.
- `list` — print every registered entry.
- `diff` — compare a live `settings.local.json` against the registry, printing a JSON report with
  one section per field: `in_envelope` and `out_of_envelope` value lists. If the target file
  doesn't exist, reports `{"status": "no_local_file", "fields": {}}` rather than raising.

No subcommand ever writes to any `settings*.json` file. The only file this module ever writes is
`registries/capability_envelope_registry.jsonl`.

## Known limitations (disclosed, not fixed here)

- `settings.local.json`'s git-ignore coverage is only enforced by the user's personal global
  `~/.config/git/ignore`, not this repo's own tracked `.gitignore` — a real gap, explicitly out of
  scope for this ticket to fix.
- The diff is an exact-string comparison. Near-duplicate command variants and very broad entries
  (e.g. `Read(//tmp/**)`, `Bash(find / -maxdepth 8 ...)`) are compared literally, not normalized —
  a deliberate, simple starting point, not a claim of semantic equivalence detection.
- No actual runtime-enforcement mechanism exists. This tool only reports drift for human review.
