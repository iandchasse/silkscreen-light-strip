"""Build silkscreen-light-strip.kicad_pcb with pcbnew (called from generate.py).

Geometry lives in params.py; the net of every pad comes from the schematic's
netlist, so the layout always matches the schematic.
"""
from __future__ import annotations

import math
import os

import pcbnew

import params as P
from kigeom import q, f, uid, rounded_path, prims_to_polygon, dist
import generate as G

BAR_END = 0.0     # set in build(): where the bar lanes end and the foot sweeps begin

MM = pcbnew.FromMM
V = lambda x, y: pcbnew.VECTOR2I(MM(x), MM(y))

L = P.LED
XP = G.XP
T = P.TAIL
TIP = G.TIP_Y
W_LANE_F = P.LANES["f_lane"]
W_BCM = P.LANES["b_cminus"]
W_BWM = P.LANES["b_wminus"]
OUT_X = P.BAR["outer_x"]
IN_X = P.BAR["inner_x"]
FOOT_T = P.BAR["foot_top_y"]
FOOT_B = P.FOOT["bottom_y"]
NECK_L = G.TAB_L                 # the neck's left edge is the tab's left edge (one straight line)
NECK_R = P.NECK["right_x"]
VIA_R = P.RULES["via_pad"] / 2
PAD_EDGE = L["pad_c"] + L["pad_len"] / 2        # 2.65: LED centre to the outer edge of a pad
VIA_GAP = 0.60                                   # pad edge to via centre: ring 0.325 clear, 0.225 clear of the opening

# trace widths
W_BAR = 0.20          # inside the bar (lanes behind the LED pads)
W_WIDE = 0.40         # foot, fold and back run: twice the bar width
W_FINGER = T["finger_w"]

# ---------------------------------------------------------------- foot geometry: two concentric turns
# Turn 1 (bar -> east, bottom-left): the four lanes are concentric with the outline's outer arc and
# start turning at the foot's top edge, so the inner lanes never cut the bezel-hidden inner corner.
C1 = (OUT_X + P.FOOT["r_outer1"], FOOT_B - P.FOOT["r_outer1"])          # (46.5, 134.6)
X1 = {"C-": 43.60, "W-": XP, "C_A": 44.30, "W_A": W_BWM}                # lane x entering turn 1
# Turn 2 (east -> down the neck, top-right): all four arcs share one centre, so every row/column
# pair sits on one 45-degree diagonal and the conductors keep a 0.8 mm pitch all the way round.
COL = {"C_A": 53.84, "C-": 54.64, "W_A": 55.44, "W-": 56.24}          # neck columns, west to east
ROW_WM = FOOT_T + 0.50                                                 # W- row: north-most, 0.3 mm edge gap
C2 = (51.80, ROW_WM + COL["W-"] - 51.80)                               # (51.80, 139.54)
ROW = {k: C2[1] - (x - C2[0]) for k, x in COL.items()}                 # W- 135.1, W_A 135.9, C- 136.7, C_A 137.5
RAIL_W = 0.30                                                          # copper tear-stop rails on the neck edges
RAIL_IN = 0.30                                                         # rail distance from the edge

# ---------------------------------------------------------------- back run (behind the main board)
Y_STIFF = TIP - T["stiffener_back"]                    # 154.665: start of the back-run PI stiffener
Y_DIODE = Y_STIFF + 2.40                               # SOT-323 row (rot 90: pin 3 up, pins 1/2 down)
DC_AT = (COL["C_A"], Y_DIODE)                          # cool BAV70W: pin3 <- C_A, pin1 SW = LED_SW, pin2 SE = C-
DW_AT = (COL["C_A"] + 2.50, Y_DIODE)                   # warm BAV70W (0.55 web to the cool one): pin3 <- W_A, pin1 SW = LED_SW, pin2 SE = W-
Y_TP = Y_DIODE + 2.45                                  # C- and W- test pads (0.5 web to the diodes); the LED_SW pad sits 1.5 mm lower
Y_TAPER0 = Y_TP + 2.1                                  # the 5.5 mm tail eases into the 3.5 mm tab below here
FINGER_OF = {"LED_SW_a": 1, "C-": 2, "LED_SW_b": 5, "W-": 6}


def sot_pin(at, n):
    # SOT-323 at 90 deg (pin 3 up): pad1 (-0.65,+1.0) SW, pad2 (+0.65,+1.0) SE, pad3 (0,-1.0) N
    return {1: (at[0] - 0.65, at[1] + 1.0), 2: (at[0] + 0.65, at[1] + 1.0), 3: (at[0], at[1] - 1.0)}[n]


TP_AT = {"TP1": (sot_pin(DC_AT, 1)[0], Y_TP + 1.5),   # LED_SW (staggered: 0.5 mm coverlay web to TP2)
         "TP2": (sot_pin(DC_AT, 2)[0], Y_TP),         # C-
         "TP3": (sot_pin(DW_AT, 2)[0], Y_TP)}         # W-


# =====================================================================================
def skeleton_text():
    fl = P.FLEX
    title = (f'\t(title_block\n\t\t(title "Silkscreen light strip")\n\t\t(date {q(P.DATE)})\n\t\t(rev {q(P.REVISION)})\n'
             f'\t\t(company {q(P.COMPANY)})\n'
             '\t\t(comment 1 "2-layer flex 0.11 mm, black coverlay, ENIG; PI stiffener 0.225 mm (*-Stiffener_PI0_225.gbr)")\n'
             '\t\t(comment 2 "Licensed under CERN-OHL-S-2.0")\n\t\t(comment 3 "(c) 2026 idc LLC")\n'
             '\t\t(comment 4 "Plugs into Silkscreen main board J3 (FH34SRJ-6S-0.5SH(50))")\n\t)\n')
    stack = f"""\t\t(stackup
\t\t\t(layer "F.SilkS" (type "Top Silk Screen") (color {q(fl["silk_color"])}))
\t\t\t(layer "F.Paste" (type "Top Solder Paste"))
\t\t\t(layer "F.Mask" (type "Top Solder Mask") (color {q(fl["coverlay_color"])}) (thickness {fl["coverlay"]}) (material "Polyimide coverlay") (epsilon_r 2.9) (loss_tangent 0))
\t\t\t(layer "F.Cu" (type "copper") (thickness {fl["copper"]}))
\t\t\t(layer "dielectric 1" (type "core") (thickness {fl["core"]}) (material "Polyimide") (epsilon_r 3.3) (loss_tangent 0.002))
\t\t\t(layer "B.Cu" (type "copper") (thickness {fl["copper"]}))
\t\t\t(layer "B.Mask" (type "Bottom Solder Mask") (color {q(fl["coverlay_color"])}) (thickness {fl["coverlay"]}) (material "Polyimide coverlay") (epsilon_r 2.9) (loss_tangent 0))
\t\t\t(layer "B.Paste" (type "Bottom Solder Paste"))
\t\t\t(layer "B.SilkS" (type "Bottom Silk Screen") (color {q(fl["silk_color"])}))
\t\t\t(copper_finish {q(fl["finish"])})
\t\t\t(dielectric_constraints no)
\t\t)
"""
    thick = 2 * fl["coverlay"] + 2 * fl["copper"] + fl["core"]
    return f"""(kicad_pcb
\t(version 20241229)
\t(generator "pcbnew")
\t(generator_version "9.0")
\t(general
\t\t(thickness {thick:.4f})
\t\t(legacy_teardrops no)
\t)
\t(paper "A3")
{title}\t(layers
\t\t(0 "F.Cu" signal)
\t\t(2 "B.Cu" signal)
\t\t(9 "F.Adhes" user "F.Adhesive")
\t\t(11 "B.Adhes" user "B.Adhesive")
\t\t(13 "F.Paste" user)
\t\t(15 "B.Paste" user)
\t\t(5 "F.SilkS" user "F.Silkscreen")
\t\t(7 "B.SilkS" user "B.Silkscreen")
\t\t(1 "F.Mask" user)
\t\t(3 "B.Mask" user)
\t\t(17 "Dwgs.User" user "User.Drawings")
\t\t(19 "Cmts.User" user "User.Comments")
\t\t(21 "Eco1.User" user "User.Eco1")
\t\t(23 "Eco2.User" user "User.Eco2")
\t\t(25 "Edge.Cuts" user)
\t\t(27 "Margin" user)
\t\t(31 "F.CrtYd" user "F.Courtyard")
\t\t(29 "B.CrtYd" user "B.Courtyard")
\t\t(35 "F.Fab" user)
\t\t(33 "B.Fab" user)
\t\t(39 "User.1" user "Stiffener.PI0.225")
\t\t(41 "User.2" user "Adhesive.3M9077")
\t\t(43 "User.3" user "Bend.Zones")
\t\t(45 "User.4" user "Panel.Reference")
\t)
\t(setup
{stack}\t\t(pad_to_mask_clearance {P.RULES["mask_expansion"]})
\t\t(allow_soldermask_bridges_in_footprints no)
\t\t(tenting front back)
\t\t(pcbplotparams
\t\t\t(layerselection 0x00000000_00000000_55555555_5755f5ff)
\t\t\t(plot_on_all_layers_selection 0x00000000_00000000_00000000_00000000)
\t\t\t(disableapertmacros no)
\t\t\t(usegerberextensions no)
\t\t\t(usegerberattributes yes)
\t\t\t(usegerberadvancedattributes yes)
\t\t\t(creategerberjobfile yes)
\t\t\t(dashed_line_dash_ratio 12.000000)
\t\t\t(dashed_line_gap_ratio 3.000000)
\t\t\t(svgprecision 4)
\t\t\t(plotframeref no)
\t\t\t(mode 1)
\t\t\t(useauxorigin no)
\t\t\t(hpglpennumber 1)
\t\t\t(hpglpenspeed 20)
\t\t\t(hpglpendiameter 15.000000)
\t\t\t(pdf_front_fp_property_popups yes)
\t\t\t(pdf_back_fp_property_popups yes)
\t\t\t(pdf_metadata yes)
\t\t\t(pdf_single_document no)
\t\t\t(dxfpolygonmode yes)
\t\t\t(dxfimperialunits no)
\t\t\t(dxfusepcbnewfont yes)
\t\t\t(psnegative no)
\t\t\t(psa4output no)
\t\t\t(plot_black_and_white no)
\t\t\t(sketchpadsonfab no)
\t\t\t(plotpadnumbers no)
\t\t\t(hidednponfab no)
\t\t\t(sketchdnponfab yes)
\t\t\t(crossoutdnponfab yes)
\t\t\t(subtractmaskfromsilk yes)
\t\t\t(outputformat 1)
\t\t\t(mirror no)
\t\t\t(drillshape 0)
\t\t\t(scaleselection 1)
\t\t\t(outputdirectory "production/gerbers/")
\t\t)
\t)
\t(net 0 "")
\t(embedded_fonts no)
)
"""


# =====================================================================================
class Builder:
    def __init__(self, board, padnet):
        self.b = board
        self.padnet = padnet
        self.nets = {}

    # ------------------------------------------------------------- nets
    def net(self, name):
        if name is None:
            return None
        if name not in self.nets:
            ni = pcbnew.NETINFO_ITEM(self.b, name)
            self.b.Add(ni)
            self.nets[name] = ni
        return self.nets[name]

    def netname(self, short):
        """Map a short name used in this file to the schematic's net name."""
        return {"LED_SW": "/LED_SW", "LED_SW_a": "/LED_SW", "LED_SW_b": "/LED_SW", "C-": "/C-", "W-": "/W-",
                "C_A": "/C_A", "W_A": "/W_A"}.get(short, short)

    # ------------------------------------------------------------- copper
    def route(self, net, layer, width, pts, radius=0.4):
        if isinstance(radius, (list, tuple)):
            radii = [0] + list(radius) + [0]
        else:
            radii = [0] + [radius] * (len(pts) - 2) + [0]
        prims = rounded_path(pts, radii, closed=False)
        n = self.net(self.netname(net))
        for p in prims:
            if p[0] == "line":
                t = pcbnew.PCB_TRACK(self.b)
                t.SetStart(V(*p[1]))
                t.SetEnd(V(*p[2]))
            else:
                t = pcbnew.PCB_ARC(self.b)
                t.SetStart(V(*p[1]))
                t.SetMid(V(*p[2]))
                t.SetEnd(V(*p[3]))
            t.SetWidth(MM(width))
            t.SetLayer(layer)
            t.SetNet(n)
            self.b.Add(t)

    def via(self, net, at):
        v = pcbnew.PCB_VIA(self.b)
        v.SetPosition(V(*at))
        v.SetViaType(pcbnew.VIATYPE_THROUGH)
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        v.SetDrill(MM(P.RULES["via_drill"]))
        try:
            v.SetWidth(MM(P.RULES["via_pad"]))
        except TypeError:
            v.SetWidth(pcbnew.F_Cu, MM(P.RULES["via_pad"]))
        v.SetNet(self.net(self.netname(net)))
        self.b.Add(v)

    # ------------------------------------------------------------- graphics
    def shape_prims(self, prims, layer, width):
        for p in prims:
            s = pcbnew.PCB_SHAPE(self.b)
            if p[0] == "line":
                s.SetShape(pcbnew.SHAPE_T_SEGMENT)
                s.SetStart(V(*p[1]))
                s.SetEnd(V(*p[2]))
            else:
                s.SetShape(pcbnew.SHAPE_T_ARC)
                s.SetArcGeometry(V(*p[1]), V(*p[2]), V(*p[3]))
            s.SetLayer(layer)
            s.SetWidth(MM(width))
            self.b.Add(s)

    def poly(self, pts, layer, width=0.0, filled=True, net=None):
        s = pcbnew.PCB_SHAPE(self.b)
        s.SetShape(pcbnew.SHAPE_T_POLY)
        s.SetPolyPoints([V(*p) for p in pts])
        s.SetLayer(layer)
        s.SetWidth(MM(width))
        s.SetFilled(filled)
        if net:
            s.SetNet(self.net(self.netname(net)))
        self.b.Add(s)

    def line(self, a, b, layer, width=0.1):
        self.shape_prims([("line", a, b)], layer, width)

    def rect(self, a, b, layer, width=0.1):
        pts = [a, (b[0], a[1]), b, (a[0], b[1])]
        for i in range(4):
            self.line(pts[i], pts[(i + 1) % 4], layer, width)

    def text(self, s, at, layer, h=1.0, angle=0, w=None, justify=None, mirror=False):
        t = pcbnew.PCB_TEXT(self.b)
        t.SetText(s)
        t.SetPosition(V(*at))
        t.SetLayer(layer)
        t.SetTextSize(pcbnew.VECTOR2I(MM(h), MM(h)))
        t.SetTextThickness(MM(w if w is not None else max(0.15, h * 0.15)))
        t.SetTextAngleDegrees(angle)
        if justify == "left":
            t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_LEFT)
        if mirror:
            t.SetMirrored(True)
        self.b.Add(t)

    def rule_area(self, pts, layers, no_tracks=False, no_vias=True, no_pads=True, name=""):
        z = pcbnew.ZONE(self.b)
        z.SetIsRuleArea(True)
        ls = pcbnew.LSET()
        for l in layers:
            ls.AddLayer(l)
        z.SetLayerSet(ls)
        z.SetDoNotAllowTracks(no_tracks)
        z.SetDoNotAllowVias(no_vias)
        z.SetDoNotAllowPads(no_pads)
        z.SetDoNotAllowFootprints(False)
        z.SetDoNotAllowCopperPour(True)
        z.SetZoneName(name)
        ol = z.Outline()
        ol.NewOutline()
        for p in pts:
            ol.Append(MM(p[0]), MM(p[1]))
        self.b.Add(z)

    # ------------------------------------------------------------- footprints
    def place(self, ref, fpname, at, rot, comp, value):
        fp = pcbnew.FootprintLoad(G.PRETTY, fpname)
        if fp is None:
            raise RuntimeError("footprint not found: " + fpname)
        fp.SetReference(ref)
        fp.SetValue(value)
        fp.SetFPIDAsString(f"{G.LIBNAME}:{fpname}")
        fp.SetPosition(V(*at))
        fp.SetOrientationDegrees(rot)
        fp.SetPath(pcbnew.KIID_PATH("/" + uid("sym", ref)))
        fp.SetSheetname("/")
        fp.SetSheetfile(G.NAME + ".kicad_sch")
        # the coverlay opening is pinned on each footprint: a plotter that changes the board-wide mask margin
        # (the Fabrication Toolkit sets 0.05) must not change the openings measured in docs/review/dfm.md
        fp.SetLocalSolderMaskMargin(MM(P.RULES["mask_expansion"]))
        for k in ("MPN", "Manufacturer", "LCSC", "FT Rotation Offset", "Datasheet", "Description"):
            v = comp["fields"].get(k)
            if v:
                fp.SetField(k, v)
        for fld in fp.GetFields():
            if fld.GetName() not in ("Reference",):
                fld.SetVisible(False)
        fp.Reference().SetVisible(False)
        for pad in fp.Pads():
            nm = self.padnet.get((ref, pad.GetNumber()))
            if nm:
                pad.SetNet(self.net(nm))
        self.b.Add(fp)
        return fp


# =====================================================================================
def add_teardrops(board, B):
    """Copper teardrops (filled polygons on the track's net) where a narrow track meets a pad or via.

    Flex copper cracks at abrupt width changes; KiCad's own teardrop generator only runs in the GUI,
    so the fillets are drawn here explicitly.  Returns the number added.
    """
    import math as _m
    step = pcbnew.FromMM(0.01)
    count = 0
    pads = [pd for fp in board.GetFootprints() for pd in fp.Pads()]
    vias = [t for t in board.GetTracks() if t.GetClass() == "PCB_VIA"]
    for t in list(board.GetTracks()):
        if t.GetClass() != "PCB_TRACK":
            continue
        w = pcbnew.ToMM(t.GetWidth())
        for end, other in ((t.GetStart(), t.GetEnd()), (t.GetEnd(), t.GetStart())):
            ex, ey = pcbnew.ToMM(end.x), pcbnew.ToMM(end.y)
            ox, oy = pcbnew.ToMM(other.x), pcbnew.ToMM(other.y)
            seg = _m.hypot(ox - ex, oy - ey)
            if seg < 0.3:
                continue
            ux, uy = (ox - ex) / seg, (oy - ey) / seg
            nx, ny = -uy, ux
            target = None
            for pd in pads:
                if pd.GetNetCode() == t.GetNetCode() and pd.IsOnLayer(t.GetLayer()) and pd.HitTest(end):
                    target = ("pad", pd)
                    break
            if target is None:
                for v in vias:
                    if v.GetNetCode() == t.GetNetCode() and (v.GetPosition() - end).EuclideanNorm() < pcbnew.FromMM(0.01):
                        target = ("via", v)
                        break
            if target is None:
                continue
            kind, obj = target

            def inside(dx, dy):
                return obj.HitTest(pcbnew.VECTOR2I(pcbnew.FromMM(ex + dx), pcbnew.FromMM(ey + dy)))

            # distance to the edge along the track, and half-extent across it
            d_edge = 0.0
            while inside(ux * (d_edge + 0.01), uy * (d_edge + 0.01)) and d_edge < 3:
                d_edge += 0.01
            hw = 0.0
            while inside(nx * (hw + 0.01), ny * (hw + 0.01)) and hw < 3:
                hw += 0.01
            hw2 = 0.0
            while inside(-nx * (hw2 + 0.01), -ny * (hw2 + 0.01)) and hw2 < 3:
                hw2 += 0.01
            half0 = min(hw, hw2, 2.0 * w) * 0.9
            if half0 <= w / 2 + 0.02:
                continue
            length = min(0.5 + half0, seg - d_edge - 0.05)
            if length < 0.15:
                continue
            pts = []
            n_s = 8
            for i in range(n_s + 1):                     # one flank, pad edge -> track
                sfr = i / n_s
                half = w / 2 + (half0 - w / 2) * (1 - sfr) ** 2
                s_ = d_edge + length * sfr
                pts.append((ex + ux * s_ + nx * half, ey + uy * s_ + ny * half))
            for i in range(n_s, -1, -1):                 # other flank back
                sfr = i / n_s
                half = w / 2 + (half0 - w / 2) * (1 - sfr) ** 2
                s_ = d_edge + length * sfr
                pts.append((ex + ux * s_ - nx * half, ey + uy * s_ - ny * half))
            pts.append((ex - nx * half0, ey - ny * half0))
            pts.append((ex + nx * half0, ey + ny * half0))
            sh = pcbnew.PCB_SHAPE(board)
            sh.SetShape(pcbnew.SHAPE_T_POLY)
            sh.SetPolyPoints([pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y)) for x, y in pts])
            sh.SetLayer(t.GetLayer())
            sh.SetWidth(0)
            sh.SetFilled(True)
            sh.SetNet(t.GetNet())
            board.Add(sh)
            count += 1
    return count


# =====================================================================================
def outline_vertices():
    """Board outline as (vertex, fillet radius), clockwise on screen.

    Only two places keep a small radius: the concave corner where the bar meets the foot
    (1.0 mm; larger would show in the bezel window, and it sits on the PI stiffener) and the contact
    tab's leading corners (Hirose R0.2).  Every other turn is a 1.6-4 mm sweep.
    """
    half = (IN_X - OUT_X) / 2
    return [
        ((OUT_X, P.BAR["top_y"]), half),                   # full-round top end
        ((IN_X, P.BAR["top_y"]), half),
        ((IN_X, FOOT_T), 1.0),                             # concave, hidden under the bezel
        ((NECK_R, FOOT_T), P.FOOT["r_outer2"]),            # foot -> neck, outer sweep
        ((NECK_R, Y_TAPER0), 3.0),                         # 5.5 mm tail eases into the 3.5 mm tab
        ((G.TAB_R, TIP - T["tab_len"]), 3.0),
        ((G.TAB_R, TIP), T["tip_r"]),
        ((G.TAB_L, TIP), T["tip_r"]),
        ((NECK_L, FOOT_B), P.FOOT["r_inner2"]),            # concave: neck leaves the foot
        ((OUT_X, FOOT_B), P.FOOT["r_outer1"]),             # bar -> foot, outer sweep
    ]


def outline_polygon(seg=24):
    verts = outline_vertices()
    return prims_to_polygon(rounded_path([v for v, _ in verts], [r for _, r in verts], closed=True), seg)


def clip_below(poly, y0):
    """Keep the part of a polygon with y >= y0 (Sutherland-Hodgman against one horizontal line)."""
    out = []
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        ina, inb = a[1] >= y0, b[1] >= y0
        if ina:
            out.append(a)
        if ina != inb:
            t = (y0 - a[1]) / (b[1] - a[1])
            out.append((a[0] + t * (b[0] - a[0]), y0))
    return out


def clip_above(poly, y1):
    """Keep the part of a polygon with y <= y1."""
    flipped = [(x, -y) for x, y in poly]
    return [(x, -y) for x, y in clip_below(flipped, -y1)]


def front_region_polygon():
    """Bar + foot: everything that lies flat on the panel's protective sheet (stiffener and tape)."""
    return clip_above(outline_polygon(), FOOT_B)


def front_pieces():
    """The front stiffener (and tape) in two pieces, split at the hinge: the top pair's piece, and bar + foot."""
    front = front_region_polygon()
    h0, h1 = G.HINGE_Y
    return [clip_above(front, h0), clip_below(front, h1)]


def turn1(net, layer, lane_x, y_start, jog_x, target_y, end_pt, radii_after):
    """Points for one lane: down the bar at lane_x, concentric turn 1, 45-degree jog to its turn-2 row,
    then end_pt (the rest of the path).  Returns (points, fillet radii)."""
    r1 = C1[0] - lane_x
    y1 = C1[1] + r1
    pts = [(lane_x, y_start), (lane_x, y1), (jog_x, y1), (jog_x + abs(target_y - y1), target_y)]
    return pts + end_pt, [r1, 0.5, 0.5] + radii_after


def build(padnet, comps):
    global BAR_END
    with open(G.PCB, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(skeleton_text())
    board = pcbnew.LoadBoard(G.PCB)
    B = Builder(board, padnet)
    FC, BC = pcbnew.F_Cu, pcbnew.B_Cu

    # --------------------------------------------------------------- footprints
    for d in G.LEDS:
        c = comps[d["ref"]]
        B.place(d["ref"], G.FP_LED, (XP, d["y"]), 270, c, c["value"])
    B.place(G.DW_REF, G.FP_SOT, DW_AT, 90, comps[G.DW_REF], comps[G.DW_REF]["value"])
    B.place(G.DC_REF, G.FP_SOT, DC_AT, 90, comps[G.DC_REF], comps[G.DC_REF]["value"])
    B.place("J1", G.FP_TAIL, (P.J3["center_x"], TIP), 0, comps["J1"], comps["J1"]["value"])
    for ref, at in TP_AT.items():
        B.place(ref, G.FP_TP, at, 0, comps[ref], comps[ref]["value"])

    # --------------------------------------------------------------- outline
    verts = outline_vertices()
    B.shape_prims(rounded_path([v for v, _ in verts], [r for _, r in verts], closed=True), pcbnew.Edge_Cuts, 0.05)

    cool, warm = G.COOL, G.WARM          # chain order: top first (current flows down the bar)

    def gap_centre(pair):                # centre of the 1.3 mm gap inside a warm/cool pair
        return (XP, (cool[pair]["y"] + warm[pair]["y"]) / 2)

    # --------------------------------------------------------------- bar: cool links on the F lane behind the pads
    for i in range(len(cool) - 1):
        yk = G.k_pad(cool[i])[1]
        yn = G.a_pad(cool[i + 1])[1]
        B.route("/" + G.LINK_C[i], FC, W_BAR, [(XP, yk), (W_LANE_F, yk), (W_LANE_F, yn), (XP, yn)], 0.3)
    # --------------------------------------------------------------- bar: warm links on B.Cu under the column
    for i in range(len(warm) - 1):
        net = "/" + G.LINK_W[i]
        v1 = (XP, warm[i]["y"] + PAD_EDGE + VIA_GAP)        # between the pairs, below the upper warm LED
        v2 = gap_centre(i + 1)                               # inside the next pair, above its warm anode
        B.route(net, FC, W_BAR, [G.k_pad(warm[i]), v1])
        B.via(net, v1)
        B.route(net, BC, W_BAR, [v1, v2])
        B.via(net, v2)
        B.route(net, FC, W_BAR, [v2, G.a_pad(warm[i + 1])])
    # --------------------------------------------------------------- anode feeds start at the top pair
    v_wa = gap_centre(0)                                     # W_A: B lane -> via inside the top pair -> D1 anode
    B.via("W_A", v_wa)
    B.route("W_A", FC, W_BAR, [v_wa, G.a_pad(warm[0])])
    v_ca = (XP, cool[0]["y"] - PAD_EDGE - VIA_GAP)           # C_A: B lane -> via above the top LED -> D6 anode
    B.via("C_A", v_ca)
    B.route("C_A", FC, W_BAR, [v_ca, G.a_pad(cool[0])])

    # --------------------------------------------------------------- bar bottom -> foot: four concentric sweeps
    y_w = warm[-1]["y"] + PAD_EDGE + 0.5                     # below the bottom LED: lanes widen and jog
    BAR_END = y_w + 0.6
    jog0 = C1[0] + 0.35                                      # east end of turn 1: rows step to their turn-2 rows
    d11 = {n: sot_pin(DW_AT, n) for n in (1, 2, 3)}
    d12 = {n: sot_pin(DC_AT, n) for n in (1, 2, 3)}
    y_d_top = Y_DIODE - 2.3                                  # columns step sideways onto the diode pins here
    # W- (F): bottom warm cathode -> column -> turn 1 -> up to the north row -> turn 2 -> D11.2
    # It passes D11.3 (W_A) 0.1 mm right of the pad-2 column, so D11.3's coverlay opening keeps 0.15+ from it.
    B.route("W-", FC, W_WIDE, [G.k_pad(warm[-1]), (XP, BAR_END)])
    x_wm = d11[2][0] + 0.10
    pts, rad = turn1("W-", FC, XP, BAR_END, jog0, ROW["W-"],
                     [(COL["W-"], ROW["W-"]), (COL["W-"], y_d_top - 0.6), (x_wm, y_d_top - 0.6 + (x_wm - COL["W-"])),
                      (x_wm, d11[2][1] - 0.55), d11[2]],
                     [COL["W-"] - C2[0], 0.3, 0.3, 0.2])
    B.route("W-", FC, W_WIDE, pts, rad)
    # C- (F): bottom cool cathode -> F lane -> x 43.6 -> turn 1 -> up to its row -> turn 2 -> D12.2
    B.route("C-", FC, W_BAR, [G.k_pad(cool[-1]), (W_LANE_F, G.k_pad(cool[-1])[1]), (W_LANE_F, y_w),
                              (X1["C-"], BAR_END)], [0.3, 0.3])
    pts, rad = turn1("C-", FC, X1["C-"], BAR_END, jog0 + 1.95, ROW["C-"],
                     [(COL["C-"], ROW["C-"]), (COL["C-"], Y_DIODE + 0.2), (d12[2][0], Y_DIODE + 0.55), d12[2]],
                     [COL["C-"] - C2[0], 0.3, 0.3])
    B.route("C-", FC, W_WIDE, pts, rad)
    # W_A (B then F): lane 44.9 -> turn 1 on B -> step to its row -> via -> turn 2 -> D11.3
    v_wa_f = (jog0 + 3.35, ROW["W_A"])
    y_wa0 = FOOT_T                              # W_A hugs the bar inner edge: stay narrow until the foot
    B.route("W_A", BC, W_BAR, [v_wa, (W_BWM, v_wa[1]), (W_BWM, y_wa0)], [0.3])
    pts, rad = turn1("W_A", BC, W_BWM, y_wa0, jog0 + 0.6, ROW["W_A"], [v_wa_f], [])
    B.route("W_A", BC, W_WIDE, pts, rad)
    B.via("W_A", v_wa_f)
    B.route("W_A", FC, W_WIDE, [v_wa_f, (COL["W_A"], ROW["W_A"]), (COL["W_A"], y_d_top), (d11[3][0], y_d_top + (d11[3][0] - COL["W_A"])),
                                d11[3]], [COL["W_A"] - C2[0], 0.3, 0.3])
    # C_A (B then F): lane 43.4 -> x 44.3 -> turn 1 on B -> step to its row -> via -> turn 2 -> D12.3
    v_ca_f = (jog0 + 3.55, ROW["C_A"])
    B.route("C_A", BC, W_BAR, [v_ca, (W_BCM, v_ca[1]), (W_BCM, y_w), (X1["C_A"], BAR_END)], [0.3, 0.3])
    pts, rad = turn1("C_A", BC, X1["C_A"], BAR_END, jog0 + 0.4, ROW["C_A"], [v_ca_f], [])
    B.route("C_A", BC, W_WIDE, pts, rad)
    B.via("C_A", v_ca_f)
    B.route("C_A", FC, W_WIDE, [v_ca_f, (COL["C_A"], ROW["C_A"]), d12[3]], [COL["C_A"] - C2[0]])

    # --------------------------------------------------------------- back run: fan-in to the fingers, LED_SW tie
    y_f0 = TP_AT["TP1"][1] + 0.9                   # fan-in to the finger pitch starts here
    y_f1 = TIP - T["tab_len"] + 0.55               # ... and is done here, where the tail is down to ~3.6 mm
    y_pad = TIP - T["finger_setback"] - T["finger_len"] / 2
    fan = {"LED_SW_a": (d12[1], 1), "C-": (d12[2], 2), "LED_SW_b": (d11[1], 5), "W-": (d11[2], 6)}
    for key, (start, fn) in fan.items():
        fx = G.finger_x(fn)
        y0 = TP_AT["TP3"][1] + 0.7 if key == "W-" else y_f0    # W- leaves its column early: the taper cuts it
        B.route(key, FC, W_WIDE, [start, (start[0], y0)])
        B.route(key, FC, W_FINGER, [(start[0], y0), (start[0], y0 + 0.3), (fx, y_f1), (fx, y_pad)], 0.6)
    v_t1 = TP_AT["TP1"]
    v_t2 = (d11[1][0], TP_AT["TP1"][1])
    B.via("LED_SW", v_t1)
    B.via("LED_SW", v_t2)
    B.route("LED_SW", BC, 0.3, [v_t1, v_t2])

    # --------------------------------------------------------------- tear stops
    y_r1 = Y_STIFF - 0.3
    xl = NECK_L + RAIL_IN + RAIL_W / 2
    xr = NECK_R - RAIL_IN - RAIL_W / 2
    B.shape_prims([("line", (xl, FOOT_B + P.FOOT["r_inner2"] + 0.2), (xl, y_r1))], FC, RAIL_W)
    B.shape_prims([("line", (xr, FOOT_T + P.FOOT["r_outer2"] + 0.2), (xr, y_r1))], FC, RAIL_W)
    cx, cy, rr = NECK_L - P.FOOT["r_inner2"], FOOT_B + P.FOOT["r_inner2"], P.FOOT["r_inner2"] + 0.45
    pts = [(cx + rr * math.cos(math.radians(a)), cy + rr * math.sin(math.radians(a))) for a in (-40, -20, 0)]
    B.shape_prims([("arc", pts[0], pts[1], pts[2])], BC, RAIL_W)

    # --------------------------------------------------------------- rule areas: bend zone
    bz0, bz1 = T["bend_zone"]
    zone = [(NECK_L - 0.5, bz0), (NECK_R + 0.5, bz0), (NECK_R + 0.5, bz1), (NECK_L - 0.5, bz1)]
    B.rule_area(zone, [FC, BC], no_tracks=False, name="bend: no vias or pads")
    B.rule_area(zone, [BC], no_tracks=True, no_vias=True, no_pads=True, name="bend: single-layer copper")
    # hinge between the top pair and the next: bare flex, tracks straight through on both layers
    h0, h1 = G.HINGE_Y
    hz = [(OUT_X - 0.5, h0), (IN_X + 0.5, h0), (IN_X + 0.5, h1), (OUT_X - 0.5, h1)]
    B.rule_area(hz, [FC, BC], no_tracks=False, name="hinge: no vias or pads")

    # --------------------------------------------------------------- stiffener, adhesive, bend zone, panel reference
    U1, U2, U3, U4 = pcbnew.User_1, pcbnew.User_2, pcbnew.User_3, pcbnew.User_4
    back = clip_below(outline_polygon(), Y_STIFF)
    for piece in front_pieces():
        B.poly(piece, U1)
        B.poly(piece, U2)
    B.poly(back, U1)
    B.rect((NECK_L, bz0), (NECK_R, bz1), U3, 0.1)
    B.rect((OUT_X, h0), (IN_X, h1), U3, 0.1)
    B.text("HINGE (3.68in: fold back)", (OUT_X - 2.0, (h0 + h1) / 2 - 14.0), U3, 0.8, 90)
    B.text("BEND ZONE: no stiffener, vias or pads", (NECK_R + 3.5, (bz0 + bz1) / 2), U3, 0.8, 90)
    B.text("PI 0.225 stiffener, B side", (NECK_R + 3.5, TIP - 7.0), U1, 0.8, 90)
    B.text("PI 0.225 stiffener + 3M 9077 tape, B side", (OUT_X - 2.0, 90.0), U1, 0.8, 90)
    B.text("3M 9077 tape 0.05 mm, B side, over the PI stiffener", (OUT_X - 2.0, 90.0), U2, 0.8, 90)
    pn, ac = P.PANEL, P.ACTIVE
    B.rect((pn["left"], pn["top"]), (pn["right"], pn["bottom"]), U4, 0.1)
    B.rect((ac["left"], ac["top"]), (ac["right"], ac["bottom"]), U4, 0.1)
    m = P.BEZEL_MARGIN
    B.rect((ac["left"] - m, ac["top"] - m), (ac["right"] + m, ac["bottom"] + m), U4, 0.05)
    B.line((pn["left"] + pn["ps_inset_long"], pn["top"] + 0.5), (pn["left"] + pn["ps_inset_long"], pn["ps_bottom"]), U4, 0.05)
    B.line((pn["left"], pn["ps_bottom"]), (pn["right"], pn["ps_bottom"]), U4, 0.05)
    B.text("4.26in panel glass edge", (74.0, pn["top"] - 1.2), U4, 1.0)
    B.text("active area 55.68 x 92.8", (74.0, 88.0), U4, 1.5)
    B.text("bezel aperture = active + 0.7", (74.0, 92.0), U4, 1.0)
    B.text("PS edge (ledge below)", (74.0, pn["ps_bottom"] + 1.0), U4, 0.8)
    B.text("FOLD LINE = glass edge", (74.0, pn["bottom"] + 1.0), U4, 0.8)
    B.rect((58.5, pn["bottom"] - 4.0), (89.8, pn["bottom"] + 2.0), U4, 0.05)
    B.text("EPD FPC bond (keep clear)", (74.0, pn["bottom"] - 2.0), U4, 0.8)
    p3, a3 = P.PANEL_368, P.ACTIVE_368                           # the 3.68in panel, dashed-thin
    B.rect((p3["left"], p3["top"]), (p3["right"], p3["bottom"]), U4, 0.05)
    B.rect((a3["left"], a3["top"]), (a3["right"], a3["bottom"]), U4, 0.05)
    B.text("3.68in glass / active area", (74.0, p3["top"] + 1.2), U4, 1.0)

    # --------------------------------------------------------------- silkscreen
    SF = pcbnew.F_SilkS
    B.text("LIGHT STRIP " + P.REVISION, (49.6, (ROW["W_A"] + ROW["C-"]) / 2), SF, 1.0)
    tx, ty = G.finger_x(1), TIP - T["tab_len"] + 0.2           # pin-1 marker just outside the J3 mouth
    B.line((tx - 0.25, ty - 0.5), (tx + 0.25, ty - 0.5), SF, 0.15)
    B.line((tx - 0.25, ty - 0.5), (tx, ty), SF, 0.15)
    B.line((tx + 0.25, ty - 0.5), (tx, ty), SF, 0.15)
    for y in (P.PANEL["bottom"] - 0.8, bz1 + 0.4):           # fold marks just outside the creases
        B.line((NECK_L + 0.35, y), (NECK_L + 0.85, y), SF, 0.15)
        B.line((NECK_R - 0.85, y), (NECK_R - 0.35, y), SF, 0.15)
    for y in (h0 + 0.2, h1 - 0.2):                           # hinge ends: just inside, clear of pad openings
        B.line((OUT_X + 0.25, y), (OUT_X + 0.75, y), SF, 0.15)
    B.text("S", (TP_AT["TP1"][0], TP_AT["TP1"][1] + 1.35), SF, 1.0)   # each letter sits directly below its pad
    B.text("C", (TP_AT["TP2"][0], TP_AT["TP2"][1] + 1.35), SF, 1.0)
    B.text("W", (TP_AT["TP3"][0], TP_AT["TP3"][1] + 1.35), SF, 1.0)

    # --------------------------------------------------------------- fab notes (outside the board)
    notes = [
        "SILKSCREEN LIGHT STRIP rev " + P.REVISION + " - FAB NOTES (JLCPCB flex)",
        "2 layers, finished 0.11 mm, 25 um adhesiveless PI core, 1/3 oz Cu, BLACK coverlay, white silk, ENIG.",
        "Stiffener PI 0.225 mm, B side (file *-Stiffener_PI0_225.gbr), 3 pieces: top pair, bar + foot, last 14 mm of the tail.",
        "Gold fingers: 0.30 +/-0.03 mm total, tab width 3.50 +/-0.05 mm (Hirose FH34SRJ). Fingers on F, 0.2 mm from the tip.",
        "3M 9077 tape on the B side of the bar + foot (file *-Adhesive_3M9077.gbr), over the stiffener.",
        "No stiffener, vias or pads in the bend zone or in the hinge between the top two pairs. Tear-stop rails along the neck.",
        "Min track/space 0.15/0.15, via 0.3/0.55. Outline laser cut; every corner radiused (tab corners R0.2).",
    ]
    for i, s in enumerate(notes):
        B.text(s, (112.0, 60.0 + i * 2.0), pcbnew.Cmts_User, 1.0, 0, justify="left")

    n_td = add_teardrops(board, B)
    print("teardrops:", n_td)
    board.SetFileName(G.PCB)
    pcbnew.SaveBoard(G.PCB, board)
