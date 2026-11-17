// Dawgs Uprising -> Unity: turns the Blender-rigged units (Assets/Dawgs/Rigged/*.fbx, made by DawgsRig/du_rig.py) into
// prefabs the game uses: Generic rig, looping Idle / Walk / Drive clips, the soldiers' at-ease moves (look around, check
// ammunition, stretch, adjust gear, take a knee), an Animator controller that switches on Speed, the shared unit
// material, and a DawgsUnitRig that aims turrets and torsos and starts the at-ease moves at run time.
//   Dawgs > Build Rigged Units
// The REF_X / REF_Y / REF_Z marker bones (one game unit along each game axis) line the import up with the rest of the
// slice whatever axis convention the FBX came in with.
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.Animations;
using UnityEngine;

public static class DawgsRigBuilder
{
    const string Src = "Assets/Dawgs/Rigged";
    const string Out = "Assets/Dawgs/Generated/Rigged";
    const float UnitScale = 0.6f;

    [MenuItem("Dawgs/Build Rigged Units")]
    public static void BuildMenu() { Debug.Log("[Dawgs] " + string.Join("\n", BuildAll().Keys)); }

    static void Dir(string p) { if (!AssetDatabase.IsValidFolder(p)) { var parent = Path.GetDirectoryName(p).Replace('\\', '/'); Dir(parent); AssetDatabase.CreateFolder(parent, Path.GetFileName(p)); } }

    /// returns replay keys (u_{type}_{army}) -> rigged prefab
    public static Dictionary<string, GameObject> BuildAll()
    {
        var res = new Dictionary<string, GameObject>();
        if (!AssetDatabase.IsValidFolder(Src)) return res;
        Dir(Out);
        var unitMat = AssetDatabase.LoadAssetAtPath<Material>("Assets/Dawgs/Generated/Materials/Unit.mat");
        foreach (var guid in AssetDatabase.FindAssets("t:Model", new[] { Src }))
        {
            string path = AssetDatabase.GUIDToAssetPath(guid);
            string unit = Path.GetFileNameWithoutExtension(path);          // e.g. rifle_0, mtank_1
            ConfigureImport(path);
            var pf = BuildPrefab(unit, path, unitMat);
            if (pf) res["u_" + unit] = pf;
        }
        AssetDatabase.SaveAssets();
        return res;
    }

    static void ConfigureImport(string path)
    {
        var mi = (ModelImporter)AssetImporter.GetAtPath(path);
        bool dirty = false;
        if (mi.animationType != ModelImporterAnimationType.Generic) { mi.animationType = ModelImporterAnimationType.Generic; dirty = true; }
        if (mi.materialImportMode != ModelImporterMaterialImportMode.None) { mi.materialImportMode = ModelImporterMaterialImportMode.None; dirty = true; }
        if (!mi.importAnimation) { mi.importAnimation = true; dirty = true; }
        if (mi.importCameras || mi.importLights) { mi.importCameras = false; mi.importLights = false; dirty = true; }
        if (dirty) mi.SaveAndReimport();
        // every take the FBX carries, under its plain name; only the cycles loop (Idle, Walk, Drive and the kneeling watch) -
        // looking around, checking ammunition, stretching, adjusting gear and getting down / up play once
        var takes = mi.defaultClipAnimations;
        if (takes.Length > 0)
        {
            foreach (var c in takes) { c.name = ClipName(c.name); c.loopTime = Loops(c.name); }
            var cur = mi.clipAnimations;
            bool same = cur.Length == takes.Length && takes.All(t => cur.Any(c => c.name == t.name && c.loopTime == t.loopTime && c.firstFrame == t.firstFrame && c.lastFrame == t.lastFrame));
            if (!same) { mi.clipAnimations = takes; mi.SaveAndReimport(); }
        }
    }

    static string ClipName(string take) { int k = take.LastIndexOf('|'); return k >= 0 ? take.Substring(k + 1) : take; }
    static bool Loops(string clip) => clip == "Idle" || clip == "Walk" || clip == "Drive" || clip == "KneelIdle";
    static readonly string[] IdleMoves = { "LookAround", "CheckAmmo", "Stretch", "AdjustGear" };

    static Transform Find(Transform t, string name)
    {
        if (t.name == name) return t;
        foreach (Transform c in t) { var r = Find(c, name); if (r) return r; }
        return null;
    }

    static GameObject BuildPrefab(string unit, string path, Material unitMat)
    {
        var model = AssetDatabase.LoadAssetAtPath<GameObject>(path);
        if (!model) return null;
        var clips = AssetDatabase.LoadAllAssetsAtPath(path).OfType<AnimationClip>().Where(c => !c.name.StartsWith("__preview__")).ToList();
        AnimationClip Clip(string n) => clips.FirstOrDefault(c => c.name == n) ?? clips.FirstOrDefault(c => c.name.EndsWith("|" + n));
        AnimationClip idle = Clip("Idle");
        AnimationClip move = Clip("Walk") ?? Clip("Drive");
        bool infantry = Clip("Walk") != null;

        // the Animator controller: Idle <-> Walk / Drive on Speed; Dir runs the Walk / Drive cycle backwards while reversing
        string cp = $"{Out}/{unit}.controller";
        AssetDatabase.DeleteAsset(cp);
        var ctrl = AnimatorController.CreateAnimatorControllerAtPath(cp);
        ctrl.AddParameter("Speed", AnimatorControllerParameterType.Float);
        ctrl.AddParameter(new AnimatorControllerParameter { name = "Dir", type = AnimatorControllerParameterType.Float, defaultFloat = 1f });
        var sm = ctrl.layers[0].stateMachine;
        var sIdle = sm.AddState("Idle"); sIdle.motion = idle;
        var sMove = sm.AddState(infantry ? "Walk" : "Drive"); sMove.motion = move ? move : idle;
        sMove.speedParameter = "Dir"; sMove.speedParameterActive = true;
        sm.defaultState = sIdle;
        var go = sIdle.AddTransition(sMove); go.hasExitTime = false; go.duration = 0.15f; go.AddCondition(AnimatorConditionMode.Greater, 0.2f, "Speed");
        var stop = sMove.AddTransition(sIdle); stop.hasExitTime = false; stop.duration = 0.2f; stop.AddCondition(AnimatorConditionMode.Less, 0.15f, "Speed");

        if (infantry)
        {   // the at-ease moves DawgsUnitRig starts (CrossFade): each plays once and hands back to Idle, or breaks into Walk
            void ToWalk(AnimatorState s, float blend)
            {
                var t = s.AddTransition(sMove); t.hasExitTime = false; t.hasFixedDuration = true; t.duration = blend;
                t.AddCondition(AnimatorConditionMode.Greater, 0.2f, "Speed");
            }
            void Then(AnimatorState s, AnimatorState next, float blend)
            {
                var t = s.AddTransition(next); t.hasExitTime = true; t.hasFixedDuration = true; t.duration = blend;
                float len = s.motion is AnimationClip c && c.length > 0.01f ? c.length / Mathf.Max(0.01f, s.speed) : 1f;
                t.exitTime = Mathf.Clamp01(1f - blend / len);
            }
            foreach (var n in IdleMoves)
            {
                var c = Clip(n); if (!c) continue;
                var s = sm.AddState(n); s.motion = c;
                ToWalk(s, 0.2f); Then(s, sIdle, 0.1f);
            }
            AnimationClip kd = Clip("KneelDown"), ki = Clip("KneelIdle"), ku = Clip("KneelUp");
            if (kd && ki && ku)
            {   // take a knee, keep watch from there, get back up (a little quicker than going down)
                var sDown = sm.AddState("KneelDown"); sDown.motion = kd;
                var sKneel = sm.AddState("KneelIdle"); sKneel.motion = ki;
                var sUp = sm.AddState("KneelUp"); sUp.motion = ku; sUp.speed = 1.4f;
                ToWalk(sDown, 0.25f); ToWalk(sKneel, 0.28f); ToWalk(sUp, 0.2f);
                Then(sDown, sKneel, 0.06f); Then(sUp, sIdle, 0.1f);
            }
        }

        // wrapper (positioned by the replay, forward = +x) -> model, turned and scaled so the game's axes come out right
        var root = new GameObject("u_" + unit);
        var inst = (GameObject)PrefabUtility.InstantiatePrefab(model);
        inst.name = "model";
        inst.transform.SetParent(root.transform, false);
        var rx = Find(inst.transform, "REF_X"); var ry = Find(inst.transform, "REF_Y"); var rz = Find(inst.transform, "REF_Z");
        if (rx && ry && rz)
        {
            Vector3 ax = root.transform.InverseTransformPoint(rx.position), ay = root.transform.InverseTransformPoint(ry.position), az = root.transform.InverseTransformPoint(rz.position);
            var A = new Matrix4x4(ax, ay, az, new Vector4(0, 0, 0, 1));
            var Dm = new Matrix4x4(new Vector4(UnitScale, 0, 0, 0), new Vector4(0, UnitScale, 0, 0), new Vector4(0, 0, -UnitScale, 0), new Vector4(0, 0, 0, 1));   // game z = Unity -z
            var T = Dm * A.inverse;   // what the model's own transform must do
            float det = T.determinant, s = Mathf.Pow(Mathf.Abs(det), 1f / 3f);
            var M = T * Matrix4x4.Scale(new Vector3(1f / s, 1f / s, (det < 0 ? -1f : 1f) / s));   // M is a pure rotation
            var Rm = M * Matrix4x4.TRS(Vector3.zero, inst.transform.localRotation, Vector3.one);
            Vector3 fwd = Rm.GetColumn(2), up = Rm.GetColumn(1);
            inst.transform.localRotation = Quaternion.LookRotation(fwd, up);
            var ls = inst.transform.localScale;
            inst.transform.localScale = new Vector3(ls.x * s, ls.y * s, ls.z * s * (det < 0 ? -1f : 1f));
        }
        var anim = inst.GetComponent<Animator>();
        if (!anim) anim = inst.AddComponent<Animator>();
        anim.runtimeAnimatorController = ctrl;
        anim.applyRootMotion = false;
        anim.cullingMode = AnimatorCullingMode.AlwaysAnimate;
        foreach (var smr in inst.GetComponentsInChildren<SkinnedMeshRenderer>())
        {
            if (unitMat) smr.sharedMaterial = unitMat;
            smr.updateWhenOffscreen = false;
            smr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.On;
        }

        var rig = root.AddComponent<DawgsUnitRig>();
        rig.animator = anim;
        rig.infantry = infantry;
        rig.aimBone = Find(inst.transform, infantry ? "torso" : "turret");
        rig.kickBone = Find(inst.transform, infantry ? "arms" : "turret");
        var muz = new List<Transform>();
        var m0 = Find(inst.transform, "muzzle"); if (m0) muz.Add(m0);
        for (int i = 0; i < 8; i++) { var m = Find(inst.transform, "muzzle" + i); if (m) muz.Add(m); }
        rig.muzzles = muz.ToArray();
        rig.maxYaw = infantry ? 75f : 180f;
        rig.holdAim = 2.5f;
        if (infantry) rig.strideLength = 0.552f;   // du_infantry.py: one Walk cycle covers 1.2 real metres x 0.46 scale
        rig.traverseSpeed = infantry ? 240f : unit.StartsWith("htank") ? 50f : unit.StartsWith("mtank") || unit.StartsWith("ltank") ? 75f : 120f;
        rig.recoilDistance = infantry ? 0.035f : unit.Contains("tank") ? 0.25f : 0.08f;
        // wheel size for timing the Drive clip: the average road wheel, from the rig's wheel bones (radius ~ distance to the ground)
        var wheels = inst.GetComponentsInChildren<Transform>().Where(t => t.name.StartsWith("wheel")).ToList();
        if (wheels.Count > 0) rig.wheelRadius = Mathf.Max(0.12f, wheels.Average(w => root.transform.InverseTransformPoint(w.position).y));

        var pf = PrefabUtility.SaveAsPrefabAsset(root, $"{Out}/u_{unit}.prefab");
        Object.DestroyImmediate(root);
        return pf;
    }
}
