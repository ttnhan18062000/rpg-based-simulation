#!/usr/bin/env python3
"""
Render docs/brainstorm/mechanisms.yaml as a static, self-contained HTML page:
docs/brainstorm/mechanism_registry.html.

TCK-20260916-MECHANISM-COMPLETE-REGISTRY-VIEW, Scope item 2. Replaces a hand-authored artifact
(caught and reverted before landing) that embedded the registry's own numbers -- mechanism count,
ranked table, verification ledger -- directly in prose. That is exactly the failure this epic
exists to prevent: a hand-maintained surface duplicating generated data, going stale the moment
`mechanisms.yaml` changes. This page is data generated, never typed -- every row comes straight
from `all_mechanisms_combined_view()`, the same function `generate_mechanism_registry_view.py`
uses for the markdown table, so the two views can never independently disagree.

Governing principle (user, absolute): a piece of information must be defined in one document
only. Defined-once-rendered-many-times is fine (this page is a rendering); authored twice is not.
Per that rule, this page links to TCK-20260915-EPIC-MECHANISM-REGISTRY's own Completion Summary
for the epic's measured findings (17% wiring drift, 2 stale atlas badges, the `camp` seeding
error, the scoping doc's own wrong claim) rather than restating any of those numbers here -- they
live in exactly one place, and this page points to it. In `--target artifact` mode, that link (and
the two sibling-view links) are dropped rather than inlined -- inlining the epic's own findings
text here would itself be the duplication this same principle forbids; a plain-text mention
without a link is honest about a fact this page cannot host, rather than lying with a dead link.

Two publish targets, since this page is meant to be readable both as a repo file (relative links
work; a fixed light palette is fine, GitHub/browser rendering has no host theme to fight) and as a
published Artifact (relative links to sibling repo files/tickets do not resolve; the viewer paints
its own light/dark theme around the page, which a hardcoded palette fights):

  --target repo      (default) relative links to sibling docs/tickets work as committed
  --target artifact  drops the two links that don't resolve outside the repo; theme CSS is
                      always emitted regardless of target, since it costs nothing for the repo
                      copy and is required for the artifact copy

Theme handling follows the standard contract: light tokens on bare :root, dark overrides under
`@media (prefers-color-scheme: dark)` guarded by `:root:not([data-theme="light"])`, and again
under `:root[data-theme="dark"]` so an explicit toggle wins in both directions. Badge colors are
CSS classes keyed by state/evidence value, not inline `style=` colors, so they can vary by theme.

Usage:
  python3 tools/mechanism_registry/generate_mechanism_registry_html.py                    # writes the real output
  python3 tools/mechanism_registry/generate_mechanism_registry_html.py --check             # exit 1 if output is stale
  python3 tools/mechanism_registry/generate_mechanism_registry_html.py --target artifact   # publish-ready variant
  python3 tools/mechanism_registry/generate_mechanism_registry_html.py --output PATH       # write elsewhere (tests)
"""
from __future__ import annotations

import argparse
import html
import re
import sys
from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_REGISTRY_PATH = _REPO_ROOT / "docs" / "brainstorm" / "mechanisms.yaml"
_DEFAULT_OUTPUT = _REPO_ROOT / "docs" / "brainstorm" / "mechanism_registry.html"
_EPIC_TICKET_ID = "TCK-20260915-EPIC-MECHANISM-REGISTRY"
_EPIC_TICKET_RELATIVE_LINK = f"../../tickets/done/mechanism-registry/{_EPIC_TICKET_ID}.md"

sys.path.insert(0, str(_REPO_ROOT / "tools" / "mechanism_registry"))
from registry import all_mechanisms_combined_view  # noqa: E402

_VALID_TARGETS = ("repo", "artifact")

# CSS class suffixes, keyed by real registry values -- a bad/unknown value falls back to a
# neutral "unknown" class rather than crashing, since new states/evidence values are a real
# possibility this file shouldn't need to change for.
_STATE_CLASSES = frozenset({"done", "partial", "skeleton", "gap", "orphan", "gated"})
_EVIDENCE_CLASSES = frozenset({"runtime", "static", "unverified"})


def _css_key(value: str, valid: frozenset) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or "unknown"
    return slug if slug in valid else "unknown"


def _badge(text: str, kind: str, key: str) -> str:
    css_key = _css_key(key, _STATE_CLASSES if kind == "state" else _EVIDENCE_CLASSES)
    return f'<span class="badge {kind}-{css_key}">{html.escape(text)}</span>'


def render(data: dict, target: str = "repo") -> str:
    if target not in _VALID_TARGETS:
        raise ValueError(f"target must be one of {_VALID_TARGETS}, got {target!r}")

    rows = all_mechanisms_combined_view(data)
    total = len(rows)
    runtime_count = sum(1 for r in rows if r["evidence"] == "runtime")
    static_count = sum(1 for r in rows if r["evidence"] == "static")
    unverified_count = sum(1 for r in rows if r["evidence"] == "unverified")

    table_rows = []
    for r in rows:
        verdict = r["verdict"] or "unverified"
        table_rows.append(
            "<tr>"
            f"<td><code>{html.escape(r['id'])}</code></td>"
            f"<td>{html.escape(str(r['layer']))}</td>"
            f"<td>{_badge(str(r['state']), 'state', str(r['state']))}</td>"
            f"<td>{_badge(r['evidence'], 'evidence', r['evidence'])}</td>"
            f"<td>{html.escape(verdict)}</td>"
            f"<td>{r['priority']}</td>"
            f"<td>{r['transitive_dependent_count']}</td>"
            "</tr>"
        )

    if target == "repo":
        sibling_links = (
            'See <a href="mechanism_priority_view.md">mechanism_priority_view.md</a> for the '
            "focused, unverified-only, top-25 &quot;verify next&quot; ranking, and "
            '<a href="mechanism_verification_view.md">mechanism_verification_view.md</a> for the '
            "full verification ledger with notes."
        )
        epic_mention = (
            f'<a href="{_EPIC_TICKET_RELATIVE_LINK}">{_EPIC_TICKET_ID}\'s Completion Summary</a>'
        )
    else:
        sibling_links = (
            "See <code>mechanism_priority_view.md</code> (in the repository) for the focused, "
            "unverified-only, top-25 &quot;verify next&quot; ranking, and "
            "<code>mechanism_verification_view.md</code> for the full verification ledger with "
            "notes -- not linkable from a published page."
        )
        epic_mention = f"{_EPIC_TICKET_ID}'s Completion Summary (in the repository)"

    return f"""<title>Mechanism Registry</title>
<style>
:root {{
  --bg: #EDEEE9; --surface: #FFFFFF; --surface-2: #E3E4DC; --ink: #1F2421; --ink-soft: #4B534E;
  --border: #D3D5CB; --accent: #A9720C;
  --state-done-ink: #2C6E63; --state-done-bg: #DCEBE7;
  --state-partial-ink: #B8860B; --state-partial-bg: #F3E7C9;
  --state-skeleton-ink: #7A5C3E; --state-skeleton-bg: #EDE1D2;
  --state-gap-ink: #8B8378; --state-gap-bg: #EAE8E2;
  --state-orphan-ink: #6B5B95; --state-orphan-bg: #E7E3F1;
  --state-gated-ink: #2E6E8E; --state-gated-bg: #DCEAF0;
  --state-unknown-ink: #4B534E; --state-unknown-bg: #E3E4DC;
  --evidence-runtime-ink: #2C6E63; --evidence-runtime-bg: #DCEBE7;
  --evidence-static-ink: #2E6E8E; --evidence-static-bg: #DCEAF0;
  --evidence-unverified-ink: #8B8378; --evidence-unverified-bg: #EAE8E2;
  --evidence-unknown-ink: #4B534E; --evidence-unknown-bg: #E3E4DC;
  --font-body: -apple-system, BlinkMacSystemFont, "Segoe UI", "Inter", Roboto, Helvetica, Arial, sans-serif;
}}
@media (prefers-color-scheme: dark) {{
  :root:not([data-theme="light"]) {{
    --bg: #1B1D1A; --surface: #24261F; --surface-2: #2C2E27; --ink: #E8E6DF; --ink-soft: #B7BAB1;
    --border: #3A3D34; --accent: #E0B168;
    --state-done-ink: #7FD8C8; --state-done-bg: #1E3B36;
    --state-partial-ink: #F0C868; --state-partial-bg: #4A3B14;
    --state-skeleton-ink: #D8B78C; --state-skeleton-bg: #3E3020;
    --state-gap-ink: #C7C2B6; --state-gap-bg: #3A382F;
    --state-orphan-ink: #C7B8ED; --state-orphan-bg: #362E4A;
    --state-gated-ink: #8FC8E0; --state-gated-bg: #1E3A47;
    --state-unknown-ink: #C7C2B6; --state-unknown-bg: #3A382F;
    --evidence-runtime-ink: #7FD8C8; --evidence-runtime-bg: #1E3B36;
    --evidence-static-ink: #8FC8E0; --evidence-static-bg: #1E3A47;
    --evidence-unverified-ink: #C7C2B6; --evidence-unverified-bg: #3A382F;
    --evidence-unknown-ink: #C7C2B6; --evidence-unknown-bg: #3A382F;
  }}
}}
:root[data-theme="dark"] {{
  --bg: #1B1D1A; --surface: #24261F; --surface-2: #2C2E27; --ink: #E8E6DF; --ink-soft: #B7BAB1;
  --border: #3A3D34; --accent: #E0B168;
  --state-done-ink: #7FD8C8; --state-done-bg: #1E3B36;
  --state-partial-ink: #F0C868; --state-partial-bg: #4A3B14;
  --state-skeleton-ink: #D8B78C; --state-skeleton-bg: #3E3020;
  --state-gap-ink: #C7C2B6; --state-gap-bg: #3A382F;
  --state-orphan-ink: #C7B8ED; --state-orphan-bg: #362E4A;
  --state-gated-ink: #8FC8E0; --state-gated-bg: #1E3A47;
  --state-unknown-ink: #C7C2B6; --state-unknown-bg: #3A382F;
  --evidence-runtime-ink: #7FD8C8; --evidence-runtime-bg: #1E3B36;
  --evidence-static-ink: #8FC8E0; --evidence-static-bg: #1E3A47;
  --evidence-unverified-ink: #C7C2B6; --evidence-unverified-bg: #3A382F;
  --evidence-unknown-ink: #C7C2B6; --evidence-unknown-bg: #3A382F;
}}
body {{ background: var(--bg); color: var(--ink); font-family: var(--font-body); margin: 0; padding: 24px 16px; }}
.wrap {{ max-width: 1000px; margin: 0 auto; }}
h1 {{ margin-bottom: 4px; }}
p.sub {{ color: var(--ink-soft); max-width: 72ch; }}
.counts {{ font-weight: 600; margin: 16px 0; }}
table {{ width: 100%; border-collapse: collapse; background: var(--surface); box-shadow: 0 1px 2px rgba(0,0,0,0.15); }}
th, td {{ text-align: left; padding: 6px 10px; border-bottom: 1px solid var(--border); font-size: 14px; }}
th {{ background: var(--surface-2); position: sticky; top: 0; }}
.badge {{ display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 12px; font-weight: 600; }}
.state-done, .evidence-runtime {{ color: var(--state-done-ink); background: var(--state-done-bg); }}
.state-partial {{ color: var(--state-partial-ink); background: var(--state-partial-bg); }}
.state-skeleton {{ color: var(--state-skeleton-ink); background: var(--state-skeleton-bg); }}
.state-gap {{ color: var(--state-gap-ink); background: var(--state-gap-bg); }}
.state-orphan {{ color: var(--state-orphan-ink); background: var(--state-orphan-bg); }}
.state-gated, .evidence-static {{ color: var(--state-gated-ink); background: var(--state-gated-bg); }}
.state-unknown, .evidence-unknown {{ color: var(--state-unknown-ink); background: var(--state-unknown-bg); }}
.evidence-unverified {{ color: var(--evidence-unverified-ink); background: var(--evidence-unverified-bg); }}
a {{ color: var(--accent); }}
.tablewrap {{ overflow-x: auto; }}
</style>
<div class="wrap">
<h1>Mechanism Registry</h1>
<p class="sub">Generated from <code>docs/brainstorm/mechanisms.yaml</code> &mdash;
regenerate with <code>make mechanism-registry-html</code>. Do not hand-edit. Every row comes
directly from the registry; nothing on this page is hand-typed.</p>
<p class="sub">Sorted by priority (layer weight &times; transitive dependent-count) descending.
{sibling_links}</p>
<p class="sub">For the epic's own measured findings about what this registry replaced and what it
found &mdash; wiring-map drift, stale atlas badges, seeding errors &mdash; see
{epic_mention} rather than this page, so those figures are defined in exactly one place.</p>
<p class="counts">{runtime_count} runtime-verified, {static_count} static (code_trace)-verified,
{unverified_count} unverified &mdash; of {total} total.</p>
<div class="tablewrap">
<table>
<thead><tr><th>Mechanism</th><th>Layer</th><th>State</th><th>Evidence</th><th>Verdict</th><th>Priority</th><th>Transitive Dependents</th></tr></thead>
<tbody>
{''.join(table_rows)}
</tbody>
</table>
</div>
</div>
"""


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=_DEFAULT_OUTPUT)
    parser.add_argument("--registry", type=Path, default=_REGISTRY_PATH)
    parser.add_argument(
        "--target", choices=_VALID_TARGETS, default="repo",
        help="'repo' (default) keeps working relative links to sibling docs/tickets; "
             "'artifact' drops the links that don't resolve outside the repository, for "
             "publishing this page as a standalone Artifact.",
    )
    parser.add_argument(
        "--check", action="store_true",
        help="Exit 1 if the output file would change, without writing it.",
    )
    args = parser.parse_args(argv)

    with open(args.registry, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    content = render(data, target=args.target)

    if args.check:
        existing = args.output.read_text(encoding="utf-8") if args.output.exists() else None
        if existing != content:
            print(f"STALE: {args.output} does not match the real registry -- "
                  "run `make mechanism-registry-html`")
            return 1
        print(f"OK: {args.output} is up to date")
        return 0

    args.output.write_text(content, encoding="utf-8")
    n_mechanisms = len(data.get("mechanisms", []) or [])
    print(f"Wrote {args.output} ({n_mechanisms} mechanisms, target={args.target})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
