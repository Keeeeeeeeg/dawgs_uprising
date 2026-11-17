// Dawgs Uprising -> Unity: the browser game's sound settings (Settings / pause screen): music volume with a mute
// (Shift+M), alerts volume (sirens, alarms, pings) and unit sounds. Same defaults as the game (50 / 70 / 60 %),
// kept between sessions in PlayerPrefs. DawgsFx and DawgsGame listen for changes.
using System;
using UnityEngine;

public static class DawgsAudio
{
    public const float DefaultMusic = 0.5f, DefaultAlerts = 0.7f, DefaultUnits = 0.6f;
    static float music = DefaultMusic, alerts = DefaultAlerts, units = DefaultUnits;
    static bool muted, loaded;
    public static event Action Changed;

    static void Load()
    {
        if (loaded) return; loaded = true;
        music = PlayerPrefs.GetFloat("dawgs.vol.music", DefaultMusic);
        alerts = PlayerPrefs.GetFloat("dawgs.vol.alerts", DefaultAlerts);
        units = PlayerPrefs.GetFloat("dawgs.vol.units", DefaultUnits);
        muted = PlayerPrefs.GetInt("dawgs.vol.musicMuted", 0) == 1;
    }
    static void Save()
    {
        PlayerPrefs.SetFloat("dawgs.vol.music", music); PlayerPrefs.SetFloat("dawgs.vol.alerts", alerts);
        PlayerPrefs.SetFloat("dawgs.vol.units", units); PlayerPrefs.SetInt("dawgs.vol.musicMuted", muted ? 1 : 0);
        PlayerPrefs.Save();
        Changed?.Invoke();
    }

    public static float Music { get { Load(); return music; } set { Load(); music = Mathf.Clamp01(value); Save(); } }
    public static float Alerts { get { Load(); return alerts; } set { Load(); alerts = Mathf.Clamp01(value); Save(); } }
    public static float Units { get { Load(); return units; } set { Load(); units = Mathf.Clamp01(value); Save(); } }
    public static bool MusicMuted { get { Load(); return muted; } set { Load(); muted = value; Save(); } }

    // gains relative to the levels the sounds were balanced at (the defaults play them as before)
    public static float MusicGain => MusicMuted ? 0f : Music / DefaultMusic;
    public static float AlertGain => Alerts / DefaultAlerts;
    public static float UnitGain => Units / DefaultUnits;
}
