# Dawgs Uprising -> Unity: rigs the game's soldiers and turreted vehicles in Blender and exports one FBX per unit and army.
#   soldiers: hips / thigh.L / thigh.R / torso / arms (+ muzzle marker), clips Idle and Walk
#   vehicles: hull / turret (+ muzzle markers) / one bone per road wheel, clips Idle and Drive
# Turret and torso aiming is left to Unity (DawgsUnitRig turns those bones toward the target at run time).
# REF_X / REF_Y / REF_Z marker bones sit 1 game unit along each game axis so Unity can line the import up exactly.
import bpy, bmesh, json, math, os
from mathutils import Vector, Quaternion, Matrix

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


SRC = os.path.join(_project_root(), "DawgsRig", "rigsrc.json")
OUT = os.path.join(_project_root(), "Assets", "Dawgs", "Rigged")
os.makedirs(OUT, exist_ok=True)
D = json.load(open(SRC))
US = D["unitScale"]          # every unit is drawn at 0.6 of its model
S = D["scale"]               # soldier part pivots are in model units x 0.91
FPS = 24
GAME_Z = Vector((0, -1, 0))  # the game's +z axis in Blender (game x -> x, y -> z, z -> -y)
UP = Vector((0, 0, 1))


def g2b(x, y, z):
    return Vector((x * US, -z * US, y * US))


def lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def rig_scene():
    sc = bpy.data.scenes.get("DU Rigs") or bpy.data.scenes.new("DU Rigs")
    sc.render.fps = FPS
    return sc


def clear_unit(name):
    for o in [o for o in bpy.data.objects if o.name in (name, name + "_rig")]:
        bpy.data.objects.remove(o, do_unlink=True)
    for a in [a for a in bpy.data.actions if a.name.startswith(name + "|")]:
        bpy.data.actions.remove(a)


def make_mesh(name, pos, col, coll):
    """triangle soup in game coords -> flat-shaded Blender mesh with linear vertex colours per corner"""
    n = len(pos) // 3
    verts = [g2b(pos[i * 3], pos[i * 3 + 1], pos[i * 3 + 2]) for i in range(n)]
    faces = [(i, i + 1, i + 2) for i in range(0, n - 2, 3)]   # (x, y, z) -> (x, -z, y) is a pure rotation, so the winding stays
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], faces)
    me.update()
    ca = me.color_attributes.new("Col", "FLOAT_COLOR", "CORNER")
    data = [0.0] * (len(me.loops) * 4)
    for li, lp in enumerate(me.loops):
        v = lp.vertex_index
        data[li * 4:li * 4 + 4] = [lin(col[v * 3]), lin(col[v * 3 + 1]), lin(col[v * 3 + 2]), 1.0]
    ca.data.foreach_set("color", data)
    me.color_attributes.active_color = ca
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    return ob


def make_armature(name, coll, bones):
    """bones: list of (name, head, tail, parent, deform)"""
    arm = bpy.data.armatures.new(name + "_rig")
    ao = bpy.data.objects.new(name + "_rig", arm)
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


def bind(mesh_ob, arm_ob, groups):
    """rigid skinning: groups = {bone name: [vertex indices]}"""
    for bn, idx in groups.items():
        if not idx:
            continue
        vg = mesh_ob.vertex_groups.new(name=bn)
        vg.add(idx, 1.0, "REPLACE")
    md = mesh_ob.modifiers.new("Armature", "ARMATURE")
    md.object = arm_ob
    mesh_ob.parent = arm_ob


def rot_local(pb, axis_arm, angle):
    R = pb.bone.matrix_local.to_quaternion()
    return R.inverted() @ Quaternion(axis_arm, angle) @ R


def loc_local(pb, v_arm):
    return pb.bone.matrix_local.to_3x3().inverted() @ v_arm


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


def key(pb, frame, rot=None, loc=None, euler=None):
    if rot is not None:
        pb.rotation_mode = "QUATERNION"
        pb.rotation_quaternion = rot
        pb.keyframe_insert("rotation_quaternion", frame=frame)
    if euler is not None:
        pb.rotation_mode = "XYZ"
        pb.rotation_euler = euler
        pb.keyframe_insert("rotation_euler", frame=frame)
    if loc is not None:
        pb.location = loc
        pb.keyframe_insert("location", frame=frame)


def reset_pose(ao):
    for pb in ao.pose.bones:
        pb.location = (0, 0, 0)
        pb.rotation_quaternion = (1, 0, 0, 0)
        pb.rotation_euler = (0, 0, 0)


def ref_bones():
    return [("REF_X", g2b(1, 0, 0), g2b(1, 0.1, 0), "root", False),
            ("REF_Y", g2b(0, 1, 0), g2b(0, 1.1, 0), "root", False),
            ("REF_Z", g2b(0, 0, 1), g2b(0, 0.1, 1), "root", False)]


def export(unit, mesh_ob, arm_ob):
    bpy.ops.object.select_all(action="DESELECT")
    mesh_ob.select_set(True)
    arm_ob.select_set(True)
    bpy.context.view_layer.objects.active = arm_ob
    path = os.path.join(OUT, unit + ".fbx")
    bpy.ops.export_scene.fbx(filepath=path, use_selection=True, object_types={"ARMATURE", "MESH"},
                             add_leaf_bones=False, use_armature_deform_only=False, primary_bone_axis="Y", secondary_bone_axis="X",
                             bake_anim=True, bake_anim_use_all_bones=True, bake_anim_use_nla_strips=True, bake_anim_use_all_actions=False,
                             bake_anim_force_startend_keying=True, bake_anim_step=1.0, bake_anim_simplify_factor=0.0,
                             apply_scale_options="FBX_SCALE_ALL", axis_forward="-Z", axis_up="Y", colors_type="LINEAR",
                             mesh_smooth_type="FACE", use_mesh_modifiers=False)
    return path


# ------------------------------------------------------------------ soldiers
def build_soldier(unit, src, coll):
    clear_unit(unit)
    O = D["rigo"].get(unit.split("_")[0], D["rigo"]["rifle"])
    tp = Vector(O["torso"]) * S
    ap = tp + Vector(O["arms"]) * S
    mp = ap + Vector(O["mag"]) * S
    zp = ap + Vector(O["muz"]) * S
    pos, col, part = [], [], []
    if "whole" in src:      # the sniper: one piece, split by height
        w = src["whole"]
        pos, col = list(w["pos"]), list(w["col"])
        part = ["hips"] * w["n"]
        for i in range(w["n"]):
            if pos[i * 3 + 1] > 0.72:
                part[i] = "torso"
    else:
        for pn, off in (("lower", Vector()), ("torso", tp), ("arms", ap), ("mag", mp)):
            g = src[pn]
            for i in range(g["n"]):
                pos += [g["pos"][i * 3] + off.x, g["pos"][i * 3 + 1] + off.y, g["pos"][i * 3 + 2] + off.z]
            col += g["col"]
            part += [{"lower": "hips", "torso": "torso", "arms": "arms", "mag": "arms"}[pn]] * g["n"]
    # legs, by the game's own rule (its walk shader): low, either side of the centre line, under the hips
    for i in range(len(part)):
        if part[i] != "hips":
            continue
        x, y, z = pos[i * 3], pos[i * 3 + 1], pos[i * 3 + 2]
        if y < 0.64 and 0.02 < abs(z) < 0.235 and abs(x) < 0.45:
            part[i] = "thigh.L" if z > 0 else "thigh.R"
    ob = make_mesh(unit, pos, col, coll)
    hip = 0.7
    bones = [("root", g2b(0, 0, 0), g2b(0, 0.25, 0), None, False),
             ("hips", g2b(0, hip, 0), g2b(0, hip + 0.12, 0), "root", True),
             ("thigh.L", g2b(0, hip, 0.12), g2b(0, 0.05, 0.12), "hips", True),
             ("thigh.R", g2b(0, hip, -0.12), g2b(0, 0.05, -0.12), "hips", True),
             ("torso", g2b(tp.x, tp.y, tp.z), g2b(tp.x, tp.y + 0.45, tp.z), "hips", True),
             ("arms", g2b(ap.x, ap.y, ap.z), g2b(ap.x + 0.35, ap.y, ap.z), "torso", True),
             ("muzzle", g2b(zp.x, zp.y, zp.z), g2b(zp.x + 0.1, zp.y, zp.z), "arms", False)] + ref_bones()
    ao = make_armature(unit, coll, bones)
    bind(ob, ao, {b: [i for i, p in enumerate(part) if p == b] for b in ("hips", "thigh.L", "thigh.R", "torso", "arms")})
    pb = ao.pose.bones
    # Idle: breathing, 2 s
    act = new_action(ao, unit, "Idle")
    for f in range(1, 50, 4):
        ph = (f - 1) / 48 * 2 * math.pi
        key(pb["torso"], f, loc=loc_local(pb["torso"], UP * 0.006 * math.sin(ph)), rot=rot_local(pb["torso"], GAME_Z, 0.015 * math.sin(ph)))
        key(pb["arms"], f, rot=rot_local(pb["arms"], GAME_Z, -0.02 + 0.01 * math.sin(ph)))
    push_nla(ao, act, "Idle")
    reset_pose(ao)
    # Walk: legs swing from the hips in opposite phase (as the game's walk shader), hips bob twice a stride, 1 s
    act = new_action(ao, unit, "Walk")
    amp = 0.5
    for f in range(1, 26):
        ph = (f - 1) / 24 * 2 * math.pi
        key(pb["thigh.L"], f, rot=rot_local(pb["thigh.L"], GAME_Z, amp * math.sin(ph)))
        key(pb["thigh.R"], f, rot=rot_local(pb["thigh.R"], GAME_Z, -amp * math.sin(ph)))
        key(pb["hips"], f, loc=loc_local(pb["hips"], UP * 0.025 * US * abs(math.cos(ph))))
        key(pb["torso"], f, rot=rot_local(pb["torso"], UP, 0.07 * math.sin(ph)) @ rot_local(pb["torso"], GAME_Z, -0.05))
        key(pb["arms"], f, rot=rot_local(pb["arms"], GAME_Z, -0.12 + 0.03 * math.sin(ph * 2)))
    push_nla(ao, act, "Walk")
    reset_pose(ao)
    return ob, ao


# ------------------------------------------------------------------ vehicles
def wheels_of(pos, n_hull):
    """the game's runGear rule: weld the hull into pieces; low, round pieces are road wheels"""
    bm = bmesh.new()
    lay = bm.faces.layers.int.new("tri")
    vs = [bm.verts.new((pos[i * 3], pos[i * 3 + 1], pos[i * 3 + 2])) for i in range(n_hull)]
    for t in range(n_hull // 3):
        try:
            fc = bm.faces.new((vs[t * 3], vs[t * 3 + 1], vs[t * 3 + 2]))
            fc[lay] = t
        except ValueError:
            pass
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.002)
    bm.faces.index_update()
    bm.faces.ensure_lookup_table()
    seen, pieces = set(), []
    for f0 in bm.faces:
        if f0.index in seen:
            continue
        stack, comp = [f0], []
        seen.add(f0.index)
        while stack:
            f = stack.pop()
            comp.append(f)
            for e in f.edges:
                for f2 in e.link_faces:
                    if f2.index not in seen:
                        seen.add(f2.index)
                        stack.append(f2)
        pts = [v.co for f in comp for v in f.verts]
        lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
        hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
        pieces.append((lo, hi, [f[lay] for f in comp]))
    bm.free()
    gy0 = min(pos[i * 3 + 1] for i in range(n_hull))
    gy1 = max(pos[i * 3 + 1] for i in range(n_hull))
    low = gy0 + (gy1 - gy0) * 0.45
    out = []
    for lo, hi, tris in pieces:
        d = hi - lo
        cy = (lo.y + hi.y) / 2
        mx = max(d.x, d.y)
        if cy > low or mx < 0.2:
            continue
        if abs(d.x - d.y) < 0.22 * mx and d.z < 1.3 * mx:
            out.append(((lo + hi) / 2, mx / 2, d.z, tris))
    return out


def build_vehicle(unit, src, coll):
    clear_unit(unit)
    pos, col, n = src["pos"], src["col"], src["n"]
    tu = src["turret"]
    frm = tu["from"]
    part = ["hull"] * frm + ["turret"] * (n - frm)
    wheels = wheels_of(pos, frm)
    for wi, (c, r, w, tris) in enumerate(wheels):
        for t in tris:
            for k in range(3):
                part[t * 3 + k] = "wheel%02d" % wi
    ob = make_mesh(unit, pos, col, coll)
    ty = min(pos[i * 3 + 1] for i in range(frm, n)) if n > frm else 1.0
    pv = (tu["px"], ty, tu["pz"])
    hy = sum(pos[i * 3 + 1] for i in range(frm)) / max(1, frm)
    bones = [("root", g2b(0, 0, 0), g2b(0, 0.4, 0), None, False),
             ("hull", g2b(0, hy, 0), g2b(0.6, hy, 0), "root", True),
             ("turret", g2b(*pv), g2b(pv[0], pv[1] + 0.6, pv[2]), "hull", True)]
    for mi, m in enumerate(tu["mz"]):
        bones.append(("muzzle%d" % mi, g2b(*m), g2b(m[0] + 0.2, m[1], m[2]), "turret", False))
    for wi, (c, r, w, tris) in enumerate(wheels):
        bones.append(("wheel%02d" % wi, g2b(c.x, c.y, c.z), g2b(c.x, c.y, c.z + max(0.15, w)), "hull", True))   # bone along the axle
    bones += ref_bones()
    ao = make_armature(unit, coll, bones)
    names = ["hull", "turret"] + ["wheel%02d" % wi for wi in range(len(wheels))]
    bind(ob, ao, {b: [i for i, p in enumerate(part) if p == b] for b in names})
    pb = ao.pose.bones
    # Idle: the engine ticking over, 1 s
    act = new_action(ao, unit, "Idle")
    for f in range(1, 26):
        ph = (f - 1) / 24 * 2 * math.pi
        key(pb["hull"], f, loc=loc_local(pb["hull"], UP * 0.006 * US * math.sin(ph * 6)))
    push_nla(ao, act, "Idle")
    reset_pose(ao)
    # Drive: every road wheel rolls one turn a second, the hull pitches and bobs over the ground
    act = new_action(ao, unit, "Drive")
    for f in range(1, 26):
        ph = (f - 1) / 24 * 2 * math.pi
        key(pb["hull"], f, loc=loc_local(pb["hull"], UP * 0.02 * US * math.sin(ph * 4)), rot=rot_local(pb["hull"], GAME_Z, 0.008 * math.sin(ph * 2)))
        for wi in range(len(wheels)):
            key(pb["wheel%02d" % wi], f, euler=(0.0, -2 * math.pi * (f - 1) / 24, 0.0))   # local Y = the axle (game +z); rolling forward turns it clockwise
    push_nla(ao, act, "Drive")
    reset_pose(ao)
    return ob, ao, len(wheels)


def run(units=None):
    sc = rig_scene()
    if bpy.context.window:
        bpy.context.window.scene = sc
    coll = sc.collection
    done = []
    names = units or (list(D["inf"].keys()) + list(D["veh"].keys()))
    for i, u in enumerate(names):
        if u in D["inf"]:
            ob, ao = build_soldier(u, D["inf"][u], coll)
            extra = ""
        else:
            ob, ao, nw = build_vehicle(u, D["veh"][u], coll)
            extra = "%d wheels" % nw
        path = export(u, ob, ao)
        col_i, row = i % 6, i // 6
        ao.location = (col_i * 6.0, -row * 8.0, 0)
        done.append([u, len(ob.data.polygons), len(ao.data.bones), extra, os.path.basename(path)])
    return done
