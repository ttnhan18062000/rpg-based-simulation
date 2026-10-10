---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261010-VISUAL-ASSETS-PNG-DECODER-SPEEDUP
artifact_type: investigation
tags: [architecture, security, testing]
---

# Investigation
- Before (this machine, 2026-10-10, same inputs): Paeth RGBA noise 1024 px 1.19 s, 1536 px 2.85 s, 2048 px 5.02 s; smooth mixed-filter 1024 px 0.58 s. After: 0.61 / 1.43 / 2.53 s and 0.26 s. About 2x on the worst filter, 2-11x on Sub/Up (Up 0.56 s to 0.05 s).
- Paeth is inherently sequential per channel; a pure-Python loop cannot go much further without raising complexity. A native decoder is out of scope by the owner's decision.
- Decode call sites: `adoption.py:119`, `rendering.py:39,70`, `intake/validator.py:126` decode the same preview bytes in one `adopt`; the memo removes the repeats without changing any call site.
- Memory: one decode peaks at 17.5 MiB (1024 px RGBA); the memo holds at most four decoded images.
- `test_pixels.py::test_the_pixels_layer_is_pure` allowed-import list extended with `functools` and `itertools` (stdlib).
