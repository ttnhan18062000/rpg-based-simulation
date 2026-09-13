#!/usr/bin/env bash
# Post-merge hook: regenerate docs/REGISTRY.yaml if it drifted from a fresh generation.
# Install: make setup-merge-drivers
#
# Paired with the trivial `true` merge driver configured on docs/REGISTRY.yaml
# (.gitattributes: `docs/REGISTRY.yaml merge=registry-regen`) -- that driver resolves any
# merge conflict on this path by keeping the "ours" side, with zero regeneration attempted
# there. Regeneration happens here instead, because a per-path merge driver runs with no
# ordering guarantee relative to other paths in the same merge (the docs/ticket files this
# registry is actually generated from); a post-merge hook runs only after every path in the
# merge is already resolved on disk, which is what makes regenerating here correct.
#
# No-op if generate_registry.py is missing (e.g. a stripped-down checkout).
#
# REQUIRED BACKSTOP -- this driver+hook pair is only safe because a separate CI test exists:
# tests/tools/test_generate_registry.py::TestRealDocsTree::
# test_check_flag_detects_no_drift_against_real_registry (already running in the "API / tools
# / logging" CI job). `git rebase` and `git cherry-pick` also invoke the `.gitattributes`
# merge driver but never run this hook (only `git merge` does), so on those two paths the
# driver's "keep one side" resolution is never followed by a regeneration -- that CI test is
# the ONLY thing that catches the resulting drift. If it is ever deleted or stops running,
# this mechanism silently degrades to "always take one side" with zero detection. Do not
# remove it without replacing this hook's own safety argument.

set -euo pipefail

if [ ! -f tools/generate_registry.py ]; then
    exit 0
fi

check_rc=0
python3 tools/generate_registry.py --check > /dev/null 2>&1 || check_rc=$?

if [ "$check_rc" -eq 0 ]; then
    exit 0
elif [ "$check_rc" -ne 2 ]; then
    # 1 (doc frontmatter errors) or anything unexpected -- a real problem to surface, not
    # something to silently regenerate over. Leave it for the next `make docs-registry` or
    # CI's own drift test to report.
    echo "[registry-post-merge] --check exited $check_rc (not plain drift) -- skipping auto-regen" >&2
    exit 0
fi

python3 tools/generate_registry.py
git add docs/REGISTRY.yaml
git commit -m "auto-regenerate docs/REGISTRY.yaml after merge" -q
echo "[registry-post-merge] docs/REGISTRY.yaml regenerated and committed"
