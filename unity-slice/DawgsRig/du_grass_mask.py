# Dawgs Uprising -> Unity: where the grass grows (Data/grass_cover.raw, read by Dawgs > Upgrade Environment).
# The terrain's grass (Data/ground_splat.raw from du_ground.py when it is there: full on grass, thinner and drier on
# meadow, none on bare earth or sand; otherwise the game's own grass splat), minus anything built on the ground
# (roads, the railway, buildings, fields, walls: every triangle of the baked world in Data/world.bytes), thinned on
# slopes and the beach, broken into natural patches.
# One byte of cover (0-255) per detail cell and layer: tuft, tall, dry, daisy, buttercup, clover (rows = Unity z).
# Run with plain Python 3 (needs numpy and Pillow):  python du_grass_mask.py
import json, os, struct, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("DAWGS_ROOT", os.path.dirname(HERE))
K = os.path.join(ROOT, "Assets", "Dawgs", "Data")


def read_bank(path):
    """the DWG1 mesh bank: per entry a JSON head, then positions / normals / colours / uvs / indices"""
    f = open(path, 'rb').read(); assert f[:4] == b'DWG1'
    n = struct.unpack_from('<I', f, 4)[0]; o = 8
    for _ in range(n):
        hl = struct.unpack_from('<I', f, o)[0]; o += 4; h = json.loads(f[o:o + hl]); o += hl
        bl = struct.unpack_from('<I', f, o)[0]; o += 4; b = f[o:o + bl]; o += bl
        nv, ni = h['nv'], h['ni']
        pos = np.frombuffer(b, np.float32, nv * 3, 0).reshape(-1, 3)
        idx = np.frombuffer(b, np.uint32, ni, nv * 28)
        yield h, pos, idx


T = json.load(open(os.path.join(K, 'terrain.json')))
X0, Z0, W, D = T['x0'], T['z0'], T['width'], T['depth']      # game z0; Unity z runs -(z0+D) .. -z0
UZ0 = -(Z0 + D)
RES = 1024
# 1) footprint of every baked world triangle, at ~0.3 m
SX, SZ = 4096, 1536
img = Image.new('L', (SX, SZ), 0); dr = ImageDraw.Draw(img)
for h, pos, idx in read_bank(os.path.join(K, 'world.bytes')):
    if h.get('proto'): continue
    P = pos[idx.reshape(-1, 3)]
    a = 0.5 * np.abs((P[:, 1, 0] - P[:, 0, 0]) * (P[:, 2, 2] - P[:, 0, 2]) - (P[:, 2, 0] - P[:, 0, 0]) * (P[:, 1, 2] - P[:, 0, 2]))
    P = P[a < 3000]
    px = (P[:, :, 0] - X0) / W * SX
    pz = (P[:, :, 2] - UZ0) / D * SZ
    for t in range(len(px)):
        dr.polygon([(px[t, 0], pz[t, 0]), (px[t, 1], pz[t, 1]), (px[t, 2], pz[t, 2])], fill=255)
img = img.filter(ImageFilter.MaxFilter(5))                  # ~0.6 m margin round everything built
built = np.asarray(img.resize((RES, RES), Image.BILINEAR), float) / 255.0
# 2) the grass splat and the ground shape
sp = np.fromfile(os.path.join(K, 'splat1024.raw'), np.uint8).reshape(RES, RES, 4) / 255.0
hm = np.fromfile(os.path.join(K, 'height1025.raw'), np.uint16).reshape(1025, 1025) / 65535.0 * (T['hmax'] - T['hmin']) + T['hmin']
gy, gx = np.gradient(hm, D / 1024, W / 1024)
slope = np.hypot(gx, gy)[:RES, :RES]
hgt = hm[:RES, :RES]
gs_path = os.path.join(K, 'ground_splat.raw')                # du_ground.py: grass, meadow, dirt, sand
meadow = np.zeros_like(sp[:, :, 0])
if os.path.exists(gs_path):
    gs = np.fromfile(gs_path, np.uint8).reshape(RES, RES, 4) / 255.0
    meadow = gs[:, :, 1]
    green = gs[:, :, 0] + 0.55 * meadow                            # rough meadow grows thinner; bare earth and sand none
else:
    green = sp[:, :, 0]
grass = green * np.clip(1 - (slope - 0.35) / 0.4, 0, 1) * np.clip((hgt - 0.35) / 0.5, 0, 1)
base = np.clip(grass * (1 - built) ** 2, 0, 1)
# 3) patches (value noise at a few scales, in metres)
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


def fbm(scale, seed): return vnoise(scale, seed) * 0.6 + vnoise(scale / 2.7, seed + 1) * 0.3 + vnoise(scale / 7, seed + 2) * 0.1
def ss(x, a, b): t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)


n1, n2, n3, n4, n5 = fbm(26, 1), fbm(18, 11), fbm(34, 21), fbm(9, 31), fbm(12, 41)
layers = {
    'tuft': base * (0.45 + 0.55 * ss(n1, 0.2, 0.7)),
    'tall': base * ss(n2, 0.5, 0.72) * 0.9,
    'dry': base * np.clip(ss(n3, 0.55, 0.75) * 0.7 + meadow * 0.6, 0, 1),
    'daisy': base * ss(n4, 0.66, 0.8) * 0.55,
    'buttercup': base * ss(n5, 0.66, 0.8) * 0.55,
    'clover': base * (0.25 + 0.35 * ss(1 - n1, 0.3, 0.8)),
}
out = np.stack([np.clip(np.round(v * 255), 0, 255).astype(np.uint8) for v in layers.values()], -1)
out.tofile(os.path.join(K, 'grass_cover.raw'))
print('grass_cover.raw written:', {k: round(float(v.mean()), 3) for k, v in layers.items()}, 'built', round(float(built.mean()), 3))
