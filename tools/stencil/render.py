"""Pictures for the paste stencil (matplotlib, CadQuery venv). Run after stencil.py and slice_check.py:
    <venv>\\Scripts\\python.exe -X utf8 -I tools/stencil/render.py

Writes to docs/images/:
    stencil_overview.png    top (squeegee) face over the strip: pads, apertures, tape, datum edges, a zoom on one LED pair
    stencil_underside.png   the FR4 face: the pocket, the hinge groove, the label (from the real mesh)
    stencil_section.png     a cross-section across the bar through D2's cathode pad, z exaggerated 10 x (from the real mesh)
    stencil_toolpaths.png   the sliced G-code of layers 1 and 2 around D8/D2, with the design overlaid; the stock
                            elephant-foot compensation next to it (from build/stencil/slice/, so run slice_check.py first)
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
from shapely.geometry import Polygon, box

import stencil as S
import slice_check as C

ROOT = S.ROOT
IMG = ROOT / 'docs' / 'images'
P = S.PARAMS
CX, CY = (P['card'][0] + P['card'][1]) / 2, (P['card'][2] + P['card'][3]) / 2
D = P['default_depth']
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
    add(ax, g['card'], fc=PLA, ec=PLA_DARK, lw=1.0, alpha=0.55, zorder=4)
    add(ax, g['pocket'].intersection(g['card']), fc='none', ec=PLA_DARK, lw=0.7, ls=(0, (4, 2)), zorder=5)
    gy, gw, _ = P['groove']
    rects(ax, [(x0, gy - gw / 2, x1, gy + gw / 2)], fc='none', ec=PLA_DARK, hatch='////', lw=0, alpha=0.7, zorder=5)
    for p in inp['paste_pads']:
        b = p['paste_bbox']
        rects(ax, [(b[0], b[1], b[2], b[3])], fc=GOLD, ec='#7a5a00', lw=0.3, zorder=6)
    for a in g['aps']:
        add(ax, a['pd_rect'], fc='none', ec=BLUE, lw=0.5, ls=(0, (2, 1.5)), zorder=7)
        add(ax, a['sq_rect'], fc='white', ec=BLUE, lw=0.7, zorder=7)
    ax.set_xlim(26, 72)
    ax.set_ylim(170, 28)
    ax.set_aspect('equal')
    ax.set_xlabel('x (mm, KiCad frame)')
    ax.set_ylabel('y (mm, KiCad frame, down)')
    ax.set_title('Squeegee face, card over the strip', fontsize=10)
    ax.annotate('', xy=(P['datum_x'] + 0.2, 100), xytext=(P['datum_x'] - 8, 100), arrowprops=dict(arrowstyle='-|>', color='#b00020', lw=1.2), zorder=9)
    ax.text(31.6, 97.5, 'push the card\ntoward +x onto\nthe strip edge', color='#b00020', fontsize=7.5, va='bottom')
    ax.annotate('', xy=(50, P['datum_y'] + 0.3), xytext=(50, P['datum_y'] - 5), arrowprops=dict(arrowstyle='-|>', color='#b00020', lw=1.2), zorder=9)
    ax.text(51.2, 131.2, 'push toward +y onto\nthe foot\'s top edge', color='#b00020', fontsize=7.5, va='center')
    ax.text(x1 - 0.5, y1 - 1.0, 'card ends at y 140', fontsize=7, ha='right', va='bottom', color=PLA_DARK)
    ax.text(x0 + 3.5, y0 + 1.2, 'chamfer =\ntop left', fontsize=7, color=PLA_DARK, va='top', ha='left')
    ax.text(60.5, 156, 'D13, D14:\nhand-dotted,\nno stencil', fontsize=7.5, va='center')
    ax.text(27, 153, 'hatched = hinge groove\n(underside, 0.20 deep)\ndashed = pocket (underside)\norange = Kapton tape', fontsize=7, va='top', color=PLA_DARK)

    # zoom on D8/D2
    az = fig.add_subplot(gs[1])
    zx0, zx1, zy0, zy1 = 40.2, 48.6, 57.4, 71.0
    add(az, strip, fc=PI, ec=INK, lw=1.0, zorder=2)
    add(az, g['card'], fc=PLA, ec='none', alpha=0.45, zorder=3)
    add(az, g['pocket'], fc='none', ec=PLA_DARK, lw=1.0, ls=(0, (4, 2)), zorder=4)
    for p in inp['paste_pads']:
        b = p['paste_bbox']
        rects(az, [(b[0], b[1], b[2], b[3])], fc=GOLD, ec='#7a5a00', lw=0.5, zorder=5)
    for a in g['aps']:
        add(az, a['pd_rect'], fc='none', ec=BLUE, lw=0.9, ls=(0, (2, 1.5)), zorder=7)
        add(az, a['sq_rect'], fc='white', ec=BLUE, lw=1.3, zorder=7)
    az.set_xlim(zx0, zx1)
    az.set_ylim(zy1, zy0)
    az.set_aspect('equal')
    az.set_title('D8 above, D2 below (pads 1.00 x 1.60, 3.70 apart)', fontsize=10)
    az.set_xlabel('x (mm)')
    d2 = [a for a in g['aps'] if a['ref'] == 'D2' and a['pad'] == '2'][0]     # anode, y 65.6
    d8 = [a for a in g['aps'] if a['ref'] == 'D8' and a['pad'] == '2'][0]
    def dim(x, y, text, dx=0, dy=0, ha='left'):
        az.text(x + dx, y + dy, text, fontsize=8, color=BLUE, ha=ha, va='center', zorder=9,
                bbox=dict(fc='white', ec='none', alpha=0.8, pad=0.5))
    dim(46.15, d8['cy'], 'squeegee side 0.80 x 1.10\n(solid blue)', ha='left')
    dim(46.15, d8['cy'] + 1.1, 'pad side 0.90 x 1.20\n(dashed)', ha='left')
    dim(46.15, 62.7 + 0.0, 'pad (gold) 1.00 x 1.60 = paste pad;\nestimate: the paste is about 60-80 %\nof a steel stencil\'s', ha='left')
    az.annotate('', xy=(P['datum_x'], 71.6 - 0.3), xytext=(P['datum_x'] - 0.12, 71.6 - 0.3))
    az.text(42.9, 70.9, 'strip edge x 43.00', fontsize=7.5, ha='right', va='bottom', color=INK, rotation=90)
    az.text(42.88, 57.55, '0.12 clearance', fontsize=7, ha='right', va='top', color=PLA_DARK)
    az.text(45.42, 57.55, '0.12', fontsize=7, ha='left', va='top', color=PLA_DARK)
    fig.suptitle('Light-strip paste stencil, D0.4 file (use view; nothing here has been printed or tried)', fontsize=11, y=0.93)
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
    ax.annotate('x datum: pocket wall\ntouches strip edge x 43.0', xy=(42.88, 118), xytext=(26, 124), fontsize=7.5, color='#b00020', arrowprops=dict(arrowstyle='-', lw=0.6, color='#b00020'))
    ax.annotate('y datum: wall above the\nfoot touches y 135.5', xy=(50, 135.38), xytext=(56.5, 126), fontsize=7.5, color='#b00020', arrowprops=dict(arrowstyle='-', lw=0.6, color='#b00020'))
    fig.savefig(IMG / 'stencil_underside.png', dpi=130, bbox_inches='tight', facecolor='white')
    plt.close(fig)


def section(inp, g, mesh, H):
    ycut = 69.30                                    # D2's cathode pad (y 68.5 to 70.1)
    geom = mesh_rings(mesh, [0, ycut - CY, 0], [0, 1, 0], 1)     # x, z (print frame)
    geom = translate(geom, CX, 0)
    ZX = 10.0
    fig, ax = plt.subplots(figsize=(10.5, 6.2))
    # card: print z -> use z = H - z
    def flip(poly):
        return Polygon([(x, (H - zz) * ZX) for x, zz in poly.exterior.coords], [[(x, (H - zz) * ZX) for x, zz in r.coords] for r in poly.interiors])
    for q in (geom.geoms if hasattr(geom, 'geoms') else [geom]):
        add(ax, flip(q), fc=PLA, ec=PLA_DARK, lw=0.8, zorder=3)
    # FR4 and the strip stack
    meas = D + 0.02                                 # the strip as measured with the liner on, 0.02 over the pocket depth
    liner = meas - 0.385
    layers = [('release liner (measure it\nall: liner on)', 0, liner, '#dddddd', True), ('3M 9077 adhesive 0.05', liner, liner + 0.05, '#c9b27a', False),
              ('PI stiffener 0.225', liner + 0.05, liner + 0.275, '#e6a23c', False), ('flex 0.11 (copper, coverlay)', liner + 0.275, meas, '#2f7d4f', False)]
    rects(ax, [(35, -0.25 * ZX, 52, 0)], fc='#8c7a5b', ec='none', zorder=1)
    ax.text(51.8, -0.2 * ZX, 'FR4 carrier', fontsize=8, ha='right', va='center', color='white')
    for nm, a, b, col, dashed in layers:
        ax.add_patch(Rectangle((43.0, a * ZX), 2.3, (b - a) * ZX, fc=col, ec=INK, lw=0.6, ls='--' if dashed else '-', zorder=2))
    ax.add_patch(Rectangle((43.75, (meas - 0.04) * ZX), 1.0, 0.04 * ZX, fc=GOLD, ec='#7a5a00', lw=0.6, zorder=4))
    ax.text(44.25, (meas + 0.012) * ZX, 'pad', fontsize=7.5, ha='center', va='bottom', color='#7a5a00', zorder=6)
    ax.set_xlim(40.2, 48.3)
    ax.set_ylim(-0.27 * ZX, (H + 0.30) * ZX)
    ax.set_aspect('equal')
    ticks = [0, 0.2, 0.4, 0.6]
    ax.set_yticks([t * ZX for t in ticks if t <= H + 1e-9])
    ax.set_yticklabels([f'{t:.1f}' for t in ticks if t <= H + 1e-9])
    ax.set_ylabel('height above the FR4 (mm), drawn 10 x taller')
    ax.set_xlabel('x (mm), across the bar')
    ax.set_title(f'Section across the bar through D2\'s cathode pad (y 69.30), D{D} file', fontsize=10)
    def lab(x, zz, txt, **kw):
        ax.text(x, zz * ZX, txt, fontsize=7.5, va='center', **kw)
    lab(45.7, liner / 2 - 0.02, 'release liner, stays on (' + f'{liner:.2f}' + f' if the bar measures {meas:.2f})')
    lab(45.7, liner + 0.04, '3M 9077 adhesive 0.05')
    lab(45.7, liner + 0.16, 'PI stiffener 0.225')
    lab(45.7, liner + 0.33, 'flex 0.11')
    lab(46.2, D + 0.1, 'membrane 0.20 = 2 layers\n(layer 1 = squeegee face, layer 2 = pad side)', color=INK)
    lab(40.4, H + 0.04, f'squeegee face, z {H:.1f}', color=INK)
    lab(40.4, D - 0.06, f'z {D:.1f} = pocket depth D:\nthe membrane rests on the strip', color=INK)
    ax.annotate('', xy=(42.88, 0.22 * ZX), xytext=(43.0, 0.22 * ZX), arrowprops=dict(arrowstyle='<->', lw=0.7))
    ax.text(42.8, 0.22 * ZX, '0.12 clearance\neach side', fontsize=7, va='center', ha='right')
    ax.text(44.25, (H + 0.1) * ZX, 'aperture: 0.80 across on the squeegee side,\n0.90 on the pad side', fontsize=7.5, ha='center', va='bottom', color=BLUE)
    ax.text(43.05, -0.12 * ZX, 'x datum: strip edge 43.00', fontsize=7, ha='left', va='center', color='white')
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
        return {z: translate(C.layer_union(layers[z], ox, oy), CX, CY) for z in zs[:2]}
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
                add(ax, a['sq_rect'], fc='none', ec=BLUE, lw=1.2, zorder=5)
                add(ax, a['pd_rect'], fc='none', ec=BLUE, lw=0.9, ls=(0, (2, 1.5)), zorder=5)
        ax.set_xlim(41.0, 47.2)
        ax.set_ylim(71.2, 57.0)
        ax.set_aspect('equal')
        ax.set_title(title, fontsize=9)
        ax.set_xlabel('x (mm)')
    axs[0].set_ylabel('y (mm)')
    fig.suptitle('Sliced toolpath around D8 / D2 (grey = plastic, white = open). Gold = pad, blue = designed aperture.', fontsize=10)
    fig.savefig(IMG / 'stencil_toolpaths.png', dpi=130, bbox_inches='tight', facecolor='white')
    plt.close(fig)


def main():
    IMG.mkdir(parents=True, exist_ok=True)
    inp = S.load_input()
    g = S.geometry(D, inp)
    mesh = trimesh.load(S.OUT / f'light-strip-stencil_D{D}_print.stl')
    overview(inp, g)
    underside(inp, g, mesh, g['H'])
    section(inp, g, mesh, g['H'])
    toolpaths(g)
    for n in ('overview', 'underside', 'section', 'toolpaths'):
        print('wrote docs/images/stencil_%s.png' % n)


if __name__ == '__main__':
    main()
