// Dawgs Uprising -> Unity: the browser game's interface settings (Settings / pause screen), kept between sessions in
// PlayerPrefs like the game keeps them in the browser.
//   HpAlways   "Always show unit health bars" (on by default; off = only selected or damaged units)
//   MidPan     "Middle mouse drag": false = Orbit · Shift pans (the default), true = Pan · Shift orbits
using System;
using UnityEngine;

public static class DawgsPrefs
{
    static bool loaded, hpAlways = true, midPan;
    public static event Action Changed;

    static void Load()
    {
        if (loaded) return; loaded = true;
        hpAlways = PlayerPrefs.GetInt("dawgs.hpAlways", 1) == 1;
        midPan = PlayerPrefs.GetInt("dawgs.midPan", 0) == 1;
    }
    static void Save()
    {
        PlayerPrefs.SetInt("dawgs.hpAlways", hpAlways ? 1 : 0);
        PlayerPrefs.SetInt("dawgs.midPan", midPan ? 1 : 0);
        PlayerPrefs.Save();
        Changed?.Invoke();
    }

    public static bool HpAlways { get { Load(); return hpAlways; } set { Load(); hpAlways = value; Save(); } }
    public static bool MidPan { get { Load(); return midPan; } set { Load(); midPan = value; Save(); } }
}
