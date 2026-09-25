"""Render the light strip folded into the reader (panel + main board) with Blender, for either panel.

    tools\\export_geometry.py            (KiCad Python) writes build/geometry.json
    blender -b -P tools\\blender_fold.py -- [samples] [426|368]

426: the strip lies on the plain 4.26in panel's left border (enclosure silkscreen-enclosure-claude, light-strip
     tub): flat on the border, a U around the bottom glass edge, back under the glass, down the main board's
     FPC slot and along the board's back into J3.
368: the strip lies beside the 3.68in panel (enclosure silkscreen-enclosure-codex-x3, light-strip tub) on a
     shelf at the panel-front plane; the top pair folds back under the bar on its hinge; the tail folds over the
     glass edge with a small loop into the chin, drops through the slot and takes its spare length as a loop
     on the board's back.
x never changes; every point past the fold line (and, on the 3.68in, above the hinge) is placed by its
distance along that path.  Scene units are millimetres.  Renders go to docs/images/fold_*.png (426) and
docs/images/fold368_*.png (368).
"""
import json
import math
import os
import sys

import bmesh
import bpy
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = json.load(open(os.path.join(ROOT, "build", "geometry.json"), encoding="utf-8"))
ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SAMPLES = int(ARGS[0]) if len(ARGS) > 0 else 48
CASE = ARGS[1] if len(ARGS) > 1 else "426"

X0, Y0 = 44.237, 148.25           # main-board KiCad -> device frame (X right, Y up, Z toward the reader)
T = G["flex_t"]
H = T / 2
TAPE, STIFF = 0.05, G["stiffener"]
TIP_TARGET_Y = Y0 - 125.0         # contact tip fully home in J3
Z_BACK = -0.30                    # tail mid-plane on the board's back (ramps into J3's slot)

if CASE == "426":
    PANEL, ACTIVE = G["panel"], G["active"]
    Z_PANEL_REAR = 3.0                                   # plain panel on the midplate (light-strip tub stops)
    Z_PANEL_FRONT = Z_PANEL_REAR + PANEL["thickness"]
    Z_FOOT = Z_PANEL_FRONT + TAPE + STIFF + H            # flex mid-plane on the stiffened bar/foot
    Z_LEDGE = Z_PANEL_REAR + 0.5 + H                     # on the bare-glass ledge (0.5 mm TFT glass)
    FOLD_Y = G["fold_y"]                                 # the 4.26in bottom glass edge
    PS_END = 138.965
    PATH = [("line", 0.12), ("arc", 0.8 + H, 180.0), ("line", 0.38), ("arc", 0.8 + H, -90.0),
            ("line", 0.58), ("arc", 0.8 + H, 90.0), ("line", 60.0)]
    SOLVE = ("legs", (0, 2))                             # spare length goes into the U's legs
    PREFIX = "fold_"
else:
    PANEL, ACTIVE = G["panel_368"], G["active_368"]
    Z_PANEL_REAR = 2.6
    Z_PANEL_FRONT = Z_PANEL_REAR + PANEL["thickness"]    # 3.47: the shelf beside the glass is at this plane
    Z_FOOT = Z_PANEL_FRONT + TAPE + STIFF + H
    Z_LEDGE = Z_PANEL_REAR + 0.5 + H
    FOLD_Y = PANEL["bottom"]                             # the 3.68in bottom glass edge (flat y 141.2)
    PS_END = PANEL["ps_bottom"]
    # small loop into the chin, down the slot, onto the back, then a loop on the back that takes the rest
    PATH = [("line", 1.0), ("arc", 0.65 + H, 180.0), ("line", 0.45), ("arc", 0.4 + H, -90.0),
            ("line", 0.74), ("arc", 0.8 + H, 90.0),
            ("arc", 0.6, -40.0), ("arc", 0.6, 80.0), ("arc", 0.6, -40.0), ("line", 60.0)]
    SOLVE = ("bump", (6, 7, 8))                          # spare length goes into the back loop's angle
    PREFIX = "fold368_"
    # top pair folds back under the bar: path from the hinge's lower end, heading up the bar (+Y)
    HINGE_PATH = [("line", 0.25), ("arc", 0.55, -180.0), ("arc", 1.5, -31.5), ("arc", 1.5, 31.5), ("line", 60.0)]
Z_BAR_FLEX = Z_FOOT


def dev(x, y):
    return x - X0, Y0 - y


def walk(path, s, y, z, ang):
    """Point (Y, Z) and heading (deg, 0 = +Y, 90 = +Z) at distance s along a path of lines and arcs."""
    for seg in path:
        if seg[0] == "line":
            d = min(s, seg[1])
            y += d * math.cos(math.radians(ang))
            z += d * math.sin(math.radians(ang))
            s -= d
        else:
            r, sweep = seg[1], seg[2]
            L = abs(math.radians(sweep)) * r
            d = min(s, L)
            sign = 1 if sweep > 0 else -1
            cy = y + r * math.cos(math.radians(ang + 90 * sign))
            cz = z + r * math.sin(math.radians(ang + 90 * sign))
            a1 = ang - 90 * sign + math.degrees(d / r) * sign
            y, z = cy + r * math.cos(math.radians(a1)), cz + r * math.sin(math.radians(a1))
            ang += math.degrees(d / r) * sign
            s -= d
        if s <= 0:
            break
    return y, z, ang


def path_at(s):
    return walk(PATH, s, dev(0, FOLD_Y)[1], Z_LEDGE, 180.0)


def solve():
    """Stretch the chosen segments until the contact tip lands on J3."""
    kind, idx = SOLVE
    base = [PATH[i] for i in idx]

    def apply(k):
        if kind == "legs":
            for i, b in zip(idx, base):
                PATH[i] = ("line", b[1] + k / 2)
        else:
            a = 5.0 + k                                   # bump angle, degrees
            PATH[idx[0]] = ("arc", base[0][1], -a)
            PATH[idx[1]] = ("arc", base[1][1], 2 * a)
            PATH[idx[2]] = ("arc", base[2][1], -a)

    lo, hi = -0.3, 160.0 if kind == "bump" else 8.0
    for _ in range(60):
        mid = (lo + hi) / 2
        apply(mid)
        y, _, _ = path_at(G["tip_y"] - FOLD_Y)
        if y > TIP_TARGET_Y:
            lo = mid
        else:
            hi = mid
    apply(mid)
    return mid


SPARE = solve()
H0, H1 = G["hinge_y"]


def place(x, y):
    """Flat-pattern point -> 3D.  Returns (location, F-side normal)."""
    X = x - X0
    if CASE == "368" and y < H1:                       # hinge and the top pair, folded back under the bar
        Y, Z, ang = walk(HINGE_PATH, H1 - y, dev(0, H1)[1], Z_BAR_FLEX, 0.0)
        n = Vector((0, -math.sin(math.radians(ang)), math.cos(math.radians(ang))))
        return Vector((X, Y, Z)), n
    if y <= FOLD_Y:
        Y = Y0 - y
        if y <= G["foot_b"]:
            Z = Z_FOOT
        else:                                          # drapes off the stiffener onto the glass ledge
            t = min(1.0, (y - G["foot_b"]) / max(0.6, PS_END - G["foot_b"] + 0.8))
            Z = Z_FOOT + (Z_LEDGE - Z_FOOT) * (0.5 - 0.5 * math.cos(math.pi * t))
        return Vector((X, Y, Z)), Vector((0, 0, 1))
    Y, Z, ang = path_at(y - FOLD_Y)
    n = Vector((0, math.sin(math.radians(ang)), -math.cos(math.radians(ang))))
    return Vector((X, Y, Z)), n


# ------------------------------------------------------------------ helpers
def material(name, rgb, rough=0.5, metal=0.0, emit=None, strength=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = strength
    return m


def box(name, x0, y0, z0, x1, y1, z1, mat):
    bpy.ops.mesh.primitive_cube_add(size=1, location=((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
    o = bpy.context.active_object
    o.name = name
    o.scale = (abs(x1 - x0), abs(y1 - y0), abs(z1 - z0))
    bpy.ops.object.transform_apply(scale=True)
    o.data.materials.append(mat)
    return o


def oriented_box(name, centre, normal, size_x, size_along, size_n, mat):
    """Box sitting on the flex: size_n along the flex normal, size_along along the local path."""
    bpy.ops.mesh.primitive_cube_add(size=1, location=centre)
    o = bpy.context.active_object
    o.name = name
    o.scale = (size_x, size_along, size_n)
    o.rotation_mode = "QUATERNION"
    o.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(normal)
    bpy.ops.object.transform_apply(scale=True, rotation=True)
    o.data.materials.append(mat)
    return o


def bent_sheet(name, poly, cuts, offset, thickness, mat):
    """A flat polygon from the pattern, sliced along y and bent through place(); offset along the normal."""
    bm = bmesh.new()
    vs = [bm.verts.new((x, y, 0.0)) for x, y in poly]
    bm.faces.new(vs)
    for yc in cuts:
        geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
        bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(0, yc, 0), plane_no=(0, 1, 0))
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    for v in bm.verts:
        loc, n = place(v.co.x, v.co.y)
        v.co = loc + n * offset
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    o = bpy.data.objects.new(name, me)
    scene.collection.objects.link(o)
    o.data.materials.append(mat)
    sol = o.modifiers.new("t", "SOLIDIFY")
    sol.thickness = thickness
    sol.offset = 0.0
    return o


# ------------------------------------------------------------------ scene
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.samples = SAMPLES
scene.cycles.use_denoising = True
scene.render.resolution_x, scene.render.resolution_y = 1800, 1100
world = bpy.data.worlds.new("w")
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (0.82, 0.84, 0.88, 1)
world.node_tree.nodes["Background"].inputs[1].default_value = 0.55

M_GLASS = material("panel", (0.86, 0.86, 0.84), rough=0.35)
M_ACTIVE = material("epaper", (0.93, 0.92, 0.88), rough=0.9)
M_PCB = material("pcb", (0.05, 0.25, 0.12), rough=0.45)
M_FLEX = material("coverlay", (0.02, 0.02, 0.02), rough=0.35)
M_STIFF = material("pi", (0.55, 0.32, 0.05), rough=0.4)
M_LEDBODY = material("led", (0.95, 0.95, 0.93), rough=0.3)
M_WARM = material("warm", (1.0, 0.8, 0.45), emit=(1.0, 0.72, 0.4), strength=6.0)
M_COOL = material("cool", (0.9, 0.93, 1.0), emit=(0.85, 0.9, 1.0), strength=0.3)
M_GOLD = material("gold", (0.95, 0.72, 0.3), rough=0.25, metal=1.0)
M_BLACK = material("sot", (0.32, 0.32, 0.34), rough=0.35)
M_CONN = material("fh34", (0.9, 0.88, 0.8), rough=0.5)

px0, py1 = dev(PANEL["left"], PANEL["top"])
px1, py0 = dev(PANEL["right"], PANEL["bottom"])
box("panel", px0, py0, Z_PANEL_REAR, px1, py1, Z_PANEL_FRONT, M_GLASS)
ax0, ay1 = dev(ACTIVE["left"], ACTIVE["top"])
ax1, ay0 = dev(ACTIVE["right"], ACTIVE["bottom"])
box("active", ax0, ay0, Z_PANEL_FRONT, ax1, ay1, Z_PANEL_FRONT + 0.01, M_ACTIVE)

b = dict(G["board"])
if CASE == "368":
    b["y0"] = 62.0                                        # the x3 build trims the board above KiCad y 62
bx0, by1 = dev(b["x0"], b["y0"])
bx1, by0 = dev(b["x1"], b["y1"])
pcb = box("main_board", bx0, by0, 0, bx1, by1, b["t"], M_PCB)
sx0, sy1 = dev(b["slot"][0], b["slot"][1])
sx1, sy0 = dev(b["slot"][2], b["slot"][3])
cut = box("slot", sx0, sy0, -1, sx1, sy1, b["t"] + 1, M_PCB)
mod = pcb.modifiers.new("slot", "BOOLEAN")
mod.operation = "DIFFERENCE"
mod.object = cut
bpy.context.view_layer.objects.active = pcb
bpy.ops.object.modifier_apply(modifier="slot")
bpy.data.objects.remove(cut)
jx0, jy1 = dev(b["j3"][0], b["j3"][1])
jx1, jy0 = dev(b["j3"][2], b["j3"][3])
box("J3", jx0, jy0, -1.0, jx1, jy1, 0, M_CONN)

# ------------------------------------------------------------------ the flex and its stiffeners
cuts = [G["foot_b"] + 0.1 * k for k in range(0, 70)]                         # drape and ledge
cuts += [FOLD_Y + 0.08 * k for k in range(1, 180)]                           # the bends
cuts += [FOLD_Y + 14.4 + 1.0 * k for k in range(0, 14)]
if CASE == "368":
    cuts += [H0 - 1.0 + 0.06 * k for k in range(0, 100)]                     # the hinge's fold
bent_sheet("flex", G["outline"], cuts, 0.0, T, M_FLEX)
for i, piece in enumerate(G["front_pieces"]):
    bent_sheet(f"stiffener_front{i}", piece, cuts, -(H + STIFF / 2), STIFF, M_STIFF)
bent_sheet("stiffener_back", G["back_stiffener"], cuts, -(H + STIFF / 2), STIFF, M_STIFF)

# ------------------------------------------------------------------ parts
Lg = G["led"]
spots = []
for d in G["leds"]:
    loc, n = place(d["x"], d["y"])
    folded = n.z < 0
    c = loc + n * (H + Lg["h"] / 2)
    c.x += (Lg["face_ahead"] - Lg["rear_behind"]) / 2
    oriented_box(d["ref"], c, n, Lg["face_ahead"] + Lg["rear_behind"], Lg["len"], Lg["h"], M_LEDBODY)
    face = loc + n * (H + Lg["h"] / 2)
    face.x += Lg["face_ahead"] + 0.005
    oriented_box(d["ref"] + "_lens", face, n, 0.02, Lg["window"], Lg["h"] - 0.2,
                 M_WARM if d["colour"] == "warm" else M_COOL)
    if d["colour"] == "warm" and not folded:
        bpy.ops.object.light_add(type="SPOT", location=(face.x + 0.05, face.y, face.z),
                                 rotation=(0, math.radians(90), 0))
        L = bpy.context.active_object
        L.data.energy = 0.35
        L.data.spot_size = math.radians(120)
        L.data.color = (1.0, 0.75, 0.45)
        L.data.shadow_soft_size = 0.2
        spots.append(L)

for d in G["diodes"]:
    loc, n = place(d["x"], d["y"])
    oriented_box(d["ref"], loc + n * (H + 0.45), n, 1.25, 2.0, 0.9, M_BLACK)
for d in G["tps"]:
    loc, n = place(d["x"], d["y"])
    oriented_box(d["ref"], loc + n * (H + 0.01), n, 0.8, 0.8, 0.02, M_GOLD)
for fx in G["fingers"]:
    loc, n = place(fx, G["tip_y"] - 1.1)
    oriented_box("finger", loc + n * (H + 0.01), n, 0.3, 1.8, 0.02, M_GOLD)

tipY, tipZ, _ = path_at(G["tip_y"] - FOLD_Y)
print(f"case {CASE}: spare solved {SPARE:.2f} ({SOLVE[0]}); tip at device Y {tipY:.2f} Z {tipZ:.2f}")
if CASE == "368":
    ys = [walk(HINGE_PATH, s, dev(0, H1)[1], Z_BAR_FLEX, 0.0) for s in [k * 0.05 for k in range(0, 80)]]
    print(f"hinge loop: lowest flex mid-plane Z {min(p[1] for p in ys):.2f}, furthest Y {max(p[0] for p in ys):.2f}")

# ------------------------------------------------------------------ lights and cameras
bpy.ops.object.light_add(type="AREA", location=(-60, -40, 120))
key = bpy.context.active_object
key.data.energy = 2.2e5
key.data.size = 80
key.rotation_euler = (math.radians(25), math.radians(-30), 0)
bpy.ops.object.light_add(type="AREA", location=(80, -80, -60))
fill = bpy.context.active_object
fill.data.energy = 6e4
fill.data.size = 80
fill.rotation_euler = (math.radians(130), math.radians(35), 0)


def shoot(name, loc, target, lens=50):
    cam_data = bpy.data.cameras.new(name)
    cam_data.lens = lens
    cam_data.clip_start = 0.5
    cam_data.clip_end = 2000
    cam = bpy.data.objects.new(name, cam_data)
    scene.collection.objects.link(cam)
    cam.location = loc
    direction = Vector(target) - Vector(loc)
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    scene.camera = cam
    out = os.path.join(ROOT, "docs", "images", f"{PREFIX}{name}.png")
    scene.render.filepath = out
    bpy.ops.render.render(write_still=True)
    print("wrote", out)


if CASE == "426":
    shoot("overview", (-55, -70, 95), (22, 42, 3), lens=42)
    shoot("corner", (-22, -28, 22), (9, 9, 2), lens=55)
    shoot("back", (-14, -10, -38), (11, 15, -1), lens=60)
    night_cam = ((30, -60, 110), (28, 55, 4))
else:
    shoot("overview", (-55, -62, 92), (22, 46, 3), lens=42)
    shoot("corner", (-22, -26, 20), (9, 10, 2), lens=55)
    shoot("hinge", (-18, 62, 14), (0, 86, 2.8), lens=70)
    shoot("back", (-14, -10, -38), (11, 15, -1), lens=60)
    night_cam = ((30, -52, 104), (28, 52, 3))

world.node_tree.nodes["Background"].inputs[1].default_value = 0.004
key.data.energy = 0.0
fill.data.energy = 0.0
for L in spots:
    L.data.energy = 12000.0
scene.view_settings.exposure = 1.0
shoot("night_warm", *night_cam, lens=40)
