// Dawgs Uprising -> Unity: drives a unit rigged in Blender (Assets/Dawgs/Rigged/*.fbx).
//   SetMotion(speed, reversing)  Idle or Walk / Drive on the Animator, the stride / wheel turn timed to the ground speed
//                                (wheels and tracks run backwards while a vehicle reverses)
//   Aim(target) / Fire(target)   turns the upper body (soldiers) onto the target; Fire also kicks the gun back
//   SetTurret(yaw)               vehicles: the turret sits exactly where the game's own traverse has it
//   SetDeployed(on)              a gunner who has set up to fire goes down on one knee behind the gun
//   Alert()                      it was shot at or ordered about: a resting soldier gets back up
// The turn is applied after the Animator each frame (LateUpdate), on top of whatever clip is playing, so a soldier can
// walk one way and shoot another, and a tank's turret tracks while its wheels roll. The unit's forward is local +x.
//
// Soldiers with nothing to do don't stand like statues. At ease they look around, check their ammunition, shift their
// weight and stretch, and adjust their helmet and gear, each at their own irregular rhythm; left alone long enough they
// take a knee and keep watch from there. Moving, getting a target or being hit ends all of it at once.
using System.Collections.Generic;
using UnityEngine;

public class DawgsUnitRig : MonoBehaviour
{
    public Animator animator;
    public Transform aimBone;            // turret, or a soldier's torso
    public Transform kickBone;           // what recoils: the turret, or a soldier's arms
    public Transform[] muzzles;
    public bool infantry;
    public float strideLength = 0.8f;    // m covered by one Walk cycle
    public float wheelRadius = 0.35f;    // m, for timing the Drive clip
    public float traverseSpeed = 110f;   // deg/s
    public float maxYaw = 180f;          // soldiers twist at most this far from where their legs point
    public float recoilDistance = 0.12f;
    public float holdAim = 2.5f;         // s the gun stays on its last target before coming back to the front
    public bool idleMoves = true;        // soldiers at ease fidget and, after a while, take a knee
    public Vector2 fidgetEvery = new Vector2(5f, 13f);   // s between two idle moves
    public Vector2 kneelAfter = new Vector2(26f, 60f);   // s at ease before taking a knee

    float yaw, kick, aimUntil = -99f, alertT = -99f;
    Vector3 aimPoint; bool aiming;
    int muzzleIndex;
    bool turretDriven; float turretYaw;

    // at ease
    enum Rest { Ready, Fidget, Kneel }
    static readonly string[] Fidgets = { "LookAround", "LookAround", "CheckAmmo", "Stretch", "AdjustGear" };
    static readonly int SpeedId = Animator.StringToHash("Speed"), DirId = Animator.StringToHash("Dir");
    static readonly int IdleId = Animator.StringToHash("Idle"), KneelDownId = Animator.StringToHash("KneelDown"),
        KneelIdleId = Animator.StringToHash("KneelIdle"), KneelUpId = Animator.StringToHash("KneelUp");
    readonly Dictionary<string, float> clipLen = new Dictionary<string, float>();
    Rest rest; float easeT, nextFidget, fidgetEnd, kneelAt, groundSpeed;
    bool hasIdles, hasKneel, hasDir, deployedKneel, ready; string lastFidget;

    public bool Kneeling => rest == Rest.Kneel;

    public Vector3 MuzzlePosition
    {
        get
        {
            if (muzzles != null && muzzles.Length > 0)
            {
                var m = muzzles[muzzleIndex % muzzles.Length];
                if (m) return m.position;
            }
            return transform.position + transform.up * (infantry ? 0.6f : 1.5f);
        }
    }

    void Awake()
    {
        if (animator) animator.cullingMode = AnimatorCullingMode.AlwaysAnimate;   // the aim is layered on the clip's pose every frame
        if (muzzles != null && muzzles.Length > 0) muzzleIndex = Random.Range(0, muzzles.Length);
    }

    void Prepare()
    {
        ready = true;
        if (!animator || !animator.runtimeAnimatorController) return;
        foreach (var c in animator.runtimeAnimatorController.animationClips) if (c) clipLen[c.name] = c.length;
        foreach (var p in animator.parameters) if (p.nameHash == DirId) hasDir = true;
        hasKneel = infantry && animator.HasState(0, KneelDownId) && animator.HasState(0, KneelIdleId) && animator.HasState(0, KneelUpId) && clipLen.ContainsKey("KneelUp");
        hasIdles = infantry && hasKneel && animator.HasState(0, Animator.StringToHash("LookAround"));
        Schedule();
        nextFidget = Time.time + Random.Range(1.5f, fidgetEvery.y);              // so a fresh squad doesn't all fidget together
    }

    public void SetMotion(float speed) { SetMotion(speed, false); }
    public void SetMotion(float speed, bool reversing)
    {
        groundSpeed = speed;
        if (!animator || !animator.isActiveAndEnabled) return;
        if (!ready) Prepare();
        animator.SetFloat(SpeedId, speed);
        if (hasDir) animator.SetFloat(DirId, reversing ? -1f : 1f);
        float cycle = infantry ? strideLength : 2f * Mathf.PI * Mathf.Max(0.05f, wheelRadius);
        animator.speed = speed > 0.2f ? Mathf.Clamp(speed / cycle, 0.3f, 6f) : 1f;
    }

    /// keep the gun on this point (called while a target is in range)
    public void Aim(Vector3 target) { aimPoint = target; aiming = true; aimUntil = Mathf.Max(aimUntil, Time.time + 1.2f); }

    public void Fire(Vector3 target)
    {
        aimPoint = target; aiming = true; aimUntil = Time.time + holdAim; kick = 1f;
        if (muzzles != null && muzzles.Length > 1) muzzleIndex = (muzzleIndex + 1) % muzzles.Length;   // twin guns take turns
    }

    /// vehicles: where the turret points, in degrees from the hull's front (the game traverses it; this just shows it)
    public void SetTurret(float relativeYawDeg) { turretDriven = true; turretYaw = relativeYawDeg; }

    public void SetDeployed(bool on) { deployedKneel = on; }
    public void Alert() { alertT = Time.time; }

    // ---------------------------------------------------------------- at ease
    void Schedule()
    {
        easeT = 0f; kneelAt = Random.Range(kneelAfter.x, kneelAfter.y);
        nextFidget = Time.time + Random.Range(2.5f, fidgetEvery.y);
    }

    void Update()
    {
        if (!animator || !animator.isActiveAndEnabled) return;
        if (!ready) Prepare();
        if (!hasKneel) return;
        float now = Time.time, dt = Time.deltaTime;
        bool moving = groundSpeed > 0.2f;
        if (deployedKneel && !moving)
        {   // set up to fire: on one knee behind the gun for as long as it stays deployed
            if (rest != Rest.Kneel) Kneel();
            easeT = 0f; return;
        }
        bool alert = now < aimUntil + 1.5f || now - alertT < 4f;
        switch (rest)
        {
            case Rest.Ready:
                if (moving || alert || !idleMoves || !hasIdles) { easeT = 0f; if (nextFidget < now + 2f) nextFidget = now + Random.Range(2f, fidgetEvery.x); break; }
                easeT += dt;
                if (easeT >= kneelAt) Kneel();
                else if (now >= nextFidget) Fidget();
                break;
            case Rest.Fidget:
                easeT += dt;
                if (moving) { rest = Rest.Ready; Schedule(); }                     // the Animator's own transition takes it into Walk
                else if (alert) { animator.CrossFadeInFixedTime(IdleId, 0.18f, 0, 0f); rest = Rest.Ready; Schedule(); }
                else if (now >= fidgetEnd) { rest = Rest.Ready; nextFidget = now + Random.Range(fidgetEvery.x, fidgetEvery.y); }
                break;
            case Rest.Kneel:
                if (moving) { rest = Rest.Ready; Schedule(); }                     // Kneel -> Walk is a transition in the controller
                else if (alert) Stand();
                break;
        }
    }

    void Fidget()
    {
        string pick = null;
        for (int i = 0; i < 6 && pick == null; i++)
        {
            string n = Fidgets[Random.Range(0, Fidgets.Length)];
            if (n != lastFidget && clipLen.ContainsKey(n) && animator.HasState(0, Animator.StringToHash(n))) pick = n;
        }
        if (pick == null) { nextFidget = Time.time + fidgetEvery.y; return; }
        lastFidget = pick; rest = Rest.Fidget;
        animator.CrossFadeInFixedTime(pick, 0.18f, 0, 0f);
        fidgetEnd = Time.time + clipLen[pick] - 0.05f;
    }

    void Kneel() { rest = Rest.Kneel; animator.CrossFadeInFixedTime(KneelDownId, 0.15f, 0, 0f); }

    void Stand()
    {
        rest = Rest.Ready; Schedule();
        var st = animator.IsInTransition(0) ? animator.GetNextAnimatorStateInfo(0) : animator.GetCurrentAnimatorStateInfo(0);
        if (st.shortNameHash == KneelIdleId) animator.CrossFadeInFixedTime(KneelUpId, 0.12f, 0, 0f);
        else if (st.shortNameHash == KneelDownId)
        {   // caught half way down: come back up from the same depth
            float k = Mathf.Clamp01(st.normalizedTime);
            if (k < 0.3f) animator.CrossFadeInFixedTime(IdleId, 0.25f, 0, 0f);
            else animator.CrossFadeInFixedTime(KneelUpId, 0.12f, 0, (1f - k) * clipLen["KneelUp"]);
        }
    }

    // ---------------------------------------------------------------- aim and recoil, on top of the clip
    void LateUpdate()
    {
        float dt = Time.deltaTime;
        if (aiming && Time.time > aimUntil) aiming = false;
        if (turretDriven) yaw = turretYaw;
        else
        {
            float want = 0f;
            if (aiming && aimBone)
            {
                Vector3 d = Vector3.ProjectOnPlane(aimPoint - aimBone.position, transform.up);
                if (d.sqrMagnitude > 0.01f) want = Mathf.Clamp(Vector3.SignedAngle(transform.right, d, transform.up), -maxYaw, maxYaw);
            }
            yaw = Mathf.MoveTowardsAngle(yaw, want, traverseSpeed * dt);
        }
        if (aimBone && Mathf.Abs(yaw) > 0.01f) aimBone.rotation = Quaternion.AngleAxis(yaw, transform.up) * aimBone.rotation;
        kick = Mathf.MoveTowards(kick, 0f, dt * 7f);
        if (kickBone && kick > 0f)
        {
            Vector3 f = MuzzlePosition - kickBone.position; f = f.sqrMagnitude > 1e-4f ? f.normalized : transform.right;
            kickBone.position -= f * (kick * kick) * recoilDistance;
        }
    }
}
