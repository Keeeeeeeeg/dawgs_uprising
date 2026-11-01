using System;
using System.Collections.Generic;

namespace DawgsUprising.Sim
{
    /// <summary>A base type's wall layout (balance.json walls.hq/fortress/town/airbase), in the base's own frame:
    /// a along the gate direction (front = gate side), b across it.</summary>
    public sealed class WallDef
    {
        public sealed class Bulge { public int[] Faces; public double In, Out; }

        public string Shape;   // "oct", "poly" (N faces) or a rectangle (anything else)
        public int N;
        public double Ap, Half, Front, Back, GateHalf, Thick, Inner, GateHp, KeepDoor, KeepTop, KeepA, BarrierH, TowerH;
        public bool Light;
        public double[][] Blocks, Towers;
        public double[] Silo;
        public Bulge Fat;
    }

    // Walled bases (web createGame, "walled bases"): solid walls and one gate. The courtyard and gate lane are open to
    // the owner's team (to everyone while the base is neutral or its gate is down); each team paths on its own copy
    // of the passability grid. A walled Town has also outgrown its walls: workshops and yards outside the barrier.
    public sealed partial class Battle
    {
        public byte[][] TeamPass;      // web teamPass: one land grid per team (null until the walls are laid)
        public short[] CellZone;       // web cellZone: 1 + the walled base a cell belongs to, or 0
        public byte[] WallCell;        // web wallCell: 1 where a wall stands

        public double[] WallLocal(Zone z, double x, double zz)
        {
            double c = DMath.Cos(z.Gate), s = DMath.Sin(z.Gate), dx = x - z.X, dz = zz - z.Z;
            return new[] { dx * c + dz * s, dz * c - dx * s };
        }

        public double[] WallWorld(Zone z, double a, double b)
        {
            double c = DMath.Cos(z.Gate), s = DMath.Sin(z.Gate);
            return new[] { z.X + a * c - b * s, z.Z + a * s + b * c };
        }

        bool ZoneOpenTo(Zone z, int team) => z.Owner == null || z.Breached || Factions[z.Owner.Value].Team == team;

        void RefreshGate(Zone z)
        {
            if (TeamPass == null) return;
            foreach (int k in z.WallCells)
                for (int t = 0; t < TeamPass.Length; t++) TeamPass[t][k] = ZoneOpenTo(z, t) ? Terrain.LandGrid[k] : (byte)0;
        }

        /// <summary>Copies a land-grid cell into every team's grid (closed to teams a walled base keeps out).</summary>
        internal void SyncCell(int k)
        {
            if (TeamPass == null) return;
            int zc = CellZone[k];
            var z = zc != 0 ? Zones[zc - 1] : null;
            for (int t = 0; t < TeamPass.Length; t++) TeamPass[t][k] = z != null && !ZoneOpenTo(z, t) ? (byte)0 : Terrain.LandGrid[k];
        }

        Unit MakeGate(Zone z)
        {
            var WL = Balance.Obj("walls");
            var p = WallWorld(z, z.Wall.Front + WL.Num("gateOut"), 0);
            var u = SpawnUnit("bld", z.Owner, p[0], p[1]);
            u.X = u.Lx = u.Ax = p[0];
            u.Z = u.Lz = u.Az = p[1];
            u.Ang = z.Gate;
            u.GateOf = z.Id;
            u.MaxHp = u.Hp = DMath.RoundJs(z.Wall.GateHp * WL.Nums("gateHpLevel")[(z.Drill ?? 1) - 1]);
            z.GateU = u;
            z.Breached = false;
            RefreshGate(z);
            return u;
        }

        /// <summary>Path finding for units: a target inside a courtyard this army can't enter becomes the courtyard's gate.</summary>
        List<double[]> FindPath(double sx, double sz, double tx, double tz, byte[] grid)
        {
            if (CellZone != null && grid != Terrain.WaterGrid && grid != Terrain.LandGrid)
            {
                int tc = Terrain.CellOf(tx, tz), zc = tc >= 0 ? CellZone[tc] : 0;
                if (zc != 0 && grid[tc] == 0)
                {
                    var z = Zones[zc - 1];
                    var o = WallWorld(z, z.Wall.Front + z.Wall.Thick + Balance.Obj("walls").Num("gateApproach"), 0);
                    tx = o[0];
                    tz = o[1];
                }
            }
            return Pathing.FindPath(sx, sz, tx, tz, grid);
        }

        void SetupWalls(Plots plots)
        {
            var WL = Balance.Obj("walls");
            var types = new HashSet<string>(WL.Strs("types"));
            if (types.Contains("town")) plots.TownGrowth();
            int GW = Terrain.GW, GH = Terrain.GH;
            double X0 = Terrain.X0, Z0 = Terrain.Z0, CELL = Terrain.Cell;
            var pass = Terrain.LandGrid;
            CellZone = new short[GW * GH];
            WallCell = new byte[GW * GH];
            int nteam = 0;
            foreach (var f in Factions) nteam = Math.Max(nteam, f.Team);
            nteam++;
            double reach = WL.Num("cellReach"), edgePad = WL.Num("edgePad"), towerR = WL.Num("towerR"), turn = Data.Mapgen.Obj("plots").Num("turn");
            const double OctK = 0.7071;   // the web game's 1/sqrt(2): octagon distance in apothems
            foreach (var z in Zones)
            {
                if (!types.Contains(z.Type)) continue;
                var W = Bind.To<WallDef>(WL.Obj(z.Type));
                z.Wall = W;
                z.Walled = true;
                z.Breached = false;
                z.BreachT = -1e9;
                z.GateOpen = 0;
                z.GateHold = -1e9;
                z.GateU = null;
                z.WallCells = new List<int>();
                z.Yard = new List<int>();
                double FO = W.Fat != null ? W.Fat.Out : 0;
                double R = DMath.Hypot(W.Half + W.Thick + reach + FO, Math.Max(W.Front, -W.Back) + W.Thick + reach + FO), edge = W.Thick + edgePad;
                bool oct = W.Shape == "oct", poly = W.Shape == "poly";
                double[] PC = null, PS = null;
                if (poly)
                {
                    PC = new double[W.N];
                    PS = new double[W.N];
                    for (int q = 0; q < W.N; q++) { PC[q] = DMath.Cos((double)q / W.N * turn); PS[q] = DMath.Sin((double)q / W.N * turn); }
                }
                int j1 = Math.Min(GH - 1, (int)Math.Floor((z.Z + R - Z0) / CELL)), i1 = Math.Min(GW - 1, (int)Math.Floor((z.X + R - X0) / CELL));
                for (int j = Math.Max(0, (int)Math.Floor((z.Z - R - Z0) / CELL)); j <= j1; j++)
                    for (int i = Math.Max(0, (int)Math.Floor((z.X - R - X0) / CELL)); i <= i1; i++)
                    {
                        int k = j * GW + i;
                        var lb = WallLocal(z, X0 + (i + 0.5) * CELL, Z0 + (j + 0.5) * CELL);
                        double a = lb[0], b = lb[1], ab = Math.Abs(b);
                        double od = oct ? Math.Max(Math.Max(Math.Abs(a), ab), (Math.Abs(a) + ab) * OctK) : 0;
                        int fk = -1;
                        if (poly)
                        {   // n-gon: distance to the face it lies in front of
                            od = -1e9;
                            for (int q = 0; q < W.N; q++) { double v = a * PC[q] + b * PS[q]; if (v > od) { od = v; fk = q; } }
                        }
                        bool fat = poly && W.Fat != null && Array.IndexOf(W.Fat.Faces, fk) >= 0;
                        if (oct ? od > W.Ap + edge : poly ? od > W.Ap + edge + (fat ? W.Fat.Out : 0) : (a < W.Back - edge || a > W.Front + edge || ab > W.Half + edge)) continue;
                        bool inner = oct ? od < W.Ap - W.Inner : poly ? od < W.Ap - (fat ? W.Fat.In : W.Inner) : (a > W.Back + W.Inner && a < W.Front - W.Inner && ab < W.Half - W.Inner);
                        bool lane = ab < W.GateHalf && a > 0;
                        bool blocked = (!inner && !lane);
                        if (!blocked && inner)
                        {
                            foreach (var q in W.Blocks ?? new double[0][]) if (a > q[0] && a < q[1] && b > q[2] && b < q[3]) { blocked = true; break; }
                            if (!blocked && W.Towers != null)
                                foreach (var t in W.Towers) if (Math.Abs(a - t[0]) < towerR && Math.Abs(b - t[1]) < towerR) { blocked = true; break; }
                        }
                        if (blocked) { pass[k] = 0; WallCell[k] = 1; continue; }
                        if (CellZone[k] != 0) continue;
                        CellZone[k] = (short)(z.Id + 1);
                        z.WallCells.Add(k);
                        if (inner && !lane && pass[k] != 0) z.Yard.Add(k);
                    }
            }
            TeamPass = new byte[nteam][];
            for (int t = 0; t < nteam; t++) TeamPass[t] = (byte[])pass.Clone();
            foreach (var z in Zones)
                if (z.Walled)
                {
                    RefreshGate(z);
                    if (z.Owner != null) MakeGate(z);
                }
        }
    }
}
