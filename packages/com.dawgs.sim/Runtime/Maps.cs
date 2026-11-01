using System;
using System.Collections.Generic;

namespace DawgsUprising.Sim
{
    public sealed class Blob { public double X, Z, Rx, Rz; }
    public sealed class Carve { public double X, Z, R; }

    /// <summary>A causeway (neck) or a ridge: a line from A to B, W wide (ridges also H high).</summary>
    public sealed class Segment
    {
        public double[] A, B;
        public double W, H;
    }

    /// <summary>A base site on a map, stored as a row ["name", "type", x, z, port] like the web game.</summary>
    public sealed class MapZone : IJsonRow
    {
        public string Name, Type;
        public double X, Z;
        public bool? Port;   // null: not decided yet (Chaos Isles before convertMap)

        public void ReadRow(List<object> row)
        {
            Name = (string)row[0];
            Type = (string)row[1];
            X = (double)row[2];
            Z = (double)row[3];
            Port = row.Count > 4 ? (bool?)(bool)row[4] : null;
        }

        /// <summary>The row as the web game has it (4 items, or 5 with the port flag).</summary>
        public object[] Row() => Port == null ? new object[] { Name, Type, X, Z } : new object[] { Name, Type, X, Z, Port.Value };

        public MapZone Copy() => (MapZone)MemberwiseClone();
    }

    /// <summary>
    /// A map, with the web game's fields: W, H, ns (noise scale), blobs (islands), necks (causeways), carves
    /// (lakes), ridges, zones (base sites), slots (zone index of each HQ start), mix, palette...
    /// </summary>
    public sealed class MapDef
    {
        public string Id, Name, Desc, Palette;
        public double W, H;
        public double[] Ns;
        public int MaxPlayers;
        public List<Blob> Blobs = new List<Blob>();
        public List<Segment> Necks = new List<Segment>();
        public List<Carve> Carves = new List<Carve>();
        public List<Segment> Ridges = new List<Segment>();
        public List<MapZone> Zones = new List<MapZone>();
        public List<int> Slots = new List<int>();
        public Dictionary<string, int> Mix;
        public bool Balanced, Hidden, FixedTypes, Generated, Large, NoWater, Carrier, Chaos, Scaled;
        /// <summary>The zones after start slots are assigned (unused HQ slots become Fortresses).</summary>
        public List<MapZone> ZonesFinal;

        /// <summary>A copy the battle can change (its own zone lists; the shapes are only read).</summary>
        public MapDef Copy()
        {
            var m = (MapDef)MemberwiseClone();
            m.Zones = Zones.ConvertAll(z => z.Copy());
            m.Slots = new List<int>(Slots);
            return m;
        }
    }

    /// <summary>Start slots for a battle (web createGame, "assign HQ start slots").</summary>
    public sealed class BattleZones
    {
        public int[] SlotOf;
        public List<MapZone> ZonesFinal;
        public int NF;
        public int[] TeamOf;
        public string Mode;
        public List<HumanCfg> Humans;
        public List<AiCfg> Ai;
    }

    /// <summary>
    /// Map logic. Fixed maps come from data/maps.json (exported from the web game by tools/export_maps.js).
    /// Chaos Isles is rolled for every battle here, ported from the web SIM's genMap (chaos style), convertMap,
    /// scaleMap and makeChaosMap. Numbers come from mapgen.json and balance.json.
    /// </summary>
    public static class Maps
    {
        /// <summary>Reads maps.json ({"maps": {id: map}}), keeping the file's order.</summary>
        public static Dictionary<string, MapDef> Load(JObj file)
        {
            var maps = file.Obj("maps");
            var r = new Dictionary<string, MapDef>();
            foreach (var id in maps.Keys) r[id] = Bind.To<MapDef>(maps.Obj(id));
            return r;
        }

        // ---------- geometry helpers (web segDist, smooth, landRaw) ----------

        public static double SegDist(double px, double pz, double ax, double az, double bx, double bz)
        {
            double dx = bx - ax, dz = bz - az;
            double t = ((px - ax) * dx + (pz - az) * dz) / (dx * dx + dz * dz);
            if (double.IsNaN(t)) return double.NaN; // JS Math.max/min pass NaN through
            t = Math.Max(0.0, Math.Min(1.0, t));
            return DMath.Hypot(px - (ax + dx * t), pz - (az + dz * t));
        }

        public static double Smooth(double e0, double e1, double x)
        {
            double t = Math.Max(0.0, Math.Min(1.0, (x - e0) / (e1 - e0)));
            return t * t * (3.0 - 2.0 * t);
        }

        /// <summary>The island shape without noise (web landRaw, same rules as the terrain builder's land()).</summary>
        public static double LandRaw(MapDef m, double x, double z, JObj cv)
        {
            double L = -2.0;
            foreach (var b in m.Blobs)
            {
                double v = 1.0 - DMath.Hypot((x - b.X) / b.Rx, (z - b.Z) / b.Rz);
                if (v > L) L = v;
            }
            foreach (var c in m.Carves)
            {
                double d = DMath.Hypot(x - c.X, z - c.Z);
                if (d < c.R) L = Math.Min(L, -(1.0 - d / c.R) * cv.Num("carveDepth") - cv.Num("carveFloor"));
            }
            foreach (var n in m.Necks)
            {
                double nv = 1.0 - SegDist(x, z, n.A[0], n.A[1], n.B[0], n.B[1]) / n.W;
                if (nv * cv.Num("neckLand") > L) L = nv * cv.Num("neckLand");
            }
            double W = m.W, H = m.H;
            double ex = Math.Min(Math.Min(x + W / 2.0, W / 2.0 - x), Math.Min(z + H / 2.0, H / 2.0 - z));
            L -= Math.Max(0.0, (cv.Num("edgeFade") - ex) / cv.Num("edgeFade"));
            return L;
        }

        /// <summary>Metres past the ring to deep water, or +infinity (web coastDist). reach &lt;= 0 means the default.</summary>
        public static double CoastDist(MapDef m, double x, double z, double r, double reach, JObj mx, JObj cv)
        {
            if (m.NoWater) return double.PositiveInfinity;
            double top = reach > 0.0 ? reach : mx.Num("portReachMax");
            int rays = cv.Int("coastRays");
            for (double d = mx.Num("portReachMin"); d <= top; d += cv.Num("coastStep"))
                for (int a = 0; a < rays; a++)
                {
                    double t = (double)a / cv.Num("coastRays") * cv.Num("turn");
                    if (LandRaw(m, x + DMath.Cos(t) * (r + d), z + DMath.Sin(t) * (r + d), cv) < mx.Num("portWater")) return d;
                }
            return double.PositiveInfinity;
        }

        /// <summary>Counts of each base type (web baseMix).</summary>
        public static Dictionary<string, int> BaseMix(List<MapZone> zones)
        {
            var c = new Dictionary<string, int> { ["hq"] = 0, ["fortress"] = 0, ["town"] = 0, ["airbase"] = 0, ["port"] = 0 };
            foreach (var z in zones)
            {
                c.TryGetValue(z.Type, out int n);
                c[z.Type] = n + 1;
                if (z.Port == true && (z.Type == "hq" || z.Type == "fortress" || z.Type == "town")) c["port"]++;
            }
            return c;
        }

        /// <summary>Stable sort by a JS-style comparator (negative = a first), like V8's. List.Sort isn't stable.</summary>
        public static List<T> SortStable<T>(List<T> a, Func<T, T, double> cmp)
        {
            if (a.Count < 2) return new List<T>(a);
            int mid = a.Count / 2;
            var l = SortStable(a.GetRange(0, mid), cmp);
            var r = SortStable(a.GetRange(mid, a.Count - mid), cmp);
            var o = new List<T>(a.Count);
            int i = 0, j = 0;
            while (i < l.Count && j < r.Count)
            {
                if (cmp(r[j], l[i]) < 0) o.Add(r[j++]);
                else o.Add(l[i++]);
            }
            while (i < l.Count) o.Add(l[i++]);
            while (j < r.Count) o.Add(r[j++]);
            return o;
        }

        // ---------- Chaos Isles (web makeChaosMap) ----------

        /// <summary>Rolls the Chaos Isles map for a battle seed. Same seed = same map as the web game.</summary>
        public static MapDef MakeChaos(double seedIn, JObj gen, JObj balance)
        {
            var C = gen.Obj("chaos");
            long seed = (long)Math.Floor(Math.Abs(seedIn));
            if (seed == 0) seed = 1;
            seed = seed % (long)C.Num("seedMod") + 1;
            int tries = 0;
            while (true)
            {
                var m = GenChaos(seed, gen);
                if (m.Zones.Count < C.Num("minZones") && tries < C.Num("maxRetries"))
                {
                    tries++;
                    seed = seed % (long)C.Num("retryMod") + (long)C.Num("retryStep");
                    continue;
                }
                ConvertMap(m, gen, balance);
                ScaleMap(m, gen);
                return m;
            }
        }

        sealed class Isle { public double X, Z, Rx, Rz; }

        static double[] Pair(JObj o, string k) => o.Nums(k);

        static MapDef GenChaos(long seed, JObj gen)
        {
            var C = gen.Obj("chaos");
            var rng = new Rng(seed);
            double R(double a, double b) => a + rng.Next() * (b - a);
            double W = C.Num("W"), H = C.Num("H");
            double hw = W / 2.0, hh = H / 2.0;
            var m = new MapDef();
            void Neck(Blob a, Blob b) => m.Necks.Add(new Segment { A = new[] { a.X, a.Z }, B = new[] { b.X, b.Z }, W = gen.Num("neckWidth") });
            // islands, spaced apart
            double[] islands = Pair(C, "islands"), irx = Pair(C, "islandRx"), irz = Pair(C, "islandRz"), lobeScale = Pair(C, "lobeScale");
            int n = (int)DMath.RoundJs(R(islands[0], islands[1]));
            var isl = new List<Blob>();
            int k = 0;
            while (k < C.Num("islandTries") && isl.Count < n)
            {
                k++;
                var c = new Blob();
                c.X = R(-hw + C.Num("edgeX"), hw - C.Num("edgeX"));
                c.Z = R(-hh + C.Num("edgeZ"), hh - C.Num("edgeZ"));
                c.Rx = R(irx[0], irx[1]);
                c.Rz = R(irz[0], irz[1]);
                bool clash = false;
                foreach (var q in isl)
                    if (DMath.Hypot(q.X - c.X, q.Z - c.Z) < (Math.Max(q.Rx, q.Rz) + Math.Max(c.Rx, c.Rz)) * C.Num("islandGap")) { clash = true; break; }
                if (!clash) isl.Add(c);
            }
            foreach (var c in isl)
            {
                m.Blobs.Add(c);
                if (rng.Next() < C.Num("lobeChance"))
                {
                    var lobe = new Blob();
                    lobe.X = c.X + R(-C.Num("lobeDx"), C.Num("lobeDx"));
                    lobe.Z = c.Z + R(-C.Num("lobeDz"), C.Num("lobeDz"));
                    lobe.Rx = c.Rx * R(lobeScale[0], lobeScale[1]);
                    lobe.Rz = c.Rz * R(lobeScale[0], lobeScale[1]);
                    m.Blobs.Add(lobe);
                }
            }
            // join each island to its nearest already-joined one
            var done = new List<Blob> { isl[0] };
            for (int ci = 1; ci < isl.Count; ci++)
            {
                var c = isl[ci];
                var b = done[0];
                double bd = 1e9;
                foreach (var d in done)
                {
                    double q = DMath.Hypot(d.X - c.X, d.Z - c.Z);
                    if (q < bd) { bd = q; b = d; }
                }
                Neck(c, b);
                done.Add(c);
            }
            // a few extra causeways
            double[] jit = Pair(C, "extraNeckJitter");
            k = 0;
            while (k < DMath.RoundJs(n / C.Num("extraNecksDiv")))
            {
                k++;
                var a = isl[(int)Math.Floor(rng.Next() * isl.Count)];
                Blob b = null;
                double bd = 1e9;
                foreach (var c in isl)
                {
                    if (ReferenceEquals(c, a)) continue;
                    double q = DMath.Hypot(a.X - c.X, a.Z - c.Z) * R(jit[0], jit[1]);
                    if (q < bd) { bd = q; b = c; }
                }
                if (b != null) Neck(a, b);
            }
            // ridges and lakes. The web loops re-roll their limit on every pass, so do the same.
            double[] ridges = Pair(C, "ridges"), rlen = Pair(C, "ridgeLen"), rw = Pair(C, "ridgeW"), rh = Pair(C, "ridgeH");
            k = 0;
            while (k < DMath.RoundJs(R(ridges[0], ridges[1])))
            {
                k++;
                var c = isl[(int)Math.Floor(rng.Next() * isl.Count)];
                double sp = C.Num("ridgeSpread");
                double x = c.X + R(-c.Rx * sp, c.Rx * sp);
                double z = c.Z + R(-c.Rz * sp, c.Rz * sp);
                double ang = R(0.0, C.Num("ridgeTurn"));
                double L = R(rlen[0], rlen[1]);
                var rg = new Segment { A = new[] { x, z }, B = new[] { x + DMath.Cos(ang) * L, z + DMath.Sin(ang) * L } };
                rg.W = R(rw[0], rw[1]);
                rg.H = R(rh[0], rh[1]);
                m.Ridges.Add(rg);
            }
            double[] lakes = Pair(C, "lakes"), lakeR = Pair(C, "lakeR");
            k = 0;
            while (k < DMath.RoundJs(R(lakes[0], lakes[1])))
            {
                k++;
                var c = isl[(int)Math.Floor(rng.Next() * isl.Count)];
                double sp = C.Num("lakeSpread");
                var lake = new Carve();
                lake.X = c.X + R(-c.Rx * sp, c.Rx * sp);
                lake.Z = c.Z + R(-c.Rz * sp, c.Rz * sp);
                lake.R = R(lakeR[0], lakeR[1]);
                m.Carves.Add(lake);
            }
            var palettes = C.Strs("palettes");
            return PlaceSites(m, rng, R, W, H, (int)C.Num("zones"), C.Num("spacing"), (int)C.Num("maxPlayers"), palettes[seed % palettes.Length], gen);
        }

        sealed class Pt { public double X, Z; }

        /// <summary>The second half of the web genMap: base sites, HQ start slots, site kinds and names.</summary>
        static MapDef PlaceSites(MapDef m, Rng rng, Func<double, double, double> R, double W, double H,
            int want, double spacing, int players, string palette, JObj gen)
        {
            var S = gen.Obj("sites");
            var cv = gen.Obj("convert");
            double hw = W / 2.0, hh = H / 2.0;
            double Base(double x, double z)
            {
                double L = -2.0;
                foreach (var b in m.Blobs)
                {
                    double v = 1.0 - DMath.Hypot((x - b.X) / b.Rx, (z - b.Z) / b.Rz);
                    if (v > L) L = v;
                }
                foreach (var c in m.Carves)
                {
                    double d = DMath.Hypot(x - c.X, z - c.Z);
                    if (d < c.R) L = Math.Min(L, -(1.0 - d / c.R) * cv.Num("carveDepth") - cv.Num("carveFloor"));
                }
                return L;
            }
            bool Ok(double x, double z, double mn)
            {
                if (!(Base(x, z) > mn)) return false;
                foreach (var g in m.Ridges)
                    if (!(SegDist(x, z, g.A[0], g.A[1], g.B[0], g.B[1]) > g.W + S.Num("ridgeClear"))) return false;
                foreach (var g in m.Necks)
                    if (!(SegDist(x, z, g.A[0], g.A[1], g.B[0], g.B[1]) > S.Num("neckClear"))) return false;
                return Math.Abs(x) < hw - S.Num("edge") && Math.Abs(z) < hh - S.Num("edge");
            }
            var pts = new List<Pt>();
            double edge = S.Num("edge");
            int k = 0;
            while (k < S.Num("tries") && pts.Count < want)
            {
                k++;
                double x = R(-hw + edge, hw - edge);
                double z = R(-hh + edge, hh - edge);
                if (!Ok(x, z, S.Num("landMin"))) continue;
                bool near = false;
                foreach (var p in pts)
                    if (DMath.Hypot(p.X - x, p.Z - z) < spacing) { near = true; break; }
                if (near) continue;
                double pr = S.Num("probe"), pl = S.Num("probeLand");
                int around = (Ok(x + pr, z, pl) ? 1 : 0) + (Ok(x - pr, z, pl) ? 1 : 0) + (Ok(x, z + pr, pl) ? 1 : 0) + (Ok(x, z - pr, pl) ? 1 : 0);
                if (around < S.Num("probeNeed")) continue;
                pts.Add(new Pt { X = x, Z = z });
            }
            // HQ slots: farthest-point picks, starting from the westernmost site
            pts = SortStable(pts, (a, b) => a.X - b.X);
            var slots = new List<int> { 0 };
            while (slots.Count < Math.Min(players, pts.Count))
            {
                int best = -1;
                double bd = -1.0;
                for (int i = 0; i < pts.Count; i++)
                {
                    if (slots.Contains(i)) continue;
                    double md = 1e9;
                    foreach (int s in slots) md = Math.Min(md, DMath.Hypot(pts[i].X - pts[s].X, pts[i].Z - pts[s].Z));
                    if (md > bd) { bd = md; best = i; }
                }
                slots.Add(best);
            }
            // the most central sites become strongholds, the rest a mix
            var others = new List<int>();
            for (int i = 0; i < pts.Count; i++) if (!slots.Contains(i)) others.Add(i);
            others = SortStable(others, (a, b) => DMath.Hypot(pts[a].X, pts[a].Z) - DMath.Hypot(pts[b].X, pts[b].Z));
            var types = new string[pts.Count];
            foreach (int i in slots) types[i] = "hq";
            int strongholds = S.Int("defaultStrongholds");
            var mix = S.Strs("mix");
            for (int kk = 0; kk < others.Count; kk++) types[others[kk]] = kk < strongholds ? "stronghold" : mix[kk % mix.Length];
            // names stitched from two halves, shuffled, never repeating
            var pool = new List<string>();
            foreach (var a in S.Strs("nameA"))
                foreach (var b in S.Strs("nameB"))
                    pool.Add(a + b);
            for (int i2 = pool.Count - 1; i2 > 0; i2--)
            {
                int j = (int)Math.Floor(rng.Next() * (i2 + 1));
                (pool[i2], pool[j]) = (pool[j], pool[i2]);
            }
            for (int i = 0; i < pts.Count; i++)
                m.Zones.Add(new MapZone { Name = pool[i % pool.Count], Type = types[i], X = DMath.RoundJs(pts[i].X), Z = DMath.RoundJs(pts[i].Z) });
            m.Id = "chaos";
            m.Name = "Chaos Isles";
            m.W = W;
            m.H = H;
            m.Ns = new[] { 2.0, 2.0 };
            m.MaxPlayers = Math.Min(players, slots.Count);
            m.Slots = slots;
            m.Generated = true;
            m.Palette = palette ?? "earth";
            m.Chaos = true;
            m.Large = true;
            return m;
        }

        // ---------- convertMap / scaleMap ----------

        /// <summary>Turns the old site kinds into Fortresses, Towns and Airbases and marks Ports (web convertMap,
        /// the path for generated maps; fixed maps arrive already converted in maps.json).</summary>
        public static void ConvertMap(MapDef m, JObj gen, JObj balance)
        {
            var MX = balance.Obj("mapMix");
            var cv = gen.Obj("convert");
            var BZ = balance.Obj("zones");
            var Z = m.Zones;
            var slots = m.Slots;
            double diag = DMath.Hypot(m.W, m.H);
            var old = Z.ConvertAll(z => z.Type);
            double R0(string t) => BZ.Has(t) ? BZ.Obj(t).Num("r") : cv.Num("defaultR");
            const double INF = double.PositiveInfinity;
            var coast = new double[Z.Count];
            for (int i = 0; i < Z.Count; i++)
                coast[i] = CoastDist(m, Z[i].X, Z[i].Z, R0(slots.Contains(i) ? "hq" : "town"), 0.0, MX, cv);
            double RidgeClear(double x, double z)
            {
                double a = cv.Num("ridgeClearStart");
                foreach (var g in m.Ridges) a = Math.Min(a, SegDist(x, z, g.A[0], g.A[1], g.B[0], g.B[1]) - g.W);
                return a;
            }
            var free = new List<int>();
            for (int i = 0; i < Z.Count; i++) if (!slots.Contains(i)) free.Add(i);
            int n = free.Count;
            var type = new string[Z.Count];
            for (int i = 0; i < Z.Count; i++) type[i] = slots.Contains(i) ? "hq" : null;
            double Spread(int i, List<int> set)
            {
                double d = 1e9;
                foreach (int k in set) d = Math.Min(d, DMath.Hypot(Z[i].X - Z[k].X, Z[i].Z - Z[k].Z));
                return Math.Min(1.0, d / (diag * cv.Num("spreadDiag")));
            }
            List<int> Plus(List<int> a, List<int> b) { var r = new List<int>(a); r.AddRange(b); return r; }
            List<int> Pick(int count, Func<int, List<int>, double> score)
            {
                var o = new List<int>();
                for (int k = 0; k < count; k++)
                {
                    int b = -1;
                    double bs = -1e9;
                    foreach (int i in free)
                    {
                        if (type[i] != null || o.Contains(i)) continue;
                        double s = score(i, o);
                        if (s > bs) { bs = s; b = i; }
                    }
                    if (b < 0) break;
                    o.Add(b);
                }
                return o;
            }
            // airbases: open, inland ground, spread apart (a site already called an airfield always is one)
            int nAir = Math.Max(MX.Int("minAirbases"), (int)DMath.RoundJs(n * MX.Num("airbase")));
            foreach (int i in Pick(nAir, (i, o) =>
            {
                double s = Z[i].Name.ToLowerInvariant().Contains("airfield") ? cv.Num("airfieldBonus") : 0.0;
                s += Math.Min(1.0, RidgeClear(Z[i].X, Z[i].Z) / cv.Num("ridgeNorm"));
                s += Math.Min(1.0, Math.Max(0.0, LandRaw(m, Z[i].X, Z[i].Z, cv)) / cv.Num("landNorm")) * cv.Num("landWeight");
                s -= coast[i] < INF ? cv.Num("coastPenalty") : 0.0;
                return s + cv.Num("airSpread") * Spread(i, Plus(slots, o));
            })) type[i] = "airbase";
            // fortresses: walled sites first (strongholds, then outposts), spread across the map
            int nFort = (int)DMath.RoundJs(n * MX.Num("fortress"));
            foreach (int i in Pick(nFort, (i, o) =>
            {
                double s = old[i] == "stronghold" ? cv.Num("strongholdScore") : old[i] == "outpost" ? cv.Num("outpostScore") : 0.0;
                return s + cv.Num("fortSpread") * Spread(i, Plus(slots, o));
            })) type[i] = "fortress";
            foreach (int i in free) if (type[i] == null) type[i] = "town";
            // Ports: minPorts of them outside the HQs, at least one Port Fortress and one Port Town
            if (!m.NoWater)
            {
                List<int> Ports(string t) => free.FindAll(i => type[i] == t && coast[i] < INF);
                double fb = MX.Num("portFallbackReach");
                foreach (double reach in new[] { fb, fb * cv.Num("fallbackReachGrow") })
                {
                    var far = new double[Z.Count];
                    for (int i = 0; i < Z.Count; i++)
                        far[i] = coast[i] < INF || slots.Contains(i) ? INF : CoastDist(m, Z[i].X, Z[i].Z, R0(type[i]), reach, MX, cv);
                    int Nearest(string t)
                    {
                        var c = SortStable(free.FindAll(i => type[i] == t && coast[i] == INF && far[i] < INF), (a, b) => far[a] - far[b]);
                        return c.Count > 0 ? c[0] : -1;
                    }
                    foreach (var t in new[] { "town", "fortress" })
                        while (Ports("town").Count + Ports("fortress").Count < MX.Num("minPorts"))
                        {
                            int f = Nearest(t);
                            if (f < 0) break;
                            coast[f] = far[f];
                        }
                    foreach (var w in new[] { "fortress", "town" })
                        if (Ports(w).Count == 0)
                        {
                            int f = Nearest(w);
                            if (f >= 0) coast[f] = far[f];
                        }
                }
                foreach (var pair in new[] { new[] { "fortress", "town" }, new[] { "town", "fortress" } })
                {
                    if (Ports(pair[0]).Count > 0) continue;
                    var c = Ports(pair[1]);
                    if (c.Count > 1)
                        foreach (int d in free)
                            if (type[d] == pair[0] && coast[d] == INF)
                            {
                                type[c[0]] = pair[0];
                                type[d] = pair[1];
                                break;
                            }
                }
            }
            var zs = new List<MapZone>();
            for (int i = 0; i < Z.Count; i++) zs.Add(new MapZone { Name = Z[i].Name, Type = type[i], X = Z[i].X, Z = Z[i].Z, Port = coast[i] < INF });
            m.Zones = zs;
            m.Mix = BaseMix(zs);
        }

        /// <summary>Draws the battlefield mapScale times larger than it was laid out (web scaleMap).</summary>
        public static void ScaleMap(MapDef m, JObj gen)
        {
            if (m.Scaled) return;
            m.Scaled = true;
            double S = gen.Num("mapScale"), step = gen.Num("sizeStep");
            m.W = DMath.RoundJs(m.W * S / step) * step;
            m.H = DMath.RoundJs(m.H * S / step) * step;
            foreach (var z in m.Zones) { z.X *= S; z.Z *= S; }
            // features shared between maps (or listed twice) are scaled once, like the web's WeakSet
            var seen = new List<object>();
            bool Once(object o)
            {
                foreach (var x in seen) if (ReferenceEquals(x, o)) return false;
                seen.Add(o);
                return true;
            }
            foreach (var b in m.Blobs) if (Once(b)) { b.X *= S; b.Z *= S; b.Rx *= S; b.Rz *= S; }
            foreach (var c in m.Carves) if (Once(c)) { c.X *= S; c.Z *= S; c.R *= S; }
            foreach (var list in new[] { m.Ridges, m.Necks })
                foreach (var r in list)
                    if (Once(r))
                    {
                        r.A = new[] { r.A[0] * S, r.A[1] * S };
                        r.B = new[] { r.B[0] * S, r.B[1] * S };
                        r.W *= S;
                    }
            m.Ns = new[] { m.Ns[0] * S, m.Ns[1] * S };
        }

        // ---------- start slots (web createGame: "assign HQ start slots") ----------

        /// <summary>Picks each army's HQ start. opts: the battle options (humans, ai, mode). rnd: the battle's Rng
        /// (Chaos Isles shuffles the starts with it). Unused HQ slots become neutral Fortresses.</summary>
        public static BattleZones BattleZonesFor(MapDef m, BattleOptions opts, Rng rnd, JObj gen)
        {
            double far = gen.Obj("slots").Num("far"), worst = gen.Obj("slots").Num("teamWorst");
            int maxP = m.MaxPlayers;
            var humans = opts.Humans == null || opts.Humans.Count == 0 ? new List<HumanCfg> { new HumanCfg { Team = 1 } } : opts.Humans;
            humans = humans.GetRange(0, Math.Min(maxP, humans.Count));
            int H = humans.Count;
            var ai = opts.Ai ?? new List<AiCfg> { new AiCfg { P = 0, Team = 2 }, new AiCfg { P = 1, Team = 3 }, new AiCfg { P = 2, Team = 4 } };
            ai = ai.GetRange(0, Math.Min(ai.Count, Math.Max(0, maxP - H)));
            int NF = ai.Count + H;
            string mode = opts.Mode == "teams" || m.Carrier ? "teams" : "ffa";
            var teamOf = new int[NF];
            for (int i = 0; i < H; i++) teamOf[i] = mode == "teams" ? humans[i].Team ?? 1 : i;
            for (int i = 0; i < ai.Count; i++) teamOf[H + i] = mode == "teams" ? ai[i].Team ?? 2 : H + i;
            var sp = m.Slots.ConvertAll(i => new[] { m.Zones[i].X, m.Zones[i].Z });
            double Dist(double[] a, double[] b) => DMath.Hypot(a[0] - b[0], a[1] - b[1]);
            var slotOf = new int[NF];
            for (int i = 0; i < NF; i++) slotOf[i] = -1;
            var used = new HashSet<int>();
            slotOf[0] = 0;
            used.Add(0);
            if (mode == "teams")
            {
                var teams = new List<int>();
                foreach (int t in teamOf) if (!teams.Contains(t)) teams.Add(t);
                foreach (int t in teams)
                {
                    var members = new List<int>();
                    for (int f = 1; f < NF; f++) if (teamOf[f] == t && slotOf[f] < 0) members.Add(f);
                    if (members.Count == 0) continue;
                    int anchor = t == teamOf[0] ? 0 : -1;
                    foreach (int f in members)
                    {
                        int best = -1;
                        double bs = worst;
                        for (int k = 0; k < sp.Count; k++)
                        {
                            if (used.Contains(k)) continue;
                            double sc;
                            if (anchor >= 0) sc = -Dist(sp[k], sp[anchor]);
                            else
                            {
                                sc = far;
                                for (int g = 0; g < NF; g++)
                                    if (slotOf[g] >= 0 && teamOf[g] != t) sc = Math.Min(sc, Dist(sp[k], sp[slotOf[g]]));
                            }
                            if (sc > bs) { bs = sc; best = k; }
                        }
                        slotOf[f] = best;
                        used.Add(best);
                        if (anchor < 0) anchor = best;
                    }
                }
            }
            else
            {
                for (int f = 1; f < NF; f++)
                {
                    int best = -1;
                    double bs = -1.0;
                    for (int k = 0; k < sp.Count; k++)
                    {
                        if (used.Contains(k)) continue;
                        double md = far;
                        for (int g = 0; g < NF; g++)
                            if (slotOf[g] >= 0) md = Math.Min(md, Dist(sp[k], sp[slotOf[g]]));
                        if (md > bs) { bs = md; best = k; }
                    }
                    slotOf[f] = best;
                    used.Add(best);
                }
            }
            // Chaos Isles: throw the plan away and shuffle every army onto a random start
            if (m.Chaos)
            {
                used.Clear();
                var perm = new int[sp.Count];
                for (int i = 0; i < perm.Length; i++) perm[i] = i;
                for (int i = perm.Length - 1; i > 0; i--)
                {
                    int j = (int)Math.Floor(rnd.Next() * (i + 1));
                    (perm[i], perm[j]) = (perm[j], perm[i]);
                }
                for (int f = 0; f < NF; f++)
                {
                    slotOf[f] = perm[f];
                    used.Add(perm[f]);
                }
            }
            var zonesFinal = m.Zones.ConvertAll(z => z.Copy());
            for (int k = 0; k < m.Slots.Count; k++)
                if (!used.Contains(k)) zonesFinal[m.Slots[k]].Type = "fortress";
            return new BattleZones { SlotOf = slotOf, ZonesFinal = zonesFinal, NF = NF, TeamOf = teamOf, Mode = mode, Humans = humans, Ai = ai };
        }
    }
}
