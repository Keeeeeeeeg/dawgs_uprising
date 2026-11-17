# Dawgs Uprising -> Unity: ground and building surfaces (realistic, weathered), made in Blender and numpy.
#   run in Blender (or bpy):  import du_surfaces; du_surfaces.run()
# Writes into the Unity project (Assets/Dawgs/Textures/Surface):
#   ground  grass / meadow / dirt / sand  _a (albedo)  _n (normal)  _m (mask: G = occlusion, B = height, A = smoothness)
#           Each is a real patch of ground modelled in 3D - tens of thousands of grass blades in tufts, bare earth with
#           stones and litter, rippled sand - rendered straight down with soft sky light so it tiles without a seam.
#           The height in the mask lets the terrain blend layers by height: grass tufts stand up through the dirt
#           instead of fading into it.
#   walls   wall_a / wall_n      cast concrete: formwork panels, tie holes, rain streaks, stains, hairline cracks
#   roofs   roof_a / roof_n      felt roofing in lapped strips with gravel, patches and ponding stains
#   paving  pave_a / pave_n      worn asphalt / concrete: aggregate, sealed cracks, oil stains, patches
#           (these three multiply the buildings' own colours in the Dawgs/Lit shader, so every wall keeps its paint)
#   facades t8.png (city blocks, 2048), t12.png (houses, 1024), t9.png (lit windows): the game's own window layouts
#           redrawn sharp, with frames, sills, blinds and streaks; alpha marks the glass so the shader can make it shine
# Everything tiles: all the noise here is periodic over the tile.
import math
import os
import sys

import bpy
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import du_env as E  # noqa: E402

OUT = os.path.join(E.ROOT, "Assets", "Dawgs", "Textures", "Surface")
BAKED = os.path.join(E.ROOT, "Assets", "Dawgs", "Textures", "Baked")
hx, s2l, l2s = E.hx, E.s2l, E.l2s


# ------------------------------------------------------------------ periodic noise
def pval(res, n, rng):
    """value noise with n cells across the tile, wrapping at the edges"""
    g = rng.random((n, n))
    x = np.arange(res) / res * n
    i = np.floor(x).astype(int)
    t = x - i
    t = t * t * (3 - 2 * t)
    i0, i1 = i % n, (i + 1) % n
    tx, ty = t[None, :], t[:, None]
    return (g[np.ix_(i0, i0)] * (1 - tx) + g[np.ix_(i0, i1)] * tx) * (1 - ty) + (g[np.ix_(i1, i0)] * (1 - tx) + g[np.ix_(i1, i1)] * tx) * ty


def pfbm(res, n0, octaves, seed, gain=0.5):
    rng = np.random.default_rng(seed)
    out, amp, tot = np.zeros((res, res)), 1.0, 0.0
    for o in range(octaves):
        n = n0 * 2 ** o
        if n >= res:
            break
        out += amp * pval(res, n, rng)
        tot += amp
        amp *= gain
    return out / tot


def ss(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def pblur(a, sigma):
    """gaussian blur that wraps (so a tile stays a tile)"""
    if sigma <= 0:
        return a
    n = a.shape[0]
    f = np.fft.fftfreq(n)
    g = np.exp(-2 * (math.pi * sigma) ** 2 * f ** 2)
    return np.real(np.fft.ifft2(np.fft.fft2(a) * g[None, :] * g[:, None]))


def at(field, x, y, tile):
    """sample a periodic field (rows = y) at tile coordinates"""
    r = field.shape[0]
    return field[(np.floor(y / tile * r).astype(int)) % r, (np.floor(x / tile * r).astype(int)) % r]


def normal_from_height(h, metres_per_px, strength=1.0):
    """tangent-space normal map (R = +x, G = +y up, as Unity reads it) from a height field in metres, rows top-down"""
    dx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) / (2 * metres_per_px)
    dy = (np.roll(h, 1, 0) - np.roll(h, -1, 0)) / (2 * metres_per_px)      # +y is up the image
    n = np.dstack([-dx * strength, -dy * strength, np.ones_like(h)])
    n /= np.linalg.norm(n, axis=2, keepdims=True)
    return n


def save_rgb(path, a):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    Image.fromarray(np.clip(np.round(a * 255), 0, 255).astype(np.uint8)).save(path)


def save_normal(path, n):
    save_rgb(path, n * 0.5 + 0.5)


# ------------------------------------------------------------------ Blender plumbing
def mesh_object(name, V, F, C, co, mat, smooth=True):
    old = bpy.data.objects.get(name)
    if old:
        bpy.data.objects.remove(old, do_unlink=True)
    me = bpy.data.meshes.new(name)
    nv, nf, k = len(V), len(F), F.shape[1]
    me.vertices.add(nv)
    me.vertices.foreach_set("co", np.asarray(V, np.float32).ravel())
    me.loops.add(nf * k)
    me.loops.foreach_set("vertex_index", np.asarray(F, np.int32).ravel())
    me.polygons.add(nf)
    me.polygons.foreach_set("loop_start", np.arange(0, nf * k, k, dtype=np.int32))
    try:
        me.polygons.foreach_set("loop_total", np.full(nf, k, np.int32))
    except Exception:
        pass
    me.update(calc_edges=True)
    me.polygons.foreach_set("use_smooth", np.full(nf, smooth, bool))
    ca = me.color_attributes.new("Col", "FLOAT_COLOR", "POINT")
    ca.data.foreach_set("color", np.hstack([s2l(np.asarray(C, float)), np.ones((nv, 1))]).astype(np.float32).ravel())
    me.color_attributes.active_color = ca
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    co.objects.link(ob)
    return ob


def height_material(z0, z1):
    m = bpy.data.materials.get("DU_HeightOut") or bpy.data.materials.new("DU_HeightOut")
    m.use_nodes = True
    nt = m.node_tree
    for nd in list(nt.nodes):
        nt.nodes.remove(nd)
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value, mr.inputs["From Max"].default_value = z0, z1
    em = nt.nodes.new("ShaderNodeEmission")
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(geo.outputs["Position"], sep.inputs[0])
    nt.links.new(sep.outputs["Z"], mr.inputs["Value"])
    nt.links.new(mr.outputs[0], em.inputs["Color"])
    nt.links.new(em.outputs[0], out.inputs["Surface"])
    return m


def render_tile(name, tile, objs, res, samples, z0, z1, tmp):
    """albedo under soft sky light (occlusion settles between the blades and stones), then the height seen from above"""
    sc = bpy.context.scene
    hidden = [o for o in sc.objects if o not in objs and not o.hide_render]
    for o in hidden:
        o.hide_render = True
    cam = bpy.data.cameras.new(name + "_cam")
    cam.type = "ORTHO"
    cam.ortho_scale = tile
    cam.clip_start, cam.clip_end = 0.1, 20
    co = bpy.data.objects.new(name + "_cam", cam)
    sc.collection.objects.link(co)
    co.location = (tile / 2, tile / 2, 5)
    sc.camera = co
    w = sc.world or bpy.data.worlds.new("W")
    sc.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs[0].default_value, bg.inputs[1].default_value = (1, 1, 1, 1), 1.0
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = samples
    sc.cycles.max_bounces = 3
    sc.cycles.use_denoising = True
    sc.render.resolution_x = sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = False
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "None"
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGB"
    sc.render.image_settings.color_depth = "8"
    a_path = os.path.join(tmp, name + "_albedo.png")
    sc.render.filepath = a_path
    bpy.ops.render.render(write_still=True)
    vl = sc.view_layers[0]
    vl.material_override = height_material(z0, z1)
    bg.inputs[1].default_value = 0.0
    sc.cycles.use_denoising = False
    sc.cycles.samples = 6
    sc.view_settings.view_transform = "Raw"
    sc.render.image_settings.file_format = "OPEN_EXR"
    sc.render.image_settings.color_mode = "RGB"
    sc.render.image_settings.color_depth = "32"
    h_path = os.path.join(tmp, name + "_height.exr")
    sc.render.filepath = h_path
    bpy.ops.render.render(write_still=True)
    vl.material_override = None
    sc.view_settings.view_transform = "Standard"
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_depth = "8"
    img = bpy.data.images.load(h_path)
    px = np.array(img.pixels[:], np.float32).reshape(res, res, -1)[::-1, :, 0]     # top row first, like the PNG
    bpy.data.images.remove(img)
    alb = np.asarray(Image.open(a_path).convert("RGB"), float) / 255.0
    for o in hidden:
        o.hide_render = False
    for o in objs:
        bpy.data.objects.remove(o, do_unlink=True)
    bpy.data.objects.remove(co, do_unlink=True)
    return alb, np.clip(px, 0, 1) * (z1 - z0) + z0


# ------------------------------------------------------------------ what grows / lies on the ground
PAL = dict(root=hx("34421f"), mid=[hx("4e6234"), hx("54683a"), hx("4b5f36"), hx("506b33")], tip=[hx("5f733c"), hx("64773f"), hx("687a42"), hx("5c7a3a")],
           dry=[hx("8a8450"), hx("93895a"), hx("7f7a4a"), hx("9c9060")], straw=[hx("a89a68"), hx("b3a574"), hx("9a8c5c")])
BLADE_F = np.array([(0, 2, 1), (1, 2, 3), (2, 4, 3), (3, 4, 5), (4, 6, 5)])


def blades(base, az, lean, curl, h, w, c_root, c_mid, c_tip, rng):
    """n grass blades at once: each a tapering, curving strip of 5 triangles; returns V (n*7,3), F, C"""
    n = len(base)
    d = np.stack([np.cos(az), np.sin(az), np.zeros(n)], 1)
    sa = az + math.pi / 2 + rng.uniform(-0.6, 0.6, n)
    side = np.stack([np.cos(sa), np.sin(sa), np.zeros(n)], 1)
    V = np.zeros((n, 7, 3))
    C = np.zeros((n, 7, 3))
    k = 0
    for i, t in enumerate((0.0, 1 / 3, 2 / 3, 1.0)):
        bend = lean * t + curl * t * t
        p = base + d * (h * bend * 0.55)[:, None]
        p[:, 2] += h * (t - 0.18 * curl * t * t)
        col = c_root * (1 - 2 * t) + c_mid * 2 * t if t < 0.5 else c_mid * (2 - 2 * t) + c_tip * (2 * t - 1)
        if i < 3:
            ww = (w * (1 - t) ** 0.9 / 2)[:, None]
            V[:, k], V[:, k + 1] = p - side * ww, p + side * ww
            C[:, k] = C[:, k + 1] = col
            k += 2
        else:
            V[:, k], C[:, k] = p, c_tip
    F = (BLADE_F[None, :, :] + (np.arange(n) * 7)[:, None, None]).reshape(-1, 3)
    return V.reshape(-1, 3), F, C.reshape(-1, 3)


def wrap_copies(P, tile, margin):
    """offsets that put things near an edge on the far side too, so the tile wraps"""
    out = []
    for dx in (-tile, 0, tile):
        for dy in (-tile, 0, tile):
            m = (P[:, 0] + dx > -margin) & (P[:, 0] + dx < tile + margin) & (P[:, 1] + dy > -margin) & (P[:, 1] + dy < tile + margin)
            out.append((np.nonzero(m)[0], np.array([dx, dy, 0.0])))
    return out


def pick(rng, cols, n, lo=0.9, hi=1.1):
    c = np.stack(cols)[rng.integers(0, len(cols), n)]
    return c * rng.uniform(lo, hi, (n, 1))


def grass_layer(tile, spacing, rng, cover=None, keep=1.0, n_blades=(7, 12), h=(0.07, 0.17), dry=None, dry_bias=0.0, hf=None, splay=(0.3, 0.9)):
    """tufts on a jittered grid; cover (periodic field 0..1) thins them into clumps, dry (field) yellows them"""
    g = int(round(tile / spacing))
    gx, gy = np.meshgrid(np.arange(g), np.arange(g))
    c = np.stack([(gx.ravel() + rng.uniform(0.1, 0.9, g * g)) * tile / g, (gy.ravel() + rng.uniform(0.1, 0.9, g * g)) * tile / g], 1)
    if cover is not None:
        c = c[at(cover, c[:, 0], c[:, 1], tile) > 1 - keep + rng.uniform(-0.08, 0.08, len(c))]
    nt = len(c)
    nb = rng.integers(n_blades[0], n_blades[1] + 1, nt)
    ti = np.repeat(np.arange(nt), nb)
    n = len(ti)
    r = rng.uniform(0.015, 0.05, nt)[ti] * np.sqrt(rng.random(n))
    a0 = rng.uniform(0, 2 * math.pi, n)
    base = np.stack([c[ti, 0] + np.cos(a0) * r, c[ti, 1] + np.sin(a0) * r, np.full(n, -0.008)], 1)
    az = a0 + rng.uniform(-0.7, 0.7, n)
    hh = rng.uniform(h[0], h[1], n) * rng.uniform(0.8, 1.2, nt)[ti]
    if hf is not None:
        hh *= 0.65 + 0.7 * at(hf, base[:, 0], base[:, 1], tile)
    dr = np.clip((at(dry, base[:, 0], base[:, 1], tile) if dry is not None else np.zeros(n)) + dry_bias + rng.uniform(-0.25, 0.25, nt)[ti], 0, 1)
    dead = rng.random(n) < 0.03 + 0.25 * dr ** 2
    gain = rng.uniform(0.86, 1.12, (nt, 1))[ti]
    mid = pick(rng, PAL["mid"], n) * (1 - dr[:, None] * 0.75) + pick(rng, PAL["dry"], n) * 0.85 * dr[:, None] * 0.75
    tip = pick(rng, PAL["tip"], n) * (1 - dr[:, None]) + pick(rng, PAL["dry"], n) * dr[:, None]
    mid[dead], tip[dead] = pick(rng, PAL["dry"], int(dead.sum())) * 0.9, pick(rng, PAL["straw"], int(dead.sum()))
    root = np.tile(PAL["root"], (n, 1)) * (1 - dr[:, None] * 0.3) + hx("5a4c30") * dr[:, None] * 0.3
    V, F, C = blades(base, az, rng.uniform(splay[0], splay[1], n), rng.uniform(0.1, 0.6, n), hh, rng.uniform(0.014, 0.026, n), root * gain, mid * gain, tip * gain, rng)
    Vs, Fs, Cs, o = [], [], [], 0
    for idx, off in wrap_copies(base, tile, 0.3):
        if not len(idx):
            continue
        vi = (idx[:, None] * 7 + np.arange(7)[None, :]).ravel()
        remap = np.full(n * 7, -1)
        remap[vi] = np.arange(len(vi))
        Vs.append(V[vi] + off)
        Cs.append(C[vi])
        Fs.append(remap[F[(idx[:, None] * 5 + np.arange(5)[None, :]).ravel()]] + o)
        o += len(vi)
    return np.vstack(Vs), np.vstack(Fs), np.vstack(Cs)


def litter(tile, n, rng, zf, cols):
    """dead blades lying flat on the earth"""
    base = np.stack([rng.uniform(0, tile, n), rng.uniform(0, tile, n), np.zeros(n)], 1)
    base[:, 2] = at(zf, base[:, 0], base[:, 1], tile) + 0.004
    c = pick(rng, cols, n, 0.85, 1.1)
    V, F, C = blades(base, rng.uniform(0, 2 * math.pi, n), rng.uniform(2.2, 3.2, n), rng.uniform(-0.3, 0.3, n), rng.uniform(0.02, 0.05, n),
                     rng.uniform(0.008, 0.016, n), c * 0.9, c, c * 1.05, rng)
    Vs, Fs, Cs, o = [], [], [], 0
    for idx, off in wrap_copies(base, tile, 0.3):
        if not len(idx):
            continue
        vi = (idx[:, None] * 7 + np.arange(7)[None, :]).ravel()
        remap = np.full(n * 7, -1)
        remap[vi] = np.arange(len(vi))
        Vs.append(V[vi] + off)
        Cs.append(C[vi])
        Fs.append(remap[F[(idx[:, None] * 5 + np.arange(5)[None, :]).ravel()]] + o)
        o += len(vi)
    return np.vstack(Vs), np.vstack(Fs), np.vstack(Cs)


def stones(tile, n, rng, zf, cols, size=(0.004, 0.02), sink=0.45, level=1):
    U, F0 = E.ico(level)
    nu = len(U)
    c = np.stack([rng.uniform(0, tile, n), rng.uniform(0, tile, n)], 1)
    r = rng.uniform(size[0], size[1], n) * rng.uniform(0.6, 1.0, n) ** 2 * 1.4
    Vs, Fs, Cs, o = [], [], [], 0
    P = np.stack([c[:, 0], c[:, 1], at(zf, c[:, 0], c[:, 1], tile)], 1)
    col = pick(rng, cols, n, 0.85, 1.12)
    shapes = []
    for i in range(n):
        k = 1 + rng.uniform(-0.2, 0.2, nu)
        sh = np.array([r[i] * rng.uniform(0.8, 1.35), r[i] * rng.uniform(0.7, 1.1), r[i] * rng.uniform(0.45, 0.8)])
        W = (U * k[:, None] * sh) @ E.rotz(rng.uniform(0, 6.28)).T
        W[:, 2] += sh[2] * (1 - 2 * sink)
        shapes.append(W)
    for idx, off in wrap_copies(P, tile, 0.15):
        for i in idx:
            Vs.append(shapes[i] + P[i] + off)
            Fs.append(F0 + o)
            Cs.append(np.tile(col[i], (nu, 1)))
            o += nu
    return np.vstack(Vs), np.vstack(Fs), np.vstack(Cs)


def ground(tile, n, zf, cf, pad=0.3):
    """the earth itself: a fine grid over the tile (and a little beyond), heights and colours from periodic fields"""
    xs = np.linspace(-pad, tile + pad, n + 1)
    X, Y = np.meshgrid(xs, xs)
    Z = at(zf, X, Y, tile)
    V = np.stack([X.ravel(), Y.ravel(), Z.ravel()], 1)
    i = np.arange(n * n)
    a = i + i // n
    F = np.stack([a, a + 1, a + n + 2, a + n + 1], 1)
    r = cf.shape[0]
    C = cf[(np.floor(Y.ravel() / tile * r).astype(int)) % r, (np.floor(X.ravel() / tile * r).astype(int)) % r]
    return V, F, C


def mix(c0, c1, t):
    return c0[None, None, :] * (1 - t[..., None]) + c1[None, None, :] * t[..., None]


# ------------------------------------------------------------------ the four ground tiles
GROUND = dict(
    grass=dict(tile=6.0, mean=hx("5a6d41"), smooth=0.16, hmap=(-0.02, 0.17)),
    meadow=dict(tile=6.0, mean=hx("6f6c43"), smooth=0.13, hmap=(-0.02, 0.17)),
    dirt=dict(tile=5.0, mean=hx("7d6b4c"), smooth=0.10, hmap=(-0.045, 0.10)),
    sand=dict(tile=5.0, mean=hx("a89c79"), smooth=0.20, hmap=(-0.05, 0.10)),
)


def scene_grass(tile, rng, R=512):
    co, mat = E.coll("DU Surfaces"), E.vc_material("DU_GroundVC", rough=0.9, spec=0.15)
    zf = (pfbm(R, 6, 4, 11) - 0.5) * 0.03
    thatch = mix(hx("3a3a20"), hx("4a4426"), pfbm(R, 24, 3, 12)) * (0.85 + 0.3 * pfbm(R, 96, 2, 13))[..., None]
    objs = [mesh_object("g_ground", *ground(tile, 360, zf, thatch), co, mat)]
    dry = ss(pfbm(R, 4, 4, 14), 0.45, 0.85) * 0.55
    hf = pfbm(R, 7, 3, 15)
    V, F, C = grass_layer(tile, 0.072, rng, dry=dry, hf=hf)
    objs.append(mesh_object("g_blades", V, F, C, co, mat))
    V, F, C = grass_layer(tile, 0.19, rng, cover=pfbm(R, 9, 3, 16), keep=0.55, n_blades=(5, 9), h=(0.13, 0.24), dry=dry, dry_bias=0.1, splay=(0.2, 0.6))
    objs.append(mesh_object("g_tall", V, F, C, co, mat))
    return objs


def scene_meadow(tile, rng, R=512):
    co, mat = E.coll("DU Surfaces"), E.vc_material("DU_GroundVC", rough=0.9, spec=0.15)
    zf = (pfbm(R, 5, 5, 21) - 0.5) * 0.045
    earth = mix(hx("5c4a32"), hx("7a6646"), pfbm(R, 10, 4, 22)) * (0.82 + 0.36 * pfbm(R, 128, 2, 23))[..., None]
    objs = [mesh_object("m_ground", *ground(tile, 520, zf, earth), co, mat)]
    cover = pfbm(R, 5, 4, 24)
    dry = 0.35 + 0.5 * pfbm(R, 4, 3, 25)
    V, F, C = grass_layer(tile, 0.085, rng, cover=cover, keep=0.60, n_blades=(8, 14), h=(0.08, 0.2), dry=dry, hf=pfbm(R, 8, 3, 26), splay=(0.35, 1.0))
    objs.append(mesh_object("m_blades", V, F, C, co, mat))
    V, F, C = grass_layer(tile, 0.24, rng, cover=cover, keep=0.45, n_blades=(6, 10), h=(0.16, 0.3), dry=dry, dry_bias=0.25, splay=(0.2, 0.55))
    objs.append(mesh_object("m_tall", V, F, C, co, mat))
    V, F, C = litter(tile, 2600, rng, zf, PAL["straw"] + PAL["dry"])
    objs.append(mesh_object("m_litter", V, F, C, co, mat))
    V, F, C = stones(tile, 900, rng, zf, [hx("8e8676"), hx("7a7264"), hx("9e9482"), hx("6c6252")], size=(0.004, 0.016))
    objs.append(mesh_object("m_stones", V, F, C, co, mat, smooth=False))
    return objs


def cracks(R, cells, seed):
    """dried-mud crack lines: distance to the nearest cell wall of a periodic Voronoi diagram (0 on a crack)"""
    rng = np.random.default_rng(seed)
    g = cells
    pts = (np.stack(np.meshgrid(np.arange(g), np.arange(g)), -1).reshape(-1, 2) + rng.uniform(0.15, 0.85, (g * g, 2))) / g
    yy, xx = np.mgrid[0:R, 0:R] / R
    d1 = np.full((R, R), 9.0)
    d2 = np.full((R, R), 9.0)
    for p in pts:
        dx = np.abs(xx - p[0]); dx = np.minimum(dx, 1 - dx)
        dy = np.abs(yy - p[1]); dy = np.minimum(dy, 1 - dy)
        d = np.hypot(dx, dy)
        near = d < d1
        d2 = np.where(near, d1, np.minimum(d2, d))
        d1 = np.where(near, d, d1)
    return (d2 - d1) * g


def scene_dirt(tile, rng, R=1024):
    co, mat = E.coll("DU Surfaces"), E.vc_material("DU_GroundVC", rough=0.9, spec=0.15)
    big = pfbm(R, 3, 5, 31)
    cr = cracks(R, 11, 32)
    crackle = ss(pfbm(R, 3, 3, 33), 0.55, 0.78) * 0.75                            # where the earth has dried and split
    groove = (1 - ss(cr, 0.0, 0.09)) * crackle
    zf = (big - 0.5) * 0.06 + (pfbm(R, 28, 3, 34) - 0.5) * 0.012 + (pfbm(R, 160, 2, 35) - 0.5) * 0.004 - groove * 0.012
    damp = ss(pfbm(R, 4, 4, 36), 0.5, 0.9)
    earth = mix(hx("7a6748"), hx("94805a"), pfbm(R, 7, 4, 37))
    earth = earth * (1 - damp[..., None] * 0.28) * (0.86 + 0.28 * pfbm(R, 200, 2, 38))[..., None] * (1 - groove[..., None] * 0.3)
    objs = [mesh_object("d_ground", *ground(tile, 860, zf, earth), co, mat)]
    greys = [hx("8e8676"), hx("7a7264"), hx("a39a88"), hx("6c6252"), hx("94856c"), hx("b0a892")]
    V, F, C = stones(tile, 2600, rng, zf, greys, size=(0.004, 0.017))
    objs.append(mesh_object("d_pebbles", V, F, C, co, mat, smooth=False))
    V, F, C = stones(tile, 70, rng, zf, greys, size=(0.03, 0.06), sink=0.55)
    objs.append(mesh_object("d_stones", V, F, C, co, mat, smooth=False))
    V, F, C = litter(tile, 2200, rng, zf, PAL["straw"] + PAL["dry"])
    objs.append(mesh_object("d_litter", V, F, C, co, mat))
    V, F, C = grass_layer(tile, 0.3, rng, cover=pfbm(512, 6, 3, 39), keep=0.22, n_blades=(4, 7), h=(0.05, 0.12), dry_bias=0.7, splay=(0.5, 1.2))
    objs.append(mesh_object("d_wisps", V, F, C, co, mat))
    return objs


def scene_sand(tile, rng, R=1024):
    co, mat = E.coll("DU Surfaces"), E.vc_material("DU_GroundVC", rough=0.85, spec=0.2)
    yy, xx = np.mgrid[0:R, 0:R] / R
    warp = (pfbm(R, 3, 4, 41) - 0.5) * 2.2 + (pfbm(R, 9, 3, 42) - 0.5) * 0.5
    ripple = np.sin(2 * math.pi * (xx * 38 + yy * 9 + warp))                       # wind ripples, a whole number of them per tile
    fade = 0.35 + 0.65 * ss(pfbm(R, 4, 3, 43), 0.3, 0.7)
    zf = (pfbm(R, 3, 4, 44) - 0.5) * 0.05 + ripple * 0.0045 * fade + (pfbm(R, 180, 2, 45) - 0.5) * 0.002
    grain = pfbm(R, 256, 1, 46)
    sand = mix(hx("b0a27c"), hx("c2b48e"), pfbm(R, 6, 4, 47)) * (0.9 + 0.2 * grain)[..., None] * (1 - 0.07 * (ripple * fade < -0.4))[..., None]
    sand = sand * (1 - 0.16 * ss(pfbm(R, 5, 4, 48), 0.55, 0.9))[..., None]         # darker damp drifts
    objs = [mesh_object("s_ground", *ground(tile, 860, zf, sand), co, mat)]
    V, F, C = stones(tile, 520, rng, zf, [hx("d8d0bc"), hx("8a8272"), hx("a89c84"), hx("6e665a"), hx("e4dccb")], size=(0.004, 0.014))
    objs.append(mesh_object("s_shells", V, F, C, co, mat, smooth=False))
    return objs


SCENES = dict(grass=scene_grass, meadow=scene_meadow, dirt=scene_dirt, sand=scene_sand)


def build_ground(names=None, res=1024, samples=40, tmp=None):
    os.makedirs(OUT, exist_ok=True)
    tmp = tmp or os.path.join(OUT, "_work")
    os.makedirs(tmp, exist_ok=True)
    out = {}
    for name in names or list(GROUND):
        g = GROUND[name]
        rng = np.random.default_rng(dict(grass=1, meadow=2, dirt=3, sand=4)[name])
        objs = SCENES[name](g["tile"], rng)
        alb, hgt = render_tile(name, g["tile"], objs, res, samples, -0.08, 0.36, tmp)
        # albedo: bring the tile to the palette the game's ground has (the grass models were matched to it)
        lin = s2l(alb)
        lin *= (s2l(g["mean"]) / lin.reshape(-1, 3).mean(0))[None, None, :]
        save_rgb(os.path.join(OUT, name + "_a.png"), l2s(lin))
        save_normal(os.path.join(OUT, name + "_n.png"), normal_from_height(pblur(hgt, 0.6), g["tile"] / res, 1.0))
        h01 = np.clip((hgt - g["hmap"][0]) / (g["hmap"][1] - g["hmap"][0]), 0, 1)
        cav = np.clip(0.82 + (pblur(hgt, 1.0) - pblur(hgt, 9.0)) * 9.0, 0.55, 1.0)   # a little occlusion in the hollows
        m = np.dstack([np.zeros_like(h01), cav, h01, np.full_like(h01, g["smooth"])])
        Image.fromarray(np.clip(np.round(m * 255), 0, 255).astype(np.uint8), "RGBA").save(os.path.join(OUT, name + "_m.png"))
        out[name] = dict(mean=[round(float(v), 3) for v in l2s(lin).reshape(-1, 3).mean(0)], h=[round(float(hgt.min()), 3), round(float(hgt.max()), 3)],
                         h01=round(float(h01.mean()), 3))
    return out


# ------------------------------------------------------------------ building surfaces (numpy, periodic)
def lines_h(R, ys, width):
    """soft horizontal lines at rows ys (px), wrapping"""
    y = np.arange(R)[:, None]
    out = np.zeros((R, 1))
    for y0 in ys:
        d = np.abs(y - y0); d = np.minimum(d, R - d)
        out = np.maximum(out, np.exp(-(d / width) ** 2))
    return np.repeat(out, R, 1)


def build_wall(R=1024, tile=8.0, seed=5):
    """cast concrete seen face-on: u runs along the wall, v is up. 8 m tile: pours 2 m high, panels 4 m wide, staggered"""
    rng = np.random.default_rng(seed)
    px = R / tile                                                                  # pixels per metre
    yy, xx = np.mgrid[0:R, 0:R]
    row = (yy // (2 * px)).astype(int)                                             # which pour (0 at the top of the image)
    xo = (xx + (row % 2) * 2 * px) % R
    col = (xo // (4 * px)).astype(int)
    seam_h = lines_h(R, [k * 2 * px for k in range(4)], 1.3)
    dxs = np.abs(xo % (4 * px)); dxs = np.minimum(dxs, 4 * px - dxs)
    seam_v = np.exp(-(dxs / 1.1) ** 2)
    seam = np.maximum(seam_h, seam_v * 0.8)
    # each panel poured a little differently
    tone = rng.uniform(-0.045, 0.045, (4, 2))[row % 4, col % 2]
    # tie holes: four across each panel, two rows per pour
    holes = np.zeros((R, R))
    for ry in (0.5, 1.5):
        for rx in (0.5, 1.5, 2.5, 3.5):
            d = np.hypot((xo % (4 * px)) - rx * px, (yy % (2 * px)) - ry * px)
            holes = np.maximum(holes, np.exp(-(d / 2.6) ** 2))
    # stains: broad blotches, and streaks that start under a seam or a tie hole and run down the wall
    blot = pfbm(R, 3, 5, seed + 1)
    streak_src = pfbm(R, 90, 2, seed + 2)[0:1, :]                                  # varies along the wall only
    streaks = np.zeros((R, R))
    for k in range(4):
        y0 = k * 2 * px
        d = (yy - y0) % R                                                          # distance below this seam
        ln = (0.25 + 1.5 * pval(R, 23, rng)[0:1, :] ** 2) * px                     # how far each streak runs
        s = ss(streak_src + 0.25 * pval(R, 150, rng)[k:k + 1, :], 0.62, 0.78) * np.exp(-d / ln) * (d < 2 * px)
        streaks = np.maximum(streaks, s)
    drip = pblur(streaks, 1.2)
    wet = np.exp(-((yy % (2 * px)) / (0.16 * px))) * 0.5                            # the band just under each seam stays damp longer
    light = ss(pfbm(R, 60, 2, seed + 3)[0:1, :] * np.ones((R, 1)), 0.7, 0.82) * np.exp(-((yy % (2 * px)) / (0.7 * px)))   # lime bloom
    # hairline cracks: a few wandering lines
    ci = Image.new("L", (R, R), 0)
    dr = ImageDraw.Draw(ci)
    for i in range(9):
        x, y = rng.uniform(0, R), rng.uniform(0, R)
        pts = [(x, y)]
        for k in range(rng.integers(6, 14)):
            x += rng.normal(0, 14); y += rng.uniform(6, 26)
            pts.append((x, y))
        for ox in (-R, 0, R):
            for oy in (-R, 0, R):
                dr.line([(a + ox, b + oy) for a, b in pts], fill=255, width=1)
    crack = np.asarray(ci.filter(ImageFilter.GaussianBlur(0.6)), float) / 255.0
    grain = pfbm(R, 128, 3, seed + 4) - 0.5
    pits = ss(pfbm(R, 200, 2, seed + 5), 0.72, 0.85)                               # bug holes left by air in the pour
    v = 1.0 + tone + (blot - 0.5) * 0.16 + grain * 0.09 - seam * 0.2 - holes * 0.3 - drip * 0.24 - wet * 0.07 * (0.4 + blot) + light * 0.08 - crack * 0.22 - pits * 0.1
    rust = ss(pfbm(R, 5, 3, seed + 6), 0.62, 0.8) * drip                           # some streaks carry rust from the ties
    rgb = np.dstack([v * (1 + 0.10 * rust + 0.015 * (blot - 0.5)), v * (1 - 0.02 * rust), v * (1 - 0.13 * rust - 0.03 * (blot - 0.5) - 0.025 * drip)])
    rgb /= rgb.reshape(-1, 3).mean(0)[None, None, :]
    # alpha: weathering big enough to read from the battle camera, used at 4x the size (a 32 m tile): long rain runs
    # down from where water collects, broad damp patches and lighter, sun-bleached stretches (0.5 = no change)
    mrng = np.random.default_rng(seed + 20)
    runs = np.zeros((R, R))
    for i in range(55):
        x0, y0 = mrng.uniform(0, R), mrng.uniform(0, R)
        w, ln, k = mrng.uniform(5, 26), mrng.uniform(0.08, 0.45) * R, mrng.uniform(0.3, 1.0)
        dx = np.abs(xx - x0); dx = np.minimum(dx, R - dx)
        d = (yy - y0) % R
        runs = np.maximum(runs, k * np.exp(-(dx / w) ** 2) * np.exp(-d / ln) * (d < 0.8 * R))
    runs = pblur(runs, 2.0)
    damp = ss(pfbm(R, 3, 4, seed + 21), 0.55, 0.85)
    bleach = ss(pfbm(R, 2, 3, seed + 22), 0.6, 0.85)
    macro = 0.5 - 0.30 * runs - 0.14 * damp + 0.10 * bleach
    macro += 0.5 - macro.mean()
    os.makedirs(OUT, exist_ok=True)
    rgba = np.dstack([np.clip(rgb * 0.5, 0, 1), np.clip(macro, 0, 1)])
    Image.fromarray(np.round(rgba * 255).astype(np.uint8), "RGBA").save(os.path.join(OUT, "wall_a.png"))   # rgb stored at half: 0.5 = leave the colour alone
    h = -seam * 0.004 - holes * 0.006 - crack * 0.002 + grain * 0.0012 - pits * 0.0015 + tone * 0.01
    save_normal(os.path.join(OUT, "wall_n.png"), normal_from_height(h, tile / R, 1.0))
    return dict(mean=[round(float(x), 3) for x in rgb.reshape(-1, 3).mean(0)], std=round(float(v.std()), 3))


def build_roof(R=1024, tile=6.0, seed=9):
    """felt roofing from above: lapped strips a metre wide, mineral chippings, patches, ponding stains"""
    rng = np.random.default_rng(seed)
    px = R / tile
    yy, xx = np.mgrid[0:R, 0:R]
    strip = (yy // px).astype(int)
    lap = np.exp(-(((yy % px)) / 2.0) ** 2)                                        # the lap of each strip over the next
    lap_soft = np.exp(-((yy % px) / (0.08 * px)))
    tone = rng.uniform(-0.05, 0.05, 6)[strip % 6]
    # end laps: each strip is jointed somewhere along its length
    ends = np.zeros((R, R))
    for s in range(6):
        x0 = rng.uniform(0, R)
        d = np.abs(xx - x0); d = np.minimum(d, R - d)
        ends = np.maximum(ends, np.exp(-(d / 1.6) ** 2) * (strip == s))
    chips = pfbm(R, 256, 2, seed + 1) - 0.5
    speck = (pval(R, 510, rng) > 0.9) * 0.10 - (pval(R, 509, rng) > 0.93) * 0.12
    blot = pfbm(R, 3, 5, seed + 2)
    pond = pfbm(R, 4, 4, seed + 3)
    pool = ss(pond, 0.56, 0.62)                                                    # where water stands after rain
    ring = ss(pond, 0.545, 0.565) * (1 - ss(pond, 0.565, 0.60))                    # the tide mark it leaves
    # repair patches: a few rectangles of newer felt, torched on at slightly different angles
    pat = Image.new("L", (R, R), 0)
    dr = ImageDraw.Draw(pat)
    edge = Image.new("L", (R, R), 0)
    de = ImageDraw.Draw(edge)
    for i in range(7):
        w, h, x, y = rng.uniform(0.5, 1.5) * px, rng.uniform(0.4, 1.1) * px, rng.uniform(0, R), rng.uniform(0, R)
        for ox in (-R, 0, R):
            for oy in (-R, 0, R):
                dr.rectangle([x + ox, y + oy, x + ox + w, y + oy + h], fill=int(rng.uniform(90, 255)))
                de.rectangle([x + ox, y + oy, x + ox + w, y + oy + h], outline=255, width=2)
    patch = np.asarray(pat, float) / 255.0
    pedge = np.asarray(edge.filter(ImageFilter.GaussianBlur(0.8)), float) / 255.0
    moss = ss(pfbm(R, 6, 4, seed + 4), 0.66, 0.8) * (0.4 + 0.6 * lap_soft)          # green grows along the laps
    v = 1.0 + tone + (blot - 0.5) * 0.2 + chips * 0.16 + speck - lap * 0.22 - ends * 0.2 - lap_soft * 0.05 - pool * 0.1 + ring * 0.1 + (patch - 0.5) * 0.14 * (patch > 0) - pedge * 0.2
    rgb = np.dstack([v * (1 - 0.10 * moss + 0.02 * ring), v * (1 + 0.03 * moss + 0.01 * ring), v * (1 - 0.16 * moss - 0.03 * pool)])
    rgb /= rgb.reshape(-1, 3).mean(0)[None, None, :]
    save_rgb(os.path.join(OUT, "roof_a.png"), rgb * 0.5)
    h = chips * 0.003 + lap * 0.004 + lap_soft * 0.002 + ends * 0.003 + pedge * 0.003 + (patch > 0) * 0.002 - pool * 0.001
    save_normal(os.path.join(OUT, "roof_n.png"), normal_from_height(h, tile / R, 1.0))
    return dict(mean=[round(float(x), 3) for x in rgb.reshape(-1, 3).mean(0)], std=round(float(v.std()), 3))


def build_pave(R=1024, tile=5.0, seed=13):
    """worn asphalt and concrete from above: aggregate showing through, sealed cracks, oil stains, a patch or two"""
    rng = np.random.default_rng(seed)
    px = R / tile
    agg = pfbm(R, 256, 2, seed + 1) - 0.5
    stones_ = (pval(R, 400, rng) > 0.86) * 0.13 - (pval(R, 380, rng) > 0.9) * 0.10
    blot = pfbm(R, 3, 5, seed + 2)
    wear = ss(pfbm(R, 2, 3, seed + 3), 0.4, 0.75)                                  # polished, paler where traffic runs
    warp = (pfbm(R, 6, 3, seed + 7) - 0.5) * 0.05
    cr = np.roll(cracks(R, 6, seed + 4), (int(R * 0.013), 0), (0, 1)) + warp
    crack = (1 - ss(cr, 0.0, 0.022)) * ss(pfbm(R, 3, 3, seed + 5), 0.52, 0.72)      # only parts of the network have opened
    seal = pblur(crack, 2.2)                                                       # tar poured over the worst of them
    oil = ss(pfbm(R, 7, 4, seed + 6), 0.7, 0.86)
    pat = Image.new("L", (R, R), 0)
    dr = ImageDraw.Draw(pat)
    edge = Image.new("L", (R, R), 0)
    de = ImageDraw.Draw(edge)
    for i in range(3):
        w, h, x, y = rng.uniform(0.8, 1.8) * px, rng.uniform(0.6, 1.2) * px, rng.uniform(0, R), rng.uniform(0, R)
        for ox in (-R, 0, R):
            for oy in (-R, 0, R):
                dr.rectangle([x + ox, y + oy, x + ox + w, y + oy + h], fill=255)
                de.rectangle([x + ox, y + oy, x + ox + w, y + oy + h], outline=255, width=2)
    patch = np.asarray(pat, float) / 255.0
    pedge = np.asarray(edge.filter(ImageFilter.GaussianBlur(0.9)), float) / 255.0
    v = 1.0 + (blot - 0.5) * 0.18 + agg * 0.2 + stones_ + wear * 0.07 - crack * 0.22 - seal * 0.16 - oil * 0.2 - patch * 0.08 - pedge * 0.18
    rgb = np.dstack([v * (1 + 0.012 * wear), v, v * (1 - 0.03 * wear - 0.04 * oil)])
    rgb /= rgb.reshape(-1, 3).mean(0)[None, None, :]
    save_rgb(os.path.join(OUT, "pave_a.png"), rgb * 0.5)
    h = agg * 0.003 + stones_ * 0.01 - crack * 0.004 + seal * 0.001 + pedge * 0.002
    save_normal(os.path.join(OUT, "pave_n.png"), normal_from_height(h, tile / R, 1.0))
    return dict(mean=[round(float(x), 3) for x in rgb.reshape(-1, 3).mean(0)], std=round(float(v.std()), 3))


# ------------------------------------------------------------------ facades: the game's window layouts, redrawn sharp
def _streaks(im, rng, n, x0, x1, y0, y1, length, alpha, col=(30, 28, 22)):
    ov = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    for i in range(n):
        x, y, ln = rng.uniform(x0, x1), rng.uniform(y0, y1), rng.uniform(*length)
        w = rng.uniform(1.5, 5)
        for k in range(8):
            d.rectangle([x, y + ln * k / 8, x + w, y + ln * (k + 1) / 8], fill=(*col, int(alpha * 255 * (1 - k / 8) * rng.uniform(0.6, 1))))
    im.alpha_composite(ov.filter(ImageFilter.GaussianBlur(1.2)))


def build_city_facade(S=2048, seed=77):
    """t8: ten bays by five storeys (the lit-window map t9 uses the same grid). Alpha = 255 wall, low = glass."""
    rng = np.random.default_rng(seed)
    k = S / 512.0
    im = Image.new("RGBA", (S, S), (74, 80, 72, 255))
    gl = Image.new("L", (S, S), 255)
    d, dg = ImageDraw.Draw(im), ImageDraw.Draw(gl)
    bay, st = 51.2 * k, 102.4 * k
    for s in range(5):
        y = s * st
        # the spandrel: precast panels below the windows, a pale ledge on top, a shadow line beneath it
        for b in range(10):
            g = rng.uniform(-7, 7)
            d.rectangle([b * bay, y + 66 * k, (b + 1) * bay, y + st], fill=(int(86 + g), int(91 + g), int(66 + g * 0.8), 255))
            d.line([b * bay, y + 84 * k, (b + 1) * bay, y + 84 * k], fill=(60, 64, 46, 255), width=max(1, int(0.6 * k)))
            if rng.random() < 0.3:                                                 # a louvred vent
                vx, vy = b * bay + 30 * k, y + 71 * k
                d.rectangle([vx, vy, vx + 17 * k, vy + 17 * k], fill=(70, 74, 56, 255))
                for j in range(5):
                    d.rectangle([vx + k, vy + (1.2 + j * 3.2) * k, vx + 16 * k, vy + (2.6 + j * 3.2) * k], fill=(128, 130, 118, 255))
                    d.line([vx + k, vy + (2.9 + j * 3.2) * k, vx + 16 * k, vy + (2.9 + j * 3.2) * k], fill=(40, 43, 34, 255), width=1)
        d.rectangle([0, y + 66 * k, S, y + 69 * k], fill=(186, 186, 176, 255))
        d.rectangle([0, y + 69 * k, S, y + 70.2 * k], fill=(52, 56, 44, 255))
        d.rectangle([0, y + st - 1.5 * k, S, y + st], fill=(44, 47, 42, 255))
        # the head of the window band
        d.rectangle([0, y, S, y + 6 * k], fill=(66, 72, 80, 255))
        d.rectangle([0, y + 5 * k, S, y + 6.2 * k], fill=(120, 128, 134, 255))
        for b in range(10):
            x0, y0, w, h = b * bay + 5 * k, y + 7 * k, 42 * k, 56 * k
            # glass: the sky's reflection, brighter towards the top, a blind or the dark of a room behind it
            v = rng.random()
            top = np.array([96 + v * 30, 118 + v * 30, 138 + v * 32])
            bot = np.array([36 + v * 12, 48 + v * 12, 62 + v * 14])
            for j in range(int(h)):
                t = j / h
                c = top * (1 - t) ** 1.6 + bot * (1 - (1 - t) ** 1.6)
                d.line([x0, y0 + j, x0 + w, y0 + j], fill=(int(c[0]), int(c[1]), int(c[2]), 255))
            if rng.random() < 0.45:                                                # a blind drawn part way
                bh = rng.uniform(0.15, 0.7) * h
                bc = int(rng.uniform(150, 190))
                ov = Image.new("RGBA", (int(w), int(bh)), (bc, bc - 4, bc - 14, 150))
                od = ImageDraw.Draw(ov)
                for j in range(0, int(bh), max(2, int(1.6 * k))):
                    od.line([0, j, w, j], fill=(60, 60, 56, 120), width=1)
                im.alpha_composite(ov, (int(x0), int(y0)))
            # a diagonal glint across the upper corner
            ov = Image.new("RGBA", (int(w), int(h)), (0, 0, 0, 0))
            ImageDraw.Draw(ov).polygon([(0, 0), (w * 0.42, 0), (w * 0.18, h * 0.42), (0, h * 0.42)], fill=(190, 210, 225, 46))
            im.alpha_composite(ov, (int(x0), int(y0)))
            dg.rectangle([x0, y0, x0 + w, y0 + h], fill=40)
            # frame, transom, mullion, sill
            fc, fd = (150, 156, 160, 255), (44, 50, 56, 255)
            fw = max(2, int(1.3 * k))
            d.rectangle([x0 - fw, y0 - fw, x0 + w + fw, y0], fill=fc); d.rectangle([x0 - fw, y0, x0, y0 + h], fill=fc)
            d.rectangle([x0 + w, y0, x0 + w + fw, y0 + h], fill=(104, 110, 116, 255))
            ty = y0 + h * 0.46
            d.rectangle([x0, ty, x0 + w, ty + fw], fill=(98, 106, 112, 255)); d.line([x0, ty + fw, x0 + w, ty + fw], fill=fd, width=1)
            if b % 2 == 0:
                d.rectangle([x0 + w / 2 - fw / 2, ty, x0 + w / 2 + fw / 2, y0 + h], fill=(98, 106, 112, 255))
            for box in ([x0 - fw, y0 - fw, x0 + w + fw, y0], [x0 - fw, y0, x0, y0 + h], [x0 + w, y0, x0 + w + fw, y0 + h], [x0, ty, x0 + w, ty + fw]):
                dg.rectangle(box, fill=255)
            d.rectangle([x0 - k, y0 + h, x0 + w + k, y0 + h + 3 * k], fill=(176, 176, 166, 255))
            d.line([x0 - k, y0 + h + 3 * k, x0 + w + k, y0 + h + 3 * k], fill=(48, 50, 42, 255), width=max(1, int(0.5 * k)))
            dg.rectangle([x0 - k, y0 + h, x0 + w + k, y0 + h + 3 * k], fill=255)
    # the piers between bays: a lit edge and a shaded edge so they read as standing proud of the glass
    for b in range(11):
        x = b * bay
        d.rectangle([x - 2.2 * k, 0, x + 2.2 * k, S], fill=(84, 88, 84, 255))
        d.rectangle([x - 2.2 * k, 0, x - 1.5 * k, S], fill=(126, 130, 124, 255))
        d.rectangle([x + 1.5 * k, 0, x + 2.2 * k, S], fill=(46, 50, 48, 255))
        dg.rectangle([x - 2.2 * k, 0, x + 2.2 * k, S], fill=255)
    # weather: streaks below every ledge and sill, a film of dust on the spandrels
    for s in range(5):
        _streaks(im, rng, 130, 0, S, s * st + 69 * k, s * st + 72 * k, (6 * k, 30 * k), 0.26)
        _streaks(im, rng, 60, 0, S, s * st + 63 * k, s * st + 66 * k, (3 * k, 10 * k), 0.2)
    a = np.asarray(im, float) / 255.0
    n = (pfbm(S, 6, 4, seed + 1) - 0.5) * 0.10 + (pfbm(S, 300, 2, seed + 2) - 0.5) * 0.05
    wallm = (np.asarray(gl, float) / 255.0 > 0.5)
    a[..., :3] = np.clip(a[..., :3] * (1 + n * wallm)[..., None], 0, 1)
    a[..., 3] = np.asarray(gl.filter(ImageFilter.GaussianBlur(0.7)), float) / 255.0
    os.makedirs(os.path.join(OUT, "Facade"), exist_ok=True)
    Image.fromarray(np.round(a * 255).astype(np.uint8), "RGBA").save(os.path.join(OUT, "Facade", "t8.png"))
    src = os.path.join(BAKED, "t9.png")
    if os.path.exists(src):                                                        # the lit windows, on the same grid, kept hard-edged
        Image.open(src).convert("RGBA").resize((S, S), Image.NEAREST).save(os.path.join(OUT, "Facade", "t9.png"))
    return dict(size=S)


def build_house_facade(S=1024, seed=11):
    """t12: plaster wall with four windows (same places as the game's 128 px original), stone sills, a damp plinth"""
    rng = np.random.default_rng(seed)
    k = S / 128.0
    plaster = (pfbm(S, 5, 5, seed) - 0.5) * 0.10 + (pfbm(S, 220, 2, seed + 1) - 0.5) * 0.06
    base = np.array([216, 207, 188], float) / 255.0
    a = np.clip(base[None, None, :] * (1 + plaster)[..., None], 0, 1)
    im = Image.fromarray(np.round(np.dstack([a, np.ones((S, S))]) * 255).astype(np.uint8), "RGBA")
    gl = Image.new("L", (S, S), 255)
    d, dg = ImageDraw.Draw(im), ImageDraw.Draw(gl)
    for (x, y) in [(16, 22), (76, 22), (16, 72), (76, 72)]:
        x0, y0, w, h = x * k, y * k, 30 * k, 26 * k
        d.rectangle([x0 - 1.6 * k, y0 - 1.6 * k, x0 + w + 1.6 * k, y0 + h], fill=(196, 186, 166, 255))          # the reveal
        d.rectangle([x0 - 1.6 * k, y0 - 1.6 * k, x0 + w + 1.6 * k, y0 - 1.1 * k], fill=(120, 112, 98, 255))
        v = rng.random()
        top = np.array([92 + v * 26, 112 + v * 26, 128 + v * 26]); bot = np.array([38 + v * 10, 48 + v * 10, 56 + v * 12])
        for j in range(int(h)):
            t = j / h
            c = top * (1 - t) ** 1.5 + bot * (1 - (1 - t) ** 1.5)
            d.line([x0, y0 + j, x0 + w, y0 + j], fill=(int(c[0]), int(c[1]), int(c[2]), 255))
        if rng.random() < 0.75:                                                    # curtains drawn back to either side
            cc = (int(rng.uniform(170, 215)), int(rng.uniform(160, 200)), int(rng.uniform(140, 180)), 170)
            ov = Image.new("RGBA", (int(w), int(h)), (0, 0, 0, 0))
            od = ImageDraw.Draw(ov)
            od.polygon([(0, 0), (w * 0.3, 0), (w * 0.12, h), (0, h)], fill=cc); od.polygon([(w, 0), (w * 0.7, 0), (w * 0.88, h), (w, h)], fill=cc)
            im.alpha_composite(ov, (int(x0), int(y0)))
        ov = Image.new("RGBA", (int(w), int(h)), (0, 0, 0, 0))
        ImageDraw.Draw(ov).polygon([(w * 0.5, 0), (w * 0.8, 0), (w * 0.55, h), (w * 0.25, h)], fill=(200, 215, 225, 30))
        im.alpha_composite(ov, (int(x0), int(y0)))
        dg.rectangle([x0, y0, x0 + w, y0 + h], fill=45)
        fc = (232, 228, 216, 255)
        fw = max(2, int(0.9 * k))
        for box in ([x0, y0, x0 + w, y0 + fw], [x0, y0 + h - fw, x0 + w, y0 + h], [x0, y0, x0 + fw, y0 + h], [x0 + w - fw, y0, x0 + w, y0 + h],
                    [x0 + w / 2 - fw / 2, y0, x0 + w / 2 + fw / 2, y0 + h], [x0, y0 + h * 0.5 - fw / 2, x0 + w, y0 + h * 0.5 + fw / 2]):
            d.rectangle(box, fill=fc); dg.rectangle(box, fill=255)
        d.line([x0 + fw, y0 + fw, x0 + w - fw, y0 + fw], fill=(60, 66, 70, 255), width=max(1, int(0.3 * k)))
        d.rectangle([x0 - 2 * k, y0 + h, x0 + w + 2 * k, y0 + h + 4 * k], fill=(150, 134, 110, 255))             # the sill
        d.rectangle([x0 - 2 * k, y0 + h, x0 + w + 2 * k, y0 + h + 1.0 * k], fill=(184, 170, 146, 255))
        d.rectangle([x0 - 2 * k, y0 + h + 4 * k, x0 + w + 2 * k, y0 + h + 4.8 * k], fill=(96, 86, 70, 255))
        _streaks(im, rng, 14, x0 - 2 * k, x0 + w + 2 * k, y0 + h + 4.6 * k, y0 + h + 5.4 * k, (4 * k, 16 * k), 0.22, (70, 60, 44))
    # the plinth: darker, with damp creeping up from the ground
    arr = np.asarray(im, float) / 255.0
    yy = np.arange(S)[:, None] / S
    damp = np.clip((yy - (1 - 10 / 128.0 - 0.05 * pfbm(S, 12, 3, seed + 2))) / 0.02, 0, 1)
    arr[..., :3] *= (1 - 0.2 * damp)[..., None]
    arr[..., :3] *= (1 - 0.1 * ss(pfbm(S, 4, 4, seed + 3), 0.55, 0.85) * (np.asarray(gl, float) > 128))[..., None]
    arr[..., 3] = np.asarray(gl.filter(ImageFilter.GaussianBlur(0.7)), float) / 255.0
    os.makedirs(os.path.join(OUT, "Facade"), exist_ok=True)
    Image.fromarray(np.round(np.clip(arr, 0, 1) * 255).astype(np.uint8), "RGBA").save(os.path.join(OUT, "Facade", "t12.png"))
    return dict(size=S)


def run(ground_tiles=True, buildings=True, facades=True, res=1024, samples=40, blend=None):
    os.makedirs(OUT, exist_ok=True)
    out = {}
    if ground_tiles:
        out["ground"] = build_ground(res=res, samples=samples)
    if buildings:
        out["wall"], out["roof"], out["pave"] = build_wall(), build_roof(), build_pave()
    if facades:
        out["city"], out["house"] = build_city_facade(), build_house_facade()
    if blend:
        bpy.ops.wm.save_as_mainfile(filepath=blend)
    return out
