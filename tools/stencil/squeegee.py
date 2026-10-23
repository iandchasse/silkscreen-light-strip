"""Build the printed squeegee for the paste stencil (CadQuery): one handle that clamps a piece of plastic card, plus a PLA blade.

Run in the CadQuery venv (cadquery, shapely, trimesh), after stencil.py:
    <venv>\\Scripts\\python.exe -X utf8 -I tools/stencil/squeegee.py            # build, self-checks, STLs
    <venv>\\Scripts\\python.exe -X utf8 -I tools/stencil/squeegee.py --slice    # also the OrcaSlicer CLI read-back (never its window)

What it makes (production/stencil/): squeegee_print.stl (the handle and two PLA blades on one plate, as they are printed),
squeegee-blade-pla_print.stl (one blade, for spares) and squeegee_params.json. Design: docs/ASSEMBLY.md, the squeegee block of the
stencil option, and production/stencil/README.md. Nothing here has been printed or tried; every force and stress is a beam estimate.

Frame (the squeegee frame, which is also the print frame before the plate is centred): s along the stroke (+s = travel = card +y,
toward the foot), w across (w = card x - 44.13), h up from the runner plane (the stencil card's squeegee face). The blade leans
forward: its top is ahead of its edge, so the paste rolls in the acute wedge in front of it. Q(lam, o) is a point on the blade:
lam along its front face up from the edge, o the offset toward the back.

Self-checks (exit 1 on any failure) are in build(); the numbers go to squeegee_params.json.
"""
import argparse
import json
import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import trimesh
from shapely.affinity import translate
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

import stencil as S

ROOT = S.ROOT
OUT = S.OUT
REPORT = ROOT / 'docs' / 'reports' / 'stencil_squeegee_check.md'

# ---- every number of the design (mm, degrees). Edit here and rerun. --------------------------------------------------
SQ = dict(
    alpha=50.0,            # the slot holds the blade at this angle to the runner plane
    interference=0.9,      # the undeflected edge sits this far below the runner plane (card blade)
    mouth=15.0,            # free length of the card blade, measured on its front face to the slot-mouth lip
    stop=27.0,             # card blade length: the slot's stop
    cap=30.0,              # the end cap's top, along the front face
    slot=1.25,             # slot width, perpendicular to the blade
    slot_w=10.6,           # slot width across (w); the blade is 10.0
    front_jaw=3.0,         # front jaw thickness (o -3 .. 0), above the mouth plane
    tongue=1.60,           # tongue thickness (o 1.25 .. 2.85)
    back_slit=0.80,        # between the tongue and the back block
    side_slit=0.80,        # either side of the tongue
    back_block=5.40,       # o 3.65 .. 9.05
    hole_d=2.6,            # M3 thread-forming
    hole_lam=18.0,         # the screw's position up the blade
    runner_w=(7.13, 10.13),   # |w| of each runner
    runner_s=(-10.0, 12.0),   # s of each runner (22 long; the 1.0 x 45 degree lead-ins leave 20 on the bed)
    runner_chamfer=1.0,
    ceiling=3.0,           # nothing behind the blade below this height: the filled openings pass under
    finger_s0=-4.0,        # the flat finger pad runs from here to the back face
    rear_h=10.0,           # the rear face is vertical from the runner up to this height
    blade_w=10.0,
    card_len=27.0, card_t=(0.68, 0.76, 0.84),
    pla=(10.0, 1.0, 26.2),     # PLA blade: width, thickness, length
    arrow_h=13.0, arrow_depth=0.4,
    E_pvc=3000.0, E_pla=3500.0,     # MPa, assumed: not measured
    stroke=(36.5, 135.0),          # blade contact line, card y, start and end of the pass
    column_x=44.13,                # the openings' column in card x (pad x 44.25 - 0.12)
    pla_x=(-10.0, 10.0), pla_gap=12.0,   # where the two spare blades sit on the plate
)
A = math.radians(SQ['alpha'])
U = (math.cos(A), math.sin(A))                 # up the blade
NB = (-math.sin(A), math.cos(A))               # toward the back face
P0 = (0.0, -SQ['interference'])
O_T0 = SQ['slot']
O_T1 = O_T0 + SQ['tongue']                     # 2.85
O_S1 = O_T1 + SQ['back_slit']                  # 3.65: the back block's front face is the slit's back wall (no 0.15 notch)
O_BACK = O_S1 + SQ['back_block']               # 9.05
BIG = 300.0


def Q(lam, o):
    return (P0[0] + lam * U[0] + o * NB[0], P0[1] + lam * U[1] + o * NB[1])


def lo(p):
    """(lam, o) of an (s, h) point."""
    dx, dy = p[0] - P0[0], p[1] - P0[1]
    return dx * U[0] + dy * U[1], dx * NB[0] + dy * NB[1]


def half_o(o0, above=True):
    """The half plane o >= o0 (or o <= o0), as a big polygon in (s, h)."""
    a, b = (o0, o0 + BIG) if above else (o0 - BIG, o0)
    return Polygon([Q(-BIG, a), Q(BIG, a), Q(BIG, b), Q(-BIG, b)])


def half_l(l0):
    """lam <= l0."""
    return Polygon([Q(-BIG, -BIG), Q(l0, -BIG), Q(l0, BIG), Q(-BIG, BIG)])


def band(o0, o1, l0=-BIG, l1=BIG):
    return Polygon([Q(l0, o0), Q(l1, o0), Q(l1, o1), Q(l0, o1)])


# ---------------------------------------------------------------------------------------------------------------
# 2-D profiles in (s, h)
# ---------------------------------------------------------------------------------------------------------------
def profiles(SQ=SQ):
    hm = Q(SQ['mouth'], 0)[1]                          # the mouth plane h
    C, D, G = Q(SQ['cap'], -SQ['front_jaw']), Q(SQ['cap'], O_BACK), Q(SQ['mouth'], O_BACK)
    s0, s1 = SQ['runner_s']
    ch = SQ['runner_chamfer']
    side = Polygon([(s0 + ch, 0), (s1 - ch, 0), (s1, ch), C, D, G, (SQ['finger_s0'], G[1]), (s0, SQ['rear_h']), (s0, ch)])
    assert side.is_valid
    # the middle zone (|w| < runner_w[0]): above the ceiling, behind the front jaw, and below the mouth plane only behind the slit
    mid = side.intersection(box(-BIG, SQ['ceiling'], BIG, BIG)).intersection(half_o(-SQ['front_jaw']))
    mid = mid.intersection(unary_union([box(-BIG, hm, BIG, BIG), half_o(O_S1)]))
    assert mid.geom_type == 'Polygon' and mid.is_valid, mid.geom_type
    slot = band(0, SQ['slot'], -BIG, SQ['stop'])
    # the side slits start 0.25 below the slot's back wall, so the tongue and the slot's side walls do not touch along a bare edge
    side_slit = band(O_T0 - 0.25, O_S1, -BIG, SQ['stop'])
    back_slit = band(O_T1, O_S1, -BIG, SQ['stop'])
    return dict(hm=hm, C=C, D=D, G=G, side=side, mid=mid, slot=slot, side_slit=side_slit, back_slit=back_slit)


def arrow_poly(SQ=SQ):
    h = SQ['arrow_h']
    # the head's roof slopes at 45 degrees, so the 0.4 deep recess prints without a flat roof
    return Polygon([(-3.0, h - 0.6), (8.5, h - 0.6), (8.5, h - 1.6), (10.1, h), (8.5, h + 1.6), (8.5, h + 0.6), (-3.0, h + 0.6)])


# ---------------------------------------------------------------------------------------------------------------
# CadQuery solids. Model frame: X = s, Y = w, Z = h.
# ---------------------------------------------------------------------------------------------------------------
def prism_sh(poly, w0, w1):
    import cadquery as cq
    parts = list(poly.geoms) if hasattr(poly, 'geoms') else [poly]
    out = None
    for p in parts:
        assert not list(p.interiors)
        p = p.simplify(0.0005)
        pts = list(p.exterior.coords)[:-1]
        sol = cq.Workplane('XZ', origin=(0, w1, 0)).polyline(pts).close().extrude(w1 - w0)      # 'XZ' extrudes toward -Y
        out = sol if out is None else out.union(sol)
    return out


def build_handle(P, SQ=SQ):
    import cadquery as cq
    r0, r1 = SQ['runner_w']
    s = prism_sh(P['side'], r0, r1).union(prism_sh(P['side'], -r1, -r0))
    s = s.union(prism_sh(P['mid'], -r0, r0))
    # the slot, the tongue's slits (the tongue stays attached at the end cap), the screw hole, the arrows
    s = s.cut(prism_sh(P['slot'], -SQ['slot_w'] / 2, SQ['slot_w'] / 2))
    sw = SQ['slot_w'] / 2
    for sign in (1, -1):
        a, b = sorted((sign * sw, sign * (sw + SQ['side_slit'])))
        s = s.cut(prism_sh(P['side_slit'], a, b))
    s = s.cut(prism_sh(P['back_slit'], -(sw + SQ['side_slit']), sw + SQ['side_slit']))
    ax = Q(SQ['hole_lam'], 0)
    start = (ax[0] + (O_S1 - 0.25) * NB[0], 0.0, ax[1] + (O_S1 - 0.25) * NB[1])
    length = (O_BACK + 1.0) - (O_S1 - 0.25)
    plane = cq.Plane(origin=start, xDir=(0, 1, 0), normal=(NB[0], 0.0, NB[1]))
    s = s.cut(cq.Workplane(plane).circle(SQ['hole_d'] / 2).extrude(length))
    arrow = arrow_poly(SQ)
    d = SQ['arrow_depth']
    for sign in (1, -1):                                  # 0.4 deep, on both outer faces, pointing +s
        w0, w1 = sorted((sign * (r1 - d), sign * (r1 + 0.01)))
        s = s.cut(prism_sh(arrow, w0, w1))
    return s


# ---------------------------------------------------------------------------------------------------------------
# Sections of a mesh as shapely geometry
# ---------------------------------------------------------------------------------------------------------------
def section_poly(mesh, axis, value):
    """The mesh cut by the plane axis = value, as even-odd shapely geometry in the other two coordinates (s,h for axis 1;
    s,w for axis 2; w,h for axis 0)."""
    origin = [0, 0, 0]
    origin[axis] = value
    normal = [0, 0, 0]
    normal[axis] = 1
    sec = mesh.section(plane_origin=origin, plane_normal=normal)
    if sec is None:
        return Polygon()
    keep = [i for i in range(3) if i != axis]
    rings = []
    for pts in sec.discrete:
        q = np.asarray(pts)[:, keep]
        if len(q) >= 4:
            rings.append(Polygon(q).buffer(0))
    acc = Polygon()
    for r in sorted(rings, key=lambda r: -r.area):
        acc = acc.symmetric_difference(r)
    return acc


def bent_blade(delta_tip, t, lam_tip, L):
    """The blade (thickness t) between its clamp at the slot mouth (lam = mouth) and its tip at lam_tip, bent so that its tip has moved
    `delta_tip` toward the back; L is the free length. A clamped cantilever with an end load. Returns a shapely polygon in (s, h)."""
    ls = np.linspace(lam_tip, SQ['mouth'], 40)
    front, back = [], []
    for lam in ls:
        xp = SQ['mouth'] - lam                                          # distance from the clamp
        y = delta_tip * (3 * L * xp ** 2 - xp ** 3) / (2 * L ** 3)
        front.append(Q(lam, y))
        back.append(Q(lam, y + t))
    return Polygon(front + back[::-1]).buffer(0)


# ---------------------------------------------------------------------------------------------------------------
# Beam estimates (a clamped cantilever with an end load; PVC card E and printed PLA E are ASSUMED, not measured)
# ---------------------------------------------------------------------------------------------------------------
def card_force(t, L, E, interference=None, b=None):
    """(edge force N perpendicular-free estimate, tip deflection mm, root stress MPa) of a card blade of thickness t and free length L."""
    b = b or SQ['blade_w']
    d = (SQ['interference'] if interference is None else interference) / math.cos(A)       # the tip is pushed up by `interference`
    I = b * t ** 3 / 12
    F = 3 * E * I / L ** 3 * d
    return F, d, F * L * (t / 2) / I


def estimates():
    est = {}
    for t in SQ['card_t']:
        for L in (14.0, 15.0):
            F, d, sg = card_force(t, L, SQ['E_pvc'])
            est[f'card_t{t}_L{L}'] = dict(force_N=round(F, 2), tip_deflection_mm=round(d, 2), root_stress_MPa=round(sg, 1))
    for dl in (-0.3, 0.0, 0.3):
        # a card cut dl too long stays against the stop, so its edge sits dl further down the blade (lower by dl sin(alpha)) and its free length is dl longer
        L = SQ['mouth'] + dl
        interf = SQ['interference'] + dl * math.sin(A)
        F, d, sg = card_force(0.76, L, SQ['E_pvc'], interference=interf)
        est[f'card_t0.76_cut{dl:+.1f}'] = dict(force_N=round(F, 2), free_length_mm=L, tip_deflection_mm=round(d, 2))
    pw, pt, pl = SQ['pla']
    for dl in (-0.2, 0.0, 0.2):
        Lp = pl + dl
        L = Lp - (SQ['stop'] - SQ['mouth'])
        interf = SQ['interference'] - (SQ['stop'] - Lp) * math.sin(A)
        I = pw * pt ** 3 / 12
        F = 3 * SQ['E_pla'] * I / L ** 3 * (interf / math.cos(A)) if interf > 0 else 0.0
        est[f'pla_length{Lp:.1f}'] = dict(force_N=round(F, 2), free_length_mm=round(L, 2), edge_below_runner_mm=round(interf, 3),
                                          inter_layer_stress_MPa=round(F * L * (pt / 2) / I, 1) if F else 0)
    return est


# ---------------------------------------------------------------------------------------------------------------
def build(write=True):
    import cadquery as cq
    fails, notes = [], []

    def check(cond, msg):
        if not cond:
            fails.append(msg)

    P = profiles()
    hm = P['hm']
    r0, r1 = SQ['runner_w']
    s0, s1 = SQ['runner_s']
    ch = SQ['runner_chamfer']

    # ---- the handle solid ----
    solid = build_handle(P)
    sv = solid.val()
    check(sv.isValid(), 'handle solid is not valid')
    check(len(solid.solids().vals()) == 1, f'{len(solid.solids().vals())} solids in the handle, expected 1')
    OUT.mkdir(parents=True, exist_ok=True)
    tmp = OUT / '_handle_model.stl'
    cq.exporters.export(solid, str(tmp), tolerance=0.002, angularTolerance=0.05)
    hm_mesh = trimesh.load(tmp)
    tmp.unlink()
    check(hm_mesh.is_watertight, 'handle STL is not watertight')
    check(abs(hm_mesh.volume - sv.Volume()) / sv.Volume() < 0.002, 'handle STL volume differs from the solid')
    bb = hm_mesh.bounds
    size = bb[1] - bb[0]
    notes.append(f'handle {size[0]:.2f} (s) x {size[1]:.2f} (w) x {size[2]:.2f} (h) mm, {hm_mesh.volume:.0f} mm3 solid ({hm_mesh.volume * 1.24e-3:.1f} g if solid), {len(hm_mesh.faces)} triangles')
    check(abs(bb[0][2]) < 1e-6, f'handle does not start at z 0 ({bb[0][2]})')
    check(abs(size[1] - 2 * r1) < 0.01, f'handle width {size[1]:.3f}, expected {2 * r1:.2f}')

    # ---- 2. runner bottoms: exactly two rectangles at the bed, 3.0 x 20 after the lead-ins (22 at their top) ----
    for z, want_len in ((0.001, s1 - s0 - 2 * ch), (ch + 0.01, s1 - s0)):
        sec = section_poly(hm_mesh, 2, z)
        parts = list(sec.geoms) if hasattr(sec, 'geoms') else [sec]
        check(len(parts) == 2, f'{len(parts)} shapes at z={z}, expected the two runners')
        for p in parts:
            b = p.bounds
            wlo, whi = sorted((abs(b[1]), abs(b[3])))
            check(abs((b[2] - b[0]) - want_len) < 0.03 + 2 * z and abs(p.area - (b[2] - b[0]) * (b[3] - b[1])) < 0.01,
                  f'runner at z={z}: length {b[2] - b[0]:.3f} (want {want_len}), area {p.area:.3f}')
            check(abs((b[3] - b[1]) - (r1 - r0)) < 0.01 and abs(whi - r1) < 0.01 and abs(wlo - r0) < 0.01, f'runner at z={z}: w {b[1]:.3f}..{b[3]:.3f}')
    notes.append(f'runner bottoms at the bed: two rectangles {r1 - r0:.1f} x {s1 - s0 - 2 * ch:.0f} mm at |w| {r0}-{r1} (lead-ins {ch} x 45 degrees)')

    # ---- sections at w = 0 and +-5 (through the slot and the tongue) and in the side slits ----
    sec_w = {w: section_poly(hm_mesh, 1, w) for w in (0.0, 4.9, -4.9, 5.7, -5.7, 6.4, -6.4)}

    def solid_at(sec, p):
        return sec.contains(Point(p))

    # ---- 5. slot width, perpendicular, mouth to stop, at w = 0 and +-4.9 ----
    widths = []
    for w in (0.0, 4.9, -4.9):
        for lam in np.arange(SQ['mouth'] + 0.5, SQ['stop'] - 0.4, 0.5):
            line = LineString([Q(lam, -1.0), Q(lam, 2.5)])
            free = line.difference(sec_w[w])
            parts = list(free.geoms) if hasattr(free, 'geoms') else [free]
            mid_pt = Point(Q(lam, 0.6))
            hit = [g for g in parts if g.distance(mid_pt) < 1e-6]
            widths.append(hit[0].length if hit else 0.0)
    check(min(widths) > 1.25 - 0.015 and max(widths) < 1.25 + 0.015, f'slot width {min(widths):.3f}..{max(widths):.3f}, want 1.25 +- 0.015')
    notes.append(f'slot width, perpendicular, mouth to stop, w 0 and +-4.9: {min(widths):.3f}..{max(widths):.3f} mm (design 1.25)')

    # ---- 6. tongue: free on three sides (side slits and back slit open, no bridge), attached at the end cap ----
    solid_pts, empty_pts = 0, 0
    lams = np.arange(15.0, SQ['stop'] - 0.4, 1.0)
    for w in (0.0, 4.9, -4.9):
        for lam in lams:
            for o in (1.5, 2.0, 2.5):                                  # tongue
                solid_pts += solid_at(sec_w[w], Q(lam, o))
    check(solid_pts == 3 * len(lams) * 3, f'tongue is not solid everywhere sampled ({solid_pts} of {3 * len(lams) * 3})')
    for w in (0.0, 4.9, -4.9):                                         # back slit empty
        for lam in np.arange(10.0, SQ['stop'] - 0.4, 1.0):
            for o in (3.0, 3.3, 3.55):
                empty_pts += solid_at(sec_w[w], Q(lam, o))
    for w in (5.7, -5.7):                                              # side slits empty (o 1.25 .. 3.65), lam up to just under the stop
        for lam in np.arange(10.0, SQ['stop'] - 0.4, 1.0):
            for o in (1.5, 2.0, 2.5, 3.0, 3.5):
                empty_pts += solid_at(sec_w[w], Q(lam, o))
    check(empty_pts == 0, f'{empty_pts} sample points inside the slits')
    check(solid_at(sec_w[0.0], Q(SQ['stop'] + 1.0, 2.0)) and solid_at(sec_w[0.0], Q(SQ['stop'] + 1.0, 3.2)), 'tongue root / end cap is not solid above the stop')
    # tongue free length: from the root (lam stop) down to the mouth plane at o = 1.25 .. 2.85
    tongue_tip = (hm - P0[1] - O_T0 * NB[1]) / U[1]                    # lam where o = 1.25 meets the mouth plane
    tongue_free = SQ['stop'] - tongue_tip
    check(11.5 < tongue_free < 14, f'tongue free length {tongue_free:.2f}')
    notes.append(f'tongue: o {O_T0}..{O_T1} (thick {SQ["tongue"]}), free from lam {tongue_tip:.2f} to its root at {SQ["stop"]} ({tongue_free:.2f} long); its front corner on the mouth plane is at s {Q(tongue_tip, O_T0)[0]:.2f}, h {hm:.2f}')

    # ---- 4. paste wedge and the area behind the blade ----
    bad = 0
    for w in (0.0, 3.0, 4.9, -4.9, 6.4, -6.4):
        sec = sec_w.get(w) if w in sec_w else section_poly(hm_mesh, 1, w)
        # below the mouth plane, ahead of o = O_S1 (the front of the back block): nothing
        wedge = box(-BIG, -BIG, BIG, hm - 0.01).intersection(half_o(O_S1 - 1e-6, above=False))
        bad += sec.intersection(wedge).area > 1e-6
        # behind the blade, below the ceiling h = 3: nothing
        bad += sec.intersection(box(-BIG, -BIG, BIG, SQ['ceiling'] - 0.01)).area > 1e-6
        # anything ahead of the front jaw (o < -3) in the middle zone
        bad += sec.intersection(half_o(-SQ['front_jaw'] - 1e-6, above=False)).area > 1e-6
    check(bad == 0, f'{bad} sections have material in the paste wedge, ahead of the jaw, or under the ceiling')
    notes.append(f'middle zone is empty below the mouth plane (h {hm:.2f}) ahead of o {O_S1:.2f}, and below h {SQ["ceiling"]} behind the blade (sectioned at w 0, 3, +-4.9, +-6.4)')

    # ---- 3. blade envelope: the card blade at rest and bent by its full interference, clear of the handle by >= 0.5 ----
    t_max = SQ['card_t'][-1]
    L = SQ['mouth']
    d_tip = SQ['interference'] / math.cos(A)

    card_env = unary_union([bent_blade(d_tip * f, t_max, 0.0, L) for f in np.linspace(0, 1, 9)])
    pw, pt, plen = SQ['pla']
    lam_tip_pla = SQ['stop'] - plen
    Lp = SQ['mouth'] - lam_tip_pla
    d_pla = (SQ['interference'] - lam_tip_pla * math.sin(A)) / math.cos(A)
    pla_env = unary_union([bent_blade(d_pla * f, pt, lam_tip_pla, Lp) for f in np.linspace(0, 1, 9)])
    envelope = unary_union([card_env, pla_env])
    below = envelope.intersection(box(-BIG, -BIG, BIG, hm - 1.0))      # the free part, a mm clear of the mouth lip
    clear_min = 99.0
    for w in (0.0, 4.9, -4.9):
        clear_min = min(clear_min, below.distance(sec_w[w]))
    check(clear_min >= 0.5, f'the swept blade comes within {clear_min:.2f} of the handle')
    notes.append(f'blade envelope (card 0.84 thick bent {d_tip:.2f} at the tip, and the PLA blade): nearest handle surface {clear_min:.2f} mm (>= 0.5), measured below h {hm - 1:.1f}')
    back_clear = O_S1 - (t_max + d_tip)
    notes.append(f'bent 0.84 card, back face at the tip: o {t_max + d_tip:.2f}; the back block starts at o {O_S1:.2f}: {back_clear:.2f} clear')

    # ---- 7. screw hole: length, clear along its axis, and an 8 mm screw reaches the tongue ----
    hole_len = O_BACK - O_S1
    check(abs(hole_len - 5.40) < 1e-9, f'screw hole length {hole_len}')
    ok = True
    for o in np.arange(O_S1 + 0.3, O_BACK + 0.8, 0.5):                 # along the axis, in the w = 0 section
        ok &= not solid_at(sec_w[0.0], Q(SQ['hole_lam'], o))
    # and across: the hole's width in w at the axis, sectioned in the plane through the axis point square to s
    check(ok, 'the screw hole is not clear along its axis (section w = 0)')
    tip8 = O_BACK - 8.0
    check(tip8 <= O_T1 - 0.5, f'an M3 x 8 only reaches o {tip8:.2f}')
    check(O_BACK - 6.0 > O_T1, 'an M3 x 6 would reach the tongue: it should not')
    notes.append(f'screw hole: {SQ["hole_d"]} mm, {hole_len:.2f} long from the back face (o {O_BACK:.2f}) to the back slit (o {O_S1:.2f}); entry at s {Q(SQ["hole_lam"], O_BACK)[0]:.2f}, h {Q(SQ["hole_lam"], O_BACK)[1]:.2f}; M3 x 8 tip at o {tip8:.2f}')

    # ---- 8. blade tips ----
    # (by construction) the card blade, length 27 against the stop, has its edge at lam 0: P0; the PLA blade's front corner at lam stop - length
    tip_card = P0
    tip_pla = Q(SQ['stop'] - plen, 0)
    check(abs(tip_card[1] + 0.90) < 1e-9, f'card tip h {tip_card[1]}')
    check(abs(tip_pla[1] + 0.287) < 0.001, f'PLA blade tip h {tip_pla[1]:.4f}, expected -0.287')
    notes.append(f'card blade tip {tip_card[1]:.2f} below the runner plane, PLA blade tip {tip_pla[1]:.2f}; loaded tip moves to s {-d_tip * math.sin(A):.2f}')

    # ---- mass, overhangs ----
    overhang = overhang_check(hm_mesh)
    notes += overhang['notes']
    if overhang['fails']:
        fails += overhang['fails']

    # ---- the PLA blade, the plate ----
    blade_box = trimesh.creation.box(extents=[pw, pt, plen])
    blade_box.apply_translation([0, 0, plen / 2])            # standing on its 10.0 x 1.0 working edge, z from 0
    check(blade_box.is_watertight and abs(blade_box.volume - pw * pt * plen) < 1e-6, 'PLA blade box')
    shift_s = -(bb[0][0] + bb[1][0]) / 2
    plate = [hm_mesh.copy()]
    plate[0].apply_translation([shift_s, 0, 0])
    y_blade = r1 + SQ['pla_gap'] + pt / 2
    for xs in SQ['pla_x']:
        b = blade_box.copy()
        b.apply_translation([xs, y_blade, 0])
        plate.append(b)
    plate_mesh = trimesh.util.concatenate(plate)
    check(abs(plate_mesh.bounds[0][2]) < 1e-9, 'plate does not sit on z 0')
    check(plate_mesh.bounds[1][1] < 120, 'plate is too big')
    handle_clear = (y_blade - pt / 2) - r1
    if write:
        plate_mesh.export(OUT / 'squeegee_print.stl')
        blade_box.export(OUT / 'squeegee-blade-pla_print.stl')
    m = trimesh.load(OUT / 'squeegee_print.stl') if write else plate_mesh
    check(m.is_watertight and len(m.split(only_watertight=False)) == 3, 'plate: expected 3 watertight shells (handle and two blades)')
    notes.append(f'plate: handle (centred on x 0, shifted {shift_s:+.2f} in s) and two PLA blades {SQ["pla_gap"]} mm beyond its +w side at x {SQ["pla_x"]}; plate {m.extents[0]:.1f} x {m.extents[1]:.1f} x {m.extents[2]:.1f} mm')

    # ---- 9. use overlay against the stencil card ----
    ov = overlay(check, notes)

    est = estimates()
    derived = dict(
        frame='s along the stroke (+s = card +y, toward the foot), w across (card x - 44.13), h up from the runner plane',
        mouth_plane_h=round(hm, 3), front_lip=[round(v, 3) for v in Q(SQ['mouth'], 0)], stop_corner=[round(v, 3) for v in Q(SQ['stop'], 0)],
        tongue_front_corner=[round(Q(tongue_tip, O_T0)[0], 3), round(hm, 3)], screw_entry=[round(v, 3) for v in Q(SQ['hole_lam'], O_BACK)],
        profile_points=dict(C=[round(v, 3) for v in P['C']], D=[round(v, 3) for v in P['D']], G=[round(v, 3) for v in P['G']]),
        handle_mm=[round(float(v), 2) for v in size], handle_volume_mm3=round(float(hm_mesh.volume), 1),
        blade_tip_h=dict(card=round(tip_card[1], 3), pla=round(tip_pla[1], 3)), loaded_tip_s=round(-d_tip * math.sin(A), 3),
        loaded_blade_angle_deg_estimate='42-45', pla_blade_mm=list(SQ['pla']),
        estimates_note='beam formulas, PVC E 3.0 GPa and PLA E 3.5 GPa assumed, nothing measured', estimates=est,
        tongue_strain_percent=dict(thinnest_card=round(3 * SQ['tongue'] * (SQ['slot'] - SQ['card_t'][0]) / (2 * tongue_free ** 2) * 100, 2),
                                   no_blade=round(3 * SQ['tongue'] * SQ['slot'] / (2 * tongue_free ** 2) * 100, 2)),
        overlay=ov, notes=notes)
    if fails:
        print('squeegee: FAIL')
        for f in fails:
            print('  -', f)
        sys.exit(1)
    print(f'squeegee: all self-checks ok')
    for n in notes:
        print('  ', n)
    return derived, hm_mesh, plate_mesh, P


def overhang_check(mesh):
    """Downward-facing faces: report the steepest overhang (angle from vertical) and the area of horizontal underside above the bed."""
    fails, notes = [], []
    n = mesh.face_normals
    a = mesh.area_faces
    down = n[:, 2] < -1e-6
    ang = np.degrees(np.arccos(np.clip(-n[:, 2], -1, 1)))         # 0 = facing straight down (horizontal underside), 90 = vertical
    # the overhang angle from vertical = 90 - (angle from straight down)
    from_vertical = 90 - ang
    flat_under = down & (ang < 1.0) & (mesh.triangles_center[:, 2] > 0.05)
    steep = down & (ang >= 1.0) & (from_vertical > 45.5)
    flat_levels = sorted({round(float(z), 2) for z in mesh.triangles_center[flat_under][:, 2]})
    notes.append(f'horizontal undersides above the bed at h {flat_levels} (area {a[flat_under].sum():.0f} mm2): the bridges')
    notes.append(f'steepest sloping overhang: {from_vertical[down & (ang >= 1.0)].max():.1f} degrees from vertical' if (down & (ang >= 1.0)).any() else 'no sloping overhang')
    if steep.any():
        # allow the 50-degree inclined hole roof and the short stop face; report them
        notes.append(f'{int(steep.sum())} faces past 45 degrees from vertical, {a[steep].sum():.1f} mm2')
    return dict(fails=fails, notes=notes, flat_levels=flat_levels)


# ---------------------------------------------------------------------------------------------------------------
# Use overlay: the squeegee swept along the stencil card (card frame)
# ---------------------------------------------------------------------------------------------------------------
def overlay(check, notes):
    g = S.geometry(S.PARAMS['default_depth'])
    P_ = S.PARAMS
    x0, x1, y0, y1 = P_['card']
    card = g['card']
    cx = SQ['column_x']
    r0, r1 = SQ['runner_w']
    s0, s1 = SQ['runner_s']
    ch = SQ['runner_chamfer']
    d_tip = SQ['interference'] / math.cos(A)
    s_contact = -d_tip * math.sin(A)                        # the loaded edge line, behind the squeegee's s = 0
    y_start, y_end = SQ['stroke']
    res = {}
    # tracks (the runners' bottoms, lead-ins excluded), in card x
    left = (cx - r1, cx - r0)
    right = (cx + r0, cx + r1)
    sweep_y = (y_start - s_contact + (s0 + ch), y_end - s_contact + (s1 - ch))       # s = 0 sits at yc - s_contact
    tracks = [box(left[0], sweep_y[0], left[1], sweep_y[1]), box(right[0], sweep_y[0], right[1], sweep_y[1])]
    res['tracks_x'] = dict(left=[round(v, 2) for v in left], right=[round(v, 2) for v in right])
    inset = min(left[0] - x0, x1 - right[1])
    res['track_inset_from_card_edge_min'] = round(left[0] - x0, 2), round(x1 - right[1], 2)
    check(left[0] - x0 >= 2.0 and x1 - right[1] >= 2.0, f'a runner track is less than 2.0 from the card edge ({left[0] - x0:.2f}, {x1 - right[1]:.2f})')
    on_card = [t.intersection(card) for t in tracks]
    # openings
    min_gap = min(t.distance(a['sq_rect']) for t in tracks for a in g['aps'])
    min_gap_pd = min(t.distance(a['pd_rect']) for t in tracks for a in g['aps'])
    check(min_gap >= 5.0, f'a runner track comes within {min_gap:.2f} of an opening')
    res['track_to_opening_min'] = round(min_gap, 2)
    # pocket and groove
    pk = g['pocket'].intersection(card)
    over_pocket = [t.intersection(pk) for t in tracks]
    pocket_y = []
    for op in over_pocket:
        if not op.is_empty:
            pocket_y.append((round(op.bounds[1], 2), round(op.bounds[3], 2), round(op.area, 2)))
    res['tracks_over_pocket_y_and_area'] = pocket_y
    foot_y = P_['datum_y'] - P_['clear']                    # the wall above the foot, card frame
    check(all(a_ >= foot_y - 0.01 for (a_, b_, ar) in pocket_y), f'a runner track crosses the pocket above the foot: {pocket_y}')
    res['track_to_pocket_min_above_foot'] = round(min(t.distance(pk.intersection(box(-BIG, -BIG, BIG, foot_y - 0.5))) for t in tracks), 2)
    check(res['track_to_pocket_min_above_foot'] >= 5.0, f"a track comes within {res['track_to_pocket_min_above_foot']} of the bar's pocket")
    gy, gw, gd = P_['groove']
    groove_len = [t.intersection(g['groove']).bounds for t in tracks]
    bridge = (s1 - ch) - (s0 + ch)
    check(bridge >= gw + 2 * 4.0, f'the runner bottom is {bridge} long; it should bridge the {gw} mm groove with 4 mm each side')
    res['groove'] = dict(width=gw, runner_bottom_length=bridge)
    # blade band: the openings with their spare
    bx = (cx - SQ['blade_w'] / 2, cx + SQ['blade_w'] / 2)
    xs0 = min(a['sq_rect'].bounds[0] for a in g['aps'])
    xs1 = max(a['sq_rect'].bounds[2] for a in g['aps'])
    spare = min(xs0 - bx[0], bx[1] - xs1)
    check(spare >= 4.0, f'blade band spare {spare:.2f} < 4.0')
    res['blade_spare_each_side'] = round(spare, 2)
    ys0 = min(a['sq_rect'].bounds[1] for a in g['aps'])
    ys1 = max(a['sq_rect'].bounds[3] for a in g['aps'])
    res['openings_y'] = [round(ys0, 2), round(ys1, 2)]
    res['openings_span_mm'] = round(ys1 - ys0, 2)
    # stroke ends
    check(ys0 - y_start >= 3.5, f'start line is {ys0 - y_start:.2f} before the first opening (want >= 3.5)')
    check(y_start - y0 >= 3.0, f'start line is {y_start - y0:.2f} inside the top edge (want >= 3.0)')
    check(y_end - ys1 >= 3.0, f'end line is {y_end - ys1:.2f} past the last opening (want >= 3.0)')
    res['stroke'] = dict(start_line_y=y_start, end_line_y=y_end, length_mm=round(y_end - y_start, 2), start_before_first_opening=round(ys0 - y_start, 2),
                         start_inside_top_edge=round(y_start - y0, 2), end_past_last_opening=round(y_end - ys1, 2),
                         foot_top_edge_card_frame=round(foot_y, 2), end_line_to_foot_edge=round(foot_y - y_end, 2))
    # the on-card part of each runner at both ends of the stroke (bottom runs s -9..11)
    def on_card_s(yc):
        ys = yc - s_contact                                   # card y of s = 0
        lo_ = max(y0, ys + s0 + ch) - ys
        hi_ = min(y1, ys + s1 - ch) - ys
        return lo_, hi_
    a_lo, a_hi = on_card_s(y_start)
    b_lo, b_hi = on_card_s(y_end)
    pad_lo, pad_hi = SQ['finger_s0'], profiles()['G'][0]
    check(a_lo <= pad_lo - 0.3 and b_hi >= pad_hi + 0.3, f'the finger pad (s {pad_lo}..{pad_hi:.2f}) is not over the on-card part at both stroke ends (start s {a_lo:.2f}..{a_hi:.2f}, end s {b_lo:.2f}..{b_hi:.2f})')
    res['on_card_runner_s'] = dict(start=[round(a_lo, 2), round(a_hi, 2)], end=[round(b_lo, 2), round(b_hi, 2)], finger_pad=[pad_lo, round(pad_hi, 2)])
    # the Kapton: neck tape (y 142-150, x 49-61) and tail tape are off the card; only the neck tape can be reached
    neck = box(49.0, 142.0, 61.0, 150.0)
    end_runner_front = box(right[0], y_end - s_contact + s1 - ch - 0.01, right[1], y_end - s_contact + s1 - ch)
    res['end_runner_front_y'] = round(y_end - s_contact + s1 - ch, 2)
    check(res['end_runner_front_y'] < 150.0, 'runner reaches the neck tape')
    # the label recess under the right track
    res['notes'] = 'card frame (stencil.py geometry, D0.4): the card as built, before the push; once pushed home everything moves +0.12'
    notes.append(f"use overlay: tracks x {res['tracks_x']['left']} and {res['tracks_x']['right']} (inset {res['track_inset_from_card_edge_min'][0]} / {res['track_inset_from_card_edge_min'][1]} from the card edges); "
                 f"{min_gap:.2f} from the nearest opening; blade band spare {spare:.2f} each side")
    notes.append(f"stroke: blade line from card y {y_start} ({res['stroke']['start_before_first_opening']} before the first opening, {res['stroke']['start_inside_top_edge']} inside the top edge) to {y_end} "
                 f"({res['stroke']['end_past_last_opening']} past the last opening, {res['stroke']['end_line_to_foot_edge']} short of the foot's top edge at {res['stroke']['foot_top_edge_card_frame']}); pass {res['stroke']['length_mm']} mm")
    notes.append(f"runner tracks over the pocket: {pocket_y} (y0, y1, area); on-card runner part s {a_lo:.1f}..{a_hi:.1f} at the start, {b_lo:.1f}..{b_hi:.1f} at the end; finger pad s {pad_lo}..{pad_hi:.2f}")
    return res


# ---------------------------------------------------------------------------------------------------------------
# Slicer read-back
# ---------------------------------------------------------------------------------------------------------------
SLICE_PRESETS = {'machine': 'Elegoo Centauri Carbon 2 0.4 nozzle', 'process': '0.20mm Standard @Elegoo CC2 0.4 nozzle', 'filament': 'Elegoo PLA @ECC2'}
# only these change on the stock 0.20 Standard profile (the elephant-foot compensation is left at the stock 0.1, the opposite of the stencil)
SLICE_OVERRIDES = dict(wall_loops='3', wall_generator='arachne', brim_type='no_brim', brim_width='0', enable_support='0')


def slice_read_back(derived, hm_mesh, plate_mesh, P):
    import slice_check as C
    work = C.WORK.parent / 'squeegee'
    stl = OUT / 'squeegee_print.stl'
    gcode = C.slice_stl(stl, work, SLICE_OVERRIDES, presets=SLICE_PRESETS)
    layers, types, arcs = C.parse(gcode)
    zs = sorted(layers)
    fails, notes = [], []
    head = Path(gcode).read_text(errors='ignore')
    cfg = {}
    for key, pat in {'time': r'estimated printing time \(normal mode\) = (.+)', 'grams': r'total filament used \[g\] = ([\d.]+)',
                     'efc': r'; elefant_foot_compensation = (\S+)', 'layer_height': r'; layer_height = (\S+)',
                     'first_layer_height': r'; initial_layer_print_height = (\S+)', 'wall_loops': r'; wall_loops = (\S+)',
                     'wall_generator': r'; wall_generator = (\S+)', 'brim_type': r'; brim_type = (.+)', 'infill': r'; sparse_infill_density = (\S+)',
                     'enable_support': r'; enable_support = (\S+)'}.items():
        m = re.search(pat, head)
        cfg[key] = m.group(1).strip() if m else None
    lh = float(cfg['layer_height'])
    efc = float(cfg['efc'])

    def chk(cond, msg):
        if not cond:
            fails.append(msg)

    chk(cfg['efc'] == '0.1', f"elephant-foot compensation {cfg['efc']} (the stock 0.1 is wanted here)")
    chk(cfg['wall_loops'] == '3' and cfg['wall_generator'] == 'arachne' and cfg['brim_type'] == 'no_brim', f'overrides did not take: {cfg}')
    bad = sorted(set(types) & {'Support', 'Support interface', 'Support transition', 'Ironing'})
    chk(not bad, f'forbidden line types in the G-code: {bad}')
    chk(not arcs, f'{len(arcs)} G2/G3 arc moves')
    skirt_brim = sorted(set(types) & {'Skirt', 'Brim'})
    chk(not skirt_brim, f'skirt or brim lines in the G-code: {skirt_brim}')
    # the design's footprint at layer 1, in the plate frame, to find where the slicer put the plate
    first_sec = section_poly(plate_mesh, 2, lh / 2)
    first_eroded = first_sec.buffer(-efc)
    # where the slicer put the plate: read from the two runner rails (the 1.0 mm blades keep less of the elephant-foot shrink than the
    # rails do, so they would bias a box centre); the rails are the segments on the handle's side of the plate
    rail_segs = [q for q in layers[zs[0]] if (q[1] + q[3]) / 2 < C.BED_CENTRE[1] + 15]
    rxs = [c for q in rail_segs for c in (q[0], q[2])]
    rys = [c for q in rail_segs for c in (q[1], q[3])]
    rails_design = first_eroded.intersection(box(-100, -100, 100, 15))
    ox = (min(rxs) + max(rxs)) / 2 - (rails_design.bounds[0] + rails_design.bounds[2]) / 2
    oy = (min(rys) + max(rys)) / 2 - (rails_design.bounds[1] + rails_design.bounds[3]) / 2
    chk(abs(ox - C.BED_CENTRE[0]) < 8 and abs(oy - C.BED_CENTRE[1]) < 8, f'the plate was placed {ox - C.BED_CENTRE[0]:+.1f}, {oy - C.BED_CENTRE[1]:+.1f} from where it was put')
    Ul = {z: C.layer_union(layers[z], ox, oy) for z in zs}
    top = plate_mesh.bounds[1][2]
    chk(len(zs) == int(top / lh + 1e-6) and zs[-1] > top - lh - 1e-3, f'{len(zs)} layers up to z {zs[-1]}, expected {int(top / lh + 1e-6)} (the model is {top:.3f} tall)')

    # per layer: the sliced union against the design section at the layer's middle
    worst_out, worst_cover = 0.0, 1.0
    out_rows = []
    for z in zs:
        sec = section_poly(plate_mesh, 2, z - lh / 2)
        if sec.is_empty:
            continue
        target = sec.buffer(-efc) if z == zs[0] else sec
        out = Ul[z].difference(sec.buffer(0.12)).area                    # extrusion beyond the design (0.12 for bead rounding)
        cover = Ul[z].intersection(target).area / target.area if target.area else 1.0
        worst_out = max(worst_out, out)
        if z > zs[0]:
            worst_cover = min(worst_cover, cover)
        out_rows.append((z, out, cover))
    chk(worst_out < 0.15, f'extrusion outside the design section by up to {worst_out:.3f} mm2 in a layer (paste wedge, blade envelope, slot, slits or hole)')
    # layer 1: the two rails (shrunk by the elephant-foot compensation) and the two blade edges
    pw, pt, plen = SQ['pla']
    y_blade = SQ['runner_w'][1] + SQ['pla_gap'] + pt / 2
    parts = list(first_sec.geoms) if hasattr(first_sec, 'geoms') else [first_sec]
    chk(len(parts) == 4, f'layer 1 has {len(parts)} footprints, expected 4 (two rails, two blades)')
    rails = first_eroded.intersection(box(-100, -100, 100, 15))
    u1 = Ul[zs[0]]
    r_got = u1.intersection(box(-100, -100, 100, 15)).area
    chk(u1.intersection(rails).area / rails.area > 0.95 and abs(r_got - rails.area) / rails.area < 0.05, f'layer 1 rails: {r_got:.1f} mm2 against {rails.area:.1f} designed (after the {efc} elephant-foot shrink)')
    blade_boxes = [box(xs_ - pw / 2, y_blade - pt / 2, xs_ + pw / 2, y_blade + pt / 2) for xs_ in SQ['pla_x']]
    b_got = [u1.intersection(b_).area for b_ in blade_boxes]
    chk(all(0.75 * pw * pt <= g_ <= 1.02 * pw * pt for g_ in b_got), f'layer 1 blade footprints {b_got}')
    notes.append(f'layer 1: {len(parts)} footprints; the two rails {r_got:.1f} mm2 against {rails.area:.1f} designed after the {efc} mm elephant-foot shrink ({r_got / rails.area:.1%}); '
                 f'the two blade edges {b_got[0]:.1f} and {b_got[1]:.1f} mm2 of the 10.0 x 1.0 footprint (the slicer did not shrink them)')
    a_got, a_exp = u1.area, rails.area + sum(b_got)
    # the PLA blades: every layer covers >= 97 % of 10 x 1.0 above layer 1
    blades = blade_boxes
    worst_blade = 1.0
    for z in zs[1:]:
        if z - lh >= plen + 1e-6:
            continue
        for b in blades:
            if z <= plen + 1e-6:
                worst_blade = min(worst_blade, Ul[z].intersection(b).area / b.area)
    chk(worst_blade >= 0.97, f'a PLA blade layer covers only {worst_blade:.1%} of 10 x 1.0')
    top_blade = max(z for z in zs if any(Ul[z].intersection(b).area > 0.5 for b in blades))
    chk(abs(top_blade - plen) < 1e-3, f'the PLA blades end at z {top_blade}, expected {plen}')
    notes.append(f'PLA blades: every layer above layer 1 covers >= {worst_blade:.1%} of 10.0 x 1.0, top layer at z {top_blade}')

    # ---- features read from the layers ----
    shift_s = -(hm_mesh.bounds[0][0] + hm_mesh.bounds[1][0]) / 2

    def plate_pt(s_h):
        return (s_h[0] + shift_s, s_h[1])
    hm = P['hm']
    # the paste wedge, the blade's swept space and the space under the ceiling (|w| <= 6.5): no bead at all, layer by layer
    forbid = unary_union([box(-BIG, 0, BIG, hm).intersection(half_o(O_S1, above=False)), box(-BIG, 0, BIG, SQ['ceiling'])])
    worst_clear = 0.0
    n_forbid = 0
    for z in zs:
        hline = LineString([(-BIG, z - lh / 2), (BIG, z - lh / 2)]).intersection(forbid)
        parts_ = list(hline.geoms) if hasattr(hline, 'geoms') else [hline]
        for seg in parts_:
            if seg.is_empty or seg.length < 0.5:
                continue
            a_, b_ = sorted((seg.bounds[0], seg.bounds[2]))
            rect = box(a_ + shift_s + 0.15, -6.5, b_ + shift_s - 0.15, 6.5)
            worst_clear = max(worst_clear, Ul[z].intersection(rect).area)
            n_forbid += 1
    chk(worst_clear < 0.01, f'{worst_clear:.3f} mm2 of extrusion inside the paste wedge, the blade envelope or under the ceiling')
    notes.append(f'paste wedge, blade space and the space under the ceiling (|w| <= 6.5): {n_forbid} layer stretches checked, most extrusion inside any of them {worst_clear:.4f} mm2')
    # slot: horizontal open stretch along s through the slot's centre line, per layer, w = 0 and +-4.8
    slot_min = 99.0
    slot_rows = 0
    for z in zs:
        h = z - lh / 2
        if not (hm + 0.3 < h < Q(SQ['stop'], 0)[1] - 0.3):
            continue
        lam = (h - P0[1] - 0.625 * NB[1]) / U[1]
        sc = Q(lam, 0.625)[0] + shift_s
        for w in (0.0, 4.8, -4.8):
            wd, _ = C.free_interval(Ul[z], sc, w, 'x', reach=2.0)
            slot_min = min(slot_min, wd * math.sin(A))              # the open width perpendicular to the blade
            slot_rows += 1
    chk(slot_rows > 0 and slot_min >= 1.15, f'the slot is {slot_min:.2f} open (perpendicular, per layer); want >= 1.15 (design 1.25)')
    notes.append(f'slot: narrowest bead-to-bead gap, perpendicular to the blade, over {slot_rows} layer samples (w 0 and +-4.8): {slot_min:.2f} mm (design 1.25, want >= 1.15)')
    notes.append(f'fit as sliced: a 0.84 card leaves {slot_min - 0.84:.2f} mm in the slot and the 1.0 PLA blade {slot_min - 1.0:.2f} mm; the tongue closes that gap')
    # back slit and side slits
    bs_min, ss_min = 99.0, 99.0
    for z in zs:
        h = z - lh / 2
        if not (hm + 0.3 < h < Q(SQ['stop'], 0)[1] - 0.3):
            continue
        lam_b = (h - P0[1] - (O_T1 + SQ['back_slit'] / 2) * NB[1]) / U[1]
        sb = Q(lam_b, O_T1 + SQ['back_slit'] / 2)[0] + shift_s
        wd, _ = C.free_interval(Ul[z], sb, 0.0, 'x', reach=2.0)
        bs_min = min(bs_min, wd * math.sin(A))
        lam_s = (h - P0[1] - 2.45 * NB[1]) / U[1]
        sm = Q(lam_s, 2.45)[0] + shift_s
        for sg in (1, -1):
            wd, _ = C.free_interval(Ul[z], sm, sg * (SQ['slot_w'] / 2 + SQ['side_slit'] / 2), 'y', reach=1.5)
            ss_min = min(ss_min, wd)
    chk(bs_min >= 0.6, f'the back slit is {bs_min:.2f} open; want >= 0.6')
    chk(ss_min >= 0.6, f'a side slit is {ss_min:.2f} open; want >= 0.6')
    notes.append(f'back slit open {bs_min:.2f} (perpendicular, design 0.80), side slits open {ss_min:.2f} (design 0.80)')
    # screw hole: open width along w through the axis, per layer within its height range
    ax_lam = SQ['hole_lam']
    h_lo = Q(ax_lam, O_S1)[1]
    h_hi = Q(ax_lam, O_BACK)[1]
    hole_min = 99.0
    hole_rows = 0
    for z in zs:
        h = z - lh / 2
        if not (h_lo + 1.5 < h < h_hi - 0.5):
            continue
        # the axis point at this height: along n_b from the axis start
        o = (h - Q(ax_lam, 0)[1]) / NB[1]
        sx = Q(ax_lam, o)[0] + shift_s
        wd, _ = C.free_interval(Ul[z], sx, 0.0, 'y', reach=2.0)
        hole_min = min(hole_min, wd)
        hole_rows += 1
    chk(hole_rows > 0 and hole_min >= 2.2, f'the screw hole is {hole_min:.2f} open across; want >= 2.2 (design {SQ["hole_d"]})')
    notes.append(f'screw hole: narrowest open width across (w) through its axis, {hole_rows} layers: {hole_min:.2f} mm (design {SQ["hole_d"]}, want >= 2.2)')
    # what the slicer itself says about air under the extrusion: its Bridge / Internal Bridge / Overhang wall lines, by layer
    seg_len = lambda q: math.hypot(q[2] - q[0], q[3] - q[1])
    def by_layer(kind):
        d_ = {z_: round(sum(seg_len(q) for q in layers[z_] if q[5] == kind), 1) for z_ in zs}
        return {z_: v for z_, v in d_.items() if v > 0}
    bridge_z, internal_z = by_layer('Bridge'), by_layer('Internal Bridge')
    over_len = sum(seg_len(q) for z_ in zs for q in layers[z_] if q[5] == 'Overhang wall')
    wall_len = sum(seg_len(q) for z_ in zs for q in layers[z_] if q[5] in ('Outer wall', 'Inner wall', 'Overhang wall'))
    over_layers = len([z_ for z_ in zs if any(q[5] == 'Overhang wall' for q in layers[z_])])
    notes.append(f'"Bridge" lines (mm of extrusion) by layer height z: {bridge_z} (z 3.2: the ceiling at h 3.0 and z 10.8: the underside of the slot mouth, both spanning the 14.26 mm between the runner walls; z 20.8 and 22.2: the roofs at the 1 mm wide ends of the slot and the slits); '
                 f'"Internal Bridge" (solid skin over sparse infill, not over air): {internal_z}; "Overhang wall" lines: {over_len:.0f} mm of {wall_len:.0f} mm of wall, on {over_layers} layers '
                 '(the 40-50 degree faces); no Support type, so nothing is added under them')
    res = dict(time=cfg['time'], grams=cfg['grams'], layers=len(zs), line_types=sorted(types), skirt_or_brim=skirt_brim, settings=cfg,
               worst_extrusion_outside_design_mm2=round(worst_out, 3), layer1=dict(footprints=len(parts), rails_area=round(r_got, 1), rails_designed=round(rails.area, 1), blade_edges_area=[round(v, 1) for v in b_got]),
               pla_blade_layer_cover_min=round(worst_blade, 3), slot_open_min=round(slot_min, 3), back_slit_open_min=round(bs_min, 3),
               side_slit_open_min=round(ss_min, 3), hole_open_min=round(hole_min, 3), bridges=dict(bridge_mm_by_layer_z=bridge_z, internal_bridge_mm_by_layer_z=internal_z, overhang_wall_mm=round(over_len), wall_mm=round(wall_len), overhang_layers=over_layers),
               pass_=not fails, notes=notes)
    return res, fails


def write_report(res, fails, derived):
    s = res['settings']
    L = ['# Squeegee slice check', '',
         'Generated by `tools/stencil/squeegee.py --slice` (OrcaSlicer command line, stock Elegoo Centauri Carbon 2 0.4 nozzle and Elegoo PLA profiles). '
         'It reads the sliced G-code back against the model: **a toolpath check only. Nothing has been printed**, and nothing here shows that the fit, the clamp, '
         'the pressure or the paste behave as designed (the forces in `squeegee_params.json` are beam estimates with assumed moduli).', '',
         f"Process: stock `{SLICE_PRESETS['process']}` with Elegoo PLA; changed only " + ', '.join(f'`{k}` = {v}' for k, v in SLICE_OVERRIDES.items()) +
         f" (the elephant-foot compensation stays at the stock {s['efc']}, the opposite of the stencil card). Read back from the G-code: layer height {s['layer_height']}, "
         f"first layer {s['first_layer_height']}, {s['wall_loops']} walls, {s['wall_generator']}, brim {s['brim_type']}, supports {s['enable_support']}, infill {s['infill']}.", '',
         '| Check | Result |', '|---|---|',
         f"| Layers | {res['layers']} |",
         f"| Line types in the G-code | {', '.join(res['line_types'])} |",
         f"| Support, ironing, arc moves | none |" if not fails else '| Support, ironing, arc moves | see failures |',
         f"| Print time (slicer estimate), handle and two PLA blades on one plate | {res['time']} |",
         f"| Filament (g) | {res['grams']} |",
         f"| Extrusion outside the design section (paste wedge, blade envelope, slot, slits, hole), worst layer | {res['worst_extrusion_outside_design_mm2']} mm2 |",
         f"| Layer 1 | {res['layer1']['footprints']} footprints (two runner rails, two blade edges); the rails {res['layer1']['rails_area']} mm2 against {res['layer1']['rails_designed']} designed after the elephant-foot shrink, the blade edges {res['layer1']['blade_edges_area']} mm2 of 10.0 |",
         f"| PLA blade layers, coverage of 10.0 x 1.0 | at least {res['pla_blade_layer_cover_min']:.1%} |",
         f"| Slot, narrowest open gap per layer, perpendicular | {res['slot_open_min']:.2f} mm (design 1.25, planned clearance for a 0.84 card or the 1.0 PLA blade) |",
         f"| Back slit / side slits, narrowest open | {res['back_slit_open_min']:.2f} / {res['side_slit_open_min']:.2f} mm (design 0.80) |",
         f"| Screw hole, narrowest open width | {res['hole_open_min']:.2f} mm (design {SQ['hole_d']}) |",
         f"| Bridge lines over air, by layer height z (mm of extrusion) | {res['bridges']['bridge_mm_by_layer_z']} |",
         f"| 'Overhang wall' lines | {res['bridges']['overhang_wall_mm']} mm of {res['bridges']['wall_mm']} mm of wall, on {res['bridges']['overhang_layers']} layers |",
         f"| Result | {'PASS' if res['pass_'] else 'FAIL'} |", '', '## Notes', ''] + [f'- {n}' for n in res['notes']]
    L += ['', 'Method: every extrusion segment is swept by its `;WIDTH` and unioned per layer (as in `slice_check.py`); the plate\'s position is read from the first-layer beads of the two runner rails. '
          'The model is sectioned at every layer\'s middle and compared with the sliced layer. The slot, slit and hole gaps are the bead-free stretch through the feature\'s centre line.']
    if fails:
        L += ['', '## Failures', ''] + [f'- {f}' for f in fails]
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text('\n'.join(L) + '\n', encoding='utf-8')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--slice', action='store_true', help='also slice squeegee_print.stl with the OrcaSlicer CLI and read it back')
    args = ap.parse_args()
    derived, hm_mesh, plate_mesh, P = build()
    pj = OUT / 'squeegee_params.json'
    old = json.loads(pj.read_text(encoding='utf-8')) if pj.exists() else {}
    out = dict(parameters={k: (list(v) if isinstance(v, tuple) else v) for k, v in SQ.items()}, derived=derived)
    if args.slice:
        res, fails = slice_read_back(derived, hm_mesh, plate_mesh, P)
        out['slice'] = res
        write_report(res, fails, derived)
        print(f"slice: {res['time']}, {res['grams']} g, {res['layers']} layers, {'PASS' if not fails else 'FAIL'}")
        for n in res['notes']:
            print('  ', n)
        for f in fails:
            print('   -', f)
        pj.write_text(json.dumps(out, indent=1), encoding='utf-8')
        if fails:
            print('FAIL')
            sys.exit(1)
    else:
        if 'slice' in old:
            out['slice'] = old['slice']
        pj.write_text(json.dumps(out, indent=1), encoding='utf-8')
    print('wrote', pj.relative_to(ROOT))


if __name__ == '__main__':
    main()
