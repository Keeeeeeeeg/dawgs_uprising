# Dawgs Uprising -> Unity: realistic infantry (v2), modelled procedurally in Blender.
#   Real proportions (built in real metres, then scaled to the game's ~0.85 m soldier), rounded bodies lofted from
#   cross-sections, helmets / plate carriers / pouches / boots / gloves, a proper weapon per type, camouflage and
#   baked ambient occlusion in the vertex colours.
#   Same bones the Unity side expects (root, hips, thigh.*, torso = aim, arms = recoil, muzzle, REF_*), plus shins,
#   feet and a head, with an IK-solved Walk (planted feet, heel-toe roll, hip bob and sway) and an Idle.
# Run in Blender:  exec(open(r"...\du_infantry.py").read()); run()
import bpy, bmesh, math, os, random
from mathutils import Vector, Quaternion, Matrix, noise
from mathutils.bvhtree import BVHTree

def _project_root():
    """the Unity project folder: DAWGS_ROOT if set, else the folder above DawgsRig (found from this script or the open .blend)"""
    if os.environ.get("DAWGS_ROOT"):
        return os.environ["DAWGS_ROOT"]
    for cand in (globals().get("__file__"), bpy.data.filepath):
        if cand:
            d = os.path.dirname(os.path.dirname(os.path.abspath(cand)))
            if os.path.isdir(os.path.join(d, "Assets")):
                return d
    return os.getcwd()


OUT = os.environ.get("DU_OUT", os.path.join(_project_root(), "Assets", "Dawgs", "Rigged"))
K = 0.46            # Blender metres per real metre: a 1.83 m soldier with helmet comes out at the game's ~0.84 m
US = 0.6            # game units -> metres (for the REF markers)
FPS = 24
STRIDE = 1.2        # real metres per Walk cycle (two steps); Unity's DawgsUnitRig.strideLength = STRIDE * K
BETA = 0.6          # stance share of the gait cycle
X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))
TYPES = ("rifle", "mg", "at", "sniper")


def V(*a):
    return Vector(a)


def sm(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def g2b(x, y, z):
    return Vector((x * US, -z * US, y * US))


def lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hx(h):
    h = h.lstrip("#")
    return Vector([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)])


# ------------------------------------------------------------------ palette (display colours; linearised on write)
ARMY = [dict(uni="#5d6d49", dark="#3b4630", light="#7d8259", acc="#4d4535", vest="#627e49", band="#4f9a2c"),
        dict(uni="#6c5c49", dark="#4a3e30", light="#93836a", acc="#5b5a45", vest="#805c49", band="#a8382c")]
SHARED = dict(gear="#464739", strap="#34352a", boot="#2b2a25", sole="#1a1916", glove="#302f2a", gun="#262828",
              gunlite="#3b3e3e", tan="#6f6650", lens="#4f8798", shade="#1e2426", brass="#b8902d", wood="#6b4a2b",
              warhead="#4c5a3a", metal="#55595a")
SKIN = dict(rifle="#a8866c", mg="#8f6d55", at="#b39077", sniper="#9c7b63")
GHILLIE = ["#4d5a34", "#5e6b3c", "#6b6446", "#47472f", "#7a7350", "#3f4a2c"]


class Acc:
    """the soldier as one growing triangle/quad soup: positions (real metres), faces, bone weights, colour kind"""

    def __init__(s):
        s.V, s.F, s.W, s.C, s.HARD = [], [], [], [], []

    def add(s, verts, faces, kind, w, hard=False):
        base = len(s.V)
        for v in verts:
            v = Vector(v)
            s.V.append(v)
            s.C.append(kind(v) if callable(kind) else kind)
            s.W.append(dict(w(v) if callable(w) else w))
        for f in faces:
            s.F.append(tuple(base + i for i in f))
            s.HARD.append(hard)

    def add_bm(s, bm, kind, w, hard=True, M=None, recalc=False):
        if M is not None:
            bmesh.ops.transform(bm, matrix=M, verts=bm.verts)
        if recalc:
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.verts.index_update()
        s.add([v.co.copy() for v in bm.verts], [[v.index for v in f.verts] for f in bm.faces], kind, w, hard)
        bm.free()


# ------------------------------------------------------------------ lofting: rounded tubes from cross-sections
def cr(p0, p1, p2, p3, t):
    t2, t3 = t * t, t * t * t
    return 0.5 * ((2 * p1) + (p2 - p0) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (3 * p1 - p0 - 3 * p2 + p3) * t3)


def spline(ctrl, nper):
    """ctrl: [(point, rx, ry, p)] -> Catmull-Rom samples, nper per span"""
    n = len(ctrl)
    g = lambda i: ctrl[max(0, min(n - 1, i))]
    out = []
    for i in range(n - 1):
        for k in range(nper):
            t = k / nper
            a, b, c, d = g(i - 1), g(i), g(i + 1), g(i + 2)
            pt = cr(Vector(a[0]), Vector(b[0]), Vector(c[0]), Vector(d[0]), t)
            rx, ry, p = (cr(a[j], b[j], c[j], d[j], t) for j in (1, 2, 3))
            out.append((pt, max(0.002, rx), max(0.002, ry), max(1.2, p)))
    a = ctrl[-1]
    out.append((Vector(a[0]), a[1], a[2], a[3]))
    return out


def sec(a, rx, ry, p):
    c, s = math.cos(a), math.sin(a)
    e = 2.0 / p
    return rx * math.copysign(abs(c) ** e, c), ry * math.copysign(abs(s) ** e, s)


def loft(acc, ctrl, kind, w, ref=X, nper=3, seg=16, cap0=True, cap1=True, hard=False, warp=None, frame=None):
    """a tube through cross-sections. ref: the direction (or f(point)) the section's first radius lies along;
    frame=(xa, ya) fixes the section plane for every ring (then normals are recalculated)."""
    smp = spline([(c[0], c[1], c[2], c[3] if len(c) > 3 else 2.0) for c in ctrl], nper)
    n = len(smp)
    rings = []
    for i, (c, rx, ry, p) in enumerate(smp):
        if frame:
            xa, ya = frame
        else:
            t = smp[min(n - 1, i + 1)][0] - smp[max(0, i - 1)][0]
            t = t.normalized() if t.length > 1e-9 else Z.copy()
            r = Vector(ref(c) if callable(ref) else ref)
            xa = r - t * r.dot(t)
            if xa.length < 1e-6:
                r = Y if abs(t.dot(Y)) < 0.9 else X
                xa = r - t * r.dot(t)
            xa.normalize()
            ya = t.cross(xa)
        rings.append((c, xa, ya, rx, ry, p))
    verts, faces = [], []
    for i, (c, xa, ya, rx, ry, p) in enumerate(rings):
        for j in range(seg):
            a = 2 * math.pi * j / seg
            u, v = sec(a, rx, ry, p)
            q = c + xa * u + ya * v
            if warp:
                q = warp(q, i, n, a)
            verts.append(q)
    for i in range(n - 1):
        for j in range(seg):
            faces.append([i * seg + j, i * seg + (j + 1) % seg, (i + 1) * seg + (j + 1) % seg, (i + 1) * seg + j])
    if cap0:
        ci = len(verts)
        verts.append(rings[0][0].copy())
        faces += [[ci, (j + 1) % seg, j] for j in range(seg)]
    if cap1:
        ci = len(verts)
        verts.append(rings[-1][0].copy())
        b0 = (n - 1) * seg
        faces += [[ci, b0 + j, b0 + (j + 1) % seg] for j in range(seg)]
    if frame:
        bm = bmesh.new()
        vs = [bm.verts.new(v) for v in verts]
        for f in faces:
            try:
                bm.faces.new([vs[i] for i in f])
            except ValueError:
                pass
        acc.add_bm(bm, kind, w, hard, recalc=True)
    else:
        acc.add(verts, faces, kind, w, hard)


# ------------------------------------------------------------------ hard-surface primitives
def rotY(a):
    return Matrix.Rotation(a, 4, "Y")


def box(acc, c, size, kind, w, rot=None, bevel=0.0):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector(size), verts=bm.verts)
    if bevel > 0:
        bmesh.ops.bevel(bm, geom=list(bm.edges), offset=min(bevel, min(size) * 0.45), offset_type="OFFSET", segments=1,
                        profile=0.5, affect="EDGES", clamp_overlap=True)
    M = Matrix.Translation(Vector(c)) @ (rot if rot is not None else Matrix.Identity(4))
    acc.add_bm(bm, kind, w, True, M)


def cyl(acc, p0, p1, r0, kind, w, r1=None, seg=12, hard=True):
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=seg, radius1=r0, radius2=r0 if r1 is None else r1, depth=d.length)
    M = Matrix.Translation((p0 + p1) / 2) @ Z.rotation_difference(d.normalized()).to_matrix().to_4x4()
    acc.add_bm(bm, kind, w, hard, M)


def ellip(acc, c, radii, kind, w, rot=None, seg=16, rings=10, hard=False):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=rings, radius=1.0)
    bmesh.ops.scale(bm, vec=Vector(radii), verts=bm.verts)
    M = Matrix.Translation(Vector(c)) @ (rot if rot is not None else Matrix.Identity(4))
    acc.add_bm(bm, kind, w, hard, M)


def strap(acc, pts, width, thick, kind, w, ref, nper=2):
    """a flat band through pts; ref = the direction across the band's width (vector or f(point))"""
    loft(acc, [(p, width / 2, thick / 2, 4.0) for p in pts], kind, w, ref=ref, nper=nper, seg=8)


# ------------------------------------------------------------------ weights
def w_core(p):
    z = p.z
    if z <= 0.97:
        return {"hips": 1}
    if z <= 1.10:
        t = sm((z - 0.97) / 0.13)
        return {"hips": 1 - t, "torso": t}
    if z <= 1.53:
        return {"torso": 1}
    if z <= 1.60:
        t = sm((z - 1.53) / 0.07)
        return {"torso": 1 - t, "head": t}
    return {"head": 1}


def w_leg(s):
    T, S, F = "thigh." + s, "shin." + s, "foot." + s

    def f(p):
        z = p.z
        if z >= 1.00:
            return {"hips": 1}
        if z >= 0.88:
            t = sm((z - 0.88) / 0.12)
            return {"hips": t, T: 1 - t}
        if z >= 0.57:
            return {T: 1}
        if z >= 0.44:
            t = sm((z - 0.44) / 0.13)
            return {T: t, S: 1 - t}
        if z >= 0.21:
            return {S: 1}
        if z >= 0.12:
            t = sm((z - 0.12) / 0.09)
            return {S: t, F: 1 - t}
        return {F: 1}
    return f


HEAD = {"head": 1}
TORSO = {"torso": 1}
ARMS = {"arms": 1}
GUN = {"gun": 1}      # the weapon turns in the hands (checks, low ready)
MAG = {"mag": 1}      # and its magazine comes out


# ------------------------------------------------------------------ colour
def camo(p, P, scale=13.0):
    q = Vector((p.x, p.y, p.z * 0.75)) * scale
    n1 = noise.noise(q)
    n2 = noise.noise(q * 1.25 + V(5.2, 1.3, 7.7))
    n3 = noise.noise(q * 0.9 + V(11.0, 3.0, 2.0))
    if n1 > 0.24:
        c = hx(P["dark"])
    elif n2 > 0.26:
        c = hx(P["light"])
    elif n3 > 0.36:
        c = hx(P["acc"])
    else:
        c = hx(P["uni"])
    return c * (1 + 0.06 * noise.noise(p * 95))


def colour_of(kind, p, army, utype):
    P = ARMY[army]
    if kind in ("uni", "helm"):
        return camo(p, P, 13.0 if kind == "uni" else 17.0)
    if kind == "vest":
        return hx(P["vest"]) * (1 + 0.05 * noise.noise(p * 70))
    if kind == "pouch":
        return hx(P["vest"]) * 0.88 * (1 + 0.05 * noise.noise(p * 70))
    if kind == "band":
        return hx(P["band"]) * 0.92
    if kind == "skin":
        return hx(SKIN[utype]) * (1 + 0.04 * noise.noise(p * 60))
    if kind == "stub":
        return hx(SKIN[utype]).lerp(hx("#5a5048"), 0.3) * 0.9
    if kind == "hair":
        return hx("#2c241e") * (1 + 0.08 * noise.noise(p * 140))
    if kind.startswith("gh"):
        return hx(GHILLIE[int(kind[2:]) % len(GHILLIE)]) * (1 + 0.1 * noise.noise(p * 40))
    c = hx(SHARED[kind])
    if kind in ("gear", "strap", "boot", "glove"):
        c = c * (1 + 0.06 * noise.noise(p * 80))
    return c


# ------------------------------------------------------------------ body
SHO = {"L": V(-0.005, 0.185, 1.425), "R": V(-0.005, -0.185, 1.425)}
UPPER, FORE = 0.29, 0.265


def build_legs(acc):
    for s, sy in (("L", 1), ("R", -1)):
        wl = w_leg(s)
        ctrl = [(V(0.0, sy * 0.092, 1.02), .085, .080), (V(0.005, sy * 0.095, 0.95), .094, .088),
                (V(0.008, sy * 0.097, 0.86), .086, .082), (V(0.010, sy * 0.098, 0.76), .077, .073),
                (V(0.012, sy * 0.099, 0.66), .069, .065), (V(0.014, sy * 0.100, 0.57), .061, .058),
                (V(0.012, sy * 0.100, 0.50), .057, .055), (V(0.000, sy * 0.102, 0.43), .061, .054),
                (V(-0.008, sy * 0.104, 0.36), .062, .055), (V(-0.006, sy * 0.106, 0.29), .057, .051),
                (V(-0.003, sy * 0.108, 0.23), .054, .050), (V(-0.004, sy * 0.109, 0.19), .051, .048)]
        loft(acc, [(c, a * 1.07, b * 1.07, 2.2) for c, a, b in ctrl], "uni", wl, ref=X, nper=2, seg=14)
        # cargo pocket on the outer thigh
        box(acc, V(0.0, sy * 0.172, 0.70), (0.10, 0.03, 0.12), "uni", wl, bevel=0.012)
        # knee pad
        ellip(acc, V(0.064, sy * 0.10, 0.505), (0.024, 0.052, 0.066), "gear", {"thigh." + s: .3, "shin." + s: .7}, seg=12, rings=7)
        # boot: foot along +x on a sole, shaft round the ankle
        yb = sy * 0.11
        prof = [(-0.088, .05, .028), (-0.078, .085, .041), (-0.055, .105, .046), (-0.015, .125, .048), (0.035, .12, .049),
                (0.085, .088, .051), (0.135, .068, .052), (0.175, .058, .048), (0.205, .05, .04), (0.222, .036, .026)]
        loft(acc, [(V(x, yb + sy * 0.03 * max(0, x), 0.014 + h / 2), h / 2, wd, 4.5) for x, h, wd in prof], "boot",
             {"foot." + s: 1}, ref=Z, nper=1, seg=14)
        loft(acc, [(V(x - (0.006 if i == 0 else -0.006 if i == len(prof) - 1 else 0), yb + sy * 0.03 * max(0, x), 0.0115),
                    0.0115, wd + 0.005, 6.0) for i, (x, h, wd) in enumerate(prof)], "sole", {"foot." + s: 1}, ref=Z, nper=1, seg=12)
        loft(acc, [(V(-0.012, yb, 0.05), .052, .046), (V(-0.012, yb, 0.12), .056, .049), (V(-0.012, yb, 0.20), .057, .050),
                   (V(-0.012, yb, 0.245), .061, .053), (V(-0.012, yb, 0.25), .05, .045)], "boot", wl, ref=X, nper=1, seg=14)


def build_core(acc, utype):
    loft(acc, [(V(0.0, 0, 0.84), .05, .07, 2.2), (V(0.0, 0, 0.87), .095, .14, 2.4), (V(-0.005, 0, 0.92), .115, .172, 2.6),
               (V(-0.01, 0, 0.97), .12, .176, 2.6), (V(-0.005, 0, 1.02), .117, .167, 2.6), (V(0.0, 0, 1.07), .112, .158, 2.6)],
         "uni", w_core, ref=X, nper=2, seg=22)
    loft(acc, [(V(0.0, 0, 1.04), .108, .152, 2.4), (V(0.0, 0, 1.12), .112, .158, 2.4), (V(0.005, 0, 1.20), .118, .165, 2.5),
               (V(0.01, 0, 1.28), .126, .175, 2.6), (V(0.01, 0, 1.35), .128, .186, 2.8), (V(0.0, 0, 1.41), .118, .196, 3.0),
               (V(-0.005, 0, 1.46), .098, .178, 2.8), (V(-0.005, 0, 1.50), .075, .125, 2.4), (V(-0.005, 0, 1.535), .058, .068, 2.2)],
         "uni", w_core, ref=X, nper=2, seg=22)
    # belt and its pouches
    loft(acc, [(V(0, 0, 1.012), .112, .158, 2.6), (V(0, 0, 1.017), .125, .171, 2.6), (V(0, 0, 1.053), .125, .171, 2.6),
               (V(0, 0, 1.058), .112, .158, 2.6)], "strap", w_core, ref=X, nper=1, seg=24)
    for sy in (1, -1):
        box(acc, V(-0.035, sy * 0.172, 0.99), (0.075, 0.045, 0.085), "pouch", w_core, bevel=0.01)
    box(acc, V(-0.128, 0.085, 0.99), (0.045, 0.065, 0.095), "gear", w_core, bevel=0.012)
    # plate carrier, shoulder straps, magazine pouches
    loft(acc, [(V(0.0, 0, 1.07), .12, .155, 3), (V(0.0, 0, 1.08), .148, .172, 4), (V(0.005, 0, 1.16), .152, .176, 4),
               (V(0.01, 0, 1.26), .156, .182, 4), (V(0.01, 0, 1.34), .152, .18, 4), (V(0.005, 0, 1.395), .14, .165, 3.5),
               (V(0.0, 0, 1.41), .11, .14, 3)], "vest", TORSO, ref=X, nper=2, seg=24)
    for sy in (1, -1):
        strap(acc, [V(0.135, sy * 0.10, 1.385), V(0.085, sy * 0.115, 1.47), V(0.0, sy * 0.12, 1.505),
                    V(-0.085, sy * 0.115, 1.47), V(-0.135, sy * 0.10, 1.385)], 0.056, 0.016, "vest", TORSO, ref=Y)
    for y in (-0.075, 0.0, 0.075):
        box(acc, V(0.176, y, 1.185), (0.045, 0.068, 0.12), "pouch", TORSO, bevel=0.008)
        box(acc, V(0.179, y, 1.252), (0.05, 0.072, 0.016), "pouch", TORSO, bevel=0.005)
    box(acc, V(0.171, 0.0, 1.315), (0.035, 0.15, 0.065), "pouch", TORSO, bevel=0.008)
    # radio and antenna on the back
    box(acc, V(-0.172, 0.095, 1.30), (0.05, 0.07, 0.13), "gear", TORSO, bevel=0.008)
    cyl(acc, V(-0.172, 0.115, 1.36), V(-0.20, 0.125, 1.74 if utype != "sniper" else 1.62), 0.004, "strap", TORSO, seg=6)
    if utype in ("rifle", "mg"):
        box(acc, V(-0.208, -0.01, 1.245), (0.10, 0.25, 0.27), "gear", TORSO, bevel=0.03)
        cyl(acc, V(-0.21, -0.14, 1.41), V(-0.21, 0.12, 1.41), 0.038, "strap", TORSO, seg=14)
        if utype == "mg":
            box(acc, V(-0.235, -0.01, 1.15), (0.11, 0.2, 0.09), "pouch", TORSO, bevel=0.012)
    elif utype == "at":   # two spare rockets in a carrier on the back
        box(acc, V(-0.198, 0.0, 1.22), (0.08, 0.22, 0.22), "gear", TORSO, bevel=0.025)
        for y in (-0.06, 0.06):
            cyl(acc, V(-0.24, y, 1.20), V(-0.24, y, 1.40), 0.021, "gun", TORSO, seg=10)
            ellip(acc, V(-0.24, y, 1.47), (0.042, 0.042, 0.075), "warhead", TORSO, seg=14, rings=9)
            cyl(acc, V(-0.24, y, 1.535), V(-0.24, y, 1.60), 0.027, "warhead", TORSO, r1=0.005, seg=10, hard=False)
    # neck, head, face
    loft(acc, [(V(0.0, 0, 1.50), .052, .056), (V(0.005, 0, 1.56), .05, .053), (V(0.012, 0, 1.61), .048, .05)], "skin", w_core, ref=X, nper=2, seg=14)
    hc = [(0.055, 1.552, .024, .04), (0.045, 1.565, .05, .053), (0.03, 1.585, .074, .067), (0.015, 1.615, .09, .073),
          (0.01, 1.645, .097, .076), (0.01, 1.675, .101, .078), (0.01, 1.705, .100, .077), (0.008, 1.74, .092, .072),
          (0.005, 1.77, .072, .058), (0.003, 1.79, .04, .033), (0.0, 1.798, .01, .01)]
    def head_kind(p):
        if p.z > 1.618 and p.x < 0.028 - max(0.0, 1.66 - p.z) * 0.5:
            return "hair"
        if p.z < 1.612 and p.x > 0.035:
            return "stub"
        return "skin"
    loft(acc, [(V(x, 0, z), a, b, 2.0) for x, z, a, b in hc], head_kind, HEAD, ref=X, nper=2, seg=18)
    ellip(acc, V(0.113, 0, 1.652), (0.016, 0.011, 0.024), "skin", HEAD, rot=rotY(0.25), seg=8, rings=5)
    for sy in (1, -1):
        ellip(acc, V(0.0, sy * 0.079, 1.665), (0.016, 0.008, 0.027), "skin", HEAD, seg=8, rings=5)
    # ballistic glasses
    gl = [V(0.01 + 0.114 * math.cos(math.radians(a)), 0.09 * math.sin(math.radians(a)), 1.672) for a in (-72, -40, 0, 40, 72)]
    loft(acc, [(p, 0.017, 0.004, 4.0) for p in gl], "shade", HEAD, ref=Z, nper=2, seg=8)


def build_helmet(acc):
    def warp(q, i, n, a):
        f = 1 - sm((q.z - 1.665) / 0.075)
        q = q.copy()
        q.z += f * (0.03 * abs(math.sin(a)) ** 3 + 0.022 * max(0.0, math.cos(a)) ** 2)
        return q
    hc = [(1.665, .127, .117), (1.672, .141, .130), (1.70, .139, .127), (1.735, .135, .123), (1.77, .122, .111),
          (1.80, .098, .089), (1.822, .062, .056), (1.833, .02, .018)]
    loft(acc, [(V(0.007, 0, z), a, b, 2.2) for z, a, b in hc], "helm", HEAD, ref=X, nper=2, seg=22, warp=warp)
    loft(acc, [(V(0.007, 0, 1.716), .133, .121, 2.2), (V(0.007, 0, 1.718), .141, .129, 2.2), (V(0.007, 0, 1.733), .139, .127, 2.2),
               (V(0.007, 0, 1.735), .131, .119, 2.2)], "band", HEAD, ref=X, nper=1, seg=22, warp=warp)
    box(acc, V(0.143, 0, 1.75), (0.02, 0.045, 0.035), "gear", HEAD, rot=rotY(-0.35), bevel=0.005)
    for sy in (1, -1):
        box(acc, V(0.005, sy * 0.127, 1.748), (0.09, 0.008, 0.016), "gear", HEAD, bevel=0.003)
        ctr = V(0.01, 0, 1.65)
        strap(acc, [V(0.0, sy * 0.121, 1.695), V(0.035, sy * 0.088, 1.615), V(0.054, sy * 0.03, 1.562), V(0.057, 0, 1.553)],
              0.012, 0.004, "strap", HEAD, ref=lambda c: Vector(c) - ctr)


def build_boonie(acc, rnd):
    loft(acc, [(V(0.006, 0, 1.70), .108, .095), (V(0.006, 0, 1.75), .107, .094), (V(0.004, 0, 1.79), .096, .085),
               (V(0.002, 0, 1.812), .07, .062), (V(0.0, 0, 1.82), .02, .02)], "helm", HEAD, ref=X, nper=3, seg=24)
    rings = [(.098, .086, 1.716), (.15, .138, 1.708), (.19, .175, 1.696), (.205, .19, 1.686), (.19, .176, 1.684),
             (.15, .138, 1.696), (.10, .088, 1.704)]
    loft(acc, [(V(0.006, 0, z), a, b, 2.0) for a, b, z in rings], "helm", HEAD, nper=1, seg=24, frame=(X, Y))
    loft(acc, [(V(0.006, 0, 1.712), .110, .097), (V(0.006, 0, 1.728), .110, .097)], "strap", HEAD, ref=X, nper=1, seg=24)
    # scrim on the hat
    for i in range(60):
        a = rnd.uniform(-math.pi, math.pi)
        p = V(0.006 + 0.2 * math.cos(a), 0.185 * math.sin(a), 1.69)
        out = V(math.cos(a), math.sin(a), 0)
        blade(acc, p, out, rnd, HEAD, 0.03, 0.07)
    for i in range(40):
        a = rnd.uniform(-math.pi, math.pi)
        z = rnd.uniform(1.72, 1.80)
        r = 1.0 - sm((z - 1.76) / 0.06) * 0.4
        p = V(0.006 + 0.108 * r * math.cos(a), 0.095 * r * math.sin(a), z)
        blade(acc, p, V(math.cos(a), math.sin(a), 0.3), rnd, HEAD, 0.03, 0.06)


def blade(acc, p, out, rnd, w, lmin, lmax):
    """one strip of ghillie scrim hanging from p, leaning out along `out` (double sided)"""
    out = Vector(out).normalized()
    t = rnd.uniform(0.25, 0.7)
    d = (-Z * math.cos(t) + out * math.sin(t)).normalized()
    side = d.cross(out).normalized()
    side = (side + V(rnd.uniform(-.3, .3), rnd.uniform(-.3, .3), 0)).normalized()
    L = rnd.uniform(lmin, lmax)
    wd = rnd.uniform(0.012, 0.02)
    q = [p - side * wd / 2, p + side * wd / 2, p + d * L + side * wd * 0.3, p + d * L - side * wd * 0.3]
    kind = "gh%d" % rnd.randrange(len(GHILLIE))
    acc.add(q, [[0, 1, 2, 3]], kind, w)
    acc.add(q, [[3, 2, 1, 0]], kind, w)


def build_ghillie_cape(acc, rnd):
    for i in range(320):
        a = rnd.uniform(-math.pi, math.pi)
        if math.cos(a) > 0.55 and rnd.random() < 0.8:
            continue
        z = rnd.uniform(1.22, 1.52)
        rx, ry = (0.17, 0.19) if z < 1.42 else (0.12 - (z - 1.42) * 0.6, 0.20 - (z - 1.42) * 0.9)
        u, v = sec(a, rx, ry, 3.0)
        p = V(u, v, z)
        blade(acc, p, V(math.cos(a), math.sin(a), 0.6 if z > 1.42 else 0.0), rnd, TORSO if z > 1.12 else w_core, 0.05, 0.12)


def elbow(S, W, a, b, pole):
    d = W - S
    L = min(d.length, (a + b) * 0.995)
    dn = d.normalized()
    ca = max(-1.0, min(1.0, (a * a + L * L - b * b) / (2 * a * L)))
    pp = pole - dn * pole.dot(dn)
    pp.normalize()
    return S + dn * (a * ca) + pp * (a * math.sqrt(1 - ca * ca)), d.length


def fist(acc, G, axis, palm, sgn, r, W, w=ARMS):
    """a gloved hand closed round a bar through G along `axis`; palm side `palm`; fingers wrap towards axis x palm * sgn"""
    axis = axis.normalized()
    palm = (palm - axis * palm.dot(axis)).normalized()
    side = axis.cross(palm) * sgn
    pts = []
    for i in range(8):
        ang = math.radians(-10 + 240 * i / 7)
        pts.append((G + (palm * math.cos(ang) + side * math.sin(ang)) * r + axis * 0.002, 0.039 - 0.004 * i / 7, 0.011, 4.0))
    loft(acc, pts, "glove", w, ref=axis, nper=1, seg=10)
    P = G + palm * (r + 0.004)
    loft(acc, [(W, 0.03, 0.022, 3.0), (W + (P - W) * 0.5, 0.04, 0.02, 4.0), (P - axis * 0.004, 0.042, 0.018, 4.0)], "glove", w,
         ref=axis, nper=2, seg=10)
    t0 = G + palm * r * 0.9 + axis * 0.03 - side * 0.012
    t1 = G + (palm * 0.4 - side).normalized() * (r + 0.004) + axis * 0.04
    t2 = G - side * (r * 0.95) - palm * r * 0.2 + axis * 0.034
    loft(acc, [(t0, .012, .012, 2), (t1, .0105, .0105, 2), (t2, .009, .009, 2)], "glove", w, ref=axis, nper=2, seg=8)


def build_arms(acc, grips):
    """grips: {'R': (G, axis, palm, sgn, r, palm_off, axis_off), 'L': ...}; returns the elbows"""
    out = {}
    for s, sy in (("R", -1), ("L", 1)):
        G, axis, palm, sgn, r, po, ao = grips[s]
        axis = Vector(axis).normalized()
        pn = (Vector(palm) - axis * Vector(palm).dot(axis)).normalized()
        W = G + pn * po - axis * ao
        S = SHO[s]
        pole = V(-0.3, -0.55, -0.8) if s == "R" else V(0.05, 0.3, -1.0)
        E, dist = elbow(S, W, UPPER, FORE, pole)
        out[s] = (S, E, W, dist)
        u = (E - S).normalized()
        f = (W - E).normalized()
        n = u.cross(f)
        nref = n.normalized() if n.length > 1e-4 else Y
        ctrl = [(S - u * 0.012, .062, .059), (S + u * 0.07, .057, .054), (S + u * 0.16, .051, .049), (S + u * 0.24, .047, .046),
                (E, .046, .045), (E + f * 0.06, .047, .045), (E + f * 0.14, .043, .041), (W - f * 0.04, .037, .035),
                (W - f * 0.012, .039, .037), (W + f * 0.012, .033, .031)]

        def kind(p, S=S, u=u, W=W, f=f):
            if (p - W).dot(f) > -0.03:
                return "glove"
            d = (p - S).dot(u)
            return "band" if 0.085 < d < 0.12 and (p - S).length < 0.16 else "uni"

        UA, FA, HA = "upperarm." + s, "forearm." + s, "hand." + s
        mid = (u + f).normalized()

        def wfn(p, S=S, u=u, E=E, W=W, f=f, mid=mid, UA=UA, FA=FA, HA=HA):
            dw = (p - W).dot(f)
            if dw > -0.03:                                   # wrist: forearm -> hand
                t = sm((dw + 0.03) / 0.03)
                return {FA: 1 - t, HA: t}
            e = (p - E).dot(mid)
            if e > -0.035:                                   # elbow: upper arm -> forearm
                t = sm((e + 0.035) / 0.07)
                return {UA: 1 - t, FA: t}
            t = sm(((p - S).dot(u) + 0.01) / 0.12)           # shoulder: chest -> upper arm
            return {"torso": 1 - t, UA: t}
        loft(acc, [(c, a * 1.06, b * 1.06, 2.2) for c, a, b in ctrl], kind, wfn, ref=nref, nper=2, seg=12)
        ellip(acc, S + V(0, sy * 0.002, 0.008), (0.062, 0.056, 0.058), "uni", {"torso": .6, UA: .4}, seg=12, rings=8)
        fist(acc, G, axis, Vector(palm), sgn, r, W, {HA: 1})
    return out


# ------------------------------------------------------------------ weapons (forward = +x; returns muzzle and grips)
def sling(acc, x0, g, b, front):
    strap(acc, [V(x0 + front, g + 0.02, b - 0.025), V(x0 + front * 0.78, g + 0.035, b - 0.13), V(x0 + front * 0.47, g + 0.042, b - 0.17),
                V(x0 + 0.13, g + 0.032, b - 0.09), V(x0 + 0.05, g + 0.022, b - 0.05)], 0.024, 0.004, "strap", GUN, ref=Y)


def pistol_grip(acc, c, tilt, size=(0.028, 0.026, 0.075), kind="gun"):
    box(acc, c, size, kind, GUN, rot=rotY(tilt), bevel=0.006)
    return Vector((math.sin(tilt), 0, math.cos(tilt)))


def gun_rifle(acc):
    x0, b, g = 0.06, 1.40, -0.11
    box(acc, V(x0 + 0.08, g, b - 0.028), (0.16, 0.034, 0.075), "gunlite", GUN, bevel=0.008)
    box(acc, V(x0 + 0.004, g, b - 0.03), (0.012, 0.036, 0.08), "gun", GUN, bevel=0.003)
    cyl(acc, V(x0 + 0.14, g, b - 0.004), V(x0 + 0.25, g, b - 0.004), 0.013, "gun", GUN)
    box(acc, V(x0 + 0.33, g, b - 0.022), (0.17, 0.032, 0.04), "gun", GUN, bevel=0.004)
    box(acc, V(x0 + 0.335, g, b + 0.012), (0.20, 0.03, 0.034), "gun", GUN, bevel=0.004)
    box(acc, V(x0 + 0.43, g, b + 0.034), (0.36, 0.02, 0.008), "gun", GUN)
    box(acc, V(x0 + 0.375, g, b - 0.10), (0.032, 0.024, 0.12), "gun", MAG, rot=rotY(-0.22), bevel=0.004)
    ax = pistol_grip(acc, V(x0 + 0.255, g, b - 0.07), 0.30, kind="gunlite")
    box(acc, V(x0 + 0.295, g, b - 0.05), (0.05, 0.006, 0.006), "gun", GUN)
    cyl(acc, V(x0 + 0.43, g, b), V(x0 + 0.69, g, b), 0.022, "gunlite", GUN, seg=8)
    box(acc, V(x0 + 0.70, g, b + 0.02), (0.02, 0.012, 0.04), "gun", GUN)
    cyl(acc, V(x0 + 0.69, g, b), V(x0 + 0.86, g, b), 0.0085, "gun", GUN, seg=10)
    cyl(acc, V(x0 + 0.86, g, b), V(x0 + 0.905, g, b), 0.012, "gun", GUN, seg=10)
    cyl(acc, V(x0 + 0.30, g, b + 0.068), V(x0 + 0.41, g, b + 0.068), 0.019, "gun", GUN, seg=14)
    box(acc, V(x0 + 0.355, g, b + 0.046), (0.05, 0.02, 0.03), "gun", GUN)
    cyl(acc, V(x0 + 0.296, g, b + 0.068), V(x0 + 0.302, g, b + 0.068), 0.016, "lens", GUN, seg=14)
    cyl(acc, V(x0 + 0.408, g, b + 0.068), V(x0 + 0.414, g, b + 0.068), 0.017, "lens", GUN, seg=14)
    sling(acc, x0, g, b, 0.62)
    return dict(muzzle=V(x0 + 0.905, g, b), mag=V(x0 + 0.375, g, b - 0.10), mag_out=Vector((math.sin(0.22), 0, -math.cos(0.22))),
                R=(V(x0 + 0.248, g, b - 0.072), ax, V(-1, -0.35, 0), 1, 0.026, 0.055, 0.035),
                L=(V(x0 + 0.45, g, b - 0.004), X, V(0, 0.3, -1), -1, 0.036, 0.045, 0.07))


def gun_mg(acc):
    x0, b, g = 0.05, 1.375, -0.115
    box(acc, V(x0 + 0.10, g, b - 0.03), (0.20, 0.042, 0.085), "gunlite", GUN, bevel=0.01)
    box(acc, V(x0 + 0.35, g, b - 0.005), (0.30, 0.052, 0.08), "gun", GUN, bevel=0.006)
    box(acc, V(x0 + 0.38, g, b + 0.044), (0.17, 0.05, 0.02), "gun", GUN, bevel=0.004)
    box(acc, V(x0 + 0.40, g, b + 0.058), (0.12, 0.02, 0.008), "gun", GUN)
    ax = pistol_grip(acc, V(x0 + 0.26, g, b - 0.085), 0.30, size=(0.03, 0.03, 0.08))
    box(acc, V(x0 + 0.30, g, b - 0.06), (0.05, 0.006, 0.006), "gun", GUN)
    box(acc, V(x0 + 0.39, g + 0.058, b - 0.095), (0.11, 0.055, 0.12), "gear", GUN, bevel=0.006)
    for i in range(7):   # the belt of rounds feeding from the box
        t = i / 6
        p = V(x0 + 0.385 - 0.01 * t, g + 0.05 - 0.022 * t, b - 0.03 + 0.055 * math.sin(t * 1.4))
        cyl(acc, p + V(-0.024, 0, 0), p + V(0.026, 0, 0), 0.0055, "brass", GUN, r1=0.004, seg=6)
    box(acc, V(x0 + 0.58, g, b), (0.16, 0.048, 0.05), "gunlite", GUN, bevel=0.006)
    cyl(acc, V(x0 + 0.66, g, b), V(x0 + 1.02, g, b), 0.012, "gun", GUN, seg=10)
    box(acc, V(x0 + 0.62, g, b + 0.064), (0.09, 0.012, 0.012), "gun", GUN)
    for dx in (0.585, 0.655):
        box(acc, V(x0 + dx, g, b + 0.045), (0.01, 0.01, 0.04), "gun", GUN)
    box(acc, V(x0 + 0.98, g, b + 0.025), (0.012, 0.008, 0.03), "gun", GUN)
    cyl(acc, V(x0 + 1.02, g, b), V(x0 + 1.075, g, b), 0.016, "gun", GUN, r1=0.018, seg=10)
    box(acc, V(x0 + 0.73, g, b - 0.015), (0.02, 0.03, 0.02), "gun", GUN)
    for dy in (-0.012, 0.012):
        cyl(acc, V(x0 + 0.74, g + dy, b - 0.022), V(x0 + 1.0, g + dy, b - 0.026), 0.005, "gun", GUN, seg=6)
    sling(acc, x0, g, b, 0.64)
    return dict(muzzle=V(x0 + 1.075, g, b), mag=V(x0 + 0.39, g + 0.058, b - 0.03), mag_out=V(0, 0, -1),
                R=(V(x0 + 0.252, g, b - 0.087), ax, V(-1, -0.35, 0), 1, 0.027, 0.055, 0.035),
                L=(V(x0 + 0.46, g, b - 0.004), X, V(0, 0.3, -1), -1, 0.038, 0.045, 0.07))


def gun_at(acc):
    b, g = 1.505, -0.155
    cyl(acc, V(-0.38, g, b), V(0.62, g, b), 0.034, "gun", GUN, seg=14)
    cyl(acc, V(0.02, g, b), V(0.30, g, b), 0.042, "wood", GUN, seg=14)
    cyl(acc, V(-0.52, g, b), V(-0.38, g, b), 0.058, "gun", GUN, r1=0.034, seg=14)
    cyl(acc, V(0.60, g, b), V(0.625, g, b), 0.038, "gun", GUN, seg=14)
    cyl(acc, V(0.625, g, b), V(0.70, g, b), 0.02, "warhead", GUN, seg=10)
    ellip(acc, V(0.78, g, b), (0.10, 0.052, 0.052), "warhead", GUN, seg=16, rings=10)
    cyl(acc, V(0.86, g, b), V(0.96, g, b), 0.03, "warhead", GUN, r1=0.006, seg=12, hard=False)
    cyl(acc, V(0.96, g, b), V(0.975, g, b), 0.005, "metal", GUN, seg=6)
    ax = pistol_grip(acc, V(0.20, g, b - 0.072), 0.25)
    box(acc, V(0.235, g, b - 0.05), (0.05, 0.006, 0.006), "gun", GUN)
    ax2 = pistol_grip(acc, V(0.37, g, b - 0.07), 0.15, size=(0.026, 0.026, 0.07), kind="wood")
    box(acc, V(0.12, g + 0.05, b + 0.03), (0.07, 0.025, 0.045), "gun", GUN, bevel=0.004)
    cyl(acc, V(0.08, g + 0.05, b + 0.036), V(0.086, g + 0.05, b + 0.036), 0.009, "lens", GUN, seg=10)
    for x in (0.1, 0.5):
        box(acc, V(x, g, b + 0.045), (0.012, 0.008, 0.025), "gun", GUN)
    strap(acc, [V(0.55, g - 0.03, b - 0.02), V(0.40, g - 0.045, b - 0.14), V(0.15, g - 0.05, b - 0.17), V(-0.10, g - 0.04, b - 0.10),
                V(-0.25, g - 0.03, b - 0.02)], 0.024, 0.004, "strap", GUN, ref=Y)
    return dict(muzzle=V(0.975, g, b), mag=V(0.62, g, b), mag_out=V(0, 0, -1),
                R=(V(0.195, g, b - 0.074), ax, V(-1, -0.35, 0), 1, 0.026, 0.055, 0.035),
                L=(V(0.368, g, b - 0.07), ax2, V(-1, 0.35, 0), -1, 0.026, 0.055, 0.035))


def gun_sniper(acc):
    x0, b, g = 0.05, 1.385, -0.11
    box(acc, V(x0 + 0.12, g, b - 0.04), (0.24, 0.036, 0.09), "tan", GUN, bevel=0.012)
    box(acc, V(x0 + 0.16, g, b + 0.012), (0.12, 0.03, 0.02), "tan", GUN, bevel=0.006)
    ax = pistol_grip(acc, V(x0 + 0.27, g, b - 0.05), 0.35, size=(0.034, 0.03, 0.07), kind="tan")
    box(acc, V(x0 + 0.52, g, b - 0.022), (0.36, 0.04, 0.045), "tan", GUN, bevel=0.01)
    cyl(acc, V(x0 + 0.30, g, b), V(x0 + 0.50, g, b), 0.016, "gun", GUN)
    cyl(acc, V(x0 + 0.33, g, b), V(x0 + 0.33, g - 0.045, b - 0.012), 0.004, "gun", GUN, seg=6)
    ellip(acc, V(x0 + 0.33, g - 0.048, b - 0.013), (0.008, 0.008, 0.008), "gun", GUN, seg=8, rings=6)
    box(acc, V(x0 + 0.42, g, b - 0.05), (0.06, 0.025, 0.04), "gun", MAG)
    box(acc, V(x0 + 0.30, g, b - 0.06), (0.05, 0.006, 0.006), "gun", GUN)
    cyl(acc, V(x0 + 0.26, g, b + 0.058), V(x0 + 0.52, g, b + 0.058), 0.017, "gun", GUN, seg=14)
    cyl(acc, V(x0 + 0.20, g, b + 0.058), V(x0 + 0.26, g, b + 0.058), 0.024, "gun", GUN, r1=0.017, seg=14)
    cyl(acc, V(x0 + 0.52, g, b + 0.058), V(x0 + 0.60, g, b + 0.058), 0.017, "gun", GUN, r1=0.028, seg=14)
    cyl(acc, V(x0 + 0.60, g, b + 0.058), V(x0 + 0.62, g, b + 0.058), 0.028, "gun", GUN, seg=14)
    cyl(acc, V(x0 + 0.39, g, b + 0.07), V(x0 + 0.39, g, b + 0.092), 0.01, "gun", GUN, seg=10)
    cyl(acc, V(x0 + 0.39, g - 0.015, b + 0.058), V(x0 + 0.39, g - 0.037, b + 0.058), 0.009, "gun", GUN, seg=10)
    for dx in (0.32, 0.46):
        box(acc, V(x0 + dx, g, b + 0.03), (0.015, 0.03, 0.03), "gun", GUN)
    cyl(acc, V(x0 + 0.197, g, b + 0.058), V(x0 + 0.203, g, b + 0.058), 0.022, "lens", GUN, seg=14)
    cyl(acc, V(x0 + 0.617, g, b + 0.058), V(x0 + 0.623, g, b + 0.058), 0.025, "lens", GUN, seg=14)
    cyl(acc, V(x0 + 0.50, g, b), V(x0 + 1.08, g, b), 0.012, "gun", GUN, r1=0.009, seg=10)
    cyl(acc, V(x0 + 1.08, g, b), V(x0 + 1.14, g, b), 0.014, "gun", GUN, seg=8)
    for dy in (-0.012, 0.012):
        cyl(acc, V(x0 + 0.68, g + dy, b - 0.045), V(x0 + 0.94, g + dy, b - 0.05), 0.005, "gun", GUN, seg=6)
    sling(acc, x0, g, b, 0.66)
    return dict(muzzle=V(x0 + 1.14, g, b), mag=V(x0 + 0.42, g, b - 0.05), mag_out=V(0, 0, -1),
                R=(V(x0 + 0.27, g, b - 0.05), ax, V(-1, -0.35, 0), 1, 0.03, 0.055, 0.035),
                L=(V(x0 + 0.45, g, b - 0.03), X, V(0, 0.3, -1), -1, 0.04, 0.045, 0.07))


GUNS = dict(rifle=gun_rifle, mg=gun_mg, at=gun_at, sniper=gun_sniper)


# ------------------------------------------------------------------ assembly
def build_geometry(utype):
    acc = Acc()
    rnd = random.Random(sum(map(ord, utype)))
    tris = lambda: sum(len(f) - 2 for f in acc.F)
    st = {}
    n0 = 0
    for nm, fn in (("legs", lambda: build_legs(acc)), ("core", lambda: build_core(acc, utype)),
                   ("head", lambda: (build_boonie(acc, rnd), build_ghillie_cape(acc, rnd)) if utype == "sniper" else build_helmet(acc)),
                   ("gun", lambda: st.__setitem__("_gun", GUNS[utype](acc))), ("arms", lambda: st.__setitem__("_arms", build_arms(acc, st["_gun"])))):
        fn()
        st[nm] = tris() - n0
        n0 = tris()
    acc.stats = {k: v for k, v in st.items() if not k.startswith("_")}
    return acc, st["_gun"], st["_arms"]


def ao_and_colour(acc, me, army, utype):
    bvh = BVHTree.FromPolygons([tuple(v) for v in acc.V], [list(f) for f in acc.F], all_triangles=False, epsilon=0.0)
    me.update()
    normals = [v.normal.copy() for v in me.vertices]
    # cosine-ish hemisphere directions (z-up)
    dirs = []
    nd = 14
    for i in range(nd):
        zz = 1 - (i + 0.5) / nd * 0.92
        r = math.sqrt(max(0.0, 1 - zz * zz))
        ph = i * 2.39996
        dirs.append(Vector((r * math.cos(ph), r * math.sin(ph), zz)))
    out = []
    for i, p in enumerate(acc.V):
        n = normals[i]
        if n.length < 0.5:
            out.append(1.0)
            continue
        t = n.orthogonal().normalized()
        bt = n.cross(t)
        o = p + n * 0.003
        hit = 0
        for d in dirs:
            ww = t * d.x + bt * d.y + n * d.z
            if bvh.ray_cast(o, ww, 0.13)[0] is not None:
                hit += 1
        occ = hit / nd
        out.append(1.0 - (0.35 if acc.C[i] in ("skin", "stub") else 0.62) * occ ** 0.85)
    cols = []
    for i, p in enumerate(acc.V):
        c = colour_of(acc.C[i], p, army, utype)
        grad = 0.84 + 0.16 * min(1.0, p.z / 0.9)
        k = out[i] * grad
        cols.append((lin(min(1, c.x)) * k, lin(min(1, c.y)) * k, lin(min(1, c.z)) * k, 1.0))
    return cols


def make_armature(name, coll, bones):
    arm = bpy.data.armatures.new(name)
    ao = bpy.data.objects.new(name, arm)
    coll.objects.link(ao)
    arm.display_type = "STICK"
    ao.show_in_front = True
    bpy.context.view_layer.objects.active = ao
    bpy.ops.object.mode_set(mode="EDIT")
    for bn, h, t, par, deform in bones:
        eb = arm.edit_bones.new(bn)
        eb.head, eb.tail = h, t
        eb.use_deform = deform
        if par:
            eb.parent = arm.edit_bones[par]
    bpy.ops.object.mode_set(mode="OBJECT")
    return ao


POLE = {"R": V(-0.3, -0.55, -0.8), "L": V(0.05, 0.3, -1.0)}     # which way each elbow points (as build_arms)


def bone_spec(gun, arms):
    muzzle = gun["muzzle"]
    grip = gun["R"][0]
    B = [("root", V(0, 0, 0), V(0, 0, 0.3), None, False),
         ("hips", V(0, 0, 0.95), V(0, 0, 1.05), "root", True)]
    for s, sy in (("L", 1), ("R", -1)):
        B += [("thigh." + s, V(0, sy * 0.095, 0.93), V(0.012, sy * 0.10, 0.50), "hips", True),
              ("shin." + s, V(0.012, sy * 0.10, 0.50), V(0, sy * 0.11, 0.09), "thigh." + s, True),
              ("foot." + s, V(0, sy * 0.11, 0.09), V(0.13, sy * 0.115, 0.03), "shin." + s, True)]
    B += [("torso", V(0, 0, 1.05), V(0, 0, 1.45), "hips", True),
          ("head", V(0.01, 0, 1.56), V(0.01, 0, 1.75), "torso", True),
          ("arms", V(0, 0, 1.40), V(0.30, 0, 1.40), "torso", True),
          # the weapon pivots at the trigger hand; the magazine slides out of it; each arm is a shoulder-elbow-wrist chain
          ("gun", grip, grip + V(0.3, 0, 0), "arms", True),
          ("mag", gun["mag"], gun["mag"] + gun["mag_out"] * 0.1, "gun", True),
          ("muzzle", muzzle, muzzle + V(0.1, 0, 0), "gun", False)]
    for s in ("L", "R"):
        S, E, W, _ = arms[s]
        G = gun[s][0]
        B += [("upperarm." + s, S, E, "arms", True),
              ("forearm." + s, E, W, "upperarm." + s, True),
              ("hand." + s, W, W + (G - W).normalized() * 0.08, "forearm." + s, True)]
    out = [(n, h * K, t * K, p, d) for n, h, t, p, d in B]
    out += [("REF_X", g2b(1, 0, 0), g2b(1, 0.1, 0), "root", False),
            ("REF_Y", g2b(0, 1, 0), g2b(0, 1.1, 0), "root", False),
            ("REF_Z", g2b(0, 0, 1), g2b(0, 0.1, 1), "root", False)]
    return out


def make_soldier(utype, army, coll):
    unit = "%s_%d" % (utype, army)
    name = "inf_" + unit
    for o in [o for o in bpy.data.objects if o.name in (name, name + "_rig")]:
        bpy.data.objects.remove(o, do_unlink=True)
    for a in [a for a in bpy.data.actions if a.name.startswith(name + "|")]:
        bpy.data.actions.remove(a)
    acc, gun, arms = build_geometry(utype)
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v * K) for v in acc.V], [], [list(f) for f in acc.F])
    me.update()
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.faces.ensure_lookup_table()
    for f in bm.faces:
        f.smooth = True
    for e in bm.edges:
        lf = e.link_faces
        if len(lf) == 2 and (acc.HARD[lf[0].index] or acc.HARD[lf[1].index]):
            if lf[0].normal.angle(lf[1].normal, 0) > math.radians(38):
                e.smooth = False
    bm.to_mesh(me)
    bm.free()
    me.update()
    cols = ao_and_colour(acc, me, army, utype)
    ca = me.color_attributes.new("Col", "FLOAT_COLOR", "CORNER")
    data = [0.0] * (len(me.loops) * 4)
    for li, lp in enumerate(me.loops):
        data[li * 4:li * 4 + 4] = cols[lp.vertex_index]
    ca.data.foreach_set("color", data)
    me.color_attributes.active_color = ca
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    ao = make_armature(name + "_rig", coll, bone_spec(gun, arms))
    groups = {}
    for i, w in enumerate(acc.W):
        tot = sum(w.values()) or 1.0
        for bn, x in w.items():
            if x > 1e-4:
                groups.setdefault(bn, []).append((i, x / tot))
    for bn, lst in groups.items():
        vg = ob.vertex_groups.new(name=bn)
        for i, x in lst:
            vg.add([i], x, "REPLACE")
    md = ob.modifiers.new("Armature", "ARMATURE")
    md.object = ao
    ob.parent = ao
    animate(ao, name, utype, gun)
    return unit, ob, ao, acc, arms


# ------------------------------------------------------------------ animation
def new_action(ao, unit, clip):
    act = bpy.data.actions.new(unit + "|" + clip)
    act.use_fake_user = True
    if ao.animation_data is None:
        ao.animation_data_create()
    ao.animation_data.action = act
    return act


def push_nla(ao, act, clip):
    ad = ao.animation_data
    tr = ad.nla_tracks.new()
    tr.name = clip
    st = tr.strips.new(clip, int(act.frame_range[0]), act)
    st.name = clip
    ad.action = None


def reset_pose(ao):
    for pb in ao.pose.bones:
        pb.location = (0, 0, 0)
        pb.rotation_quaternion = (1, 0, 0, 0)
        pb.rotation_euler = (0, 0, 0)


class Poser:
    """turns armature-space wishes (where the ankles go, how the pelvis and chest turn) into keyed bone rotations"""

    def __init__(s, ao):
        s.ao = ao
        s.pb = ao.pose.bones
        s.R = {b.name: b.matrix_local.to_quaternion() for b in ao.data.bones}
        s.H = {b.name: b.head_local / K for b in ao.data.bones}
        s.T = {b.name: b.tail_local / K for b in ao.data.bones}

    def local(s, bn, Dpar, D):
        R = s.R[bn]
        return R.inverted() @ Dpar.inverted() @ D @ R

    def key(s, f, bn, rot=None, loc=None):
        pb = s.pb[bn]
        if rot is not None:
            pb.rotation_mode = "QUATERNION"
            pb.rotation_quaternion = rot
            pb.keyframe_insert("rotation_quaternion", frame=f)
        if loc is not None:
            pb.location = loc
            pb.keyframe_insert("location", frame=f)

    def frames(s, hip_off, yaw, roll, torso_D, head_D, arms_D=None, arms_off=V(0, 0, 0), gun_R=None, gun_off=V(0, 0, 0)):
        """where the chest, head, shoulders and gun end up for these wishes (real metres, armature space).
        gun_R: the gun's own turn in the arms' frame (about the trigger hand); gun_off: its shift in the arms' frame"""
        Dh = Quaternion(Z, yaw) @ Quaternion(X, roll)
        hh = s.H["hips"] + hip_off
        Ht = hh + Dh @ (s.H["torso"] - s.H["hips"])
        Da = arms_D if arms_D is not None else torso_D
        Ha = Ht + torso_D @ (s.H["arms"] - s.H["torso"]) + arms_off
        Dg = Da @ gun_R if gun_R is not None else Da
        Hg = Ha + Da @ (s.H["gun"] - s.H["arms"] + gun_off)
        Hh = Ht + torso_D @ (s.H["head"] - s.H["torso"])
        fr = dict(Dh=Dh, hh=hh, Ht=Ht, Dt=torso_D, Da=Da, Ha=Ha, Dg=Dg, Hg=Hg, Hh=Hh, Dhd=head_D)
        fr["torso"] = lambda p, fr=fr: fr["Ht"] + fr["Dt"] @ (Vector(p) - s.H["torso"])      # a rest-pose point carried by the chest
        fr["head"] = lambda p, fr=fr: fr["Hh"] + fr["Dhd"] @ (Vector(p) - s.H["head"])       # ... by the head
        fr["gun"] = lambda p, fr=fr: fr["Hg"] + fr["Dg"] @ (Vector(p) - s.H["gun"])          # ... by the weapon
        return fr

    def pose(s, f, hip_off, yaw, roll, ankles, pitches, torso_D, head_D, arms_D=None, arms_off=V(0, 0, 0),
             gun_R=None, gun_off=V(0, 0, 0), lh=None, rh=None, mag_off=V(0, 0, 0), knee_pole=None):
        """lh / rh: None keeps that hand on the weapon; (point, D) sends the wrist to a point with the hand turned D
        (absolute); mag_off: the magazine's shift in the gun's own rest axes; knee_pole: {side: which way the knee points}"""
        I = Quaternion()
        fr = s.frames(hip_off, yaw, roll, torso_D, head_D, arms_D, arms_off, gun_R, gun_off)
        Dh, hh, Da, Dg = fr["Dh"], fr["hh"], fr["Da"], fr["Dg"]
        s.key(f, "hips", rot=s.local("hips", I, Dh), loc=s.R["hips"].inverted() @ (hip_off * K))
        for side in ("L", "R"):
            th, sh, ft = "thigh." + side, "shin." + side, "foot." + side
            Hj = hh + Dh @ (s.H[th] - s.H["hips"])
            A = ankles[side]
            a = (s.H[sh] - s.H[th]).length
            b = (s.H[ft] - s.H[sh]).length
            Kn, _ = elbow(Hj, A, a, b, knee_pole[side] if knee_pole else V(1, 0, 0))
            Dt = (s.H[sh] - s.H[th]).normalized().rotation_difference((Kn - Hj).normalized())
            Ds = (s.H[ft] - s.H[sh]).normalized().rotation_difference((A - Kn).normalized())
            Df = Quaternion(Y, -pitches[side])
            s.key(f, th, rot=s.local(th, Dh, Dt))
            s.key(f, sh, rot=s.local(sh, Dt, Ds))
            s.key(f, ft, rot=s.local(ft, Ds, Df))
        s.key(f, "torso", rot=s.local("torso", Dh, torso_D))
        s.key(f, "head", rot=s.local("head", torso_D, head_D))
        s.key(f, "arms", rot=s.local("arms", torso_D, Da), loc=s.R["arms"].inverted() @ (torso_D.inverted() @ (arms_off * K)))
        s.key(f, "gun", rot=s.local("gun", Da, Dg), loc=s.R["gun"].inverted() @ (gun_off * K))
        s.key(f, "mag", rot=I, loc=s.R["mag"].inverted() @ (Vector(mag_off) * K))
        # arms: two-bone IK from each shoulder (carried by the arms bone) to the wrist
        for side, tgt in (("L", lh), ("R", rh)):
            UA, FA, HA = "upperarm." + side, "forearm." + side, "hand." + side
            S = fr["Ha"] + Da @ (s.H[UA] - s.H["arms"])
            if tgt is None:
                Wt, Dhand = fr["gun"](s.H[HA]), Dg
            else:
                Wt, Dhand = Vector(tgt[0]), tgt[1]
            a = (s.H[FA] - s.H[UA]).length
            b = (s.H[HA] - s.H[FA]).length
            pole = tgt[2] if tgt is not None and len(tgt) > 2 else Da @ POLE[side]
            E, _ = elbow(S, Wt, a, b, pole)
            u0 = Da @ (s.H[FA] - s.H[UA]).normalized()
            f0 = Da @ (s.H[HA] - s.H[FA]).normalized()
            Du = u0.rotation_difference((E - S).normalized()) @ Da
            Df = f0.rotation_difference((Wt - E).normalized()) @ Da
            s.key(f, UA, rot=s.local(UA, Da, Du))
            s.key(f, FA, rot=s.local(FA, Du, Df))
            s.key(f, HA, rot=s.local(HA, Df, Dhand))


HEEL, BALL = V(-0.07, 0, -0.08), V(0.12, 0, -0.07)


def rot2(v, th):
    c, s = math.cos(th), math.sin(th)
    return Vector((v.x * c - v.z * s, v.y, v.x * s + v.z * c))


def ankle_at(xg, th, y, lift=0.0):
    """ankle position for a foot whose flat-foot ground track is at xg, pitched th (toes up +), resting on heel or ball"""
    h, bl = rot2(HEEL, th), rot2(BALL, th)
    z = max(0.01 - h.z, 0.02 - bl.z)
    if th < 0:      # rolling over the ball
        x = xg + BALL.x - bl.x
    else:           # rocking on the heel
        x = xg + HEEL.x - h.x
    return Vector((x, y, z + lift))


def gait(phi):
    travel = STRIDE * BETA
    xf, xb = travel * 0.47, -travel * 0.53
    if phi < BETA:
        s = phi / BETA
        x = xf + (xb - xf) * s
        if s < 0.15:
            th = math.radians(14) * (1 - sm(s / 0.15))
        elif s < 0.62:
            th = 0.0
        else:
            th = -math.radians(36) * sm((s - 0.62) / 0.38)
        lift = 0.0
    else:
        s = (phi - BETA) / (1 - BETA)
        e = 0.5 - 0.5 * math.cos(math.pi * s)
        x = xb + (xf - xb) * e
        th = math.radians(-36 + 50 * sm(s / 0.85))
        lift = 0.075 * math.sin(math.pi * s) ** 0.9
    return x, th, lift


def kf(t, keys):
    """a value through (time, value) keys, eased between them"""
    if t <= keys[0][0]:
        return keys[0][1]
    for (t0, v0), (t1, v1) in zip(keys, keys[1:]):
        if t <= t1:
            u = sm((t - t0) / (t1 - t0)) if t1 > t0 else 1.0
            return v0 + (v1 - v0) * u
    return keys[-1][1]


# clips every soldier gets, and how long each runs (frames at 24 fps)
CLIPS = dict(Idle=48, Walk=24, LookAround=96, CheckAmmo=120, Stretch=96, AdjustGear=96, KneelDown=22, KneelIdle=72, KneelUp=16)


def animate(ao, name, utype, gun):
    P = Poser(ao)
    lean = 0.13 if utype != "at" else 0.09
    head_pitch = {"rifle": 0.12, "mg": 0.10, "at": 0.16, "sniper": 0.14}[utype]
    head_roll = 0.10 if utype == "at" else 0.04   # + tilts the head to its right, onto the stock / sight
    W0, G0 = P.H["hand.L"], Vector(gun["L"][0])    # the support hand's wrist and what it holds, at rest

    def base(sec, sway=1.0):
        """the Idle pose at a time: bladed stance, breathing, a slow drift of the hips and head (2 s cycle)"""
        ph = sec * math.pi
        br = math.sin(ph * 2)
        w = math.sin(ph) * sway
        return dict(hip=V(-0.015, 0.012 * w, -0.04 + 0.003 * br), yaw=-0.06, roll=0.012 * w,
                    ankles={"L": V(0.07, 0.125, 0.09), "R": V(-0.09, -0.125, 0.09)}, pitches={"L": 0.0, "R": 0.0},
                    torso=Quaternion(Y, lean * 0.6 + 0.006 * br), hyaw=0.06 * w, hpitch=head_pitch, hroll=head_roll,
                    arms=Quaternion(), arms_off=V(0, 0, 0.003 * br))

    def head_of(p):
        return Quaternion(Z, p["hyaw"]) @ Quaternion(Y, p["hpitch"]) @ Quaternion(X, p["hroll"])

    def put(f, p, **kw):
        P.pose(f, p["hip"], p["yaw"], p["roll"], p["ankles"], p["pitches"], p["torso"], head_of(p), arms_D=p["arms"],
               arms_off=p["arms_off"], **kw)

    def frames_of(p, **kw):
        return P.frames(p["hip"], p["yaw"], p["roll"], p["torso"], head_of(p), p["arms"], p["arms_off"], **kw)

    def clip(cname, fn, step=1):
        n = CLIPS[cname]
        new_action(ao, name, cname)
        for f in range(1, n + 2, step):
            fn(f, (f - 1) / n, (f - 1) / FPS)
        push_nla(ao, bpy.data.actions[name + "|" + cname], cname)
        reset_pose(ao)

    # Idle: 2 s
    clip("Idle", lambda f, t, sec: put(f, base(sec)), step=2)

    # Walk: IK-planted feet, heel strike -> roll -> toe-off, pelvis bob / sway / turn, chest steady on the gun; 1 s
    def walk(f, phi, sec):
        ankles, pitches = {}, {}
        for side, off, y in (("L", 0.0, 0.11), ("R", 0.5, -0.11)):
            x, th, lift = gait((phi + off) % 1.0)
            ankles[side] = ankle_at(x, th, y, lift)
            pitches[side] = th
        yaw = -0.09 * math.cos(2 * math.pi * phi)
        roll = 0.035 * math.cos(2 * math.pi * (phi - 0.3))
        hip = V(-0.02, 0.014 * math.cos(2 * math.pi * (phi - 0.3)), -0.075 - 0.016 * math.cos(4 * math.pi * (phi - 0.05)))
        torso = Quaternion(Z, 0.25 * yaw) @ Quaternion(Y, lean) @ Quaternion(X, -0.8 * roll)
        head = Quaternion(Z, 0.0) @ Quaternion(Y, head_pitch) @ Quaternion(X, head_roll)
        arms = Quaternion(Z, 0.25 * yaw)
        P.pose(f, hip, yaw, roll, ankles, pitches, torso, head, arms_D=arms, arms_off=V(0, 0, 0.004 * math.sin(4 * math.pi * phi)))
    clip("Walk", walk)

    # LookAround: a proper look left, then right, the shoulders and the gun following a little; 4 s
    def look(f, t, sec):
        y = kf(t, [(0, 0), (0.08, 0), (0.25, 0.64), (0.41, 0.68), (0.60, -0.72), (0.77, -0.76), (0.93, 0), (1, 0)])
        p = base(sec)
        p["hyaw"] += 0.82 * y
        p["hpitch"] -= 0.07 * abs(y)
        p["torso"] = Quaternion(Z, 0.27 * y) @ p["torso"]
        p["arms"] = Quaternion(Z, 0.17 * y)
        p["yaw"] += 0.05 * y
        put(f, p)
    clip("LookAround", look)

    # CheckAmmo: brings the weapon in, looks down at it; rifle and sniper drop the magazine into the support hand, look,
    # seat it again with a tap; the machine gunner pats his belt box, the rocketeer checks his sight; 5 s
    has_mag = utype in ("rifle", "sniper")
    mag0, mdir = Vector(gun["mag"]), Vector(gun["mag_out"]).normalized()

    def check(f, t, sec):
        g = kf(t, [(0, 0), (0.13, 1), (0.80, 1), (0.94, 0), (1, 0)])              # weapon canted into the workspace
        reach = kf(t, [(0, 0), (0.11, 0), (0.25, 1), (0.74, 1), (0.90, 0), (1, 0)])  # support hand off the handguard
        out = kf(t, [(0, 0), (0.27, 0), (0.37, 1), (0.58, 1), (0.655, 0), (0.69, -0.14), (0.73, 0), (1, 0)])
        lookk = kf(t, [(0, 0), (0.15, 1), (0.74, 1), (0.92, 0), (1, 0)])
        p = base(sec, 1 - g)
        p["hpitch"] += (0.50 if utype != "at" else 0.30) * lookk
        p["hyaw"] += (-0.30 if utype != "at" else -0.42) * lookk
        p["torso"] = p["torso"] @ Quaternion(Y, 0.07 * lookk)
        if utype == "at":
            gun_R, gun_off = Quaternion(Y, 0.20 * g) @ Quaternion(X, 0.22 * g), V(0.02, 0.03, -0.04) * g
        elif utype == "mg":
            gun_R, gun_off = Quaternion(Y, -0.16 * g) @ Quaternion(X, 0.30 * g), V(-0.03, 0.04, 0.0) * g
        else:
            gun_R, gun_off = Quaternion(Y, -0.38 * g) @ Quaternion(X, 0.62 * g), V(-0.05, 0.05, 0.02) * g
        fr = frames_of(p, gun_R=gun_R, gun_off=gun_off)
        if has_mag:
            travel = 0.085 if utype == "rifle" else 0.05
            mag_off = mdir * (travel * out)
            hold = mag0 + mdir * 0.085 + mag_off + (W0 - G0)                     # the wrist, cupping the magazine's base
            grip_D = fr["Dg"] @ Quaternion(Y, -0.25)
        else:
            pat = 0.022 * math.sin(t * 2 * math.pi * 6) * kf(t, [(0, 0), (0.30, 0), (0.36, 1), (0.60, 1), (0.66, 0), (1, 0)])
            mag_off = V(0, 0, 0)
            hold = mag0 + V(-0.02, 0.03, 0.05 + abs(pat)) + (W0 - G0) * 0.35
            grip_D = fr["Dg"] @ Quaternion(X, 0.9) @ Quaternion(Y, 0.5)
        Wg = fr["gun"](W0)
        Wt = Wg.lerp(fr["gun"](hold), reach) + fr["Dg"] @ V(0.0, 0.05, -0.05) * math.sin(math.pi * reach)
        put(f, p, gun_R=gun_R, gun_off=gun_off, mag_off=mag_off, lh=(Wt, fr["Dg"].slerp(grip_D, reach)))
    clip("CheckAmmo", check)

    # Stretch: lets the gun hang, settles onto one leg, arches the back and rolls the neck, shifts to the other leg; 4 s
    def stretch(f, t, sec):
        w = kf(t, [(0, 0), (0.15, 1), (0.44, 1), (0.58, -1), (0.82, -1), (0.95, 0), (1, 0)])
        low = kf(t, [(0, 0), (0.12, 1), (0.84, 1), (0.97, 0), (1, 0)])
        arch = kf(t, [(0, 0), (0.17, 0), (0.31, 1), (0.42, 1), (0.54, 0), (1, 0)])
        neck = kf(t, [(0, 0), (0.50, 0), (0.60, 1), (0.71, -1), (0.83, 0), (1, 0)])
        p = base(sec, 1 - low)
        p["hip"] = p["hip"] + V(0.004 * arch, 0.038 * w, -0.006 * abs(w))
        p["roll"] += 0.055 * w
        p["yaw"] += 0.035 * w
        p["torso"] = Quaternion(X, -0.05 * w) @ Quaternion(Y, lean * 0.6 - 0.17 * arch)
        p["hroll"] += 0.34 * neck
        p["hpitch"] += -0.30 * arch + 0.10 * abs(neck)
        p["arms_off"] = V(0, 0, -0.035 * low + 0.03 * arch)
        put(f, p, gun_R=Quaternion(Y, (0.40 if utype != "at" else 0.16) * low + 0.05 * arch), gun_off=V(0, 0, -0.02) * low)
    clip("Stretch", stretch)

    # AdjustGear: the support hand comes off the weapon, resettles the helmet (or hat), then tugs the vest straight; 4 s
    rim = V(0.075, 0.115, 1.705) if utype != "sniper" else V(0.10, 0.13, 1.685)
    vest = V(0.135, 0.075, 1.31)

    def gear(f, t, sec):
        up = kf(t, [(0, 0), (0.05, 0), (0.22, 1), (0.47, 1), (0.60, 0), (1, 0)])
        chest = kf(t, [(0, 0), (0.47, 0), (0.60, 1), (0.80, 1), (0.95, 0), (1, 0)])
        off = max(up, chest)
        wig = math.sin(t * 2 * math.pi * 7) * kf(t, [(0, 0), (0.24, 0), (0.28, 1), (0.42, 1), (0.47, 0), (1, 0)])
        tug = math.sin(t * 2 * math.pi * 9) * kf(t, [(0, 0), (0.62, 0), (0.66, 1), (0.76, 1), (0.80, 0), (1, 0)])
        p = base(sec, 1 - off)
        p["hpitch"] += 0.10 * up + 0.045 * wig + 0.22 * chest
        p["hroll"] += -0.04 * wig
        p["hyaw"] += 0.10 * chest
        p["torso"] = p["torso"] @ Quaternion(Y, 0.02 * tug + 0.03 * chest)
        gun_R = Quaternion(Y, (0.30 if utype != "at" else 0.10) * off)
        fr = frames_of(p, gun_R=gun_R)
        Wg = fr["gun"](W0)
        Wh = fr["head"](rim) + fr["Dhd"] @ V(0.0, 0.0, -0.012 * wig)
        Wc = fr["torso"](vest) + fr["Dt"] @ V(0.0, 0.0, -0.016 * tug)
        Wt = Wg * (1 - up - chest) + Wh * up + Wc * chest
        Wt += fr["Dt"] @ V(0.07, 0.06, 0.0) * math.sin(math.pi * up) + fr["Dt"] @ V(0.05, 0.04, 0.0) * math.sin(math.pi * chest)
        Dh = fr["Dg"].slerp(fr["Dhd"] @ Quaternion(Y, -1.15) @ Quaternion(X, 0.5), up).slerp(fr["Dt"] @ Quaternion(Y, -0.9) @ Quaternion(X, 1.1), chest)
        put(f, p, gun_R=gun_R, lh=(Wt, Dh))
    clip("AdjustGear", gear)

    # Kneel: steps the support foot forward, sinks onto the other knee, weapon ready across the thigh; then rests there
    # scanning; KneelUp is the way back
    def kneel(f, k, sec, scan=0.0):
        p = base(sec, 1 - k)
        step = sm(k / 0.5)
        back = sm((k - 0.2) / 0.7)
        sink = sm((k - 0.1) / 0.9)
        th = -1.12 * back
        ar = ankle_at(-0.09 - 0.20 * back, th, -0.125 + 0.005 * back, 0.03 * math.sin(math.pi * back))
        al = V(0.07 + 0.27 * step, 0.125 + 0.01 * step, 0.09 + 0.05 * math.sin(math.pi * step))
        p["ankles"], p["pitches"] = {"L": al, "R": ar}, {"L": 0.0, "R": th}
        p["hip"] = V(-0.015 + 0.035 * sink, p["hip"].y - 0.01 * sink, p["hip"].z - 0.415 * sink)
        p["yaw"] = -0.06 - 0.16 * sink
        p["torso"] = Quaternion(Z, 0.10 * sink) @ Quaternion(Y, lean * 0.6 + 0.07 * sink) @ Quaternion(Y, 0.006 * math.sin(sec * 2 * math.pi))
        p["hyaw"] += scan
        p["hpitch"] -= 0.04 * sink
        put(f, p, gun_R=Quaternion(Y, 0.17 * sink), gun_off=V(0, 0, -0.02) * sink)
    clip("KneelDown", lambda f, t, sec: kneel(f, sm(t), 0.0))
    clip("KneelIdle", lambda f, t, sec: kneel(f, 1.0, sec, scan=0.36 * math.sin(2 * math.pi * t)), step=2)
    clip("KneelUp", lambda f, t, sec: kneel(f, 1 - sm(t), 0.0))


# ------------------------------------------------------------------ export / run / preview
def export(unit, ob, ao):
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    ao.select_set(True)
    bpy.context.view_layer.objects.active = ao
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, unit + ".fbx")
    bpy.ops.export_scene.fbx(filepath=path, use_selection=True, object_types={"ARMATURE", "MESH"},
                             add_leaf_bones=False, use_armature_deform_only=False, primary_bone_axis="Y", secondary_bone_axis="X",
                             bake_anim=True, bake_anim_use_all_bones=True, bake_anim_use_nla_strips=True, bake_anim_use_all_actions=False,
                             bake_anim_force_startend_keying=True, bake_anim_step=1.0, bake_anim_simplify_factor=0.0,
                             apply_scale_options="FBX_SCALE_ALL", axis_forward="-Z", axis_up="Y", colors_type="LINEAR",
                             mesh_smooth_type="FACE", use_mesh_modifiers=False)
    return path


def collection():
    sc = bpy.context.scene
    sc.render.fps = FPS
    co = bpy.data.collections.get("Infantry v2")
    if co is None:
        co = bpy.data.collections.new("Infantry v2")
        sc.collection.children.link(co)
    return co


def run(types=TYPES, armies=(0, 1), do_export=True):
    co = collection()
    done = []
    for ai, army in enumerate(armies):
        for ti, t in enumerate(types):
            unit, ob, ao, acc, arms = make_soldier(t, army, co)
            path = export(unit, ob, ao) if do_export else ""
            ao.location = ((1 - ai) * 1.2, -30.0 - ti * 0.72 - ai * 0.36, 0)
            done.append(dict(unit=unit, tris=sum(len(p.vertices) - 2 for p in ob.data.polygons), verts=len(ob.data.vertices),
                             reach={s: round(v[3], 3) for s, v in arms.items()}, parts=acc.stats, fbx=os.path.basename(path)))
    return done


def preview(path, frame=7, engine="CYCLES", res=(1600, 900), samples=48, cam_loc=None, cam_at=None, lens=50, only=None):
    """lineup render of the v2 soldiers (Walk at `frame`)"""
    sc = bpy.context.scene
    mat = bpy.data.materials.get("DU_InfMat")
    if mat is None:
        mat = bpy.data.materials.new("DU_InfMat")
        mat.use_nodes = True
        nt = mat.node_tree
        bsdf = nt.nodes.get("Principled BSDF")
        at = nt.nodes.new("ShaderNodeAttribute")
        at.attribute_name = "Col"
        nt.links.new(at.outputs["Color"], bsdf.inputs["Base Color"])
        bsdf.inputs["Roughness"].default_value = 0.8
    for o in bpy.data.objects:
        if o.type == "MESH" and o.name.startswith("inf_"):
            if not o.data.materials:
                o.data.materials.append(mat)
        o.hide_render = not (o.name.startswith("inf_") or o.name.startswith("DU_Prev"))
        if only and o.name.startswith("inf_") and not any(o.name.startswith("inf_" + u) for u in only):
            o.hide_render = True
    cam = bpy.data.objects.get("DU_PrevCam")
    if cam is None:
        cam = bpy.data.objects.new("DU_PrevCam", bpy.data.cameras.new("DU_PrevCam"))
        sc.collection.objects.link(cam)
    cam.data.lens = lens
    cam.location = cam_loc
    d = Vector(cam_at) - Vector(cam_loc)
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    sc.camera = cam
    sun = bpy.data.objects.get("DU_PrevSun")
    if sun is None:
        sun = bpy.data.objects.new("DU_PrevSun", bpy.data.lights.new("DU_PrevSun", "SUN"))
        sc.collection.objects.link(sun)
    sun.data.energy = 3.2
    sun.data.angle = math.radians(3)
    sun.rotation_euler = (math.radians(50), math.radians(8), math.radians(-35))
    gnd = bpy.data.objects.get("DU_PrevGround")
    if gnd is None:
        gm = bpy.data.meshes.new("DU_PrevGround")
        gm.from_pydata([(-60, -60, 0), (60, -60, 0), (60, 60, 0), (-60, 60, 0)], [], [(0, 1, 2, 3)])
        gnd = bpy.data.objects.new("DU_PrevGround", gm)
        sc.collection.objects.link(gnd)
        gmat = bpy.data.materials.new("DU_PrevGroundMat")
        gmat.use_nodes = True
        gmat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.16, 0.15, 0.1, 1)
        gmat.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 1.0
        gm.materials.append(gmat)
    if sc.world is None:
        sc.world = bpy.data.worlds.new("DU_PrevWorld")
    sc.world.use_nodes = True
    bg = sc.world.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value = (0.55, 0.62, 0.72, 1)
    bg.inputs["Strength"].default_value = 0.9
    sc.render.engine = engine
    if engine == "CYCLES":
        sc.cycles.samples = samples
        sc.cycles.use_denoising = True
        sc.cycles.device = "CPU"
    sc.view_settings.view_transform = "AgX" if "AgX" in [i.identifier for i in sc.view_settings.bl_rna.properties["view_transform"].enum_items] else "Filmic"
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = False
    sc.frame_set(frame)
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    return path
