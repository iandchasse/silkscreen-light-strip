# Ordering from JLCPCB

**Rev A is untested.** Before you order, get one LED and diode-test it ([ASSEMBLY.md step 1](ASSEMBLY.md#1-check-led-polarity-before-anything-else)). LCSC sells them for a few cents, and the test settles the one assumption a reversed strip can't recover from.

One strip design fits both readers: the 4.26in panel in `enclosures/silkscreen-enclosure-claude`, and the 3.68in panel in `enclosures/silkscreen-enclosure-codex-x3`. Each case needs its light-strip front shell; the 3.68in case also needs its light-strip midplate ([ASSEMBLY.md §8](ASSEMBLY.md#8-the-case)). You can order and bench-test the strip before printing either.

## Files

| File | Use |
|---|---|
| `production/silkscreen-light-strip_rev-A_gerbers.zip` | Upload this to the flex order. It holds the copper, coverlay (mask), silk, paste, outline and drill files, plus two extra layers: `…-Stiffener_PI0_225.gbr` and `…-Adhesive_3M9077.gbr`. |
| `production/jlc_bom.csv`, `production/jlc_cpl.csv` | Only for an assembled order |
| `production/bom.csv` | Parts list for hand assembly or an LCSC order |

JLC does not read the stiffener or tape layers automatically. You have to choose them on the form and name the files in the remark, as below.

## Order form (Flex PCB)

| Field | Setting |
|---|---|
| Base material | **Flex** |
| Layers | **2** |
| Dimensions | Taken from the outline, about 15.1 × 127.6 mm |
| Quantity | 5, the minimum |
| FPC thickness | **0.11 mm** (25 µm PI core) |
| Copper | 1/3 oz (12 µm), the standard for 2-layer 0.11 mm |
| Coverlay colour | **Black**. It hides under the bezel and doesn't reflect amber. Yellow works if you prefer the cheaper default. |
| Silkscreen | **White** |
| Surface finish | **ENIG**, 1 U″. 2 U″ is worth it if you expect to re-insert the tail often; J3 is rated for 20 cycles. |
| Stiffener | **PI, 0.225 mm**. On the bottom side, in the three areas in `…-Stiffener_PI0_225.gbr`. |
| 3M tape | **3M 9077** (0.05 mm, heat-resistant). On the bottom side of the two front stiffener pieces, in `…-Adhesive_3M9077.gbr`, stacked on the PI stiffener. |
| EMI shielding film | No |
| Outline tolerance | Ask for ± 0.05 mm (see the remark). The standard is ± 0.1. |

**Remark** (paste as is):

> Stiffener: PI 0.225 mm on the BOTTOM side, three filled areas in silkscreen-light-strip-Stiffener_PI0_225.gbr (the short piece under the top LED pair, the LED bar + foot, and the last 14 mm of the tail). Leave the 3.6 mm gap between the top piece and the bar BARE: it is a fold hinge (no stiffener, no tape). 3M 9077 tape on the BOTTOM side of the top piece and of the LED bar + foot only, over the PI stiffener (stacked), areas in silkscreen-light-strip-Adhesive_3M9077.gbr. The gold fingers at the tail tip mate a Hirose FH34SRJ ZIF connector, which needs 0.30 +/-0.03 mm FPC thickness at the fingers. Please use PI 0.225 mm for all stiffener areas and do not change it to 0.25 mm: with no copper behind the fingers your formula gives 0.11 - 0.0275 - 0.012 + 0.225 = 0.2955 mm, the closest of your PI options. Please keep the finished finger-area thickness within 0.27-0.33 mm, and the 3.50 mm contact tab width within +/-0.05 mm. Cut the tip stiffener with the board outline (R0.2 tip corners).

**Why the thickness remark.** No PI option lands exactly on 0.30:

- **0.225** gives 0.2955 nominal. With JLC's ± 0.03 its low end is 0.2655, 4.5 µm under Hirose's 0.27.
- **0.25** gives 0.3205. JLC's own calculator rounds up to this one, but its high end is 0.3505, well over Hirose's 0.33.

So the remark fixes 0.225 and asks JLC to hold the low side. JLC's capability page also recommends 0.225 mm for a 0.3 mm contact on 0.11 mm flex.

After upload, check the online Gerber viewer:

- the outline is one closed shape with rounded corners;
- the six gold fingers are at the narrow tip;
- three stiffener areas: the short top piece, the long bar/foot, and the tail end, with a bare gap between the first two.

## Bare board or assembled?

**Bare, soldered by hand (recommended for rev A).** It is cheap and simple, and it lets you do the polarity test first. Order the parts from LCSC. Buy spares, since each part costs a few cents:

| Part | LCSC | Need | Suggested |
|---|---|---|---|
| XINGLIGHT XL-4008WWC (warm) | C5440667 | 6 per strip | 10–20 |
| XINGLIGHT XL-4008UWC (cool) | C2843774 | 6 per strip | 10–20 |
| Nexperia BAV70W,115 | C28064 | 2 per strip | 20 (LCSC sells it in multiples of 20; also stocked at DigiKey) |

**Assembled by JLC.** This is possible, but costs more and has more to check:

- **Assembly service.** Flex assembly needs a fixture ($23.57) and a panel with rails and fiducials. The files don't include one, so choose **"Panel by JLCPCB"**. Use Standard PCBA.
- **Parts.** All three parts are JLC **Extended** parts, so expect a feeder fee of about $3 each.
- **Files.** Upload `jlc_bom.csv` and `jlc_cpl.csv`. The CPL already carries the rotation corrections for JLC's library footprints (SOT-323 +180°, LED 0°).
- **Check every part in the placement preview:**
  - **LEDs:** the window faces the bar's **inner** edge, toward the screen side. The anode goes on the upper pad, toward the rounded top end. The cathode goes on the pad with the short white silk bar.
    - JLC's polarity dot sits at opposite ends for the two parts: on the anode (upper) pad for the warm C5440667, and on the cathode (lower) pad for the cool C2843774.
    - Judge by the window direction and the anode position, not the dot.
    - Tell JLC not to rotate the warm LEDs to line up the dots. Rotating a side-view LED turns its light away from the screen.
  - **Warm/cool:** warm (C5440667) in the lower position of each pair, D1–D6; cool (C2843774) in the upper, D7–D12.
  - **BAV70W (D13, D14):** the single pin (pin 3) points toward the LED end.

  If any of these looks wrong, fix it in the preview or ask JLC before paying. A reversed side-view LED can't be corrected afterwards.

## Cost ballpark

This is unverified: no instant quote has been run with these files. Upload the zip to get the real figure.

| | Estimate |
|---|---|
| 5 bare flex (2L 0.11 mm, ENIG, PI stiffener in three areas, 3M 9077 stacked) | about $45–75, plus $15–25 shipping. Black coverlay may add a little. |
| LEDs and diodes for hand assembly (with spares) | a few dollars, plus LCSC shipping |
| Assembly of 2 of the 5 by JLC | add about $65–95: setup, stencil, FPC fixture, 3 Extended-part fees, parts and the panel |

## Before you pay

- [ ] One LED diode-tested ([ASSEMBLY.md step 1](ASSEMBLY.md#1-check-led-polarity-before-anything-else))
- [ ] Your panel is a plain **GDEY0426T82** (no bonded frontlight) or the **3.68in 528 × 792** panel of the x3 build
- [ ] The main board has the frontlight driver populated (U10, Q5, Q6, R37, J3). The trimmed x3 board keeps all of it.
- [ ] You will print that case's light-strip parts ([ASSEMBLY.md §8](ASSEMBLY.md#8-the-case))
- [ ] FPC thickness 0.11, black coverlay, ENIG, PI 0.225 stiffener (not 0.25) in three areas, 3M 9077 stacked, and the remark pasted
