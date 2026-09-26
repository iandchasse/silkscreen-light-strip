"""Generate the silkscreen-light-strip KiCad 9 project from tools/params.py.

Run with KiCad's bundled Python (it needs pcbnew):

    "C:\\Program Files\\KiCad\\9.0\\bin\\python.exe" tools\\generate.py

It writes, in order:
  lib/silkscreen-light-strip.pretty     footprints (LED, contact fingers, SOT-323, test pad)
  lib/silkscreen-light-strip.3dshapes   VRML model of the side-view LED
  lib/silkscreen-light-strip.kicad_sym  symbols (copied from KiCad's stock libraries and renamed)
  silkscreen-light-strip.kicad_sch      schematic
  silkscreen-light-strip.kicad_pro, fp-lib-table, sym-lib-table, .kicad_dru
  silkscreen-light-strip.kicad_pcb      flex layout, routed

The board is built from the schematic's own netlist (kicad-cli), so the two
always agree.  Refuses to run while KiCad has the project open.
"""
from __future__ import annotations

import glob
import json
import math
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import params as P  # noqa: E402
from kigeom import (uid, q, f, rounded_path, prims_to_polygon, rotate,  # noqa: E402
                    dist, add, sub, mul, norm)

ROOT = os.path.dirname(HERE)
NAME = P.PROJECT
LIBNAME = NAME
LIBDIR = os.path.join(ROOT, "lib")
PRETTY = os.path.join(LIBDIR, NAME + ".pretty")
SHAPES = os.path.join(LIBDIR, NAME + ".3dshapes")
SYMLIB = os.path.join(LIBDIR, NAME + ".kicad_sym")
SCH = os.path.join(ROOT, NAME + ".kicad_sch")
PCB = os.path.join(ROOT, NAME + ".kicad_pcb")
PRO = os.path.join(ROOT, NAME + ".kicad_pro")
KICAD = os.environ.get("KICAD9_DIR", r"C:\Program Files\KiCad\9.0")   # set KICAD9_DIR elsewhere
KICAD_CLI = os.path.join(KICAD, "bin", "kicad-cli.exe")
STOCK_SYM = os.path.join(KICAD, "share", "kicad", "symbols")
STOCK_FP = os.path.join(KICAD, "share", "kicad", "footprints")
TEMPLATE_PRO = os.path.join(HERE, "template.kicad_pro")   # KiCad 9 project settings; rules are overwritten below


def refuse_if_open():
    locks = glob.glob(os.path.join(ROOT, "~*.lck")) + glob.glob(os.path.join(ROOT, "*.lck"))
    if locks:
        sys.exit(f"KiCad has this project open ({', '.join(os.path.basename(x) for x in locks)}). "
                 "Close it first, or your next save would overwrite the generated files.")


# =====================================================================================
# derived geometry
# =====================================================================================
L = P.LED
XP = P.BAR["face_x"] - L["face_ahead"]          # LED pad centreline x (44.20)
P.LANES["b_wcol"] = XP
N_LED = 2 * L["per_string"]
# Warm and cool LEDs sit in tight pairs (as on commercial tunable-white strips) so both colours
# light the same patch of screen.  Pairs are spread evenly over the active height; inside a pair
# the warm LED is the lower one and the pads are L["pair_gap"] apart (room for one via).
N_PAIR = L["per_string"]
PAIR_SPAN = 2 * (L["pad_c"] + L["pad_len"] / 2) + L["pair_gap"]      # LED centre to LED centre in a pair
# bottom N-1 pairs at PAIRS["pitch"], the top pair HINGE["pitch"] above them (params.PAIRS / HINGE)
PAIR_Y = [P.PAIRS["bottom_centre"] - P.PAIRS["pitch"] * (N_PAIR - 1 - p) for p in range(1, N_PAIR)]
PAIR_Y = [PAIR_Y[0] - P.HINGE["pitch"]] + PAIR_Y                    # top to bottom
PAIR_PITCH = P.PAIRS["pitch"]
HINGE_Y = (PAIR_Y[0] + P.HINGE["keep_top"], PAIR_Y[1] - P.HINGE["keep_bottom"])   # bare-flex hinge, top..bottom

# Current flows DOWN the bar (anode at the top of each LED), so each string starts at the top pair.
# refs follow the current: warm D1 (top) .. D6 (bottom), cool D7 (top) .. D12 (bottom); diodes after them.
LEDS = []                                         # dicts: ref, colour, y, index along its string; top first
for idx in range(N_PAIR):                         # idx 0 = top pair
    yc = PAIR_Y[idx]
    LEDS.append({"ref": f"D{idx + 1 + L['per_string']}", "colour": "cool", "y": yc - PAIR_SPAN / 2, "idx": idx})
    LEDS.append({"ref": f"D{idx + 1}", "colour": "warm", "y": yc + PAIR_SPAN / 2, "idx": idx})
WARM = [d for d in LEDS if d["colour"] == "warm"]   # chain order: top first
COOL = [d for d in LEDS if d["colour"] == "cool"]
DW_REF = f"D{N_LED + 1}"                            # warm string's BAV70W
DC_REF = f"D{N_LED + 2}"                            # cool string's BAV70W


def k_pad(led):   # cathode pad centre: with the light toward +x the cathode is at +y (bottom)
    return (XP, led["y"] + L["pad_c"])


def a_pad(led):   # anode pad centre (top)
    return (XP, led["y"] - L["pad_c"])


PAD_HALF_Y = L["pad_len"] / 2.0          # 0.8 along y
PAD_HALF_X = L["pad_depth"] / 2.0        # 0.55 along x

TIP_Y = P.PANEL["bottom"] + P.TAIL["length"]
TAB_L = P.J3["center_x"] - P.TAIL["tab_w"] / 2.0
TAB_R = P.J3["center_x"] + P.TAIL["tab_w"] / 2.0


def finger_x(n):
    return P.J3["pin1_x"] + (n - 1) * P.J3["pitch"]


# net names (schematic local labels; the netlist decides the final names)
LINK_W = [f"W{a}_{a + 1}" for a in range(1, L["per_string"])]
LINK_C = [f"C{a}_{a + 1}" for a in range(L["per_string"] + 1, 2 * L["per_string"])]


# =====================================================================================
# footprints
# =====================================================================================
FP_LED = "LED_SideView_XINGLIGHT_XL-4008"
FP_TAIL = "FPC_Tail_FH34SRJ_6P_P0.50mm_TopContact"
FP_SOT = "SOT-323_SC-70"
FP_TP = "TestPad_0.8mm_Wire"


def fp_header(name, descr, tags, attr):
    return [f'(footprint {q(name)}', '\t(version 20241229)', '\t(generator "silkscreen-light-strip")',
            '\t(generator_version "9.0")', '\t(layer "F.Cu")', f'\t(descr {q(descr)})', f'\t(tags {q(tags)})',
            f'\t(property "Reference" "REF**" (at 0 -2 0) (layer "F.SilkS") (uuid {q(uid(name, "ref"))}) '
            '(effects (font (size 1 1) (thickness 0.15))))',
            f'\t(property "Value" {q(name)} (at 0 2 0) (layer "F.Fab") (uuid {q(uid(name, "val"))}) '
            '(effects (font (size 0.5 0.5) (thickness 0.08))))',
            f'\t(property "Datasheet" "" (at 0 0 0) (layer "F.Fab") (hide yes) (uuid {q(uid(name, "ds"))}) '
            '(effects (font (size 1 1) (thickness 0.15))))',
            f'\t(property "Description" {q(descr)} (at 0 0 0) (layer "F.Fab") (hide yes) (uuid {q(uid(name, "de"))}) '
            '(effects (font (size 1 1) (thickness 0.15))))',
            f'\t(attr {attr})']


def g_line(a, b, layer, w, name, i):
    return (f'\t(fp_line (start {f(a[0])} {f(a[1])}) (end {f(b[0])} {f(b[1])}) '
            f'(stroke (width {f(w)}) (type solid)) (layer {q(layer)}) (uuid {q(uid(name, layer, i))}))')


def g_rect(a, b, layer, w, name, i, fill=False):
    return (f'\t(fp_rect (start {f(a[0])} {f(a[1])}) (end {f(b[0])} {f(b[1])}) '
            f'(stroke (width {f(w)}) (type solid)) (fill {"yes" if fill else "no"}) (layer {q(layer)}) '
            f'(uuid {q(uid(name, layer, "r", i))}))')


def g_text(txt, at, layer, h, name, i, w=None):
    w = w if w is not None else h * 0.15
    return (f'\t(fp_text user {q(txt)} (at {f(at[0])} {f(at[1])} 0) (layer {q(layer)}) '
            f'(uuid {q(uid(name, "t", i))}) (effects (font (size {f(h)} {f(h)}) (thickness {f(w)}))))')


def write_led_fp():
    """XINGLIGHT XL-4008 ("335") side-view LED, drawn with the light going toward -y at 0 deg.

    Top view, lens up: anode (pin 2) on the LEFT, cathode (pin 1) on the RIGHT.  Evidence, all
    independent of each other:
      * datasheet p.7 outline, third view read as a TOP view: lens band up, (2) left, (1) with the
        notch mark right;
      * datasheet p.8 reel note: the sprocket-hole side of the tape is the component's negative, and the
        tape cross-section shows the part's REAR (ejector-pin circle), so the lens faces away from it;
      * both LCSC/EasyEDA library footprints (C5440667, C2843774): '-' on the right with the lens at -y.
    Placed at 270 deg on the strip the light goes +x, the anode is at -y (top) and the cathode at +y.
    Diode-test one loose part before soldering a whole strip (docs/ASSEMBLY.md).

    Land pattern: datasheet 1.6 x 1.1 mm pads at +/-1.85 mm, with 0.1 mm trimmed off the rear so the
    coverlay opening keeps 0.15 mm from the lane behind the pads.
    """
    n = FP_LED
    hl, fa, rb = L["body_len"] / 2, L["face_ahead"], L["rear_behind"]
    trim = 1.1 - L["pad_depth"]
    pad_y = -trim / 2                         # pad keeps its front edge, loses the rear 'trim'
    out = fp_header(n, "XINGLIGHT XL-4008UWC/WWC side-view LED, 4.0x1.4x0.8 mm, light toward -y at 0 deg, "
                    "anode left / cathode right; datasheet p.7 land pattern (1.6x1.1 at +/-1.85), rear 0.1 trimmed",
                    "LED side view 335 4008 right angle", "smd")
    for num, x in (("1", L["pad_c"]), ("2", -L["pad_c"])):          # 1 = K right, 2 = A left
        out.append(f'\t(pad {q(num)} smd roundrect (at {f(x)} {f(pad_y)}) (size {f(L["pad_len"])} {f(L["pad_depth"])}) '
                   f'(layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.15) (uuid {q(uid(n, "pad", num))}))')
    # body, window and light arrow on F.Fab
    out.append(g_rect((-hl, -fa), (hl, rb), "F.Fab", 0.05, n, 0))
    out.append(g_line((-L["window"] / 2, -fa), (L["window"] / 2, -fa), "F.Fab", 0.2, n, 1))
    out.append(g_line((0, -fa - 0.1), (0, -fa - 0.6), "F.Fab", 0.08, n, 2))
    out.append(g_line((0, -fa - 0.6), (-0.2, -fa - 0.35), "F.Fab", 0.08, n, 3))
    out.append(g_line((0, -fa - 0.6), (0.2, -fa - 0.35), "F.Fab", 0.08, n, 4))
    out.append(g_text("K", (L["pad_c"], pad_y), "F.Fab", 0.5, n, 5))
    out.append(g_text("A", (-L["pad_c"], pad_y), "F.Fab", 0.5, n, 6))
    out.append(g_text("${REFERENCE}", (0, -0.2), "F.Fab", 0.4, n, 7))
    # silkscreen cathode bar behind the cathode pad (clear of the coverlay opening and the light path)
    ys = pad_y + L["pad_depth"] / 2 + 0.1 + 0.15 + 0.075
    out.append(g_line((L["pad_c"] - 0.5, ys), (L["pad_c"] + 0.5, ys), "F.SilkS", 0.15, n, 9))
    # courtyard: body + pads; the light path in front is kept clear by the strip outline itself
    cx = L["pad_c"] + L["pad_len"] / 2 + 0.15
    out.append(g_rect((-cx, -fa - 0.15), (cx, max(rb, pad_y + L["pad_depth"] / 2) + 0.15), "F.CrtYd", 0.05, n, 8))
    out.append(f'\t(model "${{KIPRJMOD}}/lib/{NAME}.3dshapes/{n}.wrl" (offset (xyz 0 0 0)) (scale (xyz 1 1 1)) '
               '(rotate (xyz 0 0 0)))')
    out.append(')')
    return n, "\n".join(out) + "\n"


def write_tail_fp():
    """Six gold fingers for a Hirose FH34SRJ-6S (J3), top-contact side = F.Cu.

    Origin = centre of the tip edge, tail running toward -y.  Pin 1 at x = -1.25.  The coverlay is
    opened across the whole tab for the exposed length (a gang opening; 0.5 mm pitch leaves no
    coverlay bridge anyway).  The PI stiffener is drawn on the board, not here.
    """
    n = FP_TAIL
    T = P.TAIL
    out = fp_header(n, "Flex tail for Hirose FH34SRJ-6S-0.5SH(50): 6 fingers 0.3 mm at 0.5 mm, 3.5 mm tab, "
                    "0.3 mm total at the contacts (0.11 flex + 0.225 PI stiffener), contacts on F.Cu (top contact)",
                    "FPC FFC tail gold finger FH34SRJ", "smd exclude_from_pos_files exclude_from_bom allow_soldermask_bridges")
    y0 = -T["finger_setback"]
    y1 = y0 - T["finger_len"]
    for k in range(1, 7):
        x = (k - 3.5) * P.J3["pitch"]
        out.append(f'\t(pad {q(str(k))} smd roundrect (at {f(x)} {f((y0 + y1) / 2)}) '
                   f'(size {f(T["finger_w"])} {f(T["finger_len"])}) (layers "F.Cu") (roundrect_rratio 0.1) '
                   f'(uuid {q(uid(n, "pad", k))}))')
    # coverlay opening: from 0.1 beyond the tip to the exposed length, full tab width + 0.1
    hw = T["tab_w"] / 2 + 0.1
    out.append(g_rect((-hw, 0.1), (hw, -T["exposed_len"]), "F.Mask", 0, n, 0, fill=True))
    # fab: tab outline and a note
    out.append(g_rect((-T["tab_w"] / 2, 0), (T["tab_w"] / 2, -T["tab_len"]), "F.Fab", 0.05, n, 1))
    out.append(g_line((-T["tab_w"] / 2, -T["stiffener_len"]), (T["tab_w"] / 2, -T["stiffener_len"]), "F.Fab", 0.05, n, 2))
    out.append(g_text("1", (-1.25, -2.6), "F.Fab", 0.4, n, 3))
    out.append(g_text("6", (1.25, -2.6), "F.Fab", 0.4, n, 4))
    out.append(g_text("to J3", (0, -4.2), "F.Fab", 0.5, n, 5))
    out.append(g_rect((-T["tab_w"] / 2 - 0.25, 0.25), (T["tab_w"] / 2 + 0.25, -T["tab_len"]), "F.CrtYd", 0.05, n, 6))
    out.append(')')
    return n, "\n".join(out) + "\n"


def write_sot_fp():
    """Copy KiCad's stock SOT-323_SC-70 so the project is self-contained."""
    src = open(os.path.join(STOCK_FP, "Package_TO_SOT_SMD.pretty", "SOT-323_SC-70.kicad_mod"), encoding="utf-8").read()
    # drop the long body outlines on F.SilkS (they collide with the foot edge); keep the pin-1 marker
    out, i = [], 0
    while True:
        cands = [x for x in (src.find("\n\t(fp_line", i), src.find("\n\t(fp_poly", i)) if x >= 0]
        j = min(cands) if cands else -1
        if j < 0:
            out.append(src[i:])
            break
        out.append(src[i:j])
        depth, k = 0, j + 2          # start at the "(" after "\n\t"
        while True:
            c = src[k]
            depth += (c == "(") - (c == ")")
            k += 1
            if depth == 0:
                break
        block = src[j:k]
        if '(layer "F.SilkS")' not in block and '(layer "F.CrtYd")' not in block:
            out.append(block)
        i = k
    src = "".join(out).replace('(descr "SOT-323, SC-70")', '(descr "SOT-323, SC-70 (KiCad stock; silkscreen body lines removed '
                                                          'and a tight courtyard so two can sit side by side on the tab)")')
    # tight courtyard: pads reach +/-1.35 in x, body +/-1.0 in y
    court = ('\t(fp_rect (start -1.45 -1.05) (end 1.45 1.05) (stroke (width 0.05) (type solid)) (fill no) '
             f'(layer "F.CrtYd") (uuid {q(uid(FP_SOT, "crtyd"))}))\n')
    j = src.rfind("\t(embedded_fonts")
    j = j if j >= 0 else src.rfind(")")
    src = src[:j] + court + src[j:]
    return FP_SOT, src


def write_tp_fp():
    n = FP_TP
    out = fp_header(n, "0.8 mm test/wire pad on flex (probe it, or solder a 30 AWG wire; the tab stiffener is behind it)",
                    "test point pad wire", "smd exclude_from_pos_files exclude_from_bom")
    out.append(f'\t(pad "1" smd roundrect (at 0 0) (size 0.8 0.8) (layers "F.Cu" "F.Mask") (roundrect_rratio 0.25) '
               f'(uuid {q(uid(n, "pad"))}))')
    out.append(f'\t(fp_circle (center 0 0) (end 0.55 0) (stroke (width 0.05) (type solid)) (fill no) (layer "F.Fab") '
               f'(uuid {q(uid(n, "c"))}))')
    out.append(g_rect((-0.6, -0.6), (0.6, 0.6), "F.CrtYd", 0.05, n, 0))
    out.append(')')
    return n, "\n".join(out) + "\n"


def write_led_wrl():
    """VRML 2.0 model, KiCad scale (1 unit = 0.1 in = 2.54 mm), footprint frame, light toward -y."""
    s = 1 / 2.54
    hl, fa, rb, h = L["body_len"] / 2, L["face_ahead"], L["rear_behind"], L["body_h"]

    def box(x0, y0, z0, x1, y1, z1, colour, emissive=(0, 0, 0), transp=0.0):
        # KiCad maps VRML x->x, y->-y (board y is down), z->z
        cx, cy, cz = (x0 + x1) / 2 * s, -(y0 + y1) / 2 * s, (z0 + z1) / 2 * s
        sx, sy, sz = abs(x1 - x0) * s, abs(y1 - y0) * s, abs(z1 - z0) * s
        return (f"Transform {{ translation {cx:.5f} {cy:.5f} {cz:.5f} children [ Shape {{ "
                f"appearance Appearance {{ material Material {{ diffuseColor {colour[0]} {colour[1]} {colour[2]} "
                f"emissiveColor {emissive[0]} {emissive[1]} {emissive[2]} specularColor 0.3 0.3 0.3 "
                f"shininess 0.3 transparency {transp} }} }} geometry Box {{ size {sx:.5f} {sy:.5f} {sz:.5f} }} }} ] }}\n")

    body = box(-hl + 0.55, -fa + 0.6, 0, hl - 0.55, rb, h, (0.93, 0.93, 0.9))          # white resin housing
    lens = box(-L["window"] / 2, -fa, 0.1, L["window"] / 2, -fa + 0.6, h - 0.1, (1.0, 0.85, 0.25), (0.35, 0.28, 0.05))
    shoulder_l = box(-hl + 0.55, -fa, 0, -L["window"] / 2, -fa + 0.6, h, (0.93, 0.93, 0.9))
    shoulder_r = box(L["window"] / 2, -fa, 0, hl - 0.55, -fa + 0.6, h, (0.93, 0.93, 0.9))
    t1 = box(-hl, -fa + 0.6, 0, -hl + 0.55, rb, h * 0.75, (0.78, 0.78, 0.8))            # terminals
    t2 = box(hl - 0.55, -fa + 0.6, 0, hl, rb, h * 0.75, (0.78, 0.78, 0.8))
    return "#VRML V2.0 utf8\n# XINGLIGHT XL-4008 side-view LED (silkscreen-light-strip, generated)\n" + \
        body + lens + shoulder_l + shoulder_r + t1 + t2


def write_footprints():
    os.makedirs(PRETTY, exist_ok=True)
    os.makedirs(SHAPES, exist_ok=True)
    for fn in (write_led_fp, write_tail_fp, write_sot_fp, write_tp_fp):
        name, text = fn()
        with open(os.path.join(PRETTY, name + ".kicad_mod"), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
    with open(os.path.join(SHAPES, FP_LED + ".wrl"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(write_led_wrl())
    import make_step_model   # STEP body beside the VRML, for kicad-cli --subst-models
    make_step_model.make(os.path.join(SHAPES, FP_LED + ".step"), os.path.join(ROOT, "build", "step_model"))


# =====================================================================================
# symbols
# =====================================================================================
def extract_symbol(lib_file, name):
    text = open(os.path.join(STOCK_SYM, lib_file), encoding="utf-8").read()
    m = re.search(r'^\t\(symbol "' + re.escape(name) + r'"\n', text, re.M)
    if not m:
        raise KeyError(name)
    i = m.start()
    depth = 0
    for j in range(i, len(text)):
        c = text[j]
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return text[i:j + 1]
    raise ValueError("unbalanced")


def set_prop(block, prop, value):
    return re.sub(r'(\(property "' + re.escape(prop) + r'" )"[^"]*"', lambda m: m.group(1) + q(value), block, count=1)


def rename_symbol(block, old, new):
    block = block.replace(f'(symbol "{old}"', f'(symbol "{new}"', 1)
    return re.sub(r'\(symbol "' + re.escape(old) + r'_(\d+_\d+)"', lambda m: f'(symbol "{new}_{m.group(1)}"', block)


def build_symbols():
    syms = {}
    led = rename_symbol(extract_symbol("Device.kicad_sym", "LED"), "LED", "LED_SideView")
    led = set_prop(led, "Footprint", f"{LIBNAME}:{FP_LED}")
    led = set_prop(led, "ki_fp_filters", "LED* LED_SideView*")
    led = set_prop(led, "Description", "Side-view (right-angle) white LED")
    syms["LED_SideView"] = led

    bav = rename_symbol(extract_symbol("Diode.kicad_sym", "BAV70"), "BAV70", "BAV70W")
    bav = set_prop(bav, "Value", "BAV70W")
    bav = set_prop(bav, "Footprint", f"{LIBNAME}:{FP_SOT}")
    bav = set_prop(bav, "ki_fp_filters", "SOT?323*")
    syms["BAV70W"] = bav

    con = rename_symbol(extract_symbol("Connector_Generic.kicad_sym", "Conn_01x06"), "Conn_01x06", "FPC_Tail_J3")
    con = set_prop(con, "Value", "FPC_Tail_J3")
    con = set_prop(con, "Footprint", f"{LIBNAME}:{FP_TAIL}")
    con = set_prop(con, "ki_fp_filters", "FPC_Tail*")
    con = set_prop(con, "Description", "Gold-finger tail that plugs into the Silkscreen main board's frontlight "
                   "connector J3 (Hirose FH34SRJ-6S-0.5SH(50))")
    names = {1: "LED_SW(C+)", 2: "C-", 3: "NC", 4: "NC", 5: "LED_SW(W+)", 6: "W-"}

    def fix_pin(m):
        body = m.group(0)
        num = int(re.search(r'\(number "(\d+)"', body).group(1))
        body = re.sub(r'\(name "[^"]*"', f'(name "{names[num]}"', body)
        if num in (3, 4):
            body = body.replace("(pin passive line", "(pin no_connect line", 1)
        return body
    con = re.sub(r'\(pin passive line.*?\(number "\d+".*?\n\t\t\t\)', fix_pin, con, flags=re.S)
    syms["FPC_Tail_J3"] = con

    tp = extract_symbol("Connector.kicad_sym", "TestPoint")
    tp = set_prop(tp, "Footprint", f"{LIBNAME}:{FP_TP}")
    syms["TestPoint"] = tp
    return syms


def write_symbol_lib(syms):
    with open(SYMLIB, "w", encoding="utf-8", newline="\n") as fh:
        fh.write('(kicad_symbol_lib\n\t(version 20241209)\n\t(generator "silkscreen-light-strip")\n'
                 '\t(generator_version "9.0")\n')
        for s in syms.values():
            fh.write(s + "\n")
        fh.write(")\n")


# =====================================================================================
# schematic
# =====================================================================================
ROOT_UUID = uid("root-sheet")


class Sch:
    def __init__(self, syms):
        self.syms = syms
        self.items = []
        self.symbols = []        # (ref, lib name, uuid, pins)
        self.n = 0

    def _u(self, *k):
        self.n += 1
        return uid("sch", self.n, *k)

    def wire(self, a, b):
        self.items.append(f'\t(wire (pts (xy {f(a[0])} {f(a[1])}) (xy {f(b[0])} {f(b[1])})) '
                          f'(stroke (width 0) (type default)) (uuid {q(self._u("w"))}))')

    def label(self, name, at, angle=0):
        just = "right bottom" if angle == 180 else "left bottom"
        self.items.append(f'\t(label {q(name)} (at {f(at[0])} {f(at[1])} {angle}) (fields_autoplaced yes) '
                          f'(effects (font (size 1.27 1.27)) (justify {just})) (uuid {q(self._u("l"))}))')

    def noconn(self, at):
        self.items.append(f'\t(no_connect (at {f(at[0])} {f(at[1])}) (uuid {q(self._u("nc"))}))')

    def junction(self, at):
        self.items.append(f'\t(junction (at {f(at[0])} {f(at[1])}) (diameter 0) (color 0 0 0 0) '
                          f'(uuid {q(self._u("j"))}))')

    def text(self, s, at, size=1.27):
        self.items.append(f'\t(text {q(s)} (exclude_from_sim no) (at {f(at[0])} {f(at[1])} 0) '
                          f'(effects (font (size {f(size)} {f(size)})) (justify left top)) (uuid {q(self._u("t"))}))')

    def symbol(self, lib, ref, at, rot=0, mirror=None, fields=None, in_bom=True, pins=(),
               ref_at=None, val_at=None, justify=None):
        u = uid("sym", ref)
        fields = dict(fields or {})
        # reference above, value below (y down) unless told otherwise; other fields hidden
        props = [("Reference", ref, ref_at or (at[0], at[1] - 3.81), False),
                 ("Value", fields.pop("Value"), val_at or (at[0], at[1] + 3.81), False)]
        for k, v in fields.items():
            props.append((k, v, at, True))
        lines = [f'\t(symbol (lib_id {q(LIBNAME + ":" + lib)}) (at {f(at[0])} {f(at[1])} {rot})'
                 + (f' (mirror {mirror})' if mirror else '') + ' (unit 1)',
                 f'\t\t(exclude_from_sim no) (in_bom {"yes" if in_bom else "no"}) (on_board yes) (dnp no) '
                 f'(uuid {q(u)})']
        for i, (k, v, pos, hidden) in enumerate(props):
            just = f' (justify {justify})' if (justify and not hidden) else ''
            lines.append(f'\t\t(property {q(k)} {q(v)} (at {f(pos[0])} {f(pos[1])} 0) '
                         f'(effects (font (size 1.27 1.27))' + just + (' (hide yes)' if hidden else '') + '))')
        for p in pins:
            lines.append(f'\t\t(pin {q(p)} (uuid {q(uid("pin", ref, p))}))')
        lines.append(f'\t\t(instances (project {q(NAME)} (path {q("/" + ROOT_UUID)} (reference {q(ref)}) (unit 1))))')
        lines.append('\t)')
        self.symbols.append("\n".join(lines))
        return u


    def write(self, path):
        head = [f'(kicad_sch', '\t(version 20250114)', '\t(generator "eeschema")', '\t(generator_version "9.0")',
                f'\t(uuid {q(ROOT_UUID)})', '\t(paper "A4")',
                '\t(title_block', f'\t\t(title "Silkscreen light strip")', f'\t\t(date {q(P.DATE)})',
                f'\t\t(rev {q(P.REVISION)})', f'\t\t(company {q(P.COMPANY)})',
                '\t\t(comment 1 "Warm/cool side-view LED strip on flex for the Silkscreen reader frontlight connector J3")',
                '\t\t(comment 2 "Licensed under CERN-OHL-S-2.0")', '\t\t(comment 3 "(c) 2026 idc LLC")',
                '\t\t(comment 4 "Companion to github.com/iandchasse/silkscreen-pcb")', '\t)', '\t(lib_symbols']
        for name, s in self.syms.items():
            s = s.replace(f'(symbol "{name}"', f'(symbol "{LIBNAME}:{name}"', 1)
            head.append("\t" + s.replace("\n", "\n\t"))
        head.append('\t)')
        body = head + self.items + self.symbols + [
            f'\t(sheet_instances (path "/" (page "1")))', '\t(embedded_fonts no)', ')']
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("\n".join(body) + "\n")


def build_schematic(syms):
    s = Sch(syms)
    G = 2.54
    # ---------------- J1: the tail (mirrored so its pins face right; pin names hidden, labels say it) ----
    jx, jy = 30.48, 99.06
    s.symbol("FPC_Tail_J3", "J1", (jx, jy), 0, mirror="y", in_bom=False,
             fields={"Value": "FPC tail to J3", "Footprint": f"{LIBNAME}:{FP_TAIL}",
                     "Datasheet": "https://www.hirose.com/en/product/series/FH34SRJ",
                     "Description": "Contact fingers, not a part: plugs into FH34SRJ-6S-0.5SH(50) J3 on the main board"},
             pins=[str(k) for k in range(1, 7)], ref_at=(jx, jy - 8.89), val_at=(jx, jy + 11.43))
    pin = lambda k: (jx + 5.08, jy - 5.08 + (k - 1) * G)
    for k, name in ((1, "LED_SW"), (2, "C-"), (5, "LED_SW"), (6, "W-")):
        a = pin(k)
        b = (a[0] + 10.16, a[1])
        s.wire(a, b)
        s.label(name, b)
    s.noconn(pin(3))
    s.noconn(pin(4))

    # ---------------- test pads (wire / probe pads on the tab) ----------------
    for i, (name, x) in enumerate((("LED_SW", 30.48), ("C-", 45.72), ("W-", 60.96))):
        ref = f"TP{i + 1}"
        at = (x, 139.7)
        s.symbol("TestPoint", ref, at, 0, in_bom=False,
                 fields={"Value": name, "Footprint": f"{LIBNAME}:{FP_TP}", "Datasheet": "~",
                         "Description": "Wire/probe pad on the stiffened tab behind the main board"}, pins=["1"],
                 ref_at=(x + 1.27, at[1] - 5.08), val_at=(x + 1.27, at[1] - 2.54), justify="left")
        s.wire(at, (x, at[1] + 7.62))
        s.label(name, (x, at[1] + 7.62))

    # ---------------- strings: current flows D1 -> D5 and D6 -> D10 ----------------
    def string_row(colour, diode_ref, anode_net, ret_net, links, leds, y_row, y_diode):
        # protection diode: pin1 A1 (left) = LED_SW, pin2 A2 (right) = return, pin3 K (below) = string anode
        dx = 83.82
        s.symbol("BAV70W", diode_ref, (dx, y_diode), 0,
                 fields={"Value": P.DIODE["value"], "Footprint": f"{LIBNAME}:{FP_SOT}",
                         "Datasheet": P.DIODE["datasheet"],
                         "Description": f"{colour.capitalize()} string: series block + reverse clamp (flip protection)",
                         "MPN": P.DIODE["mpn"], "Manufacturer": P.DIODE["manufacturer"], "LCSC": P.DIODE["lcsc"],
                         "FT Rotation Offset": f'{P.DIODE["jlc_rot"]:g}'},
                 pins=["1", "2", "3"], ref_at=(dx + 2.54, y_diode - 5.08), val_at=(dx + 2.54, y_diode - 2.54),
                 justify="left")
        p1, p2, p3 = (dx - 7.62, y_diode), (dx + 7.62, y_diode), (dx, y_diode + 5.08)
        s.wire(p1, (p1[0] - 5.08, p1[1]))
        s.label("LED_SW", (p1[0] - 5.08, p1[1]), 180)
        s.wire(p2, (p2[0] + 5.08, p2[1]))
        s.label(ret_net, (p2[0] + 5.08, p2[1]))
        x0 = 109.22
        s.wire(p3, (dx, y_row))
        s.wire((dx, y_row), (x0 - 3.81, y_row))
        s.label(anode_net, (dx + 2.54, y_row))
        spec = P.LED[colour]
        for i, led in enumerate(leds):
            x = x0 + i * 17.78
            s.symbol("LED_SideView", led["ref"], (x, y_row), 180,
                     fields={"Value": spec["mpn"], "Footprint": f"{LIBNAME}:{FP_LED}", "Datasheet": spec["datasheet"],
                             "Description": f"{colour.capitalize()} white {spec['cct']} side-view LED, 4.0x1.4x0.8 mm",
                             "MPN": spec["mpn"], "Manufacturer": P.LED["manufacturer"], "LCSC": spec["lcsc"],
                             "FT Rotation Offset": f'{P.LED["jlc_rot"]:g}'},
                     pins=["1", "2"], ref_at=(x, y_row - 5.08), val_at=(x, y_row + 5.08))
            kx = x + 3.81
            if i < len(leds) - 1:
                ax = x + 17.78 - 3.81
                s.wire((kx, y_row), (ax, y_row))
                s.label(links[i], (kx + 1.27, y_row))
            else:
                s.wire((kx, y_row), (kx + 7.62, y_row))
                s.label(ret_net, (kx + 7.62, y_row))

    string_row("warm", DW_REF, "W_A", "W-", LINK_W, WARM, 55.88, 40.64)
    string_row("cool", DC_REF, "C_A", "C-", LINK_C, COOL, 101.6, 86.36)

    # ---------------- notes ----------------
    notes = [
        "HOW IT CONNECTS",
        "J1 is not a part: it is the flex's own gold-finger tail. It plugs into the main board's frontlight connector",
        "J3 (Hirose FH34SRJ-6S-0.5SH(50)) in place of a panel's bonded frontlight. J3 map (owner-confirmed):",
        "1 C+ = LED_SW, 2 C-, 3 NC, 4 NC, 5 W+ = LED_SW, 6 W-. Pins 1 and 5 are tied here as well (redundant contact).",
        "",
        "DRIVER LIMITS (main board U10 TPS923610, R37 = 15 ohm)",
        "Constant current 13.3 mA nominal, 13.9 mA max, one string at a time (Q5 warm / Q6 cool). OVP 24.25 V min;",
        "design ceiling 22 V at -10 C. 6 LEDs per string: about 17.4 V typ (15.0-20.4 V over bins and -10..60 C) + 0.65-0.95 V diode;",
        "LED_SW about 18.4 V typ, 21.7 V worst case. Firmware: 'open' is LED_MONIT >= 2.49 V (peak in the first second).",
        "",
        f"{DW_REF}/{DC_REF} BAV70W: A1 is the series block, A2 clamps the string if the tail is inserted face-down",
        "(J3 contacts both faces; a flipped tail mirrors pins 1<->6, 2<->5). Flipped: no current, OVP latches.",
        "",
        "LEDs: XINGLIGHT XL-4008WWC (3000 K) / XL-4008UWC (6000-6500 K). Warm/cool pairs, top to bottom:",
        " ".join(f"(D{i + 1 + N_PAIR}/D{i + 1})" for i in range(N_PAIR)) + "; the anode is the top pad of every LED.",
        "On the 3.68in panel the top pair (D7/D1) folds back under the bar on the hinge; it stays in the strings.",
    ]
    s.text("\n".join(notes), (101.6, 124.46), 1.27)
    s.write(SCH)
    return s


# =====================================================================================
# project files
# =====================================================================================
def write_project_files():
    with open(os.path.join(ROOT, "fp-lib-table"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(f'(fp_lib_table\n\t(version 7)\n\t(lib (name {q(LIBNAME)})(type "KiCad")'
                 f'(uri "${{KIPRJMOD}}/lib/{NAME}.pretty")(options "")(descr "Silkscreen light strip footprints"))\n)\n')
    with open(os.path.join(ROOT, "sym-lib-table"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(f'(sym_lib_table\n\t(version 7)\n\t(lib (name {q(LIBNAME)})(type "KiCad")'
                 f'(uri "${{KIPRJMOD}}/lib/{NAME}.kicad_sym")(options "")(descr "Silkscreen light strip symbols"))\n)\n')

    pro = json.load(open(TEMPLATE_PRO, encoding="utf-8"))
    ds = pro["board"]["design_settings"]
    ds["drc_exclusions"] = []
    R = P.RULES
    ds["rules"].update({
        "min_clearance": R["clearance"], "min_copper_edge_clearance": R["edge_clearance"],
        "min_track_width": R["track_min"], "min_via_diameter": R["via_pad"],
        "min_through_hole_diameter": R["via_drill"], "min_via_annular_width": 0.12,
        "min_hole_clearance": 0.25, "min_hole_to_hole": 0.25, "min_text_height": R["silk_text_h"],
        "min_text_thickness": R["silk_line_w"], "min_silk_clearance": 0.15,
        "solder_mask_to_copper_clearance": 0.0,
    })
    ds["track_widths"] = [0.0, 0.2, 0.3, 0.45]
    ds["via_dimensions"] = [{"diameter": 0.0, "drill": 0.0}, {"diameter": R["via_pad"], "drill": R["via_drill"]}]
    ds["defaults"]["board_outline_line_width"] = 0.05
    ds["defaults"]["silk_line_width"] = R["silk_line_w"]
    ds["defaults"]["silk_text_size_h"] = R["silk_text_h"]
    ds["defaults"]["silk_text_size_v"] = R["silk_text_h"]
    ds["defaults"]["silk_text_thickness"] = R["silk_line_w"]
    sev = ds.setdefault("rule_severities", {})
    sev.update({"silk_edge_clearance": "warning", "silk_over_copper": "warning", "lib_footprint_mismatch": "warning",
                "courtyards_overlap": "error", "text_height": "warning", "text_thickness": "warning",
                "copper_edge_clearance": "error", "track_dangling": "warning", "solder_mask_bridge": "error",
                "missing_courtyard": "error", "footprint_type_mismatch": "warning",
                "footprint_filters_mismatch": "warning"})
    pro.setdefault("erc", {})["erc_exclusions"] = []          # the template came from the main board
    ns = pro["net_settings"]
    base = ns["classes"][0]
    base.update({"clearance": R["clearance"], "track_width": 0.2, "via_diameter": R["via_pad"], "via_drill": R["via_drill"]})
    ns["classes"] = [base]
    ns["netclass_assignments"] = None
    ns["netclass_patterns"] = []
    pro["meta"]["filename"] = NAME + ".kicad_pro"
    pro["sheets"] = [[ROOT_UUID, "Root"]]
    pro["text_variables"] = {}
    pro["boards"] = []
    pro["libraries"] = {"pinned_footprint_libs": [], "pinned_symbol_libs": []}
    pro.get("pcbnew", {}).get("last_paths", {}).clear() if isinstance(pro.get("pcbnew", {}).get("last_paths"), dict) else None
    pro["pcbnew"] = {"last_paths": {"gencad": "", "idf": "", "netlist": "", "plot": "production/gerbers/",
                                    "pos_files": "production/", "specctra_dsn": "", "step": "docs/", "svg": "",
                                    "vrml": ""}, "page_layout_descr_file": ""}
    with open(PRO, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(pro, fh, indent=2)

    # custom DRC rules for flex-specific constraints
    dru = """(version 1)

# Gold fingers stop 0.2 mm from the tip (JLCPCB gold-finger rule), closer than the 0.3 mm copper-to-edge
# rule that governs the rest of the flex.
(rule "gold_fingers_to_tip"
    (constraint edge_clearance (min 0.19mm))
    (condition "A.memberOfFootprint('J1') || B.memberOfFootprint('J1')"))

# The fingers sit at 0.5 mm pitch with 0.3 mm conductors (Hirose FH34SRJ recommended FPC).
(rule "finger_pitch"
    (constraint clearance (min 0.19mm))
    (condition "A.memberOfFootprint('J1') || B.memberOfFootprint('J1')"))

# Flex copper: nothing thinner than 0.15 mm anywhere.
(rule "flex_min_track"
    (constraint track_width (min 0.15mm)))
"""
    with open(os.path.join(ROOT, NAME + ".kicad_dru"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(dru)


# =====================================================================================
# netlist from the schematic (so the PCB matches it exactly)
# =====================================================================================
def schematic_netlist():
    out = os.path.join(ROOT, "build", NAME + ".net")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    r = subprocess.run([KICAD_CLI, "sch", "export", "netlist", "--format", "kicadsexpr", "-o", out, SCH],
                       capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit("netlist export failed:\n" + r.stdout + r.stderr)
    text = open(out, encoding="utf-8").read()
    padnet = {}
    for m in re.finditer(r'\(net \(code "?\d+"?\) \(name "((?:[^"\\]|\\.)*)"\)(.*?)\n\s*\)\s*(?=\(net |\)\s*\)\s*$)', text, re.S):
        pass
    # robust parse: walk net blocks
    for blk in re.split(r'\n\s*\(net ', text)[1:]:
        nm = re.search(r'\(name "((?:[^"\\]|\\.)*)"\)', blk).group(1)
        for ref, pad in re.findall(r'\(node \(ref "([^"]+)"\) \(pin "([^"]+)"\)', blk):
            padnet[(ref, pad)] = nm
    comps = {}
    for blk in re.split(r'\n\s*\(comp ', text)[1:]:
        ref = re.search(r'\(ref "([^"]+)"\)', blk).group(1)
        val = re.search(r'\(value "((?:[^"\\]|\\.)*)"\)', blk).group(1)
        fpn = re.search(r'\(footprint "([^"]+)"\)', blk)
        tstamp = re.search(r'\(tstamps "([^"]+)"\)', blk)
        fields = dict(re.findall(r'\(field \(name "([^"]+)"\) "((?:[^"\\]|\\.)*)"\)', blk))
        comps[ref] = {"value": val, "footprint": fpn.group(1) if fpn else "", "uuid": tstamp.group(1) if tstamp else "",
                      "fields": fields}
    return padnet, comps


if __name__ == "__main__":
    refuse_if_open()
    write_footprints()
    syms = build_symbols()
    write_symbol_lib(syms)
    build_schematic(syms)
    write_project_files()
    padnet, comps = schematic_netlist()
    import build_pcb   # noqa: E402  (needs pcbnew)
    build_pcb.build(padnet, comps)
    print("generated", PCB)
