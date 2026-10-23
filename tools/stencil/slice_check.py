"""Slice the stencil STLs with OrcaSlicer's command line (never its window) and read the G-code back.

Run in the CadQuery venv, after stencil.py:
    <venv>\\Scripts\\python.exe -X utf8 -I tools/stencil/slice_check.py

What it proves, and what it cannot. It proves the TOOLPATH: with the stock Elegoo Centauri Carbon 2 (0.4 nozzle, PLA)
profiles and the overrides below, every one of the 24 apertures is free of any extruded bead (squeegee-size on layer 1,
pad-size on layer 2), the membrane layers are printed, the pocket is empty above the membrane, the datum walls are
printed, nothing floats and there is no support, bridge or ironing. It does NOT prove that the printed holes stay open:
real PLA squishes and oozes, which the slicer does not model. docs/ASSEMBLY.md tells Ian to hold the card to a light.

Presets. Orca's CLI does not resolve profile inheritance for files given on the command line, so the three stock
presets are flattened here from the Elegoo folder alone (indexing every vendor takes minutes). Stock names are kept:
the CLI refuses a renamed machine. G-code goes to build/stencil/slice/ (git-ignored). Output: the table in
docs/reports/stencil_slice_check.md and a 'slice' entry per file in production/stencil/stencil_params.json.
Exit 1 on any failure.
"""
import json
import math
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
import shapely
from shapely.affinity import translate
from shapely.geometry import LineString, Point, box

import stencil as S

ROOT = S.ROOT
OUT = S.OUT
WORK = ROOT / 'build' / 'stencil' / 'slice'
REPORT = ROOT / 'docs' / 'reports' / 'stencil_slice_check.md'
ORCA = Path(r'C:\Program Files\OrcaSlicer\orca-slicer.exe')
PROFILES = Path(r'C:\Program Files\OrcaSlicer\resources\profiles\Elegoo')
PRESETS = {'machine': 'Elegoo Centauri Carbon 2 0.4 nozzle',
           'process': '0.12mm Fine @Elegoo CC2 0.4 nozzle',
           'filament': 'Elegoo PLA @ECC2'}
# the overrides on the stock 0.12 mm Fine profile (PLAN 2.8); the stock elephant-foot compensation is 0.1
OVERRIDES = dict(layer_height='0.1', initial_layer_print_height='0.1', elefant_foot_compensation='0', brim_type='no_brim',
                 brim_width='0', enable_support='0', ironing_type='no ironing', enable_arc_fitting='0',
                 slow_down_layers='2', initial_layer_speed='30')
SKIP_TYPES = ('Skirt', 'Brim', 'Custom')
FORBIDDEN = ('Support', 'Support interface', 'Support transition', 'Bridge', 'Internal bridge', 'Ironing', 'Overhang wall')
BED_CENTRE = (128.0, 128.0)   # the Centauri Carbon 2's bed is 256 x 256
TOL_AREA = 0.002          # mm2 of an aperture that may be covered by a bead (rounding of the bead polygons)
FLOAT_REACH = 0.25        # mm: extrusion further than this from the layer below counts as floating (rounded corners and bead ends
                          # stick out ~0.2 mm over the layer below; that is not an overhang)
TOL_OFFSET = 0.03         # mm: the free interval's centre against the design centre


def index(folders=None):
    """{(kind, name): file} over the given profile folders (default: the Elegoo folder); the first folder that has a name wins."""
    idx = {}
    for folder in (folders or [PROFILES]):
        for kind in ('machine', 'process', 'filament'):
            for f in Path(folder).rglob(f'{kind}/**/*.json'):
                try:
                    d = json.loads(f.read_text(encoding='utf-8'))
                except Exception:
                    continue
                if 'name' in d:
                    idx.setdefault((kind, d['name']), f)
    return idx


def flatten(kind, name, idx):
    d = json.loads(idx[(kind, name)].read_text(encoding='utf-8'))
    parent = d.get('inherits')
    base = flatten(kind, parent, idx) if parent and (kind, parent) in idx else {}
    base.update({k: v for k, v in d.items() if k != 'inherits'})
    return base


def write_presets(dest, overrides, presets=None, folders=None, relative_e_hack=True, rename=None):
    """presets: {'machine': name, 'process': name, 'filament': name}; the default is the stencil's 0.12 Fine (the squeegee passes its own).
    folders: the profile folders to search (default Elegoo only); relative_e_hack: append G92 E0 to the machine's layer gcode (read-back only).
    rename: {kind: new name} for a PROCESS (only): the kit projects must not carry a stock process name, or the OrcaSlicer GUI finds the same-named
    stock preset on opening and resets every value that is not in the (empty) changed-keys list to the stock value."""
    idx = index(folders)
    dest.mkdir(parents=True, exist_ok=True)
    files = {}
    for kind, name in (presets or PRESETS).items():
        d = flatten(kind, name, idx)
        d['name'] = (rename or {}).get(kind, name)         # keep the stock name: the CLI refuses a renamed machine (a renamed process is fine)
        d.pop('instantiation', None)
        if relative_e_hack and kind == 'machine' and 'G92 E0' not in (d.get('layer_gcode') or ''):
            d['layer_gcode'] = ((d.get('layer_gcode') or '') + '\nG92 E0').strip()      # relative-E read-back
        if kind == 'process':
            d.update(overrides)
        p = dest / f'{kind}.json'
        p.write_text(json.dumps(d, indent=1), encoding='utf-8')
        files[kind] = p
    return files


def slice_stl(stl, dest, overrides, presets=None):
    files = write_presets(dest, overrides, presets)
    for old in dest.glob('*.gcode'):
        old.unlink()
    # Placed by us, not by Orca: with --arrange 1 Orca turned the 31 x 107 card by 90 degrees. The STL's XY origin is the
    # card's centre; the copy sent to Orca has it moved to the bed centre, and the read-back subtracts BED_CENTRE again.
    import trimesh
    m = trimesh.load(stl)
    m.apply_translation([BED_CENTRE[0], BED_CENTRE[1], 0])
    placed = dest / 'part.stl'
    m.export(placed)
    cmd = [str(ORCA), '--orient', '0', '--arrange', '0', '--slice', '0', '--load-settings',
           f"{files['machine']};{files['process']}", '--load-filaments', str(files['filament']), '--outputdir', str(dest), str(placed)]
    r = subprocess.run(cmd, capture_output=True, timeout=900, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    g = next(dest.glob('*.gcode'), None)
    if r.returncode or not g:
        raise SystemExit(f'Orca CLI failed ({r.returncode}): {r.stderr.decode(errors="ignore")[-400:]}')
    return g


def parse(gcode):
    """Extrusion segments per layer (x0, y0, x1, y1, width, type), the type of every layer-change, and any arc moves."""
    layers, z, x, y, w, t, rel = {}, 0.0, 0.0, 0.0, 0.4, None, False
    types, arcs = set(), []
    for ln in Path(gcode).read_text(errors='ignore').splitlines():
        if ln.startswith(';Z:'):
            z = round(float(ln[3:]), 3)
        elif ln.startswith(';WIDTH:'):
            w = float(ln[7:])
        elif ln.startswith(';TYPE:'):
            t = ln[6:].strip()
            types.add(t)
        elif ln.startswith('M83'):
            rel = True
        elif ln.startswith(('G1 ', 'G0 ', 'G2 ', 'G3 ')):
            v = {}
            for q in ln.split(';')[0].split()[1:]:
                if q[0] in 'XYZEF' and len(q) > 1:
                    try:
                        v[q[0]] = float(q[1:])
                    except ValueError:
                        pass
            nx, ny = v.get('X', x), v.get('Y', y)
            if ln.startswith(('G2', 'G3')) and t != 'Custom':
                arcs.append((z, t))
            if ln.startswith('G1') and v.get('E', 0) > 0 and (nx, ny) != (x, y) and t not in SKIP_TYPES and t is not None:
                layers.setdefault(z, []).append((x, y, nx, ny, w, t))
            x, y = nx, ny
    assert rel, 'no M83 in the G-code: the read-back assumes relative extrusion'
    return layers, types, arcs


def layer_union(segs, ox, oy):
    """The union of a layer's beads (each segment swept by its width) in the PRINT frame (G-code minus the part's centre)."""
    lines = shapely.linestrings(np.array([[(s[0] - ox, s[1] - oy), (s[2] - ox, s[3] - oy)] for s in segs]))
    widths = np.array([s[4] / 2 for s in segs])
    # the beads of one layer share a few widths; buffer per width so the union stays quick
    parts = []
    for wd in np.unique(np.round(widths, 3)):
        sel = np.abs(widths - wd) < 1e-3
        parts.append(shapely.union_all(shapely.buffer(lines[sel], wd, quad_segs=6)))
    u = shapely.union_all(parts)
    shapely.prepare(u)
    return u


def free_interval(U, cx, cy, axis, reach=2.0):
    """Length and centre offset of the bead-free stretch of a line through (cx, cy) along x or y."""
    p = Point(cx, cy)
    line = LineString([(cx - reach, cy), (cx + reach, cy)]) if axis == 'x' else LineString([(cx, cy - reach), (cx, cy + reach)])
    rest = line.difference(U)
    if rest.is_empty:
        return 0.0, None
    parts = list(rest.geoms) if hasattr(rest, 'geoms') else [rest]
    best = min(parts, key=lambda q: q.distance(p))
    if best.distance(p) > 1e-9:
        return 0.0, None
    c = best.centroid
    return best.length, (c.x - cx if axis == 'x' else c.y - cy)


def analyse(gcode, D, g, label, parsed=None, centre=None, float_tol=0.01):
    """Read one G-code back against the design. Returns (result dict, list of failure strings).
    parsed: (layers, types, arcs) already cut down to this one card (make_plate.py reads three cards off one plate); the header of
    `gcode` still supplies the settings; centre: where the card was put on the bed (default BED_CENTRE); float_tol: the mm2 of
    extrusion with nothing under it that fails a layer (0.01 for the single card, which reads 0.000-0.01)."""
    P = S.PARAMS
    H = g['H']
    layers, types, arcs = parsed if parsed else parse(gcode)
    fails = []
    zs = sorted(layers)
    want = [round(0.1 * (i + 1), 3) for i in range(int(round(H / 0.1)))]
    if zs != want:
        fails.append(f'layers {zs}, expected {want}')
    x0, x1, y0, y1 = P['card']
    xs = [c for s in layers[zs[0]] for c in (s[0], s[2])]
    ys = [c for s in layers[zs[0]] for c in (s[1], s[3])]
    # the part's centre on the bed: the centre of the first layer's extrusion box (a symmetric card, no brim). The G-code
    # frame is the model frame minus the machine's extruder_offset (0 x 1.5 on the Centauri Carbon 2), so the part reads 1.5 mm off in y; it is read, not assumed; it must stay near
    ox, oy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    ext = (max(xs) - min(xs), max(ys) - min(ys))
    centre = centre or BED_CENTRE
    if abs(ox - centre[0]) > 5 or abs(oy - centre[1]) > 5:
        fails.append(f'first layer centred at ({ox:.3f}, {oy:.3f}), the part was placed at {centre}')
    if abs(ext[0] - (x1 - x0)) > 0.6 or abs(ext[1] - (y1 - y0)) > 0.6:
        fails.append(f'first-layer extent {ext[0]:.2f} x {ext[1]:.2f}, model {x1 - x0} x {y1 - y0}')
    U = {z: layer_union(layers[z], ox, oy) for z in zs}
    shift = lambda geom: translate(geom, -(x0 + x1) / 2, -(y0 + y1) / 2)           # KiCad frame -> print frame (S.to_print)

    # --- apertures: squeegee size on layer 1, pad size on layer 2 ---
    rows, minw = [], 9.0
    worst_cover, worst_off = 0.0, 0.0
    for a in g['aps']:
        row = dict(ref=f"{a['ref']}.{a['pad']}")
        for li, (key, size) in enumerate((('sq_rect', a['sq']), ('pd_rect', a['pd']))):
            z = zs[li]
            rect = shift(a[key])
            covered = U[z].intersection(rect).area
            worst_cover = max(worst_cover, covered)
            if covered > TOL_AREA:
                fails.append(f"{row['ref']} layer {li + 1}: {covered:.4f} mm2 of the aperture is covered by a bead")
            cx, cy = rect.centroid.x, rect.centroid.y
            # expected centre: the pad centre minus (clear, clear), in the print frame (pushing the card home adds it back)
            wx_, wy_ = shift(a['pad_poly']).centroid.x - S.PARAMS['clear'], shift(a['pad_poly']).centroid.y - S.PARAMS['clear']
            if abs(cx - wx_) > 0.005 or abs(cy - wy_) > 0.005:
                fails.append(f"{row['ref']} layer {li + 1}: aperture centre ({cx:.3f}, {cy:.3f}) is not pad - (clear, clear) = ({wx_:.3f}, {wy_:.3f})")
            for ax, want_w in (('x', size[0]), ('y', size[1])):
                wd, off = free_interval(U[z], cx, cy, ax)
                minw = min(minw, wd)
                row[f'L{li + 1}{ax}'] = round(wd, 3)
                if wd < want_w - 0.02:
                    fails.append(f"{row['ref']} layer {li + 1}: open width in {ax} is {wd:.3f}, design {want_w:.3f}")
                if off is not None:
                    worst_off = max(worst_off, abs(off))
                    if abs(off) > TOL_OFFSET:
                        fails.append(f"{row['ref']} layer {li + 1}: the open stretch in {ax} is {off:+.3f} off the design centre")
        rows.append(row)

    # --- membrane layers printed: coverage of the membrane area (pocket minus the apertures) ---
    pocket = shift(g['pocket'].intersection(box(x0, y0, x1, y1)))
    holes = [shift(a['pd_rect']) for a in g['aps']]
    mem_area = pocket.buffer(-0.1).difference(shapely.union_all(holes).buffer(0.15))
    cover = []
    for z in zs[:2]:
        cover.append(U[z].intersection(mem_area).area / mem_area.area)
        if cover[-1] < 0.97:
            fails.append(f'membrane layer z={z}: only {cover[-1]:.1%} of the membrane area is printed')
    # layer 1 over the whole card (minus the squeegee openings)
    card_area = shift(g['card']).buffer(-0.5)
    c1 = U[zs[0]].intersection(card_area.difference(shapely.union_all([shift(a['sq_rect']) for a in g['aps']]).buffer(0.1))).area / \
        card_area.difference(shapely.union_all([shift(a['sq_rect']) for a in g['aps']]).buffer(0.1)).area
    if c1 < 0.97:
        fails.append(f'layer 1 covers only {c1:.1%} of the card')

    # --- pocket empty above the membrane ---
    inner = pocket.buffer(-0.05)
    pocket_cov = 0.0
    for z in zs[2:]:
        a_ = U[z].intersection(inner).area
        pocket_cov = max(pocket_cov, a_)
        if a_ > 0.01:
            fails.append(f'z={z}: {a_:.3f} mm2 of extrusion inside the pocket')

    # --- datum walls (x wall along the bar, y wall above the foot), printed in every layer above the membrane ---
    gy, gw, gd = P['groove']
    wall = []
    for z in zs[2:]:
        z_use_mid = H - (z - 0.05)
        in_groove = z_use_mid < gd
        miss_x = miss_y = n_x = n_y = 0
        for y in np.arange(41.0, 134.01, 1.0):
            if in_groove and gy - gw / 2 - 0.3 <= y <= gy + gw / 2 + 0.3:
                continue
            n_x += 1
            px, py = S.to_print(P['datum_x'] - P['clear'] - 0.05, y)
            miss_x += not U[z].contains(Point(px, py))
        for x in np.arange(47.0, 53.01, 1.0):
            n_y += 1
            px, py = S.to_print(x, P['datum_y'] - P['clear'] - 0.05)
            miss_y += not U[z].contains(Point(px, py))
        wall.append((z, n_x - miss_x, n_x, n_y - miss_y, n_y))
        if miss_x or miss_y:
            fails.append(f'z={z}: datum wall gaps (x wall {n_x - miss_x}/{n_x}, y wall {n_y - miss_y}/{n_y})')

    # --- floating: extrusion on a layer with nothing under it ---
    float_area = 0.0
    for i in range(1, len(zs)):
        under = U[zs[i - 1]].buffer(FLOAT_REACH)
        fa = U[zs[i]].difference(under).area
        float_area = max(float_area, fa)
        if fa > float_tol:
            fails.append(f'z={zs[i]}: {fa:.3f} mm2 of extrusion has nothing under it')

    # --- forbidden roles and arcs ---
    bad = sorted(types & set(FORBIDDEN))
    if bad:
        fails.append('forbidden line types in the G-code: ' + ', '.join(bad))
    if arcs:
        fails.append(f'{len(arcs)} G2/G3 arc moves outside ;TYPE:Custom (first at z={arcs[0][0]}, {arcs[0][1]})')

    head = Path(gcode).read_text(errors='ignore')
    info = {}
    for key, pat in {'time': r'estimated printing time \(normal mode\) = (.+)', 'grams': r'total filament used \[g\] = ([\d.]+)',
                     'efc': r'; elefant_foot_compensation = (\S+)', 'layer_height': r'; layer_height = (\S+)',
                     'first_layer_height': r'; initial_layer_print_height = (\S+)'}.items():
        m = re.search(pat, head)
        info[key] = m.group(1).strip() if m else None
    n_open = len(rows) - len([r for r in rows if any(f.startswith(r['ref'] + ' ') for f in fails)])
    res = dict(label=label, layers=zs, types=sorted(types), n_apertures=n_open, min_open_width=round(minw, 3),
               worst_cover_mm2=round(worst_cover, 5), worst_offset=round(worst_off, 3), membrane_cover=[round(c, 3) for c in cover],
               layer1_card_cover=round(c1, 3), pocket_max_cover_mm2=round(pocket_cov, 4), float_max_mm2=round(float_area, 4),
               datum=wall, first_layer_extent=[round(e, 2) for e in ext], rows=rows, **info)
    return res, fails


def efc_growth(gcode, g):
    """Info only: how much the layer-1 apertures grow per side with the stock elephant-foot compensation."""
    layers, _, _ = parse(gcode)
    zs = sorted(layers)
    xs = [c for s in layers[zs[0]] for c in (s[0], s[2])]
    ys = [c for s in layers[zs[0]] for c in (s[1], s[3])]
    ox, oy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    U = layer_union(layers[zs[0]], ox, oy)
    grow = []
    for a in g['aps']:
        r = translate(a['sq_rect'], -(S.PARAMS['card'][0] + S.PARAMS['card'][1]) / 2, -(S.PARAMS['card'][2] + S.PARAMS['card'][3]) / 2)
        wx, _ = free_interval(U, r.centroid.x, r.centroid.y, 'x')
        wy, _ = free_interval(U, r.centroid.x, r.centroid.y, 'y')
        grow.append(((wx - a['sq'][0]) / 2, (wy - a['sq'][1]) / 2))
    gx = float(np.mean([q[0] for q in grow]))
    gy = float(np.mean([q[1] for q in grow]))
    return gx, gy


def main():
    WORK.mkdir(parents=True, exist_ok=True)
    allres, allfails = {}, []
    params_path = OUT / 'stencil_params.json'
    params = json.loads(params_path.read_text(encoding='utf-8'))
    for D in S.PARAMS['depths']:
        stl = OUT / f'light-strip-stencil_D{D}_print.stl'
        g = S.geometry(D)
        gcode = slice_stl(stl, WORK / f'D{D}', OVERRIDES)
        res, fails = analyse(gcode, D, g, f'D{D}')
        allres[D] = res
        allfails += [f'D{D}: {f}' for f in fails]
        print(f"D{D}: layers {len(res['layers'])}, apertures open L1+L2 {res['n_apertures']}/24 (worst bead cover {res['worst_cover_mm2']} mm2, "
              f"min open width {res['min_open_width']}, worst off-centre {res['worst_offset']}), membrane cover {res['membrane_cover']}, "
              f"pocket cover {res['pocket_max_cover_mm2']}, floating {res['float_max_mm2']}, {res['time']}, {res['grams']} g, "
              f"{'PASS' if not fails else 'FAIL'}")
        for f in fails:
            print('   -', f)
        params['files'][f'D{D}']['slice'] = dict(time=res['time'], grams=res['grams'], layers=len(res['layers']),
                                                  min_open_width_mm=res['min_open_width'], apertures_open=f"{res['n_apertures']}/24",
                                                  pass_=not fails)

    # info only: the stock elephant-foot compensation, D0.4
    stock = dict(OVERRIDES, elefant_foot_compensation='0.1')
    g04 = S.geometry(0.4)
    gcode = slice_stl(OUT / 'light-strip-stencil_D0.4_print.stl', WORK / 'D0.4_efc01', stock)
    gx, gy = efc_growth(gcode, g04)
    print(f'info: with the stock elephant-foot compensation 0.1, layer-1 apertures open by {gx:+.3f} (x) and {gy:+.3f} (y) per side')
    params['slice_info'] = dict(stock_efc_0p1_layer1_growth_per_side_mm=dict(x=round(gx, 3), y=round(gy, 3)))
    params_path.write_text(json.dumps(params, indent=1), encoding='utf-8')
    write_report(allres, gx, gy, allfails)
    if allfails:
        print('FAIL')
        sys.exit(1)
    print('PASS: all three files read back clean; report in', REPORT.relative_to(ROOT))


def write_report(res, gx, gy, fails):
    L = ['# Stencil slice check', '',
         'Generated by `tools/stencil/slice_check.py` (OrcaSlicer command line, stock Elegoo Centauri Carbon 2 0.4 nozzle and Elegoo PLA profiles, '
         'overrides below). It reads the sliced G-code back against the design. **It checks the toolpath only: the slicer keeps the '
         'apertures open, but whether the printed holes stay open is not modelled (see `docs/ASSEMBLY.md`).** Nothing here has been printed.', '',
         '| | ' + ' | '.join(f'D{D}' for D in res) + ' |', '|---|' + '---|' * len(res)]
    def row(name, f):
        L.append(f'| {name} | ' + ' | '.join(f(r) for r in res.values()) + ' |')
    row('Layers (z, mm)', lambda r: f"{len(r['layers'])} (0.1 to {r['layers'][-1]})")
    row('Apertures free of any bead, layer 1 (squeegee size) and layer 2 (pad size)', lambda r: f"{r['n_apertures']}/24 (worst bead cover {r['worst_cover_mm2']} mm2)")
    row('Smallest open width through an aperture centre (mm)', lambda r: f"{r['min_open_width']}")
    row('Worst open-stretch offset from the design centre (mm)', lambda r: f"{r['worst_offset']}")
    row('Membrane area printed, layers 1 and 2', lambda r: ' / '.join(f'{c:.1%}' for c in r['membrane_cover']))
    row('Extrusion inside the pocket above the membrane (mm2)', lambda r: f"{r['pocket_max_cover_mm2']}")
    row('Floating extrusion, worst layer (mm2)', lambda r: f"{r['float_max_mm2']}")
    row('Datum walls printed (x wall / y wall, every layer above the membrane)',
        lambda r: 'all' if all(w[1] == w[2] and w[3] == w[4] for w in r['datum']) else 'GAPS')
    row('Line types in the G-code', lambda r: ', '.join(r['types']))
    row('Print time (slicer estimate)', lambda r: r['time'])
    row('Filament (g)', lambda r: r['grams'])
    row('Result', lambda r: 'PASS' if not any(f.startswith(r['label'] + ':') for f in fails) else 'FAIL')
    L += ['', '**Overrides on the stock "0.12mm Fine @Elegoo CC2 0.4 nozzle" process:** ' + ', '.join(f'`{k}` = {v}' for k, v in OVERRIDES.items()) + '.', '',
          f'**Elephant-foot compensation (info only):** with the stock value 0.1 instead of 0, the slicer opens every layer-1 (squeegee side) aperture by '
          f'{gx:+.3f} mm (across) and {gy:+.3f} mm (along) per side. That is the wrong taper for paste release and puts down more paste, so the process '
          'must have it at 0.', '',
          'Method: apertures are tested by sweeping every extrusion segment by its `;WIDTH` and intersecting with the aperture rectangle (squeegee size on layer 1, pad size on layer 2); '
          'the part is placed at the bed centre by this script (with Orca\'s own arrange it turned the card by 90 degrees) and its position is then read from the centre of the first layer\'s extrusion bounding box (the G-code frame is the model frame minus the Centauri Carbon 2 profile\'s 1.5 mm extruder offset in y, so the part reads 1.5 mm off where it was put), so the read-back does not depend on where Orca puts it. The pocket is tested against its outline shrunk by 0.05 mm. '
          '"Floating" is extrusion further than 0.25 mm from any bead of the layer below (bead ends and corners overhang by up to about 0.2 mm without being a problem). Failing lines are `Support`, `Bridge`, `Ironing`, `Overhang wall` and any G2/G3 arc outside the end G-code.']
    if fails:
        L += ['', '## Failures', ''] + [f'- {f}' for f in fails]
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text('\n'.join(L) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
