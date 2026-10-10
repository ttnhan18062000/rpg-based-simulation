---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261010-VISUAL-ASSETS-PNG-DECODER-SPEEDUP
artifact_type: plan
tags: [architecture, security, testing]
---

# Plan: PNG decoder speed-up (pure Python, bounds unchanged)

1. `pixels._unfilter`: per-channel slice work. Sub = running sum (`itertools.accumulate`, masked with `(255).__and__`), Up = one big-integer SWAR add (`_add_bytes`), Average/Paeth = per-channel loops over `zip(line[ch::bpp], prev[ch::bpp])` with the left and up-left neighbours carried in locals; row 0 uses an all-zero previous row (no special case).
2. `decode_png` memoised (`lru_cache`, 4 entries, key = bytes + dimension limit + decoded-size bound); refusals are never cached; `adopt`/`review`/`intake` decode a preview once.
3. Proof: the pre-change loop is kept verbatim in `tests/.../test_pixels_unfilter.py::reference_unfilter`; random rows (every filter, 1-4 channels, widths 1..33, mixed filters) and EVERY committed PNG compare equal (RGBA and pixel hash). Safety bounds untouched (`test_pixels.py` malformed/oversized tests unchanged and green).
4. Re-measure with the same method; update budgets.md F3 and the MAX_PREVIEW_DIM row. No bound raised.
5. Security review (untrusted-input parser).

## Proof Plan
Equality over the committed corpus (>100 PNGs) against the old loop; 6 mutants (SWAR add, Paeth tie/neighbour, Average, Sub mask, Paeth c-carry, decoded-size guard) killed; the Paeth `<` vs `<=` tie mutant is equivalent (when pa == pb != 0 and a != b, pc is 0 so pa <= pc is false: unreachable branch).
