"""Make a STEP body for the side-view LED, using KiCad itself as the CAD kernel.

KiCad exports a board outline as a solid, so a 4.0 x 1.4 mm "board" 0.8 mm thick
is exactly the LED's body.  The outline is drawn in the footprint's own frame
(light toward -y), and KiCad's STEP export flips y the same way it expects
component models to be flipped, so the result drops straight into the
footprint as <name>.step beside the VRML (kicad-cli --subst-models picks it up).
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import params as P  # noqa: E402

KICAD_CLI = r"C:\Program Files\KiCad\9.0\bin\kicad-cli.exe"


def make(out_step, tmpdir):
    L = P.LED
    x0, x1 = -L["body_len"] / 2, L["body_len"] / 2
    y0, y1 = -L["face_ahead"], L["rear_behind"]
    # KiCad's STEP body is the board thickness minus 2 x 0.035 mm of (default) copper
    pcb = f"""(kicad_pcb (version 20241229) (generator "pcbnew") (generator_version "9.0")
  (general (thickness {L["body_h"] + 0.07:.3f}) (legacy_teardrops no))
  (paper "A4")
  (layers (0 "F.Cu" signal) (2 "B.Cu" signal) (25 "Edge.Cuts" user))
  (setup (pad_to_mask_clearance 0))
  (net 0 "")
  (gr_rect (start {x0} {y0}) (end {x1} {y1}) (stroke (width 0.01) (type solid)) (fill no) (layer "Edge.Cuts")
    (uuid "7c1d7a0e-0000-4000-8000-000000000001"))
)
"""
    os.makedirs(tmpdir, exist_ok=True)
    src = os.path.join(tmpdir, "led_body.kicad_pcb")
    with open(src, "w", encoding="utf-8") as fh:
        fh.write(pcb)
    r = subprocess.run([KICAD_CLI, "pcb", "export", "step", "--board-only", "--force", "--user-origin", "0x0mm",
                        "-o", out_step, src], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(r.stdout + r.stderr)
    return out_step


if __name__ == "__main__":
    root = os.path.dirname(HERE)
    print(make(os.path.join(root, "lib", P.PROJECT + ".3dshapes", "LED_SideView_XINGLIGHT_XL-4008.step"),
               os.path.join(root, "build", "step_model")))
