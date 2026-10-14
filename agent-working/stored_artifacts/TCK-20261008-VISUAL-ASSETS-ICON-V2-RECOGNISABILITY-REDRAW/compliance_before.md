# Spec compliance of the icons BEFORE the redraw (drafts at 2d5742368 / the 4b state), measured from the pixels

**`icon.item.weapon`**: SPEC NOT MET

| Measurement | Spec | Measured from the pixels | |
|---|---|---|---|
| measurable | every part named in the spec can be found in the pixels | could not be measured (IndexError: list index out of range) | **FAIL** |

**`icon.marker.ruins`**: SPEC NOT MET

| Measurement | Spec | Measured from the pixels | |
|---|---|---|---|
| brick courses | >= 4 alternating light and dark rows (read down the tallest column) | 3 colour bands | **FAIL** |
| broken top edge: distinct heights | >= 3 column heights | 5 ([3, 4, 7, 9, 11]) | ok |
| broken top edge: U-shaped, not a slope | heights go up and down (not monotone) and the middle is lower than both ends | heights left to right [11, 4, 3, 7, 4, 9, 9, 7, 9, 7] | **FAIL** |
| fallen brick | >= 1 loose group of 2 px or more, not part of the wall | 0 ([] px) | **FAIL** |
| nothing under the wall | no ground slab or matched pair of bricks below the wall's bottom course | 0 row(s) below the wall's bottom row | ok |
| wall width | about 10 px | 10 px | ok |

**`icon.item.trinket`**: SPEC NOT MET

| Measurement | Spec | Measured from the pixels | |
|---|---|---|---|
| bail ring at the apex | a ring of 4 px or less at the top row | top row 4 px wide | ok |
| chain thickness | 1 px strands (never a ribbon) | longest horizontal run in the chain rows 2 px | ok |
| chain loop | two separate strands from the apex down to the pendant | 5 of 5 chain rows have 2 strands | ok |
| chain loop width | wider than the pendant's neck so it rises to a point: >= 12 px | 9 px | **FAIL** |
| pendant width | >= 9 px | 10 px | ok |
| pendant height | >= 8 px | 9 px | ok |
| gem | >= 5 px wide and >= 4 px tall | 6 x 5 px | ok |

**`icon.item.tool`**: SPEC NOT MET

| Measurement | Spec | Measured from the pixels | |
|---|---|---|---|
| orientation | diagonal: long axis rises to the right at 35 to 55 degrees | 47 degrees | ok |
| elongation | long axis at least 2 times the short axis | 1.5 | **FAIL** |
| open jaw | a notch in the head: solidity (pixels over convex hull) at most 0.90 | 0.55 | ok |
| hole in the handle end | >= 1 enclosed hole (outline-coloured, no transparent neighbour) | 0 ([] px) | **FAIL** |

**`icon.class.ranger`**: SPEC NOT MET

| Measurement | Spec | Measured from the pixels | |
|---|---|---|---|
| orientation | vertical bow, at least 18 px tall | 18 px tall (whole icon 20) | ok |
| curved limbs | the belly stands at least 4 px away from the line between the tips | 0 px | **FAIL** |
| string | >= 14 visible string pixels | 17 px | ok |
| arrow nocked | a horizontal shaft of at least 12 px that crosses the bow | longest run 16 px | ok |
| no stock or bar | no horizontal bar thicker than 2 rows | 1 row(s) with a run of 8 px or more | ok |

**`icon.rarity.common`**: SPEC NOT MET

| Measurement | Spec | Measured from the pixels | |
|---|---|---|---|
| round, not square | silhouette fills at most 80 % of its bounding box (a circle is 79 %, a square 100 %, an octagon about 88 %) | 89 % | **FAIL** |
| size | 7 px across (never the tier's 8) | 6 x 6 px | **FAIL** |
| highlight | one lighter pixel inside | 1 lighter pixel(s) among 2 fills | ok |
| distance from the tier badges | >= 3 px (I1 floor) from every tier silhouette | 8 px | ok |
