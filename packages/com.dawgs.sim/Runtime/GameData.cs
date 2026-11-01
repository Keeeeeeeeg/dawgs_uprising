using System.Collections.Generic;

namespace DawgsUprising.Sim
{
    /// <summary>An army as factions.json describes it.</summary>
    public sealed class FactionDef
    {
        public string Name, Short, Color, Css, Blurb;
        public bool Player;
        public Dictionary<string, double> Comp, Prefer;
    }

    public sealed class FactionsFile
    {
        public FactionDef Player;
        public List<FactionDef> Ai;
    }

    /// <summary>
    /// Everything a battle needs, read once and shared between battles (the SIM copies what it changes):
    /// balance.json (every gameplay number), maps.json, mapgen.json and factions.json. Takes the files' text,
    /// so the SIM never touches the disk: Unity hands it TextAssets, the tests read files.
    /// </summary>
    public sealed class GameData
    {
        public JObj Balance, Mapgen;
        public Dictionary<string, MapDef> Maps;
        public FactionsFile Factions;

        public static GameData FromJson(string balance, string maps, string mapgen, string factions) => new GameData
        {
            Balance = (JObj)Json.Parse(balance),
            Maps = DawgsUprising.Sim.Maps.Load((JObj)Json.Parse(maps)),
            Mapgen = (JObj)Json.Parse(mapgen),
            Factions = Bind.To<FactionsFile>(Json.Parse(factions)),
        };

        /// <summary>Balance only: enough for the SIM to tick, for low-level tests.</summary>
        public static GameData BalanceOnly(string balance) => new GameData { Balance = (JObj)Json.Parse(balance) };
    }

    /// <summary>Colour given for an army in the battle options.</summary>
    public sealed class ColorCfg
    {
        public string Css, Hex;
    }

    public sealed class HumanCfg
    {
        public int? Team;
        public string Name;
        public ColorCfg Color;
    }

    public sealed class AiCfg
    {
        public int P;
        public int? Team;
        public string Diff, Name, Short;
        public ColorCfg Color;
    }

    /// <summary>The SIM's systems, each ticked in the web game's order. All of them run in a battle; tests that replay a
    /// web scenario recorded with only some of them switched on run the same ones.</summary>
    [System.Flags]
    public enum Systems
    {
        Units = 1,    // spatial hash, each unit's update, pushing apart, projectiles
        Heal = 2,     // units recovering in friendly bases
        All = ~0,
    }

    /// <summary>Battle options, like the web createGame options.</summary>
    public sealed class BattleOptions
    {
        public string Map, Mode;
        public long Seed, RngSeed, MapSeed;
        public List<HumanCfg> Humans;
        public List<AiCfg> Ai;
        public bool EasyAI, PassiveAI, NoStartZones;
        /// <summary>Tests: start without garrisons, squads or starting buildings.</summary>
        public bool Bare;
        public Systems Systems = Systems.All;
    }
}
