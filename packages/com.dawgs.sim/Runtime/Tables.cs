using System;
using System.Collections.Generic;

namespace DawgsUprising.Sim
{
    /// <summary>A unit type: balance.json units.* plus what the web SIM derives at load time (key, hr, wpn,
    /// rad, isVeh, sight, vision). Fields a unit doesn't list stay 0 / false / null.</summary>
    public sealed class UnitType
    {
        public string Name, Hot, Weapon, Armor, Req;
        public double Cost, Mp, Hp, Speed, Range, MinR, Dmg, Rof, Acc, Splash, Build;
        public bool Naval, Carrier, NoRecruit, Builder, Air, AirOnly, Static, Struct, Plane, Mega;
        public double Guns, Front, Rear, Deploy, Volley, Turn, Ammo, Sortie, Rearm, Evasive, Patrol, Support, Alt, Repair, FacilityDown;
        // derived
        public string Key, Wpn;
        public double Hr, Rad, Sight, Vision;
        public bool IsVeh;
    }

    /// <summary>Plot counts of a base type.</summary>
    public sealed class ZoneSlots
    {
        public int Mil, Eco, Fort;
        public int Total => Mil + Eco + Fort;
        public ZoneSlots Copy() => (ZoneSlots)MemberwiseClone();
    }

    /// <summary>What a base or facility produces: every `Every` seconds, up to `Cap`, in the order `Seq`.</summary>
    public sealed class ProdSpec
    {
        public double Every, Cap;
        public string[] Seq;
    }

    /// <summary>A base type: balance.json zones.* plus hr and recruit (web ZTYPES).</summary>
    public sealed class ZoneType
    {
        public string Label;
        public double R, Income, Mp, Garrison, GarrisonHp, CapMult, Value, EcoMult, Heal, Planes, Terminals, Runway;
        public bool Repairs;
        public ZoneSlots Slots;
        public string[] Roster, Naval, GarrisonSeq;
        public ProdSpec Prod;
        // derived
        public double Hr;
        public bool Recruit;
    }

    /// <summary>A facility (building) type: balance.json facilities.* plus prod.seq (web FACILITIES).</summary>
    public sealed class Facility
    {
        public string Name, Slot, Desc;
        public double Cost, Time, Planes, PlanesUpgraded, Income, Manpower, Vision, Radar;
        public bool Port, Coastal, Trade;
        public string[] Seq, Only, Manual;
        // derived
        public ProdSpec Prod;
    }

    /// <summary>
    /// The SIM's derived tables, built from balance.json like the web SIM does at load time: unit types (UTYPES),
    /// base types (ZTYPES), facilities and plot counts per base type. No numbers here: radii, sight and vision
    /// padding all come from balance.json.
    /// </summary>
    public sealed class Tables
    {
        public readonly Dictionary<string, UnitType> UTypes = new Dictionary<string, UnitType>();
        public readonly Dictionary<string, ZoneType> ZTypes = new Dictionary<string, ZoneType>();
        public readonly Dictionary<string, Facility> Facilities = new Dictionary<string, Facility>();
        public readonly Dictionary<string, int> Plots = new Dictionary<string, int>();

        public Tables(JObj balance)
        {
            var RAD = balance.Obj("unitRadius");
            var SG = balance.Obj("sight");
            var VIS = balance.Obj("vision");
            var units = balance.Obj("units");
            foreach (var key in units.Keys)
            {
                var b = units.Obj(key);
                var t = Bind.To<UnitType>(b);
                t.Key = key;
                t.Hr = t.Mp;
                t.Wpn = t.Weapon;
                string armor = t.Armor ?? "";
                double rad;
                if (t.Carrier) rad = RAD.Num("carrier");
                else if (armor == "ship") rad = RAD.Num("ship");
                else if (t.Naval) rad = RAD.Num("boat");
                else if (t.Air) rad = RAD.Num("air");
                else if (armor == "hvy") rad = RAD.Num("hvy");
                else if (armor == "inf") rad = RAD.Num("inf");
                else if (key == "pillbox") rad = RAD.Num("pillbox");
                else if (key == "how") rad = RAD.Num("how");
                else rad = RAD.Num("other");
                t.Rad = rad;
                t.IsVeh = armor == "veh" || armor == "hvy";
                t.Sight = Math.Max(SG.Num("min"), t.Range + SG.Num("pad"));
                t.Vision = Math.Max(t.Sight + SG.Num("visionExtra"), VIS.Num(key, 0.0));
                if (t.Plane)
                {
                    t.Rad = RAD.Num("plane");
                    t.Air = true;
                }
                UTypes[key] = t;
            }
            var fac = balance.Obj("facilities");
            foreach (var k in fac.Keys)
            {
                var f = Bind.To<Facility>(fac.Obj(k));
                if (f.Seq != null) f.Prod = new ProdSpec { Seq = f.Seq };
                Facilities[k] = f;
            }
            var zones = balance.Obj("zones");
            foreach (var k in zones.Keys)
            {
                var z = Bind.To<ZoneType>(zones.Obj(k));
                z.Hr = z.Mp;
                z.Recruit = true;
                ZTypes[k] = z;
                Plots[k] = z.Slots.Total;
            }
        }
    }
}
