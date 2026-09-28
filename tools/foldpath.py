"""Tail length the flex needs, from the panel's bottom glass edge to the contact tip, in each enclosure.

The tail leaves the panel front, goes over the bottom glass edge, through the main board's FPC slot
(KiCad y 141.2..142.5) and along the board's back into J3.  Lengths are on the flex mid-plane.
Frames: KiCad y (down the board), Z = 0 at the board's rear face, +Z toward the viewer.

  4.26in (enclosures/case-426, light-strip tub): plain GDEY0426T82 held with its rear on the
      midplate at Z 3.0; the glass edge (y 142.965) overhangs the slot, so the tail wraps a U around it,
      runs back under the glass and drops through the slot.
  3.68in (enclosures/case-368, light-strip tub): the glass edge (y 141.2) is the slot's top
      edge, so the tail folds 90 deg over it straight down through the slot.

Run with any Python 3:  python tools/foldpath.py
"""
import itertools
import math

T = 0.104            # finished flex thickness where there is no stiffener (0.11 nominal, 0.104 as built)
H = T / 2
SLOT = (141.2, 142.5)
PCB_FRONT = 1.6
J3_Z = -0.45         # mid-plane of the tail where it enters J3 (the FT01C frontlight tail runs at Z -0.45)
TIP_Y = (124.7, 125.0, 125.3)   # contact tip fully home in J3 (nominal 125.0, +/-0.3)

ENCL = {
    "4.26in claude": {"glass_y": 142.965, "ledge_z": 3.5, "wrap": "U"},
    "3.68in x3":     {"glass_y": 141.2,   "ledge_z": 3.1, "wrap": "90"},
}


def need_u(e, R1, R2, R3, o, yd, tip):
    """U around the glass edge, back under the glass, 90 deg down the slot, 90 deg onto the back."""
    r1, r2, r3 = R1 + H, R2 + H, R3 + H
    z_top = e["ledge_z"] + H
    z_leg = z_top - 2 * r1                      # bottom leg of the U
    if z_leg - H < PCB_FRONT + 0.05:            # the bottom leg must clear the board's front
        return None
    c = (e["glass_y"] + o) - (yd + r2)          # bottom leg back to the drop
    d = (z_leg - r2) - (J3_Z + r3)              # drop through the slot
    if c < 0 or d < 0:
        return None
    back = (yd - r3) - tip
    return o + math.pi * r1 + c + math.pi / 2 * r2 + d + math.pi / 2 * r3 + back


def need_90(e, R1, R3, tip):
    """90 deg over the glass edge straight down the slot, 90 deg onto the back."""
    r1, r3 = R1 + H, R3 + H
    z_top = e["ledge_z"] + H
    yd = e["glass_y"] + r1                      # the drop's mid-plane
    if yd + H > SLOT[1]:
        return None
    d = (z_top - r1) - (J3_Z + r3)
    back = (yd - r3) - tip
    return math.pi / 2 * r1 + d + math.pi / 2 * r3 + back


def sweep():
    out = {}
    e = ENCL["4.26in claude"]
    vals = []
    for R1, R2, R3, o, yd, tip in itertools.product((0.66, 0.8, 0.9), (0.6, 0.8, 1.0), (0.6, 0.8, 1.2),
                                                    (0.0, 0.12, 0.24), (141.3, 141.85, 142.3), TIP_Y):
        L = need_u(e, R1, R2, R3, o, yd, tip)
        if L is not None:
            vals.append(L)
    nom = need_u(e, 0.8, 0.8, 0.8, 0.12, 141.85, 125.0)
    out["4.26in claude"] = (min(vals), nom, max(vals), len(vals))
    e = ENCL["3.68in x3"]
    vals = [need_90(e, R1, R3, tip) for R1, R3, tip in itertools.product((0.5, 0.65, 0.9), (0.6, 0.8, 1.2), TIP_Y)]
    vals = [v for v in vals if v is not None]
    out["3.68in x3"] = (min(vals), need_90(e, 0.65, 0.8, 125.0), max(vals), len(vals))
    return out


if __name__ == "__main__":
    for k, (lo, nom, hi, n) in sweep().items():
        print(f"{k:14s} need {lo:6.2f} .. {hi:6.2f} mm (nominal {nom:6.2f}; {n} cases) from the glass edge")
