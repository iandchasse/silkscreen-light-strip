"""Read the paste pads, the outline and the stiffener/adhesive polygons from the light strip's board.

Run with KiCad 9's Python (it has pcbnew):
    "C:\\Program Files\\KiCad\\9.0\\bin\\python.exe" -X utf8 -I tools/stencil/extract_paste.py

The board is read from a COPY in build/stencil/ (build/ is git-ignored), never from the project file itself, so a
KiCad lock or an autosave cannot touch the project. Output: production/stencil/stencil_input.json, which stencil.py,
slice_check.py and render.py read (they run in the CadQuery venv, which has no pcbnew).

All coordinates are the board's KiCad frame in mm: x right, y down, seen from the component (top) side.

The script fails when the board is not what the stencil assumes: 30 F.Paste pads, none on B.Paste, and a paste margin of
0 everywhere (so the paste opening is exactly the copper; the stencil's apertures are sized from that).
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[2]
BOARD = ROOT / 'silkscreen-light-strip.kicad_pcb'
COPY_DIR = ROOT / 'build' / 'stencil'
OUT = ROOT / 'production' / 'stencil' / 'stencil_input.json'
LED_FP = 'LED_SideView_XINGLIGHT_XL-4008'
EXPECT_PASTE_PADS = 30
mm = pcbnew.ToMM


def poly_set_to_list(sps):
    """A SHAPE_POLY_SET as [outline][point] = [x, y] (mm); only the outlines (this board has no holes in them)."""
    out = []
    for i in range(sps.OutlineCount()):
        o = sps.Outline(i)
        out.append([[round(mm(o.CPoint(j).x), 4), round(mm(o.CPoint(j).y), 4)] for j in range(o.PointCount())])
        assert sps.HoleCount(i) == 0, 'a hole in a polygon: the stencil script does not handle it'
    return out


def has_local_margin(item):
    """True when a footprint or pad sets its own paste margin or ratio (KiCad 9 returns None for 'not set')."""
    return any(v not in (None, 0, 0.0) for v in (item.GetLocalSolderPasteMargin(), item.GetLocalSolderPasteMarginRatio()))


def git(*args):
    try:
        return subprocess.run(['git', *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    except Exception:
        return None


def main():
    COPY_DIR.mkdir(parents=True, exist_ok=True)
    copy = COPY_DIR / 'board_copy.kicad_pcb'
    shutil.copyfile(BOARD, copy)
    b = pcbnew.LoadBoard(str(copy))
    ds = b.GetDesignSettings()
    margin, ratio = mm(ds.m_SolderPasteMargin), ds.m_SolderPasteMarginRatio
    problems = []
    if margin != 0 or ratio != 0:
        problems.append(f'board paste margin {margin} / ratio {ratio} is not 0')

    pads = []
    for fp in b.GetFootprints():
        if has_local_margin(fp):
            problems.append(f'{fp.GetReference()} has a local paste margin')
        for p in fp.Pads():
            ls = p.GetLayerSet()
            if ls.Contains(pcbnew.B_Paste):
                problems.append(f'{fp.GetReference()}.{p.GetNumber()} has paste on B.Paste')
            if not ls.Contains(pcbnew.F_Paste):
                continue
            if has_local_margin(p):
                problems.append(f'{fp.GetReference()}.{p.GetNumber()} has a local paste margin')
            sps = pcbnew.SHAPE_POLY_SET()
            p.TransformShapeToPolygon(sps, pcbnew.F_Paste, 0, pcbnew.FromMM(0.001), pcbnew.ERROR_INSIDE)
            bb = sps.BBox()
            c = p.GetPosition()
            pads.append(dict(
                ref=fp.GetReference(), pad=str(p.GetNumber()), net=p.GetNetname(), footprint=fp.GetFPIDAsString().split(':')[-1],
                x=round(mm(c.x), 4), y=round(mm(c.y), 4), rot=p.GetOrientationDegrees(),
                rr=round(p.GetRoundRectRadiusRatio(pcbnew.F_Cu), 4),
                # the paste polygon's bounding box in the board frame: this is what the stencil aligns to
                paste_bbox=[round(mm(bb.GetLeft()), 4), round(mm(bb.GetTop()), 4), round(mm(bb.GetRight()), 4), round(mm(bb.GetBottom()), 4)],
                paste_w=round(mm(bb.GetWidth()), 4), paste_h=round(mm(bb.GetHeight()), 4)))
    if len(pads) != EXPECT_PASTE_PADS:
        problems.append(f'{len(pads)} F.Paste pads, expected {EXPECT_PASTE_PADS}')
    leds = [p for p in pads if p['footprint'] == LED_FP]
    if len(leds) != 24:
        problems.append(f'{len(leds)} LED pads, expected 24')
    if problems:
        print('FAIL: the board is not what the stencil assumes:')
        for q in problems:
            print('  -', q)
        sys.exit(1)

    outline = pcbnew.SHAPE_POLY_SET()
    if not b.GetBoardPolygonOutlines(outline) or outline.OutlineCount() != 1:
        print('FAIL: Edge.Cuts is not one closed outline')
        sys.exit(1)

    layers = {}
    for name in ('Stiffener.PI0.225', 'Adhesive.3M9077'):
        lid = b.GetLayerID(name)
        polys = []
        for d in b.GetDrawings():
            if d.GetLayer() == lid and d.GetClass() == 'PCB_SHAPE' and d.ShowShape() in ('Polygon', 'Poly'):
                polys.extend(poly_set_to_list(d.GetPolyShape()))
        layers[name] = polys
    bend = []
    lid = b.GetLayerID('Bend.Zones')
    for d in b.GetDrawings():
        if d.GetLayer() == lid:
            bb = d.GetBoundingBox()
            bend.append([round(mm(bb.GetLeft()), 3), round(mm(bb.GetTop()), 3), round(mm(bb.GetRight()), 3), round(mm(bb.GetBottom()), 3)])

    obb = outline.BBox()
    data = dict(
        board=BOARD.name,
        board_blob=git('hash-object', str(BOARD)),
        head=git('rev-parse', '--short', 'HEAD'),
        paste_margin_mm=margin, paste_margin_ratio=ratio,
        outline=poly_set_to_list(outline)[0],
        outline_bbox=[round(mm(obb.GetLeft()), 4), round(mm(obb.GetTop()), 4), round(mm(obb.GetRight()), 4), round(mm(obb.GetBottom()), 4)],
        stiffener_pi=layers['Stiffener.PI0.225'], adhesive_3m9077=layers['Adhesive.3M9077'], bend_zone_boxes=bend,
        paste_pads=pads)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, indent=1), encoding='utf-8')
    print(f'ok: {len(pads)} F.Paste pads ({len(leds)} LED, {len(pads) - len(leds)} other), outline {len(data["outline"])} points,'
          f' stiffener polygons {len(data["stiffener_pi"])}, adhesive polygons {len(data["adhesive_3m9077"])}')
    print('paste margin', margin, 'ratio', ratio, '-> wrote', OUT.relative_to(ROOT))


if __name__ == '__main__':
    main()
