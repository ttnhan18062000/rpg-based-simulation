# Implementation Sequence: visual-asset-main-green

Two independent hotfixes, one batch, one PR. Dispatched by asset-planner after the owner's "Resume all" (2026-10-15, via lead-planner).

1. `TCK-20261015-VISUAL-ASSETS-ICON-SCENE-RC11-KEYS` (#598, P0). Main's Frontend job is red since #596. Do this first.
2. `TCK-20261015-VISUAL-ASSETS-SANDBOX-BWRAP-USERNS-ERROR` (#555, P2). A clear error and an honest skip when bwrap cannot create its net namespace.

Rules for this batch: scoped tests only, one at a time, under `systemd-run --user --scope -q -p MemoryMax=3G`. Ask asset-planner before any full suite. Push and PR only on the owner's answer.
