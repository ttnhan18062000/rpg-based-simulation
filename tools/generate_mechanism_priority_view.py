#!/usr/bin/env python3
"""
Renders the flagship top-N unverified-priority view (TCK-20260915-MECHANISM-PRIORITY-DERIVATION)
to docs/brainstorm/mechanism_priority_view.md -- the text table plus the mermaid chart, "two
outputs from one registry" per the ticket's own Request Summary. Mirrors
tools/generate_mechanism_verification_view.py's own committed-markdown, --check-mode pattern.

Usage:
  python3 tools/generate_mechanism_priority_view.py
  python3 tools/generate_mechanism_priority_view.py --check
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parent.parent
_REGISTRY_PATH = _REPO_ROOT / "docs" / "brainstorm" / "mechanisms.yaml"
_DEFAULT_OUTPUT = _REPO_ROOT / "docs" / "brainstorm" / "mechanism_priority_view.md"
_DEFAULT_N = 25

sys.path.insert(0, str(_REPO_ROOT / "tools"))
from generate_mechanism_charts import render_top_n_chart, render_top_n_table  # noqa: E402
from mechanism_registry import unverified_priority_ranking  # noqa: E402


def render(data: dict, n: int = _DEFAULT_N) -> str:
    total_unverified = len(unverified_priority_ranking(data))
    total = len(data.get("mechanisms", []) or [])
    table = render_top_n_table(data, n=n)
    chart = render_top_n_chart(data, n=n)
    return f"""# Mechanism Priority View — Top {n} Unverified

Generated from `docs/brainstorm/mechanisms.yaml` — regenerate with
`make mechanism-priority-view`. Do not hand-edit.

**Which mechanism to verify next.** {total_unverified} of {total} mechanisms are currently
unverified (see `docs/brainstorm/mechanism_verification_view.md`). Priority is derived, never
hand-ranked: `layer weight × transitive dependent-count`, computed from the registry's own
`depends_on` edges — a hub mechanism nobody has verified is the highest-value next target, since
more depends on it. Ranked below, top {n}.

## Text form

{table}

## Chart form

```mermaid
{chart}
```
"""


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=_DEFAULT_OUTPUT)
    parser.add_argument("--registry", type=Path, default=_REGISTRY_PATH)
    parser.add_argument("--n", type=int, default=_DEFAULT_N)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    with open(args.registry, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    content = render(data, n=args.n)

    if args.check:
        existing = args.output.read_text(encoding="utf-8") if args.output.exists() else None
        if existing != content:
            print(f"STALE: {args.output} does not match the real registry -- "
                  "run `make mechanism-priority-view`")
            return 1
        print(f"OK: {args.output} is up to date")
        return 0

    args.output.write_text(content, encoding="utf-8")
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
