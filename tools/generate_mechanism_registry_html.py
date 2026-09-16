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
live in exactly one place, and this page points to it.

Usage:
  python3 tools/generate_mechanism_registry_html.py               # writes the real output
  python3 tools/generate_mechanism_registry_html.py --check        # exit 1 if output is stale
  python3 tools/generate_mechanism_registry_html.py --output PATH  # write elsewhere (tests)
"""
from __future__ import annotations

import argparse
import html
import sys
from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parent.parent
_REGISTRY_PATH = _REPO_ROOT / "docs" / "brainstorm" / "mechanisms.yaml"
_DEFAULT_OUTPUT = _REPO_ROOT / "docs" / "brainstorm" / "mechanism_registry.html"
_EPIC_TICKET_RELATIVE_LINK = "../../tickets/done/mechanism-registry/TCK-20260915-EPIC-MECHANISM-REGISTRY.md"

sys.path.insert(0, str(_REPO_ROOT / "tools"))
from mechanism_registry import all_mechanisms_combined_view  # noqa: E402

# Same state palette as docs/brainstorm/rpg_feature_atlas.html, reused for visual consistency
# across the corpus's own generated/hand-authored artifacts.
_STATE_COLORS = {
    "done": ("#2C6E63", "#DCEBE7"),
    "partial": ("#B8860B", "#F3E7C9"),
    "skeleton": ("#7A5C3E", "#EDE1D2"),
    "gap": ("#8B8378", "#EAE8E2"),
    "orphan": ("#6B5B95", "#E7E3F1"),
    "gated": ("#2E6E8E", "#DCEAF0"),
}
_EVIDENCE_COLORS = {
    "runtime": ("#2C6E63", "#DCEBE7"),
    "static": ("#2E6E8E", "#DCEAF0"),
    "unverified": ("#8B8378", "#EAE8E2"),
}


def _badge(text: str, colors: dict, key: str) -> str:
    ink, soft = colors.get(key, ("#4B534E", "#E3E4DC"))
    return (
        f'<span class="badge" style="color:{ink};background:{soft};">'
        f"{html.escape(text)}</span>"
    )


def render(data: dict) -> str:
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
            f"<td>{_badge(str(r['state']), _STATE_COLORS, str(r['state']))}</td>"
            f"<td>{_badge(r['evidence'], _EVIDENCE_COLORS, r['evidence'])}</td>"
            f"<td>{html.escape(verdict)}</td>"
            f"<td>{r['priority']}</td>"
            f"<td>{r['transitive_dependent_count']}</td>"
            "</tr>"
        )

    return f"""<title>Mechanism Registry</title>
<style>
:root {{
  --bg: #EDEEE9; --surface: #FFFFFF; --surface-2: #E3E4DC; --ink: #1F2421; --ink-soft: #4B534E;
  --border: #D3D5CB; --accent: #A9720C;
  --font-body: -apple-system, BlinkMacSystemFont, "Segoe UI", "Inter", Roboto, Helvetica, Arial, sans-serif;
}}
body {{ background: var(--bg); color: var(--ink); font-family: var(--font-body); margin: 0; padding: 24px 16px; }}
.wrap {{ max-width: 1000px; margin: 0 auto; }}
h1 {{ margin-bottom: 4px; }}
p.sub {{ color: var(--ink-soft); max-width: 72ch; }}
.counts {{ font-weight: 600; margin: 16px 0; }}
table {{ width: 100%; border-collapse: collapse; background: var(--surface); box-shadow: 0 1px 2px rgba(31,36,33,0.06); }}
th, td {{ text-align: left; padding: 6px 10px; border-bottom: 1px solid var(--border); font-size: 14px; }}
th {{ background: var(--surface-2); position: sticky; top: 0; }}
.badge {{ display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 12px; font-weight: 600; }}
a {{ color: var(--accent); }}
.tablewrap {{ overflow-x: auto; }}
</style>
<div class="wrap">
<h1>Mechanism Registry</h1>
<p class="sub">Generated from <code>docs/brainstorm/mechanisms.yaml</code> &mdash;
regenerate with <code>make mechanism-registry-html</code>. Do not hand-edit. Every row comes
directly from the registry; nothing on this page is hand-typed.</p>
<p class="sub">Sorted by priority (layer weight &times; transitive dependent-count) descending.
See <a href="mechanism_priority_view.md">mechanism_priority_view.md</a> for the focused,
unverified-only, top-25 &quot;verify next&quot; ranking, and
<a href="mechanism_verification_view.md">mechanism_verification_view.md</a> for the full
verification ledger with notes.</p>
<p class="sub">For the epic's own measured findings about what this registry replaced and what it
found &mdash; wiring-map drift, stale atlas badges, seeding errors &mdash; see
<a href="{_EPIC_TICKET_RELATIVE_LINK}">TCK-20260915-EPIC-MECHANISM-REGISTRY's Completion
Summary</a> rather than this page, so those figures are defined in exactly one place.</p>
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
        "--check", action="store_true",
        help="Exit 1 if the output file would change, without writing it.",
    )
    args = parser.parse_args(argv)

    with open(args.registry, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    content = render(data)

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
    print(f"Wrote {args.output} ({n_mechanisms} mechanisms)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
