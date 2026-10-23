"""Pictures for the paste stencil (matplotlib, CadQuery venv). Run after stencil.py and slice_check.py:
    <venv>\\Scripts\\python.exe -X utf8 -I tools/stencil/render.py

Writes to docs/images/:
    stencil_overview.png    top (squeegee) face over the strip: pads, apertures, tape, datum edges, a zoom on one LED pair
    stencil_underside.png   the FR4 face: the pocket, the hinge groove, the label (from the real mesh)
    stencil_section.png     a cross-section across the bar through D2's cathode pad, z exaggerated 10 x (from the real mesh)
    stencil_toolpaths.png   the sliced G-code of layers 1 and 2 around D8/D2, with the design overlaid; the stock
                            elephant-foot compensation next to it (from build/stencil/slice/, so run slice_check.py first)
    stencil_squeegee.png    the squeegee: side section, where the runners ride on the card, cutting a card into blades
    stencil_squeegee_part.png  the handle in 3-D from the STL, and the print plate as sliced (run squeegee.py --slice first)
Everything is drawn from the same data the checks use. Nothing here is a photograph of a printed part.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import trimesh
from matplotlib.patches import PathPatch, Polygon as MPoly, Rectangle
from matplotlib.path import Path as MPath
from shapely.affinity import translate
from shapely.geometry import Point, Polygon, box

import stencil as S
import slice_check as C
import squeegee as SG

ROOT = S.ROOT
IMG = ROOT / 'docs' / 'images'
P = S.PARAMS
CX, CY = (P['card'][0] + P['card'][1]) / 2, (P['card'][2] + P['card'][3]) / 2
D = P['default_depth']
CL = P['clear']


def home(geom):
    """A card-frame shape as it sits once the card is pushed onto the datums: +clear in x and in y (KiCad frame)."""
    return translate(geom, CL, CL)


INK = '#222222'
PLA, PLA_DARK = '#9fb3c8', '#6f86a0'
PI, GOLD, TAPE, BLUE = '#f1deb0', '#d9a520', '#f08c1a', '#1f5fbf'
plt.rcParams.update({'font.size': 9, 'font.family': 'DejaVu Sans', 'axes.linewidth': 0.6})


def mpl_path(poly):
    verts, codes = [], []
    for ring in [poly.exterior, *poly.interiors]:
        pts = list(ring.coords)
        verts += pts
        codes += [MPath.MOVETO] + [MPath.LINETO] * (len(pts) - 2) + [MPath.CLOSEPOLY]
    return MPath(verts, codes)


def add(ax, geom, **kw):
    for g in (geom.geoms if hasattr(geom, 'geoms') else [geom]):
        if g.geom_type == 'Polygon' and not g.is_empty:
            ax.add_patch(PathPatch(mpl_path(g), **kw))


def rects(ax, boxes, **kw):
    for x0, y0, x1, y1 in boxes:
        ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, **kw))


def tape_boxes(inp):
    ol = inp['outline_bbox']
    return {'hinge sliver\n(3 mm, in the groove)': (ol[0] - 8, 54.6, 45.3 + 8, 57.6),
            'neck': (49.0, 142.0, 61.0, 150.0),
            'tail end': (49.0, 161.0, 61.0, 166.6)}


def overview(inp, g):
    fig = plt.figure(figsize=(10.8, 13.2))
    gs = fig.add_gridspec(1, 2, width_ratios=[1, 1.15], wspace=0.08)
    ax = fig.add_subplot(gs[0])
    strip = Polygon(inp['outline'])
    add(ax, strip, fc=PI, ec=INK, lw=0.8, zorder=2)
    for t, b in tape_boxes(inp).items():
        rects(ax, [b], fc=TAPE, ec='none', alpha=0.55, zorder=3)
        ax.text(b[2] + 0.8, (b[1] + b[3]) / 2, 'Kapton: ' + t, va='center', fontsize=7.5, color='#a85c00')
    x0, x1, y0, y1 = P['card']
    add(ax, home(g['card']), fc=PLA, ec=PLA_DARK, lw=1.0, alpha=0.55, zorder=4)
    add(ax, home(g['pocket'].intersection(g['card'])), fc='none', ec=PLA_DARK, lw=0.7, ls=(0, (4, 2)), zorder=5)
    gy, gw, _ = P['groove']
    rects(ax, [(x0 + CL, gy - gw / 2 + CL, x1 + CL, gy + gw / 2 + CL)], fc='none', ec=PLA_DARK, hatch='////', lw=0, alpha=0.7, zorder=5)
    for p in inp['paste_pads']:
        b = p['paste_bbox']
        rects(ax, [(b[0], b[1], b[2], b[3])], fc=GOLD, ec='#7a5a00', lw=0.3, zorder=6)
    for a in g['aps']:
        add(ax, home(a['pd_rect']), fc='none', ec=BLUE, lw=0.5, ls=(0, (2, 1.5)), zorder=7)
        add(ax, home(a['sq_rect']), fc='white', ec=BLUE, lw=0.7, zorder=7)
    ax.set_xlim(26, 72)
    ax.set_ylim(170, 28)
    ax.set_aspect('equal')
    ax.set_xlabel('x (mm, KiCad frame)')
    ax.set_ylabel('y (mm, KiCad frame, down)')
    ax.set_title('Squeegee face, card pushed home on the strip', fontsize=10)
    ax.annotate('', xy=(P['datum_x'] + 0.2, 100), xytext=(P['datum_x'] - 8, 100), arrowprops=dict(arrowstyle='-|>', color='#b00020', lw=1.2), zorder=9)
    ax.text(31.6, 97.5, 'card shown pushed\ntoward +x onto\nthe strip edge', color='#b00020', fontsize=7.5, va='bottom')
    ax.annotate('', xy=(50, P['datum_y'] + 0.3), xytext=(50, P['datum_y'] - 5), arrowprops=dict(arrowstyle='-|>', color='#b00020', lw=1.2), zorder=9)
    ax.text(51.2, 131.2, 'and toward +y onto\nthe foot\'s top edge', color='#b00020', fontsize=7.5, va='center')
    ax.text(x1 - 0.5, y1 - 1.0, 'card ends at y 140', fontsize=7, ha='right', va='bottom', color=PLA_DARK)
    ax.text(x0 + 3.5, y0 + 1.2, 'chamfer =\ntop left', fontsize=7, color=PLA_DARK, va='top', ha='left')
    ax.text(60.5, 156, 'D13, D14:\nhand-dotted,\nno stencil', fontsize=7.5, va='center')
    ax.text(27, 153, 'hatched = hinge groove\n(underside, 0.20 deep)\ndashed = pocket (underside)\norange = Kapton tape', fontsize=7, va='top', color=PLA_DARK)

    # zoom on D8/D2
    az = fig.add_subplot(gs[1])
    zx0, zx1, zy0, zy1 = 40.2, 48.6, 57.4, 71.0
    add(az, strip, fc=PI, ec=INK, lw=1.0, zorder=2)
    add(az, home(g['card']), fc=PLA, ec='none', alpha=0.45, zorder=3)
    add(az, home(g['pocket']), fc='none', ec=PLA_DARK, lw=1.0, ls=(0, (4, 2)), zorder=4)
    for p in inp['paste_pads']:
        b = p['paste_bbox']
        rects(az, [(b[0], b[1], b[2], b[3])], fc=GOLD, ec='#7a5a00', lw=0.5, zorder=5)
    for a in g['aps']:
        add(az, home(a['pd_rect']), fc='none', ec=BLUE, lw=0.9, ls=(0, (2, 1.5)), zorder=7)
        add(az, home(a['sq_rect']), fc='white', ec=BLUE, lw=1.3, zorder=7)
    az.set_xlim(zx0, zx1)
    az.set_ylim(zy1, zy0)
    az.set_aspect('equal')
    az.set_title('D8 above, D2 below (pads 1.00 x 1.60, 3.70 apart); openings centred on the pads', fontsize=10)
    az.set_xlabel('x (mm)')
    d2 = [a for a in g['aps'] if a['ref'] == 'D2' and a['pad'] == '2'][0]     # anode, y 65.6
    d8 = [a for a in g['aps'] if a['ref'] == 'D8' and a['pad'] == '2'][0]
    def dim(x, y, text, dx=0, dy=0, ha='left'):
        az.text(x + dx, y + dy, text, fontsize=8, color=BLUE, ha=ha, va='center', zorder=9,
                bbox=dict(fc='white', ec='none', alpha=0.8, pad=0.5))
    dim(46.15, d8['cy'], 'squeegee side 0.80 x 1.10\n(solid blue)', ha='left')
    dim(46.15, d8['cy'] + 1.1, 'pad side 0.90 x 1.20\n(dashed)', ha='left')
    dim(46.15, 62.7 + 0.0, 'pad (gold) 1.00 x 1.60 = paste pad;\nestimate: the paste is about 60-80 %\nof a steel stencil\'s', ha='left')
    az.text(42.9, 70.9, 'strip edge x 43.00', fontsize=7.5, ha='right', va='bottom', color=INK, rotation=90)
    az.text(43.0, 57.55, 'wall on the\nstrip edge', fontsize=7, ha='right', va='top', color=PLA_DARK)
    az.text(45.54, 57.55, '0.24 gap', fontsize=7, ha='left', va='top', color=PLA_DARK)
    fig.suptitle('Light-strip paste stencil, D0.4 file, card pushed home (use view; nothing here has been printed or tried)', fontsize=11, y=0.93)
    fig.savefig(IMG / 'stencil_overview.png', dpi=130, bbox_inches='tight', facecolor='white')
    plt.close(fig)


def mesh_rings(mesh, origin, normal, drop_axis):
    """Closed rings of a mesh section as 2-D shapely geometry (even-odd), in world coordinates with `drop_axis` removed."""
    sec = mesh.section(plane_origin=origin, plane_normal=normal)
    acc = Polygon()
    keep = [i for i in range(3) if i != drop_axis]
    rings = []
    for pts in sec.discrete:
        q = np.asarray(pts)[:, keep]
        if len(q) >= 4:
            rings.append(Polygon(q))
    for r in sorted(rings, key=lambda r: -r.area):
        acc = acc.symmetric_difference(r.buffer(0))
    return acc


def underside(inp, g, mesh, H):
    z = H - 0.05                                   # use-frame z 0.05 = just above the FR4 face
    geom = mesh_rings(mesh, [0, 0, z], [0, 0, 1], 2)
    geom = translate(geom, CX, CY)                 # back to KiCad coordinates
    fig, ax = plt.subplots(figsize=(8.2, 11))
    strip = Polygon(inp['outline'])
    add(ax, geom, fc=PLA, ec=PLA_DARK, lw=0.8, zorder=2)
    add(ax, strip, fc='none', ec=INK, lw=0.8, ls=(0, (3, 2)), zorder=3)
    for p in inp['paste_pads']:
        b = p['paste_bbox']
        if b[3] < 141:
            rects(ax, [(b[0], b[1], b[2], b[3])], fc=GOLD, ec='#7a5a00', lw=0.3, zorder=4)
    ax.set_xlim(24, 70)
    ax.set_ylim(28, 150)       # y of KiCad increasing UPWARD: the card turned over top to bottom
    ax.set_aspect('equal')
    ax.set_xlabel('x (mm, KiCad frame)')
    ax.set_ylabel('y (mm, KiCad frame, UP in this picture)')
    ax.set_title(f'Underside (the FR4 face) of the D{D} card, turned over top to bottom', fontsize=10)
    ax.text(46.2, 140.7, 'foot', fontsize=8, color=PLA_DARK, ha='center')
    ax.text(32.5, 111, 'grey = card material at the FR4 face\n(z 0 to 0.1)\nwhite = pocket (strip outline + 0.12),\nthe hinge groove, the label', fontsize=7.5, va='top')
    ax.annotate('hinge groove\n6.0 wide, 0.20 deep', xy=(31, 56.1), xytext=(31.5, 66), fontsize=7.5, arrowprops=dict(arrowstyle='-', lw=0.6))
    ax.annotate('pocket,\ndashed = strip', xy=(43.9, 80), xytext=(33.5, 92), fontsize=7.5, arrowprops=dict(arrowstyle='-', lw=0.6))
    ax.annotate('pocket tip\n(strip tip + 0.30)', xy=(44.2, 38.9), xytext=(50.5, 36), fontsize=7.5, arrowprops=dict(arrowstyle='-', lw=0.6))
    ax.annotate('pocket runs out of the card edge\n(the neck leaves here)', xy=(55, 139.9), xytext=(47, 146), fontsize=7.5, arrowprops=dict(arrowstyle='-', lw=0.6))
    ax.annotate('x datum: pocket wall (x 42.88)\nmeets strip edge x 43.0 after the push', xy=(42.88, 118), xytext=(26, 124), fontsize=7.5, color='#b00020', arrowprops=dict(arrowstyle='-', lw=0.6, color='#b00020'))
    ax.annotate('y datum: wall above the foot (y 135.38)\nmeets y 135.5 after the push', xy=(50, 135.38), xytext=(56.5, 126), fontsize=7.5, color='#b00020', arrowprops=dict(arrowstyle='-', lw=0.6, color='#b00020'))
    fig.savefig(IMG / 'stencil_underside.png', dpi=130, bbox_inches='tight', facecolor='white')
    plt.close(fig)


def section(inp, g, mesh, H):
    ycut = 69.30                                    # D2's cathode pad (y 68.5 to 70.1)
    geom = mesh_rings(mesh, [0, ycut - CY, 0], [0, 1, 0], 1)     # x, z (print frame)
    geom = translate(geom, CX, 0)
    ZX = 10.0
    liner = P['liner']                              # 3M 9077 data sheet: 0.09 mm
    meas = P['stack_nominal'] + liner               # a nominal bar with the liner on: 0.475
    lift = meas - D                                 # the strip stands this far above the pocket ceiling: the card rides on it
    fig, ax = plt.subplots(figsize=(10.5, 6.6))
    # card: print z -> use z = H - z, drawn lifted by `lift` (the real card bends down to the FR4 a few mm away; not modelled)
    def flip(poly):
        return Polygon([(x, (H - zz + lift) * ZX) for x, zz in poly.exterior.coords], [[(x, (H - zz + lift) * ZX) for x, zz in r.coords] for r in poly.interiors])
    for q in (geom.geoms if hasattr(geom, 'geoms') else [geom]):
        add(ax, flip(q), fc=PLA, ec=PLA_DARK, lw=0.8, zorder=3)
    # FR4 and the strip stack
    layers = [('release liner', 0, liner, '#dddddd', True), ('3M 9077 adhesive 0.05', liner, liner + 0.05, '#c9b27a', False),
              ('PI stiffener 0.225', liner + 0.05, liner + 0.275, '#e6a23c', False), ('flex 0.11 (copper, coverlay)', liner + 0.275, meas, '#2f7d4f', False)]
    rects(ax, [(35, -0.25 * ZX, 52, 0)], fc='#8c7a5b', ec='none', zorder=1)
    ax.text(51.8, -0.2 * ZX, 'FR4 carrier', fontsize=8, ha='right', va='center', color='white')
    for nm, a, b, col, dashed in layers:
        ax.add_patch(Rectangle((43.0, a * ZX), 2.3, (b - a) * ZX, fc=col, ec=INK, lw=0.6, ls='--' if dashed else '-', zorder=2))
    ax.add_patch(Rectangle((43.75, (meas - 0.04) * ZX), 1.0, 0.04 * ZX, fc=GOLD, ec='#7a5a00', lw=0.6, zorder=4))
    ax.text(44.25, (meas + 0.012) * ZX, 'pad', fontsize=7.5, ha='center', va='bottom', color='#7a5a00', zorder=6)
    ax.set_xlim(40.2, 48.3)
    ax.set_ylim(-0.27 * ZX, (H + lift + 0.30) * ZX)
    ax.set_aspect('equal')
    ticks = [0, 0.2, 0.4, 0.6]
    ax.set_yticks([t * ZX for t in ticks])
    ax.set_yticklabels([f'{t:.1f}' for t in ticks])
    ax.set_ylabel('height above the FR4 (mm), drawn 10 x taller')
    ax.set_xlabel('x (mm), across the bar')
    ax.set_title(f"Section across the bar through D2's cathode pad (y 69.30), D{D} file, nominal bar {meas:.3f} mm with the liner", fontsize=10)
    def lab(x, zz, txt, **kw):
        ax.text(x, zz * ZX, txt, fontsize=7.5, va='center', **kw)
    lab(45.7, liner / 2, f'release liner {liner:.2f} (3M data sheet), stays on')
    lab(45.7, liner + 0.025, '3M 9077 adhesive 0.05')
    lab(45.7, liner + 0.16, 'PI stiffener 0.225')
    lab(45.7, liner + 0.33, 'flex 0.11')
    lab(46.2, D + lift + 0.1, 'membrane 0.20 = 2 layers\n(layer 1 = squeegee face, layer 2 = pad side)', color=INK)
    lab(40.4, H + lift + 0.04, 'squeegee face', color=INK)
    lab(40.35, D + lift + 0.10, f'pocket ceiling = bar top\n({meas:.3f}): the membrane\nrests on the strip', color=INK)
    ax.annotate('', xy=(42.88, 0.22 * ZX), xytext=(43.0, 0.22 * ZX), arrowprops=dict(arrowstyle='<->', lw=0.7))
    ax.text(42.8, 0.30 * ZX, '0.12 clearance; the push\ncloses it on this side', fontsize=7, va='center', ha='right', bbox=dict(fc=PLA, ec='none', pad=0.5))
    ax.text(44.25, (H + lift + 0.1) * ZX, 'aperture: 0.80 across on the squeegee side, 0.90 on the pad side.\nCut 0.12 toward -x of the pad centre; the push centres it on the pad', fontsize=7.5, ha='center', va='bottom', color=BLUE)
    ax.text(43.05, -0.12 * ZX, 'x datum: strip edge 43.00', fontsize=7, ha='left', va='center', color='white')
    fig.text(0.5, -0.02, f'The card is drawn lifted {lift:.3f} mm, not bent: a nominal bar stands {lift:.3f} above the D{D} pocket ceiling, '
             'so the card rides on the strip\nand bends down to the FR4 a few mm away (the bend is not modelled).', fontsize=8, ha='center', va='top', color=INK)
    fig.savefig(IMG / 'stencil_section.png', dpi=130, bbox_inches='tight', facecolor='white')
    plt.close(fig)


def toolpaths(g):
    # layers 1 and 2 of the D0.4 slice, around D8/D2, in the use view (x, y of KiCad; y down). Layer 1 is the squeegee face.
    def union_for(gcode):
        layers, _, _ = C.parse(gcode)
        zs = sorted(layers)
        xs = [c for s in layers[zs[0]] for c in (s[0], s[2])]
        ys = [c for s in layers[zs[0]] for c in (s[1], s[3])]
        ox, oy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
        return {z: translate(C.layer_union(layers[z], ox, oy), CX + CL, CY + CL) for z in zs[:2]}      # card pushed home
    base = C.WORK / 'D0.4'
    g0 = next(base.glob('plate_1.gcode'))
    g1 = next((C.WORK / 'D0.4_efc01').glob('plate_1.gcode'))
    U0, U1 = union_for(g0), union_for(g1)
    panels = [('layer 1 (squeegee face), stock settings\nwith EFC 0: apertures 0.80 x 1.10', U0[0.1]),
              ('layer 2 (pad side): 0.90 x 1.20', U0[0.2]),
              ('layer 1 with the stock EFC 0.1:\nholes grow 0.10 per side (do not use)', U1[0.1])]
    fig, axs = plt.subplots(1, 3, figsize=(12, 6.2), sharey=True)
    win = box(41.0, 57.0, 47.2, 71.2)
    for ax, (title, U) in zip(axs, panels):
        add(ax, U.intersection(win), fc='#7e8a99', ec='#3b4654', lw=0.3, zorder=2)
        for a in g['aps']:
            if win.intersects(a['pad_poly']):
                add(ax, a['pad_poly'], fc='none', ec=GOLD, lw=1.2, zorder=4)
                add(ax, home(a['sq_rect']), fc='none', ec=BLUE, lw=1.2, zorder=5)
                add(ax, home(a['pd_rect']), fc='none', ec=BLUE, lw=0.9, ls=(0, (2, 1.5)), zorder=5)
        ax.set_xlim(41.0, 47.2)
        ax.set_ylim(71.2, 57.0)
        ax.set_aspect('equal')
        ax.set_title(title, fontsize=9)
        ax.set_xlabel('x (mm)')
    axs[0].set_ylabel('y (mm)')
    fig.suptitle('Sliced toolpath around D8 / D2 (grey = plastic, white = open). Card pushed home. Gold = pad, blue = designed aperture.', fontsize=10)
    fig.savefig(IMG / 'stencil_toolpaths.png', dpi=130, bbox_inches='tight', facecolor='white')
    plt.close(fig)


# ---------------------------------------------------------------------------------------------------------------
# The squeegee (see squeegee.py). Frame: s along the stroke, w across, h up from the stencil card's face.
# ---------------------------------------------------------------------------------------------------------------
def squeegee_meshes():
    """(handle mesh in the squeegee frame, plate mesh as printed), from production/stencil/squeegee_print.stl."""
    plate = trimesh.load(S.OUT / 'squeegee_print.stl')
    bodies = sorted(plate.split(only_watertight=False), key=lambda m: -m.volume)
    handle = bodies[0].copy()
    prof = SG.profiles()
    shift = -(SG.SQ['runner_s'][0] + prof['C'][0]) / 2
    handle.apply_translation([-shift, 0, 0])
    return handle, plate


def squeegee_figure(inp, g):
    handle, plate = squeegee_meshes()
    sq = SG.SQ
    Pf = SG.profiles()
    Q = SG.Q
    A = SG.A
    d_tip = sq['interference'] / np.cos(A)
    tip_s = -d_tip * np.sin(A)
    fig = plt.figure(figsize=(15.5, 10.6))
    gs = fig.add_gridspec(2, 2, width_ratios=[1.3, 1], height_ratios=[1.45, 1], wspace=0.10, hspace=0.24)
    LBL = dict(arrowprops=dict(arrowstyle='-', lw=0.6, color='#444444'), bbox=dict(fc='white', ec='none', alpha=0.85, pad=1.0), zorder=12)

    # ---- (a) side section at w = 0 ----
    ax = fig.add_subplot(gs[0, 0])
    sec = SG.section_poly(handle, 1, 0.0)
    add(ax, sec, fc=PLA, ec=PLA_DARK, lw=0.8, zorder=3)
    ax.add_patch(Rectangle((-14, -0.6), 41, 0.6, fc='#c5d2e0', ec=PLA_DARK, lw=0.6, zorder=2))
    ax.add_patch(Rectangle((-14, -2.4), 41, 1.8, fc='#8c7a5b', ec='none', zorder=1))
    ax.text(26.6, -1.5, 'strip on an FR4 scrap', fontsize=7.5, color='white', ha='right', va='center')
    ax.plot([-14, 27], [0, 0], color=INK, lw=0.8, zorder=6)
    ax.annotate('stencil card (0.6 thick), squeegee face up:\nits face is the runner plane, h 0', xy=(-9, -0.3), xytext=(-13.8, 5.2), fontsize=7.5, va='center', **LBL)
    t = 0.76
    straight = Polygon([Q(0, 0), Q(sq['stop'], 0), Q(sq['stop'], t), Q(0, t)])
    add(ax, straight, fc='none', ec='#b36b00', lw=1.0, ls=(0, (4, 2)), zorder=7)
    inslot = Polygon([Q(sq['mouth'], 0), Q(sq['stop'], 0), Q(sq['stop'], t), Q(sq['mouth'], t)])
    loaded = SG.bent_blade(d_tip, t, 0.0, sq['mouth']).union(inslot)
    add(ax, loaded, fc='#f5d98a', ec='#7a4a00', lw=1.1, zorder=8)
    U_ = SG.U

    def tube(o0, o1, r):
        pt = lambda o, dr: (SG.Q(sq['hole_lam'], o)[0] + dr * U_[0], SG.Q(sq['hole_lam'], o)[1] + dr * U_[1])
        return Polygon([pt(o0, -r), pt(o1, -r), pt(o1, r), pt(o0, r)])
    add(ax, tube(SG.O_BACK - 8.0, SG.O_BACK, 1.5), fc='none', ec='#444444', lw=0.9, ls=(0, (3, 2)), zorder=9)
    add(ax, tube(SG.O_BACK, SG.O_BACK + 2.0, 2.75), fc='none', ec='#444444', lw=0.9, ls=(0, (3, 2)), zorder=9)
    ax.annotate('M3 thread-forming screw (8-12 mm), drawn dashed;\nit pushes the tongue, never tighten it with no blade in', xy=Q(sq['hole_lam'], SG.O_BACK + 1.0), xytext=(-13.8, 27.2), fontsize=7.5, va='center', **LBL)
    ax.annotate('tongue, 1.6 thick: free at the mouth,\nclamps the blade across its whole width', xy=Q(21, (SG.O_T0 + SG.O_T1) / 2), xytext=(-13.8, 23.3), fontsize=7.5, va='center', **LBL)
    ax.annotate('slot 1.25 wide (10.6 across);\nthe blade bottoms on the stop', xy=Q(sq['stop'] - 0.5, 0.6), xytext=(20.0, 26.2), fontsize=7.5, va='center', **LBL)
    ax.annotate('flat finger pad, above the blade', xy=(-1.0, Pf['G'][1]), xytext=(-13.8, 19.4), fontsize=7.5, va='center', **LBL)
    ax.annotate('runner (one each side, 3 x 22)', xy=(-3, 0.0), xytext=(-13.8, 9.2), fontsize=7.5, va='center', **LBL)
    # the blade's numbers, in a block on the clear side
    ax.text(10.6, 9.2, 'card blade, 0.76 thick, 10 wide, 27 long\n'
            '- slot holds it at 50 deg (dashed = unloaded, edge 0.9 below h 0)\n'
            '- loaded flat on the card: tip bent back 1.4, angle about 42 deg\n'
            '- free length 15.0 (front face, slot lip to the edge)\n'
            '- edge force about 1.4 N (1.0-2.3 N): estimate, not measured', fontsize=7.4, va='top', ha='left', color='#5a3500',
            bbox=dict(fc='white', ec='#b36b00', lw=0.6, alpha=0.92, pad=3))
    lip = Q(sq['mouth'], 0)
    ax.plot([lip[0]], [lip[1]], 'o', color='#7a4a00', ms=3.5, zorder=10)
    ax.annotate('slot lip', xy=lip, xytext=(14.2, 11.7), fontsize=7, color='#7a4a00', va='center', **LBL)
    ax.annotate('', xy=(-3.0, -sq['interference']), xytext=(-3.0, 0), arrowprops=dict(arrowstyle='<->', lw=0.7, color='#b36b00'))
    ax.plot([-3.4, 0.2], [-sq['interference']] * 2, color='#b36b00', lw=0.7, ls=(0, (3, 2)), zorder=7)
    ax.text(-3.4, -0.45, '0.9', fontsize=7, color='#b36b00', ha='right', va='center')
    ax.annotate('loaded edge, s %.1f' % tip_s, xy=(tip_s, 0.0), xytext=(-13.5, 1.6), fontsize=7.5, color='#7a4a00', va='center', **LBL)
    bead = Point(tip_s + 3.0, 0.95).buffer(0.95)
    ax.add_patch(PathPatch(mpl_path(Polygon(bead.exterior.coords)), fc='#9aa0a6', ec='#555555', lw=0.6, zorder=8))
    ax.annotate('paste ahead of the blade', xy=(tip_s + 3.5, 1.5), xytext=(5.6, 3.2), fontsize=7.5, color='#444444', va='center', **LBL)
    ax.annotate('', xy=(12.5, -3.4), xytext=(-2.0, -3.4), arrowprops=dict(arrowstyle='-|>', color='#b00020', lw=1.2))
    ax.text(5.2, -3.85, 'travel +s: toward the foot, tall end first', fontsize=8, color='#b00020', ha='center', va='top')
    ax.set_xlim(-14.5, 27.5)
    ax.set_ylim(-4.6, 29.0)
    ax.set_aspect('equal')
    ax.set_xlabel('s (mm), along the stroke')
    ax.set_ylabel('h (mm), above the card face')
    ax.set_title('(a) Side section through the middle of the handle (w = 0), loaded on the stencil card', fontsize=10, loc='left')

    # ---- (b) top view of the stencil card, card frame ----
    bx = fig.add_subplot(gs[:, 1])
    x0, x1, y0, y1 = P['card']
    add(bx, g['card'], fc=PLA, ec=PLA_DARK, lw=1.0, alpha=0.5, zorder=2)
    gy, gw, _ = P['groove']
    rects(bx, [(x0, gy - gw / 2, x1, gy + gw / 2)], fc='none', ec=PLA_DARK, hatch='////', lw=0, alpha=0.7, zorder=3)
    for t_, b_ in tape_boxes(inp).items():
        rects(bx, [b_], fc=TAPE, ec='none', alpha=0.55, zorder=3)
    bx.text(55, 146, 'neck tape', fontsize=7, color='#a85c00', ha='center', va='center')
    bx.text(55, 164, 'tail tape', fontsize=7, color='#a85c00', ha='center', va='center')
    bx.annotate('hinge groove (hatched, card underside)\nand the 3 mm Kapton sliver in it;\nthe runners bridge it', xy=(x1, gy), xytext=(x1 + 1.5, gy - 0.5), fontsize=7, color='#555555', va='center', **LBL)
    add(bx, g['pocket'].intersection(g['card']), fc='none', ec=PLA_DARK, lw=0.7, ls=(0, (4, 2)), zorder=4)
    cx = sq['column_x']
    r0, r1 = sq['runner_w']
    for a in g['aps']:
        add(bx, a['sq_rect'].buffer(0.25), fc=BLUE, ec='none', zorder=6)
    ys0, ys1 = g['aps'][0]['sq_rect'].bounds[1], g['aps'][-1]['sq_rect'].bounds[3]
    sy0, sy1 = sq['stroke']
    sweep = (sy0 - tip_s + sq['runner_s'][0] + sq['runner_chamfer'], sy1 - tip_s + sq['runner_s'][1] - sq['runner_chamfer'])
    for lo_, hi_ in ((cx - r1, cx - r0), (cx + r0, cx + r1)):
        add(bx, box(lo_, sweep[0], hi_, sweep[1]).intersection(g['card']), fc='#2f9e44', ec='#1b6b2c', lw=0.8, alpha=0.35, zorder=5)
        bx.text((lo_ + hi_) / 2, 112, 'runner track', fontsize=7, color='#1b6b2c', rotation=90, ha='center', va='center', zorder=7)
    ym = 86.0
    ys_ = ym - tip_s
    for lo_, hi_ in ((cx - r1, cx - r0), (cx + r0, cx + r1)):
        bx.add_patch(Rectangle((lo_, ys_ + sq['runner_s'][0] + sq['runner_chamfer']), hi_ - lo_, sq['runner_s'][1] - sq['runner_s'][0] - 2 * sq['runner_chamfer'], fc='#2f9e44', ec='#1b6b2c', lw=1.2, alpha=0.85, zorder=8))
    bx.plot([cx - 5, cx + 5], [ym, ym], color='#b36b00', lw=3, solid_capstyle='butt', zorder=9)
    bx.annotate('squeegee drawn mid-stroke: two runners\nand the 10 mm blade line', xy=(cx + 5, ym), xytext=(x1 + 1.5, ym + 2), fontsize=7.5, color='#7a4a00', va='center', **LBL)
    for yy, nm in ((sy0, 'start: blade line at card y %.1f\n(%.1f before the first opening)' % (sy0, ys0 - sy0)),
                   (sy1, 'end: blade line at card y %.1f\n(%.1f past the last opening)' % (sy1, sy1 - ys1))):
        bx.plot([cx - 5, cx + 5], [yy, yy], color='#b00020', lw=2.2, zorder=9)
        bx.annotate(nm, xy=(cx + 5, yy), xytext=(x1 + 1.5, yy), fontsize=7.5, color='#b00020', va='center', arrowprops=dict(arrowstyle='-', lw=0.6, color='#b00020'))
    bx.annotate('', xy=(47.6, 128), xytext=(47.6, 45), arrowprops=dict(arrowstyle='-|>', color='#b00020', lw=1.6), zorder=10)
    bx.text(47.1, 62, 'one pass, toward the foot (+y)', fontsize=7.5, color='#b00020', rotation=90, ha='right', va='center', zorder=10)
    bx.text(cx - 0.4, 120, '24 openings', fontsize=7.5, color=BLUE, ha='right', va='center', rotation=90)
    bx.annotate('', xy=(x0, 122), xytext=(cx - r1, 122), arrowprops=dict(arrowstyle='<->', lw=0.7))
    bx.annotate('about 3 mm of card outside the\nleft runner (0-6 mm is fine)', xy=((x0 + cx - r1) / 2, 122), xytext=(x1 + 1.5, 122), fontsize=7.5, va='center', **LBL)
    rects(bx, [(58.0, y0, x1, y0 + 5), (58.0, y1 - 5, x1, y1)], fc='none', ec='#a85c00', hatch='xx', lw=0.6, alpha=0.8, zorder=4)
    bx.annotate('only place for corner tape (x >= 58)', xy=(60, y1 - 2.5), xytext=(x1 + 1.5, 150.5), fontsize=7, color='#a85c00', va='center', arrowprops=dict(arrowstyle='-', lw=0.6, color='#a85c00'))
    bx.set_xlim(x0 - 3, x1 + 27)
    bx.set_ylim(170, y0 - 6)
    bx.set_aspect('equal')
    bx.set_xlabel('x (mm, card frame, as built; the push to the datums then adds +0.12)')
    bx.set_ylabel('y (mm, card frame, down)')
    bx.set_title('(b) Squeegee face of the stencil card', fontsize=10, loc='left')

    # ---- (c) cutting a card ----
    cc = fig.add_subplot(gs[1, 0])
    W, Hc = 85.6, 53.98
    add(cc, box(0, 0, W, Hc).buffer(-3.18).buffer(3.18, quad_segs=12), fc='#e8e8e8', ec=INK, lw=1.0, zorder=2)
    cc.plot([0, W], [Hc / 2, Hc / 2], color='#b00020', lw=1.2, ls=(0, (6, 3)), zorder=5)
    for k in range(7):
        xa = 7.8 + 10.0 * k
        cc.add_patch(Rectangle((xa, Hc / 2), 10.0, 26.99, fc='#f5d98a', ec='#7a4a00', lw=0.7, zorder=3))
        cc.add_patch(Rectangle((xa, 0), 10.0, 26.99, fc='#f5d98a', ec='#7a4a00', lw=0.7, zorder=3))
    cc.plot([7.8, 77.8], [Hc, Hc], color='#1b6b2c', lw=3, zorder=6)
    cc.plot([7.8, 77.8], [0, 0], color='#1b6b2c', lw=3, zorder=6)
    cc.text(W / 2, Hc + 1.0, 'thick green = the card\'s factory edge = the blade\'s working edge', fontsize=7.5, color='#1b6b2c', ha='center', va='bottom')
    cc.text(W / 2, -1.0, 'the same edge on the lower strip: 14 blades per card', fontsize=7.5, color='#1b6b2c', ha='center', va='top')
    cc.text(W / 2, Hc / 2 + 1.0, 'cut along the middle (red): 26.99 from each long edge', fontsize=7.5, color='#b00020', ha='center', va='bottom', zorder=7,
            bbox=dict(fc='white', ec='none', alpha=0.8, pad=1.0))
    cc.text(W / 2, Hc * 0.80, 'each blade 10.0 wide x 27.0 long; the cut edge goes into the slot', fontsize=7.5, ha='center', va='center', color='#7a4a00', zorder=7,
            bbox=dict(fc='white', ec='none', alpha=0.8, pad=1.0))
    cc.text(W / 2, Hc * 0.22, 'avoid embossed digits, the chip and any hologram: use a plain area', fontsize=7.5, ha='center', va='center', color='#555555', zorder=7,
            bbox=dict(fc='white', ec='none', alpha=0.8, pad=1.0))
    cc.text(3.9, Hc * 0.93, '4 mm\nspare', fontsize=6.3, ha='center', va='top', color='#555555', zorder=7)
    cc.text(W - 3.9, Hc * 0.93, '4 mm\nspare', fontsize=6.3, ha='center', va='top', color='#555555', zorder=7)
    cc.set_xlim(-3, W + 3)
    cc.set_ylim(-6.5, Hc + 7)
    cc.set_aspect('equal')
    cc.set_xlabel('mm (an ISO ID-1 card: 85.60 x 53.98 x 0.76)')
    cc.set_yticks([])
    cc.set_title('(c) Cutting a gift or loyalty card into blades', fontsize=10, loc='left')
    fig.suptitle('Stencil squeegee (printed handle, card blade). Nothing here has been printed or tried; forces and angles are beam estimates.', fontsize=11.5, y=0.945)
    fig.savefig(IMG / 'stencil_squeegee.png', dpi=120, bbox_inches='tight', facecolor='white')
    plt.close(fig)


def zbuffer_view(mesh, az, el, size=760, base=(0.60, 0.70, 0.82), pad=0.06):
    """A flat-shaded orthographic picture of a mesh with a z-buffer (matplotlib's 3-D painter's sort mangles large triangles).
    az, el in degrees: the camera sits in direction (cos el cos az, cos el sin az, sin el) from the object's centre."""
    azr, elr = np.radians(az), np.radians(el)
    d = np.array([np.cos(elr) * np.cos(azr), np.cos(elr) * np.sin(azr), np.sin(elr)])
    f = -d
    right = np.cross(f, [0, 0, 1.0])
    right /= np.linalg.norm(right)
    up = np.cross(right, f)
    centre = (mesh.bounds[0] + mesh.bounds[1]) / 2
    V = mesh.vertices - centre
    px, py, pz = V @ right, V @ up, V @ d
    tri = mesh.faces
    span = max(px.max() - px.min(), py.max() - py.min())
    scale = size * (1 - 2 * pad) / span
    X = (px - (px.max() + px.min()) / 2) * scale + size / 2
    Y = size / 2 - (py - (py.max() + py.min()) / 2) * scale
    img = np.ones((size, size, 3))
    zbuf = np.full((size, size), -1e9)
    L1 = np.array([0.35, -0.55, 0.75])
    L2 = np.array([-0.6, 0.3, 0.2])
    L1 /= np.linalg.norm(L1)
    L2 /= np.linalg.norm(L2)
    n = mesh.face_normals
    sh = 0.30 + 0.55 * np.clip(n @ L1, 0, 1) + 0.25 * np.clip(n @ L2, 0, 1)
    facing = n @ d
    for i, (a, b, c) in enumerate(tri):
        xs, ys = X[[a, b, c]], Y[[a, b, c]]
        x0_, x1_ = int(max(0, np.floor(xs.min()))), int(min(size - 1, np.ceil(xs.max())))
        y0_, y1_ = int(max(0, np.floor(ys.min()))), int(min(size - 1, np.ceil(ys.max())))
        if x1_ < x0_ or y1_ < y0_:
            continue
        gx, gy = np.meshgrid(np.arange(x0_, x1_ + 1) + 0.5, np.arange(y0_, y1_ + 1) + 0.5)
        den = (ys[1] - ys[2]) * (xs[0] - xs[2]) + (xs[2] - xs[1]) * (ys[0] - ys[2])
        if abs(den) < 1e-9:
            continue
        l1 = ((ys[1] - ys[2]) * (gx - xs[2]) + (xs[2] - xs[1]) * (gy - ys[2])) / den
        l2 = ((ys[2] - ys[0]) * (gx - xs[2]) + (xs[0] - xs[2]) * (gy - ys[2])) / den
        l3 = 1 - l1 - l2
        inside = (l1 >= -1e-6) & (l2 >= -1e-6) & (l3 >= -1e-6)
        z = l1 * pz[a] + l2 * pz[b] + l3 * pz[c]
        sub = zbuf[y0_:y1_ + 1, x0_:x1_ + 1]
        upd = inside & (z > sub)
        sub[upd] = z[upd]
        col = np.array(base) * sh[i]
        if facing[i] < 0:
            col = col * 0.7                                                   # a back face seen through a hole
        img[y0_:y1_ + 1, x0_:x1_ + 1][upd] = np.clip(col, 0, 1)
    # darken the silhouette and creases: pixels where the depth jumps
    dz = np.maximum(np.abs(np.diff(zbuf, axis=0, prepend=zbuf[:1])), np.abs(np.diff(zbuf, axis=1, prepend=zbuf[:, :1])))
    edge = (dz > 0.8) & (zbuf > -1e8)
    img[edge] = img[edge] * 0.55
    return img


def squeegee_part_figure():
    handle, plate = squeegee_meshes()
    fig = plt.figure(figsize=(14, 11.2))
    gs = fig.add_gridspec(2, 2, wspace=0.04, hspace=0.12)
    views = [('(a) From the front, a little above: the tall end leads, travel is toward +s.\nThe arrow on each side points the way.', -28, 16),
             ('(b) From the back right: the flat finger pad above the blade,\nthe M3 screw hole in the sloping back face.', 125, 28),
             ('(c) From the front and below: the two runners, the slot mouth, the tongue\nand the open space for the paste and the blade.', -22, -38)]
    for k, (title, az, el) in enumerate(views):
        a = fig.add_subplot(gs[k // 2, k % 2])
        a.imshow(zbuffer_view(handle, az, el))
        a.set_axis_off()
        a.set_title(title, fontsize=9.5, loc='left')
    a3 = fig.add_subplot(gs[1, 1])
    work = C.WORK.parent / 'squeegee'
    gc = next(work.glob('plate_1.gcode'), None)
    sec1 = SG.section_poly(plate, 2, 0.1)
    add(a3, plate_outline(plate), fc='#e9eef4', ec='#9aa7b5', lw=0.8, zorder=1)
    add(a3, sec1, fc='#3b4654', ec='none', zorder=3)
    if gc is not None:
        lay, _, _ = C.parse(gc)
        zs = sorted(lay)
        rail = [q for q in lay[zs[0]] if (q[1] + q[3]) / 2 < C.BED_CENTRE[1] + 15]
        rails_design = sec1.buffer(-0.1).intersection(box(-100, -100, 100, 15))
        ox = (min(c for q in rail for c in (q[0], q[2])) + max(c for q in rail for c in (q[0], q[2]))) / 2 - (rails_design.bounds[0] + rails_design.bounds[2]) / 2
        oy = (min(c for q in rail for c in (q[1], q[3])) + max(c for q in rail for c in (q[1], q[3]))) / 2 - (rails_design.bounds[1] + rails_design.bounds[3]) / 2
        add(a3, C.layer_union(lay[zs[0]], ox, oy), fc='#1f5fbf', ec='none', zorder=4)
    a3.set_aspect('equal')
    a3.set_xlabel('mm, print frame (the slicer puts the plate at the bed centre)')
    a3.set_title('(d) The print plate from above. Blue = sliced layer 1: the two\nrunner rails and the two blade edges. Grey = the handle above them.', fontsize=9.5, loc='left')
    a3.text(0, 24.6, 'two PLA blades, 10 x 1.0 x 26.2, standing on their working edges', fontsize=8, ha='center', va='bottom')
    a3.text(0, 0, 'handle, runners down\n(31.6 x 20.3 x 27.9)', fontsize=8, ha='center', va='center', color='#445566')
    a3.set_xlim(-20, 20)
    a3.set_ylim(-13, 29)
    fig.suptitle('Squeegee handle and print plate, from the STL and the OrcaSlicer read-back (a model view, not a photograph)', fontsize=11, y=0.96)
    fig.savefig(IMG / 'stencil_squeegee_part.png', dpi=110, bbox_inches='tight', facecolor='white')
    plt.close(fig)


def plate_outline(plate):
    """The plate's outline seen from above."""
    polys = []
    for body in plate.split(only_watertight=False):
        pts = body.vertices[:, :2]
        from shapely.geometry import MultiPoint
        polys.append(MultiPoint(pts).convex_hull)
    from shapely.ops import unary_union as uu
    u = uu(polys)
    return u


def main():
    IMG.mkdir(parents=True, exist_ok=True)
    inp = S.load_input()
    g = S.geometry(D, inp)
    mesh = trimesh.load(S.OUT / f'light-strip-stencil_D{D}_print.stl')
    overview(inp, g)
    underside(inp, g, mesh, g['H'])
    section(inp, g, mesh, g['H'])
    toolpaths(g)
    squeegee_figure(inp, g)
    squeegee_part_figure()
    for n in ('overview', 'underside', 'section', 'toolpaths', 'squeegee', 'squeegee_part'):
        print('wrote docs/images/stencil_%s.png' % n)


if __name__ == '__main__':
    main()
