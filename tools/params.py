"""Design parameters for the Silkscreen light strip.

Every coordinate is in millimetres in the MAIN BOARD's KiCad frame
(silkscreen_pcb.kicad_pcb, viewed from the screen side, x right, y down).
The part of the flex that lies on the panel is drawn exactly where it sits
on the reader.  The tail is drawn "unrolled": it keeps its x (the fold is
about an axis parallel to x) and continues in +y past the fold line.

To fit a different panel or connector position, change the PANEL / J3
blocks and re-run tools/generate.py.  The LED count per string is fixed by
the TPS923610's voltage window (see docs/DESIGN.md), not by the panel.
"""

PROJECT = "silkscreen-light-strip"
REVISION = "A"
DATE = "2026-09-24"
COMPANY = "idc LLC"

# ------------------------------------------------------------------ panels
# The strip is drawn for the plain 4.26in GDEY0426T82 (800x480): its bar lies ON that panel's left border.
# The same strip also fits the 3.68in 528x792 panel (PANEL_368), where the bar lies BESIDE the glass and
# the top pair folds back under the bar on a hinge (see HINGE and docs/DESIGN.md).
# Enclosures: enclosures/case-426 (4.26in) and enclosures/case-368 (3.68in), each with a light-strip front shell.
PANEL = {
    "left": 43.052,        # glass edge (main-board KiCad x)
    "right": 105.422,      # 62.37 wide
    "top": 37.635,
    "bottom": 142.965,     # 105.33 tall; the FPC/COG ledge is at the bottom
    "thickness": 0.926,    # plain panel; FT01C stack is 1.98
    "ps_inset_long": 0.8,  # the protective sheet stops 0.8 +/-0.2 mm in from the long edges
    "ps_bottom": 138.965,  # the flat PS ends 4.0 mm above the bottom glass edge (ledge below)
}
ACTIVE = {"left": 46.397, "right": 102.077, "top": 40.35, "bottom": 133.15}   # 55.68 x 92.8
BEZEL_MARGIN = 0.7     # the P03 aperture is the active area + 0.7 mm per side

# 3.68in 528x792 (the Xteink X3 panel, no maker part number), as placed in enclosures/case-368:
# centred on J2 in x, its bottom glass edge on the board slot's top edge.  56.24 x 86.54 x 0.87 glass;
# PS film inset 0.65 (1.78 at the bottom); active area 51.84 x 77.76 with 2.20 / 2.20 / 2.20 / 6.58 borders.
PANEL_368 = {"left": 45.367, "right": 101.607, "top": 54.66, "bottom": 141.20, "thickness": 0.87,
             "ps_bottom": 139.42}
ACTIVE_368 = {"left": 47.567, "right": 99.407, "top": 56.86, "bottom": 134.62}
WINDOW_368 = {"left": 47.067, "right": 99.907, "top": 56.36, "bottom": 135.12}   # x3 window at the lip (active + 0.5)

# ------------------------------------------------------------------ J3 (Hirose FH34SRJ-6S-0.5SH(50) on the main board's back)
J3 = {
    "center_x": 54.237,
    "pin1_x": 52.987,       # pins 1..6 at +0.5 mm steps, same x on the flex (the fold preserves x)
    "pitch": 0.5,
    # owner-confirmed map: 1 C+ (LED_SW), 2 C-, 3 NC, 4 NC, 5 W+ (LED_SW), 6 W-
    "pin_nets": {1: "LED_SW", 2: "C-", 3: None, 4: None, 5: "LED_SW", 6: "W-"},
}

# ------------------------------------------------------------------ flex build (JLCPCB)
FLEX = {
    "thickness": 0.11,          # 2-layer, 25 um adhesiveless PI core, 12 um Cu, 12.5 um PI + 15 um adhesive coverlay
    "copper": 0.012,
    "core": 0.025,
    "coverlay": 0.0275,
    "coverlay_color": "Black",       # black coverlay: invisible under the bezel, no amber reflections
    "silk_color": "White",
    "finish": "ENIG",
    "stiffener_pi": 0.225,      # one PI thickness for every stiffened area (0.11 + 0.225 at the fingers, 0.3 +/-0.03 after coverlay removal)
}

# JLCPCB flex rules we design to (docs/research/fpc-and-jlc-flex.md)
RULES = {
    "track_min": 0.15,
    "clearance": 0.15,
    "edge_clearance": 0.30,
    "via_drill": 0.30,
    "via_pad": 0.55,
    "silk_text_h": 1.0,
    "silk_line_w": 0.15,
    "mask_expansion": 0.10,
}

# ------------------------------------------------------------------ LED bar on the left border
LED = {
    "warm": {"mpn": "XL-4008WWC", "lcsc": "C5440667", "cct": "3000 K",
             "datasheet": "https://datasheet.lcsc.com/datasheet/pdf/98f3d1f702a22a454447380c669f5ab6.pdf?productCode=C5440667"},
    "cool": {"mpn": "XL-4008UWC", "lcsc": "C2843774", "cct": "6000-6500 K",
             "datasheet": "https://datasheet.lcsc.com/datasheet/pdf/e6aed946d22bf266730bba05a11330f0.pdf?productCode=C2843774"},
    "manufacturer": "XINGLIGHT",
    # JLC CPL rotation offset: the EasyEDA footprints of C5440667/C2843774 match ours at 0 deg (docs/review/dfm.md).
    # Written into each LED's "FT Rotation Offset" field, which the Fabrication Toolkit plugin reads.
    "jlc_rot": 0.0,
    "per_string": 6,       # 6 x XL-4008 + BAV70W: 21.7 V worst case (-10 C, top bin) vs the 22 V ceiling
    # XINGLIGHT 4008 ("335") side view: 4.0 long, 1.4 deep, 0.8 tall; pads 1.6 x 1.1, centres +/-1.85;
    # emitting face 1.0 mm ahead of the pad centreline, body rear 0.4 mm behind it.
    "body_len": 4.0, "body_depth": 1.4, "body_h": 0.8, "window": 1.8,
    "face_ahead": 1.0, "rear_behind": 0.4,
    "pad_len": 1.6, "pad_depth": 1.0, "pad_c": 1.85,   # datasheet depth 1.1; 0.1 trimmed off the rear (still covers the 0.8 terminal)
    "pair_gap": 1.3,      # pad-to-pad gap inside a warm/cool pair: one via, >= 0.2 mm from both coverlay openings
}

BAR = {
    "outer_x": 43.00,      # 0.05 mm outside the glass edge (43.052), within outline tolerance; the 43.40 lanes need 0.30 to the edge
    "face_x": 45.20,       # LED faces 0.5 mm behind the bezel aperture (45.70), hidden from glare
    "inner_x": 45.30,      # flex stops 0.1 mm in front of the faces, 0.4 mm inside the bezel aperture
    "top_y": 39.10,        # full-round top end, 1.5 mm above the top via; under the 4.26in top bezel
    "foot_top_y": 135.50,  # the bar turns into the foot here: 0.38 under the 3.68in window (135.12), 1.75 under the 4.26in
}
# Pair layout, shared by both panels.  The bottom five pairs are 15.55 apart (77.76 / 5, the 3.68in active
# height); the top pair sits HINGE["pitch"] above them.  On the 4.26in all six light the screen (margins 6.8
# top and bottom); on the 3.68in the bottom five do (margins 7.3 / 8.3) and the top pair folds under the bar.
PAIRS = {"pitch": 15.55, "bottom_centre": 126.35}
# Hinge between the top pair and the next: no stiffener, no tape, no vias or pads (copper on both layers
# runs straight through).  3.6 mm of bare flex takes a 180 deg teardrop fold with R_in ~0.6-0.75.
HINGE = {"pitch": 17.0,          # top pair centre to the next pair centre
         "keep_top": 7.125,      # hinge starts this far below the top pair's centre (clears its warm-link via)
         "keep_bottom": 6.25}    # and ends this far above the next pair's centre (0.3 above its anode pad)
# routing lanes in the bar (x positions)
LANES = {
    "f_lane": 43.40,       # F.Cu, behind the LED pads: cool-string links and the cool return
    "b_cminus": 43.40,     # B.Cu: cool anode feed (C_A), full length
    "b_wcol": None,        # B.Cu warm links run in the LED column (= pad centreline), set below
    "b_wminus": 44.90,     # B.Cu: warm anode feed (W_A), full length
}

# ------------------------------------------------------------------ foot, neck, tail
# The foot is a smooth hook from the bar into the neck: no components, only four concentric traces.
FOOT = {"bottom_y": 139.00,        # stiffened, on the flat protective sheet (4.26in PS ends at 138.965 +/-0.4, 3.68in at 139.42)
        "r_outer1": 3.5,           # outer radius of the bar -> foot turn (bottom-left); the four lanes turn concentrically inside it
        "r_outer2": 4.0,           # outer radius of the foot -> neck turn (top-right)
        "r_inner2": 1.6}           # inside radius where the neck leaves the foot
NECK = {"left_x": 52.487, "right_x": 58.00}     # 5.5 mm wide; the EPD FPC starts at x 58.5 at the glass edge
TAIL = {
    "length": 23.65,       # 4.26in glass edge to the contact tip: tools/foldpath.py needs 21.5-23.2 there;
                           # the 3.68in glass edge is 1.765 higher, so that build has 4-5.6 mm of spare to loop
    "tab_w": 3.50,         # Hirose: 3.5 +/-0.05 for 6 positions
    "tab_len": 5.0,        # nominal; the R3.0 taper fillet leaves 3.8 mm at exactly 3.50 (2.9 inside J3, ~0.9 outside)
    "stiffener_back": 14.0,# PI stiffener length from the tip on the back run (diodes, test pads, taper, tab);
                           # the flat run from the slot exit to the tip is ~15 mm, so the back bend stays flexible
    "stiffener_len": 5.0,  # (legacy) contact-only stiffener length; the back-run stiffener now covers it
    "exposed_len": 1.5,    # coverlay-free contact length from the tip (Hirose 1.5 +/-0.3)
    "finger_setback": 0.2, # JLC: gold fingers end 0.2 mm from the edge
    "finger_len": 1.8,
    "finger_w": 0.30,
    "tip_r": 0.2,          # Hirose R0.2 +/-0.1 on the leading corners
    "bend_zone": (140.7, 152.3),   # no vias, pads, or stiffener: the 3.68in fold is at 141.2, the 4.26in bends end by 150.5
}

# jlc_rot: EasyEDA C28064 at 0 deg == KiCad SOT-323 at 180 deg (docs/review/dfm.md), so JLC's CPL needs +180.
# make_outputs.py applies it, and it goes into the "FT Rotation Offset" field for the Fabrication Toolkit.
DIODE = {"mpn": "BAV70W,115", "manufacturer": "Nexperia", "lcsc": "C28064", "jlc_rot": 180.0,
         "datasheet": "https://assets.nexperia.com/documents/data-sheet/BAV70_SER.pdf",
         "value": "BAV70W"}
