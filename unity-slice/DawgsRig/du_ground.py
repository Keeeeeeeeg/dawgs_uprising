# Dawgs Uprising -> Unity: where the ground is grass, rough meadow, bare earth or sand (Data/ground_splat.raw).
# Read by Dawgs > Upgrade Ground, which paints the terrain with the four rendered surfaces from du_surfaces.py.
#   grass   the game's grass, broken up by drier, rougher meadow at a few scales
#   meadow  rough grass going over to earth: round every base, along the verges, at the top of the beach
#   dirt    bare, trodden earth: the game's own soil paths, worn tracks along the edges of every road and round every
#           building, the ground just outside each base's walls, steep banks, and small bare patches in the fields
#   sand    the beach and the sea bed, as in the game
# One byte per layer per alphamap texel (1024 x 1024, rows = Unity z), the four always adding up to 255.
# Run with plain Python 3 (needs numpy and Pillow):  python du_ground.py
import json
import os
import struct

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("DAWGS_ROOT", os.path.dirname(HERE))
K = os.path.join(ROOT, "Assets", "Dawgs", "Data")
RES = 1024
ROADS = {56, 57, 59, 87, 51}          # baked materials that are roads and paths (dirt road, gravel, footpath, asphalt, pavers)
OVERLAYS = {16, 10, 47, 88, 95, 96, 97, 98}   # zone tints, decals and markings lying on the ground: not built on it


def read_bank(path):
    f = open(path, 'rb').read(); assert f[:4] == b'DWG1'
    n = struct.unpack_from('<I', f, 4)[0]; o = 8
    for _ in range(n):
        hl = struct.unpack_from('<I', f, o)[0]; o += 4; h = json.loads(f[o:o + hl]); o += hl
        bl = struct.unpack_from('<I', f, o)[0]; o += 4; b = f[o:o + bl]; o += bl
        nv, ni = h['nv'], h['ni']
        yield h, np.frombuffer(b, np.float32, nv * 3, 0).reshape(-1, 3), np.frombuffer(b, np.uint32, ni, nv * 28)


T = json.load(open(os.path.join(K, 'terrain.json')))
X0, Z0, W, D = T['x0'], T['z0'], T['width'], T['depth']
UZ0 = -(Z0 + D)
MPP = W / RES                          # metres per texel across (D / RES down: 1290 x 480 m on 1024 x 1024)
hm = np.fromfile(os.path.join(K, 'height1025.raw'), np.uint16).reshape(1025, 1025) / 65535.0 * (T['hmax'] - T['hmin']) + T['hmin']
hgt = hm[:RES, :RES]
gy, gx = np.gradient(hm, D / 1024, W / 1024)
slope = np.hypot(gx, gy)[:RES, :RES]
sp = np.fromfile(os.path.join(K, 'splat1024.raw'), np.uint8).reshape(RES, RES, 4) / 255.0   # game: grass, sand, rock, soil


def ground_h(x, z):
    gx_ = np.clip((x - X0) / W * 1024, 0, 1023.999); gz_ = np.clip((z - UZ0) / D * 1024, 0, 1023.999)
    i, j = gx_.astype(int), gz_.astype(int); fx, fz = gx_ - i, gz_ - j
    return hm[j, i] * (1 - fx) * (1 - fz) + hm[j, i + 1] * fx * (1 - fz) + hm[j + 1, i] * (1 - fx) * fz + hm[j + 1, i + 1] * fx * fz


# ------------------------------------------------------------------ footprints, drawn at ~0.3 m
SX, SZ = 4096, 1536
road_i, built_i = Image.new('L', (SX, SZ), 0), Image.new('L', (SX, SZ), 0)
rd, bd = ImageDraw.Draw(road_i), ImageDraw.Draw(built_i)
for h, pos, idx in read_bank(os.path.join(K, 'world.bytes')):
    if h.get('proto') or h['mat'] in OVERLAYS:
        continue
    P = pos[idx.reshape(-1, 3)]
    a = 0.5 * np.abs((P[:, 1, 0] - P[:, 0, 0]) * (P[:, 2, 2] - P[:, 0, 2]) - (P[:, 2, 0] - P[:, 0, 0]) * (P[:, 1, 2] - P[:, 0, 2]))
    c = P.mean(1)
    low = (c[:, 1] - ground_h(c[:, 0], c[:, 2])) < 3.0                       # what stands on the ground, not roofs and bridges
    P = P[(a < 3000) & low]
    px = (P[:, :, 0] - X0) / W * SX
    pz = (P[:, :, 2] - UZ0) / D * SZ
    dr = rd if h['mat'] in ROADS else bd
    for t in range(len(px)):
        dr.polygon([(px[t, 0], pz[t, 0]), (px[t, 1], pz[t, 1]), (px[t, 2], pz[t, 2])], fill=255)


def grow(img, metres):
    """the footprint spread out by about this many metres, soft at the edge (0..1 at RES)"""
    px = metres / (W / SX)
    r = img.filter(ImageFilter.MaxFilter(3))
    blurred = r.filter(ImageFilter.GaussianBlur(px))
    a = np.asarray(blurred.resize((RES, RES), Image.BILINEAR), float) / 255.0
    return np.clip(a * 2.2, 0, 1)


road = np.asarray(road_i.resize((RES, RES), Image.BILINEAR), float) / 255.0
built = np.asarray(built_i.resize((RES, RES), Image.BILINEAR), float) / 255.0
road_near, road_far = grow(road_i, 1.4), grow(road_i, 4.5)
built_near, built_far = grow(built_i, 1.0), grow(built_i, 3.0)

# ------------------------------------------------------------------ noise (metres)
yy, xx = np.mgrid[0:RES, 0:RES]
mx, mz = xx / RES * W, yy / RES * D


def vnoise(scale, seed):
    r = np.random.default_rng(seed)
    g = r.random((int(D / scale) + 3, int(W / scale) + 3))
    fx, fz = mx / scale, mz / scale
    ix, iz = fx.astype(int), fz.astype(int); tx, tz = fx - ix, fz - iz
    tx, tz = tx * tx * (3 - 2 * tx), tz * tz * (3 - 2 * tz)
    a = g[iz, ix] * (1 - tx) + g[iz, ix + 1] * tx
    b = g[iz + 1, ix] * (1 - tx) + g[iz + 1, ix + 1] * tx
    return a * (1 - tz) + b * tz


def fbm(scale, seed): return vnoise(scale, seed) * 0.55 + vnoise(scale / 2.6, seed + 1) * 0.3 + vnoise(scale / 6.5, seed + 2) * 0.15
def ss(x, a, b): t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)


land = (sp[:, :, 0] + sp[:, :, 2] + sp[:, :, 3]) * ss(hgt, T['water'] - 0.1, T['water'] + 0.5)   # the island above the water line
edge_n, wear_n, patch_n, dry_n, dry2_n = fbm(9, 1), fbm(14, 2), fbm(5, 3), fbm(48, 4), fbm(16, 5)

# ------------------------------------------------------------------ bases: worn ground just outside the walls
zone_d = np.full((RES, RES), 9e9)
for z in T['zones']:
    ux, uz = z['x'], -z['z']
    d = np.hypot(mx + X0 - ux, mz + UZ0 - uz) / max(z['r'], 1.0)
    zone_d = np.minimum(zone_d, d)
zone_dirt = (1 - ss(zone_d, 1.05, 1.45 + 0.35 * edge_n)) * (1 - built)
zone_meadow = (1 - ss(zone_d, 1.4, 2.3 + 0.6 * edge_n)) * (1 - built)

# ------------------------------------------------------------------ the four weights
dirt = np.maximum.reduce([
    (sp[:, :, 3] * 1.0 + sp[:, :, 2]) / np.maximum(land, 1e-3) * (land > 0.02), # the game's soil paths and rock
    road_near * (1 - road) * ss(wear_n, 0.25, 0.6),                           # trodden verges, broken by noise
    built_near * (1 - built) * ss(wear_n, 0.35, 0.65) * 0.8,                  # round the foot of buildings and walls
    zone_dirt * ss(wear_n + 0.15, 0.3, 0.6),
    ss(slope, 0.55, 0.9),                                                     # steep banks
    ss(patch_n, 0.74, 0.8) * 0.9,                                             # small bare patches in the fields
]) * land
meadow = np.maximum.reduce([
    road_far * (1 - road) * 0.85,
    built_far * 0.5,
    zone_meadow * 0.9,
    ss(dry_n, 0.6, 0.72) * 0.7,                                               # big drier stretches
    ss(dry2_n, 0.64, 0.74) * 0.5,
    ss(sp[:, :, 1], 0.05, 0.6) * land * 1.0,                                  # the top of the beach
    ss(slope, 0.35, 0.6) * 0.8,
]) * land
under = 1 - ss(hgt, T['water'] - 0.1, T['water'] + 0.5)               # the sea bed keeps the game's sand and soil
sand = sp[:, :, 1]
grass = sp[:, :, 0]
# stack: sand where the game has it, then earth over meadow over grass on the land
dirt = np.clip(np.clip(dirt, 0, 1) * (1 - sand) + (sp[:, :, 2] + sp[:, :, 3]) * under, 0, 1)
sand = np.clip(sand + sp[:, :, 0] * under, 0, 1)
meadow = np.clip(meadow, 0, 1) * (1 - sand) * (1 - dirt)
grass = np.clip(1 - sand - dirt - meadow, 0, 1)
S = np.stack([grass, meadow, dirt, sand], -1)
S = S / np.maximum(S.sum(-1, keepdims=True), 1e-6)
q = np.floor(S * 255).astype(int)
q[..., 0] += 255 - q.sum(-1)                                                  # exact 255 per texel
q = np.clip(q, 0, 255).astype(np.uint8)
q.tofile(os.path.join(K, 'ground_splat.raw'))
cols = np.array([[80, 110, 60], [140, 130, 80], [125, 100, 70], [200, 185, 145]], float)
prev = (q.astype(float) / 255.0) @ cols
Image.fromarray(np.clip(prev[::-1], 0, 255).astype(np.uint8)).resize((1290, 480)).save(os.path.join(K, 'ground_splat_preview.png'))
land_px = land > 0.5
print('ground_splat.raw written; land share', {n: round(float(S[..., i][land_px].mean()), 3) for i, n in enumerate(['grass', 'meadow', 'dirt', 'sand'])})
