using System;
using System.Collections.Generic;
using System.Globalization;

namespace DawgsUprising.Sim
{
    /// <summary>An AI army's planner state (web faction.ai).</summary>
    public sealed class AiState
    {
        public double T, WaveT;
        public List<object> Groups = new List<object>();
        public Dictionary<string, object> Qrf = new Dictionary<string, object>();
    }

    /// <summary>An army (web G.factions[i]). Field names follow the web game.</summary>
    public sealed class Faction
    {
        public int Id, Team;
        public string Name, Short, Css, Blurb, Diff;
        public int Color;
        public bool Player, Alive, AutoGarrison;
        public Dictionary<string, double> Comp, Prefer;
        public double Money, Hr;
        public double[] Aggro;
        public int Kills, Losses;
        public int? LostTo;
        public AiState Ai;
    }

    /// <summary>Who is capturing a base and how far they've got.</summary>
    public sealed class CapState
    {
        public int? F;
        public double P;
    }

    public sealed class Point { public double X, Z; }

    /// <summary>A terminal stand on an airbase apron, and the plane parked there.</summary>
    public sealed class Terminal
    {
        public double X, Z;
        public object U;
    }

    /// <summary>An airbase's runway frame: direction (U), its normal (N), length, centre, ends, taxiway, stands.</summary>
    public sealed class AirField
    {
        public double Ang, Ux, Uz, Nx, Nz, L, Cx, Cz, Tx, Tz, RwyT;
        public Point A, B;
        public List<Terminal> Terms;
    }

    /// <summary>A street or quay: a line of points, W wide, belonging to a base.</summary>
    public sealed class Street
    {
        public int Zone;
        public List<double[]> Pts;
        public double W;
        public bool Quay;
    }

    /// <summary>A build plot: a levelled spot where a facility can go. Kind: mil, eco or fort.</summary>
    public sealed class Plot
    {
        public int I;
        public double X, Z, Y, Ang;
        public FacilityState Fac;   // the building on it, or null
        public string Tag, Kind;
        public Point Water;         // nearest water cell for a naval yard, or null
        public int? Zone;           // a placed building's base
        public bool Used;           // a laid-out spot something was built on
        public Unit Body;           // the building's hit points, as a structure unit
    }

    /// <summary>A building on a plot (web plot.fac): type, level, building/ready state and production timers.</summary>
    public sealed class FacilityState
    {
        public string Type, State, Pstate;
        public int Level, ProdI;
        public double T, Dur, ProdT;   // web t and T: build progress so far and the time it takes
        public Unit Unit;
    }

    /// <summary>A base (web G.zones[i]). Field names follow the web game.</summary>
    public sealed class Zone
    {
        public int Id;
        public string Name, Type, ProdState;
        public double X, Z, Y, R, GarHp, ProdT, CapturedT, ThreatT;
        public int? Owner, Home;
        public CapState Cap;
        public bool Coastal, Port, Contested;
        public int GarN, ProdI;
        public int[] Counts;
        // build plots
        public Cove Cove;
        public AirField Air;
        public double Gate;
        public int Budget;
        public ZoneSlots Slots;
        public List<Plot> Spots;
        public List<Plot> Plots;
        // walls (walled base types only)
        public WallDef Wall;
        public bool Walled, Breached;
        public double BreachT, GateOpen, GateHold;
        public Unit GateU;
        public List<int> WallCells, Yard;   // the base's cells, and the open courtyard cells garrisons stand on
        public int? Drill;                  // drill level (null = 1)
        public bool Hosp;                   // Field Hospital upgrade
        public double Msl, MslT;            // ballistic missiles stocked, and the build timer
    }

    /// <summary>
    /// The game simulation for one battle, ported from the web game's SIM script (createGame and everything in it).
    ///
    /// Rules for everything in this package:
    /// - Pure logic: no UnityEngine (the assembly has noEngineReferences), no files, no clocks.
    /// - Everything it needs comes in through the constructor: the game data and the battle options.
    /// - Deterministic: same seed + same commands = same result on every machine (multiplayer relies on it).
    ///   Randomness only from Rng, maths through DMath.
    /// - No gameplay numbers in code: read them from the data files.
    /// - The renderer reads state; it changes the SIM only through commands.
    /// </summary>
    public sealed partial class Battle
    {
        public readonly GameData Data;
        public readonly JObj Balance;
        public readonly BattleOptions Opts;
        public double Time;
        public int Ticks;
        public bool Over;

        // battle setup (web createGame)
        public long Seed;
        public Rng Rnd;                 // the battle's Rng (web rnd)
        public MapDef Map;              // the map, with ZonesFinal
        public string Mode = "ffa";
        public bool CarrierMode;        // web CVM
        public int NF;                  // number of armies
        public int H;                   // number of human players
        public List<HumanCfg> Humans;
        public List<AiCfg> AiCfg;
        public int[] TeamOf, SlotOf;
        public Terrain Terrain;
        public Pathing Pathing;
        public Tables Tables;
        public readonly List<Faction> Factions = new List<Faction>();   // web G.factions
        public readonly List<Zone> Zones = new List<Zone>();            // web G.zones
        public int Home = -1;            // web G.home: the player's HQ zone
        public int[] Homes;              // web G.homes
        public bool AiPassive;
        public List<Street> Streets = new List<Street>();     // web G.streets
        public List<AirField> AirCorr = new List<AirField>(); // web G.airCorr

        readonly double _step, _maxFrame;
        double _acc;

        /// <summary>data: the game data. opts: the battle options. checkpoint (tests): called with a name at each
        /// setup checkpoint ("zones", then "plots"), to compare the state with recordings of the web game.
        /// With balance-only data (no maps) the SIM just ticks, for low-level tests.</summary>
        public Battle(GameData data, BattleOptions opts = null, Action<string, Battle> checkpoint = null)
        {
            Data = data;
            Balance = data.Balance;
            Opts = opts ?? new BattleOptions();
            var engine = Balance.Obj("engine");
            _step = engine?.Num("step", 0) ?? 0;
            _maxFrame = engine?.Num("maxFrame", 0) ?? 0;
            if (_step <= 0 || _maxFrame <= 0) throw new ArgumentException("balance.json needs engine.step and engine.maxFrame");
            if (data.Maps != null) Setup(checkpoint);
        }

        // ---------- battle setup (web createGame) ----------

        void Setup(Action<string, Battle> checkpoint)
        {
            var gen = Data.Mapgen;
            var ST = Balance.Obj("start");
            Seed = Opts.Seed != 0 ? Opts.Seed : (long)gen.Num("defaultSeed");
            long rngSeed = Opts.RngSeed;
            Rnd = new Rng((rngSeed != 0 ? rngSeed : Seed) ^ (long)gen.Num("rngXor"));
            Map = (Opts.Map != null && Data.Maps.TryGetValue(Opts.Map, out var md) ? md : Data.Maps[gen.Str("defaultMap")]).Copy();
            if (Map.Chaos || Opts.Map == "chaos")
            {
                long ms = Opts.MapSeed;
                Map = Maps.MakeChaos(ms != 0 ? ms : rngSeed != 0 ? rngSeed : Seed, gen, Balance);
            }
            CarrierMode = Map.Carrier;
            var bz = Maps.BattleZonesFor(Map, Opts, Rnd, gen);
            NF = bz.NF;
            TeamOf = bz.TeamOf;
            Mode = bz.Mode;
            SlotOf = bz.SlotOf;
            Humans = bz.Humans;
            AiCfg = bz.Ai;
            H = Humans.Count;
            Map.ZonesFinal = bz.ZonesFinal;
            Terrain = Terrain.Build(Map, Seed, Balance, gen);
            Pathing = new Pathing(Terrain, Balance.Obj("engine"));
            Tables = new Tables(Balance);
            SetupUnits();
            SetupFactions(ST);
            SetupZones(ST);
            checkpoint?.Invoke("zones", this);
            var plots = new Plots(this);
            plots.Run();
            Streets = plots.Streets;
            AirCorr = plots.AirCorr;
            checkpoint?.Invoke("plots", this);
            SetupWalls(plots);
            SetupForces();
            checkpoint?.Invoke("forces", this);
        }

        string Difficulty(int f)
        {
            if (Opts.EasyAI) return "easy";
            string d = AiCfg[f - H].Diff;
            return d == "easy" || d == "normal" || d == "hard" ? d : "hard";
        }

        static int ParseColor(string c) => int.Parse(c.TrimStart('#'), NumberStyles.HexNumber, CultureInfo.InvariantCulture);

        void SetupFactions(JObj ST)
        {
            var player = Data.Factions.Player;
            var pool = Data.Factions.Ai;
            var money = ST.Obj("money");
            for (int f = 0; f < NF; f++)
            {
                FactionDef def;
                string name = null, shortName = null;
                ColorCfg col;
                if (f < H)
                {
                    var hu = Humans[f];
                    def = player;
                    if (hu.Name != null) name = shortName = hu.Name;
                    else if (H > 1) { name = $"Player {f + 1}"; shortName = $"P{f + 1}"; }
                    col = hu.Color;
                }
                else
                {
                    var a = AiCfg[f - H];
                    def = pool[a.P % pool.Count];
                    if (a.Name != null) { name = a.Name; shortName = a.Short ?? a.Name; }
                    col = a.Color;
                }
                var fd = new Faction
                {
                    Name = name ?? def.Name, Short = shortName ?? def.Short, Css = def.Css, Blurb = def.Blurb, Player = def.Player,
                    Color = ParseColor(def.Color),
                    Comp = def.Comp == null ? null : new Dictionary<string, double>(def.Comp),
                    Prefer = def.Prefer == null ? null : new Dictionary<string, double>(def.Prefer),
                };
                if (col != null && col.Css != null)
                {
                    fd.Css = col.Css;
                    fd.Color = ParseColor(col.Hex);
                }
                fd.Id = f;
                fd.Team = TeamOf[f];
                fd.Money = fd.Player ? money.Num("player") : money.Num("ai");
                fd.Hr = fd.Player ? ST.Num("manpower") : 0.0;
                fd.Aggro = new double[NF];
                fd.Alive = true;
                fd.AutoGarrison = true;
                if (!fd.Player)
                {
                    string d = Difficulty(f);
                    fd.Diff = d;
                    fd.Ai = new AiState
                    {
                        T = ST.Num("aiThink") + f * ST.Num("aiThinkStagger"),
                        WaveT = (ST.Num("aiWave") + f * ST.Num("aiWaveStagger")) * Balance.Obj("ai").Obj("difficulty").Obj(d).Num("first"),
                    };
                }
                Factions.Add(fd);
            }
            // tutorial: the AI holds back until it is released
            AiPassive = Opts.PassiveAI;
            if (AiPassive)
                foreach (var fac in Factions)
                    if (fac.Ai != null) fac.Ai.WaveT = Balance.Obj("ai").Num("passiveWave");
            // starting grudges toward every enemy
            var AG = Balance.Obj("aggro");
            foreach (var a in Factions)
                foreach (var b in Factions)
                    if (Hostile(a.Id, b.Id)) a.Aggro[b.Id] = AG.Num("start") + Rnd.Next() * AG.Num("startSpread");
        }

        public bool Hostile(int? a, int? b) => a != null && b != null && a != b && Factions[a.Value].Team != Factions[b.Value].Team;

        public bool Allied(int? a, int? b) => a != null && b != null && Factions[a.Value].Team == Factions[b.Value].Team;

        void SetupZones(JObj ST)
        {
            var ZT = Tables.ZTypes;
            var zf = Map.ZonesFinal;
            for (int i = 0; i < zf.Count; i++)
            {
                var d = zf[i];
                var t = ZT[d.Type];
                Zones.Add(new Zone
                {
                    Id = i, Name = d.Name, Type = d.Type, X = d.X, Z = d.Z, R = t.R,
                    Cap = new CapState(), Coastal = d.Port == true, Counts = new int[NF],
                    ProdT = t.Prod.Every * (ST.Num("zoneProdMin") + Rnd.Next() * ST.Num("zoneProdSpread")),
                    ProdState = "idle", CapturedT = -999, ThreatT = -999,
                    Y = Terrain.HeightAt(d.X, d.Z),
                });
            }
            var slots = Map.Slots;
            if (!CarrierMode)
                for (int f = 0; f < NF; f++)
                {
                    int zi = slots[SlotOf[f]];
                    Zones[zi].Owner = f;
                    Zones[zi].Home = f;
                }
            Home = slots[SlotOf[0]];
            Homes = new int[NF];
            for (int f = 0; f < NF; f++) Homes[f] = slots[SlotOf[f]];
            if (!Opts.NoStartZones && !CarrierMode)
            {
                var slotZone = new HashSet<int>(slots);
                double far = Data.Mapgen.Obj("slots").Num("far");
                for (int round = 0; round < 2; round++)
                    for (int f = 0; f < NF; f++)
                    {
                        var hq = Zones[slots[SlotOf[f]]];
                        Zone best = null;
                        double bd = far;
                        foreach (var z in Zones)
                        {
                            if (z.Owner != null || slotZone.Contains(z.Id)) continue;
                            double d = DMath.Hypot(z.X - hq.X, z.Z - hq.Z);
                            if (d < bd) { bd = d; best = z; }
                        }
                        if (best != null) best.Owner = f;
                    }
            }
        }

        // ---------- running ----------

        /// <summary>Advance by real time. Like the web G.update(): each call is capped at engine.maxFrame and run in
        /// fixed engine.step ticks.</summary>
        public void Update(double dt)
        {
            if (Over) return;
            _acc += Math.Min(dt, _maxFrame);
            while (_acc >= _step)
            {
                Tick(_step);
                _acc -= _step;
                if (Over) break;
            }
        }

        /// <summary>Run n fixed ticks directly (web stepTicks), for tests and lockstep.</summary>
        public void StepTicks(int n)
        {
            for (int i = 0; i < n && !Over; i++) Tick(_step);
        }

        void Tick(double dt)
        {
            Time += dt;
            Ticks++;
            if (Terrain == null) return;   // balance-only battles just keep time
            // Web tick() order: rebuildHash, airbaseUpkeep, updateUnit (each unit), separate, updateProjectiles, then
            // recruitTick, autoMan, every 0.25 s updateZones/produce/updateFacilities, economy, missiles, heal every 0.5 s,
            // carrierTick, faction AI and visibility every 0.2 s. Ported so far: the unit systems and healing.
            if ((Opts.Systems & Systems.Units) != 0) UnitSystems(dt);
            if ((Opts.Systems & Systems.Heal) != 0) { _healT += dt; if (_healT >= Balance.Obj("heal").Num("every")) { Heal(_healT); _healT = 0; } }
            _cleanT += dt;
            if (_cleanT >= Balance.Obj("engine").Num("cleanEvery")) { Units = Units.FindAll(u => u.Alive); _cleanT = 0; }   // drop the dead every second
        }

        /// <summary>Fingerprint of the game state, to spot machines drifting apart in multiplayer.
        /// Placeholder until units are ported.</summary>
        public ulong StateHash()
        {
            ulong h = 14695981039346656037UL;
            void Mix(long v) { unchecked { for (int i = 0; i < 8; i++) { h ^= (byte)(v >> (8 * i)); h *= 1099511628211UL; } } }
            Mix(Ticks);
            Mix(DMath.Bits(Time));
            return h;
        }
    }
}
