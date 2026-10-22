# Mechanical fit of the light-strip flex (research notes)

Status: COMPLETE for the first pass (2026-09-24). Anything not read from a source is marked UNVERIFIED.

Coordinate conventions (from the project context):
- **Main board KiCad coordinates**: mm, viewed from the FRONT (screen) side, x to the right, y downward.
- **Enclosure frame**: X = KiCad x - 44.24, Y = 148.25 - KiCad y, +Z toward the reader. The PCB occupies Z 0..1.6
  (the back copper is at Z 0) and the panel rear plane is at Z 4.0.
- "Panel left edge" means the left edge as seen from the front. It is KiCad x 43.055 (enclosure X -1.185).

Sources used (all read in this session):
- [FT01C] `[an earlier case project, not in this repo]\references\GDEQ0426T82-FT01C.pdf`
  (1 page, rendered with pymupdf).
- [GD457] https://www.good-display.com/product/457.html (GDEY0426T82 product page).
- [GDEQ] GDEQ0426T82 specification, "4 Mechanical Drawing of EPD module", page 5/23, Rev 01, 2022-10-08.
  Fetched from https://www.laskakit.cz/user/related_files/gdeq0426t82.pdf and rendered with pymupdf.
  The GDEY0426T82 spec PDF (https://v4.cecdn.yun300.cn/100001_1909185148/GDEY0426T82.pdf, and the download page
  https://www.good-display.com/companyfile/2000.html) returned HTTP 403 / a download page only.
- [H25] Hirose FH34 catalog, Mar. 2025. Fetched from
  https://www.hirose.com/en/product/document?clcode=&productname=&series=FH34SRJ&documenttype=Catalog&lang=en&documentid=en_FH34_CAT ;
  pages 1-8, 14 and 16-18 read.
- [PCB] `silkscreen-pcb\silkscreen_pcb.kicad_pcb`, loaded
  read-only with pcbnew in KiCad 9.0 python (not saved).
- [AUDIT] `[an earlier case project, not in this repo]\design\MECHANICAL-AUDIT.md`.
- [PARAM] `[an earlier case project, not in this repo]\design\parameters.json`.
- [BUILD] `[an earlier case project, not in this repo]\design\build_enclosure.py`
  (P03 bezel, carrier and shelf geometry, lines 170-200 and 370-417).
- Sibling notes: `docs\research\leds.md` (LED package sizes) and `docs\research\fpc-and-jlc-flex.md` (JLC flex
  thickness, stiffeners, bend-radius rule).

---

## 1. Panel geometry

### 1a. GDEQ0426T82-FT01C (touch + frontlight) [FT01C]
- EPD outline 62.37 +/-0.15 x 105.33 +/-0.2 (the drawing labels it "(EPD)"). LGP 61.40 x 103.60. Touch panel outline
  (TP OD) 61.50 x 99.70. The TP/LGP insets from the EPD edge are 0.47 / 0.42 on the long sides and 0.15 / 0.43 at the top.
- Z stack, front to back:
  - 0.30 ITO film + AG
  - 0.18 OCA2
  - 0.40 LGP
  - 0.18 OCA3
  - 0.93 EPD
  - Total 1.98 +/-0.2.
- The drawing does not dimension the active area. It comes from the plain-panel spec (see 1b).
- All tails exit the BOTTOM short edge, which is the FPC bond edge.
  - **Frontlight (FL) tail**, 6 pins:
    - Exits 10.00 mm from the panel's left edge. The back view shows "10.00" from the right edge, which is the left
      edge when seen from the front.
    - That puts it at KiCad x ~53.06..56.56 (center ~54.8), which is the same place the new neck uses (section 4).
    - Contact end: 0.30 +/-0.05 fingers at 0.50 +/-0.05 pitch, 2.50 +/-0.07 span, tail width 3.50 +/-0.1.
    - The tail end is 24.00 mm below the panel edge.
  - **EPD tail**, 24 pins: contact end 12.50 wide. The pin-1 end is 24.85 from the left edge. A "Bending Area" is
    marked just below the glass.
  - **CTP tail** (touch, with the touch-IC "Device area" and a steel stiffener): 10.00 from the RIGHT edge.
- **Contact face**: the note "FPC+PI thickness 0.3mm" points to the tail ends in the BACK view, which shows the PI
  stiffener outline. The FRONT view shows the hatched gold fingers. So with the tail laid flat (unfolded), the fingers
  face the same way as the display surface, and the PI stiffener is on the rear face.
- **FL pin table on the drawing**: 1 LED W-, 2 LED W+, 3 NC, 4 NC, 5 LED C-, 6 LED C+.
  - Electrical: "COLD 5PCS LED VF<=15V IF<=15mA", "WARM 5PCS LED VF<=15V IF<=15mA".
  - A row of LED packages is drawn along the bottom edge of the LGP, so the stock frontlight is edge-lit from the
    BOTTOM into a 0.40 mm light guide.

### 1b. Plain panel GDEY0426T82 [GD457] + drawing [GDEQ]
| Item | Value | Source |
|---|---|---|
| Outline (glass, "TFT OD") | 105.33 +/-0.1 x 62.37 +/-0.1 | [GD457] "105.33*62.37*0.926"; [GDEQ] callouts 6 and 1 |
| Thickness | 0.926 +/-0.1 "without protective film of PS and pull tape" | [GD457], [GDEQ] callout 13 |
| Stack | 0.5 TFT glass + 0.17 FPL + 0.256 PS (+0.065 removable protective film) | [GDEQ] side view |
| Active area | 92.8 x 55.68, pixel pitch 0.116 | [GD457], [GDEQ] |
| PS (top sheet) | 100.83 +/-0.2 x 60.77 +/-0.2. Insets from the glass edge: 0.8 +/-0.2 each long side, 0.5 +/-0.2 top, 4.0 bottom | [GDEQ] callouts 7, 2, 4, 9 |
| FPL (e-ink film) | 98.43 +/-0.2 x 58.37 +/-0.2. Insets: 2.0 +/-0.2 long sides, 1.7 +/-0.2 top, 5.2 bottom | [GDEQ] callouts 8, 3, 5, 10 |
| Border ring | 94 x 56.88. Insets (2.75) long sides, (2.14) top | [GDEQ] |
| Active-area insets | 3.35 each long side, 2.74 top, 9.79 bottom (= 105.33 - 92.8 - 2.74) | [GDEQ] |
| EPD FPC | Exits the bottom edge 15.45 +/-0.3 from the left edge, 31.3 +/-0.2 wide at the glass. Tail 24 +/-0.3 long. Contact end 12.5 +/-0.1 wide, pin 1 at 24.85 +/-0.3 from the left edge. FPC+PI 0.3 +/-0.03 | [GDEQ] callouts 11, 12, 14, 15 |
| Bottom ledge | Bare TFT glass (no PS/FPL) for 4.0 mm from the bottom edge. Carries the COG IC with a "Silicone Cover IC" and a "Max 1" callout (see note) | [GDEQ] side view |
| Pull tape | Hatched tab at the bottom-left corner (about 0.8..7 mm from the left edge; the position was scaled off the drawing, UNVERIFIED) | [GDEQ] front view |

Notes on 1b:
- The task context gives 3.345 / 2.715 / 9.815 mm for the side / top / bottom borders. The drawing gives 3.35 / 2.74 /
  9.79. The difference is 0.025 mm, which is within tolerance. The enclosure uses an active-area center 3.55 mm above
  the panel center [PARAM]; the drawing implies 3.525.
- Both [GD457] and the GDEQ spec list the same glass: 105.33 x 62.37 x 0.926 with a 92.8 x 55.68 active area. I used
  GDEQ0426T82's drawing because the GDEY PDF was blocked (403). That the two drawings are identical is UNVERIFIED.
- The "Max 1" callout sits by the silicone and pull tape at the FPC end. It probably means the silicone or tape may
  stand up to 1 mm proud of the glass edge. UNVERIFIED.
- **Is the front border flat where a strip could lie?**
  - Long edges: the top surface is the PS, and it is flat from its edge inward. The PS edge is 0.8 +/-0.2 mm in from the
    glass edge, so the flat surface is guaranteed from 1.0 mm in. Between 0.8 and 2.0 mm the PS overhangs the FPL edge;
    the edge seal under that overhang is not shown (assumed flat, UNVERIFIED).
  - The outer 0.8 +/-0.2 mm is bare 0.5 mm glass, a 0.426 mm step DOWN from the PS surface.
  - Bottom edge: the outer 4.0 mm is a bare-glass ledge with the IC, silicone and FPC bond, so it is not flat. The flat PS
    zone under the bezel on the bottom is 4.0..9.09 mm from the edge.

Main-board placement (enclosure and PCB) of the plain panel. The rear plane is at Z 4.0 [PARAM]:
- Panel: KiCad x 43.055..105.425, y 37.635..142.965.
- Active area: x 46.405..102.075, y 40.35..133.15.
- Bezel aperture (active + 0.7 mm per side, 57.08 x 94.20 [AUDIT]): x 45.70..102.78, y 39.65..133.85.
- Front surface: Z 4.926 with the protective film removed, 4.991 with it on.

---

## 2. Frontlight connector (J3): insertion direction and contact face

Facts [PCB]:

**J3**: FH34SRJ-6S-0.5SH(50) on B.Cu, rot 180, at (54.237, 126.0).

| Pad | Position (x, y) | Size | Net |
|---|---|---|---|
| 1 | (52.987, 124.575) | 0.30 x 1.15 | LED_SW |
| 2 | (53.487, 124.575) | 0.30 x 1.15 | C- |
| 3 | (53.987, 124.575) | 0.30 x 1.15 | NC |
| 4 | (54.487, 124.575) | 0.30 x 1.15 | NC |
| 5 | (54.987, 124.575) | 0.30 x 1.15 | LED_SW |
| 6 | (55.487, 124.575) | 0.30 x 1.15 | W- |
| S1 (fitting nail) | (51.737, 127.5) | | GND |
| S2 (fitting nail) | (56.737, 127.5) | | GND |

- J3 STEP solid bounds [AUDIT]: enclosure X 7.497..12.497, Y 20.35..23.60, Z -1.855..-0.085. That is KiCad
  y 124.65..127.90, so the connector mouth is at y ~127.9.

**FPC slot in Edge.Cuts** [PCB]:
- It is a trapezoid with corners (51.26, 142.5), (51.86, 141.2), (97.76, 141.2), (98.30, 142.5). So it is 1.3 mm wide,
  spans y 141.2..142.5 and x ~51.3..98.3.
- It lies 0.47..1.77 mm INSIDE the panel's bottom edge (y 142.965).
- J2 (the display connector), J3 (the frontlight connector) and J4 (the touch connector) all sit 13-17 mm above the slot on the back, with their fitting-nail side facing
  the slot.

**FH34SRJ** [H25]:
- "Top and Bottom Contact" back-flip connector. Horizontal FPC retention is about 3.0 N in top contact and 6.0 N in
  bottom contact (from the Hirose series search summary).
- FPC t = 0.3 +/-0.03, gold plated. Mating durability 20 cycles.
- The recommended FPC outline has corner R0.2 +/-0.1. It marks "Contact No.1 (Top Contact)" and "Contact No.1 (Bottom
  Contact)" at opposite ends: flipping the FPC face mirrors the numbering.
- "this connector uses a back flip type structure, and the FPC insertion direction and actuator are in different
  directions". The FPC must be inserted "horizontal to the board", and routed with no strain and with the stiffener
  "parallel to the PCB".
- Connector table for 6 pos: A 5.0, B 2.5, C 3.53, D 4.38, depth (2.9) body / (3.8) overall, height 1.0.

**Conclusion: direction of approach**
- The tail must reach J3 travelling in the **KiCad -y direction** (toward the top of the board).
- It comes up from the bottom-edge FPC slot (y 141.2..142.5) along the board's BACK face.
- It enters the connector mouth on J3's +y face (the fitting-nail side, y ~127.9). The actuator and signal leads are on
  the -y (rear) side at y ~124.6.
- In the enclosure frame, the tail travels +Y from the slot (Y 5.75..7.05) to the mouth (Y 20.35).
- Insert with the actuator open until the tip reaches about y 125.0. That is ~2.9 mm past the mouth; the exact stop
  is UNVERIFIED, +/-0.3.
- Evidence:
  - The back-flip construction.
  - The slot and nails being on the same side.
  - The stock 24.0 mm FL tail reaching exactly this far (section 4 computes 24.2 mm for the same path).

**Conclusion: contact face**
- Any path from the panel front, over the panel's bottom edge, through the slot, and back up toward J3 is a net 180 deg
  rotation about the X axis.
- So the flex face that faces the reader on the panel (the LED side, F.Cu) faces AWAY from the board (-Z) at J3.
- => **Put the gold fingers on the same side as the LEDs (F.Cu).** They then mate with J3's **top contacts**.
  - FH34SRJ supports this (top-contact retention ~3.0 N).
  - A single-layer flex (LEDs, traces and fingers all on F.Cu) is enough.
  - The PI stiffener (JLC 0.225/0.25 mm on a 0.11 mm flex, giving 0.3 +/-0.03; see fpc-and-jlc-flex.md) goes on the
    B side, under the fingers, facing the board.
- This is the same face orientation the stock FT01C tail has: fingers on the display-facing side when flat.

**Finger order**
- The fold preserves KiCad x, so each finger lands on the J3 pad at the same x.
- Draw the flex flat as it lies on the panel, seen from the LED side, with the tail hanging toward +y. Its fingers,
  left to right (x 52.987 -> 55.487), must be: **LED_SW, C-, NC, NC, LED_SW, W-** (J3 pads 1..6).
- Cross-check with the EPD tail:
  - The EPD pin 1 is 24.85 mm from the left edge, which is KiCad x 67.9.
  - J2 pin 1 is at x 67.737 and pin 24 at 79.237, which matches the drawing's 11.5 span.
  - So the x-preserving model is confirmed on J2.
- Map the fingers by J3 pad net, never by the panel's FL pin numbers.

---

## 3. Edge choice -> (a) LEFT long edge

| Edge | Border under bezel | Light throw | Tail route to J3 | Verdict |
|---|---|---|---|---|
| (a) Left long | 2.645 mm (panel edge x 43.055 to aperture edge x 45.70). The PS surface is flat from ~1.0 mm in | 55.68 mm (short axis) | The bar's lower end jogs in-plane under the bottom bezel to x 52.6..57.0, then follows the STOCK FL-tail path: over the glass edge, through the existing slot, ~13 mm to J3. No new enclosure path | **Chosen** |
| (b) Top short | 2.74 - 0.7 = 2.04 mm | 92.8 mm | ~100 mm tail. The board has no top edge at x 44..86 (battery notch, battery cavity), so the tail would cross the battery | Rejected |
| (c) Right long | 2.645 mm | 55.68 mm | Would need either a wrap at the right edge or a bottom-right slot exit, then ~45 mm across the back over J4 (x 90.3..96.2) and J2 (x 66.2..80.8) and their tails. The USB-C socket J1 and the reset button SW11 are also near the right edge | Rejected as the primary. Possible as an ADD-ON bar joined by a bridge under the bottom bezel (y 134.3..137.3, on the flat PS, clear of the ledge and IC) |
| (d) Bottom | 9.09 mm under the bezel, but the outer 4.0 mm is the bare-glass ledge with the COG IC, silicone and EPD FPC bond (GD: keep the bond/FPC area unloaded [AUDIT]). The flat PS zone is 5.1 mm | 92.8 mm (long axis) | Short | Rejected: long throw, and it shares the sensitive bond/bend zone with the EPD FPC |

Why the left edge:
- It is the shortest route. The stock FL tail already leaves the panel 10 mm from the left edge, right above J3.
- **Wraps around the side edges are not possible in P03.**
  - The glass cavity is only 0.515 mm per side [BUILD: cavity X -1.70..61.70 vs panel X -1.185..61.185].
  - The carrier side rail is at X -3.1..-1.7.
  - So the flex must fold over the bottom edge, where [BUILD] deliberately provides:
    - a bezel FPC relief at X 4.5..55.5, Y 3.8..6.4, Z 4.5..6.45;
    - an open carrier shelf at X 0.10..59.9, Y 3.5..9.0.
- The left side buttons SW5/SW7 (KiCad y 67..92) and the right ones are all on B.Cu at the board plane. The bar sits on
  the panel front, so they don't interfere.
- The battery notch and the mounting holes H2 and H3 are not touched.

---

## 4. Flex geometry for the recommended edge

Assumptions:
- Single-layer JLC flex, 25 um PI core, ~0.11 mm finished [fpc-and-jlc-flex.md]. With t = 0.11, JLC's "single layer
  >= 6x total thickness" gives R_min ~0.66 mm.
- LED pair: XL-4008 side view, 4.0 x 1.4 (depth) x 0.8 (height) mm, emitting face 4.0 x 0.8 on the side away from the
  terminals [leds.md].
- Coordinates are main-board KiCad unless stated otherwise.

### 4a. Plan view (front, flat pattern = as laid on the panel; the tail unrolled toward +y)
```
KiCad x:  43.055   45.0 45.2 45.70  46.405                                    52.6        57.0  58.5
            |        |    |    |      |                                         |           |     |
 y 38.9     (====)   :    :    :      :   <- bar top, full-round end (R1.07)
            |    |   :    :    :      :
            |[ ]>|   :    :    :      :   [ ]> side-view LED, face at x 45.0 (0.7 behind the bezel aperture
            |    |   :    :    :      :        edge x 45.70, 1.4 outside the active edge x 46.405),
            |[ ]>|   :    :    :      :        light travels +x across the 55.68 mm active width
            |    | bar 2.15 wide (x 43.055..45.2), max 2.6
            | .. |   (LED row spans the active height y 40.35..133.15)
            |[ ]>|   :  bezel   active
 y 134.0    |    |\  : aperture  edge
            |     \`-._ arc1 (centerline R3.0, inner R1.9)
 y 137.0     `-.    `-.________________________  straight, width tapers 2.15 -> 4.4
                `-.___________________________ `-._  arc2 (centerline R3.4, inner R1.2)
                                                    \  \
 y 138.965 ...... PS edge (step down 0.43 onto the glass ledge) ...
 y 140.4                                            |   |   neck 4.4 wide (x 52.6..57.0)
 y 142.965 ==== panel bottom glass edge == FOLD LINE =|===|====   EPD FPC starts at x 58.5 +/-0.3
                                                    |   |   (tail continues, folded under; see 4b)
 back side:                                         |   |   ~13 mm run on the board back
 y ~129                                             |  /    taper to the 3.5 tab (R>=1 fillet)
 y 127.9 J3 mouth                                   |_|     tab 3.5 wide, x 52.487..55.987, corners R0.2
 y ~125.0 tip                                       6 fingers, F side: LED_SW, C-, NC, NC, LED_SW, W-
```
Everything to the right of x 45.70 lies below y 133.85, i.e. hidden under the bottom bezel:
- arc1's inner edge crosses x 45.70 at y 135.3;
- arc2's outer edge reaches up to y 134.8.

### 4b. Cross-section through the neck (section plane x ~54.8, looking toward +x; y to the right = toward the board's bottom edge)
```
Z
6.50 ______________ bezel underside (P03) ______________.   bezel FPC relief to y 144.45 (Z 4.5..6.45)
                                                        :
4.93 ====PS/FPL========.                                :
4.50 ~~flex~~~~~~~~~~~~~\~~~~~~~~~~~~~~~~~~~~~~~~~~~.   :   flex on the glass ledge (tape 0.05)
4.00 ###### TFT glass 0.5 thick #################### ) U  : U-wrap 180 deg, R_in 0.8, center (143.2, 3.75)
        (panel)                                  ___/   : outer surface reaches y 144.11
2.95                          B2 _.-------------'  bottom leg (Z 2.84..2.95), y 142.76..143.2
2.14                            /  R_in 0.7              . SW9 pad-4 THT lead tip on the FRONT
                               |                        (x 51.3..53.2, y >= 142.98, Z <= ~2.3)
1.60 ===== PCB front ==========| |=========================
     PCB 1.6 thick        slot | |  (y 141.2 .. 142.5)
0.00 ===== PCB back ===========|_|====================== SW9 body on the back, y >= 142.77
-0.86 <-- ~13 mm back run --- B3 R_in 0.8   (the flex lies F side down, facing away from the board)
     to J3 mouth y 127.9, tip ~125.0 (J3 FPC opening at about Z -0.3..-0.6, UNVERIFIED)

y:  125.0   127.9           141.145 142.0 142.5 142.965  143.2   144.11
```

SW9 in the diagram is the Back button, the leftmost bottom-row button.

### 4c. Segments (centerline lengths, t = 0.11 mm, mid-plane radius = R_in + 0.055)

Front side, on the panel:
| # | Segment | Where | Length | Radius |
|---|---|---|---|---|
| F1 | LED bar, straight | x 43.055..45.2, y 38.9 -> 134.0 | 95.1 | full-round top end R1.07 |
| F2 | arc1, in-plane 90 deg left turn | center (47.13, 134.0) | 4.71 | centerline 3.0, inner 1.93 |
| F3 | horizontal run | y 137.0, x 47.13 -> 51.4, width 2.15 -> 4.4, on the flat PS | 4.27 | - |
| F4 | arc2, in-plane 90 deg right turn | center (51.4, 140.4); crosses the PS step at y 138.965 | 5.34 | centerline 3.4, inner 1.2 |
| F5 | neck on the glass ledge | x 52.6..57.0, y 140.4 -> 142.965 | 2.57 | - |
|    | **Front total** | | **~112.0 mm** | |

Tail, from the fold line at the glass edge (y 142.965) to the contact tip:
| # | Segment | Where | Length | Radius |
|---|---|---|---|---|
| T1 | overhang past the glass edge before the wrap | | 0.24 | - |
| T2 | U-wrap 180 deg around the bottom glass edge | Z 4.55 -> 2.95 | 2.69 | R_in 0.8; available 0.66..~1.0 (limited by the bezel/cavity relief y <= 144.45 and the SW9 lead below) |
| T3 | bottom leg under the panel, heading -y | Z ~2.9 | 0.45 | - |
| T4 | B2, 90 deg down into the slot | | 1.19 | R_in 0.7; available up to ~1.1 |
| T5 | vertical leg through the gap and the slot | y 142.0, Z 2.14 -> 0 | 2.14 | - |
| T6 | B3, 90 deg on the board back, toward J3 | | 1.34 | R_in 0.8; 0.66..~2 usable. Larger R just lowers the run, which then ramps up to J3's opening over 13 mm |
| T7 | back run to the contact tip | y 141.145 -> ~125.0, including ~2.9 inside J3 | 16.15 | - |
|    | **Nominal tail** | | **24.2 mm** | |

- The stock FT01C FL tail is 24.00 mm from the panel edge, which is consistent.
- **Service allowance: +5 mm, so a recommended tail of 29 mm (fold line -> tip).**
  - The slack lies as an arch in the rear service well (52 x 24 mm, ~4-5 mm deep [AUDIT]).
  - For a 13.2 mm free span, the arch height is about 0.64*sqrt(dL*L): +3 mm -> 4.0 mm tall, +5 mm -> 5.2 mm tall.
  - If the rear cover presses on it, trim to +3 mm (27 mm), or tape the slack down as a shallow S with R >= 1 mm.
- Flat centerline total: ~136 mm nominal, ~141 mm with the slack.
- Silkscreen a fold-line mark on the neck at the glass-edge position.

Widths:
- **Tail/neck: 4.4 mm (x 52.6..57.0) from the panel edge to ~1 mm behind the J3 mouth.** The width is bounded by:
  - the resistors R60 (the Right button's ladder resistor) and R50 (the W- bleeder) on the left at x <= 52.4 (back);
  - the TP5 pad (the W- test point) on the right at x >= 57.15, y 134.6..136.3 (TP5 is an F.Cu pin-header footprint whose attributes
    = 257 = through-hole + DNP in [PCB], so it is a bare pad);
  - the EPD FPC at x >= 58.5 +/-0.3 at the panel edge;
  - the slot's left end at x 51.86.
- Then taper with R >= 1 mm fillets to the 3.5 mm tab (x 52.487..55.987). The tab corners are R0.2 +/-0.1 [H25].

Contact end [H25] (details in fpc-and-jlc-flex.md):
- 0.3 +/-0.03 thick over the stiffener.
- Stiffener ~2.5 +/-0.3 long from the tip, overlapping the coverlay edge by >= 0.5 mm.
- Fingers 0.3 +/-0.03 wide at 0.5 pitch.

### 4d. LED bar geometry
- **Length**: bar from y 38.9 to y 134.0 (95.1 mm straight), plus the jog. The top end is 1.27 mm below the panel top
  edge, over the PS (the PS inset is 0.5 at the top).
- **Width**:
  - Recommended 2.15 mm (x 43.055..45.2).
  - Maximum 2.6 mm: the panel edge to the aperture edge is 2.645. Keep >= 0.4 mm behind the aperture edge so the flex
    is not visible.
- **LED row**:
  - Emitting faces at x ~45.0 (enclosure X ~0.76). That is 0.70 mm behind the aperture edge (x 45.70) and 1.40 mm
    outside the active edge (x 46.405).
  - A 1.4 mm deep XL-4008 then spans x 43.6..45.0. Its rear 0..0.45 mm overhangs the PS edge, which sits at 0.8 +/-0.2
    from the glass edge (x 43.66..44.06).
  - => Add a 0.1-0.15 mm PI stiffener on the B side under the whole LED bar (not in the bends). The bar then rests flat
    on the PS and cantilevers over the 0.43 mm glass step.
  - If the stiffener is omitted, move the faces to x 45.2. The LEDs then sit fully on the PS, but are only 0.5 mm
    behind the aperture edge (see glare, section 6).
  - LED centers go along y within the active span 40.35..133.15. The first and last LED centers should be ~2-4 mm inside
    the active corners. The count and pitch come from the electrical/optics notes (for example 12 LEDs, 6W + 6C
    alternating, gives ~7.9 mm pitch).
  - Traces can run under each LED between its two end pads, or in the outer ~0.5 mm over the step.
- **Heights (P03 enclosure with the plain panel at rear plane Z 4.0)**:

  | Layer | Thickness (mm) | Top of layer, Z |
  |---|---|---|
  | Panel front (PS) | - | 4.926 |
  | Tape | 0.05 | 4.976 |
  | Flex | 0.11 | 5.086 |
  | PI stiffener + adhesive | ~0.15 | ~5.24 |
  | LED | 0.8 | **~6.04** |

  - The bezel underside is at Z 6.5 [BUILD], so there is 0.46 mm clearance.
  - The LED window center is ~0.5-0.6 mm above the panel surface.
  - The XL-2810 fallback (1.2 mm tall) leaves 0.06 mm with the stiffener, or 0.21 without it.
- **DIY attachment**:
  - Peel the 0.065 protective film and pull tape first. The pull-tape tab is at the bottom-left corner, right where
    the jog lies.
  - Laminate thin double-sided acrylic tape (for example 3M 467MP / 200MP adhesive-transfer tape 0.05 mm, or tesa 4972
    0.048 mm PET) on the flex back under the bar and the jog, back to the PS step (y 138.9). Cut it clear of the
    fold zone.
  - Put a 1-2 mm dot of the same tape, or Kapton, on the neck where it lies on the bare glass ledge.
  - No adhesive through the U-wrap or the bends.
  - Kapton tape (1 mil) over the neck where it passes the slot's routed FR4 edges, and over the SW9 pad-4 lead tip on
    the board front (x 52.24, y 143.95).
  - Tape the tail to the board back ~3 mm before the J3 mouth as strain relief. Hirose asks for no load on the FPC.
  - Align using the bezel: the LED faces must not be visible through the aperture from straight on.

---

## 5. Enclosure impact

1. **Keep P03's 1.98 mm panel-stack parameters. Do not regenerate the enclosure for the 0.926 mm panel.**
   - With the plain panel on the unchanged Z 4.0 rear plane, the bezel underside at Z 6.5 leaves **1.574 mm** of
     headroom (1.509 with the protective film on).
   - That covers LED 0.8 + flex 0.11 + tape 0.05 + stiffener 0.15 + ~0.46 clearance. **No bezel recess is needed.**
   - If the enclosure were regenerated for 0.926, the bezel underside would drop to about Z 5.45 (4.926 + 0.52 gasket).
     The bar would then need a recess >= 1.0-1.3 mm deep over enclosure X -1.7..1.4 (plus the bottom-left jog zone).
     The lip at the aperture is only 0.8 mm thick (Z 6.5..7.3 [BUILD]), so the bezel would have to be thickened or
     raised locally on that side.
2. **Upper gasket**:
   - The P03 0.8 mm upper foam no longer reaches the thinner panel. Use ~1.8-2.0 mm free-thickness silicone foam on
     the top, right and bottom borders (or shim the existing pads with ~1.0 mm).
   - On the left border, remove the gasket pads. Replace them with a 0.8 mm black foam strip on the LED tops, which
     compresses to ~0.46. It also acts as a light visor (see glare in section 6) and holds the bar down.
3. The bottom FPC relief (X 4.5..55.5, Y 3.8..6.4) and the open carrier shelf (X 0.10..59.9, Y 3.5..9.0) already clear
   the neck (X 8.36..12.76). The PCB slot and rear service well are reused as they are. No change.
4. Leave the aperture (57.08 x 94.20) as it is. The design hides the LEDs 0.7 mm behind its edge.
5. Nothing new crosses the side walls or buttons.

---

## 6. Collisions and risks

1. **SW9 THT lead on the front** (pad 4 at (52.24, 143.95), 1.95 mm pad):
   - It is under the neck's left 0.6 mm (x 52.6..53.2).
   - The U-wrap's bottom leg (Z >= 2.84) clears the lead tip (Z ~2.3, value taken from the side-switch lead height
     Z 2.30706 in [AUDIT]; bottom-switch lead height UNVERIFIED) by ~0.5 mm.
   - Put a Kapton dot on it, or narrow the neck to start at x 53.4 and add a 0.9 mm in-plane shift on the back run.
2. **Slot edges**: routed FR4 edges at y 141.2 and 142.5. Choose the bend radii so the flex doesn't bear on them (B3's
   center is 0.745 mm from the corner). Add Kapton as an abrasion guard. Never pull on the tail.
3. **Glass edge / silicone**:
   - The flex wraps a bare 0.5 mm TFT glass edge. Don't hug it: use R_in >= 0.66, and do not crease.
   - Silicone may stand "Max 1" mm proud near the bond (UNVERIFIED). The U's outer surface at y 144.11 leaves only
     0.34 mm to the relief wall at y 144.45.
4. **EPD FPC proximity**: the neck's right edge (x 57.0) is 1.5 +/-0.3 mm from the EPD FPC (x 58.5), and both go
   through the same slot. The EPD FPC's bond and bending area must not be pressed or tensioned [AUDIT; Good Display
   handling guide].
5. **PS edge step**: the flat PS starts 0.8 +/-0.2 mm in from the long edge. Unless stiffened, the LEDs' rear pads
   sitting over the step would bend the flex. Either stiffen the bar, or set the faces at x 45.2 and accept less
   recess.
6. **Glare / seeing the LEDs**:
   - Light leaves through the gap under the bezel lip. A viewer from the right can see an LED face once the view angle
     exceeds about atan(recess / (visor height above the window)).
   - Recess 0.7 mm with the foam visor on the LED tops -> hidden to ~60 deg.
   - Recess 0.25 mm -> ~30 deg.
7. **ESP32-S3 antenna**:
   - The bar runs over the WROOM-1 antenna notch (board edge notch x 44.24..50.6, y 93.3..112) at ~5-8 mm Z separation.
   - Thin copper traces there may detune the antenna slightly (UNVERIFIED; the panel is already over it). Use no copper
     fills in that zone, keep traces narrow, and compare RSSI with and without the flex.
8. **Top-contact retention** is 3.0 N, not 6.0. Keep slack, strain-relieve the tail, and latch the actuator fully.
   Mating durability is 20 cycles [H25].
9. **Panel retention**: the 0.926 panel in the 1.98 enclosure rattles unless the gaskets are thickened (section 5.2).
10. **Illumination gradient**:
    - This is a grazing source 0.5 mm above the surface. The near-edge vs far-edge illuminance ratio is roughly
      (d_near/d_far)^2, which is steep over 55.68 mm.
    - The optional mirrored right-edge bar, joined across the bottom border at y 134.3..137.3, halves the throw.
      It stays within the same OVP-limited LED count; see the electrical notes.
11. **Pin map cross-check** (for the owner; our flex maps by J3 pad net so it is unaffected):
    - The same x-preserving fold that matches the EPD tail to J2 would put FT01C FL tail pin 1 (drawn at the left in
      the front view) on J3 pin 1.
    - The owner-confirmed map (J3 1 = C+, 6 = W-) implies the mirror: panel 6 C+ -> J3 1.
    - UNVERIFIED which is right for a real FT01C panel. Worth a continuity check before fitting a stock frontlight
      panel.
12. **UNVERIFIED items**:
    - That GDEY0426T82's drawing is identical to GDEQ0426T82's.
    - The pull-tape position.
    - The FH34SRJ insertion stop (~2.9 mm).
    - J3's FPC-opening height.
    - Whether the PS overhang zone is flat.
    - Bottom-switch lead protrusion.
    - Rear-well depth and position under J3.
