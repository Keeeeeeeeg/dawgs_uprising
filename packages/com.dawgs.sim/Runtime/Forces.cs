using System;
using System.Collections.Generic;

namespace DawgsUprising.Sim
{
    // Starting forces and healing, ported from the web SIM: garrisons (garrisonCap, garrisonPool, garrisonType,
    // addGarrison, toughen), every army's squad and starting buildings (newPlot, blockArea, attachBody), airbase hangars,
    // rovers without a job (updateRover), and heal.
    public sealed partial class Battle
    {
        int _plotSeq = 1;                                                  // web plotSeq: ids of placed buildings
        readonly Dictionary<int, byte> _plotSave = new Dictionary<int, byte>();   // web plotSave: cells a building blocked
        double _healT;

        // ---------- base rosters and garrisons ----------

        public List<string> RosterOf(Zone z)
        {
            var ZT = Tables.ZTypes[z.Type];
            var r = new List<string>(ZT.Roster);
            if (z.Port) r.AddRange(ZT.Naval);
            return r;
        }

        public int GarrisonCap(Zone z)
        {
            var capK = Balance.Obj("drill").Nums("capK");
            return Math.Max(Balance.Obj("garrison").Int("minCap"), (int)DMath.RoundJs(Tables.ZTypes[z.Type].Garrison * capK[(z.Drill ?? 1) - 1]));
        }

        /// <summary>The ground units this base can garrison right now, cheapest first.</summary>
        public List<string> GarrisonPool(Zone z)
        {
            var DRL = Balance.Obj("drill");
            int L = (z.Drill ?? 1) - 1;
            var set = new List<string>(DRL.Strs("militia"));
            foreach (var p in z.Plots)
            {
                var f = p.Fac;
                if (f == null || f.State == "building") continue;
                var prod = Tables.Facilities[f.Type].Prod;
                if (prod == null) continue;
                foreach (var t in prod.Seq) if (!set.Contains(t)) set.Add(t);
            }
            var roster = RosterOf(z);
            double maxCost = DRL.Nums("maxCost")[L];
            var pool = set.FindAll(t => Tables.UTypes.TryGetValue(t, out var d) && !d.Air && !d.Naval && !d.Plane && !d.Builder && !d.NoRecruit
                && roster.Contains(t) && d.Cost <= maxCost);
            return Maps.SortStable(pool, (a, b) => Tables.UTypes[a].Cost - Tables.UTypes[b].Cost);
        }

        /// <summary>The next garrison unit: a mix that leans toward the best the base can field, topping up whatever it
        /// has least of.</summary>
        string GarrisonType(Zone z)
        {
            var GA = Balance.Obj("garrison");
            var pool = GarrisonPool(z);
            if (pool.Count == 0) return "rifle";
            var have = new Dictionary<string, int>();
            foreach (var u in Units) if (u.Alive && u.ZoneMade == z.Id) have[u.Type] = (have.TryGetValue(u.Type, out int n) ? n : 0) + 1;
            string best = pool[0];
            double bs = -1e9;
            for (int i = 0; i < pool.Count; i++)
            {
                double w = 1 + i * GA.Num("mixStep");
                double sc = w / (1 + (have.TryGetValue(pool[i], out int h) ? h : 0)) + Rnd.Next() * GA.Num("mixJitter");
                if (sc > bs) { bs = sc; best = pool[i]; }
            }
            return best;
        }

        Unit AddGarrison(Zone z, string type)
        {
            var GA = Balance.Obj("garrison");
            double a = Rnd.Next() * GA.Num("turn"), r = z.R * (GA.Num("rMin") + Rnd.Next() * GA.Num("rSpread"));
            double gx = z.X + DMath.Cos(a) * r, gz = z.Z + DMath.Sin(a) * r;
            if (z.Yard != null && z.Yard.Count > 0)
            {   // walled: somewhere in the courtyard
                var c = Pathing.CellCenter(z.Yard[(int)Math.Floor(Rnd.Next() * z.Yard.Count)]);
                gx = c[0];
                gz = c[1];
            }
            var u = SpawnUnit(type, z.Owner, gx, gz);
            u.Garrison = z.Id;
            u.ZoneMade = z.Id;
            u.GarFlag = true;
            return Toughen(u, z);
        }

        /// <summary>Garrison troops are tougher at Fortresses and HQs: that is what makes a base hard to crack.</summary>
        Unit Toughen(Unit u, Zone z)
        {
            double k = Tables.ZTypes[z.Type].GarrisonHp;
            if (k != 1) u.MaxHp = u.Hp = u.Def.Hp * k;
            return u;
        }

        // ---------- placed buildings (web footH, waterNear, newPlot, blockArea, attachBody) ----------

        double FootH(double x, double zz)
        {
            var BL = Balance.Obj("build");
            double sm = 0, probe = BL.Num("footProbe");
            int c = 0;
            for (double b = 0; b < BL.Num("footTurn"); b += BL.Num("footStep"))
            {
                sm += Terrain.HeightAt(x + DMath.Cos(b) * probe, zz + DMath.Sin(b) * probe);
                c++;
            }
            return Math.Max(BL.Num("footMin"), sm / c);
        }

        Point WaterNear(double x, double zz)
        {
            int wc = Pathing.NearestPassCell(Terrain.CellOf(x, zz), Terrain.WaterGrid);
            if (wc < 0) return null;
            var w = Pathing.CellCenter(wc);
            return DMath.Hypot(w[0] - x, w[1] - zz) < Balance.Obj("build").Num("waterReach") ? new Point { X = w[0], Z = w[1] } : null;
        }

        Plot NewPlot(Zone z, double x, double zz, double ang, string type)
        {
            var p = new Plot { I = _plotSeq++, X = x, Z = zz, Y = FootH(x, zz), Ang = ang, Kind = Tables.Facilities[type].Slot, Zone = z.Id };
            p.Water = WaterNear(x, zz);
            z.Plots.Add(p);
            return p;
        }

        /// <summary>Blocks (on) or reopens (off) the cells within r of a point, remembering what they were.</summary>
        void BlockArea(double x, double z, double r, bool on)
        {
            var t = Terrain;
            var pass = t.LandGrid;
            int j1 = (int)Math.Floor((z + r - t.Z0) / t.Cell), i1 = (int)Math.Floor((x + r - t.X0) / t.Cell);
            for (int j = (int)Math.Floor((z - r - t.Z0) / t.Cell); j <= j1; j++)
                for (int i = (int)Math.Floor((x - r - t.X0) / t.Cell); i <= i1; i++)
                {
                    if (i < 0 || j < 0 || i >= t.GW || j >= t.GH) continue;
                    int k = j * t.GW + i;
                    if (DMath.Hypot(t.X0 + (i + 0.5) * t.Cell - x, t.Z0 + (j + 0.5) * t.Cell - z) > r) continue;
                    if (on)
                    {
                        if (!_plotSave.ContainsKey(k)) _plotSave[k] = pass[k];
                        pass[k] = 0;
                    }
                    else if (_plotSave.TryGetValue(k, out byte was))
                    {
                        pass[k] = was;
                        _plotSave.Remove(k);
                    }
                    SyncCell(k);
                }
        }

        static bool IsDefence(string type) => type == "pillbox" || type == "aa" || type == "flamer";

        /// <summary>A finished building gets hit points: a structure unit standing on its plot.</summary>
        void AttachBody(Zone z, Plot p)
        {
            if (p.Fac == null || IsDefence(p.Fac.Type) || (p.Body != null && p.Body.Alive)) return;
            var BH = Balance.Obj("buildingHp");
            var u = SpawnUnit("bld", z.Owner, p.X, p.Z);
            u.X = p.X;
            u.Z = p.Z;
            u.Ang = p.Ang;
            u.Plot = p;
            u.ZoneOf = z;
            u.MaxHp = u.Hp = DMath.RoundJs((BH.Num("base") + Tables.Facilities[p.Fac.Type].Cost * BH.Num("perCost")) * (p.Fac.Level > 1 ? BH.Num("lvl2") : 1));
            p.Body = u;
        }

        Plot StartBuilding(Zone z, Plot spot, string type, double prodT)
        {
            spot.Used = true;
            var p = NewPlot(z, spot.X, spot.Z, spot.Ang, type);
            p.Fac = new FacilityState { Type = type, Level = 1, State = "ready", T = 0, Dur = 1, ProdT = prodT, ProdI = 0, Pstate = "idle" };
            BlockArea(p.X, p.Z, Balance.Obj("build").Num("plotBlock"), true);
            AttachBody(z, p);
            return p;
        }

        // ---------- starting forces (web createGame, after the walls) ----------

        void SetupForces()
        {
            var ST = Balance.Obj("start");
            if (!Opts.Bare)
            {
                foreach (var z in Zones)
                {
                    if (z.Owner == null) continue;
                    int n = GarrisonCap(z);
                    for (int i = 0; i < n; i++) AddGarrison(z, GarrisonType(z)).Home = z.Id;
                }
                // every army starts with a squad and an HQ that already has a barracks and a supply depot
                if (!CarrierMode)
                {
                    var squad = ST.Strs("squad");
                    var facs = ST.Strs("facilities");
                    int cols = ST.Int("squadCols");
                    double gap = ST.Num("squadGap");
                    for (int f = 0; f < NF; f++)
                    {
                        var hq = Zones[Map.Slots[SlotOf[f]]];
                        for (int i = 0; i < squad.Length; i++)
                        {
                            var u = SpawnUnit(squad[i], f, hq.X + ST.Num("squadX") + (i % cols) * gap, hq.Z + ST.Num("squadZ") + Math.Floor((double)i / cols) * gap);
                            if (u.Def.Builder) u.RoverHome = hq.Id;
                        }
                        for (int k = 0; k < facs.Length; k++)
                        {
                            var s = hq.Spots.Find(q => !q.Used && q.Kind == Tables.Facilities[facs[k]].Slot);
                            if (s == null) continue;
                            StartBuilding(hq, s, facs[k], ST.Num("facilityFirst") + k * ST.Num("facilityStagger"));
                        }
                    }
                }
                if (ST.Bool("airbaseHangar"))
                    foreach (var z in Zones)
                    {
                        if (z.Type != "airbase") continue;
                        var s = z.Spots.Find(q => !q.Used && q.Kind == "mil");
                        if (s == null) continue;
                        StartBuilding(z, s, "hangar", Tables.Facilities["hangar"].Time);
                    }
            }
            // ballistic missile stockpile per base
            foreach (var z in Zones) { z.Msl = 0; z.MslT = 0; }
        }

        // ---------- rovers (web updateRover; building jobs arrive with construction) ----------

        void UpdateRover(Unit u, double dt)
        {
            var M = _ur.MO;
            if (u.Mode == "move") { FollowPath(u, dt); return; }
            if (DMath.Hypot(u.X - u.Ax, u.Z - u.Az) > M.Num("homeDrift")) GoToward(u, u.Ax, u.Az, dt, M.Num("homeArrive"));
            else u.Cpath = null;
        }

        // ---------- healing (web heal): units recover inside friendly zones once out of combat briefly ----------

        void Heal(double dt)
        {
            var HL = Balance.Obj("heal");
            foreach (var u in Units)
            {
                u.Healing = false;
                if (u.Def.Plane) continue;
                if (!u.Alive || u.Hp >= u.MaxHp || Time - u.HitT < HL.Num("delay")) continue;
                if (u.Def.Naval)
                {
                    foreach (var z in Zones)
                    {
                        if (!Allied(z.Owner, u.F)) continue;
                        if (z.Plots.Exists(p => p.Fac != null && p.Fac.Type == "dockyard" && p.Fac.State == "ready" && p.Water != null
                            && DMath.Hypot(p.Water.X - u.X, p.Water.Z - u.Z) < HL.Num("portReach")))
                        {
                            u.Hp = Math.Min(u.MaxHp, u.Hp + u.MaxHp * HL.Num("naval") * dt);
                            u.Healing = true;
                            break;
                        }
                    }
                    continue;
                }
                if (u.Def.Repair != 0)
                {
                    foreach (var z in Zones)
                    {
                        if (!Allied(z.Owner, u.F) || (z.Type != "hq" && z.Type != "fortress") || DMath.Hypot(u.X - z.X, u.Z - z.Z) > z.R + HL.Num("repairReach")) continue;
                        u.Hp = Math.Min(u.MaxHp, u.Hp + u.MaxHp * u.Def.Repair * dt);
                        u.Healing = true;
                        break;
                    }
                    continue;
                }
                foreach (var z in Zones)
                {
                    bool hosp = z.Hosp;   // Field Hospital upgrade
                    if (!Allied(z.Owner, u.F) || DMath.Hypot(u.X - z.X, u.Z - z.Z) > z.R + (hosp ? HL.Num("hospitalReach") : HL.Num("reach"))) continue;
                    var ZT = Tables.ZTypes[z.Type];
                    if (u.Def.IsVeh && !ZT.Repairs && !hosp) continue;   // vehicles need a workshop
                    u.Hp = Math.Min(u.MaxHp, u.Hp + u.MaxHp * ZT.Heal * (hosp ? HL.Num("hospitalMult") : 1) * dt);
                    u.Healing = true;
                    break;
                }
            }
        }
    }
}
