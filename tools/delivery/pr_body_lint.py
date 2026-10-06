"""Lint a PR body for an attribution trailer (TCK-20261006-PR-BODY-ATTRIBUTION-TRAILER-NOT-CHECKED).

Repo law (`docs/guides/delivery_process.md`, "PR Lifecycle" step 3): no attribution trailer in a PR body.
That means no "Generated with [Claude Code]" line, no `claude.ai/code/session_...` link and no
`Co-Authored-By:` line. Commit-message trailers are unaffected.

This is the one pattern list. `pr_render.check_against_live` imports `find_attribution` and the CI job
`.github/workflows/pr-body-lint.yml` runs this file as a script on `github.event.pull_request.body`.

The patterns are anchored on the real trailer shapes, so prose that only mentions the rule
("no Generated with line") is not a hit.

stdlib only: the CI job runs it without installing the project.
"""
import os
import re
import sys
from typing import List, Optional

ATTRIBUTION_PATTERNS = (
    re.compile(r"Generated with \[?Claude Code", re.IGNORECASE),
    re.compile(r"claude\.ai/code/session_", re.IGNORECASE),
    re.compile(r"^\s*Co-Authored-By:", re.IGNORECASE),
    re.compile("\U0001F916\\s*Generated", re.IGNORECASE),
)


def find_attribution(body: Optional[str]) -> List[str]:
    """Return each body line (stripped) that matches an attribution pattern, in order, once each."""
    hits: List[str] = []
    for line in (body or "").splitlines():
        if any(pattern.search(line) for pattern in ATTRIBUTION_PATTERNS):
            hits.append(line.strip())
    return hits


def main(argv=None, environ=None) -> int:
    """Read the body from the `PR_BODY` environment variable (no shell interpolation of untrusted text)."""
    env = os.environ if environ is None else environ
    hits = find_attribution(env.get("PR_BODY"))
    if not hits:
        print("PR body has no attribution trailer.")
        return 0
    for line in hits:
        print(f"::error::attribution trailer in PR body: {line}")
    print("Remove it and PATCH the body again (docs/guides/delivery_process.md, PR Lifecycle step 3).")
    return 1


if __name__ == "__main__":
    sys.exit(main())
