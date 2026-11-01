using System;
using System.Collections.Generic;

namespace DawgsUprising.Sim
{
    // Movement and each unit's update, ported from the web SIM: angLerp, stepToward, goToward, followPath, leashOK,
    // retaliationTarget, updateUnit and separate.
    public sealed partial class Battle
    {
        double AngLerp(double a, double b, double t)
        {
            double wrap = _ur.MO.Num("angWrap"), d = b - a;
            while (d > Math.PI) d -= wrap;
            while (d < -Math.PI) d += wrap;
            return a + d * Math.Min(1, t);
        }

        void ClampWorld(Unit u)
        {
            double e = _ur.MO.Num("worldEdge");
            u.X = Math.Max(Terrain.X0 + e, Math.Min(Terrain.X0 + Terrain.W - e, u.X));
            u.Z = Math.Max(Terrain.Z0 + e, Math.Min(Terrain.Z0 + Terrain.H - e, u.Z));
        }

        /// <summary>One step toward (x, z), sliding along blocked cells. True once within `arrive`.</summary>
        bool StepToward(Unit u, double x, double z, double dt, double arrive)
        {
            double dx = x - u.X, dz = z - u.Z, dist = DMath.Hypot(dx, dz);
            if (dist <= arrive) return true;
            double sp = u.Def.Speed * dt, m = Math.Min(sp, dist);
            double vx = dx / dist, vz = dz / dist;
            double nx = u.X + vx * m, nz = u.Z + vz * m;
            var gr = GridOf(u);
            if (!u.Def.Air && !Terrain.Passable(u.X, u.Z, gr))
            {   // stuck inside a wall: step back out the nearest way
                var e = Pathing.SnapPassable(u.X, u.Z, gr);
                double ex = e[0] - u.X, ez = e[1] - u.Z, el = DMath.Hypot(ex, ez);
                if (el == 0) el = 1;
                u.X += ex / el * Math.Min(el, sp);
                u.Z += ez / el * Math.Min(el, sp);
                return false;
            }
            if (u.Def.Air) { u.X = nx; u.Z = nz; ClampWorld(u); }
            else if (Terrain.Passable(nx, nz, gr)) { u.X = nx; u.Z = nz; }
            else if (Terrain.Passable(u.X + vx * m, u.Z, gr)) u.X += vx * m;
            else if (Terrain.Passable(u.X, u.Z + vz * m, gr)) u.Z += vz * m;
            u.Ang = AngLerp(u.Ang, DMath.Atan2(vz, vx), dt * (u.Def.IsVeh ? _ur.MO.Num("turnVeh") : _ur.MO.Num("turnInf")));
            return DMath.Hypot(x - u.X, z - u.Z) <= arrive;
        }

        /// <summary>Chase / go toward a point using a cached sub-path, refreshed every second or so.</summary>
        bool GoToward(Unit u, double x, double z, double dt, double arrive)
        {
            var M = _ur.MO;
            u.RepathT -= dt;
            if (u.Cpath == null || u.RepathT <= 0 || DMath.Hypot(u.Cgx - x, u.Cgz - z) > M.Num("repathMove"))
            {
                if (IsAir(u) || Pathing.Los(u.X, u.Z, x, z, GridOf(u))) u.Cpath = new List<double[]> { new[] { x, z } };
                else if (_pathBudget > 0)
                {
                    _pathBudget--;
                    u.Cpath = Pathing.FindPath(u.X, u.Z, x, z, GridOf(u)) ?? new List<double[]> { new[] { x, z } };
                }
                else u.Cpath = u.Cpath ?? new List<double[]> { new[] { x, z } };
                u.Cpi = 0;
                u.Cgx = x;
                u.Cgz = z;
                u.RepathT = M.Num("repathEvery") + Rnd.Next() * M.Num("repathJitter");
            }
            var wp = u.Cpath[Math.Min(u.Cpi, u.Cpath.Count - 1)];
            bool last = u.Cpi >= u.Cpath.Count - 1;
            if (StepToward(u, wp[0], wp[1], dt, last ? arrive : M.Num("chaseWpArrive")))
            {
                if (last) return true;
                u.Cpi++;
            }
            return false;
        }

        void FollowPath(Unit u, double dt)
        {
            var M = _ur.MO;
            if (u.NeedRepath && IsAir(u) && u.Dest != null) { u.Path = new List<double[]> { u.Dest }; u.Pi = 0; u.NeedRepath = false; }
            if (u.NeedRepath && u.Dest != null && _pathBudget > 0)
            {
                _pathBudget--;
                u.Path = Pathing.FindPath(u.X, u.Z, u.Dest[0], u.Dest[1], GridOf(u));
                u.Pi = 0;
                u.NeedRepath = false;
            }
            if (u.Path == null || u.Pi >= u.Path.Count) { SetIdle(u); return; }
            var wp = u.Path[u.Pi];
            bool last = u.Pi == u.Path.Count - 1;
            // a wall (or a gate that has closed) between us and the next waypoint: find a new way round instead of sliding along it
            u.LosT -= dt;
            if (u.LosT <= 0)
            {
                u.LosT = M.Num("losEvery") + Rnd.Next() * M.Num("losJitter");
                if (!IsAir(u) && u.Dest != null && !Pathing.Los(u.X, u.Z, wp[0], wp[1], GridOf(u))) u.NeedRepath = true;
            }
            if (StepToward(u, wp[0], wp[1], dt, last ? M.Num("pathArrive") : M.Num("pathWpArrive")))
            {
                u.Pi++;
                if (u.Pi >= u.Path.Count) SetIdle(u);
            }
            // stuck detection
            u.StuckT += dt;
            if (u.StuckT > M.Num("stuckTime"))
            {
                if (DMath.Hypot(u.X - u.Lx, u.Z - u.Lz) < M.Num("stuckDist"))
                {
                    if (last) SetIdle(u);
                    else u.NeedRepath = true;
                }
                u.StuckT = 0;
                u.Lx = u.X;
                u.Lz = u.Z;
            }
        }

        bool LeashOK(Unit u, Unit t)
        {
            var RET = _ur.RET;
            if (u.Forced != null) return true;
            if (u.Mode == "amove") return true;
            bool ret = t == u.LastHitBy && Time - u.LastHitT < RET.Num("memory");   // hunting whoever just shot us: longer leash
            if (u.Garrison != null)
            {
                var z = Zones[u.Garrison.Value];
                return DMath.Hypot(t.X - z.X, t.Z - z.Z) < z.R + (ret ? RET.Num("garrisonLeash") : RET.Num("garrisonPad"));
            }
            if (u.Mode == "idle") return DMath.Hypot(t.X - u.Ax, t.Z - u.Az) < (ret ? RET.Num("leash") : RET.Num("idleLeash"));
            return false;
        }

        /// <summary>The unit that just shot u, if u can usefully go after it.</summary>
        Unit RetaliationTarget(Unit u)
        {
            var RET = _ur.RET;
            var a = u.LastHitBy;
            if (a == null || !a.Alive || Time - u.LastHitT > RET.Num("memory") || !Hostile(a.F, u.F) || a.Def.Plane) return null;
            if (Tables.Weapons[u.Def.Wpn].Vs(a.Def.Armor) < RET.Num("minEffect") || u.Def.Static) return null;
            if (a.Def.Naval && !u.Def.Naval && !IsAir(u) && !Terrain.Passable(a.X, a.Z) && u.Def.Range < RET.Num("boatReach")) return null;   // short-range troops can't reach boats offshore
            return a;
        }

        void UpdateUnit(Unit u, double dt)
        {
            var d = u.Def;
            var CB = _ur.CB;
            var M = _ur.MO;
            var W = Tables.Weapons[d.Wpn];
            // (coming out of a base, manning walls, planes and builders arrive later)
            double rng = d.Range;
            if (d.Struct) return;
            if (u.Guard != null) GuardTick(u, dt);
            u.Cd -= dt;
            u.AcqT -= dt;
            if (u.Forced != null && !u.Forced.Alive) { u.Forced = null; if (u.Mode == "attack") SetIdle(u); }
            if (u.AcqT <= 0)
            {
                u.AcqT = CB.Num("acquire") + Rnd.Next() * CB.Num("acquireJitter");
                if (u.Forced != null) u.Target = u.Forced;
                else if (u.Stance == "ret")
                {
                    var r = RetaliationTarget(u);
                    u.Target = r != null && DMath.Hypot(r.X - u.X, r.Z - u.Z) <= d.Range ? r : null;
                }
                else
                {
                    var t = NearestEnemy(u, u.Mode == "move" || u.Stance == "hold" ? rng : d.Sight);
                    // auto-retaliate: nothing in reach but we're being shot at from beyond it, so go after the shooter
                    if (u.Mode != "move" && u.Stance == null && (t == null || DMath.Hypot(t.X - u.X, t.Z - u.Z) > d.Range))
                    {
                        var r = RetaliationTarget(u);
                        if (r != null && LeashOK(u, r)) t = r;
                    }
                    u.Target = t;
                }
            }
            var tgt = u.Target;
            if (tgt != null && !tgt.Alive) tgt = u.Target = null;
            if (tgt != null && W.Vs(tgt.Def.Armor) == 0)
            {
                if (u.Forced != null) { u.Forced = null; if (u.Mode == "attack") SetIdle(u); }
                tgt = u.Target = null;
            }
            bool inRange = false, chase = false, tooClose = false;
            if (tgt != null)
            {
                double dx = tgt.X - u.X, dz = tgt.Z - u.Z, dist = DMath.Hypot(dx, dz);
                if (d.MinR != 0 && dist < d.MinR) { tooClose = true; if (u.Forced == null) u.Target = null; }
                else if (dist <= rng)
                {
                    inRange = true;
                    if (d.Deploy != 0 && u.Mode != "move")
                    {   // SPG: halt, deploy for d.Deploy seconds, then fire
                        if (!u.Deployed) { u.DeployT += dt; if (u.DeployT >= d.Deploy) { u.Deployed = true; u.DeployT = 0; } }
                    }
                    u.Ang = AngLerp(u.Ang, DMath.Atan2(dz, dx), dt * (d.IsVeh ? M.Num("aimTurnVeh") : M.Num("aimTurnInf")));
                    if (u.Cd <= 0 && (d.Deploy == 0 || u.Deployed))
                    {
                        Fire(u, tgt, dist);
                        u.Cd = d.Rof * (CB.Num("rofJitterMin") + Rnd.Next() * CB.Num("rofJitterSpread"));
                        if (d.Guns > 1)
                        {   // airship: each extra gun turret picks its own target in range
                            var extra = new List<KeyValuePair<double, Unit>>();
                            _hash.Query(u.X, u.Z, d.Range, (o, d2) =>
                            {
                                if (o != tgt && Hostile(o.F, u.F) && W.Vs(o.Def.Armor) > 0) extra.Add(new KeyValuePair<double, Unit>(d2, o));
                            });
                            extra = Maps.SortStable(extra, (a, b) => a.Key - b.Key);
                            int guns = (int)d.Guns;
                            for (int k = 0; k < Math.Min(guns - 1, extra.Count); k++) Fire(u, extra[k].Value, Math.Sqrt(extra[k].Key));
                            for (int k = extra.Count; k < guns - 1; k++) Fire(u, tgt, dist);
                        }
                    }
                }
                else if (u.Mode != "move")
                {
                    if ((u.Forced != null || u.Stance == null) && LeashOK(u, tgt)) chase = true;
                    else if (u.Forced == null) u.Target = null;
                }
            }
            if (d.Static) return;
            // artillery backs away from enemies inside its minimum range
            if (tooClose && u.Mode != "move")
            {
                double a = DMath.Atan2(u.Z - tgt.Z, u.X - tgt.X), back = CB.Num("minRangeBackoff");
                StepToward(u, u.X + DMath.Cos(a) * back, u.Z + DMath.Sin(a) * back, dt, M.Num("backoffArrive"));
                return;
            }
            if (d.Deploy != 0)
            {
                bool wantsMove = u.Mode == "move" || (!inRange && (chase || u.Mode == "amove" || u.Mode == "attack" || DMath.Hypot(u.X - u.Ax, u.Z - u.Az) > M.Num("homeDrift")));
                if (inRange && u.Mode != "move") return;   // stay planted while firing
                if (wantsMove && u.Deployed)
                {   // pack up first
                    u.DeployT += dt;
                    if (u.DeployT >= d.Deploy) { u.Deployed = false; u.DeployT = 0; }
                    return;
                }
                if (!wantsMove && !u.Deployed && u.DeployT > 0) u.DeployT = Math.Max(0, u.DeployT - dt);
            }
            if (u.Mode == "move") { FollowPath(u, dt); return; }
            if (u.Mode == "amove")
            {
                if (inRange) return;
                if (chase) { GoToward(u, tgt.X, tgt.Z, dt, d.Range * CB.Num("chaseStop")); u.NeedRepath = true; return; }
                FollowPath(u, dt);
                return;
            }
            if (u.Mode == "attack")
            {
                if (!inRange && tgt != null) GoToward(u, tgt.X, tgt.Z, dt, d.Range * CB.Num("chaseStop"));
                return;
            }
            // idle / garrison
            if (inRange) return;
            if (chase) { GoToward(u, tgt.X, tgt.Z, dt, d.Range * CB.Num("chaseStop")); return; }
            double hx = u.Ax, hz = u.Az;
            if (u.Garrison != null)
            {
                var z = Zones[u.Garrison.Value];
                if (DMath.Hypot(hx - z.X, hz - z.Z) > z.R) { hx = z.X; hz = z.Z; }
            }
            if (DMath.Hypot(u.X - hx, u.Z - hz) > M.Num("homeDrift")) GoToward(u, hx, hz, dt, M.Num("homeArrive"));
            else u.Cpath = null;
        }

        /// <summary>Units that overlap push each other apart (vehicles push infantry aside more than the other way round).</summary>
        void Separate(double dt)
        {
            var M = _ur.MO;
            double reach = M.Num("sepReach"), maxPush = M.Num("sepMaxPush"), pushK = M.Num("sepPushK"), rate = M.Num("sepRate");
            double vehInf = M.Num("sepVehVsInf"), overlap = M.Num("sepOverlap"), minD = M.Num("sepMinDist");
            foreach (var u in Units)
            {
                if (!u.Alive) continue;
                double r0 = u.Def.Rad;
                _hash.Query(u.X, u.Z, r0 + reach, (o, d2) =>
                {
                    if (o == u || o.Id < u.Id || IsAir(o) != IsAir(u) || o.Def.Naval != u.Def.Naval || u.Def.Static || o.Def.Static || u.Def.Plane || o.Def.Plane) return;
                    double rr = r0 + o.Def.Rad;
                    if (d2 >= rr * rr) return;
                    double dd = Math.Sqrt(d2);
                    if (dd == 0) dd = minD;
                    double dx = (u.X - o.X) / dd, dz = (u.Z - o.Z) / dd;
                    if (d2 < overlap) { dx = DMath.Cos(u.Id); dz = DMath.Sin(u.Id); }
                    double push = Math.Min(maxPush, (rr - dd) * pushK) * Math.Min(1, dt * rate);
                    double wu = u.Def.IsVeh && !o.Def.IsVeh ? vehInf : 1, wo = o.Def.IsVeh && !u.Def.IsVeh ? vehInf : 1;
                    bool air = IsAir(u);
                    var gr = GridOf(u);
                    double nx = u.X + dx * push * wu, nz = u.Z + dz * push * wu;
                    if (air || Terrain.Passable(nx, nz, gr)) { u.X = nx; u.Z = nz; }
                    nx = o.X - dx * push * wo;
                    nz = o.Z - dz * push * wo;
                    if (air || Terrain.Passable(nx, nz, GridOf(o))) { o.X = nx; o.Z = nz; }
                });
            }
        }

        void UnitSystems(double dt)
        {
            _pathBudget = (int)_ur.MO.Num("pathBudget");
            _hash.Rebuild(Units);
            foreach (var u in Units) if (u.Alive) UpdateUnit(u, dt);
            Separate(dt);
            UpdateProjectiles(dt);
        }
    }
}
