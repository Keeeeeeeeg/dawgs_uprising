using System;
using System.Collections.Generic;

namespace DawgsUprising.Sim
{
    /// <summary>A guard's duty: who it protects (T), the station it is heading for, and where T was last time.</summary>
    public sealed class GuardDuty
    {
        public Unit T;
        public double? Sx, Sz, Lx, Lz;
    }

    /// <summary>
    /// A unit (web G.units[i]). Field names follow the web game. Mode: idle, move, amove (attack-move) or attack.
    /// Paths are lists of [x, z] waypoints.
    /// </summary>
    public sealed class Unit : ISpatialItem
    {
        public int Id;
        public string Type;
        public UnitType Def;
        public int? F;                      // army, or null for a neutral base's buildings
        public double X, Z, Ang, Hp, MaxHp;
        public bool Alive;
        public string Mode;
        public List<double[]> Path;
        public int Pi;
        public Unit Target, Forced;
        public double Cd, AcqT;
        public int? Garrison;
        public object Group;
        public double Ax, Az;              // home point: where an idle unit stands
        public List<double[]> Cpath;       // cached sub-path while chasing (goToward)
        public int Cpi;
        public double Cgx, Cgz, RepathT, StuckT, Lx, Lz, LosT;
        public bool NeedRepath;
        public double[] Dest;
        public double HitT, Born;
        public bool Deployed;
        public double DeployT;
        public string Stance;               // null (aggressive), "hold" or "ret"
        public GuardDuty Guard;
        public double GT;
        public List<Unit> Guards;           // units guarding this one
        public Unit LastHitBy;
        public double LastHitT;
        public int? LastAttacker;
        public double? AlertT;
        public bool Healing;
        public int? ZoneMade, Home, RoverHome, GateOf;   // the base that raised it, its home base, a rover's base, the base whose gate it is
        public bool GarFlag;               // raised as a garrison
        public Plot Plot;                  // a building's plot
        public Zone ZoneOf;                // a building's base (web u.zone)

        double ISpatialItem.X => X;
        double ISpatialItem.Z => Z;
        bool ISpatialItem.Alive => Alive;
    }

    /// <summary>A shot in flight (web G.projectiles[i]): from S to E over Dur seconds, T so far (negative while a
    /// volley waits its turn). Tgt is the unit it will hit, or null for a miss.</summary>
    public sealed class Projectile
    {
        public double Sx, Sz, Sy, Ex, Ez, Ey, T, Dur, Dmg, Splash;
        public string Wpn;
        public int? F;
        public Unit Src, Tgt;
        public bool Homing, Air;
    }

    /// <summary>The numbers units run on, read once from balance.json.</summary>
    sealed class UnitRules
    {
        public readonly JObj OR, CB, TG, RET, GD, AG, MO, FL;
        public UnitRules(JObj b)
        {
            OR = b.Obj("orders"); CB = b.Obj("combat"); TG = b.Obj("targeting"); RET = b.Obj("retaliate");
            GD = b.Obj("guard"); AG = b.Obj("aggro"); MO = b.Obj("motion"); FL = b.Obj("flight");
        }
    }

    public sealed partial class Battle
    {
        public List<Unit> Units = new List<Unit>();                    // web G.units
        public readonly List<Projectile> Projectiles = new List<Projectile>();
        public int NextId = 1;
        /// <summary>Called for each SIM event, like the web on()/emit(): "spawn", "shot", "impact", "death", "raid".</summary>
        public event Action<string, object, object> Event;
        Spatial<Unit> _hash;
        UnitRules _ur;
        int _pathBudget;
        double _cleanT;
        double _raidT = -99;   // web raidT: when the last raid alarm sounded (long ago)
        const double LongAgo = -9;   // web "never" for hit and alert times

        void Emit(string ev, object a = null, object b = null) => Event?.Invoke(ev, a, b);

        void SetupUnits()
        {
            _ur = new UnitRules(Balance);
            _hash = new Spatial<Unit>(Terrain.W, Terrain.H, Terrain.X0, Terrain.Z0, Balance.Obj("engine").Num("hashBucket"));
        }

        // ---------- units (web spawnUnit, isAir, unitY, gridOf) ----------

        public static bool IsAir(Unit u) => u.Def.Air;

        /// <summary>The passability grid a unit moves on (web gridOf): water for boats; for ground units their team's grid
        /// once the walls are laid (courtyards open only to the owner's team), else the land grid.</summary>
        byte[] GridOf(Unit u) => u.Def.Naval ? Terrain.WaterGrid
            : TeamPass != null && !u.Def.Air && u.F != null ? TeamPass[Factions[u.F.Value].Team] : Terrain.LandGrid;

        /// <summary>The grid a group moves on: the first ground unit's (web landGrid).</summary>
        byte[] LandGridOf(List<Unit> us)
        {
            foreach (var q in us) if (!q.Def.Naval && !IsAir(q)) return GridOf(q);
            return Terrain.LandGrid;
        }

        /// <summary>Height a unit is shot from and at (web unitY), for units that exist so far. Boats use the ground height
        /// (the sea floor) like everything else: in the web game the line that would put them on the surface sits inside
        /// a comment, so it never runs, and the port keeps that so shots take the same time.</summary>
        public double UnitY(Unit u)
        {
            var d = u.Def;
            if (d.Air) return Math.Max(0, Terrain.HeightAt(u.X, u.Z)) + (d.Alt != 0 ? d.Alt : _ur.FL.Num("heliAlt"));
            return Terrain.HeightAt(u.X, u.Z);
        }

        public Unit SpawnUnit(string type, int? f, double x, double z)
        {
            var def = Tables.UTypes[type];
            if (def.Plane || def.Carrier)
                throw new NotSupportedException($"{type}: planes and carriers arrive with airbases and carrier battles");
            var p = def.Air ? new[] { x, z } : Pathing.SnapPassable(x, z, def.Naval ? Terrain.WaterGrid : Terrain.LandGrid);
            var M = _ur.MO;
            var u = new Unit
            {
                Id = NextId++, Type = type, Def = def, F = f, X = p[0], Z = p[1],
                Ang = Rnd.Next() * M.Num("spawnTurn"), Hp = def.Hp, MaxHp = def.Hp, Alive = true, Mode = "idle",
                Cd = Rnd.Next() * def.Rof, AcqT = Rnd.Next() * M.Num("spawnAcquire"),
                Ax = p[0], Az = p[1], Lx = p[0], Lz = p[1], HitT = LongAgo, Born = Time,
            };
            Units.Add(u);
            Emit("spawn", u);
            return u;
        }

        // ---------- orders (web setIdle, formationSlots, orderMove, orderSlots, orderAttack, setGuard, guardTick, orderStop, orderAs) ----------

        static void ReleaseUnit(Unit u) { u.Garrison = null; u.Group = null; }

        static void SetIdle(Unit u)
        {
            u.Mode = "idle";
            u.Path = null;
            u.Cpath = null;
            u.Ax = u.X;
            u.Az = u.Z;
        }

        /// <summary>n points in a square-ish block around (x, z), snapped onto the grid. Rx/Rz: the unsnapped point.</summary>
        List<double[]> FormationSlots(int n, double x, double z, double spacing, byte[] grid)
        {
            var o = new List<double[]>();
            int cols = (int)Math.Ceiling(Math.Sqrt(n));
            for (int k = 0; k < n; k++)
            {
                int r = k / cols, c = k % cols;
                double rx = x + (c - (cols - 1) / 2.0) * spacing, rz = z + (r - (Math.Ceiling((double)n / cols) - 1) / 2.0) * spacing;
                var s = Pathing.SnapPassable(rx, rz, grid);
                o.Add(new[] { s[0], s[1], rx, rz });
            }
            return o;
        }

        void StartMove(Unit u, List<double[]> path, double[] dest, bool amove)
        {
            u.Path = path;
            u.Pi = 0;
            u.Mode = amove ? "amove" : "move";
            u.Forced = null;
            u.Target = null;
            u.Cpath = null;
            u.Dest = dest;
            u.StuckT = 0;
        }

        public void OrderMove(List<Unit> units, double x, double z, bool amove)
        {
            units = units.FindAll(u => u != null && u.Alive);
            if (units.Count == 0) return;
            var OR = _ur.OR;
            double cx = 0, cz = 0;
            foreach (var u in units) { cx += u.X; cz += u.Z; }
            cx /= units.Count;
            cz /= units.Count;
            var lg = LandGridOf(units);
            var shared = FindPath(cx, cz, x, z, lg);
            bool veh = units.Exists(u => u.Def.IsVeh || u.Def.Naval);
            var slots = FormationSlots(units.Count, x, z, veh ? OR.Num("spacingVeh") : OR.Num("spacingInf"), lg);
            // assign slots by sorting both on axis perpendicular to travel
            double dx = x - cx, dz = z - cz, L = DMath.Hypot(dx, dz);
            if (L == 0) L = 1;
            double px = -dz / L, pz = dx / L;
            var us = Maps.SortStable(units, (a, b) => (a.X * px + a.Z * pz) - (b.X * px + b.Z * pz));
            var ss = Maps.SortStable(slots, (a, b) => (a[0] * px + a[1] * pz) - (b[0] * px + b[1] * pz));
            for (int i = 0; i < us.Count; i++)
            {
                var u = us[i];
                var s = ss[i];
                if (IsAir(u))
                {
                    double sp = u.Def.Armor == "ship" ? OR.Num("shipSpread") : OR.Num("airSpread");
                    var p = new[] { x + (s[2] - x) * sp, z + (s[3] - z) * sp };
                    StartMove(u, new List<double[]> { p }, p, amove);
                    continue;
                }
                List<double[]> path;
                if (u.Def.Naval)
                {
                    var w = Pathing.SnapPassable(s[0], s[1], Terrain.WaterGrid);
                    path = FindPath(u.X, u.Z, w[0], w[1], Terrain.WaterGrid) ?? new List<double[]> { w };
                    StartMove(u, path, w, amove);
                    continue;
                }
                // share the group's path only when this unit can walk straight onto it and straight off it to its slot
                // (no wall in between), otherwise it gets its own
                var gr = GridOf(u);
                if (DMath.Hypot(u.X - cx, u.Z - cz) > OR.Num("sharePath") || shared == null || !Pathing.Los(u.X, u.Z, shared[0][0], shared[0][1], gr)
                    || (shared.Count > 1 && !Pathing.Los(shared[shared.Count - 2][0], shared[shared.Count - 2][1], s[0], s[1], gr)))
                    path = FindPath(u.X, u.Z, s[0], s[1], gr);
                else
                {
                    path = new List<double[]>();
                    for (int k = 0; k < shared.Count - 1; k++) path.Add(new[] { shared[k][0], shared[k][1] });
                    path.Add(new[] { s[0], s[1] });
                }
                StartMove(u, path, new[] { s[0], s[1] }, amove);
            }
        }

        /// <summary>Move each unit to its own point (line formations drawn by the player).</summary>
        public void OrderSlots(List<Unit> units, List<double[]> slots, bool amove)
        {
            units = units.FindAll(u => u != null && u.Alive);
            if (units.Count == 0 || slots.Count == 0) return;
            int n = units.Count;
            double[] a = slots[0], b = slots[slots.Count - 1];
            double dx = b[0] - a[0], dz = b[1] - a[1], L = DMath.Hypot(dx, dz);
            if (L == 0) L = 1;
            dx /= L;
            dz /= L;
            var us = Maps.SortStable(units, (p, q) => ((p.X - a[0]) * dx + (p.Z - a[1]) * dz) - ((q.X - a[0]) * dx + (q.Z - a[1]) * dz));
            double cx = 0, cz = 0, sx = 0, sz = 0;
            foreach (var u in units) { cx += u.X; cz += u.Z; }
            cx /= n;
            cz /= n;
            foreach (var p in slots) { sx += p[0]; sz += p[1]; }
            sx /= slots.Count;
            sz /= slots.Count;
            var lg = LandGridOf(units);
            var shared = FindPath(cx, cz, sx, sz, lg);
            for (int i = 0; i < us.Count; i++)
            {
                var u = us[i];
                var s = Pathing.SnapPassable(slots[i][0], slots[i][1], lg);
                List<double[]> path;
                if (IsAir(u))
                {
                    var p = new[] { slots[i][0], slots[i][1] };
                    StartMove(u, new List<double[]> { p }, p, amove);
                    continue;
                }
                if (u.Def.Naval)
                {
                    var w = Pathing.SnapPassable(slots[i][0], slots[i][1], Terrain.WaterGrid);
                    path = FindPath(u.X, u.Z, w[0], w[1], Terrain.WaterGrid) ?? new List<double[]> { w };
                }
                else if (shared != null && DMath.Hypot(u.X - cx, u.Z - cz) < _ur.OR.Num("sharePath"))
                {
                    path = new List<double[]>();
                    for (int k = 0; k < shared.Count - 1; k++) path.Add(new[] { shared[k][0], shared[k][1] });
                    var last = path.Count > 0 ? path[path.Count - 1] : new[] { u.X, u.Z };
                    if (Pathing.Los(last[0], last[1], s[0], s[1], lg)) path.Add(new[] { s[0], s[1] });
                    else path = FindPath(u.X, u.Z, s[0], s[1], lg) ?? new List<double[]> { new[] { s[0], s[1] } };
                }
                else path = FindPath(u.X, u.Z, s[0], s[1], lg) ?? new List<double[]> { new[] { s[0], s[1] } };
                StartMove(u, path, new[] { s[0], s[1] }, amove);
            }
        }

        public static void OrderAttack(List<Unit> units, Unit target)
        {
            foreach (var u in units)
            {
                if (!u.Alive) continue;
                u.Mode = "attack";
                u.Forced = target;
                u.Target = target;
                u.Path = null;
                u.Cpath = null;
            }
        }

        // ---- guard: follow a friendly unit and protect it ----

        public static void SetGuard(List<Unit> units, Unit t)
        {
            t.Guards = (t.Guards ?? new List<Unit>()).FindAll(g => g.Alive && g.Guard != null && g.Guard.T == t && !units.Contains(g));
            foreach (var u in units)
            {
                if (!u.Alive) continue;
                u.Guard = new GuardDuty { T = t };
                u.GT = 0;
                u.Forced = null;
                t.Guards.Add(u);
            }
        }

        void GuardTick(Unit u, double dt)
        {
            var GD = _ur.GD;
            var g = u.Guard;
            var t = g.T;
            if (!t.Alive || !Allied(t.F, u.F)) { u.Guard = null; SetIdle(u); return; }
            u.GT -= dt;
            if (u.GT > 0) return;
            double every = GD.Num("every");
            u.GT = every * (GD.Num("jitterMin") + Rnd.Next() * GD.Num("jitterSpread"));
            double vx = g.Lx == null ? 0 : (t.X - g.Lx.Value) / every, vz = g.Lz == null ? 0 : (t.Z - g.Lz.Value) / every;
            g.Lx = t.X;
            g.Lz = t.Z;
            double dT = DMath.Hypot(u.X - t.X, u.Z - t.Z);
            var W = Tables.Weapons[u.Def.Wpn];
            // a threat to the one we guard: whoever just shot it, else the nearest enemy close to it that we can hurt
            Unit foe = t.LastHitBy != null && t.LastHitBy.Alive && Time - t.LastHitT < GD.Num("threatMemory") && Hostile(t.LastHitBy.F, u.F) ? t.LastHitBy : null;
            if (foe != null && (W.Vs(foe.Def.Armor) == 0 || DMath.Hypot(foe.X - t.X, foe.Z - t.Z) > GD.Num("leash"))) foe = null;
            if (foe == null)
            {
                double bd = GD.Num("radius");
                _hash.Query(t.X, t.Z, GD.Num("radius"), (o, d2) =>
                {
                    if (!Hostile(o.F, u.F) || W.Vs(o.Def.Armor) == 0) return;   // (planes on the ground and fog arrive later)
                    double d = DMath.Hypot(o.X - t.X, o.Z - t.Z);
                    if (d < bd) { bd = d; foe = o; }
                });
            }
            if (foe != null && dT < GD.Num("leash"))
            {
                if (u.Forced != foe) OrderAttack(new List<Unit> { u }, foe);
                return;
            }
            if (u.Mode == "attack") { u.Forced = null; u.Target = null; SetIdle(u); }
            // station: a ring around it, turned with its heading, a little ahead of where it's going
            var gs = (t.Guards ?? new List<Unit>()).FindAll(q => q.Alive && q.Guard != null && q.Guard.T == t);
            int ring = GD.Int("ring");
            int n = Math.Max(1, gs.Count), i = Math.Max(0, gs.IndexOf(u));
            double R = t.Def.Rad + u.Def.Rad + GD.Num("pad") + (n > ring ? u.Def.Rad * Math.Floor((double)i / ring) : 0);
            double a = t.Ang + Math.PI + (i % ring + 0.5) / Math.Min(n, ring) * Math.PI * 2;
            double sx = t.X + DMath.Cos(a) * R + vx * GD.Num("lead"), sz = t.Z + DMath.Sin(a) * R + vz * GD.Num("lead");
            double slack = GD.Num("slack");
            if (DMath.Hypot(u.X - sx, u.Z - sz) < slack && DMath.Hypot(vx, vz) < GD.Num("stillSpeed")) { if (u.Mode != "idle") SetIdle(u); return; }
            if (g.Sx != null && DMath.Hypot(sx - g.Sx.Value, sz - g.Sz.Value) < slack * GD.Num("onWayK") && u.Mode != "idle") return;   // already on the way
            g.Sx = sx;
            g.Sz = sz;
            OrderMove(new List<Unit> { u }, sx, sz, true);
        }

        public static void OrderStop(List<Unit> units)
        {
            foreach (var u in units)
                if (u.Alive) { SetIdle(u); u.Forced = null; u.Target = null; }
        }

        Unit FindUnit(int id)
        {
            foreach (var u in Units) if (u.Id == id) return u;
            return null;
        }

        /// <summary>A player's order to their units (web orderAs). kind: move, amove (a, b = x, z), attack (a = target
        /// unit), stop, slots (a = list of [x, z], b = attack-move), stance (a = "aggr", "hold" or "ret"), guard (a = unit).
        /// Units that aren't the army's own, alive and mobile are ignored. (Plane, builder and manning orders arrive later.)</summary>
        public void OrderAs(int f, string kind, IList<int> ids, object a = null, object b = null)
        {
            if ((kind == "move" || kind == "amove") && !(a is double ax && b is double bz && !double.IsNaN(ax) && !double.IsInfinity(ax) && !double.IsNaN(bz) && !double.IsInfinity(bz))) return;   // a real map point only
            var us = new List<Unit>();
            foreach (int id in ids)
            {
                var u = FindUnit(id);
                if (u != null && u.Alive && u.F == f && !u.Def.Static) us.Add(u);
            }
            if (kind == "stance")
            {
                var s = a as string;
                if (s != "aggr" && s != "hold" && s != "ret") return;
                foreach (var u in us) u.Stance = s == "aggr" ? null : s;
                return;
            }
            if (kind == "guard")
            {
                var t = a as Unit;
                if (t == null || !t.Alive || t.Def.Struct || !Allied(t.F, f)) return;
                var gs = us.FindAll(u => u != t);
                gs.ForEach(ReleaseUnit);
                SetGuard(gs, t);
                return;
            }
            foreach (var u in us) u.Guard = null;   // any other order ends guard duty
            us.ForEach(ReleaseUnit);
            if (kind == "move") OrderMove(us, (double)a, (double)b, false);
            else if (kind == "amove") OrderMove(us, (double)a, (double)b, true);
            else if (kind == "attack") OrderAttack(us, a as Unit);
            else if (kind == "stop") OrderStop(us);
            else if (kind == "slots") OrderSlots(us, (List<double[]>)a, b is bool amove && amove);
        }
    }
}
