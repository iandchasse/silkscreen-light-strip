# DFM review: flex manufacturability (JLCPCB) and ordering files

Lens: JLCPCB flex capabilities, the Hirose FH34SRJ recommended FPC, and the Gerber/drill/BOM/CPL set.
Date: 2026-09-25. Everything below comes from checks I ran myself: pcbnew loads a read-only copy, a Gerber parser reads the files in `production/gerbers`, JLC pages were fetched today, the LCSC API was queried live, and I downloaded the EasyEDA/JLC library footprint SVGs.
No repo `.kicad_*`, lib or `tools/*.py` file was written.

Sources fetched today:
- JLC flex capabilities: https://jlcpcb.com/capabilities/flex-pcb-capabilities. It lists regular via 0.3/0.55, "PTH annular ring >= 0.25 recommended, absolute 0.18", coverlay expansion 0.1, min bridge 0.5, coverlay opening to trace >= 0.15, silk >= 1 mm / 0.15, copper to edge >= 0.3, gold finger to edge 0.2, outline +/-0.1 (+/-0.05 on request) and gold-finger thickness +/-0.03.
- JLC FPC extra charges: https://jlcpcb.com/help/article/fpc-extra-charges. Stacked stiffeners cost $8.14 + $24.44/m2. Placing a stiffener after SMT costs $8.14.
- LCSC product API, for stock.
- EasyEDA footprint SVGs: C5440667 `9b420a040f26435a80b7130ea6ec32c6.svg`, C2843774 `b881a05c57d7457395b674dce498a396.svg`, C28064 `00b75b196d3e4c479f511d6473f041cf.svg`.

## Findings (most severe first)

### DFM-1 BLOCKER (PCBA path; confidence medium): the LED placement rotation in the CPL does not match JLC's library parts, so the assembled LEDs will very likely come back reversed
- Our footprint (`LED_SideView_XINGLIGHT_XL-4008.kicad_mod`): pad 1 = K at (-1.85, 0), pad 2 = A at (+1.85, 0), light toward -y. On the board D1..D10 sit at -90, so K is at -y (for D1, pad 1 W1_2 is at y 126.66 and pad 2 W_A at y 130.36). `jlc_cpl.csv` gives Rotation 270.0 for all ten.
- JLC/EasyEDA library footprints, read from the SVGs in their 0 deg orientation (units 10 mil, SVG y down):
  - **C5440667 (WWC).** Pad "1" at (-1.85, 0), pad "2" at (+1.85, 0), both 1.60 x 1.10. A silk "+" is centred at about (-2.05, -1.43) mm, next to pad 1. A "-" on the document layer sits at about (+2.4, -1.0). A long silk line runs along y = -1.02 and a notch feature spans y -0.12..+0.37.
  - **C2843774 (UWC).** Pad "1" at (+1.85, 0) and pad "2" at (-1.85, 0), so the numbering is the opposite of WWC. The "+" is at about (-3.4, -0.1) and the "-" at about (+3.35, -0.24). The long line is again at y = -1.02, with the notch at y 0..+0.51.
  - So both library parts put the anode at -x, the long edge at -y and the notch at +y. The two libraries also disagree with each other on pad numbering.
- The datasheet (p.7 view 3 and p.8 tape) marks pin 2 "+" on the left and pin 1 "-" on the right, with the "mark" notch on pin 1. The p.8 tape symbol has its cathode toward the sprocket holes. Taking the tape view as seen from the cover tape, the part in its pocket is view 3 rotated CCW 90 with no mirror. That makes view 3 a top view, so the anode is on the left with the notched edge at the bottom. The design's `leds.md` reads view 3 as a bottom view.
- Consequence:
  - At 270 JLC turns library -x to board -y, which puts the library anode on our K pad. That holds whichever edge is the lens.
  - If the lens is the narrow 0.6 mm band (the design's assumption), our footprint is a mirror image of the real part. No rotation can fix it, and hand assembly is also wrong.
  - If the lens is the notched edge (view 3 shows a small die rectangle inside the notch, like the one in the p.7 front-view window), then the correct JLC rotation is 90. In that case the face is only about 0.4 mm ahead of the pad centreline, not 1.0.
  - The board has no LED polarity or lens silk, so JLC's engineer has nothing to check the placement against. The warm and cool library parts, with their different pad numbering, may also be placed inconsistently.
- LCSC's product photos (front/back JPGs, C5440667) confirm that the round mark in p.7 view 2 is on the rear face. They are too small to show which terminal is the anode relative to the lens.
- Fix:
  - Diode-test one loose LED to find the anode relative to the lens. It is DIY-cheap.
  - Then either mirror the pad assignment and re-route the strings (lens = narrow band), or set CPL 90 and move the footprint body/face offset (lens = notch).
  - Add a silk polarity mark and a lens-direction arrow beside each LED, outside the pads.
  - Check every LED in JLC's placement preview. The anode must land on the pad toward W_A/C_A (+y end) and the lens must face +x.

### DFM-2 MAJOR (confidence high): the BAV70W (D11, D12) CPL rotation is 180 deg off JLC's library
- EasyEDA C28064 at 0 deg (origin 398, 297.9): pad 1 at (+1.016, +0.66) mm, pad 2 at (+1.016, -0.66), pad 3 at (-1.016, 0).
- That is exactly our D11/D12 as placed at KiCad 180. For D11: pad 1 at (54.0, 135.8), pad 2 at (54.0, 134.5), pad 3 at (52.0, 135.15), relative to (53.0, 135.15).
- So JLC needs rotation 0, but `jlc_cpl.csv` says 180.0.
- As submitted, the part's common cathode (pin 3) would sit between our LED_SW and W-/C- pads, and its A1/A2 would straddle our K pad. JLC engineers usually catch pins landing off their pads in the preview, but the order should not rely on that.
- Fix: rotation 0 for D11 and D12, or a per-footprint +180 correction in `make_outputs.py`.

### DFM-3 MINOR (confidence high): the coverlay openings on all 10 warm-LED pads are 0.10 mm from other-net copper, and JLC requires >= 0.15
- The F.Cu "f_lane" track (x = 43.35, w 0.20, edge at 43.45) carries C_A and C6_7..C9_10.
- The warm pads (D1..D5, both pads) have their openings at x 43.55 (pad 43.65 minus the 0.1 expansion).
- Measured opening-to-trace is 0.100 at D1.1, D1.2, D2.1, D2.2, D3.1, D3.2, D4.1, D4.2, D5.1 and D5.2. DRC cannot see this, because mask-to-copper clearance is 0.
- Coverlay misregistration would expose the cool lane 0.2 mm from a reflowed warm pad. A solder bridge there shorts the cool and warm strings.
- Fix: move the bar's outer edge out 0.1 (outer_x 42.85; the P03 cavity has 0.5 per side) and the lane to x 43.30. That gives 0.35 to the edge and 0.15 to the opening. Alternatively, shrink the LED pad depth to 1.0.

### DFM-4 MINOR (confidence high): vias sit 0.125 mm from the LED-pad coverlay openings (same net)
- Ten vias (W1_2..W4_5, W- at 51.12, C- at 41.84) are at 1.30 mm from the pad centres along the bar.
- Via ring edge to opening edge is 0.125. JLC's opening-to-trace rule is >= 0.15, and JLC's flex guidelines blog says vias should be >= 0.2 from openings.
- A registration shift exposes the ring or hole. Solder then wicks down the 0.3 mm via and starves a 0.8 mm-tall side-view LED joint, which invites tombstoning.
- Fix: move the vias at least 0.1 mm further along the bar.

### DFM-5 MINOR (confidence high): the test-pad coverlay webs are 0.2 mm, and JLC removes webs under 0.5
- TP1..TP3 (1.1 mm pads, 1.3 mm openings) are at 1.5 mm pitch (y 134.95 / 136.45 / 137.95), so the webs are 0.2 mm.
- JLC removes webs under 0.5 mm. The result is one bare 1.3 x 4.3 mm window with 0.4 mm copper gaps between LED_SW, C- and W-, right where DIY wires get soldered.
- The vias at (58.4, 136.45) and (58.4, 137.8) are untented inside TP2 and TP1.
- Fix: use a 2.0 mm pitch, 0.9 mm pads, or stagger the pads.

### DFM-6 MINOR: the ordering package does not carry the order settings
- There is no README or ORDERING doc in the repo.
- The fab notes live only on User.Comments in the .kicad_pcb. `make_outputs.py` does not plot that layer, so JLC gets none of them.
- The note points to "gerber *-User_1", but the file is `silkscreen-light-strip-Stiffener_PI0_225.gbr`.
- Missing entirely:
  - Outline tolerance +/-0.05 on the 3.5 mm contact tab. Hirose specifies 3.5 +/-0.05, JLC's standard is +/-0.1, and +/-0.05 is only "upon request".
  - The request "finished 0.30 +/-0.03 at the gold fingers".
  - That 3M 9077 over the PI stiffener is a JLC "stacked stiffener" ($8.14 + $24.44/m2).
- JLC does not parse stiffener layers. Each option has to be selected by hand and the file named in the remark.

### DFM-7 MINOR: the Bend_Zones Gerber in the upload zip has annotation over the board
- `Bend_Zones.gbr` (FileFunction Other,User; 298 strokes) draws a rectangle inside the board.
- Its text "BEND ZONE (no stiffener, vias or pads)" spans x 58.51..59.97, y 134.62..159.18. From y 134.62 to 138.90 that is on the foot, which runs to x 60.0 there, on top of the test pads.
- JLC says annotation must not overlap the board, and unremarked extra layers are ignored or misread.
- Fix: leave this file out of the zip, or move the text off the board.

### DFM-8 MINOR: the files have no panel or fiducials for flex PCBA
- The board is 17.1 x 130.3 mm.
- JLC's FPC SMT panel rules: 70 x 70 minimum, 5 mm rails, 1 mm fiducials, and a local fiducial per unit.
- None of these is provided, so an assembled order needs "panel by JLCPCB" (extra cost) or a panel of our own.
- Hand-soldering a bare order avoids all of this, plus the $23.57 fixture fee.

### DFM-9 NOTE: finished thickness at the contacts sits low of centre
- There is no B.Cu past y 142, so the fingers have no back copper.
- JLC's formula gives 0.11 - 0.0275 - 0.012 + 0.225 = 0.2955 nominal. With JLC's +/-0.03 that is 0.2655..0.3255, and the low tail falls below Hirose's 0.27.
- JLC's own calculator picks PI 0.25 for this exact case: 0.3205, which runs high instead.
- Put the target in the remark and let JLC choose.

### DFM-10 NOTE: the tab stiffener polygon has square corners
- The polygon is a rectangle, 52.487..55.987 x 164.165..169.165, while the outline tip has R0.2 corners.
- Each corner overhangs by about 0.083 mm on the diagonal (0.0086 mm2).
- Ask JLC to cut the stiffener with the outline, or round the polygon.

### DFM-11 NOTE: silk sits on the fold line
- The fold marks are F.Silkscreen at y 142.89..143.04, inside the bend zone, on the crease itself.
- The ink will crack there. This is harmless, but the marks are better placed just outside the fold.

### DFM-12 NOTE: the vias are right at JLC's "regular" size
- Vias are 0.3/0.55 (ring 0.125). This is exactly JLC's regular flex via, with pad = hole + 0.25.
- The "PTH annular ring 0.25/0.18" row covers component PTHs, and this board has none. The DRC minimum annular is set to 0.12.
- JLC should accept these vias.

## Parts, stock and cost

- LCSC stock on 2026-09-25 (API):

  | Part | LCSC | Stock | Price |
  |---|---|---|---|
  | XL-4008WWC | C5440667 | 8,840 | $0.0648 @10 |
  | XL-4008UWC | C2843774 | 6,850 | $0.0724 @10 |
  | BAV70W,115 | C28064 | 21,660 | $0.0272 @20 |

  All three exist and match their BOM descriptions (BAV70W is common cathode). `leds.md` records all three as JLC Extended parts; I did not re-check that. Expect a feeder fee of about $3 each.
- BOM and CPL format: the headers match JLC's templates (Comment/Designator/Footprint/JLCPCB Part #; Designator/Mid X/Mid Y/Layer/Rotation). J1 and TP1..TP3 are correctly left out. The CPL Y values are negative, matching the Gerber frame. The footprint origin is the pad midpoint in both KiCad and EasyEDA for all three parts, so there is no centroid offset.
- Cost estimate (UNVERIFIED; no instant quote was run):
  - **5 bare boards**, 2L 0.11 mm, yellow coverlay, ENIG, PI 0.225 on two areas, 3M 9077 stacked: about $45-75, plus $15-25 shipping. The flex baseline is "$25 for 5 pcs", 2L is roughly 1.4-1.5x, then the PI stiffener, 3M tape and the $8.14 stacked-stiffener fee are added.
  - **2 of those assembled**: add about $65-95. That covers standard PCBA setup (about $25), stencil (about $8), FPC fixture ($23.57), 3 Extended feeder fees (about $9), parts (about $2), and the JLC panel/rails if they panelize it.
  - Total about $110-170 plus shipping.

## Verified OK
- Trace/space: min track 0.20 (0.15 in rules) and clearance 0.15, against JLC 1/3 oz 3/3 mil.
- Copper to edge >= 0.3: DRC 0 violations with edge 0.3, and I spot-checked the tail. Gold fingers are 0.20 from the tip (custom rule 0.19), 0.35 from the side edges.
- Fingers: 0.30 wide at 0.50 pitch; outer centres 0.50 from the edges (x 52.987 / 55.487 on a 52.487..55.987 tab); tab 3.50 wide; R0.2 tip corners. No paste and no silk in the contact area.
- Gang coverlay opening over the fingers: x 52.387..56.087, y 167.665..169.265. The exposed length is 1.50 from the tip, and the opening runs 0.1 past both sides and the tip.
- Tab stiffener: 5.0 mm from the tip, overlapping the coverlay edge by 3.5 mm (Hirose P >= 0.5). It ends 0.69 mm after the flare's inner arc, and the traces cross its edge perpendicular. The pin-1 silk at 4.6..5.3 mm from the tip is outside the connector.
- Bend zone y 142.3..151.5: no vias or pads, no B.Cu. All B.Cu is at y < 142, so the tail is single-layer from the fold onward. Traces run perpendicular to the fold and use arcs, with no sharp corners.
- The nearest via is 4.5 mm from the bend zone, and the bar stiffener edge (y 138.9) is 3.4 mm from it.
- Coverlay:
  - Global expansion is 0.10.
  - The SOT-323 webs are 0.65 (above 0.5) and the LED-to-LED webs are wide.
  - B.Mask has no openings, so the back is fully covered.
  - Vias are tented on both sides (no mask flashes at via locations).
  - D11.1 to the C- trace is exactly 0.150.
- Teardrops: net-assigned F.Cu/B.Cu polygons at every via/pad junction.
- Tear-stops: unnetted B.Cu arcs (w 0.3, r 1.45) at both neck-to-foot inner corners, 0.30 from the edge. The inner corners are R1.0 at the neck/foot and flare, and R0.5 at the bar/foot, which lies inside the stiffener.
- Silkscreen: text 1.0 high, 0.15 lines. The mask openings are subtracted from the silk (LPC). The only thinner stroke (0.12) outlines filled SOT-323 pin-1 triangles.
- Only one outline Gerber (`.gm1`, Profile). The User layers are FileFunction "Other,User" and do not look like outlines.
- Stiffener and adhesive layers: filled polygons in their own Gerbers.
  - Stiffener text sits outside the board: x 40.22..41.68, 1.27 mm left of the bar, and x 59.76..61.22 at y 158..175, beside the 3.5 mm tab.
  - The adhesive polygon is the same as the bar/foot stiffener.
  - Stiffener area is 338 mm2 of 451 mm2 (75%), under JLC's 90% surcharge threshold. There are 2 PI stiffeners (under the 4-stiffener threshold).
- Drill: 17 x 0.3 mm plated vias, metric Excellon, positions matching the via list. No NPTH.
- Paste: 26 openings, 20 LED pads plus 6 SOT-323, at 100%. None on the fingers or test pads.
- Gerber zip: all 13 files present, consistent with the job file.
