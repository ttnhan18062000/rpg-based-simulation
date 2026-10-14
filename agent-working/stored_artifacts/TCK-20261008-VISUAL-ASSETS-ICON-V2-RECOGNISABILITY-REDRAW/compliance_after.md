# Spec compliance of the icons AFTER the redraw (the committed `icons-v2` drafts), measured from the pixels

**`icon.item.weapon`**: all measurements within the spec

| Measurement | Spec | Measured from the pixels | |
|---|---|---|---|
| orientation | upright, point up, centred on the vertical axis | height 20 px, width 14 px, tip row 2 px wide, content centre x 11.5 of canvas centre 11.5 | ok |
| total height | 20 px | 20 px | ok |
| blade length | >= 60 % of the total height | 12 px = 60 % | ok |
| blade width | 3 to 4 px | 4 px | ok |
| crossguard width | 9 to 12 px | 12 px | ok |
| crossguard thickness | 2 px | 2 px | ok |
| grip width | never wider than the guard or the blade | 2 px (guard 12, blade 4) | ok |
| grip length | 2 to 3 px | 2 px | ok |
| pommel | present, wider than the grip | 2 row(s), 4 px wide | ok |

**`icon.marker.ruins`**: all measurements within the spec

| Measurement | Spec | Measured from the pixels | |
|---|---|---|---|
| brick courses | >= 4 alternating light and dark rows (read down the tallest column) | 4 colour bands | ok |
| broken top edge: distinct heights | >= 3 column heights | 6 ([3, 4, 7, 8, 9, 10]) | ok |
| broken top edge: U-shaped, not a slope | heights go up and down (not monotone) and the middle is lower than both ends | heights left to right [4, 4, 4, 8, 9, 7, 10, 3, 3, 3] | ok |
| fallen brick | >= 1 loose group of 2 px or more, not part of the wall | 1 ([2] px) | ok |
| nothing under the wall | no ground slab or matched pair of bricks below the wall's bottom course | 0 row(s) below the wall's bottom row | ok |
| wall width | about 10 px | 10 px | ok |

**`icon.item.trinket`**: all measurements within the spec

| Measurement | Spec | Measured from the pixels | |
|---|---|---|---|
| bail ring at the apex | a ring of 4 px or less at the top row | top row 2 px wide | ok |
| chain thickness | 1 px strands (never a ribbon) | longest horizontal run in the chain rows 1 px | ok |
| chain loop | two separate strands from the apex down to the pendant | 4 of 4 chain rows have 2 strands | ok |
| chain loop width | wider than the pendant's neck so it rises to a point: >= 12 px | 12 px | ok |
| pendant width | >= 9 px | 10 px | ok |
| pendant height | >= 8 px | 8 px | ok |
| gem | >= 5 px wide and >= 4 px tall | 6 x 5 px | ok |

**`icon.item.tool`**: all measurements within the spec

| Measurement | Spec | Measured from the pixels | |
|---|---|---|---|
| orientation | diagonal: long axis rises to the right at 35 to 55 degrees | 45 degrees | ok |
| elongation | long axis at least 2 times the short axis | 2.5 | ok |
| open jaw | a notch in the head: solidity (pixels over convex hull) at most 0.90 | 0.63 | ok |
| hole in the handle end | >= 1 enclosed hole (outline-coloured, no transparent neighbour) | 1 ([3] px) | ok |

**`icon.class.ranger`**: all measurements within the spec

| Measurement | Spec | Measured from the pixels | |
|---|---|---|---|
| orientation | vertical bow, at least 18 px tall | 18 px tall (whole icon 20) | ok |
| curved limbs | the belly stands at least 4 px away from the line between the tips | 7 px | ok |
| string | >= 14 visible string pixels | 15 px | ok |
| arrow nocked | a horizontal shaft of at least 12 px that crosses the bow | longest run 16 px | ok |
| no stock or bar | no horizontal bar thicker than 2 rows | 1 row(s) with a run of 8 px or more | ok |

**`icon.rarity.common`**: all measurements within the spec

| Measurement | Spec | Measured from the pixels | |
|---|---|---|---|
| round, not square | silhouette fills at most 80 % of its bounding box (a circle is 79 %, a square 100 %, an octagon about 88 %) | 76 % | ok |
| size | 7 px across (never the tier's 8) | 7 x 7 px | ok |
| highlight | one lighter pixel inside | 1 lighter pixel(s) among 2 fills | ok |
| distance from the tier badges | >= 3 px (I1 floor) from every tier silhouette | 9 px | ok |
