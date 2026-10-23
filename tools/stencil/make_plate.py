"""Build the print-ready OrcaSlicer projects for the stencil kit: the three stencil cards (D0.3, D0.4, D0.5), the squeegee handle with its
two PLA blades and the aperture coupon, all on ONE plate, and read each project back from a command-line slice.

Run in the CadQuery venv (cadquery, shapely, trimesh), after stencil.py and squeegee.py (it reads their STLs from production/stencil/):
    <venv>\\Scripts\\python.exe -X utf8 -I tools/stencil/make_plate.py              # both projects, then the read-back and the report
    <venv>\\Scripts\\python.exe -X utf8 -I tools/stencil/make_plate.py --only cc2   # one of them (generic, cc2)

Writes production/stencil/stencil-kit_generic.3mf (Generic Marlin Printer 0.4 nozzle, Generic PLA; the parts sit inside a 220 x 210 mm area)
and production/stencil/stencil-kit_cc2.3mf (Elegoo Centauri Carbon 2 0.4 nozzle, Elegoo PLA), plus docs/reports/stencil_plate_check.md and
docs/images/stencil_plate.png. Scratch files go to build/stencil/plate/ (git-ignored). OrcaSlicer's command line only, never its window.

Why the projects are written by OrcaSlicer. A 3MF written by hand without OrcaSlicer's full project settings (no filament_colour, for
one) crashes OrcaSlicer 2.3.2 and later when it is opened. So this script never writes project settings: it places the STLs itself (the
positions are decided here, then read back from the 3MF), lets `orca-slicer --export-3mf` write the project with the real presets, adds only the
squeegee's own per-object print settings (3 walls, Arachne) to the object list, and lets OrcaSlicer read and write the file once more.

Process on the whole plate: the 0.12 mm Fine process of the machine with 0.10 mm layers and first layer, elephant-foot compensation 0 (the stencil
openings need it), no brim, no supports, no ironing, no arc fitting, two slow layers and a 30 mm/s first layer (slice_check.OVERRIDES).

Read-back (exit 1 on any failure): the 3MF (every part present, mesh equal to its STL, not rotated, at the planned place, per-object settings,
the project settings and their key set against an OrcaSlicer round trip), and one command-line slice of the finished file (all 3 x 24 stencil
openings clear on layers 1 and 2, the membranes, the squeegee read back by squeegee.read_back with no floating island, the coupon, no support /
brim / ironing / arcs, the plate inside its bed, time and grams).
"""
import argparse
import hashlib
import json
import math
import re
import subprocess
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import trimesh
import shapely
from shapely.affinity import translate
from shapely.geometry import box

import slice_check as C
import squeegee as SQM
import stencil as S

ROOT = S.ROOT
OUT = S.OUT
WORK = ROOT / 'build' / 'stencil' / 'plate'
REPORT = ROOT / 'docs' / 'reports' / 'stencil_plate_check.md'
IMAGE = ROOT / 'docs' / 'images' / 'stencil_plate.png'
RES = Path(r'C:\Program Files\OrcaSlicer\resources\profiles')

# ---- the plate (mm) ----------------------------------------------------------------------------------------------------
GAP_CARDS = 6.0          # between neighbouring stencil cards
GAP_COLUMN = 10.0        # between the cards and the squeegee / coupon column, and between those two
# the parts: object name in the project (it is the file name OrcaSlicer is given), the STL, the kind, the depth if a stencil
PARTS = [dict(name='stencil-D0.3', stl='light-strip-stencil_D0.3_print.stl', kind='stencil', D=0.3),
         dict(name='stencil-D0.4', stl='light-strip-stencil_D0.4_print.stl', kind='stencil', D=0.4),
         dict(name='stencil-D0.5', stl='light-strip-stencil_D0.5_print.stl', kind='stencil', D=0.5),
         dict(name='squeegee-handle-and-2-blades', stl='squeegee_print.stl', kind='squeegee'),
         dict(name='aperture-coupon', stl='aperture-coupon_print.stl', kind='coupon')]
# the process overrides of the whole plate: the stencil cards' (slice_check.OVERRIDES) plus the classic wall generator, which is what the
# stock Elegoo 0.12 mm Fine process uses and what the card read-back was done with (a generic process defaults to Arachne, whose variable bead
# widths put slivers into the 0.8 x 1.1 mm openings); the squeegee gets Arachne as its own object setting
OVERRIDES = dict(C.OVERRIDES, wall_generator='classic')
# per-object settings of the squeegee (its own wishes; the stencil cards keep the process's); OrcaSlicer's keys
SQUEEGEE_OBJECT = {'wall_loops': '3', 'wall_generator': 'arachne'}

VARIANTS = {
    'generic': dict(file='stencil-kit_generic.3mf', title='Generic Marlin Printer 0.4 nozzle, Generic PLA',
                    folders=['Custom', 'OrcaFilamentLibrary'],
                    presets={'machine': 'MyMarlin 0.4 nozzle', 'process': '0.12mm Fine @MyMarlin', 'filament': 'Generic PLA @System'},
                    area=(220.0, 210.0)),
    'cc2': dict(file='stencil-kit_cc2.3mf', title='Elegoo Centauri Carbon 2 0.4 nozzle, Elegoo PLA',
                folders=['Elegoo', 'OrcaFilamentLibrary'],
                presets={'machine': 'Elegoo Centauri Carbon 2 0.4 nozzle', 'process': '0.12mm Fine @Elegoo CC2 0.4 nozzle', 'filament': 'Elegoo PLA @ECC2'},
                area=(256.0, 256.0)),
}
# a card's extrusion with nothing under it, per layer, that still passes: a few bead-end slivers of 0.03-0.07 mm2 (about 0.15 x 0.3 mm) sit on the
# top layers of the card on the generic printer's toolpath; the single-card check keeps 0.01
FLOAT_TOL = 0.1
FORBIDDEN_PLATE = ('Support', 'Support interface', 'Support transition', 'Ironing', 'Skirt', 'Brim')


def orca(args, cwd):
    """Run OrcaSlicer's command line (no window), return the CompletedProcess."""
    r = subprocess.run([str(C.ORCA)] + [str(a) for a in args], capture_output=True, timeout=1200, cwd=str(cwd),
                       creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    if r.returncode:
        raise SystemExit(f'Orca CLI failed ({r.returncode}): {r.stderr.decode(errors="ignore")[-600:]}{r.stdout.decode(errors="ignore")[-600:]}')
    return r


# ---------------------------------------------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------------------------------------------
def layout(area):
    """Positions of the five parts as the centre of each STL's xy bounding box on the bed. The whole group is centred in `area`
    (a box from the bed's origin corner). Returns a list of part dicts with the mesh, the target centre and the STL-frame origin on the bed."""
    parts = []
    for p in PARTS:
        m = trimesh.load(OUT / p['stl'])
        b = m.bounds
        parts.append(dict(p, mesh=m, size=(float(b[1][0] - b[0][0]), float(b[1][1] - b[0][1])), height=float(b[1][2]), centre0=(float((b[0][0] + b[1][0]) / 2), float((b[0][1] + b[1][1]) / 2))))
    x = 0.0
    centres = {}
    for p in parts:
        if p['kind'] == 'stencil':
            centres[p['name']] = (x + p['size'][0] / 2, 0.0)
            x += p['size'][0] + GAP_CARDS
    x_col = x - GAP_CARDS + GAP_COLUMN
    col = [p for p in parts if p['kind'] != 'stencil']
    colw = max(p['size'][0] for p in col)
    total_h = sum(p['size'][1] for p in col) + GAP_COLUMN * (len(col) - 1)
    y = total_h / 2
    for p in col:                                             # the squeegee at the top, the coupon below it
        centres[p['name']] = (x_col + colw / 2, y - p['size'][1] / 2)
        y -= p['size'][1] + GAP_COLUMN
    # bounding box of the group, centred in the area
    x0 = min(centres[p['name']][0] - p['size'][0] / 2 for p in parts)
    x1 = max(centres[p['name']][0] + p['size'][0] / 2 for p in parts)
    y0 = min(centres[p['name']][1] - p['size'][1] / 2 for p in parts)
    y1 = max(centres[p['name']][1] + p['size'][1] / 2 for p in parts)
    dx, dy = area[0] / 2 - (x0 + x1) / 2, area[1] / 2 - (y0 + y1) / 2
    for p in parts:
        cx, cy = centres[p['name']]
        p['target'] = (round(cx + dx, 3), round(cy + dy, 3))
        p['origin'] = (p['target'][0] - p['centre0'][0], p['target'][1] - p['centre0'][1])      # the STL frame's origin on the bed
        p['bbox'] = (p['target'][0] - p['size'][0] / 2, p['target'][1] - p['size'][1] / 2, p['target'][0] + p['size'][0] / 2, p['target'][1] + p['size'][1] / 2)
    return parts, (x1 - x0, y1 - y0)


# ---------------------------------------------------------------------------------------------------------------
# The 3MF (read only: OrcaSlicer writes it)
# ---------------------------------------------------------------------------------------------------------------
NS = {'m': 'http://schemas.microsoft.com/3dmanufacturing/core/2015/02', 'p': 'http://schemas.microsoft.com/3dmanufacturing/production/2015/06'}


def read_3mf(path):
    """{'parts': [{name, bbox, volume, triangles, rotated, extra}], 'settings': project_settings dict, 'objects_xml': text}."""
    z = zipfile.ZipFile(path)
    model = ET.fromstring(z.read('3D/3dmodel.model'))
    ms = ET.fromstring(z.read('Metadata/model_settings.config'))
    names, extra = {}, {}
    for o in ms.findall('object'):
        oid = o.get('id')
        extra[oid] = {}
        for md in o.findall('metadata'):
            if md.get('key') == 'name':
                names[oid] = md.get('value')
            elif md.get('key') != 'extruder':
                extra[oid][md.get('key')] = md.get('value')
    items = {it.get('objectid'): [float(v) for v in it.get('transform').split()] for it in model.find('m:build', NS).findall('m:item', NS)}
    parts = []
    for o in model.find('m:resources', NS).findall('m:object', NS):
        comp = o.find('m:components', NS)
        if comp is None:
            continue
        oid = o.get('id')
        c = comp.find('m:component', NS)
        ct = [float(v) for v in c.get('transform').split()]
        it = items[oid]
        pth = c.get('{%s}path' % NS['p']).lstrip('/')
        sub = ET.fromstring(z.read(pth))
        mesh_obj = next(x for x in sub.find('m:resources', NS).findall('m:object', NS) if x.get('id') == c.get('objectid'))
        verts = np.array([[float(v.get(k)) for k in 'xyz'] for v in mesh_obj.find('m:mesh', NS).find('m:vertices', NS)])
        tris = np.array([[int(t.get(k)) for k in ('v1', 'v2', 'v3')] for t in mesh_obj.find('m:mesh', NS).find('m:triangles', NS)])
        rot = np.array(ct[:9]).reshape(3, 3) @ np.array(it[:9]).reshape(3, 3)
        t = np.array(ct[9:12]) + np.array(it[9:12])
        world = verts @ rot + t
        m = trimesh.Trimesh(world, tris, process=False)
        parts.append(dict(name=names[oid], bbox=m.bounds.copy(), volume=float(m.volume), triangles=len(tris),
                          rotated=not np.allclose(rot, np.eye(3), atol=1e-6), extra=extra[oid]))
    return dict(parts=parts, settings=json.loads(z.read('Metadata/project_settings.config')), zip=z)


def patch_objects(src, dst, per_object):
    """Copy a 3MF OrcaSlicer wrote, adding per-object settings ({object name: {key: value}}) to Metadata/model_settings.config and nothing else."""
    zin = zipfile.ZipFile(src)
    with zipfile.ZipFile(dst, 'w', zipfile.ZIP_DEFLATED) as zo:
        for it in zin.infolist():
            data = zin.read(it.filename)
            if it.filename == 'Metadata/model_settings.config':
                s = data.decode('utf-8')
                for name, kv in per_object.items():
                    pat = re.compile(r'(<object id="\d+">\s*<metadata key="name" value="%s"/>\s*<metadata key="extruder" value="\d+"/>)' % re.escape(name))
                    assert len(pat.findall(s)) == 1, f'object {name} not found once in model_settings.config'
                    add = ''.join(f'\n    <metadata key="{k}" value="{v}"/>' for k, v in kv.items())
                    s = pat.sub(lambda mo: mo.group(1) + add, s)
                data = s.encode('utf-8')
            zo.writestr(it, data)


# ---------------------------------------------------------------------------------------------------------------
# Build one project
# ---------------------------------------------------------------------------------------------------------------
def build_project(key, V, reuse=False):
    d = WORK / key
    stl_dir = d / 'stl'
    stl_dir.mkdir(parents=True, exist_ok=True)
    if not reuse:
        for old in list(d.glob('*.3mf')) + list(d.glob('*.gcode')):
            old.unlink()
    folders = [RES / f for f in V['folders']]
    files = C.write_presets(d / 'presets', OVERRIDES, V['presets'], folders=folders, relative_e_hack=False)
    parts, extent = layout(V['area'])
    for p in parts:
        m = p['mesh'].copy()
        m.apply_translation([p['origin'][0], p['origin'][1], 0])
        assert abs(m.bounds[0][2]) < 1e-9
        p['placed'] = stl_dir / (p['name'] + '.stl')
        m.export(p['placed'])
    if reuse and (d / V['file']).exists():
        return dict(dir=d, final=d / V['file'], parts=parts, extent=extent, files=files)
    # pass 1: OrcaSlicer loads the five STLs with the presets and writes the project (full project settings)
    orca(['--orient', '0', '--arrange', '0', '--load-settings', f"{files['machine']};{files['process']}", '--load-filaments', files['filament'],
          '--export-3mf', 'pass1.3mf', '--outputdir', d] + [p['placed'] for p in parts], d)
    # pass 2: the squeegee's own settings, as per-object settings on the object list only
    patch_objects(d / 'pass1.3mf', d / 'pass2.3mf', {next(p['name'] for p in parts if p['kind'] == 'squeegee') + '.stl': SQUEEGEE_OBJECT})
    # pass 3: OrcaSlicer reads that and writes the final project
    orca(['--orient', '0', '--arrange', '0', '--export-3mf', V['file'], '--outputdir', d, 'pass2.3mf'], d)
    final = d / V['file']
    return dict(dir=d, final=final, parts=parts, extent=extent, files=files)


# ---------------------------------------------------------------------------------------------------------------
# Read-back
# ---------------------------------------------------------------------------------------------------------------
class Check:
    def __init__(self):
        self.fails, self.rows = [], []

    def __call__(self, cond, msg, ok=None):
        if not cond:
            self.fails.append(msg)
        elif ok:
            self.rows.append(ok)
        return cond


def read_back_3mf(b, V, chk):
    """The project file against the plan. Returns a dict for the report."""
    info = read_3mf(b['final'])
    parts = {p['name'] + '.stl': p for p in b['parts']}
    chk(len(info['parts']) == len(PARTS), f"the project has {len(info['parts'])} objects, expected {len(PARTS)}")
    worst_pos, worst_vol = 0.0, 0.0
    for q in info['parts']:
        p = parts.get(q['name'])
        if not chk(p is not None, f"unexpected object {q['name']}"):
            continue
        want = np.array([p['bbox'][0], p['bbox'][1], 0.0, p['bbox'][2], p['bbox'][3], p['height']]).reshape(2, 3)
        err = float(np.abs(q['bbox'] - want).max())
        worst_pos = max(worst_pos, err)
        chk(err < 0.01, f"{q['name']}: bounding box in the project differs from the plan by {err:.3f} mm ({q['bbox'].tolist()} against {want.tolist()})")
        chk(not q['rotated'], f"{q['name']}: the object is rotated in the project")
        v_err = abs(q['volume'] - p['mesh'].volume) / p['mesh'].volume
        worst_vol = max(worst_vol, v_err)
        chk(v_err < 1e-3, f"{q['name']}: mesh volume {q['volume']:.2f} against the STL's {p['mesh'].volume:.2f}")
        chk(abs(q['bbox'][0][2]) < 1e-6, f"{q['name']}: the object does not sit on the bed (z {q['bbox'][0][2]})")
        # per-object settings: exactly the squeegee's
        wanted = SQUEEGEE_OBJECT if p['kind'] == 'squeegee' else {}
        chk(q['extra'] == wanted, f"{q['name']}: per-object settings {q['extra']}, expected {wanted}")
    # fits: the bed of the preset, and the area it is meant for
    allb = np.array([q['bbox'] for q in info['parts']])
    lo, hi = allb[:, 0, :2].min(axis=0), allb[:, 1, :2].max(axis=0)
    st = info['settings']
    pa = [tuple(float(c) for c in s.split('x')) for s in st['printable_area']]
    bed = (max(a[0] for a in pa), max(a[1] for a in pa))
    chk(lo[0] >= 0 and lo[1] >= 0 and hi[0] <= bed[0] and hi[1] <= bed[1], f'plate {lo.tolist()}..{hi.tolist()} outside the bed {bed}')
    chk(lo[0] >= 0 and lo[1] >= 0 and hi[0] <= V['area'][0] and hi[1] <= V['area'][1], f"plate {lo.tolist()}..{hi.tolist()} outside {V['area']}")
    # settings
    for k, v in dict(layer_height='0.1', initial_layer_print_height='0.1', elefant_foot_compensation='0', brim_type='no_brim', enable_support='0',
                     ironing_type='no ironing', enable_arc_fitting='0', slow_down_layers='2', initial_layer_speed='30', wall_generator='classic').items():
        chk(str(st.get(k)) == v, f'project setting {k} = {st.get(k)!r}, expected {v!r}')
    chk('filament_colour' in st and st['filament_colour'], 'project settings have no filament_colour')
    chk(st.get('print_settings_id') == V['presets']['process'] and st.get('printer_settings_id') == V['presets']['machine'] and
        st.get('filament_settings_id') == [V['presets']['filament']], f"preset names in the project: {st.get('print_settings_id')}, {st.get('printer_settings_id')}, {st.get('filament_settings_id')}")
    return dict(info=info, lo=lo, hi=hi, bed=bed, worst_pos=worst_pos, worst_vol=worst_vol)


def settings_round_trip(b, V, chk):
    """OrcaSlicer reads the finished project and writes it again: the project settings must come out the same (key set and values), and the
    key set must equal that of a plain export of the same presets without any project (the reference for 'the full key set')."""
    d = b['dir']
    orca(['--orient', '0', '--arrange', '0', '--export-3mf', 'roundtrip.3mf', '--outputdir', d, b['final']], d)
    a = read_3mf(b['final'])
    r = read_3mf(d / 'roundtrip.3mf')
    chk(a['settings'] == r['settings'], 'project settings change in an OrcaSlicer round trip: ' + ', '.join(k for k in a['settings'] if a['settings'].get(k) != r['settings'].get(k))[:300])
    chk([q['extra'] for q in sorted(a['parts'], key=lambda q: q['name'])] == [q['extra'] for q in sorted(r['parts'], key=lambda q: q['name'])], 'per-object settings change in the round trip')
    # the references: one STL, the same presets, exported by OrcaSlicer: once with the same overrides (the key set must be the same) and once
    # without any (which values the overrides change)
    refs = {}
    for tag, ov in (('ref', OVERRIDES), ('stock', {})):
        ref_dir = d / tag
        ref_dir.mkdir(exist_ok=True)
        files = C.write_presets(ref_dir, ov, V['presets'], folders=[RES / f for f in V['folders']], relative_e_hack=False)
        cube = ref_dir / 'cube.stl'
        trimesh.creation.box(extents=[10, 10, 10]).export(cube)
        orca(['--orient', '0', '--arrange', '1', '--load-settings', f"{files['machine']};{files['process']}", '--load-filaments', files['filament'],
              '--export-3mf', 'ref0.3mf', '--outputdir', ref_dir, cube], ref_dir)
        # read and written once more, as the finished project is: OrcaSlicer adds keys of its own on loading a project (upward_compatible_machine)
        orca(['--orient', '0', '--arrange', '0', '--export-3mf', 'ref.3mf', '--outputdir', ref_dir, ref_dir / 'ref0.3mf'], ref_dir)
        refs[tag] = read_3mf(ref_dir / 'ref.3mf')['settings']
    missing = sorted(set(refs['ref']) - set(a['settings']))
    extra = sorted(set(a['settings']) - set(refs['ref']))
    chk(not missing and not extra, f'project settings keys differ from a plain OrcaSlicer export with the same overrides: missing {missing}, extra {extra}')
    changed = sorted(k for k in a['settings'] if a['settings'][k] != refs['stock'].get(k))
    return dict(keys=len(a['settings']), ref_keys=len(refs['ref']), stock_keys=len(refs['stock']), changed=changed, round_trip_equal=a['settings'] == r['settings'])


def split_regions(layers, parts, margin=1.5):
    """Cut the parsed layers {z: [segment]} down to each part: the segment's midpoint inside the part's footprint box grown by `margin`."""
    out = {p['name']: {} for p in parts}
    for z, segs in layers.items():
        for s in segs:
            mx, my = (s[0] + s[2]) / 2, (s[1] + s[3]) / 2
            for p in parts:
                x0, y0, x1, y1 = p['bbox']
                if x0 - margin <= mx <= x1 + margin and y0 - margin <= my <= y1 + margin:
                    out[p['name']].setdefault(z, []).append(s)
                    break
            else:
                raise SystemExit(f'extrusion at {mx:.1f}, {my:.1f} (z {z}) belongs to no part')
    return out


def extruder_offset(head):
    """The machine's extruder_offset from the G-code header: the G-code frame is the model frame minus this (the Centauri Carbon 2 has 0 x 1.5)."""
    m = re.search(r'; extruder_offset = (\S+)x(\S+)', head)
    return (float(m.group(1)), float(m.group(2))) if m else (0.0, 0.0)


def to_model_frame(layers, off):
    """Segments from the G-code frame to the model (bed) frame the 3MF positions use."""
    return {z: [(s[0] + off[0], s[1] + off[1], s[2] + off[0], s[3] + off[1]) + tuple(s[4:]) for s in segs] for z, segs in layers.items()}


def region_grams(gcode, parts, head):
    """Filament per part: the extruding moves' E (relative) times the filament's cross-section and density. Also each part's share of the
    extruding time (move length over feed rate, a rough guide: no acceleration, no travel, no layer-time slow-down)."""
    d_fil = float(re.search(r'; filament_diameter = (\S+)', head).group(1))
    rho = float(re.search(r'; filament_density = (\S+)', head).group(1))
    area = math.pi * (d_fil / 2) ** 2
    off = extruder_offset(head)
    tot = {p['name']: 0.0 for p in parts}
    secs = {p['name']: 0.0 for p in parts}
    x = y = 0.0
    f = 1800.0
    t = None
    for ln in Path(gcode).read_text(errors='ignore').splitlines():
        if ln.startswith(';TYPE:'):
            t = ln[6:].strip()
        elif ln.startswith('G1 '):
            v = {}
            for q in ln.split(';')[0].split()[1:]:
                if q[0] in 'XYEF' and len(q) > 1:
                    try:
                        v[q[0]] = float(q[1:])
                    except ValueError:
                        pass
            f = v.get('F', f)
            nx, ny = v.get('X', x), v.get('Y', y)
            if v.get('E', 0) > 0 and (nx, ny) != (x, y) and t not in ('Custom', None):
                mx, my = (x + nx) / 2 + off[0], (y + ny) / 2 + off[1]
                for p in parts:
                    x0, y0, x1, y1 = p['bbox']
                    if x0 - 1.5 <= mx <= x1 + 1.5 and y0 - 1.5 <= my <= y1 + 1.5:
                        tot[p['name']] += v['E'] * area * rho / 1000.0
                        secs[p['name']] += math.hypot(nx - x, ny - y) / f * 60.0
                        break
            x, y = nx, ny
    whole = sum(secs.values()) or 1.0
    return tot, {k: v / whole for k, v in secs.items()}


def coupon_check(U, part, holes, zs, chk):
    """The coupon's holes on layers 1 and 2 (squeegee side = pad side here): the open width through each hole centre. Information plus the
    structural checks (membrane printed, channels empty above it, the corner mark open)."""
    ox, oy = part['origin']
    rows = []
    for h in holes:
        r = dict(short=h['short'], long=h['long'], row=h['row'])
        for li in (0, 1):
            wx, _ = C.free_interval(U[zs[li]], h['x'], h['y'], 'x', reach=2.0)
            wy, _ = C.free_interval(U[zs[li]], h['x'], h['y'], 'y', reach=2.0)
            r[f'L{li + 1}'] = (round(wx, 2), round(wy, 2))
        rows.append(r)
    # layers 3+ : the three channels (26 x 2.5) have no extrusion; the plate's footprint is printed on layers 1 and 2
    plate = box(-20, -15, 20, 15)
    notch = box(-21, 10, -15.5, 16)
    from shapely.geometry import Polygon
    mark = Polygon([(-21, 16), (-15, 16), (-21, 10)]).buffer(-0.15)
    worst_ch, worst_cov = 0.0, 1.0
    chan = shapely.union_all([box(-13 + 0.05, yc - 1.25 + 0.05, 13 - 0.05, yc + 1.25 - 0.05) for yc in (0, 8, -8)])
    for z in zs[2:]:
        worst_ch = max(worst_ch, U[z].intersection(chan).area)
    holes_union = shapely.union_all([box(h['x'] - h['long'] / 2, h['y'] - h['short'] / 2, h['x'] + h['long'] / 2, h['y'] + h['short'] / 2) for h in holes]).buffer(0.2)
    for z in zs[:2]:
        # the membrane: the channels' area minus the holes' neighbourhood must be printed
        mem = chan.difference(holes_union)
        worst_cov = min(worst_cov, U[z].intersection(mem).area / mem.area)
    chk(worst_ch < 0.01, f'coupon: {worst_ch:.3f} mm2 of extrusion inside the channels above the membrane')
    chk(worst_cov > 0.95, f'coupon: only {worst_cov:.1%} of the membrane is printed')
    notch_cov = max(U[z].intersection(mark).area for z in zs)
    chk(notch_cov < 0.01, f'coupon: {notch_cov:.3f} mm2 of extrusion in the corner mark')
    ext_ok = U[zs[0]].bounds
    chk(abs((ext_ok[2] - ext_ok[0]) - 40) < 0.7 and abs((ext_ok[3] - ext_ok[1]) - 30) < 0.7, f'coupon layer 1 extent {ext_ok}')
    return rows, worst_cov, worst_ch


def tab_probe(lay, origin, derived):
    """The clamp tongue's two tabs in the sliced layers: the points at the tabs' centres (w +-5.7, o 1.5 / 2.0 / 2.5) are extruded in the layers whose
    middle lies between the mouth plane and the tabs' top (the tongue's first layer is tied to the slot walls there), and the side slits are
    open in the layers just above. Returns {layer z: points covered of 6}."""
    from shapely.geometry import Point
    hm, tab_top = derived['P']['hm'], derived['P']['tab_top']
    shift_s = -(derived['hm'].bounds[0][0] + derived['hm'].bounds[1][0]) / 2
    out = {}
    for z in sorted(lay):
        h = z - 0.05
        if not (hm + 0.005 < h < tab_top + 0.3):
            continue
        U = C.layer_union(lay[z], origin[0], origin[1])
        n = 0
        for o in (1.5, 2.0, 2.5):
            sx = SQM.Q(0, o)[0] + (h - SQM.Q(0, o)[1]) / SQM.U[1] * SQM.U[0] + shift_s
            for w in (5.7, -5.7):
                n += U.contains(Point(sx, w))
        out[z] = int(n)
    return out


def read_back_slice(b, V, chk, derived):
    """Slice the finished project with OrcaSlicer's command line and read the G-code back, part by part."""
    d = b['dir']
    for old in d.glob('*.gcode'):
        old.unlink()
    sl = d / 'slice'
    sl.mkdir(exist_ok=True)
    for old in sl.glob('*'):
        old.unlink()
    orca(['--orient', '0', '--arrange', '0', '--slice', '0', '--outputdir', sl, b['final']], d)
    g = next(sl.glob('*.gcode'), None)
    if not chk(g is not None, 'the slice produced no G-code'):
        return {}
    layers, types, arcs = C.parse(g)
    head = g.read_text(errors='ignore')
    off = extruder_offset(head)
    layers = to_model_frame(layers, off)
    res = dict(gcode=g, types=sorted(types), extruder_offset=off)
    for key, pat in {'time': r'estimated printing time \(normal mode\) = (.+)', 'grams': r'total filament used \[g\] = ([\d.]+)',
                     'efc': r'; elefant_foot_compensation = (\S+)', 'layer_height': r'; layer_height = (\S+)',
                     'first_layer_height': r'; initial_layer_print_height = (\S+)', 'wall_loops': r'; wall_loops = (\S+)',
                     'wall_generator': r'; wall_generator = (\S+)', 'sequence': r'; print_sequence = (.+)'}.items():
        m = re.search(pat, head)
        res[key] = m.group(1).strip() if m else None
    chk(res['layer_height'] == '0.1' and res['first_layer_height'] == '0.1' and res['efc'] == '0', f"G-code header: layer {res['layer_height']}, first {res['first_layer_height']}, efc {res['efc']}")
    bad = sorted(set(types) & set(FORBIDDEN_PLATE))
    chk(not bad, f'forbidden line types in the G-code: {bad}')
    chk(not arcs, f'{len(arcs)} G2/G3 arc moves in the G-code')
    # the plate inside the bed
    xs = [c for z in layers for s in layers[z] for c in (s[0], s[2])]
    ys = [c for z in layers for s in layers[z] for c in (s[1], s[3])]
    res['extent'] = (min(xs), min(ys), max(xs), max(ys))
    bx, by = b['read']['bed']
    chk(min(xs) >= 0 and min(ys) >= 0 and max(xs) <= bx and max(ys) <= by, f'extrusion {res["extent"]} outside the bed {b["read"]["bed"]}')
    chk(min(xs) >= 0 and min(ys) >= 0 and max(xs) <= V['area'][0] and max(ys) <= V['area'][1], f'extrusion {res["extent"]} outside {V["area"]}')
    reg = split_regions(layers, b['parts'])
    grams, share = region_grams(g, b['parts'], head)
    tot = sum(grams.values())
    chk(abs(tot - float(res['grams'])) / float(res['grams']) < 0.03, f"per-part filament sums to {tot:.2f} g, the slicer says {res['grams']} g")
    res['part_grams'] = grams
    res['time_share'] = share
    res['parts'] = {}
    for p in b['parts']:
        lay = reg[p['name']]
        types_p = {s[5] for z in lay for s in lay[z]}
        parsed = (lay, types_p, [])
        if p['kind'] == 'stencil':
            gdesign = S.geometry(p['D'])
            r, fails = C.analyse(g, p['D'], gdesign, p['name'], parsed=parsed, centre=p['origin'], float_tol=FLOAT_TOL)
            for f in fails:
                chk(False, f"{p['name']}: {f}")
            # the part's centre as read must agree with the plan
            xs_ = [c for s in lay[sorted(lay)[0]] for c in (s[0], s[2])]
            ys_ = [c for s in lay[sorted(lay)[0]] for c in (s[1], s[3])]
            cx, cy = (min(xs_) + max(xs_)) / 2, (min(ys_) + max(ys_)) / 2
            chk(abs(cx - p['origin'][0]) < 0.3 and abs(cy - p['origin'][1]) < 0.3, f"{p['name']}: read centre ({cx:.2f}, {cy:.2f}) is not the planned ({p['origin'][0]:.2f}, {p['origin'][1]:.2f})")
            res['parts'][p['name']] = r
        elif p['kind'] == 'squeegee':
            hm_mesh, plate_mesh, P = derived['hm'], derived['plate'], derived['P']
            r, fails = SQM.read_back(g, lay, types_p, [], derived['derived'], hm_mesh, plate_mesh, P, origin=p['origin'], want_efc='0', global_walls=False)
            for f in fails:
                chk(False, f"{p['name']}: {f}")
            tp = tab_probe(lay, p['origin'], derived)
            tab_top = derived['P']['tab_top']
            tied = {z: n for z, n in tp.items() if z - 0.05 < tab_top}
            above = {z: n for z, n in tp.items() if z - 0.05 > tab_top + 0.01}
            chk(tied and all(n == 6 for n in tied.values()), f"{p['name']}: the tongue's tabs are not extruded in the layers {sorted(tied)} ({tied})")
            chk(above and all(n == 0 for n in above.values()), f"{p['name']}: a side slit is closed above the tabs ({above})")
            r['tab_probe'] = dict(tied=tied, above=above, tab_top=round(tab_top, 3))
            res['parts'][p['name']] = r
        else:
            zs = sorted(lay)
            U = {z: C.layer_union(lay[z], p['origin'][0], p['origin'][1]) for z in zs}
            want = [round(0.1 * (i + 1), 3) for i in range(int(round(p['height'] / 0.1)))]
            chk(zs == want, f"{p['name']}: layers {zs}, expected {want}")
            holes = json.loads((OUT / 'stencil_params.json').read_text(encoding='utf-8'))['coupon']['holes']
            rows, mem, ch = coupon_check(U, p, holes, zs, chk)
            res['parts'][p['name']] = dict(rows=rows, membrane_cover=round(mem, 3), channel_cover_mm2=round(ch, 4), layers=len(zs),
                                           bad_types=sorted(types_p & set(C.FORBIDDEN)))
            chk(not (types_p & set(C.FORBIDDEN)), f"{p['name']}: forbidden line types {sorted(types_p & set(C.FORBIDDEN))}")
    # the per-object settings took effect: the squeegee's walls differ from a slice without them (control: pass 1 has none)
    return res


def control_slice(b, V):
    """Slice pass1.3mf (no per-object settings) and compare the squeegee's wall widths: the per-object Arachne must change them."""
    d = b['dir']
    sl = d / 'control'
    sl.mkdir(exist_ok=True)
    for old in sl.glob('*'):
        old.unlink()
    orca(['--orient', '0', '--arrange', '0', '--slice', '0', '--outputdir', sl, d / 'pass1.3mf'], d)
    return next(sl.glob('*.gcode'))


def wall_stats(gcode, parts, part):
    """For one part: the number of distinct wall widths and the total wall length (mm) in the G-code."""
    layers, _, _ = C.parse(gcode)
    layers = to_model_frame(layers, extruder_offset(Path(gcode).read_text(errors='ignore')))
    reg = split_regions(layers, parts)
    widths, length = set(), 0.0
    for z, segs in reg[part['name']].items():
        for s in segs:
            if s[5] in ('Outer wall', 'Inner wall', 'Overhang wall'):
                widths.add(round(s[4], 3))
                length += math.hypot(s[2] - s[0], s[3] - s[1])
    return len(widths), round(length)


# ---------------------------------------------------------------------------------------------------------------
# Picture, report
# ---------------------------------------------------------------------------------------------------------------
def draw(b, V, res):
    """Layer 1 of the sliced plate (model frame), the parts' names, and the bed / usable area outlines."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
    layers, _, _ = C.parse(res['gcode'])
    layers = to_model_frame(layers, res['extruder_offset'])
    zs = sorted(layers)
    bx, by = b['read']['bed']
    allx = [p['bbox'][i] for p in b['parts'] for i in (0, 2)]
    ally = [p['bbox'][i] for p in b['parts'] for i in (1, 3)]
    m = 14
    fig, ax = plt.subplots(figsize=(8.6, 8.6), dpi=130)
    ax.add_patch(Rectangle((0, 0), bx, by, fill=False, ec='#444', lw=1.4))
    ax.add_patch(Rectangle((0, 0), V['area'][0], V['area'][1], fill=False, ec='#c47f00', lw=1.0, ls='--'))
    for s in layers[zs[0]]:
        ax.plot([s[0], s[2]], [s[1], s[3]], color='#1f6f8b', lw=0.5, solid_capstyle='round')
    for p in b['parts']:
        x0, y0, x1, y1 = p['bbox']
        label = {'squeegee': 'squeegee handle\n+ 2 PLA blades', 'coupon': 'aperture coupon'}.get(p['kind'], p['name'])
        ax.text((x0 + x1) / 2, y1 + 2.0, label, ha='center', va='bottom', fontsize=7.5)
    ax.set_xlim(-4, bx + 4)
    ax.set_ylim(-4, by + 4)
    ax.set_aspect('equal')
    ax.set_title(f"Stencil kit plate, {V['title']}\nlayer 1 of the command-line slice; solid line: the {bx:.0f} x {by:.0f} mm bed from its origin corner, dashed: {V['area'][0]:.0f} x {V['area'][1]:.0f} mm", fontsize=9)
    ax.set_xlabel('mm (bed x)')
    ax.set_ylabel('mm (bed y)')
    fig.tight_layout()
    path = IMAGE.with_name(f'stencil_plate_{b["key"]}.png')
    fig.savefig(path)
    plt.close(fig)
    return path


def write_report(allres, fails):
    L = ['# Stencil kit plate check', '',
         'Generated by `tools/stencil/make_plate.py`. Each `production/stencil/stencil-kit_*.3mf` is written by OrcaSlicer itself (its command line, never its window), '
         'then read back from the file and from one command-line slice of that file. **A toolpath and file check only: nothing here has been printed**, and the slicer '
         'cannot say whether the printed openings stay open (see `docs/ASSEMBLY.md`).', '']
    for key, r in allres.items():
        V, b, res, rb = r['V'], r['b'], r['res'], r['rb3']
        L += [f"## {key}: {V['title']}", '',
              f"File `production/stencil/{V['file']}`, {r['size']} bytes, sha256 `{r['sha'][:16]}`. Presets (names as OrcaSlicer holds them): machine `{V['presets']['machine']}`, "
              f"process `{V['presets']['process']}`, filament `{V['presets']['filament']}`. Bed {rb['bed'][0]:.0f} x {rb['bed'][1]:.0f} mm; the parts fill {rb['lo'][0]:.1f}..{rb['hi'][0]:.1f} x "
              f"{rb['lo'][1]:.1f}..{rb['hi'][1]:.1f} mm, inside {V['area'][0]:.0f} x {V['area'][1]:.0f}.", '',
              '| Check | Result |', '|---|---|',
              f"| Parts in the project | {', '.join(p['name'] for p in b['parts'])} |",
              f"| Position against the plan, worst error | {rb['worst_pos']:.4f} mm; none rotated; all on the bed (z 0) |",
              f"| Mesh against its STL, worst volume error | {rb['worst_vol']:.1e} |",
              f"| Per-object settings | squeegee object only: {SQUEEGEE_OBJECT}; the cards and the coupon carry none |",
              f"| Project settings | {r['keys']['keys']} keys (a plain OrcaSlicer export of the same presets and overrides has {r['keys']['ref_keys']}, of the stock presets {r['keys']['stock_keys']}); `filament_colour` present; "
              f"unchanged by an OrcaSlicer read and write; {len(r['keys']['changed'])} values differ from an export of the stock presets: {', '.join(r['keys']['changed'])} |",
              f"| Overrides on the stock process | " + ', '.join(f'`{k}` = {v}' for k, v in OVERRIDES.items()) + ' |',
              f"| G-code header | layer {res['layer_height']}, first layer {res['first_layer_height']}, elephant-foot compensation {res['efc']}, walls {res['wall_loops']} / {res['wall_generator']} (process), sequence {res['sequence']} |",
              f"| Line types | {', '.join(res['types'])} (no support, brim, skirt, ironing; 0 arc moves outside the start/end G-code) |",
              f"| Slicer estimate, whole plate | {res['time']}, {res['grams']} g |",
              f"| Filament by part (from the G-code, g) | " + ', '.join(f"{n} {g:.2f}" for n, g in res['part_grams'].items()) + ' |',
              f"| Share of the extruding time by part (rough: move length over feed rate) | " + ', '.join(f"{n} {100 * v:.0f} %" for n, v in res['time_share'].items()) + ' |']
        for n, pr in res['parts'].items():
            if n.startswith('stencil'):
                L.append(f"| {n} | apertures free on layers 1+2 {pr['n_apertures']}/24 (worst bead cover {pr['worst_cover_mm2']} mm2); smallest open width {pr['min_open_width']}; worst off-centre {pr['worst_offset']}; "
                         f"membrane = layers 1 and 2 (0.10 + 0.10 = 0.20 mm) printed {' / '.join(f'{c:.1%}' for c in pr['membrane_cover'])} of its area, layers 3 and up empty inside the pocket (worst {pr['pocket_max_cover_mm2']} mm2); datum walls {'all' if all(w[1] == w[2] and w[3] == w[4] for w in pr['datum']) else 'GAPS'}; floating {pr['float_max_mm2']} mm2; {len(pr['layers'])} layers |")
            elif n.startswith('squeegee'):
                L.append(f"| {n} | {pr['layers']} layers; floating islands in the sliced layers (0.5 mm2 or more, sparse infill aside; the clamp tongue's first layer is the one that mattered) {len(pr['floating_islands'])}, in the model sections at 0.10 mm {r['mesh_islands']}; sparse-infill stubs inside the walls {len(pr['sparse_infill_stubs'])}; extrusion outside the design {pr['worst_extrusion_outside_design_mm2']} mm2; "
                         f"slot open {pr['slot_open_min']:.2f} (design 1.25), back slit {pr['back_slit_open_min']:.2f}, side slits {pr['side_slit_open_min']:.2f} (0.80), screw hole {pr['hole_open_min']:.2f} (2.6); "
                         f"PLA blade layers >= {pr['pla_blade_layer_cover_min']:.1%}; bridges {pr['bridges']['bridge_mm_by_layer_z']} |")
                L.append(f"| clamp tongue's tabs | the 6 probe points at the two tabs are extruded in the layers {sorted(pr['tab_probe']['tied'])} (z; the mouth plane is at h {pr['tab_probe']['tab_top'] - 0.21:.2f}, the tabs end at h {pr['tab_probe']['tab_top']:.2f}), so the tongue's first layer is tied to the slot walls and is not an island; the side slits are open in the layers above ({sorted(pr['tab_probe']['above'])}) |")
            else:
                L.append(f"| {n} | {pr['layers']} layers; membrane printed {pr['membrane_cover']:.1%}; channels above it empty (worst {pr['channel_cover_mm2']} mm2) |")
        L += ['', f"Per-object settings take effect: the squeegee has {r['walls'][0]} distinct wall widths and {r['walls'][1]} mm of wall with them, "
                  f"{r['walls_control'][0]} and {r['walls_control'][1]} mm in the same slice without them.", '']
        cp = res['parts']['aperture-coupon']
        L += ['Aperture coupon: the open stretch through each hole centre in the sliced layers 1 and 2, along x and along y, against the designed hole:', '',
              '| hole as designed, x by y (mm) | open width through the centre, layer 1 (x by y) | layer 2 |', '|---|---|---|']
        for h in cp['rows']:
            L.append(f"| {h['long']} x {h['short']} | {h['L1'][0]} x {h['L1'][1]} | {h['L2'][0]} x {h['L2'][1]} |")
        L.append('')
        if r.get('image'):
            L += [f"![plate layout]({Path(r['image']).relative_to(ROOT / 'docs').as_posix().replace('images/', '../images/')})", '']
    L += ['Method: OrcaSlicer is given the five placed STLs, the flattened stock presets (its command line does not resolve preset inheritance for files; names are kept) and the overrides listed above (`slice_check.OVERRIDES` plus the classic wall generator), '
          'and writes the project; the squeegee object then gets its own `wall_loops` and `wall_generator` in the object list, and OrcaSlicer reads and writes the file again, so the project settings are OrcaSlicer\'s own. '
          'Read-back: the 3MF is parsed (object transforms, meshes, per-object and project settings, a round trip, and plain exports of the same presets, with and without the overrides, for the key set), then the finished file is sliced and each part is cut out of the G-code by position and checked with the same code as the single-part checks '
          '(`slice_check.analyse` for the cards, `squeegee.read_back` for the squeegee). The bed, 220 x 210 mm area and positions are checked on the 3MF and on the G-code. Estimates of time and grams are the slicer\'s.']
    if fails:
        L += ['', '## Failures', ''] + [f'- {f}' for f in fails]
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text('\n'.join(L) + '\n', encoding='utf-8')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--only', choices=sorted(VARIANTS), help='build one project only')
    ap.add_argument('--reuse', action='store_true', help='development: skip the OrcaSlicer export when build/stencil/plate/<variant>/ already has the project')
    args = ap.parse_args()
    WORK.mkdir(parents=True, exist_ok=True)
    print('squeegee model checks ...')
    derived, hm_mesh, plate_mesh, P = SQM.build(write=False)
    on_disk = trimesh.load(OUT / 'squeegee_print.stl')
    assert abs(on_disk.volume - plate_mesh.volume) < 1.0 and np.abs(on_disk.bounds - plate_mesh.bounds).max() < 1e-3, 'squeegee_print.stl is not the current squeegee.py output: rerun squeegee.py'
    dctx = dict(derived=derived, hm=hm_mesh, plate=plate_mesh, P=P)
    # the model itself at the plate's 0.10 mm layers: no piece of a layer that touches nothing in the layer below (squeegee.py checks at 0.20)
    n_l = int(round(plate_mesh.bounds[1][2] / 0.1))
    mesh_islands = SQM.layer_islands([((k + 1) * 0.1, SQM.section_poly(plate_mesh, 2, (k + 0.5) * 0.1)) for k in range(n_l)])
    print(f'model sections at 0.10 mm: {n_l} layers, {len(mesh_islands)} floating islands')
    allres, allfails = {}, []
    for key, V in VARIANTS.items():
        if args.only and key != args.only:
            continue
        chk = Check()
        print(f'{key}: building the project with OrcaSlicer ...')
        b = build_project(key, V, reuse=args.reuse)
        b['key'] = key
        b['read'] = read_back_3mf(b, V, chk)
        keys = settings_round_trip(b, V, chk)
        res = read_back_slice(b, V, chk, dctx)
        sqp = next(p for p in b['parts'] if p['kind'] == 'squeegee')
        walls = wall_stats(res['gcode'], b['parts'], sqp)
        walls_c = wall_stats(control_slice(b, V), b['parts'], sqp)
        chk(walls != walls_c, f'the per-object settings changed nothing in the slice: squeegee walls {walls} with, {walls_c} without')
        image = draw(b, V, res) if res else None
        data = b['final'].read_bytes()
        (OUT / V['file']).write_bytes(data)
        chk(not mesh_islands, f'floating islands in the model at 0.10 mm layers: {mesh_islands}')
        allres[key] = dict(V=V, b=b, res=res, rb3=b['read'], keys=keys, walls=walls, walls_control=walls_c, image=image, mesh_islands=len(mesh_islands),
                           size=len(data), sha=hashlib.sha256(data).hexdigest())
        print(f"{key}: {res.get('time')}, {res.get('grams')} g, {'PASS' if not chk.fails else 'FAIL'}")
        for f in chk.fails:
            print('   -', f)
        allfails += [f'{key}: {f}' for f in chk.fails]
    write_report(allres, allfails)
    if allfails:
        print('FAIL')
        sys.exit(1)
    print('PASS; report in', REPORT.relative_to(ROOT))


if __name__ == '__main__':
    main()
