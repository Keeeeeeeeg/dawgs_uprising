# Dawgs Uprising -> Unity: environment models made in Blender (trees, grass, the railway).
#   run in Blender (or bpy):  import du_env; du_env.run()
# Writes into the Unity project:
#   Assets/Dawgs/Data/env_trees.bytes    the six tree / bush prototypes, three LODs each (DWG1 bank, vertex colours,
#                                        wind weight in vertex alpha, canopy-bent normals, Cycles-baked AO)
#   Assets/Dawgs/Data/env_grass.bytes    grass / flower clumps for the terrain detail system
#   Assets/Dawgs/Data/env_track.bytes    the railway: sleepers, tie plates, profiled rails and the ballast bed, swept
#                                        along the game's own rail lines (Data/rail_lines.json), in 48 m chunks
#   Assets/Dawgs/Textures/Env/ballast.png, ballast_n.png   rendered stone ballast (albedo + normal), tileable
# Coordinates: built Z-up in Blender, written to the bank as Unity (x, y, z) = Blender (x, z, y), winding flipped.
import json
import math
import os
import random
import struct

import bpy
import numpy as np
from mathutils import Vector, noise

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


ROOT = _project_root()
DATA = os.path.join(ROOT, "Assets", "Dawgs", "Data")
TEXD = os.path.join(ROOT, "Assets", "Dawgs", "Textures", "Env")


# ------------------------------------------------------------------ colour helpers
def hx(h):
    return np.array([int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)])


def s2l(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def l2s(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)


def nz(p, f=1.0, seed=0.0, octaves=1):
    """perlin noise at points p (n,3) -> (n,), roughly -1..1"""
    p = np.asarray(p, float)
    out = np.zeros(len(p))
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        ff = f * 2 ** o
        off = Vector((seed * 17.3 + o * 31.7, seed * 7.1 - o * 13.3, seed * 3.7 + o * 5.9))
        out += amp * np.array([noise.noise(Vector(q) * ff + off) for q in p])
        tot += amp
        amp *= 0.5
    return out / tot


# ------------------------------------------------------------------ primitives
_ICO = {}


def ico(level):
    if level in _ICO:
        return _ICO[level]
    t = (1 + 5 ** 0.5) / 2
    V = [(-1, t, 0), (1, t, 0), (-1, -t, 0), (1, -t, 0), (0, -1, t), (0, 1, t), (0, -1, -t), (0, 1, -t),
         (t, 0, -1), (t, 0, 1), (-t, 0, -1), (-t, 0, 1)]
    V = [np.array(v, float) / np.linalg.norm(v) for v in V]
    F = [(0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11), (1, 5, 9), (5, 11, 4), (11, 10, 2), (10, 7, 6),
         (7, 1, 8), (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9), (4, 9, 5), (2, 4, 11), (6, 2, 10),
         (8, 6, 7), (9, 8, 1)]
    for _ in range(level):
        cache, F2 = {}, []

        def mid(a, b):
            k = (min(a, b), max(a, b))
            if k not in cache:
                m = V[a] + V[b]
                V.append(m / np.linalg.norm(m))
                cache[k] = len(V) - 1
            return cache[k]

        for a, b, c in F:
            ab, bc, ca = mid(a, b), mid(b, c), mid(c, a)
            F2 += [(a, ab, ca), (b, bc, ab), (c, ca, bc), (ab, bc, ca)]
        F = F2
    _ICO[level] = (np.array(V), np.array(F, int))
    return _ICO[level]


def vnormals(V, F):
    fn = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
    N = np.zeros_like(V)
    for k in range(3):
        np.add.at(N, F[:, k], fn)
    return N / np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-9)


def rotz(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def roty(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def rotx(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def catmull(P, n_per=4):
    P = np.asarray(P, float)
    if len(P) < 3:
        return np.array([P[0] + (P[-1] - P[0]) * t for t in np.linspace(0, 1, n_per + 1)])
    Q = np.vstack([2 * P[0] - P[1], P, 2 * P[-1] - P[-2]])
    out = []
    for i in range(1, len(Q) - 2):
        p0, p1, p2, p3 = Q[i - 1], Q[i], Q[i + 1], Q[i + 2]
        for t in np.linspace(0, 1, n_per, endpoint=False):
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(P[-1])
    return np.array(out)


# ------------------------------------------------------------------ geometry accumulator
class Geo:
    """parts of one model; each part: V F col(sRGB) alpha kind bend (canopy point its normals lean away from)"""

    def __init__(self):
        self.parts = []

    def add(self, V, F, C, A, kind=0, bend=None, bend_k=0.0, N=None):
        self.parts.append(dict(V=np.asarray(V, float), F=np.asarray(F, int), C=np.asarray(C, float), A=np.asarray(A, float),
                               kind=kind, bend=None if bend is None else np.asarray(bend, float), bend_k=bend_k, N=N))

    def scale(self, s):
        s = np.asarray(s, float)
        for p in self.parts:
            p["V"] = p["V"] * s
            if p["bend"] is not None:
                p["bend"] = p["bend"] * s

    def translate(self, t):
        t = np.asarray(t, float)
        for p in self.parts:
            p["V"] = p["V"] + t
            if p["bend"] is not None:
                p["bend"] = p["bend"] + t

    def bounds(self):
        V = np.vstack([p["V"] for p in self.parts])
        return V.min(0), V.max(0)

    def build(self):
        Vs, Fs, Ns, Cs, As, Ks = [], [], [], [], [], []
        o = 0
        for p in self.parts:
            V, F = p["V"], p["F"]
            N = p["N"] if p["N"] is not None else vnormals(V, F)
            if p["bend"] is not None and p["bend_k"] > 0:
                b = p["bend"]
                d = V - (b if b.ndim == 2 else b[None, :])
                d /= np.maximum(np.linalg.norm(d, axis=1, keepdims=True), 1e-6)
                N = N * (1 - p["bend_k"]) + d * p["bend_k"]
                N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-6)
            Vs.append(V); Fs.append(F + o); Ns.append(N); Cs.append(p["C"]); As.append(p["A"]); Ks.append(np.full(len(V), p["kind"]))
            o += len(V)
        return dict(V=np.vstack(Vs), F=np.vstack(Fs), N=np.vstack(Ns), C=np.vstack(Cs), A=np.concatenate(As), K=np.concatenate(Ks),
                    U=np.zeros((o, 2)))


def tube(geo, path, radii, sides, col, a0, a1, seed=0.0, rough=0.08, cap=True, streak=0.18, twist=0.0):
    P = np.asarray(path, float)
    R = np.asarray(radii, float)
    n = len(P)
    T = np.gradient(P, axis=0)
    T /= np.maximum(np.linalg.norm(T, axis=1, keepdims=True), 1e-9)
    ref = np.array([1.0, 0.0, 0.0]) if abs(T[0][0]) < 0.9 else np.array([0.0, 1.0, 0.0])
    Nn = np.cross(T[0], ref); Nn /= np.linalg.norm(Nn)
    frames = []
    for i in range(n):
        if i:
            Nn = Nn - T[i] * np.dot(Nn, T[i])
            Nn /= max(np.linalg.norm(Nn), 1e-9)
        frames.append((Nn.copy(), np.cross(T[i], Nn)))
    V, Nrm, C, A = [], [], [], []
    seglen = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))])
    L = seglen[-1] if seglen[-1] > 0 else 1
    for i in range(n):
        Ni, Bi = frames[i]
        for j in range(sides):
            th = 2 * math.pi * j / sides + twist * seglen[i]
            d = math.cos(th) * Ni + math.sin(th) * Bi
            q = P[i] + d * R[i]
            bump = 1 + rough * noise.noise(Vector(q * 6.0 + seed))
            V.append(P[i] + d * R[i] * bump)
            Nrm.append(d)
            st = noise.noise(Vector((math.cos(th) * 2.2, math.sin(th) * 2.2, seglen[i] * 0.6 + seed * 3)))
            C.append(col * (1 + streak * st) * (0.82 + 0.18 * min(1, seglen[i] / 0.6)))
            A.append(a0 + (a1 - a0) * seglen[i] / L)
    F = []
    for i in range(n - 1):
        for j in range(sides):
            a, b = i * sides + j, i * sides + (j + 1) % sides
            c, d = a + sides, b + sides
            F += [(a, b, d), (a, d, c)]
    if cap:
        c0 = len(V)
        V.append(P[-1] + T[-1] * R[-1] * 0.5); Nrm.append(T[-1]); C.append(col * 0.9); A.append(a1)
        for j in range(sides):
            a, b = (n - 1) * sides + j, (n - 1) * sides + (j + 1) % sides
            F.append((a, b, c0))
    geo.add(np.array(V), np.array(F), np.array(C), np.array(A), kind=0, N=np.array(Nrm))


def scatter_leaves(geo, W, F, n, size, col, alpha, rng, bend, bend_k=0.55, elong=1.6, along=None, up=0.35, tilt=0.45,
                   lift=(-0.02, 0.12), var=0.08, under=None, droop=0.0, below=0.5, shade=None):
    """small opaque leaf diamonds strewn over a surface (W, F): breaks the silhouette up into foliage.
    along: optional (n,3)-callable giving the preferred leaf direction (needle fans along a branch)"""
    fn = np.cross(W[F[:, 1]] - W[F[:, 0]], W[F[:, 2]] - W[F[:, 0]])
    area = np.linalg.norm(fn, axis=1)
    fnu = fn / np.maximum(area[:, None], 1e-12)
    keep = np.where(fnu[:, 2] > -0.55, 1.0, below)          # fewer leaves on the shaded underside
    p = area * keep
    if p.sum() <= 0:
        return
    tri = rng.choice(len(F), n, p=p / p.sum())
    r1, r2 = rng.random(n), rng.random(n)
    s = np.sqrt(r1)
    P = W[F[tri, 0]] * (1 - s)[:, None] + W[F[tri, 1]] * (s * (1 - r2))[:, None] + W[F[tri, 2]] * (s * r2)[:, None]
    nrm = fnu[tri]
    P = P + nrm * rng.uniform(lift[0], lift[1], n)[:, None] * size * 4
    ln = nrm + np.array([0, 0, up]) + rng.normal(0, tilt, (n, 3))
    ln /= np.linalg.norm(ln, axis=1, keepdims=True)
    if along is not None:
        t1 = along(P) + rng.normal(0, 0.35, (n, 3))
    else:
        t1 = rng.normal(0, 1, (n, 3))
    t1 = t1 - ln * (t1 * ln).sum(1, keepdims=True)
    t1 /= np.maximum(np.linalg.norm(t1, axis=1, keepdims=True), 1e-9)
    t2 = np.cross(ln, t1)
    sz = size * rng.uniform(0.75, 1.25, n)[:, None]
    half_w = sz / (2 * elong)
    tip = P + t1 * sz * 0.62 - ln * sz * (0.12 + droop)
    base = P - t1 * sz * 0.38
    left = P + t2 * half_w + ln * sz * 0.06
    right = P - t2 * half_w + ln * sz * 0.06
    V = np.stack([base, right, tip, left], 1).reshape(-1, 3)
    o = np.arange(n) * 4
    Fl = np.stack([np.stack([o, o + 1, o + 2], 1), np.stack([o, o + 2, o + 3], 1)], 1).reshape(-1, 3)
    # leaf colour: cluster colour, per-leaf jitter, lighter tip; some show a pale underside (olive)
    lc = np.asarray(col, float)
    lc = lc[tri] if lc.ndim == 2 else np.tile(lc, (n, 1))
    lc = lc * rng.uniform(1 - var, 1 + var, (n, 1)) * np.array([1, 1, 1]) + rng.normal(0, var * 0.08, (n, 3))
    if under is not None:
        m = rng.random(n) < under[0]
        lc[m] = lc[m] * (1 - under[2]) + np.asarray(under[1]) * under[2]
    C = np.repeat(lc, 4, 0) * np.tile(np.array([0.92, 1.0, 1.05, 1.0])[:, None], (n, 1))
    if shade is not None:
        C = C * shade(V, np.repeat(ln, 4, 0))[:, None]
    A = alpha(V) if callable(alpha) else np.full(len(V), alpha)
    b = np.asarray(bend, float)
    geo.add(V, Fl, C, np.clip(A + 0.08, 0, 1), kind=1, bend=b, bend_k=bend_k,
            N=np.repeat(ln, 4, 0))


def blob(geo, centre, radii, rot, level, col, alpha, seed, crinkle=0.08, lump=0.18, bend=None, bend_k=0.55, flat_bottom=0.0,
         shade=None):
    """a leafy cluster: noise-displaced ellipsoid. shade(V_world, Vunit) -> (n,) multiplier (optional)"""
    U, F = ico(level)
    U = U.copy()
    # lumpy, crinkled surface: low-frequency lumps + leafy high-frequency crinkle (in the cluster's own space)
    s = seed * 13.7
    k = 1 + lump * nz(U, 1.3, s, 2) + crinkle * nz(U, 4.5, s + 5, 2)
    W = U * k[:, None] * np.asarray(radii)[None, :]
    if flat_bottom > 0:
        zb = -radii[2] * (1 - flat_bottom)
        W[:, 2] = np.where(W[:, 2] < zb, zb + (W[:, 2] - zb) * 0.35, W[:, 2])
    W = W @ np.asarray(rot).T + np.asarray(centre)[None, :]
    c = np.tile(np.asarray(col, float), (len(W), 1))
    if shade is not None:
        c = c * shade(W, U)[:, None]
    a = alpha(W) if callable(alpha) else np.full(len(W), alpha)
    geo.add(W, F, c, a, kind=1, bend=bend if bend is not None else np.asarray(centre), bend_k=bend_k)
    return W, F


# ------------------------------------------------------------------ cluster LOD merging
def merge_clusters(cl, k, seed=1):
    """k-means on cluster centres; merged radius covers the volume of its members"""
    if k >= len(cl):
        return cl
    rng = np.random.default_rng(seed)
    C = np.array([c["c"] for c in cl])
    w = np.array([np.prod(c["r"]) for c in cl])
    cen = C[rng.choice(len(C), k, replace=False)]
    for _ in range(25):
        lab = np.argmin(((C[:, None, :] - cen[None]) ** 2).sum(-1), axis=1)
        for j in range(k):
            m = lab == j
            if m.any():
                cen[j] = (C[m] * w[m, None]).sum(0) / w[m].sum()
    out = []
    for j in range(k):
        m = np.where(lab == j)[0]
        if not len(m):
            continue
        members = [cl[i] for i in m]
        vol = sum(np.prod(c["r"]) for c in members)
        r0 = np.mean([c["r"] for c in members], axis=0)
        spread = np.std(C[m], axis=0) if len(m) > 1 else np.zeros(3)
        r = r0 * (vol / np.prod(r0)) ** (1 / 3) * 0.95 + spread * 0.55
        best = members[int(np.argmax([np.prod(c["r"]) for c in members]))]
        out.append(dict(best, c=cen[j], r=r))
    return out


# ------------------------------------------------------------------ species
TREES = {
    # proto key: species, target bounds (Unity x half-widths, height), palette
    "pE2E60375_9": dict(kind="pine", w=(2.3, 2.13), top=8.08, base=0.0),
    "p9F903079_9": dict(kind="cypress", w=(0.65, 0.64), top=6.2, base=-0.07),
    "pCE1377AE_9": dict(kind="umbrella", w=(1.85, 1.47), top=5.48, base=-0.01),
    "p8A82B179_9": dict(kind="olive", w=(1.36, 0.97), top=2.86, base=-0.03),
    "p28E78046_9": dict(kind="broad", w=(1.65, 1.49), top=3.74, base=0.0),
    "p45D5166C_9": dict(kind="bush", w=(0.88, 0.72), top=0.8, base=-0.24),
}

PAL = {
    "pine": ([hx("2a4426"), hx("33522c"), hx("41623a")], hx("564030")),
    "cypress": ([hx("2c482b"), hx("365631"), hx("3d5f36")], hx("4a3b2c")),
    "umbrella": ([hx("47602f"), hx("50693a"), hx("5c7840")], hx("6a4a36")),
    "olive": ([hx("6c7856"), hx("788462"), hx("84906c")], hx("5e5446")),
    "broad": ([hx("4c682c"), hx("587432"), hx("648238")], hx("5e4a36")),
    "bush": ([hx("566830"), hx("62763a"), hx("6e8040")], hx("4a3b2c")),
}


LEAF_GAIN = dict(pine=1.35, cypress=1.25, umbrella=1.2, olive=1.1, broad=1.2, bush=1.15)


def leaf_shade(cz0, cz1, tip_up=0.10, low=0.80):
    """lower foliage a touch darker / bluer; upward faces catch a warm tip"""
    def f(W, U):
        t = np.clip((W[:, 2] - cz0) / max(cz1 - cz0, 1e-3), 0, 1)
        return (low + (1 - low) * t) * (1 + tip_up * np.clip(U[:, 2], 0, 1))
    return f


def sway(H):
    return lambda W: np.clip(0.25 + 0.75 * np.clip(W[:, 2] / H, 0, 1) ** 1.3, 0, 1)


def canopy(g, cl, lod, rng, H, sh, bend, leaf, bend_k=0.72, core_dark=0.8, crinkle=(0.1, 0.07, 0.07), lump=0.2, flat=0.25,
           level=(1, 1, 1), nleaf=(70, 20, 0), lsize=(1.0, 1.65, 0), alpha=None):
    """draw clusters: a darker crinkled core plus a leaf shell (LOD0 / LOD1); merged bare cores at LOD2"""
    al = alpha or sway(H)
    ref = None
    for c in cl:
        r = np.asarray(c["r"])
        ref = ref or float(np.prod(r)) ** (1 / 3)
        core = c["col"] * (core_dark if (lod < 2 and c.get("leaves", True)) else 0.8)
        bd = bend if bend is not None else np.array([0, 0, c["c"][2] - 0.4])
        W, F = blob(g, c["c"], r * (0.9 if lod < 2 else 1.0), rotz(rng.uniform(0, 6.28)), level[lod], core, al, c["seed"],
                    crinkle=crinkle[lod], lump=lump, bend=bd, bend_k=min(0.9, bend_k + 0.12), flat_bottom=flat, shade=sh)
        if nleaf[lod] and c.get("leaves", True):
            k = max(6, int(nleaf[lod] * (float(np.prod(r)) ** (1 / 3) / ref) ** 2))
            scatter_leaves(g, W, F, k, leaf["size"] * lsize[lod], c["col"], al, rng, bd, bend_k, shade=sh,
                           **{k2: v for k2, v in leaf.items() if k2 != "size"})


def species_broad(lod, rng, pal, bark, H=3.74):
    g = Geo()
    sides = (9, 6, 5)[lod]
    trunk = catmull([(0, 0, 0), (0.03, 0.02, 0.7), (-0.02, 0.05, 1.3), (0.02, 0.0, 1.75)], (5, 3, 2)[lod])
    tube(g, trunk, np.linspace(0.17, 0.11, len(trunk)), sides, bark, 0.0, 0.08, seed=1)
    for i in range(4 if lod < 2 else 3):
        az = i * 2 * math.pi / 4 + rng.uniform(-0.4, 0.4)
        out = rng.uniform(0.55, 0.95)
        end = np.array([math.cos(az) * out, math.sin(az) * out, rng.uniform(2.35, 2.8)])
        mid = np.array([math.cos(az) * out * 0.45, math.sin(az) * out * 0.45, 2.0])
        p = catmull([trunk[-2], mid, end], (4, 2, 1)[lod])
        tube(g, p, np.linspace(0.085, 0.03, len(p)), max(4, sides - 2), bark, 0.08, 0.35, seed=2 + i)
    cc = np.array([0.0, 0.0, 2.55])
    R = np.array([1.5, 1.42, 1.08])
    cl = []
    n = 22
    for i in range(n):
        u = (i + 0.5) / n
        z = 1 - 2 * u ** 0.85
        r = math.sqrt(max(0, 1 - z * z))
        az = i * 2.399963 + rng.uniform(-0.3, 0.3)
        d = np.array([r * math.cos(az), r * math.sin(az), z])
        c = cc + d * R * rng.uniform(0.6, 0.8)
        s = rng.uniform(0.5, 0.68) * (0.85 if z < -0.3 else 1.0)
        cl.append(dict(c=c, r=np.array([s, s, s * 0.8]), col=pal[rng.integers(0, 3)] * rng.uniform(0.93, 1.07), seed=i + 0.5))
    for i in range(4):   # inner volume, so gaps read dark rather than see-through
        cl.append(dict(c=cc + rng.uniform(-0.4, 0.4, 3) * R, r=np.array([0.62, 0.62, 0.5]), col=pal[0] * 0.75, seed=40 + i, leaves=False))
    if lod == 1:
        cl = merge_clusters(cl, 13, 3)
    elif lod == 2:
        cl = merge_clusters(cl, 8, 3)
    sh = leaf_shade(cc[2] - R[2], cc[2] + R[2], tip_up=0.05)
    canopy(g, cl, lod, rng, H, sh, cc - np.array([0, 0, 0.3]), dict(size=0.18, elong=1.5, tilt=0.5), nleaf=(190, 40, 0), lsize=(1.0, 1.75, 0),
           core_dark=0.66)
    return g


def species_olive(lod, rng, pal, bark, H=2.89):
    g = Geo()
    sides = (8, 6, 4)[lod]
    tops = []
    for i, (az, lean) in enumerate(((0.4, 0.42), (2.6, 0.38), (4.4, 0.3))[: (3 if lod < 2 else 2)]):
        pts = [(0, 0, 0)]
        x = y = 0.0
        for k, z in enumerate((0.35, 0.75, 1.15, 1.5)):
            x += math.cos(az) * lean * 0.28 + rng.uniform(-0.07, 0.07)
            y += math.sin(az) * lean * 0.28 + rng.uniform(-0.07, 0.07)
            pts.append((x, y, z))
        p = catmull(pts, (4, 2, 1)[lod])
        tube(g, p, np.linspace(0.16 if i == 0 else 0.12, 0.05, len(p)), sides, bark, 0.0, 0.3, seed=7 + i, rough=0.22, streak=0.25,
             twist=1.2)
        tops.append(np.array(pts[-1]))
    cc = np.array([0.05, 0.03, 2.05])
    R = np.array([1.28, 0.92, 0.72])
    cl = []
    n = 17
    for i in range(n):
        u = (i + 0.5) / n
        z = 1 - 1.7 * u
        r = math.sqrt(max(0, 1 - min(1, z * z)))
        az = i * 2.399963 + rng.uniform(-0.5, 0.5)
        d = np.array([r * math.cos(az), r * math.sin(az), z])
        c = cc + d * R * rng.uniform(0.55, 0.85)
        s = rng.uniform(0.32, 0.48)
        cl.append(dict(c=c, r=np.array([s * 1.15, s, s * 0.72]), col=pal[rng.integers(0, 3)] * rng.uniform(0.93, 1.07), seed=i + 0.3))
    for t in tops:
        cl.append(dict(c=t + np.array([0, 0, 0.35]), r=np.array([0.42, 0.4, 0.3]), col=pal[0] * 0.8, seed=60 + t[0], leaves=False))
    if lod == 1:
        cl = merge_clusters(cl, 10, 5)
    elif lod == 2:
        cl = merge_clusters(cl, 7, 5)
    sh = leaf_shade(cc[2] - R[2], cc[2] + R[2], tip_up=0.06, low=0.82)
    canopy(g, cl, lod, rng, H, sh, cc - np.array([0, 0, 0.2]),
           dict(size=0.12, elong=3.2, tilt=0.6, up=0.2, under=(0.3, hx("a8b098"), 0.4), var=0.1), nleaf=(150, 45, 0), lsize=(1.0, 1.8, 0), lump=0.26,
           flat=0.35, bend_k=0.65, core_dark=0.72)
    return g


def species_umbrella(lod, rng, pal, bark, H=5.49):
    g = Geo()
    sides = (9, 6, 5)[lod]
    trunk = catmull([(0, 0, 0), (0.06, 0.02, 1.2), (0.18, 0.06, 2.4), (0.26, 0.1, 3.5)], (5, 3, 2)[lod])
    tube(g, trunk, np.linspace(0.15, 0.09, len(trunk)), sides, bark, 0.0, 0.12, seed=11, streak=0.28)
    top = trunk[-1]
    cc = np.array([0.15, 0.06, 4.75])
    nl = 5 if lod < 2 else 3
    for i in range(nl):
        az = i * 2 * math.pi / nl + rng.uniform(-0.3, 0.3)
        rr = rng.uniform(0.75, 1.15)
        end = cc + np.array([math.cos(az) * rr, math.sin(az) * rr * 0.85, -0.25])
        p = catmull([trunk[-3], top + (end - top) * 0.45 + np.array([0, 0, 0.25]), end], (4, 2, 1)[lod])
        tube(g, p, np.linspace(0.075, 0.03, len(p)), max(4, sides - 3), bark, 0.12, 0.4, seed=12 + i)
    cl = []
    n = 21
    for i in range(n):
        r = math.sqrt((i + 0.5) / n) * 1.45
        az = i * 2.399963 + rng.uniform(-0.25, 0.25)
        c = cc + np.array([r * math.cos(az), r * math.sin(az) * 0.82, -0.12 * (r / 1.45) ** 2 + rng.uniform(-0.06, 0.08)])
        s = rng.uniform(0.44, 0.62)
        cl.append(dict(c=c, r=np.array([s, s, s * 0.5]), col=pal[rng.integers(0, 3)] * rng.uniform(0.93, 1.07), seed=i + 0.7))
    if lod == 1:
        cl = merge_clusters(cl, 11, 7)
    elif lod == 2:
        cl = merge_clusters(cl, 6, 7)
    sh = leaf_shade(cc[2] - 0.45, cc[2] + 0.4, tip_up=0.1, low=0.7)
    canopy(g, cl, lod, rng, H, sh, cc - np.array([0, 0, 0.9]), dict(size=0.22, elong=3.6, tilt=0.4, up=0.9, droop=0.05),
           nleaf=(160, 40, 0), lsize=(1.0, 1.7, 0), bend_k=0.72, flat=0.45, core_dark=0.66)
    return g


def species_cypress(lod, rng, pal, bark, H=6.27):
    g = Geo()
    p = catmull([(0, 0, -0.1), (0, 0, 0.6), (0, 0, 1.2)], 2)
    tube(g, p, np.linspace(0.1, 0.07, len(p)), (6, 5, 4)[lod], bark, 0, 0.05, seed=21, cap=False)
    prof = lambda t: (math.sin(math.pi * min(1, t ** 0.75)) ** 0.75) * (1 - 0.15 * t)
    cl = []
    n = 34
    for i in range(n):
        t = 0.05 + 0.9 * (i + 0.5) / n
        z = t * H
        rmax = 0.62 * prof(t)
        az = i * 2.399963
        rr = rmax * rng.uniform(0.25, 0.55)
        c = np.array([math.cos(az) * rr, math.sin(az) * rr, z])
        s = max(0.13, rmax * rng.uniform(0.66, 0.84))
        cl.append(dict(c=c, r=np.array([s, s, s * 1.5]), col=pal[rng.integers(0, 3)] * rng.uniform(0.93, 1.07), seed=i + 0.9))
    cl.append(dict(c=np.array([0, 0, H - 0.3]), r=np.array([0.11, 0.11, 0.32]), col=pal[2], seed=99))
    if lod == 1:
        cl = merge_clusters(cl, 15, 9)
    elif lod == 2:
        cl = merge_clusters(cl, 7, 9)
    sh = leaf_shade(0.3, H, tip_up=0.08, low=0.78)
    up = lambda P: np.tile(np.array([0.0, 0.0, 1.0]), (len(P), 1))
    canopy(g, cl, lod, rng, H, sh, None, dict(size=0.1, elong=2.4, tilt=0.35, up=0.1, along=up, droop=-0.05), nleaf=(55, 18, 0), lsize=(1.0, 1.7, 0),
           bend_k=0.65, core_dark=0.8, level=(1, 1, 0), crinkle=(0.1, 0.06, 0.0), lump=0.18, flat=0.0)
    return g


def spray(geo, base, az, L, droop, width, thick, level, col, alpha, seed, bend, shade_low, rng=None, nleaf=0, lsize=0.3):
    """a conifer branch spray: a flattened, tapering, drooping leaf mass from the trunk outwards, with needle fans on it"""
    U, F = ico(level)
    u = (U[:, 0] + 1) / 2                                   # 0 at the trunk, 1 at the tip
    w = np.sin(np.pi * np.clip(u * 0.92 + 0.08, 0, 1)) ** 0.6 * (1 - 0.35 * u)
    k = 1 + 0.22 * nz(U, 2.6, seed, 2)
    X = u * L
    Y = U[:, 1] * width * w * k
    Z = U[:, 2] * thick * w * k - droop * u ** 1.8 + 0.12 * L * u * (1 - u)
    W = np.stack([X, Y, Z], 1) @ rotz(az).T + np.asarray(base)[None, :]
    t = np.clip(u, 0, 1)
    shade = lambda P, N: (shade_low + (1 - shade_low) * np.clip(np.linalg.norm(P[:, :2] - base[:2], axis=1) / L, 0, 1) ** 0.7) * \
        (1 + 0.1 * np.clip(N[:, 2], 0, 1))
    c = np.asarray(col)[None, :] * shade(W, U)[:, None] * (0.62 if nleaf else 0.9)
    a = np.clip(alpha + 0.6 * t, 0, 1)
    geo.add(W, F, c, a, kind=1, bend=bend, bend_k=0.65)
    if nleaf:
        d = np.array([math.cos(az), math.sin(az), -0.25])
        scatter_leaves(geo, W, F, nleaf, lsize, col, lambda P: np.clip(alpha + 0.6 * np.linalg.norm(P[:, :2] - base[:2], axis=1) / L, 0, 1),
                       rng, bend, 0.6, elong=6.0, along=lambda P: np.tile(d, (len(P), 1)), up=0.5, tilt=0.4, droop=0.15, below=0.25,
                       shade=shade)


def species_pine(lod, rng, pal, bark, H=8.08):
    g = Geo()
    trunk = catmull([(0, 0, 0), (0.02, 0.01, 2.5), (0, 0.02, 5.5), (0, 0, H - 0.4)], (5, 3, 1)[lod])
    tube(g, trunk, np.linspace(0.2, 0.03, len(trunk)), (8, 6, 5)[lod], bark, 0, 0.3, seed=31, streak=0.22)
    whorls = (12, 9, 6)[lod]
    per = (8, 7, 5)[lod]
    for wi in range(whorls):
        t = wi / (whorls - 1)
        z = 0.95 + t * (H - 1.75)
        L = 2.25 * (1 - t) ** 0.95 + 0.25
        for k in range(per):
            az = (k + 0.5 * (wi % 2)) * 2 * math.pi / per + rng.uniform(-0.25, 0.25)
            LL = L * rng.uniform(0.85, 1.08) * (1.12 if lod == 2 else 1.0)
            col = pal[rng.integers(0, 3)] * rng.uniform(0.92, 1.08)
            spray(g, np.array([0, 0, z + rng.uniform(-0.08, 0.08)]), az, LL, droop=0.42 * LL * (1 - 0.4 * t), width=0.24 * LL + 0.1,
                  thick=0.15 * LL + 0.1, level=(0, 0, 0)[lod], col=col, alpha=0.1 + 0.4 * t, seed=wi * 10 + k,
                  bend=np.array([0, 0, z - 0.8]), shade_low=0.55 + 0.25 * t, rng=rng,
                  nleaf=(int(40 + 70 * LL / 2.5), int(8 + 12 * LL / 2.5), 0)[lod], lsize=(0.2, 0.34, 0)[lod])
    # the leader: a narrow dark core with needles pointing up it
    W, F = blob(g, (0, 0, H - 0.6), (0.13, 0.13, 0.55), np.eye(3), (1, 1, 0)[lod], pal[0] * 0.7, 1.0, 77, crinkle=0.1, lump=0.1,
                bend=np.array([0, 0, H - 1.5]), bend_k=0.4)
    if lod < 2:
        scatter_leaves(g, W, F, (46, 14)[lod], (0.2, 0.3)[lod], pal[1], 1.0, rng, np.array([0, 0, H - 1.5]), 0.5, elong=5.0,
                       along=lambda P: np.tile(np.array([0, 0, 1.0]), (len(P), 1)), up=0.1, tilt=0.3, droop=-0.1)
    return g


def species_bush(lod, rng, pal, bark, H=1.04):
    g = Geo()
    cc = np.array([0.2, 0.0, 0.25])
    cl = []
    n = 10
    for i in range(n):
        az = i * 2.399963
        r = math.sqrt((i + 0.5) / n) * 0.6
        c = cc + np.array([math.cos(az) * r * 1.2, math.sin(az) * r, 0.25 * (1 - r / 0.6) + rng.uniform(-0.05, 0.05)])
        s = rng.uniform(0.28, 0.4)
        cl.append(dict(c=c, r=np.array([s, s, s * 0.85]), col=pal[rng.integers(0, 3)] * rng.uniform(0.92, 1.08), seed=i + 0.2))
    if lod == 1:
        cl = merge_clusters(cl, 7, 11)
    elif lod == 2:
        cl = merge_clusters(cl, 4, 11)
    sh = leaf_shade(-0.2, 0.8, tip_up=0.08, low=0.75)
    canopy(g, cl, lod, rng, H, sh, cc - np.array([0, 0, 0.3]), dict(size=0.09, elong=1.6, tilt=0.5), nleaf=(90, 28, 0), lsize=(1.0, 1.7, 0),
           alpha=lambda W: np.clip(0.1 + 0.5 * W[:, 2], 0, 0.6), level=(1, 1, 1), crinkle=(0.12, 0.06, 0.04), flat=0.3)
    return g


SPECIES = dict(broad=species_broad, olive=species_olive, umbrella=species_umbrella, cypress=species_cypress, pine=species_pine,
               bush=species_bush)


def make_tree(key, lod):
    spec = TREES[key]
    kind = spec["kind"]
    pal, bark = PAL[kind]
    rng = np.random.default_rng(abs(hash(key)) % (2 ** 31) if False else sum(map(ord, key)) * 7 + 3)
    g = SPECIES[kind](lod, rng, pal, bark)
    # fit the game's footprint and height (prototype pivots are at the ground)
    lo, hi = g.bounds()
    hw = np.maximum(np.maximum(-lo[:2], hi[:2]), 1e-3)
    sx, sy = spec["w"][0] / hw[0], spec["w"][1] / hw[1]
    sz = (spec["top"] - spec["base"]) / (hi[2] - lo[2])
    m = math.sqrt(sx * sy)
    g.scale([0.5 * (m + sx), 0.5 * (m + sy), sz])          # fit, but stay round-ish
    g.translate([0, 0, spec["base"] - lo[2] * sz])
    return g


# ------------------------------------------------------------------ grass, flowers, clover: terrain detail meshes
# matched to the terrain's grass layer (albedo ~5a6d41): blades sit a shade darker at the root, a shade lighter at the tip
GRASS_PAL = dict(root=hx("34421f"), mid=[hx("4e6234"), hx("54683a"), hx("4b5f36")], tip=[hx("5f733c"), hx("64773f"), hx("687a42")],
                 dry=[hx("7e7a4a"), hx("867e52"), hx("767244")])


def blade(geo, base, az, lean, h, w, col_root, col_mid, col_tip, curl=0.35, segs=3, up_k=0.72):
    """one tapering, curving grass blade (double-sided in the shader); normals lean up so a meadow lights like the ground"""
    d = np.array([math.cos(az), math.sin(az), 0.0])
    side = np.array([-math.sin(az), math.cos(az), 0.0])
    side = side @ rotz(np.random.uniform(-0.6, 0.6)).T
    V, C, A = [], [], []
    ts = np.linspace(0, 1, segs + 1)
    pts = []
    for t in ts:
        bend = lean * t + curl * t * t
        p = np.asarray(base) + d * h * (bend * 0.55) + np.array([0, 0, h * (t - 0.18 * curl * t * t)])
        pts.append(p)
    for i, t in enumerate(ts):
        ww = w * (1 - t) ** 0.9
        col = (col_root * (1 - t) * 2 + col_mid * t * 2) if t < 0.5 else (col_mid * (1 - t) * 2 + col_tip * (t - 0.5) * 2)
        if i < segs:
            V += [pts[i] - side * ww / 2, pts[i] + side * ww / 2]
            C += [col, col]
            A += [t, t]
        else:
            V.append(pts[i]); C.append(col_tip); A.append(1.0)
    F = []
    for i in range(segs - 1):
        a, b = 2 * i, 2 * i + 1
        F += [(a, a + 2, b), (b, a + 2, a + 3)]
    a = 2 * (segs - 1)
    F.append((a, a + 2, a + 1))
    V = np.array(V)
    fn = np.cross(d, side); fn = fn / np.linalg.norm(fn)
    N = np.tile(fn * (1 - up_k) + np.array([0, 0, up_k]), (len(V), 1))
    N /= np.linalg.norm(N, axis=1, keepdims=True)
    geo.add(V, np.array(F), np.array(C), np.array(A), kind=1, N=N)


def flower(geo, top, r, petal, centre, n=5, tilt=0.25):
    """a little flower head: a flat star of petals round a centre"""
    V = [np.asarray(top) + np.array([0, 0, r * 0.15])]
    C = [centre]
    for k in range(n * 2):
        a = k * math.pi / n
        rr = r if k % 2 == 0 else r * 0.38
        V.append(np.asarray(top) + np.array([math.cos(a) * rr, math.sin(a) * rr, tilt * rr * (1 if k % 2 == 0 else 0.3)]))
        C.append(petal if k % 2 == 0 else (petal * 0.7 + centre * 0.3))
    F = [(0, 1 + k, 1 + (k + 1) % (n * 2)) for k in range(n * 2)]
    N = np.tile(np.array([0, 0, 1.0]), (len(V), 1))
    geo.add(np.array(V), np.array(F), np.array(C), np.ones(len(V)), kind=1, N=N)


def stem(geo, base, top, w, col):
    side = np.array([w / 2, 0, 0])
    V = np.array([base - side, base + side, top])
    geo.add(V, np.array([(0, 2, 1)]), np.array([col * 0.7, col * 0.7, col]), np.array([0, 0, 1.0]), kind=1,
            N=np.tile(np.array([0, 0, 1.0]), (3, 1)))


def grass_clump(kind, seed):
    rng = np.random.default_rng(seed)
    np.random.seed(seed)
    g = Geo()
    P = GRASS_PAL
    pick = lambda L: L[rng.integers(0, len(L))] * rng.uniform(0.92, 1.08)
    if kind in ("tuft", "tall", "dry"):
        nb, h0, h1, rc = dict(tuft=(22, 0.09, 0.19, 0.09), tall=(16, 0.2, 0.36, 0.1), dry=(18, 0.11, 0.24, 0.09))[kind]
        for i in range(nb):
            r = rc * math.sqrt(rng.random())
            az = rng.uniform(0, 6.28)
            base = np.array([math.cos(az) * r, math.sin(az) * r, -0.01])
            tip = pick(P["dry"]) if kind == "dry" else pick(P["tip"])
            mid = (pick(P["dry"]) * 0.85 if kind == "dry" and rng.random() < 0.7 else pick(P["mid"]))
            blade(g, base, az + rng.uniform(-0.5, 0.5), rng.uniform(0.15, 0.6), rng.uniform(h0, h1), rng.uniform(0.016, 0.026),
                  P["root"], mid, tip, curl=rng.uniform(0.1, 0.55))
        if kind == "tall":
            for i in range(2):   # seed heads
                az = rng.uniform(0, 6.28)
                b = np.array([math.cos(az) * 0.03, math.sin(az) * 0.03, 0])
                t = b + np.array([math.cos(az) * 0.06, math.sin(az) * 0.06, rng.uniform(0.36, 0.46)])
                stem(g, b, t, 0.008, P["dry"][0])
                blob(g, t + np.array([0, 0, 0.02]), (0.007, 0.007, 0.028), np.eye(3), 0, P["dry"][1], 1.0, seed + i, crinkle=0, lump=0.1,
                     bend=t, bend_k=0.3)
    elif kind in ("daisy", "buttercup"):
        for i in range(7):
            az = rng.uniform(0, 6.28)
            r = 0.05 * math.sqrt(rng.random())
            blade(g, np.array([math.cos(az) * r, math.sin(az) * r, -0.01]), az, rng.uniform(0.2, 0.6), rng.uniform(0.08, 0.15), 0.02,
                  P["root"], pick(P["mid"]), pick(P["tip"]))
        petal, centre = (hx("f2efe4"), hx("e8b830")) if kind == "daisy" else (hx("f0c628"), hx("c99a18"))
        for i in range(5):
            az = rng.uniform(0, 6.28)
            r = 0.07 * math.sqrt(rng.random())
            b = np.array([math.cos(az) * r, math.sin(az) * r, 0])
            t = b + np.array([rng.uniform(-0.02, 0.02), rng.uniform(-0.02, 0.02), rng.uniform(0.12, 0.22)])
            stem(g, b, t, 0.01, P["mid"][0])
            flower(g, t, rng.uniform(0.022, 0.03) * (1.0 if kind == "daisy" else 0.8), petal * rng.uniform(0.95, 1.05), centre,
                   n=(8 if kind == "daisy" else 5))
    elif kind == "clover":
        for i in range(9):   # a low rosette of round leaves
            az = i * 2.399963
            r = rng.uniform(0.03, 0.09)
            c = np.array([math.cos(az) * r, math.sin(az) * r, rng.uniform(0.01, 0.04)])
            col = pick([hx("4f6e2a"), hx("587a30"), hx("4a6626")])
            flower(g, c, rng.uniform(0.03, 0.045), col, col * 0.85, n=3, tilt=0.15)
    m = g.build()
    m["A"] = np.clip(m["A"], 0, 1) * np.clip(m["V"][:, 2] / 0.3, 0, 1)   # wind weight grows with height
    return m


GRASS_KINDS = ["tuft", "tall", "dry", "daisy", "buttercup", "clover"]


def build_grass(do_bake=True, samples=24):
    co = coll("DU Env Grass")
    mat = vc_material()
    entries = []
    for i, kind in enumerate(GRASS_KINDS):
        m = grass_clump(kind, 100 + i)
        ob = to_object(f"grass_{kind}", m, co, mat)
        if do_bake:
            ao = bake_ao(ob, samples=samples, distance=0.12)
            apply_ao(m, ao, strength_leaf=0.5, floor=0.4)
            set_colours(ob, m)
        ob.location = (i * 0.5, -3, 0)
        entries.append(bank_entry(dict(key=f"grass_{kind}", mat=301, tx=0, tz=0, proto=f"grass_{kind}", lod=0), m))
    return entries


# ------------------------------------------------------------------ the railway
# The game's lines (Data/rail_lines.json: game x, profile y, game z, heading, city lift, ground) are swept into a ballast bed,
# chamfered sleepers with tie plates, and profiled rails. Track heights follow the browser: sleepers centred 0.07 above the
# line's profile, rail tops at 0.235, gauge +-0.42.
GAUGE = 0.42
SLEEPER = dict(step=0.5, length=1.5, width=0.17, y0=0.03, y1=0.12)
BALLAST = [(-1.40, -0.07), (-1.32, 0.02), (-1.0, 0.075), (-0.86, 0.088), (-0.5, 0.082), (0.0, 0.08), (0.5, 0.082), (0.86, 0.088),
           (1.0, 0.075), (1.32, 0.02), (1.40, -0.07)]
RAIL = [(-0.0375, 0.0), (0.0375, 0.0), (0.0375, 0.008), (0.009, 0.02), (0.0065, 0.064), (0.02, 0.072), (0.02, 0.096), (0.016, 0.1),
        (-0.016, 0.1), (-0.02, 0.096), (-0.02, 0.072), (-0.0065, 0.064), (-0.009, 0.02), (-0.0375, 0.008)]
RAIL_HEAD = {6, 7, 8}          # profile edges (i -> i+1) that are the polished running surface
RAIL_Y = 0.135                 # rail foot sits on the tie plates


class Line:
    def __init__(self, pts):
        p = np.asarray(pts, float)
        # the game's line is a polyline with a small corner every ~2 m: real track is smooth, so ease it (a few cm at most)
        def smooth(v, sig):
            r = int(3 * sig)
            k = np.exp(-0.5 * (np.arange(-r, r + 1) / sig) ** 2)
            k /= k.sum()
            vp = np.concatenate([np.full(r, v[0]) * 2 - v[r:0:-1], v, np.full(r, v[-1]) * 2 - v[-2:-r - 2:-1]])
            return np.convolve(vp, k, mode="valid")
        p = p.copy()
        for c, sig in ((0, 6.0), (2, 6.0), (1, 2.5)):
            p[:, c] = smooth(p[:, c], sig)
        self.P = np.stack([p[:, 0], -p[:, 2], p[:, 1]], 1)          # Blender coords: (game x, -game z, profile y)
        self.lift = p[:, 4]
        d = np.linalg.norm(np.diff(self.P[:, :2], axis=0), axis=1)
        self.s = np.concatenate([[0], np.cumsum(d)])
        self.L = self.s[-1]

    def at(self, s):
        s = np.clip(np.atleast_1d(s), 0, self.L)
        P = np.stack([np.interp(s, self.s, self.P[:, k]) for k in range(3)], 1)
        e = 0.6
        A = np.stack([np.interp(np.clip(s - e, 0, self.L), self.s, self.P[:, k]) for k in range(3)], 1)
        B = np.stack([np.interp(np.clip(s + e, 0, self.L), self.s, self.P[:, k]) for k in range(3)], 1)
        T = B - A
        T /= np.maximum(np.linalg.norm(T, axis=1, keepdims=True), 1e-9)
        Nh = np.stack([-T[:, 1], T[:, 0], np.zeros(len(T))], 1)        # horizontal left normal
        Nh /= np.maximum(np.linalg.norm(Nh, axis=1, keepdims=True), 1e-9)
        U = np.cross(T, Nh)                                           # up, tilted with the grade
        lift = np.interp(s, self.s, self.lift)
        return P, T, Nh, U, lift


def sweep(profile, P, Nh, flat=True, closed=False):
    """sweep a 2D (lateral, up) profile along points with left normals; returns V, F, N (per-edge flat normals if flat)"""
    prof = np.asarray(profile, float)
    n, m = len(P), len(prof)
    up = np.array([0, 0, 1.0])
    edges = [(i, (i + 1) % m) for i in range(m if closed else m - 1)]
    V, F, N, E = [], [], [], []
    for (i, j) in edges:
        a, b = prof[i], prof[j]
        d = b - a
        en = np.array([d[1], -d[0]]) / max(np.hypot(*d), 1e-9)            # outward (lateral, up) normal of this edge
        if a[0] * en[0] + a[1] * en[1] < 0 and False:
            en = -en
        o = len(V)
        for k in range(n):
            for q in (a, b):
                V.append(P[k] + Nh[k] * q[0] + up * q[1])
                N.append(Nh[k] * en[0] + up * en[1])
        for k in range(n - 1):
            p0, p1, p2, p3 = o + 2 * k, o + 2 * k + 1, o + 2 * k + 2, o + 2 * k + 3
            F += [(p0, p2, p1), (p1, p2, p3)]
            E += [(i, j)] * 2
    return np.array(V), np.array(F), np.array(N), E


def track_chunk(line, s0, s1, rng):
    """all track geometry between arc lengths s0..s1; returns {mat: mesh dict}"""
    out = {}
    # ---- ballast: swept every 0.8 m, shoulders a little lighter, oily dark between the rails, speckled
    ss = np.append(np.arange(s0, s1 - 0.2, 0.8), s1)
    P, T, Nh, U, lift = line.at(ss)
    prof = np.array(BALLAST)
    m = len(prof)
    V, C = [], []
    for k in range(len(ss)):
        for (x, y) in prof:
            jy = 0.006 * noise.noise(Vector((P[k][0] * 1.7 + x * 3, P[k][1] * 1.7, 1.3)))
            V.append(P[k] + Nh[k] * x + np.array([0, 0, y + (jy if abs(x) < 1.3 else 0)]))
            oily = math.exp(-((abs(x) - 0.0) / 0.55) ** 2) * 0.16
            shoulder = 0.08 * min(1, max(0, (abs(x) - 0.9) / 0.4))
            nzv = 0.06 * noise.noise(Vector((P[k][0] * 0.35, P[k][1] * 0.35, x)))
            C.append(hx("6e6a62") * (1 - oily + shoulder + nzv))
    F = []
    for k in range(len(ss) - 1):
        for i in range(m - 1):
            a, b, c, d = k * m + i, k * m + i + 1, (k + 1) * m + i, (k + 1) * m + i + 1
            F += [(a, c, b), (b, c, d)]
    V = np.array(V)
    F = np.array(F)
    F = orient(V, F, np.tile(np.array([0, 0, 1.0]), (len(V), 1)))
    out[312] = dict(V=V, F=F, N=vnormals(V, F), C=np.array(C), A=np.zeros(len(V)), U=np.zeros((len(V), 2)), K=np.zeros(len(V)))

    # ---- sleepers + tie plates (one vertex-coloured mesh)
    g = Geo()
    first = math.ceil((s0 - 0.25) / SLEEPER["step"])
    sl = np.arange(first, math.floor((s1 - 0.25) / SLEEPER["step"]) + 1) * SLEEPER["step"] + 0.25
    sl = sl[(sl >= s0) & (sl < s1) & (sl <= line.L - 0.2)]
    w, h0, h1, Ls = SLEEPER["width"] / 2, SLEEPER["y0"], SLEEPER["y1"], SLEEPER["length"] / 2
    sec = [(-w, h0), (w, h0), (w, h1 - 0.014), (w - 0.014, h1), (-w + 0.014, h1), (-w, h1 - 0.014)]
    if len(sl):
        P, T, Nh, U, lift = line.at(sl)
        for k in range(len(sl)):
            yaw = rng.normal(0, 0.012)
            t = T[k] * math.cos(yaw) + Nh[k] * math.sin(yaw)
            nh = Nh[k] * math.cos(yaw) - T[k] * math.sin(yaw)
            c0 = P[k] + nh * rng.normal(0, 0.012) + np.array([0, 0, rng.normal(0, 0.004)])
            wood = hx("4e3e2e") * rng.uniform(0.82, 1.15)
            if rng.random() < 0.25:
                wood = wood * 0.7 + hx("6a6458") * 0.3          # weathered grey
            # section in (along-track, up) extruded across the track
            Vs, Cs = [], []
            for side in (-Ls, Ls):
                for (a, y) in sec:
                    Vs.append(c0 + t * a + nh * side + np.array([0, 0, y]))
                    Cs.append(wood * (0.9 + 0.1 * (y > h1 - 0.02)) * (0.92 if abs(side) > 0 and rng.random() < 0.0 else 1))
            Vs = np.array(Vs)
            ns = len(sec)
            Fs = []
            for i in range(ns):
                j = (i + 1) % ns
                Fs += [(i, j, ns + j), (i, ns + j, ns + i)]
            for i in range(1, ns - 1):
                Fs += [(0, i + 1, i), (ns, ns + i, ns + i + 1)]
            # flat-shaded: split per face
            Fs = np.array(Fs)
            Vf = Vs[Fs.ravel()]
            Ff = np.arange(len(Vf)).reshape(-1, 3)
            fn = np.cross(Vf[1::3] - Vf[0::3], Vf[2::3] - Vf[0::3])
            fn /= np.maximum(np.linalg.norm(fn, axis=1, keepdims=True), 1e-9)
            # orient outward from the sleeper centre
            cen = c0 + np.array([0, 0, (h0 + h1) / 2])
            mid = (Vf[0::3] + Vf[1::3] + Vf[2::3]) / 3
            flip = ((mid - cen) * fn).sum(1) < 0
            Ff[flip] = Ff[flip][:, [0, 2, 1]]
            fn[flip] *= -1
            Cf = np.array(Cs)[Fs.ravel()]
            Cf = Cf * (1 + 0.08 * np.array([noise.noise(Vector(q * 9.0)) for q in Vf]))[:, None]
            g.add(Vf, Ff, Cf, np.zeros(len(Vf)), kind=0, N=np.repeat(fn, 3, 0))
            # tie plates under each rail (thin steel, rusty)
            for side in (-GAUGE, GAUGE):
                pc = c0 + nh * side
                pv, pf = [], []
                for (a, b) in ((-0.06, -0.1), (0.06, -0.1), (0.06, 0.1), (-0.06, 0.1)):
                    pv.append(pc + t * a + nh * b + np.array([0, 0, h1]))
                for (a, b) in ((-0.06, -0.1), (0.06, -0.1), (0.06, 0.1), (-0.06, 0.1)):
                    pv.append(pc + t * a + nh * b + np.array([0, 0, h1 + 0.015]))
                pv = np.array(pv)
                pf = np.array([(4, 5, 6), (4, 6, 7), (0, 1, 5), (0, 5, 4), (1, 2, 6), (1, 6, 5), (2, 3, 7), (2, 7, 6), (3, 0, 4), (3, 4, 7)])
                Vf = pv[pf.ravel()]
                Ff = np.arange(len(Vf)).reshape(-1, 3)
                fn = np.cross(Vf[1::3] - Vf[0::3], Vf[2::3] - Vf[0::3])
                fn /= np.maximum(np.linalg.norm(fn, axis=1, keepdims=True), 1e-9)
                mid = (Vf[0::3] + Vf[1::3] + Vf[2::3]) / 3
                flip = ((mid - (pc + np.array([0, 0, h1 + 0.0075]))) * fn).sum(1) < 0
                Ff[flip] = Ff[flip][:, [0, 2, 1]]
                fn[flip] *= -1
                g.add(Vf, Ff, np.tile(hx("4a3a30") * rng.uniform(0.85, 1.1), (len(Vf), 1)), np.zeros(len(Vf)), kind=0,
                      N=np.repeat(fn, 3, 0))
    # ---- rails: rusty web / foot, polished running surface (separate material)
    sr = np.append(np.arange(s0, s1 - 0.1, 0.5), s1)
    P, T, Nh, U, lift = line.at(sr)
    steel = Geo()
    for side in (-GAUGE, GAUGE):
        Pr = P + Nh * side + np.array([0, 0, RAIL_Y])
        V, F, N, E = sweep(RAIL, Pr, Nh)
        F = orient(V, F, N)
        head = np.array([(e[0] in RAIL_HEAD and e[1] in (7, 8, 9)) for e in E])
        rust = np.where(np.repeat([True], len(V)), 1, 1)
        Cv = np.tile(hx("5a4436"), (len(V), 1)) * (1 + 0.1 * np.array([noise.noise(Vector(q * 3.0)) for q in V]))[:, None]
        Cv[N[:, 2] > 0.5] = hx("6e5a4c")                                    # the foot's top catches some light
        # running surface faces -> steel mesh; the rest -> track mesh
        Fh, Fr = F[head], F[~head]
        g.add(V, Fr, Cv, np.zeros(len(V)), kind=0, N=N)
        steel.add(V, Fh, np.tile(hx("c4c2bc"), (len(V), 1)), np.zeros(len(V)), kind=0, N=N)
    tm = g.build()
    out[311] = tm
    sm = steel.build()
    out[313] = sm
    return out


def orient(V, F, N):
    """flip faces whose winding disagrees with their vertex normals"""
    fn = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
    vn = N[F[:, 0]] + N[F[:, 1]] + N[F[:, 2]]
    bad = (fn * vn).sum(1) < 0
    F = F.copy()
    F[bad] = F[bad][:, [0, 2, 1]]
    return F


def compact(m):
    """drop unreferenced vertices"""
    used = np.unique(m["F"])
    remap = -np.ones(len(m["V"]), int)
    remap[used] = np.arange(len(used))
    r = {k: (v[used] if isinstance(v, np.ndarray) and len(v) == len(m["V"]) else v) for k, v in m.items()}
    r["F"] = remap[m["F"]]
    return r


def build_track(chunk=48.0, preview_co=True):
    src = os.path.join(DATA, "rail_lines.json")
    R = json.load(open(src))
    rng = np.random.default_rng(5)
    co = coll("DU Env Track") if preview_co else None
    mat = vc_material()
    entries, tris = [], 0
    for li, l in enumerate(R["lines"]):
        line = Line(l["pts"])
        n = max(1, int(math.ceil(line.L / chunk)))
        for ci in range(n):
            s0, s1 = ci * line.L / n, (ci + 1) * line.L / n
            parts = track_chunk(line, s0, s1, rng)
            for mid, m in parts.items():
                m = compact(m)
                if not len(m["F"]):
                    continue
                key = f"track_{li}_{ci}"
                entries.append(bank_entry(dict(key=f"{key}|m{mid}", mat=mid, tx=li, tz=ci, proto=key, lod=0), m))
                tris += len(m["F"])
                if co is not None:
                    to_object(f"{key}_m{mid}", m, co, mat)
    return entries, tris


# ------------------------------------------------------------------ ballast stones texture (rendered, tileable)
def build_ballast_texture(res=1024, tile=1.2, n=3600, samples=48):
    """scatter ~2600 crushed stones over a tile (wrapped at the edges so it tiles), render albedo-with-cavity and a normal map"""
    sc = bpy.context.scene
    co = coll("DU Ballast Tile")
    rng = np.random.default_rng(9)
    greys = [hx(h) for h in ("8e8a82", "7a766e", "9e988e", "6c665e", "a8a296", "857d70", "726a60", "948c80")]
    Vs, Fs, Cs = [], [], []
    o = 0
    for i in range(n):
        c = rng.uniform(0, tile, 2)
        r = rng.uniform(0.013, 0.026)
        shape = np.array([r * rng.uniform(0.8, 1.35), r * rng.uniform(0.7, 1.1), r * rng.uniform(0.5, 0.85)])
        U, F = ico(1)
        k = 1 + rng.uniform(-0.22, 0.22, len(U))                    # crushed, angular: jittered facets, flat shaded
        W = U * k[:, None] * shape
        W = W @ rotz(rng.uniform(0, 6.28)).T @ rotx(rng.normal(0, 0.25)).T
        z = rng.uniform(0.0, 0.02)
        col = greys[rng.integers(0, len(greys))] * rng.uniform(0.9, 1.08)
        if rng.random() < 0.1:
            col = col * 0.75 + hx("7a5a40") * 0.25                 # rust-stained
        for dx in (-tile, 0, tile):
            for dy in (-tile, 0, tile):
                cx, cy = c[0] + dx, c[1] + dy
                if -0.06 < cx < tile + 0.06 and -0.06 < cy < tile + 0.06:
                    Vs.append(W + np.array([cx, cy, z])); Fs.append(F + o); Cs.append(np.tile(col, (len(W), 1))); o += len(W)
    m = dict(V=np.vstack(Vs), F=np.vstack(Fs), C=np.vstack(Cs))
    m["N"] = vnormals(m["V"], m["F"])
    ob = to_object("ballast_stones", m, co, vc_material("DU_Stone", rough=0.9), custom_normals=False)
    for p in ob.data.polygons:
        p.use_smooth = False
    # dark fines underneath
    gm = bpy.data.meshes.new("ballast_floor")
    gm.from_pydata([(-1, -1, -0.004), (tile + 1, -1, -0.004), (tile + 1, tile + 1, -0.004), (-1, tile + 1, -0.004)], [], [(0, 1, 2, 3)])
    fm = bpy.data.materials.new("DU_Fines")
    fm.use_nodes = True
    fm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*s2l(hx("3c3832")), 1)
    gm.materials.append(fm)
    gf = bpy.data.objects.new("ballast_floor", gm)
    co.objects.link(gf)
    # camera straight down over the tile; soft sky light only (cavity shading), plus a normal pass
    hidden = [o2 for o2 in sc.objects if o2 not in (ob, gf) and not o2.hide_render]
    for o2 in hidden:
        o2.hide_render = True
    cam = bpy.data.cameras.new("ballast_cam")
    cam.type = "ORTHO"
    cam.ortho_scale = tile
    co_ = bpy.data.objects.new("ballast_cam", cam)
    sc.collection.objects.link(co_)
    co_.location = (tile / 2, tile / 2, 2)
    co_.rotation_euler = (0, 0, 0)
    sc.camera = co_
    w = sc.world or bpy.data.worlds.new("W")
    sc.world = w
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (1, 1, 1, 1)
    w.node_tree.nodes["Background"].inputs[1].default_value = 1.0
    sc.render.engine = "CYCLES"
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    sc.render.resolution_x = sc.render.resolution_y = res
    sc.render.film_transparent = False
    sc.view_settings.view_transform = "Standard"
    os.makedirs(TEXD, exist_ok=True)
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGB"
    sc.render.filepath = os.path.join(TEXD, "ballast.png")
    bpy.ops.render.render(write_still=True)
    # normal map: same view, every surface emitting its normal (raw, no view transform, no denoising)
    nm = bpy.data.materials.new("DU_NormalOut")
    nm.use_nodes = True
    nt = nm.node_tree
    for nd in list(nt.nodes):
        nt.nodes.remove(nd)
    geo_ = nt.nodes.new("ShaderNodeNewGeometry")
    mad = nt.nodes.new("ShaderNodeVectorMath")
    mad.operation = "MULTIPLY_ADD"
    mad.inputs[1].default_value = (0.5, 0.5, 0.5)
    mad.inputs[2].default_value = (0.5, 0.5, 0.5)
    em = nt.nodes.new("ShaderNodeEmission")
    outn = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(geo_.outputs["Normal"], mad.inputs[0])
    nt.links.new(mad.outputs[0], em.inputs["Color"])
    nt.links.new(em.outputs[0], outn.inputs["Surface"])
    vl = sc.view_layers[0]
    vl.material_override = nm
    w.node_tree.nodes["Background"].inputs[1].default_value = 0.0
    sc.cycles.use_denoising = False
    sc.cycles.samples = 16
    sc.view_settings.view_transform = "Raw"
    sc.render.filepath = os.path.join(TEXD, "ballast_n.png")
    bpy.ops.render.render(write_still=True)
    vl.material_override = None
    sc.view_settings.view_transform = "Standard"
    for o2 in hidden:
        o2.hide_render = False
    for o2 in (ob, gf, co_):
        o2.hide_render = True
    return os.path.join(TEXD, "ballast.png")


# ------------------------------------------------------------------ Blender objects, AO bake, preview
def coll(name):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(c)
    return c


def to_object(name, m, co, mat=None, custom_normals=True):
    old = bpy.data.objects.get(name)
    if old:
        bpy.data.objects.remove(old, do_unlink=True)
    me = bpy.data.meshes.get(name)
    if me:
        bpy.data.meshes.remove(me)
    me = bpy.data.meshes.new(name)
    me.from_pydata(m["V"].tolist(), [], m["F"].tolist())
    me.update()
    if custom_normals:
        me.normals_split_custom_set_from_vertices([tuple(n) for n in m["N"]])
    ca = me.color_attributes.new("Col", "FLOAT_COLOR", "POINT")
    lin = np.hstack([s2l(m["C"]), np.ones((len(m["C"]), 1))])
    ca.data.foreach_set("color", lin.ravel().astype(np.float32))
    me.color_attributes.active_color = ca
    if "U" in m and np.any(m["U"]):
        uvl = me.uv_layers.new(name="UV")
        uv = m["U"][m["F"].ravel()]
        uvl.data.foreach_set("uv", uv.ravel().astype(np.float32))
    ob = bpy.data.objects.new(name, me)
    co.objects.link(ob)
    if mat:
        me.materials.append(mat)
    return ob


def vc_material(name="DU_EnvVC", rough=0.85, spec=0.25):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bs = nt.nodes.get("Principled BSDF")
    at = nt.nodes.new("ShaderNodeAttribute")
    at.attribute_name = "Col"
    nt.links.new(at.outputs["Color"], bs.inputs["Base Color"])
    bs.inputs["Roughness"].default_value = rough
    if "Specular IOR Level" in bs.inputs:
        bs.inputs["Specular IOR Level"].default_value = spec
    return m


def bake_ao(ob, samples=48, ground=True, distance=1.5):
    """Cycles AO bake into a vertex colour attribute; returns per-vertex AO (n,)"""
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = samples
    sc.world = sc.world or bpy.data.worlds.new("W")
    sc.world.light_settings.distance = distance
    gp = None
    if ground:
        gm = bpy.data.meshes.new("aoground")
        gm.from_pydata([(-30, -30, 0), (30, -30, 0), (30, 30, 0), (-30, 30, 0)], [], [(0, 1, 2, 3)])
        gp = bpy.data.objects.new("aoground", gm)
        sc.collection.objects.link(gp)
    me = ob.data
    ao = me.color_attributes.new("AO", "FLOAT_COLOR", "POINT")
    me.color_attributes.active_color = ao
    hidden = []
    for o in sc.objects:
        if o not in (ob, gp) and not o.hide_render:
            o.hide_render = True
            hidden.append(o)
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.bake(type="AO", target="VERTEX_COLORS")
    a = np.zeros(len(me.vertices) * 4, np.float32)
    ao.data.foreach_get("color", a)
    for o in hidden:
        o.hide_render = False
    if gp:
        bpy.data.objects.remove(gp, do_unlink=True)
        bpy.data.meshes.remove(gm)
    me.color_attributes.active_color = me.color_attributes["Col"]
    return a.reshape(-1, 4)[:, 0]


def apply_ao(m, ao, strength_leaf=0.75, strength_bark=0.6, floor=0.25):
    k = np.where(m["K"] == 1, strength_leaf, strength_bark)
    f = 1 - k * (1 - np.clip(ao, floor, 1))
    m["C"] = l2s(s2l(m["C"]) * f[:, None])
    return m


def set_colours(ob, m):
    ca = ob.data.color_attributes["Col"]
    lin = np.hstack([s2l(m["C"]), np.ones((len(m["C"]), 1))])
    ca.data.foreach_set("color", lin.ravel().astype(np.float32))


# ------------------------------------------------------------------ bank (DWG1) writer: Blender -> Unity axes
def bank_entry(head, m):
    V = m["V"][:, [0, 2, 1]].astype(np.float32)
    N = np.clip(np.round(m["N"][:, [0, 2, 1]] * 127), -127, 127).astype(np.int8)
    N4 = np.zeros((len(V), 4), np.int8); N4[:, :3] = N
    C = np.zeros((len(V), 4), np.uint8)
    C[:, :3] = np.clip(np.round(m["C"] * 255), 0, 255)
    C[:, 3] = np.clip(np.round(m["A"] * 255), 0, 255)
    U = m["U"].astype(np.float32)
    I = m["F"][:, [0, 2, 1]].astype(np.uint32).ravel()
    head = dict(head, nv=len(V), ni=len(I))
    blob_ = V.tobytes() + N4.tobytes() + C.tobytes() + U.tobytes() + I.tobytes()
    h = json.dumps(head).encode()
    return struct.pack("<I", len(h)) + h + struct.pack("<I", len(blob_)) + blob_


def write_bank(path, entries):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(b"DWG1" + struct.pack("<I", len(entries)))
        for e in entries:
            f.write(e)
    return path


# ------------------------------------------------------------------ trees: build all, bake, export
def build_trees(do_bake=True, samples=32):
    co = coll("DU Env Trees")
    mat = vc_material()
    entries, stats = [], {}
    for ki, key in enumerate(TREES):
        for lod in range(3):
            g = make_tree(key, lod)
            m = g.build()
            ob = to_object(f"{TREES[key]['kind']}_LOD{lod}", m, co, mat)
            ob.location = (ki * 6.0, lod * 7.0, 0)
            if do_bake:
                ob.location = (0, 0, 0)
                ao = bake_ao(ob, samples=samples, distance=1.2 if TREES[key]["kind"] != "pine" else 1.6)
                ob.location = (ki * 6.0, lod * 7.0, 0)
                apply_ao(m, ao)
                # lift the canopy back to the game's overall brightness (the baked AO and dark cores pull it down)
                g_ = LEAF_GAIN.get(TREES[key]["kind"], 1.2)
                leaf = m["K"] == 1
                m["C"][leaf] = l2s(s2l(m["C"][leaf]) * g_)
                set_colours(ob, m)
            entries.append(bank_entry(dict(key=f"{key}|L{lod}", mat=300, tx=0, tz=0, proto=key, lod=lod), m))
            stats[f"{TREES[key]['kind']}{lod}"] = len(m["F"])
    return entries, stats


def preview(path, objs_filter=None, res=(1800, 800), samples=24, cam_loc=(15, -34, 9), cam_at=(15, 7, 3.2), lens=40, ortho=None):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.film_transparent = False
    w = sc.world or bpy.data.worlds.new("W")
    sc.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes.get("Background")
    bg.inputs[0].default_value = (0.55, 0.68, 0.85, 1)
    bg.inputs[1].default_value = 0.65
    for o in [o for o in sc.objects if o.name.startswith("pv_")]:
        bpy.data.objects.remove(o, do_unlink=True)
    sun = bpy.data.lights.get("pv_sun") or bpy.data.lights.new("pv_sun", "SUN")
    sun.energy = 2.6
    sun.angle = 0.05
    so = bpy.data.objects.new("pv_sun", sun)
    sc.collection.objects.link(so)
    so.rotation_euler = (math.radians(50), math.radians(10), math.radians(35))
    gm = bpy.data.meshes.get("pv_ground") or bpy.data.meshes.new("pv_ground")
    if not len(gm.vertices):
        gm.from_pydata([(-200, -200, 0), (200, -200, 0), (200, 200, 0), (-200, 200, 0)], [], [(0, 1, 2, 3)])
        gmat = bpy.data.materials.new("pv_groundmat")
        gmat.use_nodes = True
        gmat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*s2l(hx("6b7a3e")), 1)
        gm.materials.append(gmat)
    go = bpy.data.objects.new("pv_ground", gm)
    sc.collection.objects.link(go)
    cam = bpy.data.cameras.get("pv_cam") or bpy.data.cameras.new("pv_cam")
    cam.lens = lens
    if ortho:
        cam.type = "ORTHO"
        cam.ortho_scale = ortho
    else:
        cam.type = "PERSP"
    co = bpy.data.objects.new("pv_cam", cam)
    sc.collection.objects.link(co)
    co.location = cam_loc
    d = Vector(cam_at) - Vector(cam_loc)
    co.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    sc.camera = co
    hidden = []
    if objs_filter:
        for o in sc.objects:
            if o.type == "MESH" and not o.name.startswith("pv_") and not objs_filter(o) and not o.hide_render:
                o.hide_render = True
                hidden.append(o)
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    for o in hidden:
        o.hide_render = False
    return path


def run(trees=True, grass=True, track=True, ballast=True, samples=32, blend=None):
    out = {}
    if trees:
        e, st = build_trees(samples=samples)
        out["trees"] = write_bank(os.path.join(DATA, "env_trees.bytes"), e)
        out["tree_tris"] = st
    if grass:
        out["grass"] = write_bank(os.path.join(DATA, "env_grass.bytes"), build_grass())
    if track:
        e, tris = build_track()
        out["track"] = write_bank(os.path.join(DATA, "env_track.bytes"), e)
        out["track_tris"] = tris
    if ballast:
        out["ballast"] = build_ballast_texture()
    if blend:
        bpy.ops.wm.save_as_mainfile(filepath=blend)
        out["blend"] = blend
    return out
