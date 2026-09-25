"""Checks and fabrication outputs for the light strip, all through kicad-cli.

    "C:\\Program Files\\KiCad\\9.0\\bin\\python.exe" tools\\make_outputs.py

Writes:
  docs/reports/        ERC and DRC (with schematic parity) reports, text + JSON
  production/gerbers/  Gerbers incl. stiffener (User.1), tape (User.2), bend zones (User.3) + drill
  production/*.zip     the Gerber zip to upload to JLCPCB's flex order page
  production/          JLC BOM + CPL, a full BOM with MPNs
  docs/                schematic PDF, layout PDF (one layer per page), STEP (flat), 3D renders
Fails (non-zero exit) if ERC or DRC finds anything.
"""
import csv
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import params as P  # noqa: E402

ROOT = os.path.dirname(HERE)
NAME = P.PROJECT
CLI = os.environ.get("KICAD_CLI", r"C:\Program Files\KiCad\9.0\bin\kicad-cli.exe")
PCB = os.path.join(ROOT, NAME + ".kicad_pcb")
SCH = os.path.join(ROOT, NAME + ".kicad_sch")
REP = os.path.join(ROOT, "docs", "reports")
PROD = os.path.join(ROOT, "production")
GERB = os.path.join(PROD, "gerbers")
IMG = os.path.join(ROOT, "docs", "images")
MECH = os.path.join(ROOT, "docs", "mechanical")


def run(args, ok=(0,)):
    r = subprocess.run([CLI] + args, capture_output=True, text=True)
    if r.returncode not in ok:
        print(r.stdout, r.stderr)
        raise SystemExit(f"kicad-cli {' '.join(args[:3])} failed ({r.returncode})")
    return r.stdout


def checks():
    os.makedirs(REP, exist_ok=True)
    run(["sch", "erc", "--severity-all", "-o", os.path.join(REP, "erc.rpt"), SCH], ok=(0, 5))
    run(["sch", "erc", "--severity-all", "--format", "json", "-o", os.path.join(REP, "erc.json"), SCH], ok=(0, 5))
    run(["pcb", "drc", "--schematic-parity", "--severity-all", "-o", os.path.join(REP, "drc.rpt"), PCB], ok=(0, 5))
    run(["pcb", "drc", "--schematic-parity", "--severity-all", "--format", "json",
         "-o", os.path.join(REP, "drc.json"), PCB], ok=(0, 5))
    erc = json.load(open(os.path.join(REP, "erc.json"), encoding="utf-8"))
    drc = json.load(open(os.path.join(REP, "drc.json"), encoding="utf-8"))
    n_erc = sum(len(s.get("violations", [])) for s in erc.get("sheets", []))
    n_drc = len(drc.get("violations", []))
    n_unc = len(drc.get("unconnected_items", []))
    n_par = len(drc.get("schematic_parity", []))
    print(f"ERC {n_erc}  DRC {n_drc}  unconnected {n_unc}  parity {n_par}")
    return n_erc + n_drc + n_unc + n_par


def gerbers():
    if os.path.isdir(GERB):
        shutil.rmtree(GERB)
    os.makedirs(GERB)
    layers = "F.Cu,B.Cu,F.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts,User.1,User.2,User.3"
    run(["pcb", "export", "gerbers", "--layers", layers, "--subtract-soldermask", "--precision", "6",
         "-o", GERB + os.sep, PCB])
    run(["pcb", "export", "drill", "--format", "excellon", "--excellon-units", "mm", "--generate-map",
         "--map-format", "pdf", "-o", GERB + os.sep, PCB])
    zpath = os.path.join(PROD, f"{NAME}_rev-{P.REVISION}_gerbers.zip")
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for fn in sorted(os.listdir(GERB)):
            # the bend-zone layer is documentation only: JLC reads anything over the board as a request
            # (the job file is left out too: it still lists the Bend_Zones layer)
            if fn.endswith(".pdf") or fn.endswith(".gbrjob") or "Bend_Zones" in fn:
                continue
            z.write(os.path.join(GERB, fn), fn)
    print("gerbers:", len(os.listdir(GERB)), "files ->", os.path.relpath(zpath, ROOT))


def boms():
    net = os.path.join(ROOT, "build", NAME + ".xml")
    run(["sch", "export", "netlist", "--format", "kicadxml", "-o", net, SCH])
    text = open(net, encoding="utf-8").read()
    comps = []
    for m in re.finditer(r'<comp ref="([^"]+)">(.*?)</comp>', text, re.S):
        ref, body = m.group(1), m.group(2)
        val = re.search(r"<value>(.*?)</value>", body).group(1)
        fp = re.search(r"<footprint>(.*?)</footprint>", body)
        fields = dict(re.findall(r'<field name="([^"]+)">(.*?)</field>', body))
        exclude = bool(re.search(r'<property name="exclude_from_bom"', body))
        comps.append({"ref": ref, "value": val, "footprint": fp.group(1) if fp else "", "fields": fields,
                      "exclude": exclude})
    parts = [c for c in comps if not c["exclude"]]
    groups = {}
    for c in parts:
        key = (c["value"], c["footprint"], c["fields"].get("LCSC", ""))
        groups.setdefault(key, []).append(c)

    def refkey(r):
        m = re.match(r"([A-Z]+)(\d+)", r)
        return (m.group(1), int(m.group(2)))
    os.makedirs(PROD, exist_ok=True)
    with open(os.path.join(PROD, "jlc_bom.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["Comment", "Designator", "Footprint", "JLCPCB Part #"])
        for (val, fp, lcsc), cs in sorted(groups.items(), key=lambda kv: refkey(kv[1][0]["ref"])):
            refs = ",".join(sorted((c["ref"] for c in cs), key=refkey))
            w.writerow([val, refs, fp.split(":")[-1], lcsc])
    with open(os.path.join(PROD, "bom.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["Qty", "Designators", "Value", "Manufacturer", "MPN", "LCSC", "Footprint", "Description"])
        for (val, fp, lcsc), cs in sorted(groups.items(), key=lambda kv: refkey(kv[1][0]["ref"])):
            f0 = cs[0]["fields"]
            refs = ",".join(sorted((c["ref"] for c in cs), key=refkey))
            w.writerow([len(cs), refs, val, f0.get("Manufacturer", ""), f0.get("MPN", ""), lcsc,
                        fp.split(":")[-1],
                        "; ".join(dict.fromkeys(f"{c['ref']}: {c['fields'].get('Description', '')}" for c in cs))
                        if len({c["fields"].get("Description", "") for c in cs}) > 1 else f0.get("Description", "")])
    print("bom:", len(parts), "parts in", len(groups), "lines")


def cpl():
    raw = os.path.join(ROOT, "build", "pos.csv")
    run(["pcb", "export", "pos", "--format", "csv", "--units", "mm", "--side", "front", "--exclude-dnp",
         "-o", raw, PCB])
    rows = list(csv.DictReader(open(raw, encoding="utf-8")))
    # JLC's library footprints are not always at KiCad's 0 deg.  Offsets checked against the EasyEDA
    # footprints of the ordered LCSC parts (docs/review/dfm.md):
    #   BAV70W C28064: EasyEDA 0 deg == KiCad SOT-323 at 180 deg -> add 180
    #   XL-4008 C5440667/C2843774: lens toward -y, anode at -x at 0 deg, same as ours -> add 0
    offset = {"SOT-323_SC-70": 180.0, "LED_SideView_XINGLIGHT_XL-4008": 0.0}
    with open(os.path.join(PROD, "jlc_cpl.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
        for r in rows:
            rot = (float(r["Rot"]) + offset.get(r["Package"], 0.0)) % 360
            w.writerow([r["Ref"], f'{float(r["PosX"]):.4f}mm', f'{float(r["PosY"]):.4f}mm', "Top", f"{rot:.1f}"])
    print("cpl:", len(rows), "placements")


def docs():
    os.makedirs(IMG, exist_ok=True)
    os.makedirs(MECH, exist_ok=True)
    run(["sch", "export", "pdf", "-o", os.path.join(ROOT, "docs", NAME + "_schematic.pdf"), SCH])
    run(["pcb", "export", "pdf", "--mode-multipage", "--include-border-title",
         "--layers", "F.Cu,B.Cu,F.Silkscreen,F.Mask,User.1,User.2,User.3,User.4,F.Fab",
         "--cl", "Edge.Cuts", "-o", os.path.join(ROOT, "build") + os.sep, PCB])
    # multipage export writes <board>.pdf into a folder; move it to docs/ under its own name
    lay = os.path.join(ROOT, "docs", NAME + "_layout.pdf")
    if os.path.isdir(lay):
        shutil.rmtree(lay)
    shutil.move(os.path.join(ROOT, "build", NAME + ".pdf"), lay)
    run(["pcb", "export", "step", "--force", "--subst-models", "-o",
         os.path.join(MECH, NAME + "_flat.step"), PCB])
    run(["pcb", "export", "vrml", "--force", "--units", "mm", "-o", os.path.join(MECH, NAME + "_flat.wrl"), PCB],
        ok=(0, 1, 2))
    # renders: the strip is long and narrow, so turn it 90 deg for a landscape image
    common = ["--quality", "high", "--background", "opaque", "--width", "3200", "--height", "900",
              "--rotate", " 0,0,90", "--zoom", "3.2", "--use-board-stackup-colors"]
    run(["pcb", "render", "--side", "top"] + common + ["-o", os.path.join(IMG, "render_front.png"), PCB])
    run(["pcb", "render", "--side", "bottom"] + common + ["-o", os.path.join(IMG, "render_back.png"), PCB])
    run(["pcb", "render", "--side", "top", "--quality", "high", "--background", "opaque", "--width", "1800",
         "--height", "1400", "--perspective", "--rotate", " -50,0,35", "--zoom", "4.5", "--use-board-stackup-colors",
         "-o", os.path.join(IMG, "render_foot_iso.png"), PCB])
    print("docs: schematic/layout PDF, STEP, renders")


if __name__ == "__main__":
    bad = checks()
    gerbers()
    boms()
    cpl()
    docs()
    if bad:
        raise SystemExit(f"{bad} ERC/DRC findings - see docs/reports")
