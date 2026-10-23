"""Build the 3D-printable paste stencil for the light strip's 24 LED pads (CadQuery).

Run in the CadQuery venv (it has cadquery, shapely, trimesh), after extract_paste.py:
    <venv>\\Scripts\\python.exe -X utf8 -I tools/stencil/stencil.py            # all three pocket depths + the coupon
    <venv>\\Scripts\\python.exe -X utf8 -I tools/stencil/stencil.py --depth 0.4

What it makes: a flat PLA card (31 x 107 mm, 0.6 mm thick by default) with a pocket on its underside shaped like
the strip. The pocket's ceiling is a 0.20 mm membrane that rests on the strip's top face; the 24 LED apertures go
through the membrane. The card prints squeegee face down, so there are no overhangs and no supports.
Aperture placement. Pushing the card onto the two datums moves it +clear (0.12) in x and in y, so every aperture is cut at
the pad centre minus (clear, clear) in KiCad x/y; it sits on the pad centre once the card is home.
The design is in docs/ASSEMBLY.md ("Option: 3D-printed paste stencil") and production/stencil/README.md.

Frames. Everything is first built in the USE frame: KiCad x, y (component side up, seen from above), z up from the
FR4 carrier's top face (z = 0). CadQuery's Y is -y of KiCad's, because KiCad's y points down. The PRINT STL is that
solid rotated 180 degrees about X (a rotation, never a mirror), with its squeegee face on z = 0 and the card centred
on the XY origin. Seen from above in a slicer the layout therefore looks flipped top to bottom compared with the use
view. That is correct. to_print() below is the one place that maps use-frame points to print-frame points; the
slice check and the renders import it instead of deriving it a second time.

Self-checks (exit 1 on any failure) are at the end of build(); the numbers go to production/stencil/stencil_params.json.
"""
import argparse
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'production' / 'stencil'
INPUT = OUT / 'stencil_input.json'
LED_FP = 'LED_SideView_XINGLIGHT_XL-4008'

# ---- parameters (mm). CLI: --depth. Everything else is edited here and the three scripts rerun. ----
PARAMS = dict(
    layer=0.10,                 # print layer height (and first layer); the membrane is two of them
    membrane=0.20,              # stencil thickness at the apertures
    depths=(0.3, 0.4, 0.5),     # pocket depth D: pick from the strip height measured with the liner on
    default_depth=0.4,
    liner=0.09,                 # 3M 9077 release liner, from 3M's data sheet (3.6 mil; 260 C short term); it stays on
    stack_nominal=0.385,        # flex 0.11 + PI stiffener 0.225 + 9077 adhesive 0.05, without the liner (JLC holds the stiffener to +-0.1)
    clear=0.12,                 # pocket clearance round the strip outline
    tip_extra=0.30,             # extra pocket length past the strip's tip
    led_ap=(0.80, 1.10),        # squeegee-side aperture: (across the bar, along the bar)
    release_step=0.05,          # the pad-side half is this much bigger per side
    card=(31.0, 62.0, 33.0, 140.0),   # x0, x1, y0, y1 in KiCad coordinates
    corner_r=3.0,
    chamfer=3.0,                # which-way-up mark at the top-left corner of the use view
    groove=(56.0875, 6.0, 0.20),      # centre y, width, depth: relief for the Kapton across the hinge
    label_depth=0.10,
    datum_x=43.0,               # the strip's long straight outer edge (card pushes toward +x onto it)
    datum_y=135.5,              # the foot's top edge (card pushes toward +y onto it)
    steel_thickness=0.12,       # a normal steel stencil, for the paste-volume comparison only
)


def pick_depth(reading, P=PARAMS):
    """The pocket depth for a bar reading (liner on): the largest multiple of 0.1 mm at least 0.02 mm below the reading."""
    return round(math.floor((reading - 0.02) / 0.1 + 1e-9) * 0.1, 1)


def check_pick_depth(P=PARAMS):
    """Self-checks of the depth rule (docs/ASSEMBLY.md and production/stencil/README.md quote these bands). Exit 1 on failure."""
    bad = []
    nominal = round(P['stack_nominal'] + P['liner'], 3)
    if pick_depth(nominal) != P['default_depth']:
        bad.append(f"a nominal bar ({nominal}) picks D{pick_depth(nominal)}, not the default D{P['default_depth']}")
    for reading, want in ((0.32, 0.3), (0.41, 0.3), (0.42, 0.4), (0.51, 0.4), (0.52, 0.5), (0.61, 0.5)):
        if pick_depth(reading) != want:
            bad.append(f'reading {reading} picks D{pick_depth(reading)}, expected D{want}')
    # JLC's +-0.1 on the stiffener: every plausible reading must land on one of the three files
    for reading in (nominal - 0.1, nominal, nominal + 0.1):
        if pick_depth(reading) not in P['depths']:
            bad.append(f'a plausible reading {reading:.3f} picks D{pick_depth(reading)}, which is not one of {P["depths"]}')
    if bad:
        print('pick_depth: FAIL')
        for b in bad:
            print('  -', b)
        sys.exit(1)
    print(f'pick_depth: ok (nominal bar with the liner {nominal} -> D{pick_depth(nominal)}; plausible {nominal - 0.1:.3f}-{nominal + 0.1:.3f} -> '
          f'D{pick_depth(nominal - 0.1)}-D{pick_depth(nominal + 0.1)})')
    return nominal


def load_input():
    return json.loads(INPUT.read_text(encoding='utf-8'))


# ---------------------------------------------------------------------------------------------------------------
# 2-D geometry in the KiCad frame (shapely). Shared with slice_check.py and render.py.
# ---------------------------------------------------------------------------------------------------------------
def geometry(D, inp=None, P=PARAMS):
    from shapely.geometry import Polygon, box
    from shapely.ops import unary_union
    inp = inp or load_input()
    x0, x1, y0, y1 = P['card']
    card = box(x0, y0, x1, y1).buffer(-P['corner_r'], quad_segs=16).buffer(P['corner_r'], quad_segs=16)
    c = P['chamfer']
    card = card.difference(Polygon([(x0 - 1, y0 - 1), (x0 + c, y0 - 1), (x0 + c, y0), (x0, y0 + c), (x0 - 1, y0 + c)]))
    outline = Polygon(inp['outline'])
    tipx = 44.15
    tip_y = inp['outline_bbox'][1]                       # 39.10, the rounded tip
    hw = 1.15 + P['clear']
    tip_rect = box(tipx - hw, tip_y - P['clear'] - P['tip_extra'], tipx + hw, tip_y + 1.15)
    pocket = unary_union([outline.buffer(P['clear'], quad_segs=16), tip_rect])
    pocket = pocket.intersection(box(x0 - 1, y0 - 1, x1 + 1, y1 + 1))      # runs out of the card's bottom edge
    assert pocket.geom_type == 'Polygon' and not list(pocket.interiors)
    gy, gw, gd = P['groove']
    groove = box(x0 - 1, gy - gw / 2, x1 + 1, gy + gw / 2)
    aps = []
    for p in inp['paste_pads']:
        if p['footprint'] != LED_FP:
            continue
        bx0, by0, bx1, by1 = p['paste_bbox']
        r = p['rr'] * min(bx1 - bx0, by1 - by0)
        pad = box(bx0 + r, by0 + r, bx1 - r, by1 - r).buffer(r, quad_segs=8)
        cx, cy = (bx0 + bx1) / 2, (by0 + by1) / 2
        sq = (P['led_ap'][0], P['led_ap'][1])
        pd = (sq[0] + 2 * P['release_step'], sq[1] + 2 * P['release_step'])
        # (cx, cy) is the PAD centre; (ax, ay) is where the aperture is cut in the card. The card is pushed onto the
        # datums, which moves it +clear in x and +clear in y (KiCad frame), so the aperture is cut that much the other
        # way and lands on the pad centre once the card is home.
        ax_, ay_ = cx - P['clear'], cy - P['clear']
        aps.append(dict(ref=p['ref'], pad=p['pad'], cx=cx, cy=cy, ax=ax_, ay=ay_, pad_poly=pad, pad_size=(bx1 - bx0, by1 - by0),
                        sq=sq, pd=pd,
                        sq_rect=box(ax_ - sq[0] / 2, ay_ - sq[1] / 2, ax_ + sq[0] / 2, ay_ + sq[1] / 2),
                        pd_rect=box(ax_ - pd[0] / 2, ay_ - pd[1] / 2, ax_ + pd[0] / 2, ay_ + pd[1] / 2)))
    aps.sort(key=lambda a: (a['cy'], a['ref']))
    return dict(card=card, pocket=pocket, groove=groove, outline=outline, aps=aps, D=D,
                H=round(D + P['membrane'], 3))


def to_print(x, y, z=None, H=None, P=PARAMS):
    """Use-frame (KiCad x, y; z up from the FR4) to print-frame (centred on the card, z up from the squeegee face)."""
    x0, x1, y0, y1 = P['card']
    px, py = x - (x0 + x1) / 2, y - (y0 + y1) / 2
    return (px, py) if z is None else (px, py, H - z)


# ---------------------------------------------------------------------------------------------------------------
# CadQuery solid
# ---------------------------------------------------------------------------------------------------------------
def prism(poly, z0, z1):
    import cadquery as cq
    assert not list(poly.interiors)
    poly = poly.simplify(0.0005)                      # drops duplicate and collinear points that OCC rejects
    pts = [(x, -y) for x, y in list(poly.exterior.coords)[:-1]]
    return cq.Workplane('XY').workplane(offset=z0).polyline(pts).close().extrude(z1 - z0)


def rect_prism(cx, cy, sx, sy, z0, z1):
    import cadquery as cq
    return cq.Workplane('XY').workplane(offset=z0).center(cx, -cy).rect(sx, sy).extrude(z1 - z0)


def label_solids(D, P=PARAMS):
    """Underside label, cut 0.1 deep from the FR4 face. Text is laid on a plane facing -Z so it reads correctly when the
    card is turned over top to bottom (its 'up' is +y of KiCad)."""
    import cadquery as cq
    plane = lambda x, y: cq.Plane(origin=(x, -y, 0), xDir=(1, 0, 0), normal=(0, 0, -1))
    out = []
    for txt, (x, y) in ((f'D{D}', (51.0, 83.0)), ('LS-A', (51.0, 90.0))):
        t = cq.Workplane(plane(x, y)).text(txt, 4.0, -P['label_depth'], combine=False, halign='left', valign='center')
        out.append((txt, t))
    return out


def build_solid(g, P=PARAMS):
    D, H = g['D'], g['H']
    m = P['membrane']
    solid = prism(g['card'], 0, H)
    solid = solid.cut(prism(g['pocket'], 0, D))
    solid = solid.cut(prism(g['groove'].intersection(g['card'].buffer(0.5)), 0, P['groove'][2]))
    for a in g['aps']:
        solid = solid.cut(rect_prism(a['ax'], a['ay'], a['pd'][0], a['pd'][1], D - 0.01, D + P['layer']))   # pad half
        solid = solid.cut(rect_prism(a['ax'], a['ay'], a['sq'][0], a['sq'][1], D + P['layer'] - 0.01, H + 0.01))   # squeegee half
    labels = []
    for txt, t in label_solids(D, P):
        bb = t.val().BoundingBox()
        labels.append((txt, (bb.xmin, -bb.ymax, bb.xmax, -bb.ymin, bb.zmin, bb.zmax)))
        solid = solid.cut(t)
    return solid, labels


# ---------------------------------------------------------------------------------------------------------------
def build(D, P=PARAMS, write=True):
    import cadquery as cq
    import numpy as np
    import trimesh
    from shapely.geometry import box
    from shapely.affinity import translate
    inp = load_input()
    g = geometry(D, inp, P)
    H = g['H']
    fails, notes = [], []

    def check(cond, msg):
        if not cond:
            fails.append(msg)

    # --- 2-D checks ---
    check(len(g['aps']) == 24, f"{len(g['aps'])} apertures, expected 24")
    check(abs(H - round(H / 0.1) * 0.1) < 1e-9 and abs(D + P['membrane'] - H) < 1e-9, 'D + 0.2 = H on the 0.10 layer grid')
    check(D >= P['groove'][2] + 0.1 - 1e-9, 'pocket must be deeper than the groove')
    x0, x1, y0, y1 = P['card']
    for a in g['aps']:
        for nm in ('sq_rect', 'pd_rect'):
            # with the card pushed home (+clear in x and y) the opening must lie inside the pad
            check(a['pad_poly'].contains(translate(a[nm], P['clear'], P['clear'])), f"{a['ref']}.{a['pad']} {nm} is not inside the pad once the card is pushed home")
        c = a['pad_poly'].centroid
        check(abs(c.x - (a['ax'] + P['clear'])) < 0.005 and abs(c.y - (a['ay'] + P['clear'])) < 0.005,
              f"{a['ref']}.{a['pad']} aperture centre is not the pad centre minus (clear, clear)")
        check(abs(a['sq_rect'].centroid.x - (c.x - P['clear'])) < 1e-6 and abs(a['sq_rect'].centroid.y - (c.y - P['clear'])) < 1e-6
              and abs(a['pd_rect'].centroid.x - (c.x - P['clear'])) < 1e-6 and abs(a['pd_rect'].centroid.y - (c.y - P['clear'])) < 1e-6,
              f"{a['ref']}.{a['pad']} cut rectangles are not centred on pad - (clear, clear)")
        check(a['cx'] - x0 >= 6 and x1 - a['cx'] >= 6 and a['cy'] - y0 >= 6 and y1 - a['cy'] >= 6,
              f"{a['ref']}.{a['pad']} is less than 6 mm inside the card edges")
        check(g['pocket'].contains(a['pd_rect']), f"{a['ref']}.{a['pad']} aperture is outside the pocket")
    on_card = g['outline'].intersection(box(x0, y0, x1, y1))
    check(on_card.within(g['pocket'].buffer(-0.10)), 'pocket clearance round the strip is under 0.10 somewhere')
    check(g['pocket'].buffer(-1e-6).contains(g['outline'].intersection(box(x0, y0, x1, y1 - 1e-3)).buffer(0.119)),
          'pocket does not surround the strip by 0.12')

    solid, labels = build_solid(g, P)
    s = solid.val()
    check(s.isValid(), 'solid is not valid')
    check(len(solid.solids().vals()) == 1, f"{len(solid.solids().vals())} solids, expected 1")
    bb = s.BoundingBox()
    check(abs(bb.zmin) < 1e-6 and abs(bb.zmax - H) < 1e-6, f'z extent {bb.zmin:.4f}..{bb.zmax:.4f}, expected 0..{H}')
    for txt, (lx0, ly0, lx1, ly1, lz0, lz1) in labels:
        pocket_gap = g['pocket'].distance(box(lx0, ly0, lx1, ly1))
        check(pocket_gap >= 5 and lx1 <= x1 - 2 and lx0 >= x0 + 2 and abs(lz0) < 1e-6 and abs(lz1 - P['label_depth']) < 1e-6,
              f"label {txt}: {pocket_gap:.2f} from the pocket, x {lx0:.1f}..{lx1:.1f}, z {lz0:.2f}..{lz1:.2f}")
        check(not box(lx0, ly0, lx1, ly1).intersects(g['groove']), f'label {txt} touches the hinge groove')
        notes.append(f'label {txt}: x {lx0:.1f}..{lx1:.1f}, y {ly0:.1f}..{ly1:.1f}, {pocket_gap:.1f} mm from the pocket')

    # --- print STL: rotate 180 about X, centre, squeegee face on z = 0 ---
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    pr = solid.rotate((0, 0, 0), (1, 0, 0), 180).translate((-cx, -cy, H))     # rotation, not a mirror: y_print = y_kicad - cy
    name = f'light-strip-stencil_D{D}_print.stl'
    stl = OUT / name
    OUT.mkdir(parents=True, exist_ok=True)
    cq.exporters.export(pr, str(stl), tolerance=0.002, angularTolerance=0.05)
    mesh = trimesh.load(stl)
    check(mesh.is_watertight, 'STL is not watertight')
    check(abs(mesh.bounds[0][2]) < 1e-6 and abs(mesh.bounds[1][2] - H) < 1e-6, f'STL z extent {mesh.bounds[:, 2]}')
    check(abs(mesh.volume - s.Volume()) / s.Volume() < 0.002, 'STL volume differs from the solid')

    # --- membrane thickness at every aperture, from the mesh (vertical rays in the print frame) ---
    tri = mesh.triangles                                   # (m, 3, 3); vertical rays are cast with numpy (no rtree here)
    tmin, tmax = tri[:, :, :2].min(axis=1), tri[:, :, :2].max(axis=1)

    def thickness(pts):
        """Material thickness along z at each (x, y) print-frame point: the sum of the inside intervals of a vertical ray."""
        out = np.zeros(len(pts))
        for i, (px, py) in enumerate(pts):
            near = np.where((tmin[:, 0] <= px) & (tmax[:, 0] >= px) & (tmin[:, 1] <= py) & (tmax[:, 1] >= py))[0]
            zs = []
            for t in tri[near]:
                (ax, ay, az), (bx, by, bz), (cx_, cy_, cz) = t
                det = (by - cy_) * (ax - cx_) + (cx_ - bx) * (ay - cy_)
                if abs(det) < 1e-12:
                    continue                                   # a vertical wall seen edge-on
                l1 = ((by - cy_) * (px - cx_) + (cx_ - bx) * (py - cy_)) / det
                l2 = ((cy_ - ay) * (px - cx_) + (ax - cx_) * (py - cy_)) / det
                l3 = 1 - l1 - l2
                if min(l1, l2, l3) >= -1e-9:
                    zs.append(l1 * az + l2 * bz + l3 * cz)
            zs = sorted(zs)
            zs = [z for k, z in enumerate(zs) if k == 0 or z - zs[k - 1] > 1e-6]      # a hit on a shared diagonal counts once
            assert len(zs) % 2 == 0, f'odd hit count at ({px:.3f}, {py:.3f}): the probe sits on an edge'
            out[i] = sum(zs[k + 1] - zs[k] for k in range(0, len(zs), 2))
        return out

    inside, around = [], []
    for a in g['aps']:
        px, py = to_print(a['ax'], a['ay'])
        hx, hy = a['sq'][0] / 2 - 0.05, a['sq'][1] / 2 - 0.05
        inside += [(px, py), (px + hx, py + hy), (px - hx, py - hy), (px + hx, py - hy), (px - hx, py + hy)]
        # in the membrane just outside the pad-side opening, in x and y
        dx, dy = a['pd'][0] / 2 + 0.10, a['pd'][1] / 2 + 0.10
        around += [(px + dx, py + 0.013), (px - dx, py + 0.013), (px + 0.013, py + dy), (px + 0.013, py - dy)]
    ti, ta = thickness(inside), thickness(around)
    check(float(np.max(ti)) < 1e-6, f'material found inside an aperture (max {np.max(ti):.4f})')
    check(np.allclose(ta, P['membrane'], atol=1e-3), f'membrane is not {P["membrane"]} everywhere around the apertures: {ta.min():.4f}..{ta.max():.4f}')
    notes.append(f'membrane around the 24 apertures: {ta.min():.4f}..{ta.max():.4f} mm (n={len(ta)}); inside the apertures: max {np.max(ti):.4f}')

    # --- derived numbers ---
    a0 = g['aps'][0]
    vol_model = a0['sq'][0] * a0['sq'][1] * P['layer'] + a0['pd'][0] * a0['pd'][1] * P['layer']
    pad_area = a0['pad_poly'].area
    steel = pad_area * P['steel_thickness']
    ar = (a0['sq'][0] * a0['sq'][1]) / (2 * (a0['sq'][0] + a0['sq'][1]) * P['membrane'])
    derived = dict(file=name, D=D, H=H, aperture_squeegee_mm=list(a0['sq']), aperture_pad_side_mm=[round(v, 3) for v in a0['pd']],
                   pad_mm=[round(v, 3) for v in a0['pad_size']], paste_per_pad_model_mm3=round(vol_model, 3),
                   paste_per_pad_steel_0p12_mm3=round(steel, 3), area_ratio_squeegee_half=round(ar, 2),
                   card_mm=[x1 - x0, y1 - y0, H], card_vs_strip_clear_mm=P['clear'], notes=notes,
                   mesh_triangles=int(len(mesh.faces)), mesh_volume_mm3=round(float(mesh.volume), 2))

    if fails:
        print(f'D{D}: FAIL')
        for f in fails:
            print('  -', f)
        sys.exit(1)
    print(f'D{D}: ok  ({name}: {len(mesh.faces)} triangles, {mesh.volume:.0f} mm3, H {H})')
    for n in notes:
        print('   ', n)
    if write and abs(D - P['default_depth']) < 1e-9:
        step = OUT / f'light-strip-stencil_D{D}_use.step'
        cq.exporters.export(solid, str(step))
        derived['step'] = step.name
    return derived, g


# ---------------------------------------------------------------------------------------------------------------
def build_coupon(P=PARAMS):
    """Optional aperture test coupon (about 1 g, 5 min): three rows of holes from 0.4 to 1.0 mm in a 0.2 mm membrane
    over 2.5 mm wide channels, printed face down like the stencil, so Ian can see where HIS printer stops opening holes."""
    import cadquery as cq
    import trimesh
    M, D = 0.2, 0.4
    H = M + D
    plate = cq.Workplane('XY').box(40, 30, H, centered=(True, True, False))
    for yc in (0, 8, -8):
        plate = plate.cut(cq.Workplane('XY').workplane(offset=M).center(0, yc).rect(26, 2.5).extrude(D + 1))
    rows = {0: [(0.5, 1.1), (0.6, 1.1), (0.7, 1.1), (0.8, 1.1), (0.9, 1.3), (1.0, 1.6)],       # short side, long side
            8: [(0.45, 0.7), (0.5, 0.75), (0.55, 0.8), (0.6, 0.9), (0.65, 0.9), (0.7, 1.0)],
            -8: [(0.4, 0.4), (0.5, 0.5), (0.6, 0.6), (0.7, 0.7), (0.8, 0.8), (1.0, 1.0)]}
    holes = []
    for yc, row in rows.items():
        for i, (w, l) in enumerate(row):
            xc = -10 + 4 * i
            holes.append(dict(row=yc, x=xc, y=yc, long=l, short=w))
            plate = plate.cut(cq.Workplane('XY').workplane(offset=-1).center(xc, yc).rect(l, w).extrude(H + 2))
    plate = plate.cut(cq.Workplane('XY').workplane(offset=-1).polyline([(-21, 16), (-15, 16), (-21, 10)]).close().extrude(H + 2))   # corner mark
    stl = OUT / 'aperture-coupon_print.stl'
    cq.exporters.export(plate, str(stl), tolerance=0.002, angularTolerance=0.05)
    m = trimesh.load(stl)
    assert m.is_watertight
    print(f'coupon: ok ({len(m.faces)} triangles)')
    return dict(file=stl.name, holes=holes, size_mm=[40, 30, H])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--depth', type=float, help='build only this pocket depth (0.3, 0.4 or 0.5)')
    ap.add_argument('--no-coupon', action='store_true')
    args = ap.parse_args()
    nominal = check_pick_depth()
    depths = (args.depth,) if args.depth else PARAMS['depths']
    results = {}
    g = None
    for D in depths:
        results[f'D{D}'], g = build(D)
    params = dict(parameters={k: (list(v) if isinstance(v, tuple) else v) for k, v in PARAMS.items()},
                  liner_mm=PARAMS['liner'], bar_nominal_with_liner_mm=nominal, files=results,
                  source=dict(board=load_input()['board'], board_blob=load_input()['board_blob'], head=load_input()['head']))
    if not args.no_coupon:
        params['coupon'] = build_coupon()
    pj = OUT / 'stencil_params.json'
    if pj.exists():      # keep the slice-check numbers when only some files are rebuilt
        old = json.loads(pj.read_text(encoding='utf-8'))
        for k, v in old.get('files', {}).items():
            if k in params['files'] and 'slice' in v and 'slice' not in params['files'][k]:
                params['files'][k]['slice'] = v['slice']
        for k, v in old.get('files', {}).items():
            params['files'].setdefault(k, v)
    pj.write_text(json.dumps(params, indent=1), encoding='utf-8')
    print('wrote', pj.relative_to(ROOT))


if __name__ == '__main__':
    main()
