"""Grazing-light irradiance model for the side-emitting LED strip, on both panels.

Each LED is a point source a height h above the panel surface, its optical
axis parallel to the surface and pointing into the active area.  Intensity
falls off as cos^m in the horizontal plane and cos^n in the vertical plane,
with m and n set from the datasheet's full viewing angles.  The irradiance
on the (flat, matte) panel surface at distance r is

    E = I(theta_h, theta_v) * cos(incidence) / r^2,   cos(incidence) = h / r

This is geometry only.  A real e-paper front film is a textured scatterer,
so the far side of the screen looks brighter than this predicts, but the
shape of the gradient (and which layout is better) holds.

LED positions come from tools/params.py (PAIRS, HINGE, LED), the same formula
tools/generate.py uses, so this script needs no KiCad.

Run with any Python 3 that has numpy and matplotlib:
    python tools/optics_sim.py            -> docs/images/optics_*.png + summary
"""
from __future__ import annotations

import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "docs", "images")
sys.path.insert(0, HERE)
import params as P  # noqa: E402


def exponent_for_full_angle(full_deg: float) -> float:
    """cos^m exponent whose half-intensity full angle is full_deg (120 deg -> m = 1)."""
    half = math.radians(full_deg / 2.0)
    return math.log(0.5) / math.log(math.cos(half))


def irradiance(grid_x, grid_y, leds, h, face_gap, m, n, axis="x"):
    """Sum irradiance from LEDs on one edge.

    axis="x": LEDs on the left edge at x = -face_gap, shining +x; positions are y values.
    axis="y": LEDs on the top edge at y = -face_gap, shining +y; positions are x values.
    """
    e = np.zeros_like(grid_x)
    for p in leds:
        if axis == "x":
            dx = grid_x + face_gap        # along the optical axis
            dl = grid_y - p               # lateral
        else:
            dx = grid_y + face_gap
            dl = grid_x - p
        rho = np.hypot(dx, dl)
        r = np.hypot(rho, h)
        th_h = np.arctan2(np.abs(dl), dx)
        th_v = np.arctan2(h, rho)
        ih = np.clip(np.cos(th_h), 0, None) ** m
        iv = np.clip(np.cos(th_v), 0, None) ** n
        e += ih * iv * (h / r) / r**2
    return e


def mix_error(e_warm, e_cool, xs, ys, axis):
    """With both strings lit equally: worst |warm share - 0.5| along the edge at a few depths."""
    share = e_warm / (e_warm + e_cool)
    out = {}
    for d in (3, 6, 10, 20):
        if axis == "x":
            line = share[:, int(np.argmin(np.abs(xs - d)))]
        else:
            line = share[int(np.argmin(np.abs(ys - d))), :]
        k = max(1, len(line) // 12)
        out[f"{d}mm"] = round(float(np.max(np.abs(line[k:-k] - 0.5))), 3)
    return out


def strip_leds():
    """(cool_y, warm_y) of every pair, top pair first, in the main-board KiCad frame (as generate.py)."""
    L = P.LED
    n = L["per_string"]
    span = 2 * (L["pad_c"] + L["pad_len"] / 2) + L["pair_gap"]
    centres = [P.PAIRS["bottom_centre"] - P.PAIRS["pitch"] * (n - 1 - p) for p in range(1, n)]
    centres = [centres[0] - P.HINGE["pitch"]] + centres
    return [(c - span / 2, c + span / 2) for c in centres]


def run_case(name, active, pairs, face_gap, h, m, n, axis="x", res=0.25, note=""):
    """active: dict left/right/top/bottom (KiCad); pairs: [(cool_y, warm_y)] in KiCad y (axis x)
    or x (axis y); positions are made relative to the active area's lit edge."""
    aw = active["right"] - active["left"]
    ah = active["bottom"] - active["top"]
    xs = np.arange(res / 2, aw, res)
    ys = np.arange(res / 2, ah, res)
    gx, gy = np.meshgrid(xs, ys)
    off = active["top"] if axis == "x" else active["left"]
    cool = np.array([c - off for c, _ in pairs])
    warm = np.array([w - off for _, w in pairs])
    both = np.sort(np.concatenate([cool, warm]))
    e_warm = irradiance(gx, gy, warm, h, face_gap, m, n, axis)
    e_cool = irradiance(gx, gy, cool, h, face_gap, m, n, axis)
    e_both = e_warm + e_cool

    throw = xs if axis == "x" else ys
    prof = np.median(e_warm, axis=0) if axis == "x" else np.median(e_warm, axis=1)
    far = prof[-1]
    idx = lambda d: int(np.argmin(np.abs(throw - d)))
    ratios = {f"{d:g}mm": float(prof[idx(d)] / far) for d in (2, 5, 10, 20, 30, 40)}

    pitch = float(np.median(np.diff(np.sort(warm)))) if len(warm) > 1 else float(ah)
    scallop = {}
    for d in (3, 6, 10, 20):
        i = idx(d)
        line = e_warm[:, i] if axis == "x" else e_warm[i, :]
        k = int(pitch / 2 / res)             # ignore half a pitch at each end (corner falloff, not scalloping)
        seg = line[k:-k] if len(line) > 2 * k else line
        scallop[f"{d}mm"] = float(seg.max() / seg.min())

    # how evenly the edge is covered: brightness along the edge at 10 mm, ends vs middle
    i10 = idx(10)
    line10 = e_both[:, i10] if axis == "x" else e_both[i10, :]
    q = max(1, len(line10) // 10)
    ends_vs_mid = float(min(line10[:q].mean(), line10[-q:].mean()) / line10[len(line10) // 2 - q:len(line10) // 2 + q].mean())

    return {
        "name": name, "note": note, "axis": axis, "active_mm": [round(aw, 2), round(ah, 2)],
        "pairs_lit": len(pairs), "h_mm": h, "face_gap_mm": round(face_gap, 3), "pitch_mm": round(pitch, 2),
        "near_to_far_ratio": ratios, "scallop_max_over_min": scallop,
        "edge_ends_vs_middle_at_10mm": round(ends_vs_mid, 3),
        "colour_mix_error": mix_error(e_warm, e_cool, xs, ys, axis),
        "warm_positions_mm": [round(float(v), 2) for v in warm],
        "cool_positions_mm": [round(float(v), 2) for v in cool],
        "_grid": (gx, gy), "_e_warm": e_warm, "_extent": (aw, ah),
    }


def save_heatmaps(cases, path):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib.colors import LogNorm
    except ImportError:
        print("matplotlib not available; skipping heatmap", file=sys.stderr)
        return False
    fig, axes = plt.subplots(1, len(cases), figsize=(4.2 * len(cases), 6.4), constrained_layout=True)
    if len(cases) == 1:
        axes = [axes]
    for ax, c in zip(axes, cases):
        aw, ah = c["_extent"]
        e = c["_e_warm"] / np.percentile(c["_e_warm"], 50)
        im = ax.imshow(e, origin="upper", extent=(0, aw, ah, 0), norm=LogNorm(vmin=0.2, vmax=50), cmap="magma")
        wp, cp = np.array(c["warm_positions_mm"]), np.array(c["cool_positions_mm"])
        ax.scatter(np.full_like(wp, -1.2), wp, c="#ffb347", s=18, clip_on=False, label="warm")
        ax.scatter(np.full_like(cp, -1.2), cp, c="#9ecbff", s=18, clip_on=False, label="cool")
        ax.set_xlim(-2.0, aw)
        ax.set_ylim(ah, 0)
        ax.set_title(f"{c['name']}\nwarm string only", fontsize=9)
        ax.set_xlabel("mm from the lit edge")
        ax.set_aspect("equal")
    fig.colorbar(im, ax=axes, shrink=0.6, label="irradiance / screen median (log)")
    fig.savefig(path, dpi=130)
    plt.close(fig)
    return True


def save_profiles(cases, path):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return False
    fig, ax = plt.subplots(figsize=(7.5, 4.2), constrained_layout=True)
    for c, colour in zip(cases, ("#d9822b", "#2b6cb0", "#888888", "#55aa55")):
        gx, gy = c["_grid"]
        e = c["_e_warm"]
        prof, d = (np.median(e, axis=0), gx[0]) if c["axis"] == "x" else (np.median(e, axis=1), gy[:, 0])
        ax.semilogy(d, prof / prof[-1], color=colour, label=c["name"])
    ax.set_xlabel("distance from the lit edge of the active area (mm)")
    ax.set_ylabel("irradiance / far edge (log)")
    ax.grid(True, which="both", alpha=0.3)
    ax.legend(frameon=False, fontsize=8)
    ax.set_title("Grazing light falls off steeply: geometry only, one string lit", fontsize=9)
    fig.savefig(path, dpi=140)
    plt.close(fig)
    return True


def main():
    os.makedirs(OUT, exist_ok=True)
    full_h = float(os.environ.get("LED_FULL_ANGLE_H", 120))   # datasheet 2-theta-1/2 (XL-4008: 120 deg)
    full_v = float(os.environ.get("LED_FULL_ANGLE_V", 120))   # not given separately; assume the same
    m, n = exponent_for_full_angle(full_h), exponent_for_full_angle(full_v)
    # emitter centre above the panel's front surface: tape + PI + flex + half an LED.  On the 4.26in the bar
    # lies on the panel's border; on the 3.68in it lies beside the glass on a shelf at the panel-front plane.
    h = 0.05 + P.FLEX["stiffener_pi"] + P.FLEX["thickness"] + P.LED["body_h"] / 2
    pairs = strip_leds()
    face = P.BAR["face_x"]
    rev_a = [(c - 3.3, c + 3.3) for c in (49.63, 68.19, 86.75, 105.31, 123.87)]   # the first layout, for comparison

    cases = [
        run_case("4.26in, 6 pairs (this strip)", P.ACTIVE, pairs, P.ACTIVE["left"] - face, h, m, n),
        run_case("3.68in, 5 pairs lit (top pair folded under)", P.ACTIVE_368, pairs[1:],
                 P.ACTIVE_368["left"] - face, h, m, n,
                 note="the bar lies beside the glass, so the LED faces are 2.37 mm from the active area"),
        run_case("4.26in, rev A 5 pairs (before)", P.ACTIVE, rev_a, P.ACTIVE["left"] - face, h, m, n),
    ]
    top_edge = [(P.ACTIVE["left"] + (P.ACTIVE["right"] - P.ACTIVE["left"]) * (k + 0.5) / 6 - 3.3,
                 P.ACTIVE["left"] + (P.ACTIVE["right"] - P.ACTIVE["left"]) * (k + 0.5) / 6 + 3.3) for k in range(6)]
    extra = [run_case("4.26in, 6 pairs on the top short edge (not built)", P.ACTIVE, top_edge, 1.197, h, m, n, axis="y")]

    summary = [{k: v for k, v in c.items() if not k.startswith("_")} for c in cases + extra]
    with open(os.path.join(OUT, "optics_summary.json"), "w") as f:
        json.dump({"assumptions": {"full_angle_h": full_h, "full_angle_v": full_v, "emitter_h_mm": round(h, 3),
                                   "m": m, "n": n}, "cases": summary}, f, indent=2)
    save_heatmaps(cases[:2], os.path.join(OUT, "optics_heatmaps.png"))
    save_profiles(cases, os.path.join(OUT, "optics_profile.png"))
    for s in summary:
        print(s["name"], "| pitch", s["pitch_mm"], "gap", s["face_gap_mm"],
              "| near/far", {k: round(v, 1) for k, v in s["near_to_far_ratio"].items()},
              "| scallop", {k: round(v, 2) for k, v in s["scallop_max_over_min"].items()},
              "| ends/mid@10", s["edge_ends_vs_middle_at_10mm"], "| mix", s["colour_mix_error"])


if __name__ == "__main__":
    main()
