// Dawgs Uprising -> Unity: the browser game's own rules, exported from its BALANCE table (Data/game_data.json):
// unit stats, weapons and the armour model, zone types, capture / economy / start settings, and the map's walk grid.
// DawgsRules wraps them with the game's damage formula (makeCombat in the browser source) so both sides fight alike.
using System;
using System.Collections.Generic;
using UnityEngine;

[Serializable] public class DGUnitDef
{
    public string key, name, hot, weapon, armor;
    public float cost, mp, hp, speed, range, minR, dmg, rof, acc, splash, build, mag, reload, deploy, turret, arm, hardK, vision, minShare;
    public float rad = 0.4f, sight;      // collision radius and how far it spots enemies (the browser's def.rad / def.sight)
    public bool isVeh;
    public float[] burst;
    public bool semi, plane, air, naval, builder, isStatic, @struct, noRecruit, kneel, prone, snipe;
    public int guns;
}
[Serializable] public class DGWeapon { public string key; public float soft, hard, pen, speed; public bool homing, airburst; public string[] modCls; public float[] modVal; }
[Serializable] public class DGArmor { public float minShare; public string[] soft; public string[] cls; public float[] val; }
[Serializable] public class DGZType { public string key, name; public float income, mp; }
[Serializable] public class DGZone { public int id; public string name, type; public float x, z, r, y; public int owner; public bool port; }
[Serializable] public class DGFaction { public string name, @short, css, blurb; }
[Serializable] public class DGGrid { public int GW, GH; public float CELL, X0, Z0, W, H; }
[Serializable] public class DGCapture { public float @base, perUnit, maxUnits, rivalDrain, decay, threatPause, outnumber; }
[Serializable] public class DGEconomy { public float incomeDiv, manpowerDiv; }
[Serializable] public class DGMoney { public float player, ai; }
[Serializable] public class DGStart { public DGMoney money; public float manpower; public string[] squad; public float aiThink, aiWave, aiWaveStagger; }
[Serializable] public class DGCombat { public float acquire, acquireJitter, rofJitterMin, rofJitterSpread, vsVehicleAcc, longRange, longRangeAcc, missSpread, chaseStop, hitRadius, splashFalloff, kiteAt, minRangeBackoff, turretAim; }
// BALANCE.orders: formation spacing, the formation march and personal space
[Serializable] public class DGOrders
{
    public float spacingInf = 2.2f, spacingVeh = 3.4f, sharePath = 25f, formDist = 30f, formReady = 0.85f, formWait = 5f, fileGap = 4.6f, rowGap = 5.5f,
        rankGap = 2.6f, rearGap = 5f, lagSoft = 6f, lagHard = 15f, turnRate = 0.7f, catchUp = 1.35f, pace = 0.92f, infSpace = 1.6f, vehSpace = 0.8f;
    public int formMin = 4, armourFiles = 3;
}
// BALANCE.movement: how each class of unit speeds up, brakes, turns and reverses
[Serializable] public class DGMoveClass { public float acc = 22f, dec = 26f, turn = 11f, rev, revDist, align; }
[Serializable] public class DGMovement { public DGMoveClass inf = new DGMoveClass(), light = new DGMoveClass(), tank = new DGMoveClass(), heavy = new DGMoveClass(); }
// BALANCE.guard (escorting a unit) and BALANCE.retaliate (going after whoever shot you)
[Serializable] public class DGGuard { public float every = 1f, pad = 3f, lead = 1.5f, radius = 45f, leash = 60f, slack = 5f; }
[Serializable] public class DGRetaliate { public float leash = 65f, memory = 8f, idleLeash = 20f; }
[Serializable] public class DGTargeting { public float antiVehOnVeh, antiVehOnInf, gunOnVeh, stickiness, uselessBelow, uselessPenalty; }
[Serializable] public class DGSight { public float min, pad; }
[Serializable] public class DGData
{
    public DGGrid grid; public string pass, wpass;
    public DGUnitDef[] units; public DGWeapon[] weapons; public DGArmor armor; public DGZType[] ztypes; public DGZone[] zones; public DGFaction[] factions;
    public DGCapture capture; public DGEconomy economy; public DGStart start; public DGCombat combat; public DGTargeting targeting; public DGSight sight;
    public DGOrders orders = new DGOrders(); public DGMovement movement = new DGMovement(); public DGGuard guard = new DGGuard(); public DGRetaliate retaliate = new DGRetaliate();
}

public class DawgsRules
{
    public readonly DGData D;
    public readonly Dictionary<string, DGUnitDef> unit = new Dictionary<string, DGUnitDef>();
    public readonly Dictionary<string, DGWeapon> weapon = new Dictionary<string, DGWeapon>();
    public readonly Dictionary<string, DGZType> ztype = new Dictionary<string, DGZType>();
    readonly Dictionary<string, float> classArmor = new Dictionary<string, float>();
    readonly HashSet<string> soft = new HashSet<string>();

    public DawgsRules(string json)
    {
        D = JsonUtility.FromJson<DGData>(json);
        foreach (var u in D.units) { if (u.burst == null) u.burst = new float[0]; unit[u.key] = u; }
        foreach (var w in D.weapons) weapon[w.key] = w;
        foreach (var z in D.ztypes) ztype[z.key] = z;
        for (int i = 0; i < D.armor.cls.Length; i++) classArmor[D.armor.cls[i]] = D.armor.val[i];
        foreach (var s in D.armor.soft) soft.Add(s);
    }

    /// the browser's moveClass(): infantry; light (technicals, light tanks, anti-air); tank (medium tanks, SPGs, howitzers); heavy
    public DGMoveClass MoveClass(DGUnitDef d) =>
        d.armor == "inf" ? D.movement.inf : d.armor == "hvy" ? D.movement.heavy : d.key == "mtank" || d.key == "spg" || d.key == "how" ? D.movement.tank : D.movement.light;
    /// the browser's formRole(): where a unit marches in a formation
    public static int FormRole(DGUnitDef d) =>
        d.builder || d.weapon == "artillery" || (d.deploy > 0f && !d.kneel) || d.weapon == "flak" || d.weapon == "sam" || d.key == "qaa" ? 2 : d.armor == "inf" ? 1 : 0;   // 0 armour, 1 infantry, 2 rear

    public bool IsSoft(DGUnitDef d) => soft.Contains(d.armor);
    public float ArmorOf(DGUnitDef d) => Mathf.Max(0f, d.arm >= 0 ? d.arm : classArmor.TryGetValue(d.armor, out var a) ? a : 0f);
    public bool IsInfantry(DGUnitDef d) => d.armor == "inf";
    public bool IsGround(DGUnitDef d) => !d.plane && !d.air && !d.naval && d.armor != "air" && d.armor != "plane" && d.armor != "hair" && d.armor != "ship" && d.armor != "boat";

    static float Mod(DGWeapon W, string cls)
    {
        if (W.modCls != null) for (int i = 0; i < W.modCls.Length; i++) if (W.modCls[i] == cls) return Mathf.Max(0f, W.modVal[i]);
        return 1f;
    }

    /// the browser's COMBAT.hit: damage one round of `wpn` does to a unit of type `tgt`
    public float Hit(string wpn, float dmg, DGUnitDef tgt)
    {
        if (!weapon.TryGetValue(wpn, out var W) || tgt == null || dmg <= 0f) return 0f;
        float mod = Mod(W, tgt.armor); if (mod <= 0f) return 0f;
        float atk = dmg * Mathf.Max(0f, IsSoft(tgt) ? W.soft : W.hard); if (atk <= 0f) return 0f;
        float ea = Mathf.Max(0f, ArmorOf(tgt) - Mathf.Max(0f, W.pen));
        float share = Mathf.Clamp01(tgt.minShare >= 0 ? tgt.minShare : D.armor.minShare);
        return Mathf.Max(atk * share, atk - ea) * mod;
    }

    /// share of a weapon's nominal damage that reaches this target (target choice; 0 = cannot hurt it)
    public float Eff(DGUnitDef shooter, DGUnitDef tgt)
    {
        float d = Mathf.Max(1e-6f, shooter.dmg);
        float e = Hit(shooter.weapon, d, tgt) / d;
        if (!IsSoft(tgt)) e *= shooter.hardK;
        return e;
    }
}
