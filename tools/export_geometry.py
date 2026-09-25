"""Export the flat pattern and part positions to build/geometry.json for tools/blender_fold.py.

Run with KiCad's Python (it imports the generator's geometry, not the saved board):
    "C:\\Program Files\\KiCad\\9.0\\bin\\python.exe" tools\\export_geometry.py
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import params as P  # noqa: E402
import generate as G  # noqa: E402
import build_pcb as B  # noqa: E402


def main():
    out = {
        "outline": B.outline_polygon(32),
        "fold_y": P.PANEL["bottom"],
        "foot_b": P.FOOT["bottom_y"],
        "stiff_back_y": B.Y_STIFF,
        "tip_y": G.TIP_Y,
        "leds": [{"ref": d["ref"], "colour": d["colour"], "x": G.XP, "y": d["y"]} for d in G.LEDS],
        "led": {"len": P.LED["body_len"], "depth": P.LED["body_depth"], "h": P.LED["body_h"],
                "face_ahead": P.LED["face_ahead"], "rear_behind": P.LED["rear_behind"], "window": P.LED["window"]},
        "diodes": [{"ref": G.DW_REF, "x": B.DW_AT[0], "y": B.DW_AT[1]}, {"ref": G.DC_REF, "x": B.DC_AT[0], "y": B.DC_AT[1]}],
        "hinge_y": list(G.HINGE_Y),
        "front_pieces": B.front_pieces(),
        "back_stiffener": B.clip_below(B.outline_polygon(32), B.Y_STIFF),
        "panel_368": P.PANEL_368, "active_368": P.ACTIVE_368,
        "tps": [{"ref": k, "x": v[0], "y": v[1]} for k, v in B.TP_AT.items()],
        "fingers": [G.finger_x(n) for n in range(1, 7)],
        "panel": P.PANEL, "active": P.ACTIVE,
        "flex_t": P.FLEX["thickness"], "stiffener": P.FLEX["stiffener_pi"],
        # main board (KiCad frame), for the scene
        "board": {"x0": 44.237, "x1": 104.237, "y0": 37.0, "y1": 148.25, "t": 1.6,
                  "slot": [51.56, 141.2, 98.3, 142.5], "j3": [51.26, 123.25, 57.21, 128.07]},
    }
    path = os.path.join(G.ROOT, "build", "geometry.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    print(path)


if __name__ == "__main__":
    main()
