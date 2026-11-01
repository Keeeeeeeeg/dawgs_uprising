using System;
using System.Collections.Generic;

namespace DawgsUprising.Sim
{
    // Combat, ported from the web SIM: nearestEnemy, fire, armorFacing, damage, updateProjectiles.
    public sealed partial class Battle
    {
        /// <summary>The enemy u most wants to shoot within r: nearest, weighted by what its weapon is good against.</summary>
        Unit NearestEnemy(Unit u, double r)
        {
            var TG = _ur.TG;
            var W = Tables.Weapons[u.Def.Wpn];
            Unit best = null;
            double bs = 1e9;
            bool antiVeh = u.Def.Wpn != "bullet";
            double minR2 = u.Def.MinR * u.Def.MinR;
            _hash.Query(u.X, u.Z, r, (o, d2) =>
            {
                double vs = W.Vs(o.Def.Armor);
                if (!Hostile(o.F, u.F) || vs == 0 || d2 < minR2) return;   // (planes on the ground arrive later)
                double s = d2;
                if (antiVeh) s *= o.Def.IsVeh ? TG.Num("antiVehOnVeh") : TG.Num("antiVehOnInf");
                else s *= o.Def.IsVeh ? TG.Num("gunOnVeh") : 1;
                if (o == u.Target) s *= TG.Num("stickiness");
                if (o.Def.Struct) s *= TG.Num("structPenalty");   // buildings only when nothing that fights back is near
                if (vs < TG.Num("uselessBelow")) s *= TG.Num("uselessPenalty");   // e.g. rifles plinking at an airship: last resort only
                if (s < bs) { bs = s; best = o; }
            });
            return best;
        }

        void Fire(Unit u, Unit t, double dist)
        {
            var d = u.Def;
            var W = Tables.Weapons[d.Wpn];
            var CB = _ur.CB;
            int volley = d.Volley != 0 ? (int)d.Volley : 1;
            for (int v = 0; v < volley; v++)
            {
                double acc = d.Acc * (t.Def.IsVeh ? CB.Num("vsVehicleAcc") : 1) * (dist > d.Range * CB.Num("longRange") ? CB.Num("longRangeAcc") : 1);   // (wall cover arrives later)
                if (W.Homing && t.Def.Evasive != 0) acc *= t.Def.Evasive;   // fast interceptors shake off missiles
                bool hit = Rnd.Next() < acc;
                double sp2 = W.Speed, alt = Math.Abs(UnitY(t) - UnitY(u));
                double T = Math.Max(CB.Num("minFlight"), DMath.Hypot(dist, alt) / sp2);
                double ex = t.X, ez = t.Z;   // (leading moving planes arrives with aircraft)
                if (!hit)
                {
                    double a = Rnd.Next() * CB.Num("scatterTurn");
                    double m = (W.Airburst ? CB.Num("flakScatter") : CB.Num("missScatter")) + Rnd.Next() * (W.Airburst ? CB.Num("flakSpread") : CB.Num("missSpread"));
                    ex += DMath.Cos(a) * m;
                    ez += DMath.Sin(a) * m;
                }
                var p = new Projectile
                {
                    Sx = u.X, Sz = u.Z, Sy = UnitY(u) + (IsAir(u) ? CB.Num("shotYAir") : u.Def.IsVeh ? CB.Num("shotYVeh") : CB.Num("shotYInf")),
                    Ex = ex, Ez = ez, Ey = IsAir(t) ? UnitY(t) : Terrain.HeightAt(ex, ez) + (t.Def.IsVeh ? CB.Num("hitYVeh") : CB.Num("hitYInf")),
                    T = -v * CB.Num("volleyStagger"), Dur = T, Wpn = d.Wpn, Dmg = d.Dmg, Splash = d.Splash, F = u.F, Src = u,
                    Tgt = hit ? t : null, Homing = W.Homing && hit, Air = IsAir(t),
                };
                Projectiles.Add(p);
                Emit("shot", u, p);
            }
            // anti-air guns opening up on a bomber: sound the raid alarm
            if (t.Def.Armor == "hair" && d.AirOnly && Time - _raidT > CB.Num("raidAlarm")) { _raidT = Time; Emit("raid", u, t); }
        }

        /// <summary>Directional armor: tanks and SPGs shrug off frontal hits and suffer from flanking shots.</summary>
        double ArmorFacing(Unit t, double? sx, double? sz)
        {
            if (t.Def.Front == 0 || sx == null) return 1;
            var CB = _ur.CB;
            double dx = sx.Value - t.X, dz = sz.Value - t.Z, L = DMath.Hypot(dx, dz);
            if (L == 0) L = 1;
            double c = (dx * DMath.Cos(t.Ang) + dz * DMath.Sin(t.Ang)) / L;
            return c > CB.Num("frontCos") ? t.Def.Front : c < CB.Num("rearCos") ? t.Def.Rear : CB.Num("sideMult");
        }

        void Damage(Unit t, double amt, int? f, double? sx, double? sz, Unit src)
        {
            if (!t.Alive) return;
            var RET = _ur.RET;
            amt *= ArmorFacing(t, sx, sz);
            t.Hp -= amt;
            t.HitT = Time;
            t.LastAttacker = f;
            if (src != null && src.Alive && !t.Def.Plane)
            {
                t.LastHitBy = src;
                t.LastHitT = Time;
                // shout for help: nearby idle friends hunt the shooter too (at most every alertEvery s per victim)
                double alertT = t.AlertT == null || t.AlertT == 0 ? LongAgo : t.AlertT.Value;   // web `t.alertT||-9`
                if (Time - alertT > RET.Num("alertEvery"))
                {
                    t.AlertT = Time;
                    double memory = RET.Num("memory") * RET.Num("alertRefresh");
                    _hash.Query(t.X, t.Z, RET.Num("alertR"), (o, d2) =>
                    {
                        if (o == t || o.F != t.F || o.Def.Plane || o.Def.Static || o.Mode == "move" || o.Forced != null) return;
                        if (o.LastHitBy == null || !o.LastHitBy.Alive || Time - o.LastHitT > memory) { o.LastHitBy = src; o.LastHitT = Time; }
                    });
                }
            }
            if (t.Garrison != null) Zones[t.Garrison.Value].ThreatT = Time;
            if (t.Hp <= 0)
            {
                t.Alive = false;
                Factions[t.F.Value].Losses++;
                if (f != null)
                {
                    Factions[f.Value].Kills++;
                    Factions[t.F.Value].Aggro[f.Value] += t.Def.IsVeh ? _ur.AG.Num("killVeh") : _ur.AG.Num("killInf");
                }
                Emit("death", t);
                // (destroyed buildings arrive with construction)
            }
        }

        void UpdateProjectiles(double dt)
        {
            var CB = _ur.CB;
            var ps = Projectiles;
            int w = 0;
            for (int i = 0; i < ps.Count; i++)
            {
                var p = ps[i];
                p.T += dt;
                if (p.Homing && p.Tgt != null && p.Tgt.Alive) { p.Ex = p.Tgt.X; p.Ez = p.Tgt.Z; p.Ey = UnitY(p.Tgt); }
                if (p.T >= p.Dur)
                {
                    var W = Tables.Weapons[p.Wpn];
                    if (p.Tgt != null && p.Tgt.Alive && DMath.Hypot(p.Tgt.X - p.Ex, p.Tgt.Z - p.Ez) <
                        (p.Air ? Math.Max(CB.Num("airHitRadius"), p.Tgt.Def.Rad * CB.Num("airHitRad")) : CB.Num("hitRadius")))
                        Damage(p.Tgt, p.Dmg * W.Vs(p.Tgt.Def.Armor), p.F, p.Sx, p.Sz, p.Src);
                    if (p.Splash > 0 && W.Airburst)
                    {   // flak: bursts damage every aircraft nearby
                        _hash.Query(p.Ex, p.Ez, p.Splash, (o, d2) =>
                        {
                            if (!Hostile(o.F, p.F) || o == p.Tgt || !IsAir(o)) return;
                            Damage(o, p.Dmg * CB.Num("flakFalloff") * W.Vs(o.Def.Armor) * (1 - Math.Sqrt(d2) / p.Splash), p.F, p.Sx, p.Sz, p.Src);
                        });
                    }
                    else if (p.Wpn == "bomb" || p.Wpn == "missile") throw new NotSupportedException("bombs and missiles arrive with aircraft and silos");
                    else if (p.Splash > 0)
                    {
                        _hash.Query(p.Ex, p.Ez, p.Splash, (o, d2) =>
                        {
                            if (!Hostile(o.F, p.F) || o == p.Tgt || IsAir(o)) return;
                            Damage(o, p.Dmg * CB.Num("splashFalloff") * W.Vs(o.Def.Armor) * (1 - Math.Sqrt(d2) / p.Splash), p.F, p.Sx, p.Sz, p.Src);
                        });
                    }
                    Emit("impact", p);
                }
                else ps[w++] = p;
            }
            ps.RemoveRange(w, ps.Count - w);
        }
    }
}
